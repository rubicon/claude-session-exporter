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
    if show or not set_output:
        cfg = config.load(path)
        typer.echo(
            f"output_dir = {cfg.output_dir}\nsources = {cfg.sources}\n"
            f"emoji_headers = {cfg.emoji_headers}\ninclude_subagents = {cfg.include_subagents}"
        )


# Register the config command under the name "config" (avoids shadowing the module).
app.command(name="config")(config_cmd)
