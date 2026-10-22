from pathlib import Path

import pytest

from transcript_shaker.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
PAGINATED = FIXTURES / "codex_paginated.jsonl"


def test_stdout(capsys):
    assert main([str(PAGINATED)]) == 0
    assert capsys.readouterr().out.startswith("# Transcript · codex · ")


def test_out_file(tmp_path, capsys):
    target = tmp_path / "out.md"
    assert main([str(PAGINATED), "--out", str(target)]) == 0
    assert capsys.readouterr().out == ""
    assert target.read_text(encoding="utf-8").startswith("# Transcript · codex · ")


def test_out_file_creates_missing_parent_dir(tmp_path, capsys):
    target = tmp_path / "nested" / "dir" / "out.md"
    assert main([str(PAGINATED), "--out", str(target)]) == 0
    assert capsys.readouterr().out == ""
    assert target.read_text(encoding="utf-8").startswith("# Transcript · codex · ")


def test_max_chars_applies_to_tool_result(capsys):
    assert main([str(PAGINATED), "--max-chars", "10"]) == 0
    out = capsys.readouterr().out
    assert "DEMO_OUTPU\n[... truncated 108 chars ...]" in out


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "nope.jsonl")]) == 1
    assert "file not found" in capsys.readouterr().err


def test_unsupported_format(tmp_path, capsys):
    path = tmp_path / "other.json"
    path.write_text('{"hello": "world"}', encoding="utf-8")
    assert main([str(path)]) == 1
    assert "unsupported transcript format" in capsys.readouterr().err


def test_format_yaml(capsys):
    assert main([str(PAGINATED), "--format", "yaml"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("harness: codex\n")
    assert "profile: default\n" in out


def test_profile_compact_stays_a_transcript(capsys):
    assert main([str(PAGINATED), "--profile", "compact"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Transcript · codex · ")
    assert "- profile: compact" in out
    assert "# Transcript digest" not in out


def test_digest_is_not_a_script_profile(capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(PAGINATED), "--profile", "digest"])
    assert exc.value.code == 2


def test_max_chars_requires_default_profile(capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(PAGINATED), "--profile", "full", "--max-chars", "10"])
    assert exc.value.code == 2


def test_list_rejects_profile_and_format(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--list", "--profile", "compact"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main(["--list", "--format", "yaml"])
    assert exc.value.code == 2
