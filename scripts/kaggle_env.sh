#!/bin/sh
# Build ~/.kaggle/kaggle.json from environment secrets only (never commit).
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
mkdir -p "$HOME/.kaggle"
chmod 700 "$HOME/.kaggle"
if [ -n "${KAGGLE_JSON:-}" ]; then
  printf '%s' "$KAGGLE_JSON" > "$HOME/.kaggle/kaggle.json"
elif [ -n "${KAGGLE_USERNAME:-}" ] && [ -n "${KAGGLE_KEY:-}" ]; then
  KAGGLE_USERNAME="$KAGGLE_USERNAME" KAGGLE_KEY="$KAGGLE_KEY" python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path.home() / ".kaggle" / "kaggle.json"
path.write_text(
    json.dumps(
        {"username": os.environ["KAGGLE_USERNAME"], "key": os.environ["KAGGLE_KEY"]}
    ),
    encoding="utf-8",
)
PY
else
  echo "Kaggle API missing: set KAGGLE_USERNAME + KAGGLE_KEY or KAGGLE_JSON in environment secrets." >&2
  exit 1
fi
chmod 600 "$HOME/.kaggle/kaggle.json"
