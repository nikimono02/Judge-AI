import requests
from functools import lru_cache
from typing import List, Dict
TAVILY_API_KEY = "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"

@lru_cache(maxsize=100)
def run_tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    """Search using Tavily API with caching."""
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "api_key": TAVILY_API_KEY
        }
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return normalize_tavily_response(response.json())
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []

def normalize_tavily_response(data: Dict) -> List[Dict]:
    """Normalize Tavily API response."""
    results = []
    if not isinstance(data, dict):
        return results
    items = data.get("results") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "Untitled"
        url = item.get("url") or ""
        snippet = item.get("content") or item.get("snippet") or ""
        results.append({"title": title, "url": url, "snippet": snippet})
    return results