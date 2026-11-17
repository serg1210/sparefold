"""Work-unit files. JSON, stdlib only, so joining needs no installer."""

from __future__ import annotations

import json
from pathlib import Path

from sparefold.errors import SchemaError

STATUSES = {"open", "ready"}
LANES = {"self", "gtm", "gym", "kernel", "proof"}
REQUIRED = (
    "id",
    "project",
    "title",
    "summary",
    "spec",
    "points",
    "budget_minutes",
    "claim_ttl_minutes",
    "lane",
    "status",
    "allowed_paths",
    "checker",
)


def validate(unit: dict, source: str) -> None:
    missing = [key for key in REQUIRED if key not in unit]
    if missing:
        raise SchemaError(f"{source}: missing {', '.join(missing)}")
    if not isinstance(unit["id"], str) or not unit["id"]:
        raise SchemaError(f"{source}: id must be a non-empty string")
    if unit["status"] not in STATUSES:
        raise SchemaError(f"{source}: status must be open or ready")
    if unit["lane"] not in LANES:
        raise SchemaError(f"{source}: unknown lane {unit['lane']!r}")
    if not isinstance(unit["project"], str) or not unit["project"]:
        raise SchemaError(f"{source}: project must be a non-empty string")
    points = unit["points"]
    if not isinstance(points, int) or isinstance(points, bool) or not 1 <= points <= 8:
        raise SchemaError(f"{source}: points must be an int from 1 to 8")
    for key in ("budget_minutes", "claim_ttl_minutes"):
        value = unit[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise SchemaError(f"{source}: {key} must be a positive int")
    spec = unit["spec"]
    if not isinstance(spec, str) or len(spec.strip()) < 40:
        raise SchemaError(f"{source}: spec is too short to be a contract")
    allowed = unit["allowed_paths"]
    if not isinstance(allowed, list) or not allowed or not all(isinstance(p, str) for p in allowed):
        raise SchemaError(f"{source}: allowed_paths must be a non-empty list of strings")
    checker = unit["checker"]
    if not isinstance(checker, dict):
        raise SchemaError(f"{source}: checker must be an object")
    command = checker.get("command")
    paths = checker.get("paths")
    timeout = checker.get("timeout_s")
    if not isinstance(command, list) or not command or not all(isinstance(p, str) for p in command):
        raise SchemaError(f"{source}: checker.command must be a list of strings")
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
        raise SchemaError(f"{source}: checker.paths must be a non-empty list of strings")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 600:
        raise SchemaError(f"{source}: checker.timeout_s must be an int from 1 to 600")
    for path in paths:
        if _is_allowed(path, allowed):
            raise SchemaError(f"{source}: checker path {path} is also an allowed edit")


def _is_allowed(rel: str, allowed: list[str]) -> bool:
    rel = rel.replace("\\", "/")
    for item in allowed:
        item = item.replace("\\", "/")
        if rel == item or rel.startswith(item.rstrip("/") + "/"):
            return True
    return False


def is_allowed(rel: str, allowed: list[str]) -> bool:
    return _is_allowed(rel, allowed)


def load_work_units(root: Path) -> list[dict]:
    units: list[dict] = []
    work_root = root / "projects"
    if not work_root.is_dir():
        raise SchemaError(f"missing {work_root}")
    for path in sorted(work_root.glob("*/work/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SchemaError(f"{path}: {exc}") from exc
        if not isinstance(data, dict):
            raise SchemaError(f"{path}: work unit must be an object")
        rel = path.relative_to(root).as_posix()
        validate(data, rel)
        project_dir = path.parents[1].name
        if data["project"] != project_dir:
            raise SchemaError(f"{rel}: project {data['project']!r} does not match directory {project_dir}")
        if path.stem != data["id"]:
            raise SchemaError(f"{rel}: filename must match id {data['id']}")
        data["_path"] = rel
        units.append(data)
    ids = [unit["id"] for unit in units]
    if len(ids) != len(set(ids)):
        raise SchemaError("duplicate work unit id")
    return units


def get_unit(root: Path, unit_id: str) -> dict:
    for unit in load_work_units(root):
        if unit["id"] == unit_id:
            return unit
    raise SchemaError(f"no work unit {unit_id}")
