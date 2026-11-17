# Contributing

1. `python3 -m sparefold join --handle yourname`
2. `python3 -m sparefold claim <id>`
3. Edit only the paths the unit lists.
4. `python3 -m sparefold verify <id>` must exit 0.
5. `python3 -m sparefold submit <id>`
6. Open a pull request with the result file in `ledger/results/`.

Do not edit checkers. CI re-runs them. On a pull request it also diffs checker bytes against the base branch.

If you finish a unit, leave its status as `open` until the checker passes on the PR. A maintainer flips it to `ready` when the result is merged, and adds the next unit. The test `test_open_units_fail_on_a_clean_tree` is the tripwire: an open unit that already passes is a bug.
