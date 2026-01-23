from pymongo import MongoClient
from config.config import settings

class MongoDB:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_CONNECTION_STRING)
        self.db = self.client["llm_memory"]
        self.conversation = self.db["conversation_memory"]
        self.user_memory = self.db["user_memory"]
