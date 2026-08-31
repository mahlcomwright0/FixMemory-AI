from __future__ import annotations

from config import Settings
from models import Diagnosis, RepairPlan


class RepairAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def plan(self, diagnosis: Diagnosis) -> RepairPlan:
        destructive = any(word in diagnosis.proposed_fix.lower() for word in ["delete", "remove directory", "wipe"])
        return RepairPlan(
            safe_to_apply=not destructive,
            requires_confirmation=destructive and self.settings.require_destructive_confirmation,
            destructive=destructive,
            patch_summary=diagnosis.proposed_fix,
            commands=["python -m py_compile <changed_files>", "python -m unittest discover -s tests"],
            files_to_change=diagnosis.files_involved,
        )
