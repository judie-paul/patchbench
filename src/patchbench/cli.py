"""Command line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from patchbench.bench import render_markdown, run_bench
from patchbench.executors.base import Executor
from patchbench.loader import DEFAULT_TASKS_DIR, get_task, load_tasks
from patchbench.models import Submission
from patchbench.runner import DEFAULT_TIMEOUT, evaluate

app = typer.Typer(help="Evaluate code patches against a repository's own tests.")

TasksOpt = Annotated[Path, typer.Option("--tasks", help="Directory of task folders.")]
ExecutorOpt = Annotated[str, typer.Option("--executor", help="local (tests only) or docker.")]
TimeoutOpt = Annotated[int, typer.Option("--timeout", help="Seconds before a run is killed.")]


def make_executor(name: str) -> Executor:
    """Build an executor by name."""
    if name == "local":
        from patchbench.executors.local import LocalExecutor

        return LocalExecutor()
    if name == "docker":
        raise typer.BadParameter("the docker executor lands in the next milestone")
    raise typer.BadParameter(f"unknown executor {name!r}; choose local or docker")


@app.command()
def tasks(root: TasksOpt = DEFAULT_TASKS_DIR) -> None:
    """List the available tasks."""
    for task in load_tasks(root):
        typer.echo(
            f"{task.instance_id}\t{task.repo}\t"
            f"F2P={len(task.fail_to_pass)} P2P={len(task.pass_to_pass)}"
        )


@app.command()
def run(
    instance_id: Annotated[str, typer.Argument(help="Task id.")],
    patch: Annotated[Path | None, typer.Option("--patch", help="Unified diff to evaluate.")] = None,
    gold: Annotated[bool, typer.Option("--gold", help="Evaluate the task's gold patch.")] = False,
    root: TasksOpt = DEFAULT_TASKS_DIR,
    executor: ExecutorOpt = "docker",
    timeout: TimeoutOpt = DEFAULT_TIMEOUT,
    show_log: Annotated[bool, typer.Option("--log", help="Print the full run log.")] = False,
) -> None:
    """Evaluate one patch for one task and print the result as JSON."""
    if gold == (patch is not None):
        raise typer.BadParameter("pass exactly one of --patch FILE or --gold")
    task = get_task(root, instance_id)
    text = task.patch if gold else (patch.read_text(encoding="utf-8") if patch else "")
    submission = Submission(instance_id=instance_id, patch=text, label="gold" if gold else "cli")
    result = evaluate(task, submission, make_executor(executor), timeout)
    data = result.model_dump(mode="json", exclude=set() if show_log else {"log"})
    typer.echo(json.dumps(data, indent=2))
    raise typer.Exit(0 if result.verdict == "resolved" else 1)


@app.command()
def bench(
    root: TasksOpt = DEFAULT_TASKS_DIR,
    executor: ExecutorOpt = "local",
    timeout: TimeoutOpt = 10,
    out: Annotated[Path, typer.Option("--out", help="JSON report path.")] = Path("runs/bench.json"),
) -> None:
    """Run every fixture submission and compare verdicts with the expected ones."""
    report = run_bench(root, make_executor(executor), timeout)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    out.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    typer.echo(
        f"{report.executor}: {report.matched}/{report.submissions} verdicts as expected; "
        f"gold resolved {report.gold_resolved}/{report.gold_total}; report: {out}"
    )
    raise typer.Exit(0 if report.ok else 1)
