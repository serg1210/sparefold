"""Peer exchange without a server.

A pack is a JSON file. Accepting it re-runs the checker. A matching hash on a
checker the submitter rewrote is not enough: --base compares checker bytes to
a git ref the peer already trusts.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sparefold.errors import SparefoldError
from sparefold.hashing import sha256_file
from sparefold.ledger import result_path
from sparefold.schema import get_unit
from sparefold.verify import run_checker


def git_show(root: Path, ref: str, rel: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SparefoldError(proc.stderr.decode("utf-8", "replace").strip() or f"git show failed for {rel}")
    return proc.stdout


def pack_results(root: Path) -> dict:
    records = []
    results = root / "ledger" / "results"
    if results.is_dir():
        for path in sorted(results.glob("*.json")):
            records.append(json.loads(path.read_text(encoding="utf-8")))
    return {"version": 1, "results": records}


def write_pack(root: Path, dest: Path) -> dict:
    payload = pack_results(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _checker_ok(root: Path, record: dict, base: str | None) -> list[str]:
    problems = []
    unit = get_unit(root, record["id"])
    for rel, digest in record.get("checker_hashes", {}).items():
        path = root / rel
        if not path.is_file():
            problems.append(f"{record['id']}: missing checker {rel}")
            continue
        if sha256_file(path) != digest:
            problems.append(f"{record['id']}: checker hash mismatch {rel}")
        if base:
            try:
                base_bytes = git_show(root, base, rel)
            except SparefoldError as exc:
                problems.append(f"{record['id']}: {exc}")
                continue
            if base_bytes != path.read_bytes():
                problems.append(f"{record['id']}: {rel} differs from {base}")
    if base:
        unit_path = unit["_path"]
        try:
            base_unit = git_show(root, base, unit_path)
        except SparefoldError as exc:
            problems.append(f"{record['id']}: {exc}")
        else:
            if base_unit != (root / unit_path).read_bytes():
                problems.append(f"{record['id']}: work unit differs from {base}")
    result = run_checker(root, unit)
    if not result.ok:
        tail = (result.stdout + result.stderr).strip().splitlines()
        detail = tail[-1] if tail else "checker failed"
        problems.append(f"{record['id']}: checker failed ({detail})")
    return problems


def audit(root: Path, base: str | None = None) -> list[str]:
    problems: list[str] = []
    results = root / "ledger" / "results"
    if not results.is_dir():
        return problems
    for path in sorted(results.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: {exc}")
            continue
        problems.extend(_checker_ok(root, record, base))
    return problems


def accept_pack(root: Path, pack_path: Path, base: str | None = None) -> list[str]:
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    accepted = []
    for record in payload.get("results", []):
        problems = _checker_ok(root, record, base)
        if problems:
            raise SparefoldError("; ".join(problems))
        dest = result_path(root, record["id"])
        if dest.is_file():
            existing = json.loads(dest.read_text(encoding="utf-8"))
            if existing != record:
                raise SparefoldError(f"{record['id']} already has a different result")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        accepted.append(record["id"])
    return accepted
