# Latest

milestone: M5
result: QLoRA adapter trained on Tesla T4
next: Evaluate the v28 adapter on transfer tasks t17–t24
train: 16/16
transfer: 8/8
held_out_tools: escalate lookup_customer_by_email quote_refund
held_out_leaked_into_train: none
tests: passed
waiting: none
note: data/predictions.jsonl holds t17–t24 only. Gold unchanged. Adapter weights stay on the Kaggle kernel output (v28), not in git.

## QLoRA training (go-ahead: yes)

| field | value |
| --- | --- |
| target | Qwen/Qwen3-1.7B |
| traces | `scripts/export_traces.py` → `data/traces/train.jsonl` (16 rows, gitignored) |
| runner | `python3 notebooks/qlora_qwen3_1_7b.py` |
| this VM | no CUDA; CPU forward/backward OOM (~15 GiB cap) |
| result | v28 adapter written on Kaggle (`adapter_exists` true, 4-bit QLoRA) |
| kaggle | private kernel `slm-toolrouter-qlora-train` v28 `KernelWorkerStatus.COMPLETE` after a GPU queue; v16 had failed with no GPU |
| kaggle_device | Tesla T4. `nvidia-smi -L` showed GPU 0 and GPU 1. torch 2.11.0+cu128 `cuda True`. Training pinned to CUDA device 0: Tesla T4, capability 7.5 |
| kaggle_steps | 24 (`epoch` 12, `train_runtime` 110.1s, `train_loss` 1.974) |
| kaggle_success | true — `KAGGLE_TRAINING_SUMMARY` with `global_step` 24, `train_loss` 1.9737860734264057, quantization 4bit, adapter files present |

## Scores

| split | method | n | exact_match | stagnation | tool_errors | calls |
|-------|--------|---|-------------|------------|-------------|-------|
| train | specification | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| train | keyword baseline | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| transfer | specification | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | blind predictions | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | keyword baseline | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
