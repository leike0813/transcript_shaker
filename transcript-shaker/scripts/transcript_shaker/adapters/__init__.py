"""adapter 注册表：按注册顺序做内容级识别。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..model import Event, Session
from .base import Adapter
from .codex import CodexAdapter


class UnsupportedTranscript(Exception):
    """文件内容不属于任何已注册 harness。"""


ADAPTERS: List[Adapter] = [CodexAdapter()]


def detect_adapter(path: Path) -> Adapter:
    for adapter in ADAPTERS:
        if adapter.detect(path):
            return adapter
    raise UnsupportedTranscript(f"unsupported transcript format: {path}")


def supported_harnesses() -> str:
    return "、".join(adapter.name for adapter in ADAPTERS)
