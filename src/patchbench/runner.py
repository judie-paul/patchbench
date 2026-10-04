"""Evaluate one submission: stage a workspace, run it in an executor, grade the log."""

from __future__ import annotations

import shutil
import stat
import tempfile
from pathlib import Path

from patchbench.executors.base import ExecOutput, Executor
from patchbench.grading import count_passed, decide
from patchbench.models import EvalResult, Submission, Task
from patchbench.parsing import ParsedLog, parse_log
from patchbench.script import build_eval_script

DEFAULT_TIMEOUT = 120


def materialize_repo(task: Task, dest: Path) -> None:
    """Place the repository at ``task.base_commit`` into ``dest``."""
    if task.snapshot_path is None:
        raise ValueError(f"{task.instance_id} has no repository snapshot to evaluate against")
    shutil.copytree(task.snapshot_path, dest)


def stage_workspace(task: Task, patch: str, work: Path) -> None:
    """Write repo/, patches/ and eval.sh under ``work``."""
    materialize_repo(task, work / "repo")
    patches = work / "patches"
    patches.mkdir()
    (patches / "model.patch").write_text(_with_newline(patch), encoding="utf-8")
    (patches / "test.patch").write_text(_with_newline(task.test_patch), encoding="utf-8")
    script = work / "eval.sh"
    script.write_text(build_eval_script(task.test_command), encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)


def _with_newline(text: str) -> str:
    return text if not text or text.endswith("\n") else text + "\n"


def execute(
    task: Task, patch: str, executor: Executor, timeout: int = DEFAULT_TIMEOUT
) -> tuple[ExecOutput, ParsedLog]:
    """Run ``patch`` for ``task`` and return the raw output and its parsed log."""
    with tempfile.TemporaryDirectory(prefix="patchbench-") as tmp:
        work = Path(tmp)
        stage_workspace(task, patch, work)
        out = executor.run(work, timeout)
    return out, parse_log(out.log)


def evaluate(
    task: Task, submission: Submission, executor: Executor, timeout: int = DEFAULT_TIMEOUT
) -> EvalResult:
    """Grade ``submission`` against ``task``."""
    out, parsed = execute(task, submission.patch, executor, timeout)
    verdict, detail = decide(task, parsed, out.timed_out)
    f2p_passed, failed_f2p = count_passed(task.fail_to_pass, parsed.statuses)
    p2p_passed, failed_p2p = count_passed(task.pass_to_pass, parsed.statuses)
    return EvalResult(
        instance_id=task.instance_id,
        label=submission.label,
        verdict=verdict,
        executor=executor.name,
        patch_applied=parsed.patch_applied,
        f2p_passed=f2p_passed,
        f2p_total=len(task.fail_to_pass),
        p2p_passed=p2p_passed,
        p2p_total=len(task.pass_to_pass),
        failed_f2p=failed_f2p,
        failed_p2p=failed_p2p,
        tests=parsed.statuses,
        duration_s=round(out.duration_s, 3),
        timed_out=out.timed_out,
        log=out.log,
        detail=detail,
    )
