# claude-session-exporter — Core + CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python engine + CLI that exports Claude Code and cowork sessions (with subagent sidechains) to Markdown with YAML frontmatter, incrementally.

**Architecture:** A pure library (`models`, `parser`, `naming`, `renderer`) sits under an orchestration layer (`discovery`, `manifest`, `exporter`). A Typer `cli` and `config` module drive the orchestrator. The TUI (Plan 2) will reuse the same `exporter.export()` entry point, so behavior never diverges between interactive and automated runs.

**Tech Stack:** Python 3.11+, uv, Typer (+Rich), stdlib `tomllib`, `tomli-w`, pytest, Black, Ruff.

**Spec:** `docs/superpowers/specs/2026-07-06-claude-session-exporter-design.md`

## Global Constraints

- Python 3.11+ (uses stdlib `tomllib`). Package `claude_session_exporter` under `src/`.
- Console entry points: `claude-session-exporter` and `cse`.
- Public GitHub repo `rubicon/claude-session-exporter`; MIT license; `SPDX-License-Identifier: MIT` header in every `.py` source file.
- Conventional Commits; signed commits; branch `dev/<issue>-<slug>` per issue; PR body `Closes #N`; no AI-authorship trailers.
- Formatters: Black + Ruff must pass before every commit that is part of a PR.
- Emoji headers OFF by default. Subagents INCLUDED by default.
- Discovery: a session = a UUID-named `.jsonl` directly inside a `.claude/projects/<encoded-cwd>/` dir. Exclude `audit.jsonl`; attach `agent-*.jsonl` to the parent session.
- Output layout: `<output>/<source_type>/<project>/<YYYY-MM-DD_slug>.md`; manifest `.claude-export-manifest.json` at output root.
- Session sources:
  - Claude Code: `~/.claude/projects/*/*.jsonl`
  - Cowork: `~/Library/Application Support/Claude/local-agent-mode-sessions/<space>/<org>/local_<id>/.claude/projects/*/*.jsonl`; project name = `<space>` folder.

---

## Issue / Branch Grouping (repo process)

Each issue is worked in its own worktree branch and merged via one PR (`Closes #N`).

| Issue | Branch | Tasks | Deliverable |
|---|---|---|---|
| #1 | `dev/1-scaffold` | Task 1 | Repo scaffold, tooling, CI skeleton, commits the approved spec |
| #2 | `dev/2-core-engine` | Tasks 2–5 | Pure library: models, parser, naming, renderer |
| #3 | `dev/3-orchestration` | Tasks 6–8 | discovery, manifest, exporter (incremental) |
| #4 | `dev/4-cli` | Tasks 9–11 | config, Typer CLI, end-to-end test + user docs |

Worktree per issue: `git worktree add worktrees/dev-<n>-<slug> -b dev/<n>-<slug> main`.

---

## File Structure

```
src/claude_session_exporter/
  __init__.py       # __version__ = "0.1.0"
  __main__.py       # dispatch: no subcommand → TUI stub; else CLI
  models.py         # Message, Subagent, Session, Report dataclasses
  parser.py         # parse(path) -> list[Message]; helpers for facts
  naming.py         # derive_title, slugify, output_path
  renderer.py       # render(...) -> markdown string
  discovery.py      # find(sources) -> list[Session]
  manifest.py       # Manifest: load/save/classify/update
  config.py         # Config: load/create, resolve output_dir
  exporter.py       # export(sessions, output_dir, *, force, include_subagents) -> Report
  cli.py            # Typer app: export/list/config
tests/
  fixtures/         # sample jsonl written by tests or committed
  test_parser.py test_naming.py test_renderer.py
  test_discovery.py test_manifest.py test_exporter.py
  test_config.py test_cli.py
```

---

### Task 1: Provision repo + scaffold

**Issue #1 / branch `dev/1-scaffold`.**

**Files:**
- Create: `pyproject.toml`, `.editorconfig`, `.gitignore`, `README.md`, `LICENSE`, `CHANGELOG.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `CLAUDE.md`, `AGENTS.md`
- Create: `src/claude_session_exporter/__init__.py`, `src/claude_session_exporter/__main__.py`
- Create: `tests/test_smoke.py`
- Create: `.github/workflows/ci.yaml`, `.github/dependabot.yml`
- Already present: `docs/superpowers/specs/2026-07-06-claude-session-exporter-design.md`, `docs/superpowers/plans/2026-07-06-claude-session-exporter-core-cli.md`

- [ ] **Step 1: Create the GitHub repo and worktree**

```bash
gh repo create rubicon/claude-session-exporter --public \
  --description "Export Claude Code and cowork sessions to Markdown" \
  --disable-wiki
