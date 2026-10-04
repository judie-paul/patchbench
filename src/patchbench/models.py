"""Canonical records for tasks, submissions and evaluation results."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_TEST_COMMAND = "python -m pytest -rA -p no:cacheprovider --no-header -q"


class Verdict(StrEnum):
    """Outcome of evaluating one patch, following SWE-bench's resolution statuses."""

    RESOLVED = "resolved"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"
    APPLY_FAILED = "apply_failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class Task(BaseModel):
    """A SWE-bench-shaped task: a repository state, an issue and the tests defining the fix."""

    model_config = ConfigDict(populate_by_name=True)

    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: str = ""
    test_patch: str
    fail_to_pass: list[str] = Field(default_factory=list, alias="FAIL_TO_PASS")
    pass_to_pass: list[str] = Field(default_factory=list, alias="PASS_TO_PASS")
    test_command: str = DEFAULT_TEST_COMMAND
    hints_text: str = ""
    created_at: str = ""
    version: str = ""
    # Directory holding the repository at base_commit (fixtures); never serialized.
    snapshot_path: Path | None = Field(default=None, exclude=True)

    @field_validator("fail_to_pass", "pass_to_pass", mode="before")
    @classmethod
    def _parse_json_list(cls, value: Any) -> Any:
        """SWE-bench stores these lists as JSON strings."""
        if isinstance(value, str):
            return json.loads(value) if value.strip() else []
        return value


class Submission(BaseModel):
    """A candidate patch (a unified diff) for one task."""

    instance_id: str
    patch: str
    label: str = ""


class EvalResult(BaseModel):
    """The graded outcome of running one submission."""

    instance_id: str
    label: str = ""
    verdict: Verdict
    executor: str
    patch_applied: bool
    f2p_passed: int
    f2p_total: int
    p2p_passed: int
    p2p_total: int
    failed_f2p: list[str] = Field(default_factory=list)
    failed_p2p: list[str] = Field(default_factory=list)
    tests: dict[str, str] = Field(default_factory=dict)
    duration_s: float
    timed_out: bool = False
    log: str = ""
    detail: str = ""
