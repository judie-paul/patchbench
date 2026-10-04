# PatchBench

A SWE-bench-style task runner: it checks whether a proposed patch actually resolves an issue
without breaking anything else, by running the patch against the repository's own test suite in
an isolated Docker container.

> Work in progress. See [PLAN.md](PLAN.md) once it lands for the roadmap.
