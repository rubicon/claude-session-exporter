# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter.manifest import Manifest, MANIFEST_NAME
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
