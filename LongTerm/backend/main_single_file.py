import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from tavily import TavilyClient

load_dotenv()

app = FastAPI(title="LLM Memory System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== DATABASE =====================

class MongoDBMemory:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        self.db = self.client["llm_memory"]
        self.conversation_collection = self.db["conversation_memory"]
        self.user_memory_collection = self.db["user_memory"]

    def save_conversation(self, user_id, session_id, role, text):
        line = f"{role}: {text}"

        doc = self.conversation_collection.find_one(
            {"user_id": user_id, "session_id": session_id}
        )

        conversation = (
            doc["conversation"] + "\n" + line
            if doc and doc.get("conversation")
            else line
        )

        self.conversation_collection.update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$set": {
                    "conversation": conversation,
                    "last_updated": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    def fetch_conversation(self, user_id, session_id):
        doc = self.conversation_collection.find_one(
            {"user_id": user_id, "session_id": session_id}
        )
        return doc["conversation"] if doc else ""

    def save_user_memory(self, user_id, facts: Dict[str, str]):
        if not facts:
            return

        self.user_memory_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {f"memory.{k}": v for k, v in facts.items()},
                "$currentDate": {"updated_at": True},
            },
            upsert=True,
        )

    def fetch_user_memory(self, user_id):
        doc = self.user_memory_collection.find_one({"user_id": user_id})
        if not doc or "memory" not in doc:
            return "No prior memory."

        return "\n".join(f"{k}: {v}" for k, v in doc["memory"].items())

memory_db = MongoDBMemory()



llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)


# memory extractor
class MemoryExtractor:
    def __init__(self, llm):
        self.llm = llm

    def extract_memory(self, text: str) -> Optional[Dict[str, str]]:
        prompt = f"""
Extract personal information.

Format:
Category: value, Category: value

If none, return null.

Message:
{text}
"""
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

memory_extractor = MemoryExtractor(llm)

# tool

@tool(description="Searches the web using Tavily")
def tavily_search(query: str) -> str:
    """Searches the web using Tavily and returns the top results."""
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    response = client.search(query=query, max_results=3)

    # Correct key access
    search_results = response.get("results", [])

    if not search_results:
        return "No results found."

    formatted_results = "\n".join(
        f"- {res['title']}: {res['url']}"
        for res in search_results
    )

    return formatted_results

tools = [tavily_search]


# prompt
prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

User Memory:
{input}

{agent_scratchpad}""")

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
    max_iterations=15,
    max_execution_time=60,
)


# fastapi
class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    user_input: str

@app.post("/chat")
async def chat(req: QueryRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input cannot be empty")

    user_memory = memory_db.fetch_user_memory(req.user_id)
    conversation = memory_db.fetch_conversation(req.user_id, req.session_id)

    final_input = f"""
User Memory:
{user_memory}

Conversation so far:
{conversation}

User Question:
{req.user_input}
""".strip()

    memory_db.save_conversation(req.user_id, req.session_id, "user", req.user_input)

    result = agent_executor.invoke({"input": final_input})
    answer = result["output"]

    memory_db.save_conversation(req.user_id, req.session_id, "assistant", answer)

    extracted = memory_extractor.extract_memory(req.user_input)
    if extracted:
        memory_db.save_user_memory(req.user_id, extracted)

    return {
        "answer": answer,
        "stored_memory": extracted,
        "conversation": memory_db.fetch_conversation(req.user_id, req.session_id),
    }