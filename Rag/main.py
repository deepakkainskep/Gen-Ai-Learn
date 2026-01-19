from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import logging



load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Rag Application")


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


app = FastAPI(title="Rag Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


loader = PyPDFLoader("./Deepak_Resume.pdf")
document = loader.load()

logger.info("Document loaded!")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100
)

chunk = text_splitter.split_documents(document)

logger.info("Chunk----- %s",chunk)

vectorstore = Chroma.from_documents(
    documents=chunk,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

vectorstore.persist()

logger.info("Vector store created and persisted")

# prompt =  PromptTemplate(
#     input_variables=["context","question"],
#     template="""
#     you are a helpful pdf based assisant.
#     answer the question based on the context.
#     if the answer is not found in the context
#     say: 'sorry i could not find the answer in the document'.
# context:
# {context}

# question:
# {question}

# Answer:
# """   
# )

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful and accurate pdf based AI assistant.

Your task is to answer the user's question using ONLY the information
provided in the context below.

RULES:
- Use only the given context to answer.
- Do NOT use prior knowledge or make assumptions.
- If the answer is NOT clearly present in the context,
  respond exactly with:
  "sorry i could not find the answer in the document"
- Do NOT explain why the answer is missing.
- Keep the answer clear, concise, and directly relevant.

Context:
{context}

Question:
{question}

Answer:
"""
)

def ask_document_question(question: str):
    docs = vectorstore.similarity_search(
        question,
        k=4
    )

    context = "\n".join(doc.page_content for doc in docs)

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question
        }
    )
    logger.info("Response: %s", response.content)

    return response.content



class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
async def rag_chat(request: ChatRequest):
    answer = ask_document_question(request.question)
    return {"answer": answer}
