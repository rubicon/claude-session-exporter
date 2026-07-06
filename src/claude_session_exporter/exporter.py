# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from claude_session_exporter import naming, parser, renderer
from claude_session_exporter.manifest import Manifest
from claude_session_exporter.models import Report, Session, Subagent


def _first_user_text(messages) -> str | None:
    for m in messages:
        if m.role == "user" and m.text.strip():
            return m.text
    return None


def _build_subagents(session: Session) -> list[Subagent]:
    subs: list[Subagent] = []
    for f in session.subagent_files:
        subs.append(Subagent(label=f.stem, messages=parser.parse(f)))
    return subs


def export(
    sessions: list[Session],
    output_dir: Path,
    *,
    force: bool = False,
    include_subagents: bool = True,
    emoji: bool = False,
    dry_run: bool = False,
) -> Report:
    report = Report()
    manifest = Manifest.load(output_dir)

    for session in sessions:
        state = "updated" if force else manifest.classify(session)
        if state == "unchanged":
            report.skipped.append(session.session_id)
            continue
        try:
            messages = parser.parse(session.source_file)
            facts = parser.facts(session.source_file)
            title = naming.derive_title(_first_user_text(messages), facts["created"])
            subagents = _build_subagents(session) if include_subagents else []
            markdown = renderer.render(
                session,
                messages,
                subagents,
                title=title,
                created=facts["created"],
                updated=facts["updated"],
                emoji=emoji,
            )
            new_path = naming.output_path(output_dir, session, title, facts["created"])

            if dry_run:
                (report.updated if state == "updated" else report.exported).append(
                    session.session_id
                )
                continue

            old = manifest.output_path_for(session.session_id)
            if old and old != str(new_path):
                Path(old).unlink(missing_ok=True)

            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.write_text(markdown, encoding="utf-8")
            manifest.update(session, new_path, title)
            (report.updated if state == "updated" else report.exported).append(session.session_id)
        except Exception as exc:  # isolate per-session failures
            report.failed.append((session.session_id, str(exc)))

    if not dry_run:
        manifest.save()
    return report
