"""Checker for gtm-003. Fails until sparefold/gtm/svgcard.py matches the contract."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


try:
    from sparefold.gtm.svgcard import render_svg_card
except Exception as exc:
    fail(f"cannot import render_svg_card: {exc}")

svg = render_svg_card("ada", 4, "self")
if not isinstance(svg, str) or not svg.lstrip().startswith("<svg"):
    fail("expected an SVG document")
if 'width="1200"' not in svg or 'height="630"' not in svg:
    fail("expected width 1200 and height 630")
if "ada" not in svg or "self" not in svg or "4" not in svg:
    fail("card must show handle, project, and points")
lower = svg.lower()
if "<script" in lower or "href=" in lower:
    fail("card must not include script or href")

evil = render_svg_card("<script>", 1, "self")
if "<script>" in evil.lower():
    fail("handle was not escaped")

print("PASS")
