"""
Flow: User input -> creative answer -> historian analyzes both + web search -> constructive feedback with sources
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask import stream_with_context
import json
import os
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
        """Generator that yields SSE messages for creative and historian."""
        try:
            import ollama
            
            # 1) Creative answer
            wants_list = "list" in user_fact.lower() or "all" in user_fact.lower()
            from prompts import build_creative_prompt
            creative_prompt = build_creative_prompt(user_fact, list_mode=wants_list)
            
            creative_text = []
            for chunk in ollama.generate(model="llama3", prompt=creative_prompt, options={"temperature": 0.9}, stream=True):
                piece = chunk.get("response", "")
                if piece:
                    creative_text.append(piece)
                    yield sse_format("creative", {"delta": piece})

            full_creative = "".join(creative_text)

            # 2) Smart historian with research
            search_query = f"{user_fact} latest news 2025 current information"
            evidences = run_tavily_search(search_query, max_results=5)
            
            from prompts import build_smart_historian_prompt
            historian_prompt = build_smart_historian_prompt(user_fact, full_creative, evidences)
            
            for chunk in ollama.generate(model="llama3", prompt=historian_prompt, options={"temperature": 0.1}, stream=True):
                piece = chunk.get("response", "")
                if piece:
                    yield sse_format("historian", {"delta": piece})

        except Exception as e:
            yield sse_format("error", {"message": str(e)})

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    # Start the local development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)