from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    @staticmethod
    def _digest(record: dict) -> str:
        unsigned = {key: value for key, value in record.items() if key != "hash"}
        raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def append(self, event: str, payload: dict) -> dict:
        records = self._records()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
            "previous_hash": records[-1]["hash"] if records else "GENESIS",
        }
        record["hash"] = self._digest(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def verify(self) -> dict:
        previous = "GENESIS"
        for index, record in enumerate(self._records()):
            if record.get("previous_hash") != previous or record.get("hash") != self._digest(record):
                return {"ok": False, "record": index}
            previous = record["hash"]
        return {"ok": True, "records": len(self._records()), "tip": previous}
