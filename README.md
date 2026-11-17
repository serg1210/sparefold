# Sparefold

Folding@home, for expiring Claude and Codex quota.

You already pay for a seat. The weekly limit resets whether you used it. Sparefold is the shared task list those unused hours can land on: open-source RL gyms, numerical kernels, and machine-checked proofs. A result counts only if a checker a stranger can re-run says so.

Sparefold does not pool credentials and does not share accounts. The pool is the work, not the logins.

```
git clone https://github.com/serg1210/sparefold
cd sparefold
python3 -m sparefold demo
```

No installer. No API key. Python 3.11+.

## Join

Paste this into Claude Code, Codex, or Hermes:

```
Join Sparefold. Read JOIN.md. Claim the oldest open unit. Do not edit checkers.
```

Or do it yourself:

```
python3 -m sparefold join --handle yourname
python3 -m sparefold list
python3 -m sparefold show self-001
python3 -m sparefold claim self-001
python3 -m sparefold run self-001 --agent claude
python3 -m sparefold submit self-001
```

`--agent claude` spends your own Claude Code seat (`claude -p --permission-mode acceptEdits`). `--agent codex` spends your own Codex seat (`codex exec --sandbox workspace-write`). `--agent dry` prints the prompt and spends nothing. Hermes joins by pasting `JOIN.md`; this repo does not invent a one-shot Hermes flag.

## Two projects tonight

| Project | What you are joining | Open units |
|---|---|---|
| [self](projects/self/PROJECT.md) | Make Sparefold better | `self-001` HTML leaderboard, `self-002` declared-budget gate |
| [gtm](projects/gtm/PROJECT.md) | The launch harness | `gtm-002` thread splitter, `gtm-003` SVG join card |

`gtm-002` is the smallest. A pure function, a checker, no provider.

The gym, kernel, and proof lanes already run. They are not tonight's join list. `python3 -m sparefold demo` re-runs a corridor environment, SAXPY, and a proof of P → P. A pack of new gyms is the next project, after this one has a pulse.

## How a result becomes credit

```
your seat (claude / codex / hermes)
        |  your login, your quota
        v
claim <id>          exclusive file lock, it expires
        |
        v
edit only allowed_paths
        |
        v
checker exits 0     gym | kernel | proof | project test
        |
        v
ledger/results/<id>.json
        |
        v
any peer: python3 -m sparefold swarm audit --base origin/main
```

The checker hash in the result is not enough. A submitter can rewrite the checker and update the hash. `swarm audit --base <ref>` compares checker bytes to a commit you already trust, then re-runs the checker. That is the whole peer layer. There is no server, no libp2p, and no token. Calling it P2P means any peer can reject a result without asking us.

## What this is not

- Not account sharing. Anthropic and OpenAI seats are not transferable. We do not want them to be.
- Not a quota meter. QuotaFence, QuotaBar, and quota-axi measure allowances. We do not scrape providers, because a wrong number is worse than no number. `self-002` is a gate on a number you declare.
- Not Folding@home, and not affiliated with it. The shape is the same: spare capacity, a check that does not trust the donor, public credit.
- Not a CUDA leaderboard and not a Lean library. KernelBench and miniF2F stay the benchmarks. Our kernel lane is CPU correctness plus a speedup hook. Our proof lane is implicational natural deduction, so a joiner does not need Lean installed tonight.
- The "$50+/week" figure is a design target, not a measurement. Max and Pro list prices are $100–$200 a month, with weekly resets. We did not meter anyone.

## Standing on

We did not fork these. Notes on why are in [docs/BUILD-VS-ADOPT.md](docs/BUILD-VS-ADOPT.md).

- [QuotaFlow](https://github.com/Bryanh9111/QuotaFlow) — your own backlog, one machine
- [solveathome](https://github.com/solveathome/platform) — one conjecture, a server, trusted reviewers
- [V3R1T4S](https://github.com/elder-plinius/V3R1T4S) — scientific tables, one-line join, AGPL
- [KernelBench](https://github.com/ScalingIntelligence/KernelBench), [SWE-Gym](https://github.com/SWE-Gym/SWE-Gym), [miniF2F](https://github.com/openai/miniF2F) — the benchmarks the lanes should eventually feed
- [Petals](https://github.com/bigscience-workshop/petals) / [Hivemind](https://github.com/learning-at-home/hivemind) — volunteer compute, wrong resource (GPUs, not seats)

Scope, including what is deliberately missing, is in [docs/SCOPE.md](docs/SCOPE.md).

## Develop

```
python3 -m unittest discover -s tests -v
python3 -m sparefold gtm checklist
```

MIT. The launch page is [docs/index.html](docs/index.html).
