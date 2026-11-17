"""Go-to-market harness. The launch post has to pass the same checker a stranger would run."""

from __future__ import annotations

import html
from pathlib import Path

BANNED = (
    "revolutionary",
    "game-changer",
    "game changer",
    "disrupt",
    "guaranteed",
    "10x",
)


def lint_hn(title: str, body: str) -> list[str]:
    issues = []
    if not title.startswith("Show HN: "):
        issues.append("title must start with 'Show HN: '")
    if len(title) > 80:
        issues.append(f"title is {len(title)} characters; maximum is 80")
    if len(title) < 24:
        issues.append("title is too short to say what this is")
    if title.count("!") + body.count("!") > 2:
        issues.append("more than two exclamation marks")
    haystack = f"{title}\n{body}".lower()
    for phrase in BANNED:
        if phrase in haystack:
            issues.append(f"banned hype: {phrase}")
    if "```" not in body:
        issues.append("body needs a fenced command a stranger can run")
    if "python3 -m sparefold demo" not in body and "python -m sparefold demo" not in body:
        issues.append("body must include the demo command")
    if "what this is not" not in body.lower():
        issues.append("body must include a 'What this is not' section")
    if "credential" not in body.lower():
        issues.append("body must say this does not pool credentials")
    if len(body) < 400:
        issues.append("body is too thin for a Show HN post")
    if len(body) > 6000:
        issues.append("body is too long for a Show HN post")
    return issues


def lint_hn_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("Title: "):
        return ["file must start with 'Title: '"]
    first, _, body = text.partition("\n")
    title = first.removeprefix("Title: ").strip()
    return lint_hn(title, body.lstrip("\n"))


def render_html_card(handle: str, points: int, project: str) -> str:
    safe_handle = html.escape(handle, quote=True)
    safe_project = html.escape(project, quote=True)
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>Sparefold {safe_handle}</title></head>\n"
        "<body style=\"margin:0;background:#f4f0e6;color:#1c1915;"
        "font-family:Georgia,serif;padding:48px\">\n"
        "<p style=\"letter-spacing:.14em;font-size:13px\">SPAREFOLD</p>\n"
        f"<h1 style=\"font-weight:500;font-size:64px;margin:8px 0\">{safe_handle}</h1>\n"
        f"<p style=\"font-size:22px\">{points} points on {safe_project}</p>\n"
        "</body></html>\n"
    )
