"""Episode scoring. Exact tool sequence, plus a stagnation flag."""

from __future__ import annotations

from toolrouter.tools import dispatch, fresh_world


def normalize_call(call: dict) -> tuple:
    tool = call["tool"]
    args = call.get("args") or {}
    items = tuple(sorted((str(key), _norm(value)) for key, value in args.items()))
    return (tool, items)


def _norm(value: object) -> object:
    if isinstance(value, dict):
        return tuple(sorted((str(key), _norm(item)) for key, item in value.items()))
    if isinstance(value, list):
        return tuple(_norm(item) for item in value)
    return value


def execute(calls: list[dict], world: dict | None = None) -> tuple[dict, list[dict]]:
    state = fresh_world() if world is None else world
    results = [dispatch(state, call["tool"], call.get("args")) for call in calls]
    return state, results


def is_stagnant(calls: list[dict], results: list[dict]) -> bool:
    """Same tool and arguments twice in a row, or a failed call issued again later."""
    norms = [normalize_call(call) for call in calls]
    failed: set[tuple] = set()
    for index, signature in enumerate(norms):
        if index > 0 and signature == norms[index - 1]:
            return True
        if results[index].get("ok") is False:
            if signature in failed:
                return True
            failed.add(signature)
    return False


def score_episode(calls: list[dict], gold: list[dict]) -> dict:
    _state, results = execute(calls)
    exact = [normalize_call(call) for call in calls] == [
        normalize_call(call) for call in gold
    ]
    stagnant = is_stagnant(calls, results)
    tool_errors = sum(1 for result in results if not result.get("ok"))
    return {
        "exact_match": exact,
        "stagnant": stagnant,
        "success": exact and not stagnant and tool_errors == 0,
        "n_calls": len(calls),
        "tool_errors": tool_errors,
    }
