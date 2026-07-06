# Architecture

`claude-session-exporter` is a pure library (`models`, `parser`, `naming`, `renderer`) underneath an orchestration layer (`discovery`, `manifest`, `exporter`), driven by a Typer `cli` and a `config` module. A future TUI will reuse the same `exporter.export()` entry point so interactive and automated runs never diverge in behavior.

## Module map

```
src/claude_session_exporter/
  __init__.py       # __version__ = "0.1.0"
  __main__.py       # dispatch: no subcommand -> TUI stub; else CLI
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

## Layers

- **Core library** (`models`, `parser`, `naming`, `renderer`) has no filesystem side effects beyond reading the session file it is given; it is pure data-in, markdown-out.
- **Orchestration** (`discovery`, `manifest`, `exporter`) finds sessions on disk, tracks what has already been exported via a JSON manifest, and drives the core library to produce output files incrementally.
- **Interface** (`config`, `cli`) resolves user configuration (TOML) and exposes the orchestration layer as a command-line tool with `export`, `list`, and `config` subcommands.

## Session sources

- Claude Code: `~/.claude/projects/*/*.jsonl`
- Cowork: `~/Library/Application Support/Claude/local-agent-mode-sessions/<space>/<org>/local_<id>/.claude/projects/*/*.jsonl` (project name = `<space>` folder)

A session is a UUID-named `.jsonl` file directly inside a `.claude/projects/<encoded-cwd>/` directory. `audit.jsonl` files are excluded; `agent-*.jsonl` files are attached to their parent session as subagent sidechains.

## Output layout

```
<output>/<source_type>/<project>/<YYYY-MM-DD_slug>.md
```

with a `.claude-export-manifest.json` manifest at the output root tracking what has been exported, so repeated runs are incremental.

See `docs/superpowers/specs/2026-07-06-claude-session-exporter-design.md` for the full design spec and `docs/superpowers/plans/2026-07-06-claude-session-exporter-core-cli.md` for the implementation plan.
