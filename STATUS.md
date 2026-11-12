# Status

next: none
updated: 2026-11-12
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
- 2026-10-27 — User confirmed relance; Kaggle training delegated to fresh cloud run bc-698ed86a-cd4a-5478-8727-692c1b51f2b0.
- 2026-10-27 — Relance run saw `KAGGLE_KEY` only; training blocked until `KAGGLE_USERNAME` or `KAGGLE_JSON` is added, then `./scripts/run_kaggle_training.sh` again.
- 2026-10-27 — Kaggle relance with both secrets: kernel v15 ERROR (no GPU on worker; CUDA required). Runner hardened; retry when GPU quota available.
- 2026-11-02 — Kaggle retry (bc-8b794a29): secrets OK; kernel v16 pushed, ran ~8 min then ERROR — still no GPU (`nvidia-smi` missing, torch CPU); CUDA required. Retry when T4 quota returns.
- 2026-11-09 — Kaggle QLoRA v28 COMPLETE. Worker saw two Tesla T4s; `nvidia-smi` listed them, torch 2.11.0+cu128 reported cuda True, training used device 0 (sm 7.5, 4-bit). 24 steps, train_loss 1.974, adapter written. Next is the transfer-split evaluation of that adapter.
- 2026-11-12 — QLoRA v28 adapter scored on transfer (Kaggle eval kernel, Tesla T4, greedy decode): exact_match 0.000, stagnation 0.500, tool_errors 6.125, calls 6.62. Predictions in `data/qlora_v28.jsonl`. Experiment complete.
