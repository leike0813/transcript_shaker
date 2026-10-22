from transcript_shaker.model import Event, Session
from transcript_shaker.render import prepare_compact, render_markdown, render_yaml


def _session(**overrides):
    base = dict(harness="codex", source="/tmp/x.jsonl", session_id="sid", cwd="/tmp",
                started="2026-01-01T00:00:00Z")
    base.update(overrides)
    return Session(**base)


def _compact(session, events):
    return render_markdown(session, prepare_compact(events), max_chars=0, profile="compact")


def test_caps_message_text_by_role():
    doc = _compact(
        _session(),
        [
            Event(kind="message", role="system", text="s" * 400),
            Event(kind="message", role="user", text="u" * 1300),
            Event(kind="message", role="assistant", text="a" * 1300),
        ],
    )
    assert doc.startswith("# Transcript · codex · 2026-01-01T00:00:00Z\n")
    assert "s" * 300 + "\n[... truncated 100 chars ...]" in doc
    assert "u" * 1200 + "\n[... truncated 100 chars ...]" in doc
    assert "a" * 1200 + "\n[... truncated 100 chars ...]" in doc


def test_keeps_shell_command_head_and_drops_results():
    doc = _compact(
        _session(),
        [
            Event(kind="tool", tool="exec_command", call="q" * 300, result="RESULT_NOISE"),
            Event(kind="tool", tool="read_file", call="CALL_NOISE", result="RESULT_NOISE"),
        ],
    )
    assert "q" * 160 + "\n[... truncated 140 chars ...]" in doc
    assert "CALL_NOISE" not in doc and "RESULT_NOISE" not in doc
    assert "## 2 · tool · read_file" in doc


def test_keeps_one_section_per_event():
    same = Event(kind="tool", tool="exec_command", call="pytest -q")
    doc = _compact(_session(), [same, same, same])
    assert "- events: 3" in doc
    assert "## 1 · tool · exec_command" in doc
    assert "## 2 · tool · exec_command" in doc
    assert "## 3 · tool · exec_command" in doc
    assert "×3" not in doc


def test_yaml_drops_results_and_non_shell_calls():
    doc = render_yaml(
        _session(),
        prepare_compact(
            [
                Event(kind="message", role="user", text="hi"),
                Event(kind="tool", tool="bash", call="ls", result="out"),
                Event(kind="tool", tool="read_file", call="secret", result="out"),
            ]
        ),
        max_chars=0,
        profile="compact",
    )
    assert "profile: compact\n" in doc
    assert "result:" not in doc and "secret" not in doc
    assert "  - kind: tool\n    tool: bash\n    call: ls\n" in doc
    assert "  - kind: tool\n    tool: read_file\n" in doc


def test_default_profile_keeps_its_document_shape():
    doc = render_markdown(_session(), [Event(kind="message", role="user", text="hi")])
    assert "- profile:" not in doc
    assert render_yaml(_session(), []).startswith("harness: codex\nprofile: default\n")
