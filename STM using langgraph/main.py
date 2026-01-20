from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod



from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()



# state schema
class State(TypedDict):
    messages: str

# initialize  graph
graph_builder = StateGraph(State)

llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model="gpt-4.1",
    api_version="2025-01-01-preview",
    temperature=0,
)


app = FastAPI(title="langgraph sort term memory ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def chatbot(state: State):
    user_input = state["messages"]
    
    prompt = f"""
        You are a helpful AI assistant.
        Remember important details from this conversation and use them in future replies.

        Conversation so far:
        {state["messages"]}

        User question:
        {user_input}

        Reply clearly and concisely.
        """

    response = llm.invoke(prompt)
    print("AI:", response.content)

    return {"messages": state["messages"] + "\nAI: " + response.content}

# nodes and edges
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)




# Enable memory
checkpointer = MemorySaver()

# compile
graph = graph_builder.compile(checkpointer=checkpointer)

# config
config1 = {
    "configurable": {
        "thread_id": "1" # conversation unique id
    }
}


# run 
state = {"messages": ""}
# while True:
#     try:
#         user_input = input("Enter query.. ")
#         if user_input.lower() in ["quit", "exit", "thanks", "thankyou", "thank you"]:
#             print("Bye!")
#             break

#         state["messages"] += "\nUser: " + user_input
#         graph.invoke(state, config=config1)

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         break





class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat_memory(request: ChatRequest):
    state = {"messages": ""}
    while True:
        try:
            user_input = input("Enter query.. ")
            if user_input.lower() in ["quit", "exit", "thanks", "thankyou", "thank you"]:
                print("Bye!")
                break

            state["messages"] += "\nUser: " + user_input
            graph.invoke(state, config=config1)

        except Exception as e:
            print(f"An error occurred: {e}")
            break



png_bytes = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
with open("main.png", "wb") as f:
    f.write(png_bytes)