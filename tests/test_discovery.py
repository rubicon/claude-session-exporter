# SPDX-License-Identifier: MIT
import json
from pathlib import Path
from claude_session_exporter import discovery


def _cc_session(root: Path, project_enc: str, sid: str, cwd: str):
    d = root / project_enc
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": cwd, "timestamp": "2026-07-06T10:00:00Z"})
        + "\n"
        + json.dumps({"type": "user", "message": {"content": "hi"}})
        + "\n",
        encoding="utf-8",
    )


def test_find_claude_code(tmp_path):
    cc = tmp_path / "claude" / "projects"
    _cc_session(cc, "-Users-dax-proj", "11111111-1111-1111-1111-111111111111", "/Users/dax/proj")
    sessions = discovery.find(["claude-code"], roots={"claude-code": cc})
    assert len(sessions) == 1
    s = sessions[0]
    assert s.source_type == "claude-code"
    assert s.session_id == "11111111-1111-1111-1111-111111111111"
    assert s.project == "proj"
    assert s.mtime > 0 and s.size > 0


def test_find_cowork_project_is_space_and_attaches_subagents(tmp_path):
    base = tmp_path / "cowork"
    sess_dir = (
        base / "skills-plugin" / "org1" / "local_aaa" / ".claude" / "projects" / "-enc-output-x"
    )
    sess_dir.mkdir(parents=True)
    (sess_dir / "22222222-2222-2222-2222-222222222222.jsonl").write_text(
        json.dumps({"type": "mode", "cwd": "/sandbox/outputs"}) + "\n", encoding="utf-8"
    )
    subs = sess_dir / "22222222-2222-2222-2222-222222222222" / "subagents"
    subs.mkdir(parents=True)
    (subs / "agent-abc.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "sub"}}) + "\n", encoding="utf-8"
    )
    (sess_dir / "audit.jsonl").write_text("{}\n", encoding="utf-8")  # must be ignored

    sessions = discovery.find(["cowork"], roots={"cowork": base})
    assert len(sessions) == 1
    s = sessions[0]
    assert s.source_type == "cowork"
    assert s.project == "skills-plugin"
    assert len(s.subagent_files) == 1
    assert s.subagent_files[0].name == "agent-abc.jsonl"


def test_audit_and_agent_files_are_not_sessions(tmp_path):
    base = tmp_path / "cowork"
    d = base / "spaceX" / "org" / "local_z" / ".claude" / "projects" / "-enc"
    d.mkdir(parents=True)
    (d / "audit.jsonl").write_text("{}\n", encoding="utf-8")
    (d / "agent-xyz.jsonl").write_text("{}\n", encoding="utf-8")
    assert discovery.find(["cowork"], roots={"cowork": base}) == []


def test_only_uuid_named_transcripts_are_sessions(tmp_path):
    d = tmp_path / "cc" / "-Users-dax-proj"
    d.mkdir(parents=True)
    rec = json.dumps({"type": "mode", "cwd": "/Users/dax/proj"}) + "\n"
    for name in ["notes.jsonl", "agent-x.jsonl", "audit.jsonl", "Agent-Y.jsonl"]:
        (d / name).write_text(rec, encoding="utf-8")
    (d / "12345678-1234-1234-1234-123456789abc.jsonl").write_text(rec, encoding="utf-8")
    sessions = discovery.find(["claude-code"], roots={"claude-code": tmp_path / "cc"})
    assert [s.session_id for s in sessions] == ["12345678-1234-1234-1234-123456789abc"]
