# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffold: packaging, tooling, CI, and standard repository documentation.
- Core export engine: session models, a tolerant JSONL parser, title/slug derivation, and a Markdown renderer with YAML frontmatter.
- Session discovery across Claude Code and Claude cowork sources, with audit-file exclusion and subagent-file detection.
- Incremental export via a JSON manifest that tracks exported sessions, detects renames, and re-exports when subagent content changes.
- Subagent sidechains nested and collapsed into their parent session's Markdown output, with an opt-out to exclude them.
- TOML configuration (`config.py`) with first-run defaults for output directory, sources, and rendering options.
- Typer-based CLI (`claude-session-exporter`) with `export`, `list`, and `config` subcommands, supporting `--source`, `--project`, `--since`/`--until`, `--output`, `--all`, `--force`, `--no-subagents`, and `--dry-run`.
- End-to-end test covering a full export run with a nested subagent.

[Unreleased]: https://github.com/rubicon/claude-session-exporter/compare/main...HEAD
