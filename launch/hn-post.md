Title: Show HN: Sparefold - spare Claude/Codex quota for checked OSS

Weekly limits reset whether you used them. Sparefold is a git repo that turns the unused part into machine-checked open source. You run Claude Code or Codex on your own seat. You do not share the seat, and Sparefold does not pool credentials.

A work unit is a spec plus a checker. You claim it with an exclusive file lock that expires, edit only the paths it names, and submit. The checker has to exit 0. Anyone else can re-run that checker. If they pass `--base` against the commit they already trust, a rewritten checker does not count. There is no server and no token. The peer layer is a JSON pack plus git.

Tonight there are two projects and four open units:

- self: make Sparefold better. An HTML leaderboard, and a gate that refuses a unit when you declare fewer minutes than it costs. It will not invent a quota number, and it will not scrape a provider.
- gtm: the launch harness. A thread splitter, and a 1200x630 SVG card.

Gym, kernel, and proof checkers already run on seed examples: a corridor environment, SAXPY, and a machine-checked proof of P implies P. Those lanes are what the swarm is for. They are not a CUDA leaderboard and they are not Lean. A pack of new gyms is the next project, after this one has a pulse.

What this is not

- Not account sharing. Your CLI, your login.
- Not a measurement of your quota. Design target is a developer who leaves on the order of $50 of a weekly limit unused. That is a reason to build, not a number we measured.
- Not Folding@home. Same shape of idea: spare capacity, a check that does not trust the donor, public credit. No affiliation.
- Not QuotaFlow, which runs your own backlog on one machine. Not solveathome, which uses a server and trusted reviewers on one conjecture. Not V3R1T4S, which hunts scientific tables under AGPL. The one-line join and the cheap check are theirs. The factory for gyms, kernels, and proofs is the part we are building.

Try it, no API key:

```
git clone https://github.com/serg1210/sparefold
cd sparefold
python3 -m sparefold demo
python3 -m sparefold list
```

Or paste this into Claude Code, Codex, or Hermes:

```
Join Sparefold. Read JOIN.md. Claim the oldest open unit. Do not edit checkers.
```

MIT. Scope and the build-vs-adopt notes are in docs/.
