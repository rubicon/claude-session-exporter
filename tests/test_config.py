# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter import config


def test_first_run_creates_default(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg = config.load(cfg_path)
    assert cfg_path.exists()
    assert cfg.sources == ["cowork", "claude-code"]
    assert cfg.emoji_headers is False
    assert cfg.include_subagents is True
    assert cfg.output_dir == config.DEFAULT_OUTPUT


def test_reads_existing_values(tmp_path):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        'output_dir = "/tmp/exports"\nsources = ["cowork"]\n'
        "emoji_headers = true\ninclude_subagents = false\n",
        encoding="utf-8",
    )
    cfg = config.load(cfg_path)
    assert cfg.output_dir == Path("/tmp/exports")
    assert cfg.sources == ["cowork"]
    assert cfg.emoji_headers is True
    assert cfg.include_subagents is False
