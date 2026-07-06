# claude-session-exporter

`claude-session-exporter` exports Claude Code and Claude cowork sessions to readable Markdown files with YAML frontmatter, discovering sessions incrementally so repeated runs only export what changed. It renders each session's conversation turns, tool activity, and subagent sidechains into a single Markdown document per session, organized by source and project.

Status: in development.

## Install

```bash
uv tool install .
# or
pipx install .
```

(Not yet published to PyPI. Follow along in [CHANGELOG.md](CHANGELOG.md) for release status.)

## Usage

```bash
# Export everything new/updated from all configured sources
claude-session-exporter export --all

# Export a specific source, filtered by project and date range
claude-session-exporter export --source claude-code --project my-project --since 2026-01-01

# See what would be exported without writing anything
claude-session-exporter export --all --dry-run

# Re-export ignoring the manifest (overwrite existing output)
claude-session-exporter export --all --force

# Exclude subagent sidechains from the export
claude-session-exporter export --all --no-subagents

# List discovered sessions without exporting
claude-session-exporter list --source claude-code

# Show or update configuration
claude-session-exporter config --show
claude-session-exporter config --set-output ~/exports/claude-sessions
```

`export` supports `--source` (`cowork` | `claude-code`, repeatable), `--project` (repeatable), `--since`/`--until` (`YYYY-MM-DD`), `--output` (override the configured output directory), `--all` (skip filters, export everything new/updated), `--force` (ignore the manifest), `--no-subagents`, and `--dry-run` (report only, write nothing).

Repeated runs are incremental: each export is tracked in a `.claude-export-manifest.json` manifest at the output root, so unchanged sessions are skipped on subsequent runs.

### Automating with cron

```cron
0 * * * * /usr/bin/env claude-session-exporter export --all
```

## License

MIT — see [LICENSE](LICENSE).
