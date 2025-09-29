"""
Very simple server that streams three things to the browser in order:
1) Creative answer text
2) Web search evidence (to validate the creative answer)
3) Historian feedback with citations

Flow:
  user message -> creative answer -> web search validate creative -> historian feedback
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask import stream_with_context
import json
import os

# Import helper that calls Tavily web search
from research import run_tavily_search

# Create a minimal Flask app that serves static files and one API endpoint
app = Flask(__name__, static_folder=".", template_folder=".")


def sse_format(event: str, data_obj) -> str:
    """Helper: build a single Server-Sent Events (SSE) message.

    The browser listens for these events and updates the UI live.
    """
    return f"event: {event}\n" + f"data: {json.dumps(data_obj, ensure_ascii=False)}\n\n"


@app.route("/")
def index():
    """Serve the main HTML page (UI)."""
    return send_from_directory(".", "index.html")


@app.route("/app.js")
def send_js():
    """Serve the front-end JavaScript."""
    return send_from_directory(".", "app.js")


@app.route("/styles.css")
def send_css():
    """Serve the page styles."""
    return send_from_directory(".", "styles.css")


@app.route("/api/stream", methods=["POST"])
def api_stream():
    """API: stream creative answer, validation evidence, and historian feedback.

    We keep this simple: validate inputs, then stream results step-by-step.
    """
    data = request.get_json(silent=True) or {}
    user_fact = (data.get("message") or "").strip()
    if not user_fact:
        return jsonify({"error": "message is required"}), 400

    @stream_with_context
    def generate():
        """Generator that yields SSE messages in three stages."""
        try:
            # 1) CREATIVE ANSWER
            # Decide if the user asked for a list (changes the prompt style)
            creative_text = []
            wants_list = any(kw in user_fact.lower() for kw in ["list", "name all", "enumerate", "show all", "give all", "all "])
            
            from prompts import build_creative_prompt
            creative_prompt = build_creative_prompt(user_fact, list_mode=wants_list)
            
            # Try to import/connect to Ollama. If not available, bail gracefully.
            try:
                import ollama
            except Exception as e:
                yield sse_format("error", {"message": f"Ollama not available: {str(e)}"})
                return
            # Stream the creative answer as it is generated
            for chunk in ollama.generate(
                model="llama3",
                prompt=creative_prompt,
                options={"temperature": 0.9},
                stream=True
            ):
                piece = chunk.get("response", "")
                if piece:
                    creative_text.append(piece)
                    yield sse_format("creative", {"delta": piece})

            full_creative = "".join(creative_text)
            yield sse_format("creative_done", {"text": full_creative})

            # 2) WEB SEARCH VALIDATION
            # Build a simple combined query using BOTH the user's input
            # and the generated creative answer. This helps search engines
            # find sources that match the exact claim being made.
            combined_query = (user_fact + "\n" + full_creative).strip()
            evidences = run_tavily_search(combined_query, max_results=5)
            # Stream each evidence item to the UI
            for ev in evidences:
                yield sse_format("evidence", ev)
            yield sse_format("research_done", {"count": len(evidences)})

            # 3) HISTORIAN FEEDBACK
            # Build a historian prompt. If we have sources, the historian cites them.
            # We pass the creative answer so historian can correct it and attach citations.
            from prompts import build_historian_prompt_with_sources, build_historian_prompt
            historian_prompt = build_historian_prompt_with_sources(full_creative, evidences) if evidences else build_historian_prompt(full_creative)
            
            # Stream the historian's feedback as it is generated
            for chunk in ollama.generate(
                model="llama3",
                prompt=historian_prompt,
                options={"temperature": 0.1},
                stream=True
            ):
                piece = chunk.get("response", "")
                if piece:
                    yield sse_format("historian", {"delta": piece})

            yield sse_format("historian_done", {"ok": True})

        except Exception as e:
            # If anything breaks, send an error event instead of crashing the stream
            yield sse_format("error", {"message": str(e)})

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    # Start the local development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)