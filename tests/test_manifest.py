# SPDX-License-Identifier: MIT
from pathlib import Path

from claude_session_exporter.manifest import MANIFEST_NAME, Manifest
from claude_session_exporter.models import Session


def _session(mtime=100.0, size=10):
    return Session(
        source_type="cowork",
        session_id="abc",
        source_file=Path("/x.jsonl"),
        project="p",
        project_path="/c",
        mtime=mtime,
        size=size,
    )


def test_new_then_unchanged_then_updated(tmp_path):
    m = Manifest.load(tmp_path)
    s = _session()
    assert m.classify(s) == "new"
    m.update(s, tmp_path / "cowork" / "p" / "f.md", "Title")
    m.save()

    m2 = Manifest.load(tmp_path)
    assert (tmp_path / MANIFEST_NAME).exists()
    assert m2.classify(_session()) == "unchanged"
    assert m2.classify(_session(mtime=200.0)) == "updated"
    assert m2.classify(_session(size=99)) == "updated"


def test_output_path_for(tmp_path):
    m = Manifest.load(tmp_path)
    s = _session()
    m.update(s, tmp_path / "old.md", "Title")
    assert m.output_path_for("abc") == str(tmp_path / "old.md")
    assert m.output_path_for("missing") is None


def test_claimed_paths_excludes_given_session(tmp_path):
    m = Manifest.load(tmp_path)
    s1 = _session()
    s2 = Session(
        source_type="cowork",
        session_id="def",
        source_file=Path("/y.jsonl"),
        project="p",
        project_path="/c",
        mtime=100.0,
        size=10,
    )
    m.update(s1, tmp_path / "a.md", "Title A")
    m.update(s2, tmp_path / "b.md", "Title B")
    assert m.claimed_paths("abc") == {str(tmp_path / "b.md")}
    assert m.claimed_paths("def") == {str(tmp_path / "a.md")}
    assert m.claimed_paths("zzz") == {str(tmp_path / "a.md"), str(tmp_path / "b.md")}
