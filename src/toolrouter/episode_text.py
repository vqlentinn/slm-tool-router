"""Text format shared by QLoRA training and adapter evaluation.

A row is the instruction, then one tool call per line. Arguments use the
Python literal produced by ``str(dict)``, which is what training wrote.
"""

from __future__ import annotations

import ast
import json


def format_episode(instruction: str, calls: list[dict]) -> str:
    """Chat-style SFT row: instruction then one tool call per line."""
    lines = ["<|user|>", instruction, "<|assistant|>"]
    for call in calls:
        lines.append(f"TOOL {call['tool']} {call['args']}")
    return "\n".join(lines)


def prompt_for(instruction: str) -> str:
    """Prefix the model completes. Same text as format_episode with no calls, plus the newline before the first TOOL line."""
    return format_episode(instruction, []) + "\n"


def parse_tool_calls(text: str) -> list[dict]:
    """Read TOOL lines from a completion. Stop at the first line that is not a call."""
    calls = []
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if not stripped.startswith("TOOL "):
            if started:
                break
            continue
        started = True
        rest = stripped[len("TOOL ") :]
        tool, sep, args_src = rest.partition(" ")
        args = _parse_args(args_src) if sep else {}
        calls.append({"tool": tool.strip(), "args": args})
    return calls


def _parse_args(src: str) -> dict:
    src = src.strip()
    for loader in (ast.literal_eval, json.loads):
        try:
            value = loader(src)
        except (SyntaxError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return {}
