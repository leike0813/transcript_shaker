"""各 harness adapter 的识别、事件序列与工具配对。

fixture 全部是合成数据：每个文件都有 1 条 user、1 条 assistant、1 个工具调用与结果、
1 段 thinking marker、以及至少 1 条该 harness 特有的噪音记录。
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pytest

from transcript_shaker.adapters import UnsupportedTranscript, detect_adapter, supported_harnesses
from transcript_shaker.adapters._support import iso_from_ms
from transcript_shaker.adapters.deepseek_harness import DeepseekHarnessAdapter

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class Case:
    harness: str
    path: Path
    labels: Tuple[Tuple[str, str], ...]
    thinking: str
    tool: str
    result: str
    session_id: str
    cwd: str = ""
    started: str = ""


CASES = [
    Case(
        harness="claude-code",
        path=FIXTURES / "claude_code.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "Bash")),
        thinking="THINKING_PROBE_CLAUDE",
        tool="Bash",
        result="CLAUDE_RESULT",
        session_id="claude-session",
        cwd="/tmp/claude",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="qwen-code",
        path=FIXTURES / "qwen_code.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "run_shell_command")),
        thinking="THINKING_PROBE_QWEN",
        tool="run_shell_command",
        result="QWEN_RESULT",
        session_id="qwen-session",
        cwd="/tmp/qwen",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="command-code",
        path=FIXTURES / "command_code.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "shell_command")),
        thinking="THINKING_PROBE_COMMAND",
        tool="shell_command",
        result="COMMAND_RESULT",
        session_id="command-session",
        cwd="/tmp/command",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="codebuddy",
        path=FIXTURES / "codebuddy.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "Bash")),
        thinking="THINKING_PROBE_CODEBUDDY",
        tool="Bash",
        result="CODEBUDDY_RESULT",
        session_id="codebuddy-session",
        cwd="/tmp/codebuddy",
        started=iso_from_ms(1791000000000),
    ),
    Case(
        harness="pi",
        path=FIXTURES / "pi.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "bash")),
        thinking="THINKING_PROBE_PI",
        tool="bash",
        result="PI_RESULT",
        session_id="pi-session",
        cwd="/tmp/pi",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="omp",
        path=FIXTURES / "omp.jsonl",
        labels=(("message", "user"), ("message", "system"), ("message", "assistant"), ("tool", "bash")),
        thinking="THINKING_PROBE_OMP",
        tool="bash",
        result="OMP_RESULT",
        session_id="omp-session",
        cwd="/tmp/omp",
        started="2026-10-21T09:00:00.100Z",
    ),
    Case(
        harness="minimax-code",
        path=FIXTURES / "minimax_demo" / "messages.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "bash")),
        thinking="THINKING_PROBE_MINIMAX",
        tool="bash",
        result="MINIMAX_RESULT",
        session_id="mvs_demo",
        started=iso_from_ms(1791000000000),
    ),
    Case(
        harness="gemini-cli",
        path=FIXTURES / "gemini.json",
        labels=(
            ("message", "user"),
            ("message", "assistant"),
            ("tool", "run_shell_command"),
            ("message", "system"),
        ),
        thinking="THINKING_PROBE_GEMINI",
        tool="run_shell_command",
        result="GEMINI_RESULT",
        session_id="gemini-session",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="cline",
        path=FIXTURES / "cline_demo" / "1791000000000_demo.messages.json",
        labels=(
            ("message", "system"),
            ("message", "user"),
            ("message", "assistant"),
            ("tool", "run_commands"),
        ),
        thinking="THINKING_PROBE_CLINE",
        tool="run_commands",
        result="CLINE_RESULT",
        session_id="cline-session",
        cwd="/tmp/cline",
        started="2026-10-21T08:59:00.000Z",
    ),
    Case(
        harness="multicoder",
        path=FIXTURES / "multicoder.json",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "tool-execute")),
        thinking="THINKING_PROBE_MULTICODER",
        tool="tool-execute",
        result="MULTICODER_RESULT",
        session_id="ses_demo",
        cwd="/tmp/multicoder",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="grok",
        path=FIXTURES / "grok_demo" / "chat_history.jsonl",
        labels=(
            ("message", "system"),
            ("message", "user"),
            ("message", "assistant"),
            ("tool", "run_terminal_command"),
        ),
        thinking="THINKING_PROBE_GROK",
        tool="run_terminal_command",
        result="GROK_RESULT",
        session_id="grok_demo",
        cwd="/tmp/grok",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="kimi-code",
        path=FIXTURES / "kimi_demo" / "session_demo" / "agents" / "main" / "wire.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "Bash")),
        thinking="THINKING_PROBE_KIMI",
        tool="Bash",
        result="KIMI_RESULT",
        session_id="demo",
        cwd="/tmp/kimi",
        started="2026-10-21T09:00:00.000Z",
    ),
    Case(
        harness="deepseek-harness",
        path=FIXTURES / "dsh_session.jsonl",
        labels=(("message", "user"), ("message", "assistant"), ("tool", "bash")),
        thinking="THINKING_PROBE_DSH",
        tool="bash",
        result="DSH_RESULT",
        session_id="dsh-session",
        cwd="/tmp/dsh",
        started=iso_from_ms(1791000000000),
    ),
]

IDS = [case.harness for case in CASES]


def _labels(events):
    return tuple((event.kind, event.role or event.tool) for event in events)


def _blob(events):
    return json.dumps([event.__dict__ for event in events], ensure_ascii=False)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_detects_expected_harness(case):
    assert detect_adapter(case.path).name == case.harness


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_event_sequence(case):
    _, events = detect_adapter(case.path).parse(case.path)
    assert _labels(events) == case.labels


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_thinking_is_dropped(case):
    _, events = detect_adapter(case.path).parse(case.path)
    assert case.thinking not in _blob(events)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_tool_result_is_paired(case):
    _, events = detect_adapter(case.path).parse(case.path)
    tool = next(event for event in events if event.kind == "tool")
    assert tool.tool == case.tool
    assert tool.result == case.result


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_session_metadata(case):
    adapter = detect_adapter(case.path)
    session, _ = adapter.parse(case.path)
    assert session.session_id == case.session_id
    assert session.cwd == case.cwd
    assert session.started == case.started


def test_supported_harnesses_lists_every_adapter():
    names = supported_harnesses().split("、")
    assert sorted(names) == sorted([case.harness for case in CASES] + ["codex", "kilo-code"])


def test_omp_custom_tool_execution_does_not_duplicate_tool():
    path = FIXTURES / "omp.jsonl"
    _, events = detect_adapter(path).parse(path)
    assert sum(1 for event in events if event.kind == "tool") == 1
    assert "tool_execution_start" not in _blob(events)


def test_codebuddy_summary_does_not_produce_message():
    path = FIXTURES / "codebuddy.jsonl"
    _, events = detect_adapter(path).parse(path)
    assert "CODEBUDDY_SUMMARY_NOISE" not in _blob(events)


def test_grok_synthetic_user_is_skipped():
    path = FIXTURES / "grok_demo" / "chat_history.jsonl"
    _, events = detect_adapter(path).parse(path)
    assert "GROK_SYNTHETIC" not in _blob(events)


def test_grok_session_without_reply_is_detected():
    path = FIXTURES / "grok_partial" / "chat_history.jsonl"
    adapter = detect_adapter(path)
    assert adapter.name == "grok"
    session, events = adapter.parse(path)
    assert [event.role for event in events] == ["system", "user"]
    assert "GROK_PARTIAL_SYNTHETIC" not in _blob(events)
    assert session.session_id == "grok_partial"


def test_kimi_session_without_messages_is_detected():
    path = FIXTURES / "kimi_empty" / "session_empty" / "agents" / "main" / "wire.jsonl"
    adapter = detect_adapter(path)
    assert adapter.name == "kimi-code"
    session, events = adapter.parse(path)
    assert events == []
    assert session.session_id == "empty"


def test_dsh_replaced_message_is_skipped():
    path = FIXTURES / "dsh_session.jsonl"
    _, events = detect_adapter(path).parse(path)
    assert "DSH_REPLACED_NOISE" not in _blob(events)


@pytest.mark.skipif(shutil.which("zstd") is None, reason="zstd 命令行不可用")
def test_dsh_zstd_matches_plain_jsonl(tmp_path):
    plain = FIXTURES / "dsh_session.jsonl"
    packed = tmp_path / "session.v4.jsonl.zstd"
    subprocess.run(["zstd", "-q", "-f", str(plain), "-o", str(packed)], check=True)

    assert detect_adapter(packed).name == "deepseek-harness"
    plain_session, plain_events = DeepseekHarnessAdapter().parse(plain)
    packed_session, packed_events = DeepseekHarnessAdapter().parse(packed)
    assert [event.__dict__ for event in packed_events] == [event.__dict__ for event in plain_events]
    plain_meta = {key: value for key, value in plain_session.__dict__.items() if key != "source"}
    packed_meta = {key: value for key, value in packed_session.__dict__.items() if key != "source"}
    assert packed_meta == plain_meta


def test_dsh_session_header_alone_is_detected(tmp_path):
    """会话在任何消息前中断时，只剩会话头，仍应识别为 dsh 并输出空事件流。"""
    path = tmp_path / "session.v4.jsonl"
    header = {"type": "session", "version": 4, "id": "header-only", "createdAt": 1791000000000, "cwd": "/tmp/dsh"}
    path.write_text(json.dumps(header) + "\n", encoding="utf-8")

    adapter = detect_adapter(path)
    assert adapter.name == "deepseek-harness"
    session, events = adapter.parse(path)
    assert session.session_id == "header-only"
    assert events == []


def _build_kilo_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, directory TEXT, time_created INTEGER)")
    conn.execute(
        "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT)"
    )
    conn.execute(
        "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, time_created INTEGER, data TEXT)"
    )

    def session(session_id: str, directory: str, created: int) -> None:
        conn.execute("INSERT INTO session VALUES (?, ?, ?)", (session_id, directory, created))

    def message(message_id: str, session_id: str, created: int, role: str) -> None:
        conn.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            (message_id, session_id, created, json.dumps({"role": role})),
        )

    def part(part_id: str, message_id: str, session_id: str, created: int, data: dict) -> None:
        conn.execute(
            "INSERT INTO part VALUES (?, ?, ?, ?, ?)",
            (part_id, message_id, session_id, created, json.dumps(data)),
        )

    session("ses_old", "/tmp/old", 1000)
    message("msg_old", "ses_old", 1001, "user")
    part("prt_old", "msg_old", "ses_old", 1002, {"type": "text", "text": "KILO_OLD_SESSION"})

    session("ses_new", "/tmp/kilo", 2000)
    message("msg_user", "ses_new", 2001, "user")
    part("prt_user", "msg_user", "ses_new", 2002, {"type": "text", "text": "KILO_USER"})
    message("msg_bot", "ses_new", 2003, "assistant")
    part("prt_reason", "msg_bot", "ses_new", 2004, {"type": "reasoning", "text": "THINKING_PROBE_KILO"})
    part("prt_bot", "msg_bot", "ses_new", 2005, {"type": "text", "text": "KILO_ANSWER"})
    part(
        "prt_tool",
        "msg_bot",
        "ses_new",
        2006,
        {
            "type": "tool",
            "tool": "read",
            "callID": "call_k1",
            "state": {"status": "completed", "input": {"filePath": "a.txt"}, "output": "KILO_RESULT"},
        },
    )
    conn.commit()
    conn.close()


def test_kilo_code_reads_latest_session_only(tmp_path):
    db = tmp_path / "kilo.db"
    _build_kilo_db(db)

    assert detect_adapter(db).name == "kilo-code"
    session, events = detect_adapter(db).parse(db)
    assert session.session_id == "ses_new"
    assert session.cwd == "/tmp/kilo"
    assert _labels(events) == (
        ("message", "user"),
        ("message", "assistant"),
        ("tool", "read"),
    )
    tool = next(event for event in events if event.kind == "tool")
    assert tool.result == "KILO_RESULT"
    blob = _blob(events)
    assert "KILO_OLD_SESSION" not in blob
    assert "THINKING_PROBE_KILO" not in blob


def test_sqlite_without_kilo_tables_is_not_detected(tmp_path):
    db = tmp_path / "other.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE notes (id TEXT)")
    conn.commit()
    conn.close()

    with pytest.raises(UnsupportedTranscript):
        detect_adapter(db)
