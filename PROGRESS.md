# Progress

## Current phase

Milestone 1 (evaluation core, issue #3) is in review. Docker sandbox, task sources, service and UI
are not started.

## Implemented

- MIT license, contribution guidance, code of conduct, issue/PR templates, roadmap (PR #2).
- Pydantic task, submission and result models; SWE-bench-style verdicts.
- One generated `eval.sh` shared by all executors, with sentinel lines; pytest `-rA` log parser
  that reads only the last summary block; pure grading function.
- Local subprocess executor (tests only, killed by process group on timeout).
- Six verified fixture tasks and a 43-submission library (gold, empty, noop, regression,
  malformed, traversal, hang, partial), rebuilt by `scripts/build_fixtures.py`.
- `patchbench tasks|run|bench`, Makefile, pre-commit config, Python 3.11/3.12 CI.

## Measured

`make bench` (local executor, 10 s timeout, this machine): 43/43 verdicts as expected, 6/6 gold
patches resolved, 6/6 empty patches unresolved, 70.09 s of evaluation time. Written to
`runs/bench-local.{json,md}` (not committed).
