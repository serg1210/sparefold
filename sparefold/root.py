"""Find the repo that contains sparefold.toml."""

from __future__ import annotations

from pathlib import Path

from sparefold.errors import SparefoldError


def find_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "sparefold.toml").is_file():
            return candidate
    raise SparefoldError(
        "not a Sparefold repo (no sparefold.toml). Clone the repo and run from inside it."
    )
