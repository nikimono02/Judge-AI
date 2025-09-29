"""
Very small wrapper around the Tavily search API.

Input: a query string (we use the creative answer text)
Output: a short, uniform list of evidence items {title, url, snippet}
"""

import os
import requests
from functools import lru_cache
from typing import List, Dict
from urllib.parse import urlparse

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")

@lru_cache(maxsize=100)
def run_tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    """Call Tavily search and return normalized evidence. Cached for speed.

    Notes:
    - Requires a valid Tavily API key in env var TAVILY_API_KEY.
    - Returns an empty list on any failure (keeps app running).
    """
    try:
        if not TAVILY_API_KEY:
            print("Tavily error: missing TAVILY_API_KEY")
            return []
        # Tavily expects the API key in the JSON body, not Authorization header
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False
        }
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code >= 400:
            print(f"Tavily HTTP {response.status_code}: {response.text[:500]}")
            return []
        
        return normalize_tavily_response(response.json())
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []

def normalize_tavily_response(data: Dict) -> List[Dict]:
    """Convert Tavily response JSON to concise, prioritized evidence items.

    Steps:
    - Extract {title,url,snippet}
    - De-duplicate by URL
    - Score by domain reliability (.gov/.edu > reputable news/encyclopedias > others)
    - Trim title/snippet to short lengths
    - Return top 3
    """
    def extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

    reputable_domains = (
        "britannica.com",
        "bbc.com",
        "nytimes.com",
        "reuters.com",
        "apnews.com",
        "nasa.gov",
        "loc.gov",
        "archives.gov",
        "si.edu",
        "stanford.edu",
        "harvard.edu",
        "ox.ac.uk",
        "cam.ac.uk",
        ".gov",
        ".edu",
    )

    def score_domain(domain: str) -> int:
        if not domain:
            return 0
        # Highest priority: explicit .gov/.edu or known reputable sites
        if domain.endswith(".gov") or domain.endswith(".edu"):
            return 100
        for rep in reputable_domains:
            if domain.endswith(rep) or rep in domain:
                return 80
        # Otherwise give a modest baseline score
        return 40

    def trim(text: str, max_len: int) -> str:
        text = (text or "").strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "…"

    raw_results: List[Dict] = []
    if not isinstance(data, dict):
        return raw_results

    items = data.get("results") or []
    seen_urls = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if not url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = item.get("title") or "Untitled"
        snippet = item.get("content") or item.get("snippet") or ""

        domain = extract_domain(url)
        score = score_domain(domain)

        raw_results.append({
            "title": trim(title, 90),
            "url": url,
            "snippet": trim(snippet, 180),
            "_score": score
        })

    # Sort by score (desc) then keep original order for ties
    raw_results.sort(key=lambda r: r.get("_score", 0), reverse=True)

    top = raw_results[:3]
    # Drop internal fields
    concise = [{"title": r["title"], "url": r["url"], "snippet": r["snippet"]} for r in top]
    return concise