# PatchBench

Does a proposed fix actually resolve the issue without breaking anything else?

PatchBench answers that the way SWE-bench does. A **task** is a repository at a base commit, an
issue, and the tests that define the fix (`FAIL_TO_PASS` must start passing, `PASS_TO_PASS` must
keep passing). A **submission** is a unified diff. PatchBench applies it, runs the repository's own
test suite, and reports a verdict with per-test pass/fail and logs.

## Quick start

```bash
make setup        # Python 3.12 virtualenv with development tools
make bench        # evaluate every fixture submission locally, writes runs/bench-local.{json,md}
make lint typecheck test
patchbench tasks
patchbench run patchbench__csvrow-1 --gold --executor local
```

`make bench` needs no network and no Docker. It uses the local executor, which is **not a sandbox**;
run untrusted patches with the Docker executor (milestone 2).

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `resolved` | every FAIL_TO_PASS and PASS_TO_PASS test passes |
| `partial` | some but not all FAIL_TO_PASS tests pass and no PASS_TO_PASS test broke |
| `unresolved` | the issue is not fixed, or the fix breaks PASS_TO_PASS tests |
| `apply_failed` | `git apply` rejected the patch (including paths that escape the repo) |
| `timeout` | the run hit the time limit and its process group was killed |
| `error` | harness problem, such as the test patch not applying |

## How a run works

```
Submission --> stage workspace --> eval.sh --> pytest -rA log --> parse --> grade --> EvalResult
                 repo/ patches/      (apply model patch, apply test patch, run tests)
```

Every executor runs the same generated `eval.sh`; sentinel lines in the log separate an apply
failure from a test failure. Grading is a pure function of the parsed log (`grading.py`).

## Fixtures

`fixtures/tasks/` holds six small pure-Python tasks with real bug classes (accent handling,
off-by-one pagination, case-insensitive headers, unit conversion, LRU recency, CSV quoting).
`scripts/build_fixtures.py` regenerates them and derives FAIL_TO_PASS / PASS_TO_PASS by running
the tests at the base and with the gold patch. Each task ships a submission library with an
expected verdict: `gold`, `empty`, `noop`, `regression`, `malformed`, `traversal`, `hang` (and
`partial` for the CSV task). `make bench` checks every verdict against the expectation.

## Limits

- Grading reads pytest's summary from the log. A patch runs inside the test process, so hostile
  code can print text that imitates a summary; only the last summary block is read, and the
  sandbox contains the damage, but the grader cannot fully prevent spoofing.
- A submission that edits the test files can stop the test patch from applying; that is reported
  as `error`.
