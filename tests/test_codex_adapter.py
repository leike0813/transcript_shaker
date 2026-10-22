import json
import shutil
import subprocess
from pathlib import Path

import pytest

from transcript_shaker.adapters import UnsupportedTranscript, detect_adapter
from transcript_shaker.adapters.codex import CodexAdapter

FIXTURES = Path(__file__).parent / "fixtures"
PAGINATED = FIXTURES / "codex_paginated.jsonl"
LEGACY = FIXTURES / "codex_legacy.jsonl"


def _labels(events):
    return [(event.kind, event.role or event.tool) for event in events]


def test_paginated_events_and_dedup():
    session, events = CodexAdapter().parse(PAGINATED)
    assert session.history == "paginated"
    assert session.session_id == "paginated-session"
    assert _labels(events) == [
        ("message", "system"),
        ("message", "user"),
        ("message", "assistant"),
        ("tool", "exec_command"),
        ("tool", "mcp:demo.search"),
        ("tool", "file_change"),
    ]
    assert sum(1 for event in events if event.role == "assistant") == 1
    blob = json.dumps([event.__dict__ for event in events], ensure_ascii=False)
    assert "MIRROR_OUTPUT" not in blob


def test_paginated_drops_reasoning():
    _, events = CodexAdapter().parse(PAGINATED)
    blob = json.dumps([event.__dict__ for event in events], ensure_ascii=False)
    assert "PAGINATED_SECRET_REASONING" not in blob


def test_paginated_command_and_result():
    _, events = CodexAdapter().parse(PAGINATED)
    tool = next(event for event in events if event.tool == "exec_command")
    assert tool.call == "/bin/sh -lc 'ls -la'"
    assert tool.status == "completed"
    assert tool.result.startswith("DEMO_OUTPUT_0001")


def test_paginated_mcp_and_file_change():
    _, events = CodexAdapter().parse(PAGINATED)
    by_tool = {event.tool: event for event in events if event.kind == "tool"}
    assert by_tool["mcp:demo.search"].call == '{"query": "demo"}'
    assert by_tool["mcp:demo.search"].result == "mcp 结果"
    assert by_tool["file_change"].call == "/tmp/demo/a.txt (update)"
    assert "+new" in by_tool["file_change"].result


def test_legacy_call_output_pairing():
    session, events = CodexAdapter().parse(LEGACY)
    assert session.history == "legacy"
    by_tool = {event.tool: event for event in events if event.kind == "tool"}
    assert by_tool["mcp:demo.search"].call == '{"query":"demo"}'
    assert by_tool["mcp:demo.search"].result == "demo 搜索结果：三条命中。"
    assert by_tool["apply_patch"].result == "Success. Updated demo.md"


def test_legacy_roles_and_reasoning():
    _, events = CodexAdapter().parse(LEGACY)
    assert [event.role for event in events if event.kind == "message"] == ["user", "assistant", "system"]
    blob = json.dumps([event.__dict__ for event in events], ensure_ascii=False)
    assert "LEGACY_SECRET_REASONING" not in blob


def test_broken_and_unknown_lines_are_skipped(tmp_path):
    path = tmp_path / "broken.jsonl"
    path.write_text(
        PAGINATED.read_text(encoding="utf-8")
        + '{"type": "event_msg", "payload": {"type": "item_completed", "item": {"type": "Mystery"}}}\n'
        + "not json at all\n"
        + '{"type": "unknown_record"}\n',
        encoding="utf-8",
    )
    session, events = CodexAdapter().parse(path)
    assert session.history == "paginated"
    assert len(events) == 6


def test_detect_by_content_and_unknown(tmp_path):
    assert detect_adapter(PAGINATED).name == "codex"
    other = tmp_path / "other.json"
    other.write_text('{"hello": "world"}', encoding="utf-8")
    with pytest.raises(UnsupportedTranscript):
        detect_adapter(other)


def test_zst_matches_plain(tmp_path):
    zstd = shutil.which("zstd")
    if not zstd:
        pytest.skip("zstd 命令行不可用")
    target = tmp_path / "codex_paginated.jsonl.zst"
    subprocess.run([zstd, "-q", "-f", str(PAGINATED), "-o", str(target)], check=True)
    _, plain = CodexAdapter().parse(PAGINATED)
    _, compressed = CodexAdapter().parse(target)
    assert [event.__dict__ for event in compressed] == [event.__dict__ for event in plain]
