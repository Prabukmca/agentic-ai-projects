import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root if present


def serpapi_raw(query: str):
    """Raw SerpAPI usage via the google-search-results package."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError("SERPAPI_API_KEY is not set or is a placeholder. Set it in your .env or environment.")
    from serpapi import GoogleSearch

    params = {"q": query, "api_key": api_key}
    search = GoogleSearch(params)
    return search.get_dict()


def langchain_serpapi(query: str):
    """Use LangChain's SerpAPI wrapper (reads SERPAPI_API_KEY env var)."""
    try:
        from langchain.utilities import SerpAPIWrapper
    except ImportError:
        return "LangChain SerpAPI wrapper not available in this langchain installation.\nInstall a compatible langchain version or use the raw SerpAPI client."

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return "SERPAPI_API_KEY is not set or is a placeholder. Set it in your .env or environment to use the SerpAPI wrapper."

    try:
        wrapper = SerpAPIWrapper()
        return wrapper.run(query)
    except Exception as e:
        return f"LangChain SerpAPI wrapper raised an error at runtime: {e!r}"


if __name__ == "__main__":
    q = "Python programming best practices"
    print("Running SerpAPI raw example...")
    raw = serpapi_raw(q)
    print(raw.get("organic_results", [])[:1])

    print("\nRunning LangChain SerpAPI wrapper example...")
    print(langchain_serpapi(q))
