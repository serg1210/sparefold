"""Sparefold behavior that has to stay true: checkers, claims, and the launch post."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sparefold.checkers import CheckError, check_correct, check_env, check_faster, check_proof
from sparefold.examples.corridor import Corridor, Discrete
from sparefold.examples.saxpy import saxpy
from sparefold.gtm import lint_hn, render_html_card
from sparefold.ledger import ClaimError, SubmitError, claim, join, leaderboard, utcnow
from sparefold.schema import SchemaError, get_unit, load_work_units
from sparefold.seeds import run_seeds
from sparefold.swarm import audit
from sparefold.verify import run_checker
from sparefold.worker import build_command, build_prompt, run_agent


def _unit(tmp: Path, checker: str = "import sys\nraise SystemExit(0)\n") -> None:
    (tmp / "sparefold.toml").write_text('name = "sparefold"\nversion = "0.1.0"\n', encoding="utf-8")
    work = tmp / "projects" / "self" / "work"
    work.mkdir(parents=True)
    (tmp / "ledger" / "results").mkdir(parents=True)
    (tmp / "ledger" / "claims").mkdir(parents=True)
    (tmp / "check.py").write_text(checker, encoding="utf-8")
    (tmp / "README.md").write_text("keep\n", encoding="utf-8")
    payload = {
        "id": "self-900",
        "project": "self",
        "title": "Temporary unit used by the test suite only",
        "summary": "Not a public task.",
        "spec": "Write solution.txt containing hello. The checker exits 0 only if that word is present.",
        "points": 2,
        "budget_minutes": 5,
        "claim_ttl_minutes": 30,
        "lane": "self",
        "status": "open",
        "allowed_paths": ["solution.txt"],
        "checker": {
            "command": [sys.executable, "check.py"],
            "paths": ["check.py"],
            "timeout_s": 15,
        },
    }
    (work / "self-900.json").write_text(json.dumps(payload), encoding="utf-8")


class CheckerTests(unittest.TestCase):
    def test_seeds_pass(self):
        run_seeds()

    def test_bad_action_is_rejected(self):
        class Bad:
            observation_space = Discrete(2)
            action_space = Discrete(2)

            def reset(self, seed=None):
                return 0, {}

            def step(self, action):
                return 0, 0.0, False, False, {}

        with self.assertRaises(CheckError):
            check_env(Bad)

    def test_kernel_mismatch(self):
        def wrong(a, x, y):
            return [0.0 for _ in x]

        with self.assertRaises(CheckError):
            check_correct(saxpy, wrong, [(1.0, [1.0], [1.0])])

    def test_speedup_gate(self):
        def slow(value):
            time.sleep(0.03)
            return value

        ratio = check_faster(slow, lambda value: value, (1,), repeats=3, min_ratio=2.0)
        self.assertGreaterEqual(ratio, 2.0)

    def test_proof_rejects_a_lie(self):
        bad = {
            "goal": {"op": "atom", "name": "Q"},
            "steps": [
                {"id": "a", "rule": "assume", "formula": {"op": "atom", "name": "P"}},
                {"id": "b", "rule": "imply_intro", "from": "a", "discharge": "a"},
            ],
        }
        with self.assertRaises(CheckError):
            check_proof(bad)

    def test_proof_rejects_open_context(self):
        open_proof = {
            "goal": {"op": "atom", "name": "P"},
            "steps": [{"id": "a", "rule": "assume", "formula": {"op": "atom", "name": "P"}}],
        }
        with self.assertRaises(CheckError):
            check_proof(open_proof)


class WorkUnitTests(unittest.TestCase):
    def test_public_units_are_the_two_projects(self):
        units = load_work_units(ROOT)
        ids = [unit["id"] for unit in units]
        self.assertEqual(ids, ["gtm-002", "gtm-003", "self-001", "self-002"])
        self.assertTrue(all(unit["status"] == "open" for unit in units))
        projects = {unit["project"] for unit in units}
        self.assertEqual(projects, {"self", "gtm"})

    def test_open_units_fail_on_a_clean_tree(self):
        for unit in load_work_units(ROOT):
            result = run_checker(ROOT, unit)
            self.assertNotEqual(result.returncode, 0, unit["id"] + result.stdout + result.stderr)

    def test_duplicate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _unit(tmp)
            other = json.loads((tmp / "projects" / "self" / "work" / "self-900.json").read_text())
            other["id"] = "self-900"
            (tmp / "projects" / "self" / "work" / "self-901.json").write_text(json.dumps(other), encoding="utf-8")
            with self.assertRaises(SchemaError):
                load_work_units(tmp)


class ClaimTests(unittest.TestCase):
    def test_second_claim_loses(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _unit(tmp)
            claim(tmp, "self-900", "ada")
            with self.assertRaises(ClaimError):
                claim(tmp, "self-900", "bev")

    def test_expired_claim_can_be_taken(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _unit(tmp)
            claim(tmp, "self-900", "ada", now=utcnow() - timedelta(hours=5))
            taken = claim(tmp, "self-900", "bev")
            self.assertEqual(taken["handle"], "bev")

    def test_submit_accepts_only_allowed_edits(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            checker = (
                "from pathlib import Path\n"
                "import sys\n"
                "text = Path('solution.txt').read_text() if Path('solution.txt').exists() else ''\n"
                "raise SystemExit(0 if 'hello' in text else 1)\n"
            )
            _unit(tmp, checker)
            from sparefold.cli import main

            join(tmp, "ada")
            claim(tmp, "self-900", "ada")
            (tmp / "README.md").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(SubmitError):
                from sparefold.ledger import assert_unchanged, load_claim

                assert_unchanged(tmp, get_unit(tmp, "self-900"), load_claim(tmp, "self-900"))
            (tmp / "README.md").write_text("keep\n", encoding="utf-8")
            (tmp / "solution.txt").write_text("hello\n", encoding="utf-8")
            code = main(["--root", str(tmp), "submit", "self-900"])
            self.assertEqual(code, 0)
            rows = leaderboard(tmp)
            self.assertEqual(rows[0]["handle"], "ada")
            self.assertEqual(rows[0]["points"], 2)

    def test_bad_handle_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _unit(tmp)
            with self.assertRaises(ClaimError):
                claim(tmp, "self-900", "Ada")


class SwarmTests(unittest.TestCase):
    def test_base_ref_catches_a_rewritten_checker(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _unit(tmp, "import sys\nraise SystemExit(0)\n")
            subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=tmp, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "base"],
                cwd=tmp,
                check=True,
                capture_output=True,
            )
            digest_proc = subprocess.run(
                ["git", "hash-object", "check.py"],
                cwd=tmp,
                check=True,
                capture_output=True,
                text=True,
            )
            # sha256, not git hash. Compute the real checker hash after commit.
            from sparefold.hashing import sha256_file

            record = {
                "version": 1,
                "id": "self-900",
                "project": "self",
                "handle": "ada",
                "points": 2,
                "accepted_at": "2026-11-17T00:00:00Z",
                "checker_hashes": {"check.py": sha256_file(tmp / "check.py")},
                "artifact_hashes": {},
            }
            (tmp / "ledger" / "results" / "self-900.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
            self.assertEqual(audit(tmp, base="HEAD"), [])
            (tmp / "check.py").write_text("import sys\nraise SystemExit(0)\n# weakened\n", encoding="utf-8")
            record["checker_hashes"]["check.py"] = sha256_file(tmp / "check.py")
            (tmp / "ledger" / "results" / "self-900.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
            problems = audit(tmp, base="HEAD")
            self.assertTrue(problems, "a rewritten checker must fail against the base ref")
            self.assertTrue(any("differs" in problem for problem in problems))
            del digest_proc


class WorkerTests(unittest.TestCase):
    def test_prompt_forbids_credential_theft_and_checker_edits(self):
        text = build_prompt(get_unit(ROOT, "self-001"), "ada")
        self.assertIn("credential", text.lower())
        self.assertIn("self-001", text)
        self.assertIn("projects/self/checks/check_self_001.py", text)

    def test_claude_adapter_does_not_bypass_permissions(self):
        command = build_command("claude", "do the unit")
        self.assertEqual(command[0], "claude")
        self.assertIn("-p", command)
        self.assertIn("acceptEdits", command)
        self.assertNotIn("bypassPermissions", command)
        self.assertNotIn("--dangerously-skip-permissions", command)

    def test_dry_run_prints_and_does_not_spawn(self):
        def explode(*_args, **_kwargs):
            raise AssertionError("dry-run spawned a process")

        code = run_agent(ROOT, "gtm-002", "dry", "ada", runner=explode)
        self.assertEqual(code, 0)

    def test_missing_binary_does_not_spend_quota(self):
        code = run_agent(ROOT, "gtm-002", "claude", "ada", which=lambda _name: None)
        self.assertEqual(code, 127)


class LaunchTests(unittest.TestCase):
    def test_readme_refuses_credential_pooling(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("does not pool credentials", text)

    def test_hn_post_lints(self):
        from sparefold.gtm import lint_hn_file

        issues = lint_hn_file(ROOT / "launch" / "hn-post.md")
        self.assertEqual(issues, [], issues)

    def test_html_card_escapes(self):
        card = render_html_card("<script>", 1, "self")
        self.assertNotIn("<script>", card)
        self.assertIn("&lt;script&gt;", card)

    def test_lint_rejects_hype(self):
        issues = lint_hn("Show HN: Sparefold - a revolutionary swarm", "x" * 500)
        self.assertTrue(any("hype" in issue for issue in issues))

    def test_demo_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, "-m", "sparefold", "demo"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("seeds passed", proc.stdout)

    def test_list_shows_open_work(self):
        proc = subprocess.run(
            [sys.executable, "-m", "sparefold", "list"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("self-001", proc.stdout)
        self.assertIn("gtm-002", proc.stdout)


if __name__ == "__main__":
    unittest.main()
