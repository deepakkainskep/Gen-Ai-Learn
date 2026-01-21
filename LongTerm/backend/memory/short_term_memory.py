from datetime import datetime
from db.db import MongoDB

class ShortTermMemory:
    def __init__(self):
        self.db = MongoDB()

    def save(self, user_id, session_id, role, text):
        line = f"{role}: {text}"

        doc = self.db.conversation.find_one(
            {"user_id": user_id, "session_id": session_id}
        )

        conversation = (
            doc["conversation"] + "\n" + line
            if doc and doc.get("conversation")
            else line
        )

        self.db.conversation.update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$set": {
                    "conversation": conversation,
                    "last_updated": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    def fetch(self, user_id, session_id):
        doc = self.db.conversation.find_one(
            {"user_id": user_id, "session_id": session_id}
        )
        return doc["conversation"] if doc else ""
