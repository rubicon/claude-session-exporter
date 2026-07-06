# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

from claude_session_exporter.models import Message

_TOOL_INPUT_MAX = 300
_TOOL_RESULT_MAX = 200


def _extract(content) -> tuple[str, list[str]]:
    texts: list[str] = []
    notes: list[str] = []
    if isinstance(content, str):
        texts.append(content)
    elif isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype == "text":
                texts.append(part.get("text", ""))
            elif ptype == "tool_use":
                inp = json.dumps(part.get("input", {}), ensure_ascii=False)
                if len(inp) > _TOOL_INPUT_MAX:
                    inp = inp[:_TOOL_INPUT_MAX] + "…"
                notes.append(f"tool call `{part.get('name', '?')}` — {inp}")
            elif ptype == "tool_result":
                body = part.get("content") or ""
                if isinstance(body, list):
                    body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                body = str(body).strip().replace("\n", " ")
                if len(body) > _TOOL_RESULT_MAX:
                    body = body[:_TOOL_RESULT_MAX] + "…"
                notes.append(f"tool result: {body}")
    text = "\n\n".join(t for t in texts if t.strip())
    return text, notes


def _records(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def parse(path: Path) -> list[Message]:
    messages: list[Message] = []
    for rec in _records(path):
        if rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message") or {}
        text, notes = _extract(msg.get("content"))
        if not text and not notes:
            continue
        messages.append(
            Message(
                role=rec["type"],
                timestamp=rec.get("timestamp"),
                text=text,
                tool_notes=notes,
            )
        )
    return messages


def facts(path: Path) -> dict:
    cwd: str | None = None
    created: str | None = None
    updated: str | None = None
    for rec in _records(path):
        if cwd is None and rec.get("cwd"):
            cwd = rec["cwd"]
        ts = rec.get("timestamp")
        if ts:
            if created is None:
                created = ts
            updated = ts
    return {"cwd": cwd, "created": created, "updated": updated}
