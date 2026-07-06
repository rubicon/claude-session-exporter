# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from claude_session_exporter import parser


def _write(tmp_path, records) -> Path:
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def test_parse_extracts_text_and_tools_and_skips_bad_lines(tmp_path):
    p = tmp_path / "s.jsonl"
    good = [
        {"type": "user", "timestamp": "2026-07-06T10:00:00Z", "message": {"content": "hello"}},
        {
            "type": "assistant",
            "timestamp": "2026-07-06T10:00:01Z",
            "message": {
                "content": [
                    {"type": "text", "text": "hi there"},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": "2026-07-06T10:00:02Z",
            "message": {
                "content": [
                    {"type": "tool_result", "content": [{"type": "text", "text": "a\nb"}]},
                ]
            },
        },
        {"type": "mode", "message": {"content": "ignored"}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in good) + "\nNOT JSON\n", encoding="utf-8")
    msgs = parser.parse(p)
    assert [m.role for m in msgs] == ["user", "assistant", "assistant"]
    assert msgs[0].text == "hello"
    assert "hi there" in msgs[1].text
    assert any("Bash" in n for n in msgs[1].tool_notes)
    assert any("tool result" in n for n in msgs[2].tool_notes)


def test_facts_reads_cwd_and_timestamps(tmp_path):
    p = _write(
        tmp_path,
        [
            {"type": "mode", "cwd": "/home/x/proj", "timestamp": "2026-07-06T10:00:00Z"},
            {"type": "user", "timestamp": "2026-07-06T10:05:00Z", "message": {"content": "q"}},
        ],
    )
    f = parser.facts(p)
    assert f["cwd"] == "/home/x/proj"
    assert f["created"] == "2026-07-06T10:00:00Z"
    assert f["updated"] == "2026-07-06T10:05:00Z"


def test_empty_file_yields_no_messages(tmp_path):
    p = tmp_path / "e.jsonl"
    p.write_text("", encoding="utf-8")
    assert parser.parse(p) == []


def test_tool_result_null_content_does_not_render_none(tmp_path):
    p = _write(
        tmp_path,
        [
            {
                "type": "assistant",
                "timestamp": "2026-07-06T10:00:00Z",
                "message": {
                    "content": [
                        {"type": "tool_result", "content": None},
                    ]
                },
            },
        ],
    )
    msgs = parser.parse(p)
    assert len(msgs) == 1
    assert not any("None" in n for n in msgs[0].tool_notes)
