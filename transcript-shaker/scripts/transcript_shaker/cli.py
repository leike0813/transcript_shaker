"""命令行入口：transcript_shaker <transcript> [--max-chars N] [--out PATH]。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .adapters import UnsupportedTranscript, detect_adapter, supported_harnesses
from .render import DEFAULT_MAX_CHARS, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcript_shaker",
        description="把 Agent Harness 的本地 transcript 裁剪转写为 Markdown 日志。",
    )
    parser.add_argument("transcript", help="transcript 文件路径（如 Codex rollout JSONL / .jsonl.zst）")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"工具结果与 system 消息的截断上限（默认 {DEFAULT_MAX_CHARS}）",
    )
    parser.add_argument("--out", help="输出文件路径；缺省写到 stdout")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
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

    document = render_markdown(session, events, max_chars=args.max_chars)
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
