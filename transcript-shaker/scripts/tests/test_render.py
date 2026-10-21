from transcript_shaker.model import Event, Session
from transcript_shaker.render import render_markdown, truncate


def _session(**overrides):
    base = dict(
        harness="codex",
        source="/tmp/x.jsonl",
        session_id="sid",
        cwd="/tmp",
        started="2026-01-01T00:00:00Z",
        version="0.163.0",
        originator="codex-tui",
        history="paginated",
    )
    base.update(overrides)
    return Session(**base)


def test_truncate_marks_omitted_count():
    out = truncate("a" * 20, 5)
    assert out.startswith("aaaaa")
    assert "[... truncated 15 chars ...]" in out


def test_truncate_keeps_short_text():
    assert truncate("short", 5) == "short"


def test_header_and_sections():
    events = [
        Event(kind="message", role="user", text="你好", ts="t1"),
        Event(kind="tool", tool="exec_command", call="ls -la", result="ok", status="completed", ts="t2"),
        Event(kind="message", role="assistant", text="完成", ts="t3"),
    ]
    doc = render_markdown(_session(), events)
    assert doc.startswith("# Transcript · codex · 2026-01-01T00:00:00Z\n")
    assert "- harness: codex" in doc
    assert "- events: 3 (user 1, assistant 1, tool 1)" in doc
    assert "## 1 · user · t1" in doc
    assert "## 2 · tool · exec_command · t2" in doc
    assert "- status: completed" in doc
    assert "```bash\nls -la\n```" in doc
    assert "```text\nok\n```" in doc


def test_truncates_tool_result_and_system_message_only():
    user_text = "u" * 50
    events = [
        Event(kind="message", role="user", text=user_text),
        Event(kind="tool", tool="exec_command", call="cat big", result="z" * 50),
        Event(kind="message", role="system", text="s" * 50),
    ]
    doc = render_markdown(_session(), events, max_chars=10)
    assert user_text in doc
    assert "z" * 10 + "\n[... truncated 40 chars ...]" in doc
    assert "s" * 10 + "\n[... truncated 40 chars ...]" in doc


def test_keeps_shell_command_full():
    command = "echo " + "q" * 100
    doc = render_markdown(
        _session(), [Event(kind="tool", tool="exec_command", call=command, result="ok")], max_chars=10
    )
    assert command in doc


def test_truncates_non_shell_call():
    call = "p" * 100
    doc = render_markdown(
        _session(), [Event(kind="tool", tool="mcp:demo.search", call=call, result="")], max_chars=10
    )
    assert "p" * 10 + "\n[... truncated 90 chars ...]" in doc


def test_escapes_fence():
    result = "```py\nprint(1)\n```"
    doc = render_markdown(_session(), [Event(kind="tool", tool="exec_command", call="ls", result=result)])
    assert "````text\n" in doc
    assert "````\n" in doc

    message = Event(kind="message", role="assistant", text=result)
    assert result in render_markdown(_session(), [message])


def test_omits_empty_optional_fields():
    doc = render_markdown(_session(session_id="", cwd="", originator="", version="", history=""), [])
    assert "- session:" not in doc
    assert "- cwd:" not in doc
    assert "- origin:" not in doc
    assert "- history:" not in doc
    assert "- events: 0" in doc
