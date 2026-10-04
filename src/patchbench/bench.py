"""Run every fixture submission and check each verdict against the expected one."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from patchbench.executors.base import Executor
from patchbench.loader import load_submissions, load_tasks
from patchbench.models import EvalResult, Verdict
from patchbench.runner import evaluate


class BenchRow(BaseModel):
    """One submission's expected and actual verdict."""

    instance_id: str
    label: str
    expected: Verdict
    actual: Verdict
    match: bool
    f2p: str
    p2p: str
    duration_s: float


class BenchReport(BaseModel):
    """Summary of a benchmark run."""

    executor: str
    tasks: int
    submissions: int
    matched: int
    gold_resolved: int
    gold_total: int
    base_unresolved: int
    base_total: int
    verdicts: dict[str, int]
    total_seconds: float
    rows: list[BenchRow]

    @property
    def ok(self) -> bool:
        return self.matched == self.submissions


def run_bench(root: Path, executor: Executor, timeout: int = 10) -> BenchReport:
    """Evaluate all submissions for all tasks under ``root``."""
    rows: list[BenchRow] = []
    results: list[EvalResult] = []
    tasks = load_tasks(root)
    for task in tasks:
        for submission, expected in load_submissions(root, task.instance_id):
            result = evaluate(task, submission, executor, timeout)
            results.append(result)
            rows.append(
                BenchRow(
                    instance_id=task.instance_id,
                    label=submission.label,
                    expected=expected,
                    actual=result.verdict,
                    match=result.verdict == expected,
                    f2p=f"{result.f2p_passed}/{result.f2p_total}",
                    p2p=f"{result.p2p_passed}/{result.p2p_total}",
                    duration_s=result.duration_s,
                )
            )
    gold = [r for r in rows if r.label == "gold"]
    base = [r for r in rows if r.label == "empty"]
    return BenchReport(
        executor=executor.name,
        tasks=len(tasks),
        submissions=len(rows),
        matched=sum(r.match for r in rows),
        gold_resolved=sum(r.actual == Verdict.RESOLVED for r in gold),
        gold_total=len(gold),
        base_unresolved=sum(r.actual == Verdict.UNRESOLVED for r in base),
        base_total=len(base),
        verdicts=dict(Counter(r.actual.value for r in rows)),
        total_seconds=round(sum(r.duration_s for r in results), 2),
        rows=rows,
    )


def render_markdown(report: BenchReport) -> str:
    """Render a report as a Markdown table."""
    lines = [
        f"# PatchBench fixture benchmark ({report.executor} executor)",
        "",
        f"- Tasks: {report.tasks}; submissions: {report.submissions}",
        f"- Verdicts matching expectation: {report.matched}/{report.submissions}",
        f"- Gold patches resolved: {report.gold_resolved}/{report.gold_total}",
        f"- Empty patches unresolved (base fails): {report.base_unresolved}/{report.base_total}",
        f"- Verdict counts: {json.dumps(report.verdicts, sort_keys=True)}",
        f"- Total evaluation time: {report.total_seconds}s",
        "",
        "| Task | Submission | Expected | Actual | F2P | P2P | Seconds |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report.rows:
        mark = "" if r.match else " **MISMATCH**"
        lines.append(
            f"| {r.instance_id} | {r.label} | {r.expected.value} | {r.actual.value}{mark} "
            f"| {r.f2p} | {r.p2p} | {r.duration_s} |"
        )
    return "\n".join(lines) + "\n"
