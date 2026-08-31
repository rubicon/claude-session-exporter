# SPDX-License-Identifier: MIT
import json

from typer.testing import CliRunner

from claude_session_exporter.cli import app

runner = CliRunner()


def test_full_run_with_subagent(tmp_path, monkeypatch):
    base = tmp_path / "cowork"
    sess = base / "skills-plugin" / "org" / "local_a" / ".claude" / "projects" / "-enc-output-x"
    sess.mkdir(parents=True)
    (sess / "abcd1234-0000-0000-0000-000000000000.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/sandbox/outputs", "timestamp": "2026-07-06T10:00:00Z"})
        + "\n"
        + json.dumps(
            {
                "type": "user",
                "timestamp": "2026-07-06T10:00:01Z",
                "message": {"content": "Build the corpus"},
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "timestamp": "2026-07-06T10:00:02Z",
                "message": {"content": [{"type": "text", "text": "on it"}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    subs = sess / "abcd1234-0000-0000-0000-000000000000" / "subagents"
    subs.mkdir(parents=True)
    (subs / "agent-xyz.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "subagent task"}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("claude_session_exporter.discovery.COWORK_ROOT", base)

    out = tmp_path / "out"
    cfg = tmp_path / "config.toml"
    result = runner.invoke(
        app, ["export", "--source", "cowork", "--output", str(out), "--config-path", str(cfg)]
    )
    assert result.exit_code == 0
    md = out / "cowork" / "skills-plugin" / "2026-07-06_build-the-corpus.md"
    text = md.read_text(encoding="utf-8")
    assert "subagent_count: 1" in text
    assert "## Subagent runs" in text
    assert "subagent task" in text
