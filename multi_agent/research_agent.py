from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Literal
import operator


# Define State
class ResearchAgentState(TypedDict):
    messages: Annotated[list, operator.add]


# Define Research Tool
@tool
def research_tool(query: str) -> str:
    """Conducts research based on user queries."""
    print(f"Using research_tool for query: {query}")
    return f"Research results for: {query}"


def create_research_agent(llm: AzureChatOpenAI):
    """Creates and returns the research agent graph."""
    
    # Bind tools to LLM
    research_llm = llm.bind_tools([research_tool])
    
    # Create tool node
    research_tool_node = ToolNode([research_tool])
    
    # Research agent node
    def research_agent_node(state: ResearchAgentState):
        """Research agent that uses research tools."""
        response = research_llm.invoke(state["messages"])
        return {"messages": [response]}
    
    # Routing function
    def should_continue(state: ResearchAgentState) -> Literal["tools", "end"]:
        """Determines if agent should use tools or finish."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    # Build the graph
    workflow = StateGraph(ResearchAgentState)
    
    # Add nodes
    workflow.add_node("agent", research_agent_node)
    workflow.add_node("tools", research_tool_node)
    
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