# CLAUDE.md — claude-session-exporter

This is a public GitHub repository (`rubicon/claude-session-exporter`). Agent work in this repo follows the maintainer's general repository process policy (`~/.claude/policies/general-repository-process-policy.md`), which governs issues, branches, commits, PRs, and releases here. This file records only what is specific to this repo; it never restates that policy.

## Process specifics

- Canonical host for this repo is GitHub (public/open source), not Forgejo.
- Every issue gets its own worktree and branch: `git worktree add worktrees/dev-<issue>-<slug> -b dev/<issue>-<slug> main`.
- Commits are signed, Conventional Commits, one focused change per commit.
- PRs close their issue with `Closes #N`; no direct pushes to `main`.
- No AI-authorship trailers or "Generated with..." lines in commits, PRs, or files.

## Project context

- Design spec: `docs/superpowers/specs/2026-07-06-claude-session-exporter-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-07-06-claude-session-exporter-core-cli.md` (task-by-task, issue/branch grouping, file structure).
- Module map and layering: see `ARCHITECTURE.md`.

## Rewriting history (gotcha)

GitHub verifies an SSH commit signature only when the **committer** email owns the signing key. Squash-merges stamp committer `noreply@github.com` (GitHub-signed, verified). If you rewrite history, set the committer to `98216+rubicon@users.noreply.github.com` and re-sign (`git commit-tree -S`), or commits show unverified (`unknown_key`). Force-pushing protected `main` requires lifting branch protection then restoring it.

## Verification baseline

```bash
pip install -e ".[dev]"
ruff check .
black --check .
pytest -q
```

All three must pass before a commit lands on a PR branch.

## Tech stack

Python 3.11+, Typer (+ Rich), stdlib `tomllib`, `tomli-w`, pytest, Black, Ruff. `SPDX-License-Identifier: MIT` header on every `.py` source file.
