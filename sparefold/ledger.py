"""Claims and results. A claim is an exclusive file. A result is a credit."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sparefold.errors import ClaimError, SchemaError, SubmitError
from sparefold.hashing import sha256_file, tree_files
from sparefold.schema import get_unit, is_allowed

HANDLE_OK = set("abcdefghijklmnopqrstuvwxyz0123456789-_")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def validate_handle(handle: str) -> str:
    if not isinstance(handle, str) or not 2 <= len(handle) <= 32:
        raise ClaimError("handle must be 2-32 characters")
    if handle[0] not in "abcdefghijklmnopqrstuvwxyz0123456789":
        raise ClaimError("handle must start with a letter or digit")
    if any(ch not in HANDLE_OK for ch in handle):
        raise ClaimError("handle may contain only lowercase letters, digits, _ and -")
    return handle


def local_path(root: Path) -> Path:
    return root / "ledger" / "local.json"


def claim_path(root: Path, unit_id: str) -> Path:
    return root / "ledger" / "claims" / f"{unit_id}.json"


def result_path(root: Path, unit_id: str) -> Path:
    return root / "ledger" / "results" / f"{unit_id}.json"


def read_local(root: Path) -> dict | None:
    path = local_path(root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def join(root: Path, handle: str) -> dict:
    handle = validate_handle(handle)
    path = local_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"handle": handle, "joined_at": _iso(utcnow())}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def require_handle(root: Path, handle: str | None) -> str:
    if handle:
        return validate_handle(handle)
    local = read_local(root)
    if not local:
        raise ClaimError("no handle. Run `python3 -m sparefold join --handle yourname` first.")
    return validate_handle(local["handle"])


def _snapshot(root: Path, unit: dict) -> tuple[dict, dict]:
    checker_hashes = {}
    for rel in unit["checker"]["paths"]:
        path = root / rel
        if not path.is_file():
            raise ClaimError(f"checker file missing: {rel}")
        checker_hashes[rel] = sha256_file(path)
    tree = {}
    for path in tree_files(root):
        rel = path.relative_to(root).as_posix()
        if is_allowed(rel, unit["allowed_paths"]):
            continue
        if rel in checker_hashes:
            continue
        tree[rel] = sha256_file(path)
    return checker_hashes, tree


def _write_exclusive(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        raise ClaimError("claim file exists") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def claim(root: Path, unit_id: str, handle: str, now: datetime | None = None) -> dict:
    handle = validate_handle(handle)
    unit = get_unit(root, unit_id)
    if unit["status"] != "open":
        raise ClaimError(f"{unit_id} is {unit['status']}, not open")
    if result_path(root, unit_id).is_file():
        raise ClaimError(f"{unit_id} already has an accepted result")
    now = now or utcnow()
    path = claim_path(root, unit_id)
    for _ in range(3):
        if path.is_file():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
                expires = _parse(existing["expires_at"])
            except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
                raise ClaimError(f"unreadable claim on {unit_id}: {exc}") from exc
            if expires > now:
                owner = existing.get("handle", "someone")
                raise ClaimError(f"{unit_id} is claimed by {owner} until {existing['expires_at']}")
            path.unlink()
        checker_hashes, tree_hashes = _snapshot(root, unit)
        payload = {
            "id": unit_id,
            "handle": handle,
            "claimed_at": _iso(now),
            "expires_at": _iso(now + timedelta(minutes=unit["claim_ttl_minutes"])),
            "checker_hashes": checker_hashes,
            "tree_hashes": tree_hashes,
        }
        try:
            _write_exclusive(path, payload)
            return payload
        except ClaimError:
            continue
    raise ClaimError(f"could not claim {unit_id}")


def release(root: Path, unit_id: str, handle: str) -> None:
    handle = validate_handle(handle)
    path = claim_path(root, unit_id)
    if not path.is_file():
        raise ClaimError(f"{unit_id} is not claimed")
    existing = json.loads(path.read_text(encoding="utf-8"))
    if existing.get("handle") != handle:
        raise ClaimError(f"{unit_id} is claimed by {existing.get('handle')}, not {handle}")
    path.unlink()


def load_claim(root: Path, unit_id: str) -> dict:
    path = claim_path(root, unit_id)
    if not path.is_file():
        raise ClaimError(f"{unit_id} is not claimed. Claim it before submitting.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClaimError(f"unreadable claim: {exc}") from exc


def assert_unchanged(root: Path, unit: dict, claim_record: dict, now: datetime | None = None) -> None:
    now = now or utcnow()
    if claim_record.get("id") != unit["id"]:
        raise SubmitError("claim id does not match the work unit")
    if _parse(claim_record["expires_at"]) <= now:
        raise SubmitError("claim has expired")
    for rel, digest in claim_record["checker_hashes"].items():
        path = root / rel
        if not path.is_file() or sha256_file(path) != digest:
            raise SubmitError(f"checker changed after claim: {rel}")
    for rel, digest in claim_record["tree_hashes"].items():
        path = root / rel
        if not path.is_file() or sha256_file(path) != digest:
            raise SubmitError(f"file outside allowed_paths changed: {rel}")
    claimed = set(claim_record["tree_hashes"]) | set(claim_record["checker_hashes"])
    for path in tree_files(root):
        rel = path.relative_to(root).as_posix()
        if rel in claimed or is_allowed(rel, unit["allowed_paths"]):
            continue
        raise SubmitError(f"new file outside allowed_paths: {rel}")


def write_result(root: Path, unit: dict, handle: str, checker_hashes: dict) -> dict:
    if result_path(root, unit["id"]).is_file():
        raise SubmitError(f"{unit['id']} already has a result")
    artifact_hashes = {}
    for rel in unit["allowed_paths"]:
        path = root / rel
        if path.is_file():
            artifact_hashes[rel] = sha256_file(path)
    record = {
        "version": 1,
        "id": unit["id"],
        "project": unit["project"],
        "handle": handle,
        "points": unit["points"],
        "accepted_at": _iso(utcnow()),
        "checker_hashes": checker_hashes,
        "artifact_hashes": artifact_hashes,
    }
    path = result_path(root, unit["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    claim_file = claim_path(root, unit["id"])
    if claim_file.is_file():
        claim_file.unlink()
    return record


def leaderboard(root: Path) -> list[dict]:
    results_dir = root / "ledger" / "results"
    rows: dict[str, dict] = {}
    if not results_dir.is_dir():
        return []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == ".gitkeep":
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SchemaError(f"{path.name}: {exc}") from exc
        handle = record["handle"]
        row = rows.setdefault(handle, {"handle": handle, "points": 0, "units": []})
        row["points"] += int(record["points"])
        row["units"].append(record["id"])
    return sorted(rows.values(), key=lambda row: (-row["points"], row["handle"]))
