"""Checker for self-002. Fails until sparefold/budget.py matches the contract."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


try:
    from sparefold.budget import admission, load_remaining
except Exception as exc:
    fail(f"cannot import budget: {exc}")

if admission(None, 25) is not True:
    fail("undeclared remaining minutes must be allowed")
if admission(25, 25) is not True or admission(24, 25) is not False:
    fail("admission must compare remaining >= budget")

for args in ((-1, 25), (10, 0), (10, -3)):
    try:
        admission(*args)
    except ValueError:
        continue
    fail(f"expected ValueError for {args}")

missing = Path(tempfile.mkdtemp()) / "budget.json"
if load_remaining(missing) is not None:
    fail("missing file must return None")

missing.write_text(json.dumps({"remaining_minutes": 12}), encoding="utf-8")
if load_remaining(missing) != 12:
    fail("expected to read remaining_minutes")

missing.write_text("{}", encoding="utf-8")
try:
    load_remaining(missing)
except ValueError:
    pass
else:
    fail("a JSON object without remaining_minutes must raise ValueError")

print("PASS")
