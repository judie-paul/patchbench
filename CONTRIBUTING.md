# Contributing

Run `make setup`, then `make lint typecheck test` before proposing a change.
Use small branches named `feat/`, `fix/`, `docs/`, `test/`, `ci/` or `chore/`
and Conventional Commits such as `feat(runner): classify patch apply failures`.
Keep `main` releasable; do not force-push or rewrite shared history.

Track each unit of work with an issue that has acceptance criteria, and link it
from the pull request. Review the diff and require passing checks before merging.
Update `CHANGELOG.md` and `PROGRESS.md` as part of the change, not afterwards.

Guidelines:

- Submitted patches are untrusted code. Anything that executes one runs inside the Docker
  sandbox (no network, resource limits, non-root, hard timeout). The local executor exists
  for tests and fixtures only and says so in its output.
- Grading is a pure function of parsed test results and is unit tested, including the
  partial, apply-failure and timeout cases.
- Default tests never use the network or a Docker daemon. Mark those that do `network` or
  `docker`; they run in their own CI jobs or with `make test-docker`.
- Task fixtures are small, committed and verified: every fixture's gold patch must resolve
  it and its base must fail.
- Record the task set, executor, image and command behind every published number.
- Never commit cloned third-party repositories, credentials or invented results.
