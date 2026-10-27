# Status

next: none
updated: 2026-10-27
waiting: none

## Milestones

- [x] M0 — Sandbox and checks.
- [x] M1 — 16 train tasks, 8 transfer tasks, three tools that train never calls.
- [x] M2 — Blind transfer predictions for t17–t24 in data/predictions.jsonl, from the public instructions and the catalog. Score with `python -m toolrouter report`. Leave gold unchanged.
- [x] M3 — Keyword baseline over the catalog, same report, train and transfer separate. One table in logs/latest.md.
- [x] M4 — Notebook that would QLoRA-tune Qwen/Qwen3-1.7B. Do not run it and do not add a credential. Set waiting to training-go-ahead.
- [x] M5 — docs/REPORT.md from the log only. One table: specification vs baseline vs blind predictions, transfer split, exact match, stagnation, calls per task.

## Log

- 2026-10-27 — Catalog gate met. Next is the blind transfer solve.
- 2026-10-27 — Transfer blind solve: exact_match 1.000 on t17–t24. Next is keyword baseline.
- 2026-10-27 — Keyword baseline scored on train and transfer. Next is QLoRA notebook stub.
- 2026-10-27 — QLoRA notebook stub added; waiting for training go-ahead. Report written from the log.
- 2026-10-27 — Training go-ahead granted; traces exported; QLoRA run blocked on this host (no GPU, CPU OOM). Use the notebook on a free GPU runtime.
- 2026-10-27 — Kaggle GPU runner added (`scripts/run_kaggle_training.sh`); API secrets not injected on this agent boot — recheck after secrets reload.
