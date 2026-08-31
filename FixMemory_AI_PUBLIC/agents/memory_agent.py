from __future__ import annotations

from memory.recall_engine import RecallEngine
from memory.repair_memory import RepairMemory
from models import MemoryRecord


class MemoryAgent:
    def __init__(self, repair_memory: RepairMemory) -> None:
        self.repair_memory = repair_memory
        self.recall_engine = RecallEngine(repair_memory)

    def recall(self, project_id: str, problem: str) -> dict:
        return self.recall_engine.recall(project_id, problem)

    def write(self, record: MemoryRecord) -> dict:
        return self.repair_memory.remember_repair(record)
