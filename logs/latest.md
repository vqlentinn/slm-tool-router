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
| kaggle | **blocked** — env has `KAGGLE_KEY` only; need `KAGGLE_USERNAME`+`KAGGLE_KEY` or `KAGGLE_JSON` (run [bc-698ed86a](https://cursor.com/agents/bc-698ed86a-cd4a-5478-8727-692c1b51f2b0)); kernel not pushed |
| kaggle_device | n/a |
| kaggle_steps | n/a |
| kaggle_success | false (credentials incomplete) |

## Scores

| split | method | n | exact_match | stagnation | tool_errors | calls |
|-------|--------|---|-------------|------------|-------------|-------|
| train | specification | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| train | keyword baseline | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| transfer | specification | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | blind predictions | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | keyword baseline | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
