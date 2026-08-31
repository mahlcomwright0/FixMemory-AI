from __future__ import annotations

from memory.repair_memory import RepairMemory


class ProjectHistory:
    def __init__(self, memory: RepairMemory) -> None:
        self.memory = memory

    def past_fixes(self, project_id: str) -> list[dict]:
        return self.memory.recall_relevant(project_id, "")