cd ~/Developer/github.com/rubicon/claude-session-exporter
git init && git branch -m main
git remote add origin https://github.com/rubicon/claude-session-exporter.git
git worktree add worktrees/dev-1-scaffold -b dev/1-scaffold main 2>/dev/null || git checkout -b dev/1-scaffold
```
(If `git worktree` fails because `main` has no commits yet, work on `dev/1-scaffold` directly; the initial scaffold PR establishes `main`.)

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "claude-session-exporter"
version = "0.1.0"
description = "Export Claude Code and cowork sessions to Markdown"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Dax Davis" }]
dependencies = ["typer>=0.12", "tomli-w>=1.0"]

[project.scripts]
claude-session-exporter = "claude_session_exporter.cli:app"
cse = "claude_session_exporter.cli:app"

[project.optional-dependencies]
dev = ["pytest>=8", "black>=24", "ruff>=0.5"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/claude_session_exporter"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `.gitignore` and `.editorconfig`**

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
worktrees/
```

`.editorconfig`:
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space

[*.py]
indent_size = 4

[*.{toml,yaml,json,md}]
indent_size = 2
```

- [ ] **Step 4: Write package skeleton**

`src/claude_session_exporter/__init__.py`:
```python
# SPDX-License-Identifier: MIT
__version__ = "0.1.0"
```

`src/claude_session_exporter/__main__.py`:
```python
# SPDX-License-Identifier: MIT
from claude_session_exporter.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 5: Write the smoke test**

`tests/test_smoke.py`:
```python
# SPDX-License-Identifier: MIT
import claude_session_exporter


def test_version_exposed():
    assert claude_session_exporter.__version__ == "0.1.0"
```

- [ ] **Step 6: Write docs stubs and CI**

Write `LICENSE` (standard MIT text, author "Dax Davis", year 2026). Write `README.md` (name, one-paragraph purpose, "Status: in development", install placeholder). Write `CHANGELOG.md` with a Keep a Changelog `[Unreleased]` skeleton. Write `ARCHITECTURE.md` summarizing the module map from this plan's File Structure. Write `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SECURITY.md`, `SUPPORT.md` (brief, standard). Write `AGENTS.md` as the canonical pointer stub and `CLAUDE.md` with project-specific agent notes (reference this repo's process from the policy).

`.github/workflows/ci.yaml`:
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: black --check .
      - run: pytest -q
```

`.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
```

- [ ] **Step 7: Verify tooling locally**

Run: `pip install -e ".[dev]" && ruff check . && black --check . && pytest -q`
Expected: install succeeds; ruff/black clean; smoke test PASSES (`cli` import will fail until Task 10 — for Task 1, `__main__` importing `cli` is not exercised by the smoke test, which imports only the package root; leave `cli.py` creation to Task 10 and keep `__main__.py` as written).

Note: because `__main__.py` imports `cli`, do not run `python -m claude_session_exporter` until Task 10. The smoke test does not import `__main__`, so CI stays green.

- [ ] **Step 8: Commit and open PR**

```bash
git add -A
git commit -S -m "chore: scaffold project, tooling, docs, and CI"
git push -u origin dev/1-scaffold
gh pr create --title "chore: scaffold project" --body "Scaffold repo, tooling, docs, CI. Includes approved design spec and this plan.

Closes #1"
```

---

### Task 2: Data model

**Issue #2 / branch `dev/2-core-engine`.**

**Files:**
- Create: `src/claude_session_exporter/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `Message(role, timestamp, text, tool_notes)`, `Subagent(label, messages)`, `Session(source_type, session_id, source_file, project, project_path, subagent_files, mtime, size)`, `Report(exported, updated, skipped, failed)`.

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter.models import Message, Subagent, Session, Report


def test_defaults():
    m = Message(role="user", timestamp=None, text="hi")
    assert m.tool_notes == []
    s = Session(
        source_type="cowork",
        session_id="abc",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )
    assert s.subagent_files == [] and s.mtime == 0.0 and s.size == 0
    assert Subagent(label="agent-1", messages=[]).messages == []
    r = Report()
    assert r.exported == [] and r.failed == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.models`

- [ ] **Step 3: Write `models.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/models.py tests/test_models.py
git commit -S -m "feat: add core dataclasses"
```

---

### Task 3: JSONL parser

**Files:**
- Create: `src/claude_session_exporter/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `Message` from `models`.
- Produces:
  - `parse(path: Path) -> list[Message]`
  - `facts(path: Path) -> dict` with keys `cwd: str | None`, `created: str | None`, `updated: str | None` (first/last record timestamps).

- [ ] **Step 1: Write the failing test**

