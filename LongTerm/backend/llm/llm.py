from langchain_openai import AzureChatOpenAI,AzureOpenAIEmbeddings
from config.config import settings

llm = AzureChatOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)


embeddings = AzureOpenAIEmbeddings(
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    deployment=settings.EMBEDDING_DEPLOYMENT,
    api_version="2023-05-15",
)
