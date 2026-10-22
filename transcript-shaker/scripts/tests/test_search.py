from datetime import datetime, timedelta
import os
from pathlib import Path

import pytest

from transcript_shaker.cli import main
from transcript_shaker.locate import Candidate
from transcript_shaker.search import Match, count_terms, is_ambiguous, render_matches, search, tokenize

BASE = datetime(2026, 10, 21, 12, 0, 0)


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return tmp_path


def _session(home: Path, name: str, project: str = "proj") -> Path:
    return home / f".omp/agent/sessions/-{project}/2026-10-21T09-00-00-000Z_{name}.jsonl"


def _write(path: Path, text: str, when: datetime = BASE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    ts = when.timestamp()
    os.utime(path, (ts, ts))
    return path


def _out(capsys) -> list:
    return capsys.readouterr().out.splitlines()


def test_full_hit_single_match(home, capsys):
    _write(_session(home, "a"), '{"role":"user","text":"alpha and beta"}')
    assert main(["--search", "alpha beta", "--harness", "omp"]) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 1"
    assert lines[1] == "# ambiguous: no"
    assert len(lines) == 3
    assert len(lines[2].split("\t")) == 5


def test_ranks_by_weakest_term_over_total(home, capsys):
    dense = _write(_session(home, "dense"), "alpha " * 5 + "beta " * 5, BASE)
    noisy = _write(_session(home, "noisy"), "alpha " + "beta " * 100, BASE - timedelta(hours=1))
    assert main(["--search", "alpha beta", "--harness", "omp"]) == 0
    lines = _out(capsys)
    assert str(dense) in lines[2]
    assert str(noisy) in lines[3]


def test_ranks_by_weakest_term_with_newer_mtime(home, capsys):
    dense = _write(_session(home, "dense"), "alpha " * 5 + "beta " * 5, BASE - timedelta(hours=5))
    noisy = _write(_session(home, "noisy"), "alpha " + "beta " * 100, BASE)
    assert main(["--search", "alpha beta", "--harness", "omp"]) == 0
    assert str(dense) in _out(capsys)[2]


def test_partial_hit_is_ambiguous(home, capsys):
    _write(_session(home, "a"), "alpha only", BASE)
    _write(_session(home, "b"), "beta only", BASE - timedelta(hours=1))
    assert main(["--search", "alpha beta", "--harness", "omp"]) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 2"
    assert lines[1] == "# ambiguous: yes"
    assert all("terms=1/2" in line for line in lines[2:])


def test_ambiguity_threshold_on_score(home, capsys):
    _write(_session(home, "top"), "alpha " * 10, BASE)
    _write(_session(home, "second"), "alpha " * 4, BASE - timedelta(hours=1))
    assert main(["--search", "alpha", "--harness", "omp"]) == 0
    assert _out(capsys)[1] == "# ambiguous: no"

    _write(_session(home, "top"), "alpha " * 5, BASE)
    assert main(["--search", "alpha", "--harness", "omp"]) == 0
    assert _out(capsys)[1] == "# ambiguous: yes"


def test_search_requires_harness(home):
    with pytest.raises(SystemExit) as exc:
        main(["--search", "alpha"])
    assert exc.value.code == 2


def test_search_rejects_conflicting_args(home):
    for argv in (
        ["--search", "alpha", "--harness", "omp", "--list"],
        ["--search", "alpha", "--harness", "omp", "--format", "yaml"],
        ["--search", "alpha", "--harness", "omp", "x.jsonl"],
    ):
        with pytest.raises(SystemExit) as exc:
            main(argv)
        assert exc.value.code == 2


def test_search_rejects_kilo_code(home):
    with pytest.raises(SystemExit) as exc:
        main(["--search", "alpha", "--harness", "kilo-code"])
    assert exc.value.code == 2


def test_search_rejects_blank_query(home):
    with pytest.raises(SystemExit) as exc:
        main(["--search", "   ", "--harness", "omp"])
    assert exc.value.code == 2


def test_limit_truncates_rows_not_count(home, capsys):
    for index in range(3):
        _write(_session(home, f"f{index}"), "alpha beta", BASE - timedelta(hours=index))
    assert main(["--search", "alpha beta", "--harness", "omp", "--limit", "1"]) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 3"
    assert len(lines) == 3


def test_match_and_since_filter_candidates(home, capsys):
    wanted = _write(
        _session(home, "wanted", "Workspace-Code-RiskFlow"), "alpha", datetime(2026, 10, 21)
    )
    old = _write(_session(home, "old", "Workspace-Code-RiskFlow"), "alpha", datetime(2026, 10, 1))
    other = _write(_session(home, "other", "Elsewhere"), "alpha", datetime(2026, 10, 21))

    assert main(["--search", "alpha", "--harness", "omp", "--match", "RISKFLOW"]) == 0
    lines = _out(capsys)
    assert str(wanted) in lines[2] and str(old) in lines[3] and str(other) not in "\n".join(lines)

    assert main(
        ["--search", "alpha", "--harness", "omp", "--match", "RISKFLOW", "--since", "2026-10-10"]
    ) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 1"
    assert str(wanted) in lines[2]


def test_query_is_case_insensitive_and_deduplicated(home, capsys):
    _write(_session(home, "a"), "alpha", BASE)
    assert main(["--search", "Alpha   ALPHA", "--harness", "omp"]) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 1"
    assert "terms=1/1" in lines[2]


def test_zero_matches(home, capsys):
    _write(_session(home, "a"), "alpha", BASE)
    assert main(["--search", "zzz-not-here-zzz", "--harness", "omp"]) == 0
    lines = _out(capsys)
    assert lines == ["# matches: 0", "# ambiguous: no"]


def test_search_reads_zstd_candidates(home, capsys):
    zstandard = pytest.importorskip("zstandard")
    path = home / ".dsh/sessions/-proj-/session-abc/session.jsonl.zstd"
    path.parent.mkdir(parents=True, exist_ok=True)
    with zstandard.open(path, "wb") as handle:
        handle.write(b'{"text":"alpha beta"}')
    assert main(["--search", "alpha beta", "--harness", "deepseek-harness"]) == 0
    lines = _out(capsys)
    assert lines[0] == "# matches: 1"
    assert str(path) in lines[2]


def test_tokenize():
    assert tokenize("  Embedding   CACHE cache ") == ["embedding", "cache"]
    assert tokenize("   ") == []


def test_count_terms_counts_every_occurrence(home):
    path = _write(home / "x.jsonl", "Alpha alpha ALPHA beta")
    assert count_terms(path, [b"alpha", b"beta", b"gamma"]) == [3, 1, 0]


def test_search_order_and_ambiguity_units(home):
    dense = _write(_session(home, "dense"), "alpha beta", BASE)
    sparse = _write(_session(home, "sparse"), "alpha", BASE)
    results = search("omp", [b"alpha", b"beta"])
    assert [m.candidate.path for m in results] == [dense]
    results = search("omp", [b"alpha"])
    assert [m.candidate.path for m in results] == [dense, sparse]

    def match(path: str, score: int, distinct: int = 1) -> Match:
        return Match(
            candidate=Candidate(harness="omp", path=Path(path), mtime=BASE),
            counts=(score,),
            distinct=distinct,
            score=score,
        )

    assert is_ambiguous([], 1) is False
    assert is_ambiguous([match("/a", 10), match("/b", 4)], 1) is False
    assert is_ambiguous([match("/a", 5), match("/b", 4)], 1) is True
    assert is_ambiguous([match("/a", 99, distinct=1)], 2) is True
    assert render_matches([match("/a", 3)], 1, 10).startswith("# matches: 1\n# ambiguous: no\n")
