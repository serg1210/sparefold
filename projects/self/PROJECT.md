# self

Make Sparefold better. This is the dogfood project.

Open units:

- `self-001` — `render_leaderboard(rows) -> str`. Light HTML, escaped, sorted. The public site should not invent a score.
- `self-002` — `admission(remaining_minutes, budget_minutes)`. If you declare fewer minutes than the unit costs, the claim is refused. `None` means undeclared, and undeclared is allowed. Do not scrape Claude or Codex to fill the gap.

Claim before you edit. The checker is the contract. Editing the checker fails submit.

```
python3 -m sparefold join --handle yourname
python3 -m sparefold claim self-001
python3 -m sparefold show self-001
```
