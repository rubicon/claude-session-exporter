# claude-session-exporter — Design Spec

- **Date:** 2026-07-06
- **Status:** Approved (design); pending implementation plan
- **Author:** Dax Davis
- **Repo (planned):** public GitHub `rubicon/claude-session-exporter`
- **Local path:** `~/Developer/github.com/rubicon/claude-session-exporter/`

## 1. Purpose

Export local Claude **Claude Code** and **cowork (local agent mode)** sessions to clean Markdown
files with YAML frontmatter. Two entry points share one engine:

- **TUI** (Textual) — interactive selection and export.
- **CLI** (Typer) — scriptable, cron-friendly incremental export.

The tool reproduces the readable Markdown format used to recover a corrupt session earlier
(full user/assistant text, tool activity collapsed into `<details>`), generalized to any session.

## 2. Scope

### In scope

- **Claude Code** sessions: `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` (~676 uuid-named transcripts today).
- **Cowork** sessions: `~/Library/Application Support/Claude/local-agent-mode-sessions/<space>/<org-id>/local_<id>/.claude/projects/<encoded-cwd>/<session-id>.jsonl` (**307 transcripts** today).
- Subagent sidechains (`agent-*.jsonl`) nested into their parent session's export by default.
- Markdown export with YAML frontmatter.
- Incremental export (only new or updated sessions) driven by a per-output-folder manifest.
- Interactive TUI and non-interactive CLI over the same engine.

### Out of scope

- **Regular claude.ai chats.** They are not stored as transcripts locally — only a binary
  IndexedDB leveldb cache (`IndexedDB/https_claude.ai_*.leveldb`) that may be partial. For those,
  use claude.ai **Settings → Export data**. Revisit only if a reliable source appears.
- Any network/API calls. The tool reads local files only.

## 3. Session sources (verified 2026-07-06)

| Source | Location | Project name derived from |
|---|---|---|
| Claude Code | `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` | record `cwd`, last path component |
| Cowork | `~/Library/.../local-agent-mode-sessions/<space>/<org-id>/local_<id>/.claude/projects/<encoded-cwd>/<uuid>.jsonl` | the `<space>` folder name |

Both use the same Claude Code JSONL transcript format (verified: `message`, `type`, `parentUuid`,
`sessionId`, `cwd`, `toolUseResult`). Records carry `message.content` as a string or list of parts
(`text`, `tool_use`, `tool_result`), plus `timestamp` and `cwd`.

**Discovery rule (important):** a session is a **UUID-named** `.jsonl` file directly inside a
`.claude/projects/<encoded-cwd>/` directory. `audit.jsonl` (audit logs, ~190) is never a session.
`agent-*.jsonl` (subagent sidechains) are **not standalone sessions** either — they are **attached to
their parent session** and rendered within it (see Subagents, below).

