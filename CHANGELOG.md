# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2026-07-06)


### Features

* config, CLI, and docs ([#11](https://github.com/rubicon/claude-session-exporter/issues/11)) ([824ec69](https://github.com/rubicon/claude-session-exporter/commit/824ec694b40cec51df908dcc361f2283349be6db))
* core export engine (models, parser, naming, renderer) ([#8](https://github.com/rubicon/claude-session-exporter/issues/8)) ([8e0d535](https://github.com/rubicon/claude-session-exporter/commit/8e0d53545d0c91c3e7e0f258c64a589df283f874))
* discovery, manifest, and exporter (incremental) ([#10](https://github.com/rubicon/claude-session-exporter/issues/10)) ([2d917ca](https://github.com/rubicon/claude-session-exporter/commit/2d917caca43443fa41cd346c9c349bb1ba1bfa3b))


### Bug Fixes

* harden filename collisions, unicode slugs, and YAML frontmatter ([#12](https://github.com/rubicon/claude-session-exporter/issues/12)) ([7f96602](https://github.com/rubicon/claude-session-exporter/commit/7f966025224d11d3329b13c2ecc06f3dba74a7b6))


### Documentation

* note history-rewrite signing gotcha in CLAUDE.md ([#14](https://github.com/rubicon/claude-session-exporter/issues/14)) ([e4845db](https://github.com/rubicon/claude-session-exporter/commit/e4845dbfc681447ca2e3a3801b734bd16e73952a))

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
