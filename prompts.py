"""
Small helpers that build the text prompts sent to the AI models.

We keep two roles:
- Creative: writes the first answer (a paragraph or a bullet list)
- Historian: checks and corrects, optionally citing sources
"""

from typing import List, Dict

def build_creative_prompt(user_fact: str, list_mode: bool = False) -> str:
    """Create the creative-role prompt.

    If list_mode=True, we ask for a clean bullet list.
    Otherwise we ask for a short paragraph.
    """
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

def build_historian_prompt(text: str) -> str:
    """Historian prompt when we do not have web sources yet."""
    return (
        "You are a rigorous history expert. Be terse and corrective.\n"
        "- If inaccurate, state the fix in 1-2 short sentences (<= 50 words).\n"
        f"TEXT TO REVIEW: {text}\n\n"
        "Corrections:"
    )
def build_historian_prompt_with_sources(user_input: str, creative_answer: str, sources: List[Dict]) -> str:
    """Historian prompt when we have web sources.

    The historian analyzes both the user's original question and the creative answer,
    then provides constructive feedback with citations.
    """
    sources_block_lines = []
    for idx, src in enumerate(sources, start=1):
        title = src.get("title", "Untitled")
        url = src.get("url", "")
        snippet = src.get("snippet", "")
        sources_block_lines.append(f"[{idx}] {title} — {url}\n{snippet}")
    sources_block = "\n\n".join(sources_block_lines) if sources_block_lines else "(no sources)"
    return (
        "You are a history expert. Your job is to provide ACCURATE current information.\n"
        "- CRITICAL: The web sources below are MORE CURRENT than your training data.\n"
        "- If sources show information that differs from your knowledge, the sources are CORRECT.\n"
        "- For current events, ALWAYS trust recent web sources over outdated training data.\n"
        "- Give a direct, confident answer based on the sources provided.\n"
        "- Be concise (<= 80 words) and cite sources with [n] markers.\n\n"
        f"USER QUESTION: {user_input}\n\n"
        f"CREATIVE ANSWER: {creative_answer}\n\n"
        f"SOURCES:\n{sources_block}\n\n"
        "Based on the sources above, the correct answer is:"
    )