from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import asyncio
from tavily import TavilyClient
from langchain_core.tools import tool
import os

from db.db import MongoDBMemory
from helper.memory_function import MemoryFunction

load_dotenv()

app = FastAPI(title="store memory in mongodb")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongodb_memory = MongoDBMemory()

memory_function = MemoryFunction(mongodb_memory)

llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1", 
    api_version="2025-01-01-preview",
    temperature=0,
)

prompt_template = PromptTemplate.from_template("""
You are an intelligent AI assistant with memory of previous conversations.

Previous Conversation History:
{conversation_history}

You have access to the following tools:
{tools}

Tool names you can use:
{tool_names}

You MUST follow this format exactly:

Question: {input}
Thought: think about what to do (consider previous conversation if relevant)
Action: one of [{tool_names}]
Action Input: input to the action
Observation: result of the action
Thought: final reasoning
Final Answer: the final answer to the user

Rules:
- ALWAYS use this format
- NEVER reply casually
- NEVER skip Thought/Final Answer
- Use tools when required
- Remember and reference previous conversations when relevant

{agent_scratchpad}
""")


@tool(description="Searches the web using Tavily")
def tavily_search(query: str) -> str:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    response = client.search(query=query, max_results=3)
    search_results = response.get("results", [])

    if not search_results:
        return "No results found."

    formatted_results = "\n".join(
        f"- {res['title']}: {res['url']}"
        for res in search_results
    )

    return formatted_results
    

agent = create_react_agent(
    llm=llm,
    tools=[tavily_search],
    prompt=prompt_template,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[tavily_search],
    verbose=True,
    handle_parsing_errors=True,
)


class QueryRequest(BaseModel):
    user_input: str
    user_id: str


@app.post("/chat")
async def stream_response(request: QueryRequest):

    conversation_history = memory_function.get_conversation(request.user_id)
    
    memory_function.store_message(request.user_id, "user", request.user_input)
      
    # Collect the full response for storage
    full_response = ""
    
    async def event_generator():
        nonlocal full_response
        for step in agent_executor.stream({
            "input": request.user_input,
            "conversation_history": conversation_history if conversation_history else "No previous conversation."
        }):
            if "output" in step:
                for char in step["output"]:
                    full_response += char
                    yield char
                    await asyncio.sleep(0)
        
        # store message 
        if full_response:
            memory_function.store_message(request.user_id, "assistant", full_response)

    return StreamingResponse(event_generator(), media_type="text/plain")