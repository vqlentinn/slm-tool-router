#!/usr/bin/env python3
"""Greedy decode of the QLoRA adapter on public instructions. Does not read gold."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from toolrouter.episode_text import parse_tool_calls, prompt_for  # noqa: E402
from toolrouter.tasks import load_instructions  # noqa: E402


def generate_calls(model, tokenizer, instruction: str) -> list[dict]:
    import torch

    prompt = prompt_for(instruction)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=int(os.environ.get("MAX_NEW_TOKENS", "256")),
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = output[0, inputs["input_ids"].shape[1] :]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return parse_tool_calls(text)


def load_model(model_id: str, adapter_dir: str):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required to evaluate the QLoRA adapter.")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    compute = torch.float16
    try:
        import bitsandbytes  # noqa: F401
    except ImportError:
        bitsandbytes = None  # type: ignore[assignment]
    if bitsandbytes is not None:
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute,
            bnb_4bit_use_double_quant=True,
        )
        base = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant,
            device_map="auto",
            trust_remote_code=True,
        )
        quantization = "4bit"
    else:
        base = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=compute,
            device_map="auto",
            trust_remote_code=True,
        )
        quantization = "fp16"
    model = PeftModel.from_pretrained(base, adapter_dir)
    model.eval()
    return tokenizer, model, quantization


def main() -> int:
    import torch

    model_id = os.environ.get("MODEL_ID", "Qwen/Qwen3-1.7B")
    adapter_dir = os.environ["ADAPTER_DIR"]
    instructions_path = Path(
        os.environ.get("INSTRUCTIONS", str(ROOT / "data" / "instructions.jsonl"))
    )
    out_path = Path(os.environ.get("PREDICTIONS", str(ROOT / "data" / "qlora_v28.jsonl")))
    splits = {
        item.strip()
        for item in os.environ.get("SPLITS", "transfer").split(",")
        if item.strip()
    }
    rows = [
        row
        for row in load_instructions(instructions_path)
        if row["split"] in splits
    ]
    if not rows:
        raise SystemExit(f"no instructions for splits {sorted(splits)}")
    tokenizer, model, quantization = load_model(model_id, adapter_dir)
    predictions = []
    for row in rows:
        calls = generate_calls(model, tokenizer, row["instruction"])
        prediction = {"id": row["id"], "calls": calls}
        predictions.append(prediction)
        print(json.dumps(prediction, ensure_ascii=False), flush=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
        encoding="utf-8",
    )
    major, minor = torch.cuda.get_device_capability(0)
    summary = {
        "device": torch.cuda.get_device_name(0),
        "device_capability": f"{major}.{minor}",
        "quantization": quantization,
        "n": len(predictions),
        "splits": sorted(splits),
        "predictions": str(out_path),
        "decoding": "greedy",
    }
    print("EVAL_SUMMARY", json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
