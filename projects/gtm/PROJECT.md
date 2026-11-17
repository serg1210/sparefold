# gtm

The launch harness. Not a slogan file. Functions with checkers.

Already in the tree, and tested:

- `sparefold gtm lint` — the Show HN post has to pass this before it is a post
- `sparefold gtm card` — an HTML card
- `sparefold gtm checklist` — license, both projects, seeds, the post, the site

Open units:

- `gtm-002` — split a post into a thread without cutting a word. Smallest unit in the repo. Start here.
- `gtm-003` — a 1200×630 SVG card. Handle, points, project. No script, no external href.

```
python3 -m sparefold show gtm-002
python3 -m sparefold claim gtm-002
```
