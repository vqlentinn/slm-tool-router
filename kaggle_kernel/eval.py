# Kaggle GPU script — greedy eval of the QLoRA adapter on public instructions.
import base64
import io
import os
import subprocess
import sys
import tarfile
from pathlib import Path

# Replaced at push time with sources and the public instructions. Weights stay on Kaggle.
BUNDLE_B64 = ""


def materialize() -> Path:
    work = Path("/kaggle/working/eval-bundle")
    work.mkdir(parents=True, exist_ok=True)
    if not BUNDLE_B64:
        raise RuntimeError("eval bundle was not embedded in the kernel")
    raw = base64.b64decode(BUNDLE_B64.encode("ascii"))
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as handle:
        handle.extractall(work, filter="data")
    return work


def run(cmd: str) -> None:
    print(f"+ {cmd}", flush=True)
    subprocess.check_call(cmd, shell=True)


def find_adapter() -> str:
    base = Path("/kaggle/input")
    matches = []
    if base.is_dir():
        for path in base.rglob("adapter_config.json"):
            if "checkpoint-" in path.parts:
                continue
            if path.parent.name != "adapter" and path.name == "adapter_config.json":
                # A dataset may store the two adapter files in its root.
                if (path.parent / "adapter_model.safetensors").is_file():
                    matches.append(path.parent)
                    print(f"adapter candidate {path.parent}", flush=True)
                    continue
            if path.parent.name == "adapter" and (path.parent / "adapter_model.safetensors").is_file():
                matches.append(path.parent)
                print(f"adapter candidate {path.parent}", flush=True)
    preferred = [path for path in matches if "qlora" in str(path)]
    if preferred:
        return str(preferred[0])
    if matches:
        return str(matches[0])
    if base.is_dir():
        for path in sorted(base.rglob("*")):
            if path.is_dir() and len(path.relative_to(base).parts) <= 3:
                print(f"input dir {path}", flush=True)
    raise RuntimeError("adapter not found under /kaggle/input")


def model_id() -> str:
    root = Path("/kaggle/input")
    print(f"kaggle input exists={root.is_dir()}", flush=True)
    if root.is_dir():
        for path in sorted(root.rglob("config.json")):
            parent = path.parent
            if parent.name == "adapter":
                continue
            weights = list(parent.glob("*.safetensors")) + list(parent.glob("*.bin"))
            print(f"found config {path} weights={len(weights)}", flush=True)
            if weights or (parent / "model.safetensors.index.json").is_file():
                return str(parent)
    cache = Path("/kaggle/working/hf-qwen3-1.7b")
    if (cache / "config.json").is_file():
        return str(cache)
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    from huggingface_hub import snapshot_download

    print("mounted dataset not found; downloading Qwen/Qwen3-1.7B", flush=True)
    snapshot_download("Qwen/Qwen3-1.7B", local_dir=str(cache))
    if not (cache / "config.json").is_file():
        raise RuntimeError("could not fetch Qwen/Qwen3-1.7B")
    return str(cache)


def main() -> None:
    if not Path("/kaggle/working").exists():
        print("Not on Kaggle; this kernel expects a GPU notebook runtime.", file=sys.stderr)
        sys.exit(2)
    root = materialize()
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    run("pip install -q huggingface_hub")
    run("pip install -q --no-deps peft || true")
    run("pip install -q bitsandbytes || true")
    run("nvidia-smi -L || echo 'no GPU device'")
    run(
        """python3 - <<'PY'
import sys
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), flush=True)
if not torch.cuda.is_available():
    print("CUDA GPU required to evaluate the adapter", flush=True)
    sys.exit(1)
print("cuda_device", torch.cuda.get_device_name(0), flush=True)
PY"""
    )
    os.environ["PYTHONPATH"] = str(root / "src")
    os.environ["MODEL_ID"] = model_id()
    os.environ["ADAPTER_DIR"] = find_adapter()
    os.environ["INSTRUCTIONS"] = str(root / "data" / "instructions.jsonl")
    os.environ["PREDICTIONS"] = "/kaggle/working/qlora_v28.jsonl"
    os.environ["SPLITS"] = os.environ.get("SPLITS", "transfer")
    os.environ["MAX_NEW_TOKENS"] = os.environ.get("MAX_NEW_TOKENS", "256")
    subprocess.check_call([sys.executable, str(root / "scripts" / "eval_adapter.py")])


if __name__ == "__main__":
    main()
