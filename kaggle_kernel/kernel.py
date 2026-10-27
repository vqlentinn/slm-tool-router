# Kaggle GPU script — QLoRA on Qwen/Qwen3-1.7B for slm-tool-router train traces.
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/vqlentinn/slm-tool-router.git"
REF = os.environ.get("REPO_REF", "main")
WORKDIR = Path("/kaggle/working/slm-tool-router")
TRAIN_STEPS = os.environ.get("TRAIN_MAX_STEPS", "24")


def run(cmd: str) -> None:
    print(f"+ {cmd}", flush=True)
    subprocess.check_call(cmd, shell=True)


def main() -> None:
    if not Path("/kaggle/working").exists():
        print("Not on Kaggle; this kernel expects a GPU notebook runtime.", file=sys.stderr)
        sys.exit(2)
    run(f"git clone --depth 1 --branch {REF} {REPO} {WORKDIR}")
    os.chdir(WORKDIR)
    run(
        "pip install -q -e '.[dev]' transformers peft datasets accelerate "
        "bitsandbytes trl sentencepiece"
    )
    run("python3 scripts/export_traces.py")
    os.environ["TRAIN_MAX_STEPS"] = TRAIN_STEPS
    os.environ["MAX_SEQ_LENGTH"] = os.environ.get("MAX_SEQ_LENGTH", "1024")
    run("python3 notebooks/qlora_qwen3_1_7b.py")
    out = WORKDIR / "artifacts" / "qwen3-1.7b-qlora-toolrouter" / "adapter"
    summary = {"adapter_dir": str(out), "adapter_exists": out.is_dir()}
    if out.is_dir():
        summary["files"] = sorted(p.name for p in out.iterdir())
    print("KAGGLE_TRAINING_SUMMARY", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
