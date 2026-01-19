import os
import uuid
import shutil
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma


load_dotenv()




app = FastAPI(title="PDF RAG Application")

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


prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful and accurate PDF-based AI assistant.

Your task is to answer the user's question using ONLY the information
provided in the context below.

RULES:
- Use only the given context to answer.
- Do NOT use prior knowledge.
- If the answer is NOT present in the context, respond exactly with:
  "sorry i could not find the answer in the document"
- Do NOT explain why.
- Keep the answer short and clear.

Context:
{context}

Question:
{question}

Answer:
"""
)

class ChatRequest(BaseModel):
    pdf_id: str
    question: str


def get_vectorstore(pdf_id: str):
    persist_dir = f"./chroma_db2/{pdf_id}"
    if not os.path.exists(persist_dir):
        raise HTTPException(status_code=404, detail="PDF not found")

    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

def ask_document_question(pdf_id: str, question: str):
    vectorstore = get_vectorstore(pdf_id)

    docs = vectorstore.similarity_search(question, k=4)
    context = "\n".join(doc.page_content for doc in docs)

    chain = prompt | llm
    response = chain.invoke({
        "context": context,
        "question": question
    })

    return response.content


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    pdf_id = str(uuid.uuid4())

    os.makedirs("uploaded_pdfs", exist_ok=True)
    os.makedirs("chroma_db", exist_ok=True)

    pdf_path = f"./uploaded_pdfs/{pdf_id}.pdf"

    # Save PDF
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(documents)

    # Create Vector DB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=f"./chroma_db2/{pdf_id}"
    ).persist()

    return {
        "message": "PDF uploaded and indexed successfully",
        "pdf_id": pdf_id
    }

@app.post("/chat")
async def chat_with_pdf(request: ChatRequest):
    answer = ask_document_question(
        request.pdf_id,
        request.question
    )
    return {"answer": answer}
