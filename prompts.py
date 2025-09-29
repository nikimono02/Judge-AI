from typing import List, Dict

def build_creative_prompt(user_fact: str, list_mode: bool = False) -> str:
    """Create the creative-role prompt."""

    if list_mode:
        return (
            "You are a creative historian. Be precise and complete.\n"
            "- Output ONLY a Markdown bullet list, one item per line.\n"
            "- No introduction or closing text.\n"
            "- No numbering. Use '-' bullets.\n"
            "- If asked to 'list/name all', include ALL items; do not summarize.\n"
            "- Prefer official names; optionally add years in office in parentheses.\n\n"
            f"Request: {user_fact}\n\n"
            "List:"
        )
    return (
        "You are a creative historian. Be brief and direct.\n"
        "- One short paragraph (max 40-60 words).\n"
        "- Avoid fluff.\n\n"
        f"Claim: {user_fact}\n\n"
        "Answer:"
    )

def build_smart_historian_prompt(user_input: str, creative_answer: str, sources: List[Dict]) -> str:
    sources_block_lines = []
    for idx, src in enumerate(sources, start=1):
        title = src.get("title", "Untitled")
        url = src.get("url", "")
        snippet = src.get("snippet", "")
        sources_block_lines.append(f"[{idx}] {title} — {url}\n{snippet}")
    sources_block = "\n\n".join(sources_block_lines) if sources_block_lines else "(no sources)"
    
    return (
        "You are a smart history expert. Give a complete, accurate answer with sources.\n"
        "- CRITICAL: The web sources below are MORE CURRENT than your training data.\n"
        "- NEVER APOLOGIZE FOR PREVIUOS ANSWER.\n"
        "- For current events in 2025, ALWAYS trust recent web sources over outdated training data.\n"
        "- If sources show different information than your knowledge, the sources are CORRECT.\n"
        "- Provide a clear, confident answer based on the sources.\n"
        "- Include relevant citations with [n] markers.\n"
        "- Be informative but concise (100-150 words max).\n\n"
        f"USER QUESTION: {user_input}\n\n"
        f"INITIAL CREATIVE ANSWER: {creative_answer}\n\n"
        f"RESEARCH SOURCES:\n{sources_block}\n\n"
        "Based on the research above, here is the accurate answer:"
    )