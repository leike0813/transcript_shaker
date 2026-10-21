from pathlib import Path

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
