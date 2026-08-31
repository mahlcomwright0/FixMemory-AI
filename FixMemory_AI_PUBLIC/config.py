from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    sibyl_enabled: bool
    sibyl_backend: str
    sibyl_namespace: str
    sibyl_api_key: str
    sibyl_base_url: str
    sibyl_project_id: str
    sibyl_local_store: Path
    approved_project_root: Path
    max_memory_results: int
    require_destructive_confirmation: bool


def load_settings() -> Settings:
    load_dotenv()
    local_store = Path(os.getenv("SIBYL_LOCAL_STORE", DATA_DIR / "sibyl_memory" / "repair_memory.jsonl"))
    sibyl_store = Path(os.getenv("SIBYL_STORE_PATH", DATA_DIR / "sibyl_memory" / "real_sibyl_memory.db"))
    backend = os.getenv("SIBYL_MEMORY_BACKEND", os.getenv("SIBYL_BACKEND", "REAL_SIBYL"))
    return Settings(
        sibyl_enabled=_bool_env("SIBYL_ENABLED", _bool_env("SIBYL_MEMORY_ENABLED", True)),
        sibyl_backend=backend,
        sibyl_namespace=os.getenv("SIBYL_NAMESPACE", "fixmemory-ai"),
        sibyl_api_key=os.getenv("SIBYL_API_KEY", ""),
        sibyl_base_url=os.getenv("SIBYL_BASE_URL", ""),
        sibyl_project_id=os.getenv("SIBYL_PROJECT_ID", "demo-python-app"),
        sibyl_local_store=(
            sibyl_store if sibyl_store.is_absolute() else ROOT / sibyl_store
        ) if backend.upper() == "REAL_SIBYL" else (
            local_store if local_store.is_absolute() else ROOT / local_store
        ),
        approved_project_root=Path(os.getenv("APPROVED_PROJECT_ROOT", ROOT / "demo_projects")).resolve(),
        max_memory_results=int(os.getenv("MAX_MEMORY_RESULTS", "5")),
        require_destructive_confirmation=_bool_env("REQUIRE_DESTRUCTIVE_CONFIRMATION", True),
    )
