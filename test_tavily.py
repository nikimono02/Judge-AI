#!/usr/bin/env python3
"""
Simple test script to verify Tavily API is working
"""
import os
import requests

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")

def test_tavily():
    print(f"Testing Tavily API with key: {TAVILY_API_KEY[:10]}...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": "current US president 2025",
        "search_depth": "basic",
        "max_results": 3
    }
    
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data.get('results', []))} results")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_tavily()
