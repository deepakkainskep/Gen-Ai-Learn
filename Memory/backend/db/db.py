from pymongo import MongoClient
import os


class MongoDBMemory:
    def __init__(self):
        conn = os.getenv("MONGODB_CONNECTION_STRING")    
        self.collection = MongoClient(conn)["agent_memory"]["conversations"]
        self.collection.create_index([("user_id", 1)])
        