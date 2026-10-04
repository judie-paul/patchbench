"""The fixture gate: every task is solvable, its base fails, bad submissions are caught."""

import pytest

from patchbench.bench import render_markdown, run_bench
from patchbench.executors.local import LocalExecutor
from patchbench.loader import get_task, load_submissions, load_tasks
from patchbench.models import Submission, Verdict
from patchbench.runner import evaluate, materialize_repo


def test_fixture_tasks_are_well_formed(fixtures_dir):
    tasks = load_tasks(fixtures_dir)
    assert len(tasks) >= 6
    for task in tasks:
        assert task.fail_to_pass and task.pass_to_pass
        assert task.patch and task.test_patch
        assert not set(task.fail_to_pass) & set(task.pass_to_pass)


def test_gold_resolves_and_base_fails_for_every_task(fixtures_dir):
    executor = LocalExecutor()
    for task in load_tasks(fixtures_dir):
        gold = evaluate(task, Submission(instance_id=task.instance_id, patch=task.patch), executor)
        assert gold.verdict == Verdict.RESOLVED, task.instance_id
        assert gold.f2p_passed == gold.f2p_total and gold.p2p_passed == gold.p2p_total
        base = evaluate(task, Submission(instance_id=task.instance_id, patch=""), executor)
        assert base.verdict == Verdict.UNRESOLVED, task.instance_id
        assert base.failed_f2p == task.fail_to_pass and not base.failed_p2p


def test_regression_and_partial_submissions(fixtures_dir):
    executor = LocalExecutor()
    csv = get_task(fixtures_dir, "patchbench__csvrow-1")
    by_label = {s.label: s for s, _ in load_submissions(fixtures_dir, csv.instance_id)}
    partial = evaluate(csv, by_label["partial"], executor)
    assert partial.verdict == Verdict.PARTIAL and partial.f2p_passed == 1
    regression = evaluate(csv, by_label["regression"], executor)
    assert regression.verdict == Verdict.UNRESOLVED
    assert regression.failed_p2p and not regression.failed_f2p


def test_traversal_patch_is_rejected_and_writes_nothing(fixtures_dir, tmp_path):
    executor = LocalExecutor()
    task = get_task(fixtures_dir, "patchbench__slugify-1")
    by_label = {s.label: s for s, _ in load_submissions(fixtures_dir, task.instance_id)}
    result = evaluate(task, by_label["traversal"], executor)
    assert result.verdict == Verdict.APPLY_FAILED and not result.patch_applied


def test_hang_is_killed_at_the_timeout(fixtures_dir):
    task = get_task(fixtures_dir, "patchbench__slugify-1")
    by_label = {s.label: s for s, _ in load_submissions(fixtures_dir, task.instance_id)}
    result = evaluate(task, by_label["hang"], LocalExecutor(), timeout=3)
    assert result.verdict == Verdict.TIMEOUT and result.timed_out
    assert 3 <= result.duration_s < 10


def test_materialize_requires_a_snapshot(slug_task, tmp_path):
    slug_task.snapshot_path = None
    with pytest.raises(ValueError, match="no repository snapshot"):
        materialize_repo(slug_task, tmp_path / "x")


def test_expected_verdicts_match_for_the_whole_library(fixtures_dir):
    report = run_bench(fixtures_dir, LocalExecutor(), timeout=3)
    assert report.ok, [r for r in report.rows if not r.match]
    assert report.gold_resolved == report.gold_total == report.tasks
    assert report.base_unresolved == report.base_total
    assert "| Task |" in render_markdown(report)
