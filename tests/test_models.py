# SPDX-License-Identifier: MIT
from pathlib import Path

from claude_session_exporter.models import Message, Report, Session, Subagent


def test_defaults():
    m = Message(role="user", timestamp=None, text="hi")
    assert m.tool_notes == []
    s = Session(
        source_type="cowork",
        session_id="abc",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )
    assert s.subagent_files == [] and s.mtime == 0.0 and s.size == 0
    assert Subagent(label="agent-1", messages=[]).messages == []
    r = Report()
    assert r.exported == [] and r.failed == []
