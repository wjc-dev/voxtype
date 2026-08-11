"""Private bounded storage for recognized text that could not be committed."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .runtime_paths import RECOVERY_FILE


class RecoveryStore:
    def __init__(self, path: Optional[Path] = None, limit: int = 5) -> None:
        configured = os.getenv("RECOVERY_STORE_FILE", "").strip()
        self.path = path or (Path(configured).expanduser() if configured else RECOVERY_FILE)
        self.limit = max(1, min(20, limit))
        self._lock = threading.RLock()

    def load(self) -> list[dict[str, str]]:
        with self._lock:
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                return []
            if not isinstance(data, list):
                return []
            return [entry for entry in data if isinstance(entry, dict)][: self.limit]

    def add(self, text: str, reason: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        with self._lock:
            entries = self.load()
            entries.insert(
                0,
                {
                    "id": uuid.uuid4().hex,
                    "text": text,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).astimezone().isoformat(
                        timespec="seconds"
                    ),
                },
            )
            self._save(entries[: self.limit])

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            entries = self.load()
            updated = [entry for entry in entries if entry.get("id") != entry_id]
            if len(updated) == len(entries):
                return False
            self._save(updated)
            return True

    def clear(self) -> None:
        with self._lock:
            self._save([])

    def _save(self, entries: list[dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(entries, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, self.path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
