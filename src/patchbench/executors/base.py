"""Executor interface: run the eval script in some environment and return its log."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

MAX_LOG_BYTES = 200_000


@dataclass
class ExecOutput:
    """Raw outcome of running the eval script."""

    log: str
    timed_out: bool
    exit_code: int | None
    duration_s: float


class Executor(Protocol):
    """Runs ``<work>/eval.sh`` against ``<work>/repo`` and ``<work>/patches``."""

    name: str

    def run(self, work: Path, timeout: int) -> ExecOutput:  # pragma: no cover - protocol
        ...


def truncate_log(text: str) -> str:
    """Keep logs bounded; a hostile patch can print without limit."""
    data = text.encode("utf-8", "replace")
    if len(data) <= MAX_LOG_BYTES:
        return text
    head = data[: MAX_LOG_BYTES // 2].decode("utf-8", "replace")
    tail = data[-MAX_LOG_BYTES // 2 :].decode("utf-8", "replace")
    return f"{head}\n... [log truncated] ...\n{tail}"
