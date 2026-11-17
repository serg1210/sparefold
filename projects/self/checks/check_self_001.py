"""Checker for self-001. Fails until sparefold/export_html.py exists and matches the contract."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


try:
    from sparefold.export_html import render_leaderboard
except Exception as exc:
    fail(f"cannot import render_leaderboard: {exc}")

rows = [
    {"handle": "ada", "points": 2, "units": ["gtm-002"]},
    {"handle": "bev", "points": 5, "units": ["self-001", "self-002"]},
]
try:
    doc = render_leaderboard(rows)
except Exception as exc:
    fail(f"render raised {type(exc).__name__}: {exc}")

if not isinstance(doc, str) or "<html" not in doc.lower() or "<table" not in doc.lower():
    fail("expected an HTML document containing a table")
if "bev" not in doc or "ada" not in doc or "self-001" not in doc or "gtm-002" not in doc:
    fail("missing a handle or unit id")
if doc.find("bev") > doc.find("ada"):
    fail("expected bev (5) before ada (2)")

tied = [
    {"handle": "cara", "points": 3, "units": ["self-001"]},
    {"handle": "bev", "points": 3, "units": ["self-002"]},
]
tied_doc = render_leaderboard(tied)
if tied_doc.find("bev") > tied_doc.find("cara"):
    fail("equal points must sort by handle ascending")

empty = render_leaderboard([])
if "No accepted results" not in empty:
    fail("empty ledger must contain 'No accepted results'")

evil = render_leaderboard(
    [{"handle": "<script>alert(1)</script>", "points": 1, "units": ["<img>"]}]
)
if "<script>" in evil.lower() or "<img>" in evil.lower():
    fail("metacharacters were not escaped")
if "<script" in doc.lower():
    fail("leaderboard must not include a script")

print("PASS")
