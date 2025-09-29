"""
Tiny wrappers around the Ollama model calls so other files stay clean.

Two functions:
- generate_creative_answer: first answer (paragraph or list)
- generate_historian_feedback: review + corrections (+ citations)
"""

import ollama
from typing import List, Dict

def generate_creative_answer(user_fact: str, list_mode: bool = False) -> str:
    """Call Ollama to produce the creative answer text."""
    from prompts import build_creative_prompt
    
    prompt = build_creative_prompt(user_fact, list_mode=list_mode)
    try:
        res = ollama.generate(
            model="llama3",
            prompt=prompt,
            options={"temperature": 0.9}
        )
        return res.get("response", "")
    except Exception as e:
        print(f"Ollama generation error: {e}")
        return "Sorry, I couldn't generate a response at this time."

def generate_historian_feedback(text: str, sources: List[Dict] = None) -> str:
    """Call Ollama to produce historian feedback (citations if sources given)."""
    from prompts import build_historian_prompt_with_sources, build_historian_prompt
    
    prompt = build_historian_prompt_with_sources(text, sources) if sources else build_historian_prompt(text)
    try:
        res = ollama.generate(
            model="llama3",
            prompt=prompt,
            options={"temperature": 0.1}
        )
        return res.get("response", "")
    except Exception as e:
        print(f"Ollama generation error: {e}")
        return "Sorry, I couldn't verify this information."