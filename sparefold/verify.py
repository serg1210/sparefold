"""Run a work unit's checker. The exit code is the verdict."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VerifyResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run_checker(root: Path, unit: dict) -> VerifyResult:
    command = list(unit["checker"]["command"])
    if command[0] in {"python", "python3"}:
        command[0] = sys.executable
    timeout = int(unit["checker"]["timeout_s"])
    try:
        proc = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        return VerifyResult(returncode=124, stdout=stdout, stderr=stderr + "\nchecker timed out\n", timed_out=True)
    return VerifyResult(proc.returncode, proc.stdout, proc.stderr)