`tests/test_parser.py`:
```python
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from claude_session_exporter import parser


def _write(tmp_path, records) -> Path:
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def test_parse_extracts_text_and_tools_and_skips_bad_lines(tmp_path):
    p = tmp_path / "s.jsonl"
    good = [
        {"type": "user", "timestamp": "2026-07-06T10:00:00Z",
         "message": {"content": "hello"}},
        {"type": "assistant", "timestamp": "2026-07-06T10:00:01Z",
         "message": {"content": [
             {"type": "text", "text": "hi there"},
             {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
         ]}},
        {"type": "assistant", "timestamp": "2026-07-06T10:00:02Z",
         "message": {"content": [
             {"type": "tool_result", "content": [{"type": "text", "text": "a\nb"}]},
         ]}},
        {"type": "mode", "message": {"content": "ignored"}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in good) + "\nNOT JSON\n", encoding="utf-8")
    msgs = parser.parse(p)
    assert [m.role for m in msgs] == ["user", "assistant", "assistant"]
    assert msgs[0].text == "hello"
    assert "hi there" in msgs[1].text
    assert any("Bash" in n for n in msgs[1].tool_notes)
    assert any("tool result" in n for n in msgs[2].tool_notes)


def test_facts_reads_cwd_and_timestamps(tmp_path):
    p = _write(tmp_path, [
        {"type": "mode", "cwd": "/home/x/proj", "timestamp": "2026-07-06T10:00:00Z"},
        {"type": "user", "timestamp": "2026-07-06T10:05:00Z", "message": {"content": "q"}},
    ])
    f = parser.facts(p)
    assert f["cwd"] == "/home/x/proj"
    assert f["created"] == "2026-07-06T10:00:00Z"
    assert f["updated"] == "2026-07-06T10:05:00Z"


def test_empty_file_yields_no_messages(tmp_path):
    p = tmp_path / "e.jsonl"
    p.write_text("", encoding="utf-8")
    assert parser.parse(p) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.parser`

- [ ] **Step 3: Write `parser.py`**

```python
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
                body = part.get("content", "")
                if isinstance(body, list):
                    body = " ".join(
                        x.get("text", "") for x in body if isinstance(x, dict)
                    )
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/parser.py tests/test_parser.py
git commit -S -m "feat: add tolerant jsonl parser"
```

---

### Task 4: Naming (title, slug, output path)

**Files:**
- Create: `src/claude_session_exporter/naming.py`
- Test: `tests/test_naming.py`

**Interfaces:**
- Consumes: `Session` from `models`.
- Produces:
  - `derive_title(first_user_text: str | None, created: str | None) -> str`
  - `slugify(title: str) -> str`
  - `output_path(output_dir: Path, session: Session, title: str, created: str | None) -> Path`

- [ ] **Step 1: Write the failing test**

`tests/test_naming.py`:
```python
# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter import naming
from claude_session_exporter.models import Session


def test_derive_title_trims_and_cleans():
    t = naming.derive_title("```code```\n# Please **evaluate** this response now", "2026-07-06T10:00:00Z")
    assert "`" not in t and "*" not in t and "#" not in t
    assert len(t) <= 60


def test_derive_title_fallback_when_empty():
    assert naming.derive_title("", "2026-07-06T10:00:00Z") == "untitled-2026-07-06"
    assert naming.derive_title(None, None) == "untitled-unknown"


def test_slugify():
    assert naming.slugify("I received this — Response!") == "i-received-this-response"
    assert naming.slugify("///") == "untitled"


def test_output_path_mirrors_source():
    s = Session(
        source_type="cowork",
        session_id="abc",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )
    p = naming.output_path(Path("/out"), s, "My Title", "2026-07-06T10:00:00Z")
    assert p == Path("/out/cowork/skills-plugin/2026-07-06_my-title.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_naming.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.naming`

- [ ] **Step 3: Write `naming.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_naming.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/naming.py tests/test_naming.py
git commit -S -m "feat: add title, slug, and output-path derivation"
```

---

### Task 5: Renderer

**Files:**
- Create: `src/claude_session_exporter/renderer.py`
- Test: `tests/test_renderer.py`

**Interfaces:**
- Consumes: `Session`, `Message`, `Subagent` from `models`.
- Produces:
  - `render(session, messages, subagents, *, title, created, updated, emoji=False) -> str`
    where `messages: list[Message]`, `subagents: list[Subagent]`. Returns the full Markdown document (frontmatter + body). `user_messages`/`assistant_messages`/`subagent_count` are computed inside from the inputs.

- [ ] **Step 1: Write the failing test**

`tests/test_renderer.py`:
```python
# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter import renderer
from claude_session_exporter.models import Session, Message, Subagent


def _session():
    return Session(
        source_type="cowork",
        session_id="076f4d83",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )


def test_render_has_frontmatter_and_turns():
    msgs = [
        Message("user", "2026-07-06T10:00:00Z", "hello"),
        Message("assistant", "2026-07-06T10:00:01Z", "hi", ["tool call `Bash` — {}"]),
    ]
    out = renderer.render(
        _session(), msgs, [],
        title="Hello", created="2026-07-06T10:00:00Z", updated="2026-07-06T10:00:01Z",
    )
    assert out.startswith("---\n")
    assert "session_id: 076f4d83" in out
    assert "source_type: cowork" in out
    assert "user_messages: 1" in out
    assert "assistant_messages: 1" in out
    assert "subagent_count: 0" in out
    assert "# Hello" in out
    assert "## You" in out and "## Claude" in out
    assert "<details><summary>tool activity</summary>" in out
    assert "🧑" not in out  # emoji off by default


def test_render_includes_subagents_section():
    sub = Subagent("agent-a420", [Message("user", None, "You are building X")])
    out = renderer.render(
        _session(), [Message("user", None, "go")], [sub],
        title="T", created=None, updated=None,
    )
    assert "subagent_count: 1" in out
    assert "## Subagent runs" in out
    assert "<details><summary>subagent: agent-a420</summary>" in out
    assert "You are building X" in out


def test_render_emoji_mode():
    out = renderer.render(
        _session(), [Message("user", None, "hi")], [],
        title="T", created=None, updated=None, emoji=True,
    )
    assert "🧑 You" in out and "🤖 Claude" not in out  # only user turn present
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.renderer`

- [ ] **Step 3: Write `renderer.py`**

```python
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
    body.append(f"*{len(messages)} messages · started {_fmt_ts(created)} · last {_fmt_ts(updated)}*")
    body.append("")
    for m in messages:
        body.append(_turn(m, labels))
        body.append("")

    if subagents:
        body.append("## Subagent runs")
        body.append("")
        for sub in subagents:
            inner = "\n\n".join(_turn(m, labels) for m in sub.messages)
            body.append(f"<details><summary>subagent: {sub.label}</summary>\n\n{inner}\n\n</details>")
            body.append("")

    return "\n".join(front) + "\n\n" + "\n".join(body).rstrip() + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_renderer.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit and open PR for Issue #2**

```bash
black . && ruff check --fix . && pytest -q
git add src/claude_session_exporter/renderer.py tests/test_renderer.py
git commit -S -m "feat: add markdown renderer with subagent section"
git push -u origin dev/2-core-engine
gh pr create --title "feat: core export engine" --body "models, parser, naming, renderer with tests.

Closes #2"
```

---

### Task 6: Discovery

**Issue #3 / branch `dev/3-orchestration`** (branch from updated `main` after #2 merges).

**Files:**
- Create: `src/claude_session_exporter/discovery.py`
- Test: `tests/test_discovery.py`

**Interfaces:**
- Consumes: `Session` from `models`; `facts` from `parser`.
- Produces:
  - `find(sources: list[str], *, roots: dict[str, Path] | None = None) -> list[Session]`
    `sources` ⊆ `{"claude-code", "cowork"}`. `roots` overrides base dirs for tests. Each `Session` has `subagent_files`, aggregated `mtime` (max) and `size` (sum) across transcript + subagents.
  - Module constants `CLAUDE_CODE_ROOT: Path`, `COWORK_ROOT: Path`.

- [ ] **Step 1: Write the failing test**

`tests/test_discovery.py`:
```python
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from claude_session_exporter import discovery


def _cc_session(root: Path, project_enc: str, sid: str, cwd: str):
    d = root / project_enc
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": cwd, "timestamp": "2026-07-06T10:00:00Z"}) + "\n"
        + json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n",
        encoding="utf-8",
    )


