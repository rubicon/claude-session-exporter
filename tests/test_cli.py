# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from typer.testing import CliRunner
from claude_session_exporter.cli import app

runner = CliRunner()


def _seed_claude_code(root: Path, sid: str, text: str):
    d = root / "-Users-dax-proj"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/Users/dax/proj", "timestamp": "2026-07-06T10:00:00Z"})
        + "\n"
        + json.dumps({"type": "user", "message": {"content": text}})
        + "\n",
        encoding="utf-8",
    )


def test_export_command(tmp_path, monkeypatch):
    cc = tmp_path / "cc"
    _seed_claude_code(cc, "11111111-1111-1111-1111-111111111111", "Hello world")
    out = tmp_path / "out"
    cfg = tmp_path / "config.toml"
    monkeypatch.setattr("claude_session_exporter.discovery.CLAUDE_CODE_ROOT", cc)

    result = runner.invoke(
        app,
        [
            "export",
            "--source",
            "claude-code",
            "--output",
            str(out),
            "--config-path",
            str(cfg),
        ],
    )
    assert result.exit_code == 0
    assert (out / "claude-code" / "proj" / "2026-07-06_hello-world.md").exists()
    assert "exported" in result.output.lower()


def test_list_command_writes_nothing(tmp_path, monkeypatch):
    cc = tmp_path / "cc"
    _seed_claude_code(cc, "22222222-2222-2222-2222-222222222222", "List me")
    monkeypatch.setattr("claude_session_exporter.discovery.CLAUDE_CODE_ROOT", cc)
    cfg = tmp_path / "config.toml"
    result = runner.invoke(app, ["list", "--source", "claude-code", "--config-path", str(cfg)])
    assert result.exit_code == 0
    assert "2222" in result.output or "List me" in result.output.lower()
