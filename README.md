# claude-session-exporter

[![CI](https://github.com/rubicon/claude-session-exporter/actions/workflows/ci.yaml/badge.svg)](https://github.com/rubicon/claude-session-exporter/actions/workflows/ci.yaml)
[![Release](https://img.shields.io/github/v/release/rubicon/claude-session-exporter?sort=semver)](https://github.com/rubicon/claude-session-exporter/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Export your local Claude Code and Claude cowork sessions to Markdown files with YAML frontmatter. Point it at your machine, and every session becomes one readable, greppable, Obsidian-friendly `.md` file, organized by source and project. Runs are incremental, so a repeat run only writes what changed.

It reads local files only. Nothing is uploaded, and there is no network call.

## Why

Claude Code and cowork sessions live on disk as JSONL, but they are not meant to be read there, and a long session can grow large enough that the desktop app struggles to reopen it. This tool turns those transcripts into plain Markdown you can read, search, archive, and drop into a notes vault. It exists because one cowork transcript got big enough to be a problem, and exporting it once was useful enough to generalize.

## What it exports

| Source | Location | Exported |
|---|---|---|
| Claude Code | `~/.claude/projects/` | Yes |
| Claude cowork (local agent) | `~/Library/Application Support/Claude/local-agent-mode-sessions/` | Yes |
| Regular claude.ai chats | (server-side; local cache only) | No, see [Scope](#scope) |

Each session's conversation turns, tool activity, and any subagent sidechains are rendered into a single Markdown document.

## Install

Not yet on PyPI. Install from a clone:

```bash
uv tool install .
# or
pipx install .
```

Requires Python 3.11 or newer. The commands `claude-session-exporter` and the shorter `cse` are equivalent.

## Quick start

```bash
# Export everything new or changed to the default output folder
claude-session-exporter export --all

# See what would be written, without writing it
claude-session-exporter export --all --dry-run

# Point exports at an Obsidian vault (persisted to config)
claude-session-exporter config --set-output "~/Obsidian/Vault/Claude Sessions"
```

## Usage

```bash
# Filter by source, project, and date range
claude-session-exporter export --source claude-code --project my-app --since 2026-01-01

# Re-export everything, ignoring the incremental manifest
claude-session-exporter export --all --force

# Leave subagent transcripts out
claude-session-exporter export --all --no-subagents

# List discovered sessions without exporting
claude-session-exporter list --source cowork

# Show or change configuration
claude-session-exporter config --show
claude-session-exporter config --set-output ~/exports/claude-sessions
```

`export` flags: `--source` (`cowork` or `claude-code`, repeatable), `--project` (repeatable), `--since` / `--until` (`YYYY-MM-DD`), `--output` (override the configured folder for one run), `--all` (skip filters), `--force` (ignore the manifest), `--no-subagents`, and `--dry-run`.

### Incremental exports

Every export is recorded in a `.claude-export-manifest.json` file at the output root, keyed by session ID with each session's size and modification time. On the next run, unchanged sessions are skipped, changed ones are re-exported, and a session whose derived title changed is renamed rather than orphaned. The tracking is per output folder, so different destinations keep independent state. This is what makes it safe to run from cron:

```cron
0 * * * * /usr/bin/env claude-session-exporter export --all
```

### Subagents

If a session dispatched subagents, their full transcripts live in separate files and are not duplicated in the parent. By default each is nested into the parent's Markdown under a collapsed "Subagent runs" section, so the export is a complete record. Pass `--no-subagents` to leave them out.

## Output

Files mirror the source structure under the output root:

```
<output>/claude-code/<project>/2026-07-06_short-title.md
<output>/cowork/<project>/2026-07-06_short-title.md
<output>/.claude-export-manifest.json
```

Filenames are `YYYY-MM-DD_<title-slug>.md`, where the title is derived from the first user message. Two sessions that would collide on the same name are disambiguated with a short session-ID suffix, so nothing is overwritten.

Each file opens with YAML frontmatter and then the conversation:

```yaml
---
title: "Evaluate this response and suggest improvements"
session_id: 076f4d83-6e83-4e73-8154-7ff91c562913
source_type: cowork
project: my-project
created: 2026-07-06T11:18:22-05:00
updated: 2026-07-06T11:26:24-05:00
message_count: 440
user_messages: 41
assistant_messages: 240
subagent_count: 2
---
```

Frontmatter values are quoted where needed, so titles with colons do not break parsing in Obsidian or Dataview.

## Configuration

Configuration lives at `~/.config/claude-session-exporter/config.toml`, created with defaults on first run:

```toml
output_dir = "~/Documents/Claude Session Exports"
sources = ["cowork", "claude-code"]
emoji_headers = false
include_subagents = true
```

`--output`, `--source`, and `--no-subagents` override these per run. `emoji_headers = true` switches the plain `## You` / `## Claude` turn headers to emoji versions.

## Scope

Regular claude.ai chats are out of scope. Unlike Claude Code and cowork sessions, they are not stored as transcripts on disk; the desktop app keeps only a partial binary cache, and the real history is server-side. For those, use claude.ai's Settings, Export data. This tool sticks to the two sources that keep real local transcripts, so what it exports is complete and reliable.

## Development

```bash
pip install -e ".[dev]"
ruff check .
black --check .
pytest -q
```

Architecture and module layout are in [ARCHITECTURE.md](ARCHITECTURE.md). Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md): an issue first, a `dev/<issue>-<slug>` branch, signed Conventional Commits, and a PR.

## License

MIT. See [LICENSE](LICENSE).
