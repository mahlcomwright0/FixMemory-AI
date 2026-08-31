from __future__ import annotations

import re

from models import BugReport, Diagnosis


class DiagnosticAgent:
    def run(self, report: BugReport, recall: dict) -> Diagnosis:
        text = f"{report.problem}\n{report.error_message}".strip()
        memory_used = bool(recall.get("MEMORY_RECALLED"))
        previous_fix = recall.get("PREVIOUS_FIX", "")
        lower = text.lower()
        previous_fix_lower = previous_fix.lower()
        files = re.findall(r"File \"([^\"]+)\"", text)
        previous_fix_already_attempted = False

        if "modulenotfounderror" in lower or "no module named" in lower:
            missing = self._extract_missing_module(text)
            prior_install_attempt = (
                memory_used
                and missing
                and missing.lower() in previous_fix_lower
                and any(word in previous_fix_lower for word in ["install", "add", "pin", "requirements"])
            )
            if prior_install_attempt and any(phrase in lower for phrase in ["still crashes", "still failing", "after i installed", "after installing"]):
                previous_fix_already_attempted = True
                root = (
                    f"`{missing}` is still missing after the remembered dependency fix, so the likely cause is "
                    "an interpreter, virtual environment, PATH, or deployment environment mismatch rather than a first-time missing package."
                )
                fix = (
                    f"Do not repeat the old install-only fix. Verify the exact Python executable that launches the app, "
                    f"run `python -m pip show {missing}` in that same environment, apply requirements.txt to that interpreter, "
                    "and rebuild/restart the active virtual environment."
                )
            else:
                root = f"Missing Python dependency: {missing or 'unknown module'}."
                fix = f"Install or add dependency `{missing}` to requirements.txt." if missing else "Inspect missing dependency and update requirements.txt."
            error_type = "DEPENDENCY_MISSING"
        elif "syntaxerror" in lower:
            root = "Python syntax error in the reported file."
            fix = "Patch the syntax error in the indicated source file, then run py_compile."
            error_type = "SYNTAX_ERROR"
        elif "keyerror" in lower:
            root = "Configuration or dictionary key is missing at runtime."
            fix = "Add safe defaults and validate required config keys before use."
            error_type = "BAD_CONFIGURATION"
        else:
            root = "General Python runtime failure. More traceback context may be needed."
            fix = "Run tests, inspect traceback, and make the smallest safe repair."
            error_type = "RUNTIME_ERROR"

        changed = False
        if memory_used and previous_fix:
            if previous_fix_already_attempted:
                changed = True
            else:
                fix = f"Use remembered prior fix first: {previous_fix}. Then verify against the current traceback."
                changed = True

        return Diagnosis(
            error_type=error_type,
            root_cause=root,
            files_involved=files,
            proposed_fix=fix,
            confidence="HIGH" if error_type != "RUNTIME_ERROR" else "MEDIUM",
            memory_recalled=memory_used,
            previous_fix=previous_fix,
            previous_fix_already_attempted=previous_fix_already_attempted,
            decision_changed_by_memory=changed,
        )

    def _extract_missing_module(self, text: str) -> str:
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", text, re.I)
        return match.group(1) if match else ""
