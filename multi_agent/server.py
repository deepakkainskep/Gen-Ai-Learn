from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
from research_agent import create_research_agent
from code_agent import create_code_agent

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import logging


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Multi-Agent Application")



llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2025-01-01-preview",
    temperature=0,
)


app = FastAPI(title="Rag Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create agent instances
research_agent = create_research_agent(llm)
code_agent = create_code_agent(llm)


def supervisor(query: str):
    """
    Supervisor function that routes queries to appropriate agents.
    
    Args:
        query: User input query
        
    Returns:
        Final response from the selected agent
    """
    logger.info("SUPERVISOR: Analyzing query...")
    
    # Route based on query content
    if "code" in query.lower():
        logger.info("→ Routing to CODE AGENT")
        
        result = code_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
    else:
        logger.info("→ Routing to RESEARCH AGENT")
        result = research_agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
    
    return result["messages"][-1].content



class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
async def chat_with_multi_agent(request: ChatRequest):
    answer = supervisor(request.question)
    return {"final_answer": answer}




