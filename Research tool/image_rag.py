from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from PIL import Image
import base64
from io import BytesIO
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Image RAG Application")

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

app = FastAPI(title="Image RAG Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def load_images(folder_path):
    documents = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(folder_path, file)
            documents.append(
                Document(
                    page_content=f"Image file related to diagrams or UI: {file}",
                    metadata={"image_path": path}
                )
            )
    logger.info("Documents: %s",documents)
    
    return documents

image_docs = load_images("./images")


logger.info("Loaded %d images", len(image_docs))


vectorstore = Chroma.from_documents(
    documents=image_docs,
    embedding=embeddings,
    persist_directory="./chroma_image_db"
)

logger.info("Image vector store created")

retriever = vectorstore.as_retriever(
    search_kwargs={"k": 2}
    )

prompt = PromptTemplate(
    input_variables=["question"],
    template="""
You are a helpful and accurate image-based AI assistant.

You will be given images and a question.
Answer the question strictly based on the visual information
present in the images.

If the answer cannot be determined from the images,
respond exactly with:
"sorry i could not find the answer in the images"

Question:
{question}

Answer:
"""
)

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def ask_image_question(question: str):
    docs = retriever.invoke(question)

    if not docs:
        return "sorry i could not find the answer in the images"

    content = [{"type": "text", "text": prompt.format(question=question)}]
    
    for doc in docs:
        img = Image.open(doc.metadata["image_path"])
        img_base64 = image_to_base64(img)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}"
            }
        })

    message = HumanMessage(content=content)
    response = llm.invoke([message])

    return response.content



class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def rag_chat(request: ChatRequest):
    answer = ask_image_question(request.question)
    return {"answer": answer}