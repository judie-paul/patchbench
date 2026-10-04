import json
import shutil

import pytest
import typer
from typer.testing import CliRunner

from patchbench.cli import app, make_executor
from patchbench.loader import get_task, load_tasks

runner = CliRunner()


def test_tasks_command_lists_fixtures(fixtures_dir):
    result = runner.invoke(app, ["tasks", "--tasks", str(fixtures_dir)])
    assert result.exit_code == 0
    assert "patchbench__slugify-1" in result.output


def test_run_gold_prints_json_and_exit_zero(fixtures_dir):
    result = runner.invoke(
        app,
        [
            "run",
            "patchbench__slugify-1",
            "--gold",
            "--executor",
            "local",
            "--tasks",
            str(fixtures_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["verdict"] == "resolved" and "log" not in data


def test_run_requires_exactly_one_patch_source(fixtures_dir):
    result = runner.invoke(app, ["run", "patchbench__slugify-1", "--tasks", str(fixtures_dir)])
    assert result.exit_code != 0


def test_run_with_patch_file_exit_one_when_unresolved(fixtures_dir, tmp_path):
    empty = tmp_path / "empty.patch"
    empty.write_text("")
    result = runner.invoke(
        app,
        [
            "run",
            "patchbench__slugify-1",
            "--patch",
            str(empty),
            "--executor",
            "local",
            "--log",
            "--tasks",
            str(fixtures_dir),
        ],
    )
    assert result.exit_code == 1
    assert "TESTS_START" in json.loads(result.output)["log"]


def test_unknown_task_and_executor_errors(fixtures_dir):
    with pytest.raises(KeyError, match="unknown task"):
        get_task(fixtures_dir, "nope")
    with pytest.raises(FileNotFoundError):
        load_tasks(fixtures_dir / "missing")
    with pytest.raises(typer.BadParameter):
        make_executor("vm")


def test_bench_command_writes_reports(fixtures_dir, tmp_path):
    one = tmp_path / "tasks"
    shutil.copytree(fixtures_dir / "patchbench__slugify-1", one / "patchbench__slugify-1")
    out = tmp_path / "bench.json"
    result = runner.invoke(app, ["bench", "--tasks", str(one), "--timeout", "3", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text())["matched"] == json.loads(out.read_text())["submissions"]
    assert out.with_suffix(".md").exists()
