from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from dotenv import load_dotenv
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores  import Chroma
import logging

from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = FastAPI(title="Web Reseach ")

logger = logging.getLogger("web research application")


load_dotenv()


loader = WebBaseLoader("https://regexsoftware.com/")

docs = loader.load()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2025-01-01-preview",
    temperature=0,
)

embeddings = AzureOpenAIEmbeddings(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    deployment=os.environ["EMBEDDING_DEPLOYMENT"],
    api_version="2023-05-15",
)  


splitter =  RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap =50
)

chunk = splitter.split_documents(docs)



logger.info("Chunks: %s",chunk)

vectorstore = Chroma.from_documents(
    embedding = embeddings,
    documents =  chunk,
    persist_directory = "./chroma_db",
)

logger.info("Vectore store created successfully!")

vectorstore.persist()



prompt = PromptTemplate(
    input_variables=["question","context"],
    template="""
    You are a research assistant. Use the following context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context: {context}
    
    Question: {question}
    
    Answer:"""
)

def research_topic(question:str):
    # docs = vectorstore.similarity_search(
    #     question,
    #     k=4
    # )
   
    
    # context = "\n".join([doc.page_content for doc in docs])
    
    
    docs_with_scores = vectorstore.similarity_search_with_score(
    question,
    k=6
    )

    docs = [
        doc for doc, score in docs_with_scores
        if score < 0.8
    ]

    if not docs:
        return "Sorry, I could not find relevant information on the website."

    context = "\n\n".join(doc.page_content for doc in docs)

    chain = prompt  | llm
    
    response = chain.invoke(
        {
            "question":question,
            "context":context
        }
    )
    return response.content
    
    

class ChatRequest(BaseModel):
    question:str
    
    
@app.post("/chat")
async def search(request:ChatRequest):
    result =  research_topic(request.question)
    
    return {"result":result}