import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

from tavily import TavilyClient
from langchain_core.messages import HumanMessage
from typing import Optional

load_dotenv()

app = FastAPI(title="LLM Long-Term Memory with MongoDB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MongoDBMemory:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        self.db = self.client["llm_memory"]
        self.collection = self.db["memory"]

    def save(self, user_id, session_id, memory):
        """
        Save or update memory for a user session.
        If session exists, append new memory to existing memory.
        If session doesn't exist, create new document.
        """
        # Find existing session
        existing = self.collection.find_one({
            "user_id": user_id,
            "session_id": session_id
        })
        
        if existing:
            # update memory
            current_memory = existing.get("memory", "")
            
            # Append new memory to existing
            if current_memory:
                updated_memory = f"{current_memory}, {memory}"
            else:
                updated_memory = memory
            
            # Update the document
            self.collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                {
                    "$set": {
                        "memory": updated_memory,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            # New session - create new document
            self.collection.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "memory": memory,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

    def fetch_user_memory(self, user_id):
        """Fetch all memories for a user across all sessions"""
        return [d["memory"] for d in self.collection.find({"user_id": user_id})]
       
    
llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)



class MemoryExtractor:
    def __init__(self, llm: AzureChatOpenAI):
        """
        Initialize MemoryExtractor with LLM instance.
        
        Args:
            llm: AzureChatOpenAI instance
        """
        self.llm = llm
    
    def extract_memory(self, user_text: str) -> Optional[str]:
        """
        Extract long-term personal memory from user text.
        
        Args:
            user_text: The user's message
            
        Returns:
            String with extracted memory in natural language, or None if no memory to extract
        """
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

User: "I'm from Bharatpur and live in Jaipur"
Output: Hometown: Bharatpur, Current Location: Jaipur

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
{user_text}

OUTPUT:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Remove any extra formatting
            content = content.replace("```", "").replace("Output:", "").strip()
            
            # Check if no memory
            if content.lower() == "null" or content.lower() == "none" or not content:
                return None
            
            return content
            
        except Exception as e:
            print(f"Extraction error: {e}")
            return None
       
       
 
  
 
memory_db = MongoDBMemory()
memory_extractor = MemoryExtractor(llm)




@tool
def tavily_search(query: str) -> str:
    """Searches the web for information."""
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    res = client.search(query=query, max_results=3)
    results = res.get("results", [])
    return "\n".join(f"- {r['title']} : {r['url']}" for r in results) or "No results found."

tools = [tavily_search]


prompt = PromptTemplate.from_template("""
You are a helpful AI assistant with long-term memory.

You have access to the following tools:
{tools}

Tool names:
{tool_names}

Use the following format:

Question: {input}
{agent_scratchpad}
Thought:
Action:
Action Input:
Observation:
Thought:
Final Answer:
""")


agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    user_input: str

@app.post("/chat")
async def chatbot(req: QueryRequest):

    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input cannot be empty")

    memories = memory_db.fetch_user_memory(req.user_id)
    memory_block = "\n".join(f"- {m}" for m in memories) or "No prior memory."

    final_input = f"""
User Memory:
{memory_block}

User Question:
{req.user_input}
""".strip()

    result = agent_executor.invoke({"input": final_input})
    answer = result["output"]

    extracted = memory_extractor.extract_memory(req.user_input)
    if extracted:
        memory_db.save(req.user_id, req.session_id, extracted)

    return {
        "answer": answer,
        "stored_memory": extracted
    }
