from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import asyncio
from tavily import TavilyClient
from langchain_core.tools import tool
import os


load_dotenv()

app = FastAPI(title="searching agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = AzureChatOpenAI(
    api_key= os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1", 
    api_version="2025-01-01-preview",
    temperature=0,
)

prompt_template = PromptTemplate.from_template("""
You are an intelligent AI assistant.

You have access to the following tools:
{tools}

Tool names you can use:
{tool_names}

You MUST follow this format exactly:

Question: {input}
Thought: think about what to do
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

{agent_scratchpad}
""")



@tool(description="Searches the web using Tavily")
def tavily_search(query: str) -> str:
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


@app.post("/chat")
async def chatbot(request: QueryRequest):
    try:
        result = await asyncio.to_thread(
            agent_executor.invoke,
            {"input": request.user_input}
        )
        return {"response": result["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# @app.post("/ask/stream")
# async def ask_llm_stream(request: QueryRequest):
#     try:
#         async def event_generator():
#             # Agent streaming (CORRECT)
#             for step in agent_executor.stream(
#                 {"input": request.user_input}
#             ):
#                 if "output" in step:
#                     yield step["output"]
#                 await asyncio.sleep(0)
    
#         return StreamingResponse(
#             event_generator(),
#             media_type="text/plain"
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/stream")
async def ask_llm_stream(request: QueryRequest):
    async def event_generator():
        for step in agent_executor.stream({"input": request.user_input}):
            if "output" in step:
                for char in step["output"]:
                    yield char
                    await asyncio.sleep(0)

    return StreamingResponse(event_generator(), media_type="text/plain")
