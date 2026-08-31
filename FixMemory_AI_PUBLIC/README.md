# FixMemory AI

FixMemory AI is a Sibyl Labs Hackathon project: a Python debugging and repair assistant whose core behavior depends on persistent repair memory across separate sessions.

It is separate from ACE, Ultron, and StormSight.

## What It Does

FixMemory AI helps with recurring Python software failures. It remembers previous bugs, root causes, repair attempts, test results, dependency problems, and user feedback. On later sessions, it recalls relevant history and changes its diagnosis or repair plan when that history applies.

## Target User

Developers, students, and builders who repeatedly debug the same app across many sessions and want the assistant to stop forgetting what was already tried.

## Architecture

User problem -> Memory Recall -> Diagnostic Agent -> Repair Agent -> Test Agent -> Memory Write -> Review Agent -> Final Report.

Agents:

- Diagnostic Agent: identifies likely Python bug category.
- Repair Agent: proposes safe fixes and blocks destructive work.
- Test Agent: runs validation against approved Python project folders.
- Memory Agent: writes and retrieves repair memory.
- Review Agent: checks whether the recommendation is supported by evidence.

## Sibyl Memory Files

Sibyl client boundary:

- `memory/sibyl_client.py`

Real Sibyl SDK calls are in `memory/sibyl_client.py`:

- `MemoryClient.local(...)`
- `set_entity("repair_memory", ...)`
- `write_event(...)`
- `list_entities(category="repair_memory", ...)`

Memory writes:

- `memory/repair_memory.py`
- `agents/memory_agent.py`
- `app/server.py` in `repair_workflow()`

Memory reads:

- `memory/recall_engine.py`
- `memory/project_history.py`
- `agents/memory_agent.py`
- `app/server.py` in `repair_workflow()` and `history_response()`

The real Sibyl SDK store is:

- `data/sibyl_memory/real_sibyl_memory.db`

The explicit local JSONL fallback store is:

- `data/sibyl_memory/repair_memory.jsonl`

Both stores are ignored by Git because they can contain private project history.

## Why Memory Is Load-Bearing

The workflow starts with memory recall before diagnosis. If relevant memory is found and the user says the app still fails after the previous fix, `DiagnosticAgent` avoids repeating that fix and pivots to the next likely cause. For the demo `requests` failure, remembered dependency repair changes the new diagnosis toward interpreter, virtual environment, PATH, or stale environment mismatch. The UI reports:

- `MEMORY_RECALLED`
- `PREVIOUS_FIX`
- `PREVIOUS_FIX_ALREADY_ATTEMPTED`
- `NEW_DECISION_CHANGED_BY_MEMORY`

If memory is disabled or deleted, those values fall back to no recall and the agent returns a generic diagnosis.

## Fresh-Session Demo

1. Start the app.
2. Use the default demo problem: `ModuleNotFoundError: No module named 'requests'`.
3. Run the workflow once.
4. Stop the server.
5. Start the server again.
6. Run the same or related bug again.
7. Confirm the Memory Recall panel shows `MEMORY_RECALLED=true`.
8. Confirm `NEW_DECISION_CHANGED_BY_MEMORY=true`.

The fresh-session recall portion should be shown in one continuous unedited demo segment.

## Setup

Use Python 3.11 or newer.

```powershell
cd FixMemory_AI
copy .env.example .env
python main.py
```

Open:

```text
http://127.0.0.1:7870
```

## Production Sibyl Setup

Install the official Sibyl Memory client, then keep:

```text
SIBYL_ENABLED=true
SIBYL_MEMORY_BACKEND=REAL_SIBYL
SIBYL_NAMESPACE=fixmemory-ai
SIBYL_STORE_PATH=data/sibyl_memory/real_sibyl_memory.db
```

`memory/sibyl_client.py` uses the official `sibyl-memory-client` package. In hackathon mode, FixMemory does not silently fall back to local JSONL. If the real Sibyl SDK is unavailable, diagnostics show `SIBYL_STATUS=OFFLINE`.

Run the real persistence proof:

```powershell
python .\demo_real_sibyl_persistence.py session1
python .\demo_real_sibyl_persistence.py session2
```

Expected session 2:

```text
MEMORY_SOURCE=SIBYL
MEMORY_RECALLED=true
PREVIOUS_FIX_ALREADY_ATTEMPTED=true
REPEATED_FIX_AVOIDED=true
NEW_DECISION_CHANGED_BY_MEMORY=true
```

## Prior Work Declaration

This repository is a new project scaffold created for the Sibyl Labs Hackathon. It does not copy ACE, Ultron, or StormSight source code.

## Public Repo Safety

Do not commit:

- `.env`
- API keys
- private repair memories
- user projects containing secrets
- private data under `data/`

## Tests

```powershell
python -m unittest discover -s tests
```

## Demo Video Plan

1. Show a Python app bug.
2. Run FixMemory diagnosis.
3. Show the repair plan.
4. Show memory persisted.
5. Close the server.
6. Reopen a fresh server session.
7. Run a related bug.
8. Show memory recall changes the new decision.
