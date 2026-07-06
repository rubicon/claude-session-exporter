# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from pathlib import Path

from claude_session_exporter.models import Session

_TITLE_MAX = 60


def derive_title(first_user_text: str | None, created: str | None) -> str:
    date = (created or "")[:10]
    if not first_user_text or not first_user_text.strip():
        return f"untitled-{date or 'unknown'}"
    text = re.sub(r"```.*?```", " ", first_user_text, flags=re.DOTALL)
    text = re.sub(r"[`*#>_\[\]()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return f"untitled-{date or 'unknown'}"
    if len(text) <= _TITLE_MAX:
        return text
    return text[:_TITLE_MAX].rsplit(" ", 1)[0] or text[:_TITLE_MAX]


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def _safe_component(name: str) -> str:
    return re.sub(r"[/\\]+", "-", name).strip() or "unknown"


def output_path(output_dir: Path, session: Session, title: str, created: str | None) -> Path:
    date = (created or "")[:10] or "0000-00-00"
    filename = f"{date}_{slugify(title)}.md"
    return output_dir / session.source_type / _safe_component(session.project) / filename
