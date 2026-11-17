# Build vs adopt

Read 17 November 2026. The question was which repo to fork and which contract to keep. The answer is: fork none of them. Shell out to the two CLIs people already pay for. Own the work-unit format and the checkers.

## Adopt, by shelling out

| Surface | What we use | What we refuse to reimplement |
|---|---|---|
| Claude Code | `claude -p --permission-mode acceptEdits` | An agent loop, a permission bypass, an API wrapper |
| Codex CLI | `codex exec --sandbox workspace-write` | `--dangerously-bypass-approvals-and-sandbox` |
| Hermes | Paste `JOIN.md` | A one-shot flag we have not confirmed |

QuotaFlow's own notes reached the same conclusion about the CLIs: `claude -p` and `codex exec` already exist. Sparefold agrees, and stops there. The missing piece is not another agent. It is a task a second person can check.

## Do not fork

| Repo | What it actually is | Why it is not the base |
|---|---|---|
| [Bryanh9111/QuotaFlow](https://github.com/Bryanh9111/QuotaFlow) | A local daemon that spends idle Claude quota on *your* backlog, on one machine. Paused. | Complementary. It does not coordinate strangers, and it does not check their output. Close name. We say so in the README. |
| [solveathome/platform](https://github.com/solveathome/platform) | MIT swarm framework. Postgres, Docker, GitHub OAuth, trusted reviewers, one conjecture (twin primes). 8 stars, started September 2026. | The join path is a server. The authority is a reviewer, not a checker. Wrong shape for a same-day launch, and wrong authority for gyms and kernels. Took: public credit, bounded assignments. |
| [elder-plinius/V3R1T4S](https://github.com/elder-plinius/V3R1T4S) | "Turn unused tokens into scientific discoveries." One-line join. Skeptic agents. AGPL. 559 stars, 542 open issues. | Different artifact (table entries, ciphers, bounds), different license, too large to retarget tonight. Took: one-line join, cheap independent check. Credited in the post. |
| [learning-at-home/hivemind](https://github.com/learning-at-home/hivemind) and [bigscience-workshop/petals](https://github.com/bigscience-workshop/petals) | Volunteer GPUs, model-parallel inference and training. The real Folding@home analogue for weights. | Wrong resource. We spend subscription quota, not GPUs. A DHT does not verify a proof. |
| [ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench) | 250 GPU-kernel tasks. Correctness against PyTorch, then speedup. | The benchmark a later kernel lane should feed. Forking it would force a GPU sandbox onto every joiner. v0.1 kernel checker is CPU-only on purpose. |
| [SWE-Gym/SWE-Gym](https://github.com/SWE-Gym/SWE-Gym) | 2.4k real SWE tasks for training agents. | An evaluation set, not a factory for new environments. |
| [openai/miniF2F](https://github.com/openai/miniF2F), [PutnamBench](https://trishullab.github.io/PutnamBench/) | Frozen formal-math benchmarks. | We do not add proofs to a frozen test set. Our proof checker is a small target joiners can hit without Lean. |
| [quotafence/quotafence](https://github.com/quotafence/quotafence), [QuotaBar/QuotaBar](https://github.com/QuotaBar/QuotaBar), [kunchenguid/quota-axi](https://github.com/kunchenguid/quota-axi) | Local quota meters for Claude, Codex, and others. | Measuring is their job. Reading a provider window from inside a worker is how you accidentally build a scraper. `self-002` takes a declared integer instead. |
| [sjgant80-hub/kar-quotafold](https://github.com/sjgant80-hub/kar-quotafold) | An unrelated witness-gated kernel named QuotaFold. 0 stars. | Name collision. We are Sparefold. |

## What we built, because it did not exist in a form we could ship today

- A work-unit file a checker can refuse.
- An exclusive claim with expiry, so two agents do not write the same unit.
- A submit path that hashes the checker at claim time and the tree outside `allowed_paths`.
- `swarm audit --base`, which is the actual answer to "how is this a swarm and not a trust-me JSON file".
- Seed checkers for the three lanes, small enough to run in CI with no GPU and no Lean.
- A launch linter, so the Show HN post is a checked artifact rather than a paragraph we hoped was fine.

## What we would adopt later, unchanged

- Gymnasium's `Env` API, once a gym unit needs to be trained against and not only conformance-checked.
- KernelBench's evaluator, on a GPU box, as a checker command. Not as a dependency of the join path.
- A Lean binary, same way: `checker.command` points at it. The result format does not change.
