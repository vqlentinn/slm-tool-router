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
elif [ -n "${KAGGLE_KEY:-}" ]; then
  echo "KAGGLE_KEY is set but KAGGLE_USERNAME is missing." >&2
  echo "Add secret KAGGLE_USERNAME (slug on https://www.kaggle.com/settings ) or replace both with KAGGLE_JSON." >&2
  exit 1
else
  echo "Kaggle API missing: set KAGGLE_USERNAME + KAGGLE_KEY or KAGGLE_JSON in environment secrets." >&2
  exit 1
fi
chmod 600 "$HOME/.kaggle/kaggle.json"
# Kaggle CLI 2.x uses access tokens (KGAT_…) via KAGGLE_API_TOKEN, not legacy key alone.
case "${KAGGLE_KEY:-}" in
  KGAT_*)
    export KAGGLE_API_TOKEN="$KAGGLE_KEY"
    ;;
esac
