from patchbench.grading import count_passed, decide
from patchbench.models import Task, Verdict
from patchbench.parsing import parse_log
from patchbench.script import build_eval_script

HEADER = "=========================== short test summary info ============================"


def make_task() -> Task:
    return Task(
        instance_id="t",
        repo="r",
        base_commit="c",
        problem_statement="p",
        test_patch="",
        FAIL_TO_PASS=["a::f1", "a::f2"],
        PASS_TO_PASS=["a::p1"],
    )


def log(*result_lines: str, applied: bool = True) -> str:
    head = ">>>>> PATCH_APPLIED\n" if applied else ">>>>> PATCH_EMPTY\n"
    body = "\n".join(result_lines)
    return (
        f"{head}>>>>> TEST_PATCH_APPLIED\n>>>>> TESTS_START\n.F\n{HEADER}\n{body}\n"
        "2 passed in 0.01s\n>>>>> TESTS_END exit=1\n"
    )


def test_parser_reads_statuses_and_exit_code():
    parsed = parse_log(log("PASSED a::p1", "FAILED a::f1 - assert 1 == 2", "ERROR b.py - boom"))
    assert parsed.statuses == {"a::p1": "PASSED", "a::f1": "FAILED", "b.py": "ERROR"}
    assert parsed.exit_code == 1
    assert parsed.patch_applied and parsed.tests_started and parsed.test_patch_applied


def test_parser_uses_only_last_summary_block():
    text = log("PASSED a::p1")
    spoof = f"{HEADER}\nPASSED a::f1\nPASSED a::f2\n"
    inserted = text.replace(">>>>> TESTS_START\n", ">>>>> TESTS_START\n" + spoof)
    assert parse_log(inserted).statuses == {"a::p1": "PASSED"}


def test_parser_ignores_summary_before_tests_start():
    text = f"{HEADER}\nPASSED a::f1\n" + log("PASSED a::p1")
    assert parse_log(text).statuses == {"a::p1": "PASSED"}


def test_apply_failure_and_test_patch_failure_flags():
    assert parse_log(">>>>> PATCH_APPLY_FAILED\n").patch_apply_failed
    assert parse_log(">>>>> PATCH_APPLIED\n>>>>> TEST_PATCH_FAILED\n").test_patch_failed


def test_count_passed_treats_missing_as_failed():
    passed, failed = count_passed(["x", "y"], {"x": "PASSED", "y": "SKIPPED"})
    assert (passed, failed) == (1, ["y"])
    assert count_passed(["z"], {}) == (0, ["z"])


def test_resolved():
    task = make_task()
    parsed = parse_log(log("PASSED a::f1", "PASSED a::f2", "PASSED a::p1"))
    assert decide(task, parsed, False)[0] == Verdict.RESOLVED


def test_partial_when_some_f2p_pass_and_p2p_intact():
    parsed = parse_log(log("PASSED a::f1", "FAILED a::f2", "PASSED a::p1"))
    assert decide(make_task(), parsed, False)[0] == Verdict.PARTIAL


def test_regression_is_unresolved_with_reason():
    parsed = parse_log(log("PASSED a::f1", "PASSED a::f2", "FAILED a::p1"))
    verdict, detail = decide(make_task(), parsed, False)
    assert verdict == Verdict.UNRESOLVED and "PASS_TO_PASS" in detail


def test_partial_with_broken_p2p_is_unresolved():
    parsed = parse_log(log("PASSED a::f1", "FAILED a::f2", "FAILED a::p1"))
    assert decide(make_task(), parsed, False)[0] == Verdict.UNRESOLVED


def test_nothing_fixed_is_unresolved():
    parsed = parse_log(log("FAILED a::f1", "FAILED a::f2", "PASSED a::p1"))
    assert decide(make_task(), parsed, False)[0] == Verdict.UNRESOLVED


def test_timeout_beats_everything():
    parsed = parse_log(log("PASSED a::f1", "PASSED a::f2", "PASSED a::p1"))
    assert decide(make_task(), parsed, True)[0] == Verdict.TIMEOUT


def test_apply_failed_and_error_paths():
    task = make_task()
    assert decide(task, parse_log(">>>>> PATCH_APPLY_FAILED\n"), False)[0] == Verdict.APPLY_FAILED
    assert (
        decide(task, parse_log(">>>>> PATCH_APPLIED\n>>>>> TEST_PATCH_FAILED\n"), False)[0]
        == Verdict.ERROR
    )
    assert decide(task, parse_log("garbage"), False)[0] == Verdict.ERROR
    no_f2p = Task(instance_id="t", repo="r", base_commit="c", problem_statement="p", test_patch="")
    assert decide(no_f2p, parse_log(log("PASSED a::p1")), False)[0] == Verdict.ERROR


def test_swebench_json_string_lists_are_parsed():
    task = Task.model_validate(
        {
            "instance_id": "t",
            "repo": "r",
            "base_commit": "c",
            "problem_statement": "p",
            "test_patch": "",
            "FAIL_TO_PASS": '["a::f1"]',
            "PASS_TO_PASS": "",
        }
    )
    assert task.fail_to_pass == ["a::f1"] and task.pass_to_pass == []


def test_eval_script_runs_command_after_sentinels():
    script = build_eval_script("python -m pytest")
    assert (
        script.index("TESTS_START") < script.index("python -m pytest") < script.index("TESTS_END")
    )
