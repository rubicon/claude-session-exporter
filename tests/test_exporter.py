# SPDX-License-Identifier: MIT
import json
from claude_session_exporter import exporter
from claude_session_exporter.models import Session


def _make_session(tmp_path, sid="abc", text="I received this response") -> Session:
    src = tmp_path / f"{sid}.jsonl"
    src.write_text(
        json.dumps({"type": "mode", "cwd": "/c", "timestamp": "2026-07-06T10:00:00Z"})
        + "\n"
        + json.dumps(
            {"type": "user", "timestamp": "2026-07-06T10:00:01Z", "message": {"content": text}}
        )
        + "\n",
        encoding="utf-8",
    )
    st = src.stat()
    return Session("cowork", sid, src, "skills-plugin", "/c", [], st.st_mtime, st.st_size)


def test_export_writes_markdown_and_manifest(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    report = exporter.export([s], out)
    assert report.exported == ["abc"]
    md = out / "cowork" / "skills-plugin" / "2026-07-06_i-received-this-response.md"
    assert md.exists()
    assert "session_id: abc" in md.read_text(encoding="utf-8")
    assert (out / ".claude-export-manifest.json").exists()


def test_second_run_skips_unchanged(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    exporter.export([s], out)
    report = exporter.export([s], out)
    assert report.skipped == ["abc"] and report.exported == []


def test_force_reexports(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    exporter.export([s], out)
    report = exporter.export([s], out, force=True)
    assert report.updated == ["abc"]


def test_dry_run_writes_nothing(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path)
    report = exporter.export([s], out, dry_run=True)
    assert report.exported == ["abc"]
    assert not out.exists()


def test_title_change_renames_old_file(tmp_path):
    out = tmp_path / "out"
    s = _make_session(tmp_path, text="First title")
    exporter.export([s], out)
    old = out / "cowork" / "skills-plugin" / "2026-07-06_first-title.md"
    assert old.exists()
    # rewrite source with new first message + bump mtime via new content
    s.source_file.write_text(
        json.dumps({"type": "mode", "cwd": "/c", "timestamp": "2026-07-06T10:00:00Z"})
        + "\n"
        + json.dumps(
            {
                "type": "user",
                "timestamp": "2026-07-06T10:00:01Z",
                "message": {"content": "Second title"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    st = s.source_file.stat()
    s.mtime, s.size = st.st_mtime + 1, st.st_size + 1  # force "updated"
    exporter.export([s], out)
    new = out / "cowork" / "skills-plugin" / "2026-07-06_second-title.md"
    assert new.exists() and not old.exists()
