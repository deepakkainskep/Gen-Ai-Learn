from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Literal
import operator


# Define State
class CodeAgentState(TypedDict):
    messages: Annotated[list, operator.add]


# Define Code Tool
@tool
def code_tool(query: str) -> str:
    """Generates code snippets based on user queries."""
    print(f"Using code_tool for query: {query}")
    return f"Code generated for: {query}"


def create_code_agent(llm: AzureChatOpenAI):
    """Creates and returns the code agent graph."""
    
    # Bind tools to LLM
    code_llm = llm.bind_tools([code_tool])
    
    code_tool_node = ToolNode([code_tool])
    
    # Code agent node
    def code_agent_node(state: CodeAgentState):
        """Code agent that uses coding tools."""
        response = code_llm.invoke(state["messages"])
        return {"messages": [response]}
    
    # Routing function
    def should_continue(state: CodeAgentState) -> Literal["tools", "end"]:
        """Determines if agent should use tools or finish."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    # Build the graph
    
    workflow = StateGraph(CodeAgentState)
    
    # Add nodes
    workflow.add_node("agent", code_agent_node)
    workflow.add_node("tools", code_tool_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()