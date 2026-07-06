# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

from claude_session_exporter.models import Session

MANIFEST_NAME = ".claude-export-manifest.json"


class Manifest:
    def __init__(self, output_dir: Path, data: dict):
        self.output_dir = output_dir
        self._data = data

    @classmethod
    def load(cls, output_dir: Path) -> "Manifest":
        path = output_dir / MANIFEST_NAME
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}
        data.setdefault("version", 1)
        data.setdefault("sessions", {})
        return cls(output_dir, data)

    def _entry(self, session_id: str) -> dict | None:
        return self._data["sessions"].get(session_id)

    def classify(self, session: Session) -> str:
        entry = self._entry(session.session_id)
        if entry is None:
            return "new"
        if entry.get("mtime") != session.mtime or entry.get("size") != session.size:
            return "updated"
        return "unchanged"

    def output_path_for(self, session_id: str) -> str | None:
        entry = self._entry(session_id)
        return entry.get("output_path") if entry else None

    def claimed_paths(self, exclude_session_id: str) -> set[str]:
        return {
            e["output_path"]
            for sid, e in self._data["sessions"].items()
            if sid != exclude_session_id and e.get("output_path")
        }

    def update(self, session: Session, output_path: Path, title: str) -> None:
        self._data["sessions"][session.session_id] = {
            "source_file": str(session.source_file),
            "mtime": session.mtime,
            "size": session.size,
            "output_path": str(output_path),
            "title": title,
        }

    def save(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / MANIFEST_NAME
        path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
