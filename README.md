# claude-session-exporter

`claude-session-exporter` exports Claude Code and Claude cowork sessions to readable Markdown files with YAML frontmatter, discovering sessions incrementally so repeated runs only export what changed. It renders each session's conversation turns, tool activity, and subagent sidechains into a single Markdown document per session, organized by source and project.

Status: in development.

## Install

```bash
pip install claude-session-exporter
```

(Not yet published. Follow along in [CHANGELOG.md](CHANGELOG.md) for release status.)

## License

MIT — see [LICENSE](LICENSE).
