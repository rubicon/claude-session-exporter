# SPDX-License-Identifier: MIT
from pathlib import Path

from claude_session_exporter import naming
from claude_session_exporter.models import Session


def test_derive_title_trims_and_cleans():
    t = naming.derive_title(
        "```code```\n# Please **evaluate** this response now", "2026-07-06T10:00:00Z"
    )
    assert "`" not in t and "*" not in t and "#" not in t
    assert len(t) <= 60


def test_derive_title_fallback_when_empty():
    assert naming.derive_title("", "2026-07-06T10:00:00Z") == "untitled-2026-07-06"
    assert naming.derive_title(None, None) == "untitled-unknown"


def test_slugify():
    assert naming.slugify("I received this — Response!") == "i-received-this-response"
    assert naming.slugify("///") == "untitled"


def test_output_path_mirrors_source():
    s = Session(
        source_type="cowork",
        session_id="abc",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )
    p = naming.output_path(Path("/out"), s, "My Title", "2026-07-06T10:00:00Z")
    assert p == Path("/out/cowork/skills-plugin/2026-07-06_my-title.md")


def test_slugify_preserves_cjk():
    slug = naming.slugify("会议纪要：季度回顾")
    assert slug != "untitled"
    assert "会议" in slug


def test_disambiguate_no_collision_returns_base():
    base = Path("/o/a.md")
    assert naming.disambiguate(base, "abcd1234-ef00", set()) == base


def test_disambiguate_collision_uses_short_id_suffix():
    base = Path("/o/a.md")
    taken = {str(base)}
    result = naming.disambiguate(base, "abcd1234-ef00", taken)
    assert result == Path("/o/a_abcd1234.md")


def test_disambiguate_double_collision_uses_full_session_id():
    base = Path("/o/a.md")
    taken = {str(base), str(Path("/o/a_abcd1234.md"))}
    result = naming.disambiguate(base, "abcd1234-ef00", taken)
    assert result == Path("/o/a_abcd1234-ef00.md")
