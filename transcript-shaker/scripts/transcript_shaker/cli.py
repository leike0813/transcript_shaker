"""命令行入口：转写单个 transcript，或用 --list 列出本机候选。"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

from .adapters import UnsupportedTranscript, detect_adapter, supported_harnesses
from .locate import HARNESS_SOURCES, find_candidates, render_candidates
from .render import DEFAULT_MAX_CHARS, render_markdown


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        number = 0
    if number <= 0:
        raise argparse.ArgumentTypeError("expected positive integer")
    return number


def _date_arg(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcript_shaker",
        description="把 Agent Harness 的本地 transcript 裁剪转写为 Markdown 日志，或列出本机候选 transcript。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  transcript_shaker --list\n"
            "  transcript_shaker --list --harness codex --limit 5 --since 2026-10-20\n"
            "  transcript_shaker ~/.omp/agent/sessions/-proj/2026-10-21T09-00-00-000Z_<id>.jsonl --out session.md"
        ),
    )
    parser.add_argument(
        "transcript",
        nargs="?",
        help="transcript 文件路径（如 Codex rollout JSONL / .jsonl.zst）",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出本机候选 transcript（只看路径与修改时间，不解析内容）",
    )
    parser.add_argument(
        "--harness",
        choices=sorted(HARNESS_SOURCES),
        help="配合 --list：只列出某个 harness 的候选",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=None,
        help="配合 --list：最多输出多少条（默认 20）",
    )
    parser.add_argument(
        "--since",
        type=_date_arg,
        metavar="YYYY-MM-DD",
        help="配合 --list：只看修改时间不早于该本地日期的候选",
    )
    parser.add_argument(
        "--max-chars",
        type=_positive_int,
        default=None,
        help=f"工具结果与 system 消息的截断上限（默认 {DEFAULT_MAX_CHARS}）",
    )
    parser.add_argument("--out", help="输出文件路径；缺省写到 stdout")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        if args.transcript is not None or args.max_chars is not None or args.out:
            parser.error("--list 不能与 transcript / --max-chars / --out 同用")
        limit = args.limit if args.limit is not None else 20
        candidates = find_candidates(
            harnesses=[args.harness] if args.harness else None,
            since=args.since,
        )
        sys.stdout.write(render_candidates(candidates[:limit]))
        return 0
    if args.transcript is None:
        parser.error("缺少 transcript 参数（或使用 --list 列出候选）")
    if args.harness or args.since or args.limit is not None:
        parser.error("--harness / --since / --limit 仅用于 --list")
    max_chars = args.max_chars if args.max_chars is not None else DEFAULT_MAX_CHARS

    path = Path(args.transcript).expanduser()
    if not path.exists():
        print(f"transcript_shaker: file not found: {path}", file=sys.stderr)
        return 1
    if not path.is_file():
        print(f"transcript_shaker: not a file: {path}", file=sys.stderr)
        return 1

    try:
        adapter = detect_adapter(path)
    except UnsupportedTranscript:
        print(
            f"transcript_shaker: unsupported transcript format: {path}（已支持：{supported_harnesses()}）",
            file=sys.stderr,
        )
        return 1
    except (OSError, RuntimeError) as exc:
        print(f"transcript_shaker: {exc}", file=sys.stderr)
        return 1

    try:
        session, events = adapter.parse(path)
    except (OSError, RuntimeError) as exc:
        print(f"transcript_shaker: {exc}", file=sys.stderr)
        return 1

    document = render_markdown(session, events, max_chars=max_chars)
    # 某些 transcript 的 JSON 里带孤立代理项（\ud83e 之类），直接写会抛 UnicodeEncodeError。
    document = document.encode("utf-8", "replace").decode("utf-8")
    if args.out:
        out_path = Path(args.out).expanduser()
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(document, encoding="utf-8")
        except OSError as exc:
            print(f"transcript_shaker: cannot write output: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(document)
    return 0
