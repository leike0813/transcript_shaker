"""Codex rollout（JSONL）解析器。

一份 rollout 里同一内容可能在两条流里各出现一次：
`event_msg/item_completed`（富结构，TUI 视角）与 `response_item`（模型原始格式）。
两者只取其一：item 流含工具类条目时用 item 流，否则（旧版本）用 response_item。
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ..model import Event, Session
from .base import Adapter

# item 流里出现这些类型，说明该文件的工具调用记录在 item 流中。
TOOL_ITEM_TYPES = {
    "CommandExecution",
    "McpToolCall",
    "FileChange",
    "WebSearch",
    "CollabAgentToolCall",
    "ImageView",
    "SubAgentActivity",
    "Extension",
}

KNOWN_RECORD_TYPES = {
    "session_meta",
    "response_item",
    "event_msg",
    "turn_context",
    "token_usage_record",
    "world_state",
    "compacted",
}

DETECT_LINE_LIMIT = 200

_ROLE_MAP = {
    "user": "user",
    "assistant": "assistant",
    "developer": "system",
    "system": "system",
}


def _text_parts(content: Any, types: Tuple[str, ...]) -> str:
    """从 content 块列表里取出指定 type 的 text，按顺序用换行连接。"""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: List[str] = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") not in types:
            continue
        text = block.get("text")
        if isinstance(text, str) and text:
            parts.append(text)
    return "\n".join(parts)


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False)


def _output_text(output: Any) -> str:
    """工具输出：字符串原样，content 块列表取 text，其它按 JSON 文本。"""
    if isinstance(output, list):
        return _text_parts(output, ("text", "input_text", "output_text"))
    return _as_text(output)


def _join_argv(command: Any) -> str:
    if isinstance(command, str):
        return command
    if isinstance(command, list):
        return " ".join(shlex.quote(str(part)) for part in command)
    return ""


def _mcp_name(name: str) -> str:
    """`mcp__server__tool` → `mcp:server.tool`，其它名字原样返回。"""
    if not name.startswith("mcp__"):
        return name
    parts = name[len("mcp__"):].split("__")
    if len(parts) >= 2:
        return f"mcp:{parts[0]}.{parts[1]}"
    return f"mcp:{parts[0]}"


def _message(role: str, text: str, ts: str) -> Optional[Event]:
    if not text.strip():
        return None
    return Event(kind="message", role=role, text=text, ts=ts)


def _tool(tool: str, call: str, result: str, status: str, ts: str) -> Optional[Event]:
    if not call and not result and not status:
        return None
    return Event(kind="tool", tool=tool, call=call, result=result, status=status, ts=ts)


def _join_name(prefix: str, *parts: Any) -> str:
    tail = ".".join(str(part) for part in parts if part)
    return f"{prefix}{tail}" if tail else prefix.rstrip(":")


def _decompress_lines(path: Path) -> Iterator[str]:
    try:
        from compression import zstd as zstd_module  # Python 3.14+
    except ImportError:
        zstd_module = None
    if zstd_module is not None:
        with zstd_module.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            yield from handle
        return

    try:
        import zstandard as zstandard_module
    except ImportError:
        zstandard_module = None
    if zstandard_module is not None:
        with zstandard_module.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            yield from handle
        return

    zstd_bin = shutil.which("zstd")
    if zstd_bin is None:
        raise RuntimeError(
            f"cannot decompress {path}：需要 Python 3.14 compression.zstd、zstandard 包或 zstd 命令行"
        )
    proc = subprocess.run([zstd_bin, "-dc", str(path)], capture_output=True)
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"cannot decompress {path}：zstd 命令失败（{detail}）")
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        yield line


def _iter_lines(path: Path) -> Iterator[str]:
    if path.name.endswith(".zst"):
        yield from _decompress_lines(path)
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        yield from handle


def _iter_records(path: Path) -> Iterator[Dict[str, Any]]:
    """逐行解析；不可解析的行与空行直接跳过。"""
    for line in _iter_lines(path):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _payload(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}


class CodexAdapter(Adapter):
    name = "codex"

    def detect(self, path: Path) -> bool:
        if not path.is_file():
            return False
        try:
            for index, record in enumerate(_iter_records(path)):
                if index >= DETECT_LINE_LIMIT:
                    break
                if record.get("type") in KNOWN_RECORD_TYPES and isinstance(record.get("payload"), dict):
                    return True
        except OSError:
            return False
        return False

    def parse(self, path: Path) -> Tuple[Session, List[Event]]:
        meta: Dict[str, Any] = {}
        history = "legacy"
        for record in _iter_records(path):
            rtype = record.get("type")
            if rtype == "session_meta" and not meta:
                meta = _payload(record)
            elif rtype == "event_msg":
                payload = _payload(record)
                if payload.get("type") != "item_completed":
                    continue
                item = payload.get("item")
                if isinstance(item, dict) and item.get("type") in TOOL_ITEM_TYPES:
                    history = "paginated"
                    break

        session = Session(
            harness=self.name,
            source=str(path),
            session_id=str(meta.get("id") or meta.get("session_id") or ""),
            cwd=str(meta.get("cwd") or ""),
            started=str(meta.get("timestamp") or ""),
            version=str(meta.get("cli_version") or ""),
            originator=str(meta.get("originator") or ""),
            history=history,
        )
        events = self._parse_paginated(path) if history == "paginated" else self._parse_legacy(path)
        return session, events

    def _parse_paginated(self, path: Path) -> List[Event]:
        events: List[Event] = []
        for record in _iter_records(path):
            ts = str(record.get("timestamp") or "")
            rtype = record.get("type")
            payload = _payload(record)
            if rtype == "event_msg" and payload.get("type") == "item_completed":
                item = payload.get("item")
                if isinstance(item, dict):
                    event = _item_event(item, ts)
                    if event is not None:
                        events.append(event)
            elif rtype == "response_item" and payload.get("type") == "message":
                # item 流已覆盖 user/assistant，这里只补 system/developer。
                if payload.get("role") in ("developer", "system"):
                    text = _text_parts(payload.get("content"), ("input_text", "output_text", "text"))
                    event = _message("system", text, ts)
                    if event is not None:
                        events.append(event)
        return events

    def _parse_legacy(self, path: Path) -> List[Event]:
        events: List[Event] = []
        pending: Dict[str, Event] = {}
        for record in _iter_records(path):
            ts = str(record.get("timestamp") or "")
            rtype = record.get("type")
            payload = _payload(record)

            if rtype == "compacted":
                events.append(Event(kind="message", role="system", text="context compacted", ts=ts))
                continue
            if rtype == "event_msg":
                ptype = payload.get("type")
                if ptype == "agent_message":
                    event = _message("assistant", _as_text(payload.get("message") or payload.get("text")), ts)
                elif ptype == "user_message":
                    event = _message("user", _as_text(payload.get("message") or payload.get("text")), ts)
                else:
                    event = None
                if event is not None:
                    events.append(event)
                continue
            if rtype != "response_item":
                continue

            ptype = payload.get("type")
            call_id = payload.get("call_id")
            if ptype == "message":
                role = _ROLE_MAP.get(str(payload.get("role") or ""), "")
                if not role:
                    continue
                event = _message(role, _text_parts(payload.get("content"), ("input_text", "output_text", "text")), ts)
                if event is not None:
                    events.append(event)
            elif ptype == "function_call":
                event = _tool(
                    _mcp_name(str(payload.get("name") or "function")),
                    _as_text(payload.get("arguments")),
                    "",
                    "",
                    ts,
                )
                if event is not None:
                    events.append(event)
                    if call_id:
                        pending[str(call_id)] = event
            elif ptype == "function_call_output":
                _fill_result(pending, call_id, _output_text(payload.get("output")))
            elif ptype == "custom_tool_call":
                event = _tool(str(payload.get("name") or "custom_tool"), _as_text(payload.get("input")), "", "", ts)
                if event is not None:
                    events.append(event)
                    if call_id:
                        pending[str(call_id)] = event
            elif ptype == "custom_tool_call_output":
                _fill_result(pending, call_id, _output_text(payload.get("output")))
            elif ptype == "local_shell_call":
                action = payload.get("action")
                command = action.get("command") if isinstance(action, dict) else None
                event = _tool("shell", _join_argv(command), "", "", ts)
                if event is not None:
                    events.append(event)
                    if call_id:
                        pending[str(call_id)] = event
            elif ptype == "local_shell_call_output":
                _fill_result(pending, call_id, _output_text(payload.get("output")))
            elif ptype == "web_search_call":
                action = payload.get("action")
                query = payload.get("query")
                if not query and isinstance(action, dict):
                    query = action.get("query")
                event = _tool("web_search", _as_text(query), "", "", ts)
                if event is not None:
                    events.append(event)
        return events


def _fill_result(pending: Dict[str, Event], call_id: Any, text: str) -> None:
    if not call_id or not text:
        return
    event = pending.get(str(call_id))
    if event is not None:
        event.result = text


def _item_event(item: Dict[str, Any], ts: str) -> Optional[Event]:
    itype = item.get("type")
    if itype == "UserMessage":
        return _message("user", _text_parts(item.get("content"), ("text",)), ts)
    if itype == "AgentMessage":
        return _message("assistant", _text_parts(item.get("content"), ("Text", "text")), ts)
    if itype == "Plan":
        return _message("assistant", _as_text(item.get("text")), ts)
    if itype == "ContextCompaction":
        return _message("system", "context compacted", ts)
    if itype == "CommandExecution":
        event = _tool(
            "exec_command",
            _join_argv(item.get("command")),
            _as_text(item.get("aggregated_output")),
            str(item.get("status") or ""),
            ts,
        )
        return event
    if itype == "McpToolCall":
        result = item.get("result")
        content = result.get("content") if isinstance(result, dict) else None
        return _tool(
            _join_name("mcp:", item.get("server"), item.get("tool")),
            _as_text(item.get("arguments")),
            _text_parts(content, ("text",)),
            str(item.get("status") or ""),
            ts,
        )
    if itype == "FileChange":
        paths: List[str] = []
        diffs: List[str] = []
        changes = item.get("changes")
        if isinstance(changes, dict):
            for path, change in changes.items():
                if isinstance(change, dict):
                    ctype = str(change.get("type") or "")
                    paths.append(f"{path} ({ctype})" if ctype else str(path))
                    diff = change.get("unified_diff")
                    if diff:
                        diffs.append(str(diff))
                else:
                    paths.append(str(path))
        return _tool("file_change", "; ".join(paths), "\n".join(diffs), "", ts)
    if itype == "WebSearch":
        action = item.get("action")
        query = item.get("query")
        if not query and isinstance(action, dict):
            query = action.get("query")
        return _tool("web_search", _as_text(query), "", "", ts)
    if itype == "CollabAgentToolCall":
        return _tool(
            _join_name("collab:", item.get("tool")),
            _as_text(item.get("prompt")),
            "",
            str(item.get("status") or ""),
            ts,
        )
    if itype == "ImageView":
        return _tool("image_view", _as_text(item.get("path")), "", "", ts)
    if itype == "SubAgentActivity":
        call = _as_text(item.get("agent_path") or item.get("agent_thread_id"))
        if item.get("model"):
            call = f"{call} (model={item['model']})"
        return _tool(_join_name("subagent:", item.get("kind")), call, "", "", ts)
    return None
