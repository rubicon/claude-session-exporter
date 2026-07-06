# SPDX-License-Identifier: MIT
from __future__ import annotations

from datetime import datetime

from claude_session_exporter import __version__
from claude_session_exporter.models import Message, Session, Subagent

_LABELS_PLAIN = {"user": "You", "assistant": "Claude"}
_LABELS_EMOJI = {"user": "🧑 You", "assistant": "🤖 Claude"}


def _fmt_ts(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
    except ValueError:
        return ts


def _turn(msg: Message, labels: dict[str, str]) -> str:
    label = labels.get(msg.role, msg.role)
    when = _fmt_ts(msg.timestamp)
    header = f"## {label} — {when}" if when else f"## {label}"
    block = [header]
    if msg.text.strip():
        block.append(msg.text)
    if msg.tool_notes:
        notes = "\n\n".join(msg.tool_notes)
        block.append(f"<details><summary>tool activity</summary>\n\n{notes}\n\n</details>")
    return "\n\n".join(block)


def render(
    session: Session,
    messages: list[Message],
    subagents: list[Subagent],
    *,
    title: str,
    created: str | None,
    updated: str | None,
    emoji: bool = False,
) -> str:
    labels = _LABELS_EMOJI if emoji else _LABELS_PLAIN
    n_user = sum(1 for m in messages if m.role == "user")
    n_asst = sum(1 for m in messages if m.role == "assistant")

    front = [
        "---",
        f"title: {title}",
        f"session_id: {session.session_id}",
        f"source_type: {session.source_type}",
        f"project: {session.project}",
        f"project_path: {session.project_path}",
        f"created: {created or ''}",
        f"updated: {updated or ''}",
        f"message_count: {len(messages)}",
        f"user_messages: {n_user}",
        f"assistant_messages: {n_asst}",
        f"subagent_count: {len(subagents)}",
        f"source_file: {session.source_file}",
        f"exporter_version: {__version__}",
        "---",
    ]

    body = [f"# {title}", ""]
    body.append(
        f"*{len(messages)} messages · started {_fmt_ts(created)} · last {_fmt_ts(updated)}*"
    )
    body.append("")
    for m in messages:
        body.append(_turn(m, labels))
        body.append("")

    if subagents:
        body.append("## Subagent runs")
        body.append("")
        for sub in subagents:
            inner = "\n\n".join(_turn(m, labels) for m in sub.messages)
            body.append(
                f"<details><summary>subagent: {sub.label}</summary>\n\n{inner}\n\n</details>"
            )
            body.append("")

    return "\n".join(front) + "\n\n" + "\n".join(body).rstrip() + "\n"
