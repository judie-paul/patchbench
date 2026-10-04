"""Load tasks and submission libraries from a directory tree.

Layout: ``<root>/<instance_id>/task.json`` with the repository at ``repo/`` and candidate
patches in ``submissions/<label>.patch`` next to ``submissions/expected.json``
(``{label: verdict}``).
"""

from __future__ import annotations

import json
from pathlib import Path

from patchbench.models import Submission, Task, Verdict

DEFAULT_TASKS_DIR = Path("fixtures/tasks")


def load_task(task_dir: Path) -> Task:
    """Read one task directory."""
    data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    task = Task.model_validate(data)
    repo = task_dir / "repo"
    if repo.is_dir():
        task.snapshot_path = repo.resolve()
    return task


def load_tasks(root: Path) -> list[Task]:
    """Read every task under ``root`` in a stable order."""
    if not root.is_dir():
        raise FileNotFoundError(f"task directory not found: {root}")
    return [load_task(path.parent) for path in sorted(root.glob("*/task.json"))]


def get_task(root: Path, instance_id: str) -> Task:
    """Read one task by id, with a clear error for unknown ids."""
    task_dir = root / instance_id
    if not (task_dir / "task.json").is_file():
        known = ", ".join(t.instance_id for t in load_tasks(root)) or "none"
        raise KeyError(f"unknown task {instance_id!r}; known: {known}")
    return load_task(task_dir)


def load_submissions(root: Path, instance_id: str) -> list[tuple[Submission, Verdict]]:
    """Return the labelled submissions for a task with their expected verdicts."""
    sub_dir = root / instance_id / "submissions"
    expected_file = sub_dir / "expected.json"
    if not expected_file.is_file():
        return []
    expected = json.loads(expected_file.read_text(encoding="utf-8"))
    out: list[tuple[Submission, Verdict]] = []
    for label in sorted(expected):
        patch = (sub_dir / f"{label}.patch").read_text(encoding="utf-8")
        out.append((Submission(instance_id=instance_id, patch=patch, label=label), expected[label]))
    return out