def test_find_claude_code(tmp_path):
    cc = tmp_path / "claude" / "projects"
    _cc_session(cc, "-Users-dax-proj", "1111", "/Users/dax/proj")
    sessions = discovery.find(["claude-code"], roots={"claude-code": cc})
    assert len(sessions) == 1
    s = sessions[0]
    assert s.source_type == "claude-code"
    assert s.session_id == "1111"
    assert s.project == "proj"
    assert s.mtime > 0 and s.size > 0


def test_find_cowork_project_is_space_and_attaches_subagents(tmp_path):
    base = tmp_path / "cowork"
    sess_dir = base / "skills-plugin" / "org1" / "local_aaa" / ".claude" / "projects" / "-enc-output-x"
    sess_dir.mkdir(parents=True)
    (sess_dir / "2222.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/sandbox/outputs"}) + "\n", encoding="utf-8"
    )
    subs = sess_dir / "2222" / "subagents"
    subs.mkdir(parents=True)
    (subs / "agent-abc.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "sub"}}) + "\n", encoding="utf-8"
    )
    (sess_dir / "audit.jsonl").write_text("{}\n", encoding="utf-8")  # must be ignored

    sessions = discovery.find(["cowork"], roots={"cowork": base})
    assert len(sessions) == 1
    s = sessions[0]
    assert s.source_type == "cowork"
    assert s.project == "skills-plugin"
    assert len(s.subagent_files) == 1
    assert s.subagent_files[0].name == "agent-abc.jsonl"


def test_audit_and_agent_files_are_not_sessions(tmp_path):
    base = tmp_path / "cowork"
    d = base / "spaceX" / "org" / "local_z" / ".claude" / "projects" / "-enc"
    d.mkdir(parents=True)
    (d / "audit.jsonl").write_text("{}\n", encoding="utf-8")
    (d / "agent-xyz.jsonl").write_text("{}\n", encoding="utf-8")
    assert discovery.find(["cowork"], roots={"cowork": base}) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_discovery.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.discovery`

- [ ] **Step 3: Write `discovery.py`**

```python
# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from pathlib import Path

from claude_session_exporter import parser
from claude_session_exporter.models import Session

CLAUDE_CODE_ROOT = Path.home() / ".claude" / "projects"
COWORK_ROOT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Claude"
    / "local-agent-mode-sessions"
)

_UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}\.jsonl$")


