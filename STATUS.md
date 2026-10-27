# Status

next: M3
updated: 2026-10-27
waiting: none

## Milestones

- [x] M0 — Sandbox and checks.
- [x] M1 — 16 train tasks, 8 transfer tasks, three tools that train never calls.
- [x] M2 — Blind transfer predictions for t17–t24 in data/predictions.jsonl, from the public instructions and the catalog. Score with `python -m toolrouter report`. Leave gold unchanged.
- [ ] M3 — Keyword baseline over the catalog, same report, train and transfer separate. One table in logs/latest.md.
- [ ] M4 — Notebook that would QLoRA-tune Qwen/Qwen3-1.7B. Do not run it and do not add a credential. Set waiting to training-go-ahead.
- [ ] M5 — docs/REPORT.md from the log only. One table: specification vs baseline vs blind predictions, transfer split, exact match, stagnation, calls per task.

## Log

- 2026-10-27 — Catalog gate met. Next is the blind transfer solve.
- 2026-10-27 — Transfer blind solve: exact_match 1.000 on t17–t24. Next is keyword baseline.
