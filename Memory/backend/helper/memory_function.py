from datetime import datetime
from pydantic import BaseModel


class QueryRequest(BaseModel):
    user_input: str
    user_id: str
    

class MemoryFunction:
    def __init__(self, mongodb_memory):
        """Initialize with MongoDB memory instance"""
        self.collection = mongodb_memory.collection
    
    def store_message(self, user_id: str, role: str, content: str):
        """Store a message in the conversation history"""
        existing = self.collection.find_one({"user_id": user_id})
        
        if existing and "conversation" in existing:
            updated_conversation = existing["conversation"] + f"\n{role}: {content}"
        else:
            updated_conversation = f"{role}: {content}"
        
        self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "conversation": updated_conversation,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )

    def get_conversation(self, user_id: str) -> str:
        """Retrieve conversation history for a user"""
        result = self.collection.find_one({"user_id": user_id})
        if result and "conversation" in result:
            return result["conversation"]
        return ""