**Subagents:** any session that dispatched subagents stores each subagent's full conversation in a
`subagents/agent-*.jsonl` file nested under that session (Claude Code: ~458 such files; cowork: many).
This content is **unique** — the parent transcript records only the Task call and the final
`tool_result`, not the subagent's internal dialogue (verified: a sampled parent had 88 main records,
0 sidechain records). Sidechains are therefore included in the export by default, associated to their
parent **by path** (all `agent-*.jsonl` under the parent session's project subtree), and rendered as a
collapsed "Subagent runs" section. Opt out with `--no-subagents` / `include_subagents = false`.

**Cowork project = the `<space>` folder** (first path segment under `local-agent-mode-sessions/`),
e.g. `skills-plugin`, or a UUID when the space is unnamed (no friendly-name mapping exists, so the
UUID is shown as-is). The cowork `cwd` is **not** usable for grouping — it always ends in the sandbox
`/outputs`. Claude Code project name still derives from `cwd`'s last component.

**No stored title field:** sampling 30 Claude Code and 60 cowork sessions found zero `type:summary`
records. Titles are therefore *derived* from the first user message.

## 4. Project layout

```
claude-session-exporter/
  pyproject.toml            # uv-managed, Python 3.11+, console entry points
  README.md
  LICENSE                   # MIT
  CHANGELOG.md              # Keep a Changelog
  ARCHITECTURE.md
  CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md
  CLAUDE.md  AGENTS.md      # AGENTS.md = pointer stub
  .editorconfig
  .github/
    dependabot.yml
    workflows/              # ci.yaml (test+lint+commit policy), codeql, scorecard
  src/claude_session_exporter/
    __init__.py             # __version__
    __main__.py             # dispatch: no subcommand → TUI, else CLI
    cli.py                  # Typer CLI
    tui.py                  # Textual app
    discovery.py            # locate sessions across both sources → Session objects
    models.py               # Session, Message, Report dataclasses
    parser.py               # JSONL → structured messages (tolerant of bad lines)
    renderer.py             # structured → markdown (frontmatter + body)
    naming.py               # title derivation, slugify, output-path building
    manifest.py             # read/write .claude-export-manifest.json
    config.py               # read/write ~/.config/claude-session-exporter/config.toml
    exporter.py             # orchestrator: discover → filter → render → write → manifest
  tests/
    fixtures/               # sample cowork/claude-code/malformed/empty/unicode jsonl
    test_parser.py test_naming.py test_renderer.py
    test_incremental.py test_discovery.py test_config.py
```

Single-responsibility modules; `exporter.py` is the only integrator. `cli.py` and `tui.py` both
call `exporter.export()` and never each other, so interactive and automated runs behave identically.

## 5. Data model

```python
@dataclass
class Session:
    source_type: str        # "claude-code" | "cowork"
    session_id: str
    source_file: Path
    project: str            # claude-code: cwd last component; cowork: <space> folder
    project_path: str       # original cwd
    subagent_files: list[Path]   # agent-*.jsonl under this session (empty if none)
    mtime: float            # max mtime across source_file + subagent_files
    size: int               # sum of sizes across source_file + subagent_files
    # messages parsed lazily via parser.parse(source_file)

@dataclass
class Message:
    role: str               # "user" | "assistant"
    timestamp: str | None
    text: str               # concatenated text parts
    tool_notes: list[str]   # rendered tool_use / tool_result summaries

@dataclass
class Report:
    exported: list[str]     # session ids newly written
    updated: list[str]      # session ids re-written (changed)
    skipped: list[str]      # unchanged
    failed: list[tuple[str, str]]   # (session id, reason)
```

## 6. Data flow

```
discovery.find(sources)        → list[Session]
exporter.export(sessions, output_dir, force):
    manifest = manifest.load(output_dir)
    for s in sessions:
        state = classify(s, manifest, force)     # new | updated | unchanged
        if state == unchanged: skipped; continue
        try:
            msgs  = parser.parse(s.source_file)   # bad lines skipped + counted
            md    = renderer.render(s, msgs)
            path  = naming.output_path(output_dir, s)
            old   = manifest.output_path(s.session_id)
            if old and old != path: remove(old)   # title changed → rename, not orphan
            write(path, md)
            manifest.update(s, path)
            record exported/updated
        except Exception as e:
            failed.append((s.session_id, str(e)))  # isolated; run continues
    manifest.save(output_dir)
    return Report(...)
```

## 7. Markdown output format

### Frontmatter

```yaml
---
title: I received this response to the following question
session_id: 076f4d83-6e83-4e73-8154-7ff91c562913
source_type: cowork            # or claude-code
project: outputs
project_path: /original/cwd
created: 2026-07-06T11:18:22-05:00
updated: 2026-07-06T11:26:24-05:00
message_count: 440
user_messages: 41
assistant_messages: 240
subagent_count: 2
source_file: /path/to/session.jsonl
exported: 2026-07-06T12:40:33-05:00
exporter_version: 0.1.0
---
```

### Body

- `# <derived title>`
- A one-line metadata summary (messages, started, last activity).
- Turns in order:
  - **User:** `## You — <local time>` then text.
  - **Assistant:** `## Claude — <local time>` then text, followed by an optional
    `<details><summary>tool activity</summary> … </details>` block listing `tool_use` calls and
    truncated `tool_result` output.
- **Subagent runs** (when present and not opted out): a trailing `## Subagent runs` section, one
  `<details><summary>subagent: <derived label></summary> … </details>` per `agent-*.jsonl`, each
  rendering that subagent's turns with the same turn formatting. Frontmatter gains
  `subagent_count: <n>`.
- **Emoji headers off by default** (respects the no-emoji house rule); `emoji_headers = true` in
  config restores `## 🧑 You` / `## 🤖 Claude` / `🔧`.

## 8. Title & filename derivation

- **Title:** first user message → strip markdown/code fences/whitespace → collapse to one line →
  trim to ~60 chars on a word boundary. Empty/no user message → `untitled-<YYYY-MM-DD>`.
- **Filename:** `YYYY-MM-DD_<slug-of-title>.md` (date from session `created`). Pure title, no id —
  stability is guaranteed by the manifest (session_id → output_path); a changed title triggers a
  rename of the existing file rather than a new orphan.
- Full title and `session_id` always appear in frontmatter, so the id is never lost.

## 9. Output layout

Mirror the source structure under the output root:

```
<output>/claude-code/<project>/<YYYY-MM-DD_title>.md
<output>/cowork/<project>/<YYYY-MM-DD_title>.md
<output>/.claude-export-manifest.json
```

## 10. CLI

```
claude-session-exporter                       # no subcommand → launch TUI
claude-session-exporter export [options]      # non-interactive incremental export
    --source cowork|claude-code               # repeatable; default both
    --project <name>                          # repeatable filter
    --since <YYYY-MM-DD> --until <YYYY-MM-DD>  # filter on session activity
    --output <dir>                            # override config/default
    --all                                     # no filters; everything new/updated
    --force                                   # ignore manifest; re-export matched
    --no-subagents                            # exclude subagent sidechains
    --dry-run                                 # report only, write nothing
claude-session-exporter list [filters]        # show matches, write nothing
claude-session-exporter config --show | --set-output <dir>
```

- Alias `cse` maps to the same entry point.
- Prints a summary: exported / updated / skipped / failed. Nonzero exit on fatal error only.
- Cron surface: `claude-session-exporter export --all`.

## 11. TUI (Textual)

Screens:

1. **Home** — choose source (Cowork / Claude Code) and browse mode (Projects | Date range).
2. **Projects** — list projects with session counts → select → Sessions.
3. **Date range** — enter from/to → flat Sessions list.
4. **Sessions** — checkbox multi-select; rows show `date · title · size`; type-to-filter;
   "select all"; export selected.
5. **Progress + summary.**

Footer shows the active output dir with a key to change it (optionally persisted to config).

## 12. Config & state

- **Config:** `~/.config/claude-session-exporter/config.toml`

  ```toml
  output_dir = "~/Documents/Claude Session Exports"   # first-run default
  sources = ["cowork", "claude-code"]
  emoji_headers = false
  include_subagents = true
  ```

  First run creates the file. Dax's value:
  `/Users/daxdavis/Library/Mobile Documents/iCloud~md~obsidian/Documents/Dax/Claude Sessions`.

- **Manifest:** `.claude-export-manifest.json` at each output root.

  ```json
  {
    "version": 1,
    "sessions": {
      "<session_id>": {
        "source_file": "…",
        "mtime": 0,
        "size": 0,
        "output_path": "…",
        "title": "…",
        "exported_at": "…"
      }
    }
  }
  ```

  Per-destination, so distinct output folders track independently.

## 13. Incremental logic

- `new` — session_id absent from manifest.
- `updated` — `mtime` or `size` differs from manifest. Both aggregate the parent transcript **and**
  its subagent files, so a new or changed `agent-*.jsonl` re-exports the parent session.
- `unchanged` — matches → skip (unless `--force`).
- Title change (same id, different derived title) → remove old `output_path`, write new one.
- Flipping `include_subagents` does not itself invalidate the manifest; use `--force` to re-render
  existing sessions under the new setting.

## 14. Error handling

- Parser skips malformed JSONL lines and counts them; a mostly-valid file still exports.
- Per-session isolation: one failing session is recorded in `Report.failed`; the run continues.
- Sessions with no user message → `untitled-<date>` title, still exported.
- Unwritable output directory → clear fatal error before work begins.
- A summary always prints (including counts of skipped and failed).

## 15. Testing

pytest with fixtures: valid cowork, valid claude-code, malformed lines, empty file, unicode title.
Cases:

- parser tolerance (bad/empty lines) and content extraction,
- title derivation and slugification (unicode, punctuation, length),
- output-path building and source mirroring,
- frontmatter field correctness,
- incremental: new / updated / unchanged-skip / title-change-rename,
- date filtering and `--dry-run` (no writes),
- config load/create and default resolution,
- discovery: UUID-named transcripts only; `audit.jsonl` excluded; `agent-*.jsonl` attached to parent,
- subagents: association by path, nested rendering, `--no-subagents` opt-out, and subagent-change
  re-export via aggregated mtime/size,
- project derivation: claude-code from `cwd`; cowork from `<space>` folder (named and UUID).

## 16. Packaging & tooling

- Python 3.11+, `uv`, `pyproject.toml`, console entry points `claude-session-exporter` and `cse`.
- Formatters/linters: **Black** + **Ruff**.
- Install: `uv tool install .` or `pipx install .`.
- Dependencies: `textual`, `typer` (pulls Rich), stdlib `tomllib` for config read (`tomli-w` for write).

## 17. Repository process (public GitHub, per policy)

- **Host:** public GitHub `rubicon/claude-session-exporter`; `origin` → GitHub (canonical for OSS).
- **License:** MIT, with `SPDX-License-Identifier: MIT` headers in source files.
- **Universal docs:** README, LICENSE, CHANGELOG (Keep a Changelog), ARCHITECTURE, CLAUDE.md +
  AGENTS.md stub, `.editorconfig`.
- **Public/collaborative overlay:** CONTRIBUTING, CODE_OF_CONDUCT (Contributor Covenant 2.1),
  SECURITY, SUPPORT; OpenSSF Scorecard + CodeQL in CI; Dependabot; contrib.rocks grid in README.
- **Workflow:** issue-first → `dev/<issue>-<slug>` worktree branch → signed Conventional Commits →
  PR (`Closes #N`) → required checks green → squash-merge; linear history; auto-delete branches.
- **Provisioning baseline** (scripted via `gh api`): description + topics; branch protection on
  `main` (require PR, passing checks, signed commits, linear history; block direct/force push);
  secret scanning + push protection; Dependabot alerts/updates. GitHub App install for release
  automation is the one manual step, deferred with release-please.
- **Deferred until first published release:** release-please automation and installable-artifact
  provenance (SLSA / cosign / checksums). v0 ships source install plus test + lint + commit-policy CI.
- **Bootstrapping:** the repo, scaffold, and this spec land through the issue/branch/PR flow, not a
  direct push to `main`. First issue: "provision repo + scaffold."

## 18. Implementation phases (for the plan)

1. Provision repo + scaffold (pyproject, docs, CI skeleton, `.editorconfig`, licensing headers).
2. Core engine: models, parser, naming, renderer (+ tests) — the reusable library.
3. Discovery + manifest + exporter with incremental logic (+ tests).
4. CLI (Typer) over the engine (+ tests).
5. TUI (Textual) over the engine.
6. Docs pass (README usage, ARCHITECTURE), verification, first tagged release decision.
