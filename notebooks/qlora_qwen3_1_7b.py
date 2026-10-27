# %% [markdown]
# # QLoRA fine-tune for Qwen/Qwen3-1.7B on tool-router traces
#
# Run only after an explicit training go-ahead. Do not commit Hugging Face or
# Colab credentials into the repository. Use the runtime secret store for tokens.
#
# Target checkpoint: `Qwen/Qwen3-1.7B` (Apache-2.0). Train on JSONL episodes
# exported from `data/instructions.jsonl` plus recorded `calls` once blind solve
# traces are frozen.

# %% [markdown]
# ## 0. Environment (free GPU notebook)
#
# ```bash
# pip install -U "transformers>=4.51" "datasets>=3" "peft>=0.15" \
#   "bitsandbytes>=0.45" "accelerate>=1.4" "trl>=0.15" "torch"
# ```

# %% [markdown]
# ## 1. Configuration

# %%
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MODEL_ID = __import__("os").environ.get("MODEL_ID", "Qwen/Qwen3-1.7B")
MAX_SEQ_LENGTH = int(__import__("os").environ.get("MAX_SEQ_LENGTH", "1024"))
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
BATCH_SIZE = 1
GRAD_ACCUM = 8

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS = REPO_ROOT / "data" / "instructions.jsonl"
EXPORT_DIR = REPO_ROOT / "data" / "traces"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "qwen3-1.7b-qlora-toolrouter"


@dataclass(frozen=True)
class TrainSplit:
    name: str
    path: Path


TRAIN_TRACE = TrainSplit("train", EXPORT_DIR / "train.jsonl")


def format_episode(instruction: str, calls: list[dict]) -> str:
    """Chat-style SFT row: instruction then one JSON tool call per line."""
    lines = ["<|user|>", instruction, "<|assistant|>"]
    for call in calls:
        lines.append(f"TOOL {call['tool']} {call['args']}")
    return "\n".join(lines)


# %% [markdown]
# ## 2. Load model in 4-bit (QLoRA)

# %%
def load_model_and_tokenizer():
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    use_cuda = torch.cuda.is_available()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    lora = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    if use_cuda:
        try:
            import bitsandbytes  # noqa: F401
        except ImportError:
            bitsandbytes = None  # type: ignore[assignment]
        if bitsandbytes is not None:
            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                quantization_config=bnb,
                device_map="auto",
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
            return tokenizer, get_peft_model(model, lora)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        return tokenizer, get_peft_model(model, lora)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    return tokenizer, get_peft_model(model, lora)


# %% [markdown]
# ## 3. Dataset from recorded traces

# %%
def build_dataset(tokenizer):
    import json

    from datasets import Dataset

    if not TRAIN_TRACE.path.is_file():
        raise FileNotFoundError(
            f"missing {TRAIN_TRACE.path}; run scripts/export_traces.py first"
        )
    rows = []
    for line in TRAIN_TRACE.path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        text = format_episode(record["instruction"], record["calls"])
        rows.append({"text": text})
    dataset = Dataset.from_list(rows)

    def tokenize(batch):
        encoded = tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
        )
        encoded["labels"] = [row[:] for row in encoded["input_ids"]]
        return encoded

    return dataset.map(tokenize, batched=True, remove_columns=["text"])


# %% [markdown]
# ## 4. Train (not executed in CI)

# %%
def train() -> dict:
    import json
    import os

    import torch
    from datasets import Dataset

    if not TRAIN_TRACE.path.is_file():
        raise FileNotFoundError(
            f"missing {TRAIN_TRACE.path}; run scripts/export_traces.py first"
        )
    tokenizer, model = load_model_and_tokenizer()
    rows = []
    for line in TRAIN_TRACE.path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            rows.append(
                {
                    "text": format_episode(
                        record["instruction"], record["calls"]
                    )
                }
            )
    dataset = Dataset.from_list(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    use_cuda = torch.cuda.is_available()
    if not use_cuda:
        raise RuntimeError(
            "CUDA GPU required for QLoRA training; CPU runs OOM on this checkpoint."
        )
    max_steps = int(os.environ.get("TRAIN_MAX_STEPS", "0"))
    try:
        from trl import SFTConfig, SFTTrainer
    except ImportError:
        from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

        tokenized = build_dataset(tokenizer)
        training_args = TrainingArguments(
            output_dir=str(OUTPUT_DIR),
            num_train_epochs=NUM_EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=LEARNING_RATE,
            logging_steps=1,
            save_strategy="epoch",
            bf16=True,
            max_steps=max_steps if max_steps > 0 else -1,
            report_to="none",
        )
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=tokenizer, mlm=False
            ),
        )
    else:
        sft_args = SFTConfig(
            output_dir=str(OUTPUT_DIR),
            num_train_epochs=NUM_EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=LEARNING_RATE,
            logging_steps=1,
            save_strategy="epoch",
            bf16=True,
            max_seq_length=MAX_SEQ_LENGTH,
            dataset_text_field="text",
            max_steps=max_steps if max_steps > 0 else -1,
            report_to="none",
        )
        trainer = SFTTrainer(
            model=model,
            args=sft_args,
            train_dataset=dataset,
            processing_class=tokenizer,
        )
    result = trainer.train()
    adapter_dir = OUTPUT_DIR / "adapter"
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    import importlib.util

    quant = "4bit" if importlib.util.find_spec("bitsandbytes") else "bf16"
    return {
        "device": "cuda",
        "quantization": quant,
        "global_step": result.global_step,
        "train_loss": result.training_loss,
        "output_dir": str(adapter_dir),
    }


# %% [markdown]
# ## 5. Entry point
#
# Uncomment after go-ahead and trace export:
#
# ```python
# if __name__ == "__main__":
#     train()
# ```

# %%
if __name__ == "__main__":
    import json

    print(json.dumps(train(), indent=2))
