# Kaggle GPU script — QLoRA on Qwen/Qwen3-1.7B for slm-tool-router train traces.
import base64
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = "https://github.com/vqlentinn/slm-tool-router.git"
REF = os.environ.get("REPO_REF", "main")
WORKDIR = Path("/kaggle/working/slm-tool-router")
SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLE = SCRIPT_DIR / "bundle"
# Replaced at push time by scripts/run_kaggle_training.sh (repo tarball, gzip+base64).
BUNDLE_B64 = ""
TRAIN_STEPS = os.environ.get("TRAIN_MAX_STEPS", "24")
MODEL_DATASET_SLUG = "slm-toolrouter-qwen3-1-7b"


def run(cmd: str) -> None:
    print(f"+ {cmd}", flush=True)
    subprocess.check_call(cmd, shell=True)


def ensure_model_id() -> None:
    local = Path("/kaggle/input") / MODEL_DATASET_SLUG
    if local.is_dir():
        os.environ["MODEL_ID"] = str(local)
        return
    cache = Path("/kaggle/working/hf-qwen3-1.7b")
    if cache.is_dir() and (cache / "config.json").is_file():
        os.environ["MODEL_ID"] = str(cache)
        return
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    from huggingface_hub import snapshot_download

    last_err: Exception | None = None
    for attempt in range(6):
        try:
            snapshot_download(
                "Qwen/Qwen3-1.7B",
                local_dir=str(cache),
                local_dir_use_symlinks=False,
            )
            os.environ["MODEL_ID"] = str(cache)
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"model download attempt {attempt + 1} failed: {exc}", flush=True)
            time.sleep(30)
    raise RuntimeError(f"could not fetch Qwen/Qwen3-1.7B: {last_err}")


def materialize_repo() -> None:
    run(f"mkdir -p {WORKDIR}")
    if BUNDLE_B64:
        raw = base64.b64decode(BUNDLE_B64.encode("ascii"))
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            tf.extractall(WORKDIR)
        return
    if BUNDLE.is_dir():
        run(f"cp -a {BUNDLE}/. {WORKDIR}/")
        return
    run(f"git clone --depth 1 --branch {REF} {REPO} {WORKDIR}")


def main() -> None:
    if not Path("/kaggle/working").exists():
        print("Not on Kaggle; this kernel expects a GPU notebook runtime.", file=sys.stderr)
        sys.exit(2)
    materialize_repo()
    os.chdir(WORKDIR)
    run("pip install -q 'setuptools>=68'")
    run("python3 -m pip uninstall -y torchao || true")
    run("pip install -q huggingface_hub sentencepiece")
    run("pip install -q --no-deps peft datasets accelerate trl || true")
    run("pip install -q bitsandbytes || true")
    run("nvidia-smi -L || echo 'no GPU device'")
    run(
        """python3 - <<'PY'
import subprocess
import sys

import torch

print("torch", torch.__version__, "cuda", torch.cuda.is_available(), flush=True)
if torch.cuda.is_available():
    raise SystemExit(0)
subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "torch",
        "--index-url",
        "https://download.pytorch.org/whl/cu124",
    ]
)
import importlib

torch = importlib.import_module("torch")
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), flush=True)
PY"""
    )
    os.environ["PYTHONPATH"] = str(WORKDIR / "src")
    run("python3 scripts/export_traces.py")
    ensure_model_id()
    os.environ["TRAIN_MAX_STEPS"] = TRAIN_STEPS
    os.environ["MAX_SEQ_LENGTH"] = os.environ.get("MAX_SEQ_LENGTH", "1024")
    proc = subprocess.run(
        ["python3", "notebooks/qlora_qwen3_1_7b.py"],
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout, flush=True)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, flush=True)
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    train_metrics = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                train_metrics = json.loads(line)
            except json.JSONDecodeError:
                pass
    out = WORKDIR / "artifacts" / "qwen3-1.7b-qlora-toolrouter" / "adapter"
    summary = {
        "adapter_dir": str(out),
        "adapter_exists": out.is_dir(),
        **train_metrics,
    }
    if out.is_dir():
        summary["files"] = sorted(p.name for p in out.iterdir())
    print("KAGGLE_TRAINING_SUMMARY", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
