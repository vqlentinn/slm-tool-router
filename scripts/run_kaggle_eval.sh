#!/bin/sh
# Push and run greedy QLoRA eval on Kaggle. Adapter is a private dataset.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$root"
. "$root/scripts/kaggle_env.sh"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v kaggle >/dev/null 2>&1; then
  python3 -m pip install -q kaggle
  export PATH="$HOME/.local/bin:$PATH"
fi
user=$(python3 -c "import json; print(json.load(open('$HOME/.kaggle/kaggle.json'))['username'])")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
payload="$tmp/payload"
mkdir -p "$payload/src" "$payload/scripts" "$payload/data"
cp -a "$root/src/toolrouter" "$payload/src/toolrouter"
cp "$root/scripts/eval_adapter.py" "$payload/scripts/eval_adapter.py"
cp "$root/data/instructions.jsonl" "$payload/data/instructions.jsonl"
tar -czf "$tmp/bundle.tar.gz" -C "$payload" .
python3 - "$root/kaggle_kernel/eval.py" "$tmp/eval.py" "$tmp/bundle.tar.gz" <<'PY'
import base64
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text(encoding="utf-8")
out_path = Path(sys.argv[2])
bundle_path = Path(sys.argv[3])
b64 = base64.b64encode(bundle_path.read_bytes()).decode("ascii")
needle = 'BUNDLE_B64 = ""'
if needle not in template:
    raise SystemExit("eval template missing BUNDLE_B64 placeholder")
out_path.write_text(template.replace(needle, f'BUNDLE_B64 = "{b64}"', 1), encoding="utf-8")
PY
python3 - "$root/kaggle_kernel/eval-metadata.json" "$tmp/kernel-metadata.json" "$user" <<'PY'
import json
import sys
from pathlib import Path

src, dst, user = sys.argv[1:4]
meta = json.loads(Path(src).read_text(encoding="utf-8"))
meta["id"] = meta["id"].replace("__KAGGLE_USER__", user)
meta["dataset_sources"] = [
    f"{user}/slm-toolrouter-qwen3-1-7b",
    f"{user}/slm-toolrouter-qlora-adapter-v28",
]
Path(dst).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY
kernel_ref="${user}/slm-toolrouter-qlora-eval"
echo "Pushing kernel ${kernel_ref} ..."
kaggle kernels push -p "$tmp" --accelerator NvidiaTeslaT4
echo "Polling kernel status (timeout ~3 h) ..."
now=$(date +%s)
deadline=$((now + 10800))
status=""
while [ "$(date +%s)" -lt "$deadline" ]; do
  status=$(kaggle kernels status "${kernel_ref}" 2>/dev/null || true)
  echo "$status"
  case "$status" in
    *[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee]*) break ;;
    *[Ee][Rr][Rr][Oo][Rr]*|*[Cc][Aa][Nn][Cc][Ee][Ll]*) echo "Kernel failed: $status" >&2; exit 1 ;;
  esac
  sleep 30
done
case "$status" in
  *[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee]*) ;;
  *) echo "Kernel did not finish: $status" >&2; exit 1 ;;
esac
out="$root/artifacts/kaggle-eval"
mkdir -p "$out"
kaggle kernels output "${kernel_ref}" -p "$out" --file-pattern 'qlora_v28.jsonl' || true
grep EVAL_SUMMARY "$out"/* 2>/dev/null || true
