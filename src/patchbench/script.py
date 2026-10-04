"""The eval script every executor runs.

Layout under the work directory (``/work`` in a container): ``repo/`` is the repository at the
base commit, ``patches/model.patch`` the submission and ``patches/test.patch`` the tests that
define the fix. Sentinel lines let the parser tell an apply failure from a test failure.
"""

from __future__ import annotations

SENTINEL = ">>>>> "
PATCH_APPLIED = f"{SENTINEL}PATCH_APPLIED"
PATCH_EMPTY = f"{SENTINEL}PATCH_EMPTY"
PATCH_APPLY_FAILED = f"{SENTINEL}PATCH_APPLY_FAILED"
TEST_PATCH_APPLIED = f"{SENTINEL}TEST_PATCH_APPLIED"
TEST_PATCH_FAILED = f"{SENTINEL}TEST_PATCH_FAILED"
TESTS_START = f"{SENTINEL}TESTS_START"
TESTS_END = f"{SENTINEL}TESTS_END"


def build_eval_script(test_command: str) -> str:
    """Return a bash script that applies both patches and runs ``test_command``."""
    return f"""#!/usr/bin/env bash
set -u
WORK="${{PATCHBENCH_WORK:-/work}}"
cd "$WORK/repo" || exit 2
if [ -s "$WORK/patches/model.patch" ]; then
  if git apply --whitespace=nowarn "$WORK/patches/model.patch"; then
    echo "{PATCH_APPLIED}"
  else
    echo "{PATCH_APPLY_FAILED}"
    exit 0
  fi
else
  echo "{PATCH_EMPTY}"
fi
if git apply --whitespace=nowarn "$WORK/patches/test.patch"; then
  echo "{TEST_PATCH_APPLIED}"
else
  echo "{TEST_PATCH_FAILED}"
  exit 0
fi
echo "{TESTS_START}"
{test_command}
echo "{TESTS_END} exit=$?"
"""
