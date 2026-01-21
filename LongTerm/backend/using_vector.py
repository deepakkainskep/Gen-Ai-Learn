import os
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document

from langchain_community.vectorstores import Chroma
from tavily import TavilyClient

load_dotenv()

app = FastAPI(title="LLM Long-Term Memory with Chroma Vector DB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


embeddings = AzureOpenAIEmbeddings(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    deployment=os.environ["EMBEDDING_DEPLOYMENT"],
    api_version="2023-05-15",
)


class VectorMemory:
    def __init__(self):
        self.store = Chroma(
            collection_name="long_term_memory",
            embedding_function=embeddings,
            persist_directory="./chroma_memory",
        )

    def save(self, user_id: str, session_id: str, memory: str):
        doc = Document(
            page_content=memory,
            metadata={
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        self.store.add_documents([doc])

    def fetch_user_memory(self, user_id: str, k: int = 5) -> List[str]:
        results = self.store.similarity_search(
            query="personal information",
            k=k,
            filter={"user_id": user_id},
        )
        return [r.page_content for r in results]


llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2024-02-01",
    temperature=0,
)


class MemoryExtractor:
    def __init__(self, llm: AzureChatOpenAI):
        self.llm = llm

    def extract_memory(self, user_text: str) -> Optional[str]:
        prompt = f"""
You are a memory extraction system. Extract personal information from the user's message.

Extract:
- Name
- Hometown
- Current Location
- Education
- Profession
- Company
- Email
- Personal background

Rules:
- from/originally from/born in = Hometown
- live in/living in/currently in = Current Location
- Return "null" if no personal data
- Format: Category: value, Category: value

User Message:
{user_text}

Output:
"""
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip().replace("```", "")
            if content.lower() in ["null", "none", ""]:
                return None
            return content
        except:
            return None


memory_db = VectorMemory()
memory_extractor = MemoryExtractor(llm)


@tool
def tavily_search(query: str) -> str:
    """Perform a web search using Tavily API and return top 3 results."""
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    res = client.search(query=query, max_results=3)
    results = res.get("results", [])
    return "\n".join(f"- {r['title']} : {r['url']}" for r in results) or "No results found."


tools = [tavily_search]

prompt = PromptTemplate.from_template("""
You are a helpful AI assistant with long-term memory.

Tools:
{tools}

Tool Names:
{tool_names}

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


@app.post("/vectorchat")
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
        "stored_memory": extracted,
    }
