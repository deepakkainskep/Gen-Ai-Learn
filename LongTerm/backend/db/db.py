import os
from pymongo import MongoClient

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        self.db = self.client["llm_memory"]
        self.conversation = self.db["conversation_memory"]
        self.user_memory = self.db["user_memory"]