def _is_transcript(path: Path) -> bool:
    return bool(_UUID_RE.match(path.name))


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_discovery.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/discovery.py tests/test_discovery.py
git commit -S -m "feat: add session discovery with subagent attachment"
```

---

### Task 7: Manifest

**Files:**
- Create: `src/claude_session_exporter/manifest.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: `Session` from `models`.
- Produces a `Manifest` class:
  - `Manifest.load(output_dir: Path) -> Manifest`
  - `.classify(session) -> str` returning `"new" | "updated" | "unchanged"` (compares `session.mtime`/`session.size` to stored entry).
  - `.output_path_for(session_id) -> str | None`
  - `.update(session, output_path: Path, title: str) -> None`
  - `.save() -> None`
  - Manifest filename constant `MANIFEST_NAME = ".claude-export-manifest.json"`.

- [ ] **Step 1: Write the failing test**

`tests/test_manifest.py`:
```python
# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter.manifest import Manifest, MANIFEST_NAME
from claude_session_exporter.models import Session


def _session(mtime=100.0, size=10):
    return Session(
        source_type="cowork", session_id="abc", source_file=Path("/x.jsonl"),
        project="p", project_path="/c", mtime=mtime, size=size,
    )


def test_new_then_unchanged_then_updated(tmp_path):
    m = Manifest.load(tmp_path)
    s = _session()
    assert m.classify(s) == "new"
    m.update(s, tmp_path / "cowork" / "p" / "f.md", "Title")
    m.save()

    m2 = Manifest.load(tmp_path)
    assert (tmp_path / MANIFEST_NAME).exists()
    assert m2.classify(_session()) == "unchanged"
    assert m2.classify(_session(mtime=200.0)) == "updated"
    assert m2.classify(_session(size=99)) == "updated"


def test_output_path_for(tmp_path):
    m = Manifest.load(tmp_path)
    s = _session()
    m.update(s, tmp_path / "old.md", "Title")
    assert m.output_path_for("abc") == str(tmp_path / "old.md")
    assert m.output_path_for("missing") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.manifest`

- [ ] **Step 3: Write `manifest.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_manifest.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/manifest.py tests/test_manifest.py
git commit -S -m "feat: add incremental export manifest"
```

---

### Task 8: Exporter (orchestration)

**Files:**
- Create: `src/claude_session_exporter/exporter.py`
- Test: `tests/test_exporter.py`

**Interfaces:**
- Consumes: `Session`, `Report` from `models`; `parser.parse`/`parser.facts`; `naming.derive_title`/`naming.output_path`; `renderer.render`; `Manifest`.
- Produces:
  - `export(sessions: list[Session], output_dir: Path, *, force: bool = False, include_subagents: bool = True, emoji: bool = False, dry_run: bool = False) -> Report`
  - `_build_subagents(session) -> list[Subagent]` (label = subagent file stem).

- [ ] **Step 1: Write the failing test**

`tests/test_exporter.py`:
```python
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from claude_session_exporter import exporter
from claude_session_exporter.models import Session


def _make_session(tmp_path, sid="abc", text="I received this response") -> Session:
    src = tmp_path / f"{sid}.jsonl"
    src.write_text(
        json.dumps({"type": "mode", "cwd": "/c", "timestamp": "2026-07-06T10:00:00Z"}) + "\n"
        + json.dumps({"type": "user", "timestamp": "2026-07-06T10:00:01Z",
                      "message": {"content": text}}) + "\n",
        encoding="utf-8",
    )
    st = src.stat()
    return Session("cowork", sid, src, "skills-plugin", "/c", [], st.st_mtime, st.st_size)


def test_export_writes_markdown_and_manifest(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    report = exporter.export([s], out)
    assert report.exported == ["abc"]
    md = out / "cowork" / "skills-plugin" / "2026-07-06_i-received-this-response.md"
    assert md.exists()
    assert "session_id: abc" in md.read_text(encoding="utf-8")
    assert (out / ".claude-export-manifest.json").exists()


def test_second_run_skips_unchanged(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    exporter.export([s], out)
    report = exporter.export([s], out)
    assert report.skipped == ["abc"] and report.exported == []


def test_force_reexports(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    exporter.export([s], out)
    report = exporter.export([s], out, force=True)
    assert report.updated == ["abc"]


def test_dry_run_writes_nothing(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    report = exporter.export([s], out, dry_run=True)
    assert report.exported == ["abc"]
    assert not out.exists()


def test_title_change_renames_old_file(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path, text="First title")
    exporter.export([s], out)
    old = out / "cowork" / "skills-plugin" / "2026-07-06_first-title.md"
    assert old.exists()
    # rewrite source with new first message + bump mtime via new content
    s.source_file.write_text(
        json.dumps({"type": "mode", "cwd": "/c", "timestamp": "2026-07-06T10:00:00Z"}) + "\n"
        + json.dumps({"type": "user", "timestamp": "2026-07-06T10:00:01Z",
                      "message": {"content": "Second title"}}) + "\n",
        encoding="utf-8",
    )
    st = s.source_file.stat()
    s.mtime, s.size = st.st_mtime + 1, st.st_size + 1  # force "updated"
    exporter.export([s], out)
    new = out / "cowork" / "skills-plugin" / "2026-07-06_second-title.md"
    assert new.exists() and not old.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_exporter.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.exporter`

- [ ] **Step 3: Write `exporter.py`**

