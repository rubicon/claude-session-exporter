# SPDX-License-Identifier: MIT
from pathlib import Path
from claude_session_exporter import renderer
from claude_session_exporter.models import Session, Message, Subagent


def _session():
    return Session(
        source_type="cowork",
        session_id="076f4d83",
        source_file=Path("/x.jsonl"),
        project="skills-plugin",
        project_path="/cwd",
    )


def test_render_has_frontmatter_and_turns():
    msgs = [
        Message("user", "2026-07-06T10:00:00Z", "hello"),
        Message("assistant", "2026-07-06T10:00:01Z", "hi", ["tool call `Bash` — {}"]),
    ]
    out = renderer.render(
        _session(),
        msgs,
        [],
        title="Hello",
        created="2026-07-06T10:00:00Z",
        updated="2026-07-06T10:00:01Z",
    )
    assert out.startswith("---\n")
    assert "session_id: 076f4d83" in out
    assert "source_type: cowork" in out
    assert "user_messages: 1" in out
    assert "assistant_messages: 1" in out
    assert "subagent_count: 0" in out
    assert "# Hello" in out
    assert "## You" in out and "## Claude" in out
    assert "<details><summary>tool activity</summary>" in out
    assert "🧑" not in out  # emoji off by default


def test_render_includes_subagents_section():
    sub = Subagent("agent-a420", [Message("user", None, "You are building X")])
    out = renderer.render(
        _session(),
        [Message("user", None, "go")],
        [sub],
        title="T",
        created=None,
        updated=None,
    )
    assert "subagent_count: 1" in out
    assert "## Subagent runs" in out
    assert "<details><summary>subagent: agent-a420</summary>" in out
    assert "You are building X" in out


def test_render_emoji_mode():
    out = renderer.render(
        _session(),
        [Message("user", None, "hi")],
        [],
        title="T",
        created=None,
        updated=None,
        emoji=True,
    )
    assert "🧑 You" in out and "🤖 Claude" not in out  # only user turn present


def test_render_escapes_title_in_frontmatter():
    out = renderer.render(
        _session(),
        [Message("user", None, "hi")],
        [],
        title="Fix: the parser breaks",
        created=None,
        updated=None,
    )
    assert 'title: "Fix: the parser breaks"' in out


def test_fmt_ts_rejects_non_str():
    assert renderer._fmt_ts(12345) == ""
