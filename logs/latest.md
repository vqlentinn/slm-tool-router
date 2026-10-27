# Latest

milestone: M5
result: report written from log
next: none
train: 16/16
transfer: 8/8
held_out_tools: escalate lookup_customer_by_email quote_refund
held_out_leaked_into_train: none
tests: passed
waiting: none
note: data/predictions.jsonl holds t17–t24 only. Gold unchanged.

## QLoRA training (go-ahead: yes)

| field | value |
| --- | --- |
| target | Qwen/Qwen3-1.7B |
| traces | `scripts/export_traces.py` → `data/traces/train.jsonl` (16 rows, gitignored) |
| runner | `python3 notebooks/qlora_qwen3_1_7b.py` |
| this VM | no CUDA; CPU forward/backward OOM (~15 GiB cap) |
| result | adapter not written here; use free GPU notebook per `notebooks/qlora_qwen3_1_7b.py` |
| kaggle | pushed/ran private kernel `slm-toolrouter-qlora-train` (v15); secrets OK; runner fixes (API token, bundle, T4 `machine_shape`, hf-mirror model fetch) — see [bc-234754e7](https://cursor.com/agents/bc-234754e7-fead-5670-8a8a-6fa17944866f) |
| kaggle_device | **cuda T4 intended** (`NvidiaTeslaT4`); v9 reached bf16 load + hf-mirror download; v13–v15 **no GPU** (`nvidia-smi` missing, `torch 2.11.0+cpu`) — likely weekly GPU quota |
| kaggle_steps | n/a (training loop not reached on last runs) |
| kaggle_success | false — last kernel `KernelWorkerStatus.ERROR` (`RuntimeError`: CUDA required); no `KAGGLE_TRAINING_SUMMARY` in output |

## Scores

| split | method | n | exact_match | stagnation | tool_errors | calls |
|-------|--------|---|-------------|------------|-------------|-------|
| train | specification | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| train | keyword baseline | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| transfer | specification | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | blind predictions | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | keyword baseline | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
