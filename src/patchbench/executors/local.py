"""Local subprocess executor.

NOT a sandbox: the patch's code runs with the caller's privileges. It exists so unit tests and
fixture generation work without a Docker daemon. Use the Docker executor for untrusted patches.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from patchbench.executors.base import ExecOutput, truncate_log


class LocalExecutor:
    """Run the eval script in a subprocess group that is killed on timeout."""

    name = "local"

    def run(self, work: Path, timeout: int) -> ExecOutput:
        env = {
            "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}",
            "HOME": str(work),
            "PATCHBENCH_WORK": str(work),
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": "C.UTF-8",
        }
        start = time.monotonic()
        proc = subprocess.Popen(
            ["bash", str(work / "eval.sh")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=work,
            start_new_session=True,
        )
        timed_out = False
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            out, _ = proc.communicate()
        text = truncate_log(out.decode("utf-8", "replace"))
        return ExecOutput(
            log=text,
            timed_out=timed_out,
            exit_code=None if timed_out else proc.returncode,
            duration_s=time.monotonic() - start,
        )
