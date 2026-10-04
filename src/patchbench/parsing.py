"""Parse an eval-script log into per-test statuses.

pytest's ``-rA`` short summary lists every test as ``STATUS test_id``. Only the last summary
block is read. Note the limits: a submission runs inside the test process, so a hostile patch
can print text that looks like a summary; sandboxing contains it, grading cannot fully detect it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from patchbench.script import (
    PATCH_APPLIED,
    PATCH_APPLY_FAILED,
    PATCH_EMPTY,
    TEST_PATCH_APPLIED,
    TEST_PATCH_FAILED,
    TESTS_END,
    TESTS_START,
)

_SUMMARY_HEADER = re.compile(r"^=+ short test summary info =+$")
_RESULT = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(\S+)")
_EXIT = re.compile(rf"^{re.escape(TESTS_END)} exit=(\d+)")


@dataclass
class ParsedLog:
    """What the eval script reported."""

    patch_applied: bool = False
    patch_empty: bool = False
    patch_apply_failed: bool = False
    test_patch_applied: bool = False
    test_patch_failed: bool = False
    tests_started: bool = False
    exit_code: int | None = None
    statuses: dict[str, str] = field(default_factory=dict)


def parse_log(log: str) -> ParsedLog:
    """Extract sentinel state and the last pytest summary from ``log``."""
    parsed = ParsedLog()
    summary: dict[str, str] = {}
    in_summary = False
    in_tests = False
    for raw in log.splitlines():
        line = raw.rstrip()
        if line == PATCH_APPLIED:
            parsed.patch_applied = True
        elif line == PATCH_EMPTY:
            parsed.patch_empty = True
        elif line == PATCH_APPLY_FAILED:
            parsed.patch_apply_failed = True
        elif line == TEST_PATCH_APPLIED:
            parsed.test_patch_applied = True
        elif line == TEST_PATCH_FAILED:
            parsed.test_patch_failed = True
        elif line == TESTS_START:
            parsed.tests_started = True
            in_tests = True
        elif in_tests and (match := _EXIT.match(line)):
            parsed.exit_code = int(match.group(1))
            in_tests = False
            in_summary = False
        elif in_tests and _SUMMARY_HEADER.match(line):
            in_summary = True
            summary = {}
        elif in_tests and in_summary and (result := _RESULT.match(line)):
            summary[result.group(2)] = result.group(1)
    parsed.statuses = summary
    return parsed