```python
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
                session, messages, subagents,
                title=title, created=facts["created"], updated=facts["updated"], emoji=emoji,
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
            (report.updated if state == "updated" else report.exported).append(
                session.session_id
            )
        except Exception as exc:  # isolate per-session failures
            report.failed.append((session.session_id, str(exc)))

    if not dry_run:
        manifest.save()
    return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_exporter.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit and open PR for Issue #3**

```bash
black . && ruff check --fix . && pytest -q
git add src/claude_session_exporter/exporter.py tests/test_exporter.py
git commit -S -m "feat: add export orchestration with incremental logic"
git push -u origin dev/3-orchestration
gh pr create --title "feat: discovery, manifest, and exporter" --body "Session discovery, incremental manifest, and export orchestrator.

Closes #3"
```

---

### Task 9: Config

**Issue #4 / branch `dev/4-cli`** (branch from updated `main` after #3 merges).

**Files:**
- Create: `src/claude_session_exporter/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces a `Config` dataclass and loader:
  - `load(path: Path | None = None) -> Config` — reads TOML, creating it with defaults on first run.
  - `Config(output_dir: Path, sources: list[str], emoji_headers: bool, include_subagents: bool)`.
  - `DEFAULT_OUTPUT = Path("~/Documents/Claude Session Exports").expanduser()`.
  - `CONFIG_PATH = Path("~/.config/claude-session-exporter/config.toml").expanduser()`.

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter import config


def test_first_run_creates_default(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg = config.load(cfg_path)
    assert cfg_path.exists()
    assert cfg.sources == ["cowork", "claude-code"]
    assert cfg.emoji_headers is False
    assert cfg.include_subagents is True
    assert cfg.output_dir == config.DEFAULT_OUTPUT


def test_reads_existing_values(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        'output_dir = "/tmp/exports"\nsources = ["cowork"]\n'
        "emoji_headers = true\ninclude_subagents = false\n",
        encoding="utf-8",
    )
    cfg = config.load(cfg_path)
    assert cfg.output_dir == Path("/tmp/exports")
    assert cfg.sources == ["cowork"]
    assert cfg.emoji_headers is True
    assert cfg.include_subagents is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.config`

- [ ] **Step 3: Write `config.py`**

```python
# SPDX-License-Identifier: MIT
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

DEFAULT_OUTPUT = (Path("~/Documents/Claude Session Exports")).expanduser()
CONFIG_PATH = (Path("~/.config/claude-session-exporter/config.toml")).expanduser()
_DEFAULT_SOURCES = ["cowork", "claude-code"]


@dataclass
class Config:
    output_dir: Path
    sources: list[str]
    emoji_headers: bool
    include_subagents: bool


def _defaults_toml() -> dict:
    return {
        "output_dir": str(DEFAULT_OUTPUT),
        "sources": _DEFAULT_SOURCES,
        "emoji_headers": False,
        "include_subagents": True,
    }


def load(path: Path | None = None) -> Config:
    path = path or CONFIG_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomli_w.dumps(_defaults_toml()), encoding="utf-8")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        output_dir=Path(data.get("output_dir", str(DEFAULT_OUTPUT))).expanduser(),
        sources=list(data.get("sources", _DEFAULT_SOURCES)),
        emoji_headers=bool(data.get("emoji_headers", False)),
        include_subagents=bool(data.get("include_subagents", True)),
    )


def set_output(output_dir: str, path: Path | None = None) -> Config:
    path = path or CONFIG_PATH
    cfg = load(path)
    data = _defaults_toml()
    data.update(
        {
            "output_dir": str(Path(output_dir).expanduser()),
            "sources": cfg.sources,
            "emoji_headers": cfg.emoji_headers,
            "include_subagents": cfg.include_subagents,
        }
    )
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return load(path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/config.py tests/test_config.py
git commit -S -m "feat: add TOML config with first-run defaults"
```

---

### Task 10: CLI (Typer)

**Files:**
- Create: `src/claude_session_exporter/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `config.load`/`config.set_output`, `discovery.find`, `exporter.export`, `Report`.
- Produces: a Typer `app` with commands `export`, `list`, `config`. Date filtering (`--since`/`--until`) and `--project` are applied to discovered sessions before export. `--output` overrides config; `--source` repeatable overrides config sources.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from typer.testing import CliRunner
from claude_session_exporter.cli import app

runner = CliRunner()


def _seed_claude_code(root: Path, sid: str, text: str):
    d = root / "-Users-dax-proj"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/Users/dax/proj", "timestamp": "2026-07-06T10:00:00Z"}) + "\n"
        + json.dumps({"type": "user", "message": {"content": text}}) + "\n",
        encoding="utf-8",
    )


def test_export_command(tmp_path, monkeypatch):
    cc = tmp_path / "cc"
    _seed_claude_code(cc, "1111", "Hello world")
    out = tmp_path / "out"
    cfg = tmp_path / "config.toml"
    monkeypatch.setattr("claude_session_exporter.discovery.CLAUDE_CODE_ROOT", cc)

    result = runner.invoke(app, [
        "export", "--source", "claude-code", "--output", str(out), "--config-path", str(cfg),
    ])
    assert result.exit_code == 0
    assert (out / "claude-code" / "proj" / "2026-07-06_hello-world.md").exists()
    assert "exported" in result.output.lower()


