# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Message:
    role: str  # "user" | "assistant"
    timestamp: str | None
    text: str
    tool_notes: list[str] = field(default_factory=list)


@dataclass
class Subagent:
    label: str
    messages: list[Message]


@dataclass
class Session:
    source_type: str  # "claude-code" | "cowork"
    session_id: str
    source_file: Path
    project: str
    project_path: str
    subagent_files: list[Path] = field(default_factory=list)
    mtime: float = 0.0
    size: int = 0


@dataclass
class Report:
    exported: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
