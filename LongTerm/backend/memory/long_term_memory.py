from typing import Dict, Optional
from langchain_core.messages import HumanMessage
from db.db import MongoDB


class LongTermMemory:
    def __init__(self, llm):
        self.llm = llm
        self.db = MongoDB()

    def extract(self, text: str) -> Optional[Dict[str, str]]:
        prompt = f"""You are a memory extraction system. Extract personal information from the user's message.

WHAT TO EXTRACT:
- Name (first name, last name, full name)
- Hometown (where they are FROM originally - use "from", "originally from", "born in")
- Current Location (where they LIVE NOW - use "live in", "living in", "currently in", "based in")
- Education (degree, university, school, field of study)
- Profession (job title, occupation, role)
- Company (employer, organization)
- Email address
- Personal background information

DO NOT EXTRACT:
- Phone numbers
- Technical topics (programming, AI, ML, frameworks, libraries)
- Questions or requests for help
- Casual conversation without personal details

EXAMPLES:

User: "Hi my name is Raghav"
Output: Name: Raghav

User: "I am from Bharatpur and live in Jaipur"
Output: Hometown: Bharatpur, Current Location: Jaipur

User: "I'm Aditya and I live in Haryana"
Output: Name: Aditya, Current Location: Haryana

User: "I'm originally from Mumbai but now I live in Delhi"
Output: Hometown: Mumbai, Current Location: Delhi

User: "I work as a software engineer at Google"
Output: Profession: software engineer, Company: Google

User: "I'm from Chennai"
Output: Hometown: Chennai

User: "I live in Bangalore"
Output: Current Location: Bangalore

User: "How do I use LangChain?"
Output: null

User: "My name is John, I'm from Mumbai and I'm a data scientist living in Pune"
Output: Name: John, Hometown: Mumbai, Profession: data scientist, Current Location: Pune

IMPORTANT RULES:
- "from", "originally from", "born in" = Hometown
- "live in", "living in", "based in", "currently in" = Current Location
- If the message contains ANY personal information, extract it
- Format: "Category: value, Category: value" (only include categories that have values)
- If NO personal information exists, return ONLY the word: null
- Do not add explanations, just return the extracted memory or null

USER MESSAGE:
{text}

OUTPUT:"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        if content.lower() == "null":
            return None

        data = {}
        for part in content.split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                data[k.strip()] = v.strip()

        return data or None

    def save(self, user_id, memory: Dict[str, str]):
        if not memory:
            return

        self.db.user_memory.update_one(
            {"user_id": user_id},
            {
                "$set": {f"memory.{k}": v for k, v in memory.items()},
                "$currentDate": {"updated_at": True},
            },
            upsert=True,
        )

    def fetch(self, user_id):
        doc = self.db.user_memory.find_one({"user_id": user_id})
        if not doc or "memory" not in doc:
            return "No prior memory."

        return "\n".join(f"{k}: {v}" for k, v in doc["memory"].items())
