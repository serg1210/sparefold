# Scope

Decided 17 November 2026. This is the v0.1 cut for a same-day launch, not a roadmap costume.

## The job

Developers on Claude Max / Ultra and ChatGPT Pro leave weekly allowance unused. The allowance resets. Sparefold lets them spend that remainder on open-source artifacts whose checkers do not trust the donor.

The pool is a task list and a set of result files. It is not a pool of seats. Account sharing violates Anthropic's and OpenAI's terms, and it is the wrong product.

## In v0.1

- A work-unit format (JSON, no installer).
- Exclusive claims with expiry. Two processes cannot hold the same unit.
- Submit refuses edits outside `allowed_paths`, and refuses a checker that changed after the claim.
- Three checkers with seed artifacts: gym (Gymnasium-shaped, no Gymnasium install), kernel (numerical agreement plus a speedup hook), proof (implicational natural deduction).
- Two joinable projects: `self`, `gtm`. Four open units whose checkers fail on a clean tree. That failure is tested, so we cannot accidentally ship the answers.
- A worker prompt, plus adapters for `claude -p --permission-mode acceptEdits` and `codex exec --sandbox workspace-write`. Dry-run is the default.
- `swarm audit --base <ref>` so a peer can reject a rewritten checker.
- A GTM harness that lints the Show HN post this repo ships.
- Tests, a demo that exits 0 with no API key, a site, a post.

## Not in v0.1

- No central server. Coordination is git.
- No libp2p. A JSON pack is the exchange format. Adding a DHT does not make the checker more trustworthy.
- No credential collection, no quota scraping, no shared seats.
- No token, no points market, no crypto.
- No CUDA and no KernelBench runner. That benchmark needs a GPU sandbox. Shipping a fake one would be the launch-day lie.
- No Lean or Isabelle requirement. A Lean adapter is a later unit, not a join barrier.
- No automatic Hacker News submission. The post is in `launch/hn-post.md`. A person submits it.
- No measurement of "$50/week". That figure is the design target. List prices for Max and Pro are $100–$200 a month with weekly resets. We did not meter a cohort.

## What "done today" means

A stranger clones the repo, runs `python3 -m sparefold demo`, sees four open units, claims one, and either passes its checker or does not. A second stranger can re-run that checker. Nothing in that loop phones us.

## Next, after a pulse

1. A third project: new Gymnasium-compatible environments, one unit per env, conformance checker already in tree.
2. Optional declared-budget file wired into `claim`, once `self-002` lands.
3. A Lean checker behind the same result format, for people who already have Lean.
4. Only then, a CUDA lane that shells out to KernelBench's evaluator on a machine that has a GPU. We still do not fork KernelBench.
