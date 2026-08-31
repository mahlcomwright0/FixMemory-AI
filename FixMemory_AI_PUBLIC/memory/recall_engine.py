from __future__ import annotations

from memory.repair_memory import RepairMemory


class RecallEngine:
    def __init__(self, memory: RepairMemory) -> None:
        self.memory = memory

    def recall(self, project_id: str, problem: str) -> dict:
        memories = self.memory.recall_relevant(project_id, problem)
        if not memories:
            return {"MEMORY_RECALLED": False, "memories": [], "summary": "No relevant repair memory found."}
        top = memories[0]
        previous_fix = top.get("FIX_ATTEMPTED") or top.get("fix_attempted") or "UNKNOWN"
        root_cause = top.get("ROOT_CAUSE") or top.get("root_cause") or "UNKNOWN"
        return {
            "MEMORY_RECALLED": True,
            "memories": memories,
            "summary": f"Previous repair remembered: {root_cause}. Prior fix: {previous_fix}",
            "PREVIOUS_FIX": previous_fix,
        }