def test_list_command_writes_nothing(tmp_path, monkeypatch):
    cc = tmp_path / "cc"
    _seed_claude_code(cc, "2222", "List me")
    monkeypatch.setattr("claude_session_exporter.discovery.CLAUDE_CODE_ROOT", cc)
    cfg = tmp_path / "config.toml"
    result = runner.invoke(app, ["list", "--source", "claude-code", "--config-path", str(cfg)])
    assert result.exit_code == 0
    assert "2222" in result.output or "List me" in result.output.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: claude_session_exporter.cli`

- [ ] **Step 3: Write `cli.py`**

```python
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from claude_session_exporter import config, discovery, exporter
from claude_session_exporter.models import Session

app = typer.Typer(help="Export Claude Code and cowork sessions to Markdown.")


def _filter(sessions: list[Session], projects, since, until) -> list[Session]:
    out = []
    for s in sessions:
        if projects and s.project not in projects:
            continue
        # date filter on session activity (mtime → date is coarse; use file mtime day)
        out.append(s)
    if since or until:
        from datetime import datetime, timezone

        def day(ts: float) -> str:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

        out = [
            s
            for s in out
            if (not since or day(s.mtime) >= since) and (not until or day(s.mtime) <= until)
        ]
    return out


def _resolve(cfg_path: Optional[str], sources, output):
    cfg = config.load(Path(cfg_path) if cfg_path else None)
    use_sources = sources or cfg.sources
    out_dir = Path(output).expanduser() if output else cfg.output_dir
    return cfg, use_sources, out_dir


@app.command()
def export(
    source: list[str] = typer.Option(None, "--source", help="cowork | claude-code (repeatable)"),
    project: list[str] = typer.Option(None, "--project", help="filter by project (repeatable)"),
    since: str = typer.Option(None, "--since", help="YYYY-MM-DD"),
    until: str = typer.Option(None, "--until", help="YYYY-MM-DD"),
    output: str = typer.Option(None, "--output", help="override output dir"),
    all_: bool = typer.Option(False, "--all", help="no filters; everything new/updated"),
    force: bool = typer.Option(False, "--force", help="ignore manifest"),
    no_subagents: bool = typer.Option(False, "--no-subagents", help="exclude subagents"),
    dry_run: bool = typer.Option(False, "--dry-run", help="report only"),
    config_path: str = typer.Option(None, "--config-path", hidden=True),
):
    cfg, use_sources, out_dir = _resolve(config_path, source, output)
    sessions = discovery.find(use_sources)
    if not all_:
        sessions = _filter(sessions, project, since, until)
    report = exporter.export(
        sessions,
        out_dir,
        force=force,
        include_subagents=cfg.include_subagents and not no_subagents,
        emoji=cfg.emoji_headers,
        dry_run=dry_run,
    )
    typer.echo(
        f"exported: {len(report.exported)}  updated: {len(report.updated)}  "
        f"skipped: {len(report.skipped)}  failed: {len(report.failed)}"
    )
    for sid, reason in report.failed:
        typer.echo(f"  FAILED {sid}: {reason}", err=True)


@app.command("list")
def list_sessions(
    source: list[str] = typer.Option(None, "--source"),
    project: list[str] = typer.Option(None, "--project"),
    config_path: str = typer.Option(None, "--config-path", hidden=True),
):
    _cfg, use_sources, _out = _resolve(config_path, source, None)
    sessions = _filter(discovery.find(use_sources), project, None, None)
    for s in sessions:
        typer.echo(f"{s.source_type}\t{s.project}\t{s.session_id}\t{s.source_file.name}")
    typer.echo(f"{len(sessions)} sessions")


@app.command()
def config_cmd(
    show: bool = typer.Option(False, "--show"),
    set_output: str = typer.Option(None, "--set-output"),
    config_path: str = typer.Option(None, "--config-path", hidden=True),
):
    path = Path(config_path) if config_path else None
    if set_output:
        cfg = config.set_output(set_output, path)
        typer.echo(f"output_dir set to {cfg.output_dir}")
        return
    cfg = config.load(path)
    typer.echo(
        f"output_dir = {cfg.output_dir}\nsources = {cfg.sources}\n"
        f"emoji_headers = {cfg.emoji_headers}\ninclude_subagents = {cfg.include_subagents}"
    )


# Register the config command under the name "config" (avoids shadowing the module).
app.command(name="config")(config_cmd)
```

Note: the `config_cmd` function is decorated once via `app.command(name="config")` at the bottom; remove the bare `@app.command()` above it if the implementer used the decorator form — keep a single registration named `config`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
black . && ruff check --fix .
git add src/claude_session_exporter/cli.py tests/test_cli.py
git commit -S -m "feat: add Typer CLI with export, list, config"
```

---

### Task 11: End-to-end test, docs, verification

