"""事件流 → 固定 Markdown 日志。裁剪策略集中在这里。"""

from __future__ import annotations

import re
from collections import Counter
from typing import List

from .model import Event, Session

DEFAULT_MAX_CHARS = 2000

# 这些工具承载的是命令原文，命令不截断（只截结果）。
# 取值来自各 harness 实测的 shell 工具名（codex/claude/command-code/qwen/kimi/grok/dsh/pi/omp/codebuddy/cline）。
SHELL_TOOLS = {
    "exec_command",
    "shell",
    "bash",
    "Bash",
    "shell_command",
    "run_shell_command",
    "run_commands",
    "run_terminal_command",
    "terminal",
    "sh",
}

KIND_ORDER = ("user", "assistant", "system", "tool")


def truncate(text: str, limit: int) -> str:
    """超限时截断并标注被省略的字符数。"""
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + f"\n[... truncated {len(text) - limit} chars ...]"


def _fence(text: str, lang: str) -> str:
    """围栏长度自适应：内容里最长的连续反引号 +1，至少 3。"""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{lang}\n{text}\n{fence}"


def _kind_label(event: Event) -> str:
    return "tool" if event.kind == "tool" else (event.role or "message")


def _heading(index: int, event: Event) -> str:
    parts = [str(index), _kind_label(event)]
    if event.kind == "tool" and event.tool:
        parts.append(event.tool)
    if event.ts:
        parts.append(event.ts)
    return "## " + " · ".join(parts)


def _block(index: int, event: Event, max_chars: int) -> str:
    lines: List[str] = [_heading(index, event), ""]
    if event.kind == "tool":
        if event.status:
            lines += [f"- status: {event.status}", ""]
        if event.call:
            if event.tool in SHELL_TOOLS:
                lines += [_fence(event.call, "bash"), ""]
            else:
                lines += [_fence(truncate(event.call, max_chars), "text"), ""]
        if event.result:
            lines += [_fence(truncate(event.result, max_chars), "text"), ""]
    else:
        text = truncate(event.text, max_chars) if event.role == "system" else event.text
        lines += [text, ""]
    return "\n".join(lines).rstrip("\n")


def render_markdown(session: Session, events: List[Event], max_chars: int = DEFAULT_MAX_CHARS) -> str:
    counts = Counter(_kind_label(event) for event in events)
    summary = ", ".join(f"{kind} {counts[kind]}" for kind in KIND_ORDER if counts[kind])
    events_line = f"- events: {len(events)}" + (f" ({summary})" if summary else "")

    title = f"# Transcript · {session.harness}"
    if session.started:
        title += f" · {session.started}"

    meta = [f"- harness: {session.harness}"]
    if session.session_id:
        meta.append(f"- session: {session.session_id}")
    meta.append(f"- source: {session.source}")
    if session.cwd:
        meta.append(f"- cwd: {session.cwd}")
    origin = " ".join(part for part in (session.originator, session.version) if part)
    if origin:
        meta.append(f"- origin: {origin}")
    if session.history:
        meta.append(f"- history: {session.history}")
    meta.append(events_line)

    blocks = ["\n".join([title, "", *meta, "", "---"])]
    for index, event in enumerate(events, start=1):
        blocks.append(_block(index, event, max_chars))
    return "\n\n".join(blocks) + "\n"
