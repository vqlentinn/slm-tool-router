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
sed "s/__KAGGLE_USER__/$user/g" "$root/kaggle_kernel/kernel-metadata.json > "$tmp/kernel-metadata.json"
cp "$root/kaggle_kernel/kernel.py" "$tmp/kernel.py"
echo "Pushing kernel ${user}/slm-toolrouter-qlora ..."
kaggle kernels push -p "$tmp"
echo "Polling kernel status (timeout ~45 min) ..."
deadline=$(($(date +%s) + 2700))
while [ "$(date +%s)" -lt "$deadline" ]; do
  status=$(kaggle kernels status "${user}/slm-toolrouter-qlora" 2>/dev/null || true)
  echo "$status"
  case "$status" in
    *complete*) break ;;
    *error*|*cancel*) echo "Kernel failed: $status" >&2; exit 1 ;;
  esac
  sleep 30
done
out="$root/artifacts/kaggle-output"
mkdir -p "$out"
kaggle kernels output "${user}/slm-toolrouter-qlora" -p "$out" || true
grep KAGGLE_TRAINING_SUMMARY "$out"/* 2>/dev/null || true
