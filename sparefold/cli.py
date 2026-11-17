"""Sparefold command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sparefold import __version__
from sparefold.errors import SparefoldError
from sparefold.gtm import lint_hn_file, render_html_card
from sparefold.ledger import (
    assert_unchanged,
    claim,
    join,
    leaderboard,
    load_claim,
    release,
    require_handle,
    write_result,
)
from sparefold.root import find_root
from sparefold.schema import get_unit, load_work_units
from sparefold.seeds import run_seeds
from sparefold.swarm import accept_pack, audit, write_pack
from sparefold.verify import run_checker
from sparefold.worker import build_prompt, run_agent


def _units(root: Path, project: str | None) -> list[dict]:
    units = load_work_units(root)
    if project:
        units = [unit for unit in units if unit["project"] == project]
    return units


def _print_units(units: list[dict]) -> None:
    if not units:
        print("no work units")
        return
    for unit in units:
        print(
            f"{unit['id']:<10} {unit['status']:<6} {unit['points']}pts"
            f"  {unit['budget_minutes']:>3}m  {unit['title']}"
        )


def cmd_list(args, root: Path) -> int:
    _print_units(_units(root, args.project))
    return 0


def cmd_show(args, root: Path) -> int:
    unit = get_unit(root, args.id)
    print(unit["id"])
    print(unit["title"])
    print(f"project {unit['project']}  lane {unit['lane']}  {unit['status']}  {unit['points']} points")
    print(f"budget {unit['budget_minutes']}m  claim expires after {unit['claim_ttl_minutes']}m")
    print()
    print(unit["summary"])
    print()
    print(unit["spec"].rstrip())
    print()
    print("allowed:")
    for path in unit["allowed_paths"]:
        print(f"  {path}")
    return 0


def cmd_join(args, root: Path) -> int:
    record = join(root, args.handle)
    print(f"joined as {record['handle']}")
    print("This handle is local. It is not an account and it does not touch your Claude or Codex login.")
    return 0


def cmd_claim(args, root: Path) -> int:
    handle = require_handle(root, args.handle)
    record = claim(root, args.id, handle)
    print(f"claimed {record['id']} as {record['handle']} until {record['expires_at']}")
    return 0


def cmd_release(args, root: Path) -> int:
    handle = require_handle(root, args.handle)
    release(root, args.id, handle)
    print(f"released {args.id}")
    return 0


def cmd_verify(args, root: Path) -> int:
    unit = get_unit(root, args.id)
    result = run_checker(root, unit)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.ok:
        print(f"PASS {unit['id']}")
        return 0
    print(f"FAIL {unit['id']}", file=sys.stderr)
    return result.returncode or 1


def cmd_submit(args, root: Path) -> int:
    handle = require_handle(root, args.handle)
    unit = get_unit(root, args.id)
    record = load_claim(root, args.id)
    if record.get("handle") != handle:
        raise SparefoldError(f"{args.id} is claimed by {record.get('handle')}, not {handle}")
    assert_unchanged(root, unit, record)
    result = run_checker(root, unit)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if not result.ok:
        print(f"not submitted: {unit['id']} failed its checker", file=sys.stderr)
        return result.returncode or 1
    written = write_result(root, unit, handle, record["checker_hashes"])
    print(f"accepted {written['id']} for {written['handle']} ({written['points']} points)")
    print("Commit ledger/results and open a pull request. A peer re-runs the checker.")
    return 0


def cmd_leaderboard(args, root: Path) -> int:
    rows = leaderboard(root)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print("No accepted results")
        return 0
    for row in rows:
        units = ", ".join(row["units"])
        print(f"{row['points']:>4}  {row['handle']:<16} {units}")
    return 0


def cmd_prompt(args, root: Path) -> int:
    handle = require_handle(root, args.handle)
    print(build_prompt(get_unit(root, args.id), handle))
    return 0


def cmd_run(args, root: Path) -> int:
    handle = require_handle(root, args.handle)
    return run_agent(root, args.id, args.agent, handle)


def checklist(root: Path) -> list[tuple[str, bool, str]]:
    items: list[tuple[str, bool, str]] = []
    items.append(("LICENSE", (root / "LICENSE").is_file(), ""))
    items.append(("JOIN.md", (root / "JOIN.md").is_file(), ""))
    items.append(("sparefold.toml", (root / "sparefold.toml").is_file(), ""))
    try:
        units = load_work_units(root)
    except SparefoldError as exc:
        return [("work units load", False, str(exc))]
    for project in ("self", "gtm"):
        open_count = sum(1 for unit in units if unit["project"] == project and unit["status"] == "open")
        items.append((f"{project} has an open unit", open_count >= 1, f"{open_count} open"))
    post = root / "launch" / "hn-post.md"
    if not post.is_file():
        items.append(("HN post lints", False, "missing launch/hn-post.md"))
    else:
        issues = lint_hn_file(post)
        items.append(("HN post lints", not issues, "; ".join(issues)))
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    items.append((
        "README refuses credential pooling",
        "does not pool credentials" in readme,
        "",
    ))
    try:
        run_seeds()
        items.append(("seed checkers pass", True, "gym, kernel, proof"))
    except Exception as exc:
        items.append(("seed checkers pass", False, str(exc)))
    site = root / "site" / "index.html"
    site_text = site.read_text(encoding="utf-8") if site.is_file() else ""
    missing = [unit["id"] for unit in units if unit["status"] == "open" and unit["id"] not in site_text]
    items.append(("site lists open units", site.is_file() and not missing, ", ".join(missing)))
    return items


def cmd_checklist(args, root: Path) -> int:
    failed = False
    for name, ok, detail in checklist(root):
        mark = "ok" if ok else "FAIL"
        suffix = f"  {detail}" if detail else ""
        print(f"{mark:<4} {name}{suffix}")
        failed = failed or not ok
    return 1 if failed else 0


def cmd_demo(args, root: Path) -> int:
    print(f"Sparefold {__version__}")
    print("Running seed checkers (gym, kernel, proof)...")
    run_seeds()
    print("seeds passed")
    print()
    print("Open work:")
    _print_units([unit for unit in load_work_units(root) if unit["status"] == "open"])
    print()
    print("Launch checklist:")
    failed = False
    for name, ok, detail in checklist(root):
        mark = "ok" if ok else "FAIL"
        suffix = f"  {detail}" if detail else ""
        print(f"  {mark:<4} {name}{suffix}")
        failed = failed or not ok
    print()
    if failed:
        print("demo failed")
        return 1
    print("demo passed. Join with: python3 -m sparefold join --handle yourname")
    print("Then: python3 -m sparefold claim <id>")
    return 0


def cmd_gtm(args, root: Path) -> int:
    if args.gtm_command == "lint":
        issues = lint_hn_file(root / "launch" / "hn-post.md")
        if issues:
            for issue in issues:
                print(issue)
            return 1
        print("HN post lints")
        return 0
    if args.gtm_command == "card":
        print(render_html_card(args.handle, args.points, args.project))
        return 0
    if args.gtm_command == "checklist":
        return cmd_checklist(args, root)
    print("unknown gtm command")
    return 2


def cmd_swarm(args, root: Path) -> int:
    if args.swarm_command == "audit":
        problems = audit(root, args.base)
        if problems:
            for problem in problems:
                print(problem)
            return 1
        print("audit passed")
        return 0
    if args.swarm_command == "pack":
        dest = Path(args.dest)
        payload = write_pack(root, dest)
        print(f"wrote {len(payload['results'])} result(s) to {dest}")
        return 0
    if args.swarm_command == "accept":
        accepted = accept_pack(root, Path(args.pack), args.base)
        if not accepted:
            print("nothing new to accept")
        else:
            print("accepted " + ", ".join(accepted))
        return 0
    print("unknown swarm command")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sparefold",
        description="Spend spare Claude and Codex quota on machine-checked open source.",
    )
    parser.add_argument("--root", type=Path, help="repo root (default: walk up to sparefold.toml)")
    parser.add_argument("--version", action="version", version=f"sparefold {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="list work units")
    list_cmd.add_argument("--project", choices=("self", "gtm"))
    list_cmd.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="show one work unit")
    show.add_argument("id")
    show.set_defaults(func=cmd_show)

    join_cmd = sub.add_parser("join", help="choose a local handle")
    join_cmd.add_argument("--handle", required=True)
    join_cmd.set_defaults(func=cmd_join)

    claim_cmd = sub.add_parser("claim", help="lock a work unit")
    claim_cmd.add_argument("id")
    claim_cmd.add_argument("--handle")
    claim_cmd.set_defaults(func=cmd_claim)

    release_cmd = sub.add_parser("release", help="drop your claim")
    release_cmd.add_argument("id")
    release_cmd.add_argument("--handle")
    release_cmd.set_defaults(func=cmd_release)

    verify_cmd = sub.add_parser("verify", help="run a work unit checker")
    verify_cmd.add_argument("id")
    verify_cmd.set_defaults(func=cmd_verify)

    submit = sub.add_parser("submit", help="verify, then record a result")
    submit.add_argument("id")
    submit.add_argument("--handle")
    submit.set_defaults(func=cmd_submit)

    board = sub.add_parser("leaderboard", help="points from accepted results")
    board.add_argument("--json", action="store_true")
    board.set_defaults(func=cmd_leaderboard)

    prompt = sub.add_parser("prompt", help="print the agent prompt for a unit")
    prompt.add_argument("id")
    prompt.add_argument("--handle")
    prompt.set_defaults(func=cmd_prompt)

    run = sub.add_parser("run", help="hand a unit to your own agent CLI")
    run.add_argument("id")
    run.add_argument("--agent", choices=("dry", "claude", "codex"), default="dry")
    run.add_argument("--handle")
    run.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo", help="run seeds and the launch checklist")
    demo.set_defaults(func=cmd_demo)

    gtm = sub.add_parser("gtm", help="launch harness")
    gtm_sub = gtm.add_subparsers(dest="gtm_command", required=True)
    gtm_sub.add_parser("lint", help="lint launch/hn-post.md")
    gtm_sub.add_parser("checklist", help="launch checklist")
    card = gtm_sub.add_parser("card", help="print an HTML join card")
    card.add_argument("--handle", required=True)
    card.add_argument("--points", type=int, required=True)
    card.add_argument("--project", required=True)
    gtm.set_defaults(func=cmd_gtm)

    swarm = sub.add_parser("swarm", help="pack and re-check results")
    swarm_sub = swarm.add_subparsers(dest="swarm_command", required=True)
    audit_cmd = swarm_sub.add_parser("audit", help="re-run checkers for every result")
    audit_cmd.add_argument("--base", help="git ref the checker bytes must match")
    pack = swarm_sub.add_parser("pack", help="write a result pack")
    pack.add_argument("dest")
    accept = swarm_sub.add_parser("accept", help="accept a pack after re-checking")
    accept.add_argument("pack")
    accept.add_argument("--base")
    swarm.set_defaults(func=cmd_swarm)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = find_root(args.root) if args.root is None else find_root(args.root)
        if args.root is not None and not (args.root / "sparefold.toml").is_file():
            # find_root walked up. If the user passed a root, require it to be the root.
            raise SparefoldError(f"{args.root} is not a Sparefold repo")
        return args.func(args, root)
    except SparefoldError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
