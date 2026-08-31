from __future__ import annotations

from models import Diagnosis, RepairPlan, TestResult


class ReviewAgent:
    def run(self, diagnosis: Diagnosis, plan: RepairPlan, test: TestResult) -> dict:
        supported = bool(diagnosis.root_cause and plan.patch_summary)
        return {
            "SUPPORTED_BY_EVIDENCE": supported,
            "DESTRUCTIVE_ACTION_BLOCKED": plan.destructive and plan.requires_confirmation,
            "TEST_STATUS": test.status,
            "READY_FOR_USER_CONFIRMATION": plan.requires_confirmation,
        }
