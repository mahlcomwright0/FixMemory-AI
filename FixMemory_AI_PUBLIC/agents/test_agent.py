from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from models import TestResult


class TestAgent:
    def run_python_compile(self, project_path: str) -> TestResult:
        path = Path(project_path)
        if not path.exists():
            return TestResult("NO_PROJECT_PATH", "python -m py_compile", "Project path does not exist.")
        files = [str(item) for item in path.rglob("*.py") if "__pycache__" not in item.parts]
        if not files:
            return TestResult("NO_PYTHON_FILES", "python -m py_compile", "No Python files found.")
        with tempfile.TemporaryDirectory() as cache_dir:
            completed = subprocess.run(
                [sys.executable, "-X", f"pycache_prefix={cache_dir}", "-m", "py_compile", *files],
                capture_output=True,
                text=True,
                check=False,
            )
        output = (completed.stdout + completed.stderr).strip()
        return TestResult("PASS" if completed.returncode == 0 else "FAIL", "python -m py_compile", output)
