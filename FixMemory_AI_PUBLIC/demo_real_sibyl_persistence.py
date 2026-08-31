from __future__ import annotations

import json
import sys

from app.server import repair_workflow
from config import ROOT


PROJECT_ID = "demo-python-app"
PROJECT_PATH = str(ROOT / "demo_projects" / "buggy_python_app")
ERROR = "ModuleNotFoundError: No module named 'requests'"


def session_one() -> dict:
    result = repair_workflow(
        {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "problem": "My Python app crashes when I launch it.",
            "error_message": ERROR,
        }
    )
    return {
        "SIBYL_MEMORY": result["memory_status"]["SIBYL_MEMORY"],
        "SIBYL_BACKEND": result["memory_status"]["SIBYL_BACKEND"],
        "MEMORY_SOURCE": result["memory_status"]["MEMORY_SOURCE"],
        "REAL_SIBYL_WRITE": result["memory_write"]["ok"],
    }


def session_two() -> dict:
    result = repair_workflow(
        {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "problem": "My app still crashes after I installed requests.",
            "error_message": ERROR,
        }
    )
    proposed_fix = result["proposed_fix"]["patch_summary"]
    return {
        "SIBYL_MEMORY": result["memory_status"]["SIBYL_MEMORY"],
        "SIBYL_BACKEND": result["memory_status"]["SIBYL_BACKEND"],
        "MEMORY_SOURCE": result["memory_status"]["MEMORY_SOURCE"],
        "MEMORY_RECALLED": result["MEMORY_RECALLED"],
        "PREVIOUS_FIX_FOUND": result["PREVIOUS_FIX"] != "NONE",
        "PREVIOUS_FIX_ALREADY_ATTEMPTED": result["PREVIOUS_FIX_ALREADY_ATTEMPTED"],
        "REPEATED_FIX_AVOIDED": "Do not repeat the old install-only fix" in proposed_fix,
        "NEW_DIAGNOSIS": result["NEW_DIAGNOSIS"],
        "NEW_DECISION_CHANGED_BY_MEMORY": result["NEW_DECISION_CHANGED_BY_MEMORY"],
        "MEMORY_WRITE_BACK": result["memory_write"]["ok"],
        "TEST_RESULT": result["test_results"]["status"],
    }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    if mode == "session1":
        print(json.dumps(session_one(), indent=2))
    elif mode == "session2":
        print(json.dumps(session_two(), indent=2))
    else:
        print(json.dumps({"SESSION_1": session_one(), "SESSION_2": session_two()}, indent=2))
