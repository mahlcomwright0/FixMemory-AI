from __future__ import annotations

import json
import uuid
from typing import Any

from config import Settings


class SibylClient:
    """Sibyl memory boundary.

    The preferred production path is a real Sibyl CLI/SDK. When it is not
    installed, this local-first JSONL backend keeps the app runnable and makes
    the load-bearing memory behavior testable without external credentials.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._last_write_status = "NOT_RUN"
        self._last_read_status = "NOT_RUN"
        self._last_error = ""

    @property
    def backend(self) -> str:
        return self.settings.sibyl_backend.upper()

    def status(self) -> dict[str, Any]:
        if not self.settings.sibyl_enabled:
            return self._status("DISABLED", "NONE", False, "NONE")
        if self.backend == "REAL_SIBYL":
            client = self._real_client()
            connected = client is not None
            return self._status("CONNECTED" if connected else "OFFLINE", "REAL_SIBYL", connected, "SIBYL" if connected else "NONE")
        if self.backend == "LOCAL_DEV":
            return self._status("LOCAL_DEV_BACKEND", "LOCAL_DEV", True, "LOCAL_JSONL")
        return self._status("OFFLINE", self.backend, False, "NONE")

    def write(self, record: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.sibyl_enabled:
            self._last_write_status = "MEMORY_DISABLED"
            return {"ok": False, "status": "MEMORY_DISABLED", "source": "NONE"}
        if self.backend == "REAL_SIBYL":
            return self._write_real_sibyl(record)
        if self.backend != "LOCAL_DEV":
            self._last_write_status = "SIBYL_OFFLINE"
            return {"ok": False, "status": "SIBYL_OFFLINE", "source": "NONE"}
        return self._write_local(record)

    def search(self, query: str, project_id: str = "", limit: int | None = None) -> list[dict[str, Any]]:
        if not self.settings.sibyl_enabled:
            self._last_read_status = "MEMORY_DISABLED"
            return []
        limit = limit or self.settings.max_memory_results
        if self.backend == "REAL_SIBYL":
            return self._search_real_sibyl(query, project_id, limit)
        if self.backend != "LOCAL_DEV":
            self._last_read_status = "SIBYL_OFFLINE"
            return []
        return self._search_local(query, project_id, limit)

    def _real_client(self) -> Any | None:
        try:
            from sibyl_memory_client import MemoryClient

            self.settings.sibyl_local_store.parent.mkdir(parents=True, exist_ok=True)
            return MemoryClient.local(self.settings.sibyl_local_store)
        except Exception as exc:
            self._last_error = type(exc).__name__
            return None

    def _write_real_sibyl(self, record: dict[str, Any]) -> dict[str, Any]:
        client = self._real_client()
        if client is None:
            self._last_write_status = "SIBYL_OFFLINE"
            return {"ok": False, "status": "SIBYL_OFFLINE", "source": "NONE"}
        name = f"{record.get('PROJECT_ID', 'unknown')}:{record.get('BUG_ID') or uuid.uuid4()}"
        try:
            client.set_entity("repair_memory", name, record, status=record.get("FIX_RESULT", "RECORDED"))
            client.write_event(
                evaluated={"project_id": record.get("PROJECT_ID"), "error_type": record.get("ERROR_TYPE")},
                acted={"fix_attempted": record.get("FIX_ATTEMPTED"), "fix_result": record.get("FIX_RESULT")},
                extra={"namespace": self.settings.sibyl_namespace, "bug_id": record.get("BUG_ID")},
            )
        except Exception as exc:
            self._last_error = type(exc).__name__
            self._last_write_status = "MEMORY_WRITE_FAILED"
            return {"ok": False, "status": "MEMORY_WRITE_FAILED", "source": "SIBYL", "error_type": type(exc).__name__}
        finally:
            self._close_client(client)
        self._last_write_status = "OK"
        return {"ok": True, "status": "REAL_SIBYL", "source": "SIBYL"}

    def _search_real_sibyl(self, query: str, project_id: str, limit: int) -> list[dict[str, Any]]:
        client = self._real_client()
        if client is None:
            self._last_read_status = "SIBYL_OFFLINE"
            return []
        try:
            entities = client.list_entities(category="repair_memory", limit=500)
        except Exception as exc:
            self._last_error = type(exc).__name__
            self._last_read_status = "MEMORY_READ_FAILED"
            return []
        finally:
            self._close_client(client)
        records = self._rank_entities(entities, query, project_id, limit)
        self._last_read_status = "OK" if records else "NO_RELEVANT_MEMORY"
        return records

    def _rank_entities(self, entities: list[dict[str, Any]], query: str, project_id: str, limit: int) -> list[dict[str, Any]]:
        terms = {term.lower() for term in query.split() if len(term) > 2}
        matches: list[tuple[int, str, dict[str, Any]]] = []
        for entity in entities:
            body = entity.get("body", {}) if isinstance(entity, dict) else {}
            if not isinstance(body, dict):
                continue
            if project_id and body.get("PROJECT_ID") != project_id:
                continue
            haystack = json.dumps(body, ensure_ascii=True).lower()
            score = sum(1 for term in terms if term in haystack)
            if score or not terms:
                matches.append((score, body.get("TIMESTAMP", entity.get("updated_at", "")), {**body, "MEMORY_SOURCE": "SIBYL", "SIBYL_ENTITY_ID": entity.get("id")}))
        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [record for _, _, record in matches[:limit]]

    def _write_local(self, record: dict[str, Any]) -> dict[str, Any]:
        self.settings.sibyl_local_store.parent.mkdir(parents=True, exist_ok=True)
        with self.settings.sibyl_local_store.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        self._last_write_status = "OK"
        return {"ok": True, "status": "LOCAL_DEV_BACKEND", "source": "LOCAL_JSONL", "path": str(self.settings.sibyl_local_store)}

    def _search_local(self, query: str, project_id: str, limit: int) -> list[dict[str, Any]]:
        path = self.settings.sibyl_local_store
        if not path.exists():
            return []
        terms = {term.lower() for term in query.split() if len(term) > 2}
        matches: list[tuple[int, dict[str, Any]]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if project_id and record.get("PROJECT_ID") != project_id and record.get("project_id") != project_id:
                continue
            haystack = json.dumps(record, ensure_ascii=True).lower()
            score = sum(1 for term in terms if term in haystack)
            if score or not terms:
                matches.append((score, record))
        matches.sort(key=lambda item: (item[0], item[1].get("TIMESTAMP", item[1].get("timestamp", ""))), reverse=True)
        self._last_read_status = "OK" if matches else "NO_RELEVANT_MEMORY"
        return [record for _, record in matches[:limit]]

    def _status(self, memory: str, backend: str, connected: bool, source: str) -> dict[str, Any]:
        return {
            "SIBYL_MEMORY": memory,
            "SIBYL_STATUS": "CONNECTED" if connected else memory,
            "SIBYL_ENABLED": self.settings.sibyl_enabled,
            "SIBYL_BACKEND": backend,
            "SIBYL_CONNECTED": connected,
            "MEMORY_WRITE_STATUS": self._last_write_status,
            "MEMORY_READ_STATUS": self._last_read_status,
            "MEMORY_SOURCE": source,
            "LAST_ERROR": self._last_error or "NONE",
        }

    def _close_client(self, client: Any) -> None:
        try:
            client.storage.close()
        except Exception:
            return
