from pydantic_settings import BaseSettings
 
class Settings(BaseSettings):
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_MODEL: str
    AZURE_OPENAI_API_VERSION:str
    EMBEDDING_DEPLOYMENT: str
    
    TAVILY_API_KEY: str
    MONGODB_CONNECTION_STRING:str
    REDIS_HOST: str 
    REDIS_PORT: int
 
    class Config:
        env_file = ".env"
 
 
settings = Settings()