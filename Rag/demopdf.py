import os
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
import chromadb
from chromadb.config import Settings

load_dotenv()


PDF_PATH = "./uploaded_pdfs/active.pdf"
VECTOR_DB_ROOT = "./chroma_db2"
VECTOR_DB_PATH = f"{VECTOR_DB_ROOT}/active"


app = FastAPI(title="Single PDF RAG Application (Stable)")

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

Rules:
- Answer ONLY from the given context
- Do NOT use prior knowledge
- If the answer is NOT present, respond exactly:
  "sorry i could not find the answer in the document"

Context:
{context}

Question:
{question}

Answer:
"""
)

chroma_client = chromadb.Client(
    Settings(
        persist_directory=VECTOR_DB_ROOT,
        allow_reset=True
    )
)

class ChatRequest(BaseModel):
    question: str

def get_vectorstore():
    if not os.path.exists(VECTOR_DB_PATH):
        raise HTTPException(
            status_code=400,
            detail="No PDF uploaded yet. Please upload a PDF first."
        )

    return Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings,
        client=chroma_client
    )

def ask_document_question(question: str):
    vectorstore = get_vectorstore()

    docs = vectorstore.similarity_search(question, k=4)
    context = "\n".join(doc.page_content for doc in docs)

    chain = prompt | llm
    response = chain.invoke(
        {"context": context, "question": question}
    )

    return response.content


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    os.makedirs("uploaded_pdfs", exist_ok=True)
    os.makedirs(VECTOR_DB_ROOT, exist_ok=True)

    # release all file locks
    chroma_client.reset()

    # Save PDF overwrite existing document
    with open(PDF_PATH, "wb") as f:
        shutil.copyfileobj(file.file, f)

    loader = PyPDFLoader(PDF_PATH)
    
    documents = loader.load()

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )
    
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="PDF contains no extractable text. Scanned PDFs are not supported."
        )

    # Create vector DB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH,
        client=chroma_client
    ).persist()

    return {
        "message": "PDF uploaded successfully. Previous document replaced."
    }

@app.post("/chat")
async def chat_with_pdf(request: ChatRequest):
    answer = ask_document_question(request.question)
    return {"answer": answer}
