# Contributing

Thanks for your interest in contributing to `claude-session-exporter`.

## Process

- **Open an issue first.** Every non-trivial change (features, bug fixes, refactors, CI, docs affecting behavior) starts with a GitHub issue describing scope, intent, and acceptance criteria. Typo fixes, metadata-only cleanup, and comment-only changes may skip this.
- **Branch per issue.** Branch names follow `dev/<issue-number>-<short-kebab-description>`, e.g. `dev/12-fix-slug-collisions`.
- **Commits.**
  - Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`, `build`, `perf`, `revert`, `style`).
  - Commits must be signed.
  - Keep commits focused; don't mix unrelated changes.
- **Pull requests.**
  - Every branch merges through a PR, even for solo development.
  - PR body includes what changed, why, how it was verified, and closes its issue with `Closes #N`.
  - Do not merge with failing checks.

## Development setup

```bash
git clone https://github.com/rubicon/claude-session-exporter.git
cd claude-session-exporter
pip install -e ".[dev]"
```

## Verification

Before opening a PR, run:

```bash
ruff check .
black --check .
pytest -q
```

All three must pass. CI runs the same checks on every PR.

## Code style

- Python 3.11+, formatted with Black (line length 100) and linted with Ruff.
- Add `# SPDX-License-Identifier: MIT` to the top of new `.py` source files.
- Prefer small, focused pull requests over large ones.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful and constructive.
