"""Checker for gtm-002. Fails until sparefold/gtm/thread.py matches the contract."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


try:
    from sparefold.gtm.thread import split_thread
except Exception as exc:
    fail(f"cannot import split_thread: {exc}")

if split_thread("hello   world") != ["1/1 hello world"]:
    fail("whitespace must collapse and a short text is one post")

words = ["token"] * 80
posts = split_thread(" ".join(words), limit=40)
if not posts:
    fail("expected posts")
if any(len(post) > 40 for post in posts):
    fail("a post exceeded the limit")
count = len(posts)
for index, post in enumerate(posts, start=1):
    if not post.startswith(f"{index}/{count} "):
        fail(f"bad prefix on post {index}: {post!r}")
rebuilt = []
for post in posts:
    rebuilt.extend(post.split(" ", 1)[1].split())
if rebuilt != words:
    fail("joining posts dropped or changed words")

for bad in ("", "   ", "supercalifragilistic", "short " + ("x" * 40)):
    try:
        split_thread(bad, limit=10)
    except ValueError:
        continue
    fail(f"expected ValueError for {bad!r}")

print("PASS")
