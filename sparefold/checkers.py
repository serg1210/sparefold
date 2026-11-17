"""Three checkers. Finding the artifact is hard. Checking it is cheap and local.

Gym: Gymnasium-shaped reset/step/seed contract, no gymnasium install.
Kernel: numerical agreement, plus an optional speedup gate.
Proof: implicational natural deduction. The checker computes the formula.
"""

from __future__ import annotations

import time
from typing import Any, Callable


class CheckError(Exception):
    pass


def check_env(factory: Callable[[], Any], actions: tuple[int, ...] = (1, 1, 1, 1)) -> None:
    probe = factory()
    for attr in ("observation_space", "action_space", "reset", "step"):
        if not hasattr(probe, attr):
            raise CheckError(f"env is missing {attr}")

    probe.reset(seed=0)
    try:
        probe.step(999)
    except ValueError:
        pass
    else:
        raise CheckError("invalid action must raise ValueError")

    def rollout(seed: int) -> list:
        env = factory()
        obs, _info = env.reset(seed=seed)
        if not env.observation_space.contains(obs):
            raise CheckError("reset observation is outside observation_space")
        frames: list = [obs]
        terminated = False
        truncated = False
        for action in actions:
            if terminated or truncated:
                break
            obs, reward, terminated, truncated, _info = env.step(action)
            if isinstance(reward, bool) or not isinstance(reward, (int, float)):
                raise CheckError("reward must be a number")
            if not isinstance(terminated, bool) or not isinstance(truncated, bool):
                raise CheckError("terminated and truncated must be bool")
            if not env.observation_space.contains(obs):
                raise CheckError("step observation is outside observation_space")
            frames.append((obs, float(reward), terminated, truncated))
        return frames

    if rollout(0) != rollout(0):
        raise CheckError("same seed produced two different trajectories")

    env = factory()
    env.reset(seed=0)
    ended = False
    for _ in range(50):
        _obs, _reward, terminated, truncated, _info = env.step(1)
        if terminated or truncated:
            ended = True
            break
    if not ended:
        raise CheckError("episode did not end within 50 right-steps")
    try:
        env.step(1)
    except Exception:
        return
    raise CheckError("step after termination must raise")


def _close(left: Any, right: Any, tol: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tol
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_close(a, b, tol) for a, b in zip(left, right))
    return left == right


def check_correct(reference: Callable, candidate: Callable, cases: list[tuple], tol: float = 1e-9) -> None:
    if not cases:
        raise CheckError("no cases")
    for index, args in enumerate(cases):
        try:
            expected = reference(*args)
            got = candidate(*args)
        except Exception as exc:
            raise CheckError(f"case {index} raised {exc}") from exc
        if not _close(expected, got, tol):
            raise CheckError(f"case {index} mismatch: expected {expected!r} got {got!r}")


def check_faster(
    slow: Callable,
    fast: Callable,
    args: tuple,
    repeats: int = 5,
    min_ratio: float = 2.0,
) -> float:
    if repeats < 1:
        raise CheckError("repeats must be positive")

    def elapsed(fn: Callable) -> float:
        fn(*args)
        started = time.perf_counter()
        for _ in range(repeats):
            fn(*args)
        return time.perf_counter() - started

    slow_s = elapsed(slow)
    fast_s = elapsed(fast)
    if fast_s <= 0:
        return min_ratio
    ratio = slow_s / fast_s
    if ratio < min_ratio:
        raise CheckError(f"speedup {ratio:.2f} is below {min_ratio}")
    return ratio


def _validate_formula(formula: dict) -> None:
    if not isinstance(formula, dict) or "op" not in formula:
        raise CheckError("formula must be an object with op")
    op = formula["op"]
    if op == "atom":
        name = formula.get("name")
        if not isinstance(name, str) or not name.isidentifier():
            raise CheckError("atom name must be an identifier")
        return
    if op == "implies":
        _validate_formula(formula["left"])
        _validate_formula(formula["right"])
        return
    raise CheckError(f"unsupported op {op!r}")


def check_proof(document: dict) -> None:
    """Accept a closed implicational proof. Derived formulas are computed, not trusted."""
    if not isinstance(document, dict):
        raise CheckError("proof must be an object")
    goal = document.get("goal")
    steps = document.get("steps")
    _validate_formula(goal)
    if not isinstance(steps, list) or not steps:
        raise CheckError("proof needs steps")

    known: dict[str, dict] = {}
    assumptions: dict[str, dict] = {}
    last = None
    for step in steps:
        if not isinstance(step, dict) or "id" not in step or "rule" not in step:
            raise CheckError("each step needs id and rule")
        sid = step["id"]
        if not isinstance(sid, str) or sid in known:
            raise CheckError(f"bad or duplicate step id {sid!r}")
        rule = step["rule"]
        if rule == "assume":
            formula = step.get("formula")
            _validate_formula(formula)
            record = {"formula": formula, "context": frozenset([sid])}
            assumptions[sid] = record
            known[sid] = record
        elif rule == "imply_intro":
            src = known.get(step.get("from"))
            discharge = step.get("discharge")
            if src is None or not isinstance(discharge, str):
                raise CheckError(f"{sid}: imply_intro needs from and discharge")
            if discharge not in src["context"] or discharge not in assumptions:
                raise CheckError(f"{sid}: cannot discharge {discharge}")
            record = {
                "formula": {
                    "op": "implies",
                    "left": assumptions[discharge]["formula"],
                    "right": src["formula"],
                },
                "context": src["context"] - {discharge},
            }
            known[sid] = record
        elif rule == "imply_elim":
            imp = known.get(step.get("implies"))
            ant = known.get(step.get("antecedent"))
            if imp is None or ant is None:
                raise CheckError(f"{sid}: imply_elim needs implies and antecedent")
            formula = imp["formula"]
            if formula.get("op") != "implies" or formula.get("left") != ant["formula"]:
                raise CheckError(f"{sid}: antecedent does not match implication")
            known[sid] = {
                "formula": formula["right"],
                "context": imp["context"] | ant["context"],
            }
        else:
            raise CheckError(f"{sid}: unknown rule {rule}")
        stated = step.get("formula")
        if rule != "assume" and stated is not None and stated != known[sid]["formula"]:
            raise CheckError(f"{sid}: stated formula does not match the rule")
        last = known[sid]

    if last is None:
        raise CheckError("empty proof")
    if last["context"]:
        raise CheckError(f"final context is not closed: {sorted(last['context'])}")
    if last["formula"] != goal:
        raise CheckError("final formula does not match goal")
