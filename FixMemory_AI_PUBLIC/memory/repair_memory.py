from __future__ import annotations

from dataclasses import asdict
from typing import Any

from memory.sibyl_client import SibylClient
from models import MemoryRecord


class RepairMemory:
    def __init__(self, client: SibylClient) -> None:
        self.client = client

    def remember_repair(self, record: MemoryRecord) -> dict[str, Any]:
        payload = {
            "PROJECT_ID": record.project_id,
            "BUG_ID": record.bug_id,
            "ERROR_MESSAGE": record.error_message,
            "ERROR_TYPE": record.error_type,
            "FILES_INVOLVED": record.files_involved,
            "ROOT_CAUSE": record.root_cause,
            "FIX_ATTEMPTED": record.fix_attempted,
            "FIX_RESULT": record.fix_result,
            "TEST_RESULT": record.test_result,
            "DEPENDENCIES": record.dependencies,
            "TIMESTAMP": record.timestamp,
            "USER_FEEDBACK": record.user_feedback,
        }
        return self.client.write(payload)

    def recall_relevant(self, project_id: str, problem: str) -> list[dict[str, Any]]:
        return self.client.search(problem, project_id=project_id)
