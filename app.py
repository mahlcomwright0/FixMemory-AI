import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# In-memory demo storage.
# Real Sibyl credentials must ONLY come from environment variables.
repair_memory = []


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FixMemory AI</title>
    <meta charset="UTF-8">
    <style>
        body {
            background: #071018;
            color: #dffaff;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 1000px;
            margin: auto;
        }

        h1 {
            color: #4deaff;
        }

        textarea {
            width: 100%;
            min-height: 120px;
            background: #0b1822;
            color: white;
            border: 1px solid #1ccde8;
            padding: 12px;
            box-sizing: border-box;
        }

        button {
            margin-top: 12px;
            padding: 12px 20px;
            background: #12bfd8;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }

        .panel {
            margin-top: 20px;
            padding: 18px;
            background: #0b1822;
            border: 1px solid #17485a;
        }

        .pass {
            color: #57ff9a;
        }

        .warning {
            color: #ffd75a;
        }

        pre {
            white-space: pre-wrap;
        }
    </style>
</head>

<body>
<div class="container">

    <h1>FixMemory AI</h1>
    <p>Persistent-memory debugging agent</p>

    <div class="panel">
        <h3>Problem / Error</h3>

        <textarea id="problem"
        placeholder="Example: My Python app crashes when I launch it."></textarea>

        <textarea id="error"
        placeholder="Example: ModuleNotFoundError: No module named 'requests'"></textarea>

        <button onclick="debugProblem()">Analyze</button>
        <button onclick="newSession()">Start Fresh Session</button>
    </div>

    <div class="panel">
        <h3>Agent Result</h3>
        <pre id="result">Waiting for debugging request...</pre>
    </div>

</div>

<script>
async function debugProblem() {
    const problem = document.getElementById("problem").value;
    const error = document.getElementById("error").value;

    const response = await fetch("/api/debug", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            problem: problem,
            error: error
        })
    });

    const data = await response.json();

    document.getElementById("result").textContent =
        JSON.stringify(data, null, 2);
}

async function newSession() {
    const response = await fetch("/api/new-session", {
        method: "POST"
    });

    const data = await response.json();

    document.getElementById("result").textContent =
        JSON.stringify(data, null, 2);
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/debug", methods=["POST"])
def debug():
    data = request.get_json(silent=True) or {}

    problem = data.get("problem", "").strip()
    error = data.get("error", "").strip()

    if not problem and not error:
        return jsonify({
            "status": "ERROR",
            "message": "Enter a problem or error."
        }), 400

    previous_attempts = [
        item for item in repair_memory
        if item["error"].lower() == error.lower()
    ]

    memory_recalled = len(previous_attempts) > 0

    if "ModuleNotFoundError" in error and "requests" in error:

        if memory_recalled:
            diagnosis = (
                "The dependency may already have been installed previously. "
                "Check whether the application is running under a different "
                "Python interpreter, virtual environment, or PATH."
            )

            next_action = (
                "Compare the interpreter used to install requests with the "
                "interpreter launching the application."
            )

            decision_changed = True

        else:
            diagnosis = (
                "The requests package is unavailable to the Python "
                "environment currently launching the application."
            )

            next_action = (
                "Verify the active Python environment and install requests "
                "into that environment if it is actually missing."
            )

            decision_changed = False

    else:
        diagnosis = (
            "Inspect the traceback, environment, and previous repair history "
            "before choosing a repair."
        )

        next_action = (
            "Collect additional diagnostic information and avoid repeating "
            "previously unsuccessful repairs."
        )

        decision_changed = memory_recalled

    record = {
        "memory_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "problem": problem,
        "error": error,
        "diagnosis": diagnosis,
        "next_action": next_action
    }

    repair_memory.append(record)

    return jsonify({
        "agent": "FixMemory AI",
        "memory_saved": True,
        "memory_recalled": memory_recalled,
        "decision_changed_by_memory": decision_changed,
        "previous_attempts_found": len(previous_attempts),
        "diagnosis": diagnosis,
        "next_action": next_action
    })


@app.route("/api/new-session", methods=["POST"])
def new_session():
    # A new logical session intentionally DOES NOT erase repair memory.
    return jsonify({
        "fresh_session": True,
        "stored_memories": len(repair_memory),
        "message": (
            "Fresh session started. Existing repair memory remains available."
        )
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "OK",
        "service": "FixMemory AI"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7870"))

    print("FixMemory AI")
    print(f"Open: http://127.0.0.1:{port}")

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False
    )
