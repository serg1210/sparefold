"""Content hashes. The checker hash is what a peer re-checks."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_files(root: Path) -> list[Path]:
    """Files a claim snapshot covers. Skips git metadata, caches, and local identity."""
    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "dist"}
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in skip_dirs or part.endswith(".egg-info") for part in rel_parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "ledger/local.json" or rel.startswith("ledger/claims/"):
            continue
        found.append(path)
    return found
