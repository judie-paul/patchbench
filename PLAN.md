# PatchBench implementation plan

## Scope and working agreement

Build the PatchBench runner described in the portfolio brief incrementally: given a task (a
repository snapshot, an issue and the tests that define the fix) and a submitted patch, decide
whether the patch resolves the issue without breaking anything else, by running the repository's
own tests in an isolated Docker container, and report per-test results and logs.

The owner has authorized creating the public judie-paul/patchbench repository and delivering work
through issues, branches and pull requests. Every number in the docs comes from a recorded command.

Verdicts follow SWE-bench: a task is **resolved** when every FAIL_TO_PASS test passes and every
PASS_TO_PASS test still passes; **partial** when some but not all FAIL_TO_PASS tests pass (or a
fix breaks previously passing tests); otherwise **unresolved**. Patches that do not apply and runs
that time out are distinct outcomes, not silent failures.

## Milestone 1: evaluation core

- Hatchling package, Python 3.11+, pydantic models for tasks, submissions and results.
- A committed fixture set of small, verified tasks (real bug classes in tiny pure-Python
  packages) and a library of submissions per task: gold, empty, wrong, regression, malformed, hang.
- One generated eval script (apply patch, apply test patch, run pytest) shared by all executors,
  with sentinel lines so apply failures are told apart from test failures.
- pytest output parser, SWE-bench-style grading, local executor (tests only), Typer `run`/`bench`.
- Gate: every fixture's gold patch resolves it and its base fails; each broken submission gets
  the expected verdict.

## Milestone 2: Docker sandbox

- Runner image, Docker SDK executor: no network, memory/CPU/pids limits, non-root, read-only
  patches, hard timeout that kills the container, logs captured and container always removed.
- Isolation tests that a submitted patch cannot reach the network, fork-bomb, or outlive its timeout.
- Gate: the fixture benchmark gives identical verdicts under Docker and the local executor.

## Milestone 3: task sources

- Task generation by reverting a fix commit in a local git repository (tests split from source).
- GitHub REST client for closed issues and their fix commits (psf/requests, pallets/flask).
- SWE-bench Lite loader (`princeton-nlp/SWE-bench_Lite`) pinned to a dataset revision.
- Gate: a real SWE-bench Lite pure-Python instance is built and its gold patch evaluated, or the
  limitation is documented with the reason.

## Milestone 4: service

- SQLite store, FastAPI endpoints to list tasks, submit patches and read results and logs.
- Celery workers with RabbitMQ; eager mode and in-memory transport for tests.
- Gate: a submission flows API -> RabbitMQ -> worker -> Docker -> result against a real broker.

## Milestone 5: web UI and delivery

- React + Vite UI: tasks, submissions, per-test pass/fail and logs.
- Dockerfile and Compose for API, worker, RabbitMQ and UI; CI jobs for Python, web and container.

## Milestone 6: results and release

- Reproducible benchmark results with commands, README with architecture diagram, tag v0.1.0.

## Non-goals

No model-driven patch generation, no scoring of full SWE-bench, and no claims beyond what was
measured. Deployment to a VPS is documented but not claimed unless done.
