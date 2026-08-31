from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BugReport:
    project_id: str
    problem: str
    project_path: str = ""
    error_message: str = ""
    user_feedback: str = ""


@dataclass
class MemoryRecord:
    project_id: str
    bug_id: str
    error_message: str
    error_type: str
    files_involved: list[str]
    root_cause: str
    fix_attempted: str
    fix_result: str
    test_result: str
    dependencies: list[str]
    timestamp: str = field(default_factory=utc_now)
    user_feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Diagnosis:
    error_type: str
    root_cause: str
    files_involved: list[str]
    proposed_fix: str
    confidence: str
    memory_recalled: bool
    previous_fix: str
    previous_fix_already_attempted: bool
    decision_changed_by_memory: bool


@dataclass
class RepairPlan:
    safe_to_apply: bool
    requires_confirmation: bool
    destructive: bool
    patch_summary: str
    commands: list[str] = field(default_factory=list)
    files_to_change: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    status: str
    command: str
    output: str


def within_root(path: str, root: Path) -> bool:
    if not path:
        return True
    try:
        Path(path).resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
