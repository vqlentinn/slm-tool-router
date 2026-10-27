# SLM tool router

A small open model that picks and sequences tools, scored on a deterministic desk it has not memorized, with an explicit stagnation metric.

The sandbox and the gold tasks live here. Training is a later notebook, started only after an explicit go-ahead.

## Run the checks

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
.venv/bin/python -m toolrouter check
```

`check` replays every gold trajectory and exits non-zero if one fails.

## What is in the box

Seven tools over a fixed world of customers, orders, and two refund policies. A trajectory is an exact match when its tool names and arguments equal the gold sequence. It is stagnant when the same call is repeated immediately, or when a call that already failed is issued again. Success requires an exact match, no stagnation, and no tool error.

Train tasks name the customer. They never call `lookup_customer_by_email`, `quote_refund`, or `escalate`. Transfer tasks do.

Instructions and gold are separate files. `data/instructions.jsonl` has no answers. Blind evaluation uses that file, the catalog, and `python -m toolrouter episode`.

Decisions are in [docs/DECISIONS.md](docs/DECISIONS.md). Progress is [STATUS.md](STATUS.md) and [logs/latest.md](logs/latest.md). Commits use `scripts/commit.sh`, which keeps the author in `config/author`.
