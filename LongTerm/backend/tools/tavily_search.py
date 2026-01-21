import os
from tavily import TavilyClient
from langchain_core.tools import tool


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