#!/bin/sh
# Push and run the GPU training kernel on Kaggle (credentials from env only).
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
KAGGLE_USERNAME="$KAGGLE_USERNAME" KAGGLE_KEY="$KAGGLE_KEY" python3 - "$root/kaggle_kernel/kernel-metadata.json" "$tmp/kernel-metadata.json" "$user" <<'PY'
import json
import sys
from pathlib import Path

src, dst, user = sys.argv[1:4]
meta = json.loads(Path(src).read_text(encoding="utf-8"))
meta["id"] = meta["id"].replace("__KAGGLE_USER__", user)
meta["dataset_sources"] = [f"{user}/slm-toolrouter-qwen3-1-7b"]
Path(dst).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY
mkdir -p "$tmp/bundle"
tar -C "$root" -cf - \
  --exclude=.git \
  --exclude=artifacts \
  --exclude=data/traces \
  --exclude=.venv \
  --exclude=__pycache__ \
  . | tar -C "$tmp/bundle" -xf -
tar -czf "$tmp/bundle.tar.gz" -C "$tmp/bundle" .
KAGGLE_USERNAME="$KAGGLE_USERNAME" KAGGLE_KEY="$KAGGLE_KEY" python3 - "$root/kaggle_kernel/kernel.py" "$tmp/kernel.py" "$tmp/bundle.tar.gz" <<'PY'
import base64
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text(encoding="utf-8")
out_path = Path(sys.argv[2])
bundle_path = Path(sys.argv[3])
b64 = base64.b64encode(bundle_path.read_bytes()).decode("ascii")
needle = 'BUNDLE_B64 = ""'
if needle not in template:
    raise SystemExit("kernel template missing BUNDLE_B64 placeholder")
out_path.write_text(template.replace(needle, f'BUNDLE_B64 = "{b64}"', 1), encoding="utf-8")
PY
kernel_slug=slm-toolrouter-qlora-train
kernel_ref="${user}/${kernel_slug}"
echo "Pushing kernel ${kernel_ref} ..."
kaggle kernels push -p "$tmp" --accelerator NvidiaTeslaT4
echo "Polling kernel status (timeout ~45 min) ..."
now=$(date +%s)
deadline=$((now + 5400))
while [ "$(date +%s)" -lt "$deadline" ]; do
  status=$(kaggle kernels status "${kernel_ref}" 2>/dev/null || true)
  echo "$status"
  case "$status" in
    *complete*) break ;;
    *[Ee][Rr][Rr][Oo][Rr]*|*[Cc][Aa][Nn][Cc][Ee][Ll]*) echo "Kernel failed: $status" >&2; exit 1 ;;
  esac
  sleep 30
done
out="$root/artifacts/kaggle-output"
mkdir -p "$out"
kaggle kernels output "${kernel_ref}" -p "$out" || true
grep KAGGLE_TRAINING_SUMMARY "$out"/* 2>/dev/null || true
