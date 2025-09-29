"""
Simple Tavily search wrapper. Returns top 3 results with good sources.
"""

import os
import requests
from functools import lru_cache
from typing import List, Dict
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

@lru_cache(maxsize=100)
def run_tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    """Search Tavily and return top 3 results."""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False
            },
            timeout=10
        )
        
        if response.status_code >= 400:
            print(f"Tavily error {response.status_code}")
            return []
        
        return _process_results(response.json())
    except Exception as e:
        print(f"Search error: {e}")
        return []

def _process_results(data: Dict) -> List[Dict]:
    """Process Tavily results and return top 3."""
    if not isinstance(data, dict):
        return []
    
    results = []
    seen_urls = set()
    
    for item in data.get("results", []):
        if not isinstance(item, dict):
            continue
            
        url = item.get("url", "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Get domain for scoring
        try:
            domain = urlparse(url).netloc.lower()
        except:
            domain = ""
        
        # Simple scoring: news/gov/edu = high, others = low
        score = 100 if any(x in domain for x in [".gov", ".edu", "bbc.com", "cnn.com", "reuters.com", "whitehouse.gov"]) else 50
        
        results.append({
            "title": _trim(item.get("title", "Untitled"), 90),
            "url": url,
            "snippet": _trim(item.get("content", item.get("snippet", "")), 180),
            "_score": score
        })
    
    # Sort by score and return top 3
    results.sort(key=lambda x: x["_score"], reverse=True)
    return [{"title": r["title"], "url": r["url"], "snippet": r["snippet"]} for r in results[:3]]

def _trim(text: str, max_len: int) -> str:
    """Trim text to max length with ellipsis."""
    text = (text or "").strip()
    return text if len(text) <= max_len else text[:max_len-1] + "…"