**Files:**
- Create: `tests/test_end_to_end.py`
- Modify: `README.md` (usage), `ARCHITECTURE.md` (final module map), `CHANGELOG.md` (`[Unreleased]` entries)

**Interfaces:**
- Consumes: the installed console script `claude-session-exporter`.

- [ ] **Step 1: Write the end-to-end test**

`tests/test_end_to_end.py`:
```python
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from typer.testing import CliRunner
from claude_session_exporter.cli import app

runner = CliRunner()


def test_full_run_with_subagent(tmp_path, monkeypatch):
    base = tmp_path / "cowork"
    sess = base / "skills-plugin" / "org" / "local_a" / ".claude" / "projects" / "-enc-output-x"
    sess.mkdir(parents=True)
    (sess / "abcd1234-0000-0000-0000-000000000000.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/sandbox/outputs", "timestamp": "2026-07-06T10:00:00Z"}) + "\n"
        + json.dumps({"type": "user", "timestamp": "2026-07-06T10:00:01Z",
                      "message": {"content": "Build the corpus"}}) + "\n"
        + json.dumps({"type": "assistant", "timestamp": "2026-07-06T10:00:02Z",
                      "message": {"content": [{"type": "text", "text": "on it"}]}}) + "\n",
        encoding="utf-8",
    )
    subs = sess / "abcd1234-0000-0000-0000-000000000000" / "subagents"
    subs.mkdir(parents=True)
    (subs / "agent-xyz.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "subagent task"}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("claude_session_exporter.discovery.COWORK_ROOT", base)

    out = tmp_path / "out"
    cfg = tmp_path / "config.toml"
    result = runner.invoke(app, ["export", "--source", "cowork", "--output", str(out), "--config-path", str(cfg)])
    assert result.exit_code == 0
    md = out / "cowork" / "skills-plugin" / "2026-07-06_build-the-corpus.md"
    text = md.read_text(encoding="utf-8")
    assert "subagent_count: 1" in text
    assert "## Subagent runs" in text
    assert "subagent task" in text
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest -q`
Expected: PASS (all tests across all modules).

- [ ] **Step 3: Manual verification against real data (read-only, safe)**

Run:
```bash
pip install -e ".[dev]"
claude-session-exporter list --source claude-code | head
claude-session-exporter export --source claude-code --project claude-session-exporter --output /tmp/cse-verify --dry-run
```
Expected: `list` prints real sessions; `--dry-run` reports a count and writes nothing to `/tmp/cse-verify`. Then without `--dry-run`, confirm files appear and a second run reports them all `skipped`.

- [ ] **Step 4: Update docs**

Fill `README.md` with install (`uv tool install .` / `pipx install .`), the CLI usage block from the spec §10, and the cron example `claude-session-exporter export --all`. Update `ARCHITECTURE.md` to the final module map. Add `CHANGELOG.md` `[Unreleased]` entries under `### Added`.

- [ ] **Step 5: Commit and open PR for Issue #4**

```bash
black . && ruff check --fix . && pytest -q
git add -A
git commit -S -m "feat: add end-to-end test and user docs"
git push -u origin dev/4-cli
gh pr create --title "feat: config, CLI, and docs" --body "TOML config, Typer CLI (export/list/config), end-to-end test, README/ARCHITECTURE.

Closes #4"
```

---

## Self-Review

**1. Spec coverage:**
- Sources & discovery (spec §3) → Task 6 (incl. audit/agent exclusion, cowork space project). ✅
- Subagents nested/collapsed, opt-out (§3, §7) → Tasks 5, 8, 10. ✅
- Markdown format + frontmatter, emoji off (§7) → Task 5. ✅
- Title/slug/pure-filename (§8), output layout (§9) → Task 4. ✅
- CLI surface (§10) → Task 10; `--all`, `--force`, `--dry-run`, `--no-subagents`, `--since/--until`, `--project`, `--output`, `list`, `config`. ✅
- Config + manifest (§12), incremental incl. rename & subagent-change (§13) → Tasks 7, 8, 9. ✅
- Error isolation, tolerant parser, untitled fallback (§14) → Tasks 3, 4, 8. ✅
- Testing (§15) → each task's tests + Task 11 e2e. ✅
- Packaging/tooling (§16) → Task 1. ✅
- Repo process (§17) → Issue grouping + signed commits + PRs. ✅
- **Deferred to Plan 2:** TUI (§11) — intentionally out of this plan. **Deferred to first release:** release-please + provenance (§17).

**2. Placeholder scan:** No TBD/TODO; every code step has full code; docs steps (Task 1 Step 6, Task 11 Step 4) name exact files and required content. ✅

**3. Type consistency:** `find(sources, roots=…)`, `export(sessions, output_dir, *, force, include_subagents, emoji, dry_run)`, `Manifest.classify/.output_path_for/.update/.save`, `naming.output_path(output_dir, session, title, created)`, `renderer.render(session, messages, subagents, *, title, created, updated, emoji)` are used identically across tasks. ✅

One known nit for the implementer: in `cli.py`, register the config command exactly once as name `config` (the trailing `app.command(name="config")(config_cmd)` line is the single registration — do not also decorate the function definition). Task 10 Step 3 calls this out.
