from __future__ import annotations

from app.server import repair_workflow
from config import ROOT


def run_demo() -> dict:
    project_path = str(ROOT / "demo_projects" / "buggy_python_app")
    first = repair_workflow(
        {
            "project_id": "demo-python-app",
            "project_path": project_path,
            "problem": "My Python app crashes when I launch it.",
            "error_message": "ModuleNotFoundError: No module named 'requests'",
        }
    )
    second = repair_workflow(
        {
            "project_id": "demo-python-app",
            "project_path": project_path,
            "problem": "The same app is crashing again.",
            "error_message": "ModuleNotFoundError: No module named 'requests'",
        }
    )
    return {
        "SESSION_1_MEMORY_WRITE": first.get("memory_write", {}).get("ok", False),
        "SESSION_2_MEMORY_RECALLED": second.get("MEMORY_RECALLED", False),
        "PREVIOUS_FIX": second.get("PREVIOUS_FIX", "NONE"),
        "NEW_DECISION_CHANGED_BY_MEMORY": second.get("NEW_DECISION_CHANGED_BY_MEMORY", False),
        "MEMORY_BACKEND": second.get("memory_status", {}),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_demo(), indent=2))
