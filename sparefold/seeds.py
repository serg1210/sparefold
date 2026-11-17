"""Seed artifacts the demo re-runs. If these fail, the lanes are vapor."""

from __future__ import annotations

import json
from pathlib import Path

from sparefold.checkers import check_correct, check_env, check_proof
from sparefold.examples.corridor import Corridor
from sparefold.examples.saxpy import saxpy, saxpy_indexed


def run_seeds() -> None:
    check_env(Corridor)
    cases = [
        (2.0, [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]),
        (0.0, [1.0], [2.0]),
        (-1.5, [2.0, -2.0], [1.0, 1.0]),
    ]
    check_correct(saxpy, saxpy_indexed, cases)
    proof_path = Path(__file__).resolve().parent / "examples" / "imply_self.json"
    check_proof(json.loads(proof_path.read_text(encoding="utf-8")))
