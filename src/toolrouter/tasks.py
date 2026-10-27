"""Join public instructions to gold calls. Instructions never store the answer."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTRUCTIONS_PATH = ROOT / "data" / "instructions.jsonl"
GOLD_PATH = ROOT / "data" / "gold.jsonl"

TRAIN_TARGET = 16
TRANSFER_TARGET = 8
HELD_OUT_TOOLS = frozenset(
    {"lookup_customer_by_email", "quote_refund", "escalate"}
)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def load_instructions(path: Path | None = None) -> list[dict]:
    rows = _read_jsonl(path or INSTRUCTIONS_PATH)
    for row in rows:
        if "calls" in row:
            raise ValueError(f"{row.get('id')}: instructions must not contain calls")
    return rows


def load_tasks(
    instructions_path: Path | None = None,
    gold_path: Path | None = None,
) -> list[dict]:
    instructions = load_instructions(instructions_path)
    gold = {
        row["id"]: row["calls"]
        for row in _read_jsonl(gold_path or GOLD_PATH)
    }
    tasks = []
    for item in instructions:
        if item["id"] not in gold:
            raise KeyError(f"missing gold for {item['id']}")
        tasks.append({**item, "calls": gold[item["id"]]})
    return tasks


def tool_sets(tasks: list[dict]) -> tuple[set[str], set[str]]:
    def names(split: str) -> set[str]:
        return {
            call["tool"]
            for task in tasks
            if task["split"] == split
            for call in task["calls"]
        }

    return names("train"), names("transfer")


def gap_lines(tasks: list[dict]) -> list[str]:
    train = [task for task in tasks if task["split"] == "train"]
    transfer = [task for task in tasks if task["split"] == "transfer"]
    train_tools, transfer_tools = tool_sets(tasks)
    held_out = sorted(HELD_OUT_TOOLS & (transfer_tools - train_tools))
    leaked = sorted(HELD_OUT_TOOLS & train_tools)
    return [
        f"train {len(train)}/{TRAIN_TARGET}",
        f"transfer {len(transfer)}/{TRANSFER_TARGET}",
        f"held_out_tools {len(held_out)}/{len(HELD_OUT_TOOLS)} {' '.join(held_out)}".rstrip(),
        f"held_out_leaked_into_train {' '.join(leaked) if leaked else 'none'}",
    ]


def catalog_ready(tasks: list[dict]) -> bool:
    train = [task for task in tasks if task["split"] == "train"]
    transfer = [task for task in tasks if task["split"] == "transfer"]
    train_tools, transfer_tools = tool_sets(tasks)
    held_out = HELD_OUT_TOOLS & (transfer_tools - train_tools)
    leaked = HELD_OUT_TOOLS & train_tools
    return (
        len(train) >= TRAIN_TARGET
        and len(transfer) >= TRANSFER_TARGET
        and held_out == HELD_OUT_TOOLS
        and not leaked
    )
