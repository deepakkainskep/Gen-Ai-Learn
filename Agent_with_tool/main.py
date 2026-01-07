<<<<<<< HEAD
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from tavily import TavilyClient
from langchain_core.tools import tool
import os


load_dotenv()

app = FastAPI(title="Azure ReAct Agent API")

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

IMPORTANT:
- You MUST ALWAYS call one of the available tools before producing a Final Answer.
- Even if the answer seems obvious or simple, you are REQUIRED to use a tool.
- You are NOT allowed to skip the Action step.

Use the following format STRICTLY:

Question: the user question
Thought: you must decide which tool to use (tool usage is mandatory)
Action: one of [{tool_names}]
Action Input: input to the tool
Observation: tool result
Thought: final reasoning based on the tool output
Final Answer: final answer to the user


Rules:
- If the user greets you, STILL call a tool and then reply politely and ask for an Azure question
- If the question is NOT related to Azure, STILL call a tool and then reply:
  "I can only help with Azure-related questions."
- If the user provides Azure configuration/code/scripts:
  1. Call a tool to analyze/search
  2. Identify issues
  3. Explain clearly
  4. Suggest fixes
  5. Recommend best practices
- Keep answers simple and practical

Question: {input}
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


@app.post("/chatbot")
async def ask_llm(request: QueryRequest):
    try:
        result = await asyncio.to_thread(
            agent_executor.invoke,
            {"input": request.user_input}
        )
        return {"response": result["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from tavily import TavilyClient
from langchain_core.tools import tool
import os


load_dotenv()

app = FastAPI(title="Azure ReAct Agent API")

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

Use the following format STRICTLY:

Question: the user question
Thought: think whether you need a tool or not
Action: one of [{tool_names}]
Action Input: input to the tool
Observation: tool result
Thought: final reasoning
Final Answer: final answer to the user


"Rules:\n"
    "- If the user greets you, reply politely and ask for an Azure question\n"
    "- If the question is NOT related to Azure, reply:\n"
    "  'I can only help with Azure-related questions.'\n"
    "- If the user provides Azure configuration/code/scripts:\n"
    "  1. Identify issues\n"
    "  2. Explain clearly\n"
    "  3. Suggest fixes\n"
    "  4. Recommend best practices\n"
    "- Keep answers simple and practical\n\n"

Question: {input}
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


@app.post("/chatbot")
async def ask_llm(request: QueryRequest):
    try:
        result = await asyncio.to_thread(
            agent_executor.invoke,
            {"input": request.user_input}
        )
        return {"response": result["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
>>>>>>> 352c8d52bbf0ec2e22557e35926f17d3fa6233a4
