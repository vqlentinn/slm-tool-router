#!/usr/bin/env python3
"""Export instruction/call traces for SFT from the public task files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from toolrouter.tasks import load_tasks  # noqa: E402


def main() -> int:
    out_dir = ROOT / "data" / "traces"
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    for split in ("train", "transfer"):
        rows = [
            {
                "id": task["id"],
                "instruction": task["instruction"],
                "calls": task["calls"],
            }
            for task in tasks
            if task["split"] == split
        ]
        path = out_dir / f"{split}.jsonl"
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
