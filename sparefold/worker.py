"""Turn a work unit into a prompt, then optionally hand it to a local agent CLI.

Sparefold does not see your login. The CLI you already pay for does the work.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from sparefold.schema import get_unit

# Flags confirmed against `claude --help` on this machine (acceptEdits, not a bypass)
# and OpenAI's codex exec docs (--sandbox workspace-write). Hermes has no confirmed
# one-shot flag here, so Hermes joins by pasting JOIN.md.
AGENT_ARGV = {
    "claude": ["claude", "-p", "--permission-mode", "acceptEdits"],
    "codex": ["codex", "exec", "--sandbox", "workspace-write"],
}


def build_prompt(unit: dict, handle: str) -> str:
    allowed = "\n".join(f"- {path}" for path in unit["allowed_paths"])
    checkers = "\n".join(f"- {path}" for path in unit["checker"]["paths"])
    return f"""You are working a Sparefold unit. Spend this session's quota on this unit only.

Unit: {unit['id']}
Project: {unit['project']}
Handle: {handle}
Title: {unit['title']}

Contract:
{unit['spec'].rstrip()}

You may create or edit only:
{allowed}

You may not edit:
{checkers}
You may not edit sparefold.toml, the ledger, or any checker.
You may not read, print, or exfiltrate credentials, API keys, tokens, or session cookies.
You may not widen the task. If the contract and the checker disagree, stop and say so.

When the edit is in place, run:
python3 -m sparefold verify {unit['id']}

If it exits 0, stop. Do not submit unless the operator asked you to submit.
If it fails, fix only allowed paths and verify again. If you cannot, stop and report the failure.
"""


def build_command(agent: str, prompt: str) -> list[str]:
    if agent not in AGENT_ARGV:
        raise ValueError(f"unknown agent {agent!r}")
    return [*AGENT_ARGV[agent], prompt]


def run_agent(
    root: Path,
    unit_id: str,
    agent: str,
    handle: str,
    which=shutil.which,
    runner=None,
) -> int:
    unit = get_unit(root, unit_id)
    prompt = build_prompt(unit, handle)
    if agent == "dry":
        print(prompt)
        return 0
    if agent not in AGENT_ARGV:
        print(f"unknown agent {agent!r}. Use dry, claude, or codex.")
        return 2
    binary = AGENT_ARGV[agent][0]
    if which(binary) is None:
        print(f"{binary} is not on PATH. Install it, or run with --agent dry and paste the prompt.")
        return 127
    command = build_command(agent, prompt)
    if agent == "codex":
        git = root / ".git"
        if not git.exists():
            print("codex exec requires a git repository. Run git init in this repo first.")
            return 2
    print(f"starting {binary} on {unit_id}. This spends your own quota. Ctrl-C aborts.")
    if runner is None:
        completed = subprocess.run(command, cwd=root, check=False)
        return completed.returncode
    return runner(command, root)
