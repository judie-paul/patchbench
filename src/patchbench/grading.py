"""SWE-bench-style grading: a pure function of the parsed log."""

from __future__ import annotations

from patchbench.models import Task, Verdict
from patchbench.parsing import ParsedLog


def count_passed(ids: list[str], statuses: dict[str, str]) -> tuple[int, list[str]]:
    """Return how many of ``ids`` passed and the ids that did not (missing counts as failed)."""
    failed = [test for test in ids if statuses.get(test) != "PASSED"]
    return len(ids) - len(failed), failed


def decide(task: Task, parsed: ParsedLog, timed_out: bool) -> tuple[Verdict, str]:
    """Classify one run.

    Resolved: every FAIL_TO_PASS and PASS_TO_PASS test passes. Partial: some but not all
    FAIL_TO_PASS tests pass and no PASS_TO_PASS test broke. Everything else that ran is
    unresolved. Timeouts, apply failures and harness problems are distinct outcomes.
    """
    if timed_out:
        return Verdict.TIMEOUT, "run exceeded the time limit and was killed"
    if parsed.patch_apply_failed:
        return Verdict.APPLY_FAILED, "git apply rejected the submitted patch"
    if parsed.test_patch_failed:
        return Verdict.ERROR, "the test patch did not apply (submission may edit the tests)"
    if not parsed.tests_started:
        return Verdict.ERROR, "the eval script never reached the test run"
    if not task.fail_to_pass:
        return Verdict.ERROR, "task defines no FAIL_TO_PASS tests"
    f2p, _ = count_passed(task.fail_to_pass, parsed.statuses)
    p2p, _ = count_passed(task.pass_to_pass, parsed.statuses)
    f2p_all = f2p == len(task.fail_to_pass)
    p2p_all = p2p == len(task.pass_to_pass)
    if f2p_all and p2p_all:
        return Verdict.RESOLVED, ""
    if 0 < f2p < len(task.fail_to_pass) and p2p_all:
        return Verdict.PARTIAL, "only some FAIL_TO_PASS tests pass"
    if f2p_all:
        return Verdict.UNRESOLVED, "fixes the issue but breaks PASS_TO_PASS tests"
    return Verdict.UNRESOLVED, "FAIL_TO_PASS tests still fail"
