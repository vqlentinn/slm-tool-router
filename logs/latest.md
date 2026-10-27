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

## Scores

| split | method | n | exact_match | stagnation | tool_errors | calls |
|-------|--------|---|-------------|------------|-------------|-------|
| train | specification | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| train | keyword baseline | 16 | 1.000 | 0.000 | 0.000 | 2.94 |
| transfer | specification | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | blind predictions | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
| transfer | keyword baseline | 8 | 1.000 | 0.000 | 0.000 | 3.38 |
