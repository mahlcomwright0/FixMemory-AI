from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agents.diagnostic_agent import DiagnosticAgent
from config import Settings
from memory.recall_engine import RecallEngine
from memory.repair_memory import RepairMemory
from memory.sibyl_client import SibylClient
from models import BugReport, MemoryRecord


class FixMemoryTests(unittest.TestCase):
    def settings(self, root: Path) -> Settings:
        return Settings(
            sibyl_enabled=True,
            sibyl_backend="LOCAL_DEV",
            sibyl_namespace="test",
            sibyl_api_key="",
            sibyl_base_url="",
            sibyl_project_id="demo-python-app",
            sibyl_local_store=root / "memory.jsonl",
            approved_project_root=root,
            max_memory_results=5,
            require_destructive_confirmation=True,
        )

    def test_memory_write_and_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.settings(Path(tmp))
            memory = RepairMemory(SibylClient(settings))
            record = MemoryRecord(
                project_id="demo",
                bug_id="bug-1",
                error_message="ModuleNotFoundError: No module named 'requests'",
                error_type="DEPENDENCY_MISSING",
                files_involved=["app.py"],
                root_cause="Missing requests dependency.",
                fix_attempted="Add requests to requirements.txt.",
                fix_result="PASS",
                test_result="PASS",
                dependencies=["requests"],
            )
            self.assertTrue(memory.remember_repair(record)["ok"])
            found = memory.recall_relevant("demo", "requests missing module")
            self.assertEqual(found[0]["FIX_ATTEMPTED"], "Add requests to requirements.txt.")

    def test_fresh_session_recall_changes_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.settings(Path(tmp))
            first_memory = RepairMemory(SibylClient(settings))
            first_memory.remember_repair(
                MemoryRecord(
                    project_id="demo",
                    bug_id="bug-1",
                    error_message="No module named 'requests'",
                    error_type="DEPENDENCY_MISSING",
                    files_involved=["app.py"],
                    root_cause="Missing requests dependency.",
                    fix_attempted="Pin requests in requirements.txt.",
                    fix_result="PASS",
                    test_result="PASS",
                    dependencies=["requests"],
                )
            )
            second_memory = RepairMemory(SibylClient(settings))
            recall = RecallEngine(second_memory).recall("demo", "same app crashes no module requests")
            diagnosis = DiagnosticAgent().run(BugReport("demo", "same app crash", error_message="ModuleNotFoundError: No module named 'requests'"), recall)
            self.assertTrue(recall["MEMORY_RECALLED"])
            self.assertTrue(diagnosis.decision_changed_by_memory)
            self.assertIn("Pin requests", diagnosis.proposed_fix)

    def test_prior_install_attempt_changes_to_environment_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.settings(Path(tmp))
            first_memory = RepairMemory(SibylClient(settings))
            first_memory.remember_repair(
                MemoryRecord(
                    project_id="demo-python-app",
                    bug_id="bug-1",
                    error_message="ModuleNotFoundError: No module named 'requests'",
                    error_type="DEPENDENCY_MISSING",
                    files_involved=["app.py"],
                    root_cause="Missing requests dependency.",
                    fix_attempted="Install or add dependency `requests` to requirements.txt.",
                    fix_result="PASS",
                    test_result="PASS",
                    dependencies=["requests"],
                )
            )
            recall = RecallEngine(RepairMemory(SibylClient(settings))).recall(
                "demo-python-app",
                "My app still crashes after I installed requests. ModuleNotFoundError: No module named 'requests'",
            )
            diagnosis = DiagnosticAgent().run(
                BugReport(
                    "demo-python-app",
                    "My app still crashes after I installed requests.",
                    error_message="ModuleNotFoundError: No module named 'requests'",
                ),
                recall,
            )
            self.assertTrue(diagnosis.memory_recalled)
            self.assertTrue(diagnosis.previous_fix_already_attempted)
            self.assertTrue(diagnosis.decision_changed_by_memory)
            self.assertIn("virtual environment", diagnosis.root_cause)
            self.assertNotEqual(diagnosis.proposed_fix, "Install or add dependency `requests` to requirements.txt.")

    def test_missing_memory_fallback_degrades_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.settings(Path(tmp))
            settings = Settings(False, "LOCAL_DEV", "test", "", "", "demo-python-app", Path(tmp) / "memory.jsonl", Path(tmp), 5, True)
            memory = RepairMemory(SibylClient(settings))
            recall = RecallEngine(memory).recall("demo", "same app crashes no module requests")
            diagnosis = DiagnosticAgent().run(BugReport("demo", "same app crash", error_message="ModuleNotFoundError: No module named 'requests'"), recall)
            self.assertFalse(recall["MEMORY_RECALLED"])
            self.assertFalse(diagnosis.decision_changed_by_memory)

    def test_destructive_terms_require_confirmation(self) -> None:
        from agents.repair_agent import RepairAgent
        from models import Diagnosis

        with tempfile.TemporaryDirectory() as tmp:
            plan = RepairAgent(self.settings(Path(tmp))).plan(
                Diagnosis("RUNTIME_ERROR", "Bad state", [], "Delete the project directory.", "LOW", False, "", False, False)
            )
            self.assertTrue(plan.destructive)
            self.assertTrue(plan.requires_confirmation)

    def test_real_sibyl_sdk_backend_persists_across_clients(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                True,
                "REAL_SIBYL",
                "test",
                "",
                "",
                "demo-python-app",
                Path(tmp) / "real_sibyl.db",
                Path(tmp),
                5,
                True,
            )
            first_memory = RepairMemory(SibylClient(settings))
            first_memory.remember_repair(
                MemoryRecord(
                    project_id="demo-python-app",
                    bug_id="bug-real",
                    error_message="ModuleNotFoundError: No module named 'requests'",
                    error_type="DEPENDENCY_MISSING",
                    files_involved=["app.py"],
                    root_cause="Missing requests dependency.",
                    fix_attempted="Install or add dependency `requests` to requirements.txt.",
                    fix_result="PASS",
                    test_result="PASS",
                    dependencies=["requests"],
                )
            )
            second_memory = RepairMemory(SibylClient(settings))
            recall = RecallEngine(second_memory).recall(
                "demo-python-app",
                "My app still crashes after I installed requests. ModuleNotFoundError: No module named 'requests'",
            )
            diagnosis = DiagnosticAgent().run(
                BugReport("demo-python-app", "My app still crashes after I installed requests.", error_message="ModuleNotFoundError: No module named 'requests'"),
                recall,
            )
            self.assertTrue(recall["MEMORY_RECALLED"])
            self.assertTrue(diagnosis.previous_fix_already_attempted)
            self.assertTrue(diagnosis.decision_changed_by_memory)


if __name__ == "__main__":
    unittest.main()
