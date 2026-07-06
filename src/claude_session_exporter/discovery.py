# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from pathlib import Path

from claude_session_exporter import parser
from claude_session_exporter.models import Session

CLAUDE_CODE_ROOT = Path.home() / ".claude" / "projects"
COWORK_ROOT = (
    Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"
)

_SESSION_RE = re.compile(r"^(?!audit\.jsonl$|agent-).+\.jsonl$")


def _is_transcript(path: Path) -> bool:
    return bool(_SESSION_RE.match(path.name))


def _subagents_for(transcript: Path) -> list[Path]:
    sub_dir = transcript.parent / transcript.stem / "subagents"
    if not sub_dir.is_dir():
        return []
    return sorted(p for p in sub_dir.glob("agent-*.jsonl"))


def _aggregate(files: list[Path]) -> tuple[float, int]:
    mtime = 0.0
    size = 0
    for f in files:
        st = f.stat()
        mtime = max(mtime, st.st_mtime)
        size += st.st_size
    return mtime, size


def _make_session(source_type: str, transcript: Path, project: str) -> Session:
    subs = _subagents_for(transcript)
    mtime, size = _aggregate([transcript, *subs])
    project_path = parser.facts(transcript).get("cwd") or ""
    return Session(
        source_type=source_type,
        session_id=transcript.stem,
        source_file=transcript,
        project=project,
        project_path=project_path,
        subagent_files=subs,
        mtime=mtime,
        size=size,
    )


def _find_claude_code(root: Path) -> list[Session]:
    sessions: list[Session] = []
    for project_dir in sorted(p for p in root.glob("*") if p.is_dir()):
        for transcript in sorted(project_dir.glob("*.jsonl")):
            if not _is_transcript(transcript):
                continue
            cwd = parser.facts(transcript).get("cwd") or ""
            project = Path(cwd).name if cwd else project_dir.name
            sessions.append(_make_session("claude-code", transcript, project))
    return sessions


def _find_cowork(root: Path) -> list[Session]:
    sessions: list[Session] = []
    if not root.is_dir():
        return sessions
    for space_dir in sorted(p for p in root.glob("*") if p.is_dir()):
        project = space_dir.name
        for transcript in space_dir.glob("*/*/.claude/projects/*/*.jsonl"):
            if not _is_transcript(transcript):
                continue
            sessions.append(_make_session("cowork", transcript, project))
    return sessions


def find(sources: list[str], *, roots: dict[str, Path] | None = None) -> list[Session]:
    roots = roots or {}
    out: list[Session] = []
    if "claude-code" in sources:
        out.extend(_find_claude_code(roots.get("claude-code", CLAUDE_CODE_ROOT)))
    if "cowork" in sources:
        out.extend(_find_cowork(roots.get("cowork", COWORK_ROOT)))
    return out
