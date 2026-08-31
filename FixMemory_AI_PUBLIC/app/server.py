from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from agents.diagnostic_agent import DiagnosticAgent
from agents.memory_agent import MemoryAgent
from agents.repair_agent import RepairAgent
from agents.review_agent import ReviewAgent
from agents.test_agent import TestAgent
from config import ROOT, load_settings
from memory.project_history import ProjectHistory
from memory.repair_memory import RepairMemory
from memory.sibyl_client import SibylClient
from models import BugReport, MemoryRecord, within_root


STATIC = ROOT / "app" / "static"


def build_services():
    settings = load_settings()
    client = SibylClient(settings)
    repair_memory = RepairMemory(client)
    return settings, client, MemoryAgent(repair_memory), ProjectHistory(repair_memory)


def repair_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    settings, client, memory_agent, _history = build_services()
    report = BugReport(
        project_id=str(payload.get("project_id") or "demo-python-app").strip(),
        problem=str(payload.get("problem") or "").strip(),
        project_path=str(payload.get("project_path") or "").strip(),
        error_message=str(payload.get("error_message") or "").strip(),
        user_feedback=str(payload.get("user_feedback") or "").strip(),
    )
    if not report.problem and not report.error_message:
        return {"ok": False, "error": "EMPTY_PROBLEM", "answer": "Describe the bug or paste a traceback first."}
    if report.project_path and not within_root(report.project_path, settings.approved_project_root):
        return {"ok": False, "error": "PROJECT_NOT_APPROVED", "answer": "Project path is outside the approved root."}

    recall = memory_agent.recall(report.project_id, f"{report.problem} {report.error_message}")
    diagnosis = DiagnosticAgent().run(report, recall)
    plan = RepairAgent(settings).plan(diagnosis)
    test = TestAgent().run_python_compile(report.project_path) if report.project_path else TestAgent().run_python_compile(str(settings.approved_project_root))
    review = ReviewAgent().run(diagnosis, plan, test)
    record = MemoryRecord(
        project_id=report.project_id,
        bug_id=str(uuid.uuid4()),
        error_message=report.error_message or report.problem,
        error_type=diagnosis.error_type,
        files_involved=diagnosis.files_involved,
        root_cause=diagnosis.root_cause,
        fix_attempted=plan.patch_summary,
        fix_result="PROPOSED_SAFE_FIX" if plan.safe_to_apply else "CONFIRMATION_REQUIRED",
        test_result=test.status,
        dependencies=[],
        user_feedback=report.user_feedback,
    )
    write_result = memory_agent.write(record)
    return {
        "ok": True,
        "memory_status": client.status(),
        "MEMORY_RECALLED": recall.get("MEMORY_RECALLED", False),
        "PREVIOUS_FIX": recall.get("PREVIOUS_FIX", "NONE"),
        "PREVIOUS_FIX_ALREADY_ATTEMPTED": diagnosis.previous_fix_already_attempted,
        "NEW_DIAGNOSIS": diagnosis.root_cause,
        "NEW_DECISION_CHANGED_BY_MEMORY": diagnosis.decision_changed_by_memory,
        "diagnosis": asdict(diagnosis),
        "proposed_fix": asdict(plan),
        "test_results": asdict(test),
        "memory_write": write_result,
        "review": review,
        "final_report": {
            "PROJECT_ID": report.project_id,
            "ERROR_TYPE": diagnosis.error_type,
            "ROOT_CAUSE": diagnosis.root_cause,
            "MEMORY_USED": diagnosis.memory_recalled,
            "TEST_RESULT": test.status,
        },
    }


def history_response(project_id: str) -> dict[str, Any]:
    _settings, client, _memory_agent, history = build_services()
    return {"ok": True, "memory_status": client.status(), "past_fixes": history.past_fixes(project_id)}


def status_response() -> dict[str, Any]:
    settings, client, _memory_agent, _history = build_services()
    return {
        "ok": True,
        **client.status(),
        "SIBYL_STORE": "REAL_SIBYL_SQLITE" if client.backend == "REAL_SIBYL" else "LOCAL_DEV_JSONL",
        "APPROVED_PROJECT_ROOT": str(settings.approved_project_root),
    }


class FixMemoryHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._json(status_response())
            return
        if self.path.startswith("/api/history"):
            project_id = self.path.split("project_id=", 1)[-1] if "project_id=" in self.path else "demo-python-app"
            self._json(history_response(project_id))
            return
        path = STATIC / "index.html" if self.path in {"/", ""} else STATIC / self.path.lstrip("/")
        if not path.resolve().is_relative_to(STATIC.resolve()) or not path.exists():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/api/repair":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(repair_workflow(payload))
        except Exception as exc:
            self._json({"ok": False, "error": "REQUEST_FAILED", "diagnostic": type(exc).__name__}, 500)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "127.0.0.1", port: int = 7870) -> None:
    server = ThreadingHTTPServer((host, port), FixMemoryHandler)
    print(f"FixMemory AI running at http://{host}:{port}")
    server.serve_forever()
