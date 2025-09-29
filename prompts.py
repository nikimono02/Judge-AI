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
def build_historian_prompt_with_sources(text: str, sources: List[Dict]) -> str:
    """Historian prompt when we already fetched web sources.

    We show a numbered list of sources and ask the historian to cite [n].
    """
    sources_block_lines = []
    for idx, src in enumerate(sources, start=1):
        title = src.get("title", "Untitled")
        url = src.get("url", "")
        snippet = src.get("snippet", "")
        sources_block_lines.append(f"[{idx}] {title} — {url}\n{snippet}")
    sources_block = "\n\n".join(sources_block_lines) if sources_block_lines else "(no sources)"
    return (
        "You are a rigorous history expert. Use primary sources below.\n"
        "- Verify claims, correct inaccuracies, and be concise (<= 80 words).\n"
        "- Cite inline with [n] markers tied to Sources.\n"
        f"TEXT TO REVIEW: {text}\n\n"
        f"Sources:\n{sources_block}\n\n"
        "Corrections with citations:"
    )