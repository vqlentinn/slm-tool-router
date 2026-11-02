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
| kaggle | pushed/ran private kernel `slm-toolrouter-qlora-train` (v16); secrets OK (username len 13, key len 37); retry [bc-8b794a29](https://cursor.com/agents/bc-8b794a29-1966-5e65-bb29-a66e5f52046c) after v15 quota/GPU miss |
| kaggle_device | **cuda T4 intended** (`NvidiaTeslaT4`); v16 worker **no GPU** (`nvidia-smi` not found, `torch 2.11.0+cpu`, `cuda False`); v9 had GPU + hf-mirror; v13–v16 same CPU-only worker pattern — likely weekly GPU quota |
| kaggle_steps | n/a (training loop not reached; model weights loaded on CPU then aborted) |
| kaggle_success | false — v16 `KernelWorkerStatus.ERROR` (`RuntimeError`: CUDA GPU required for QLoRA); no `KAGGLE_TRAINING_SUMMARY`; no `train_loss` / `global_step` |

## Scores

| split | method | n | exact_match | stagnation | tool_errors | calls |
|-------|--------|---|-------------|------------|-------------|-------|
| train | specification | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| train | keyword baseline | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| transfer | specification | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | blind predictions | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | keyword baseline | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
