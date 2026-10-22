from datetime import date, datetime, timedelta
import os
from pathlib import Path

import pytest

from transcript_shaker.adapters import ADAPTERS
from transcript_shaker.cli import main
from transcript_shaker.locate import HARNESS_SOURCES, find_candidates

# harness -> 相对 $HOME 的候选路径
SAMPLES = {
    "codex": ".codex/sessions/2026/10/21/rollout-2026-10-21T09-00-00-abc.jsonl",
    "claude-code": ".claude/projects/proj/11111111-1111-1111-1111-111111111111.jsonl",
    "omp": ".omp/agent/sessions/proj/2026-10-21T09-00-00-000Z_abc.jsonl",
    "kimi-code": ".kimi-code/sessions/wd_demo/session_abc/agents/main/wire.jsonl",
    "deepseek-harness": ".dsh/sessions/-proj-/session-abc/session.jsonl.zstd",
}


def _touch(path: Path, when: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not a transcript", encoding="utf-8")
    ts = when.timestamp()
    os.utime(path, (ts, ts))


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return tmp_path


def _build_samples(home: Path) -> dict:
    base = datetime(2026, 10, 21, 12, 0, 0)
    made = {}
    for offset, (harness, rel) in enumerate(SAMPLES.items()):
        path = home / rel
        _touch(path, base - timedelta(hours=offset))
        made[harness] = path
    return made


def test_sources_cover_every_adapter():
    assert set(HARNESS_SOURCES) == {adapter.name for adapter in ADAPTERS}


def test_lists_candidates_sorted_by_mtime(home):
    made = _build_samples(home)
    candidates = find_candidates()
    assert len(candidates) == len(SAMPLES)
    assert [c.harness for c in candidates] == list(SAMPLES)
    assert [c.path for c in candidates] == [made[name] for name in SAMPLES]
    stamps = [c.mtime.timestamp() for c in candidates]
    assert stamps == sorted(stamps, reverse=True)


def test_harness_filter(home):
    _build_samples(home)
    candidates = find_candidates(harnesses=["codex"])
    assert [(c.harness, c.path.name) for c in candidates] == [
        ("codex", Path(SAMPLES["codex"]).name)
    ]


def test_since_filter(home):
    made = _build_samples(home)
    day = datetime(2026, 10, 21, 12, 0, 0).date()
    assert [c.path for c in find_candidates(since=day)] == list(made.values())
    assert find_candidates(since=day + timedelta(days=1)) == []


def test_cli_list_shape(home, capsys):
    _build_samples(home)
    assert main(["--list", "--limit", "1"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "# candidates: 1"
    assert len(lines) == 2
    assert len(lines[1].split("\t")) == 3


def test_cli_list_empty(home, capsys):
    assert main(["--list"]) == 0
    assert capsys.readouterr().out == "# candidates: 0\n"


def test_cli_list_ignores_content(home, capsys):
    path = home / SAMPLES["omp"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not a transcript at all", encoding="utf-8")
    assert main(["--list"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "# candidates: 1"
    assert str(path) in out


def test_codex_home_override(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "cx"))
    path = tmp_path / "cx" / SAMPLES["codex"].split("/", 1)[1]
    _touch(path, datetime(2026, 10, 21, 9, 0, 0))
    assert main(["--list", "--harness", "codex"]) == 0
    assert str(path) in capsys.readouterr().out


def test_list_rejects_positional(home):
    with pytest.raises(SystemExit) as exc:
        main(["--list", "x.jsonl"])
    assert exc.value.code == 2


def test_requires_transcript_or_list(home):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_filter_flags_require_list(home):
    with pytest.raises(SystemExit) as exc:
        main(["--harness", "codex"])
    assert exc.value.code == 2


def test_skips_zero_byte_candidates(home):
    path = home / ".codebuddy/projects/proj/empty.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("", encoding="utf-8")
    assert find_candidates(harnesses=["codebuddy"]) == []


def test_skips_declared_non_transcript_names(home):
    real = home / ".commandcode/projects/proj/abc.jsonl"
    _touch(real, datetime(2026, 10, 21, 9, 0, 0))
    checkpoint = home / ".commandcode/projects/proj/abc.checkpoints.jsonl"
    checkpoint.write_text("{}", encoding="utf-8")
    assert [c.path for c in find_candidates(harnesses=["command-code"])] == [real]


def test_match_filters_on_path(home):
    wanted = home / ".omp/agent/sessions/-Workspace-Code-RiskFlow/2026-10-21T09-00-00-000Z_a.jsonl"
    _touch(wanted, datetime(2026, 10, 21, 9, 0, 0))
    other = home / ".omp/agent/sessions/-other/2026-10-21T09-00-00-000Z_b.jsonl"
    _touch(other, datetime(2026, 10, 21, 8, 0, 0))
    assert [c.path for c in find_candidates(harnesses=["omp"], match="riskflow")] == [wanted]
    assert [c.path for c in find_candidates(harnesses=["omp"], match="RISKFLOW")] == [wanted]


def test_cli_match_filters_and_rejects_transcribe(home, capsys):
    wanted = home / ".omp/agent/sessions/-Workspace-Code-RiskFlow/2026-10-21T09-00-00-000Z_a.jsonl"
    _touch(wanted, datetime(2026, 10, 21, 9, 0, 0))
    other = home / ".omp/agent/sessions/-other/2026-10-21T09-00-00-000Z_b.jsonl"
    _touch(other, datetime(2026, 10, 21, 8, 0, 0))
    assert main(["--list", "--match", "riskflow"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "# candidates: 1"
    assert str(wanted) in out[1]
    with pytest.raises(SystemExit) as exc:
        main(["--match", "riskflow", "some.jsonl"])
    assert exc.value.code == 2
