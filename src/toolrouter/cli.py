"""Check gold, print catalog gaps, replay an episode, score a prediction file."""

from __future__ import annotations

import argparse
import json
import sys

from toolrouter.score import execute, score_episode
from toolrouter.tasks import catalog_ready, gap_lines, load_tasks


def check(tasks: list[dict]) -> list[str]:
    problems = []
    for task in tasks:
        result = score_episode(task["calls"], task["calls"])
        if not result["success"]:
            problems.append(f"{task['id']}: gold trajectory is not a success ({result})")
    if not catalog_ready(tasks):
        problems.append("catalog gate is not met")
        problems.extend(gap_lines(tasks))
    return problems


def _print_rates(label: str, results: list[dict]) -> None:
    count = len(results)
    if count == 0:
        print(f"{label} n=0")
        return
    exact = sum(1 for row in results if row["exact_match"]) / count
    stagnant = sum(1 for row in results if row["stagnant"]) / count
    errors = sum(row["tool_errors"] for row in results) / count
    calls = sum(row["n_calls"] for row in results) / count
    print(
        f"{label} n={count} exact_match={exact:.3f} "
        f"stagnation={stagnant:.3f} tool_errors={errors:.3f} calls={calls:.2f}"
    )


def report(tasks: list[dict], predictions: list[dict]) -> int:
    by_id = {task["id"]: task for task in tasks}
    grouped: dict[str, list[dict]] = {"train": [], "transfer": []}
    missing = []
    for task in tasks:
        prediction = next((row for row in predictions if row["id"] == task["id"]), None)
        if prediction is None:
            missing.append(task["id"])
            continue
        grouped[task["split"]].append(score_episode(prediction["calls"], by_id[task["id"]]["calls"]))
    for split in ("train", "transfer"):
        _print_rates(split, grouped[split])
    if missing:
        print("missing " + " ".join(missing), file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="toolrouter")
    parser.add_argument("command", choices=["check", "gaps", "episode", "report"])
    parser.add_argument("path", nargs="?")
    args = parser.parse_args(argv)
    tasks = load_tasks()

    if args.command == "gaps":
        print("\n".join(gap_lines(tasks)))
        print("catalog_ready" if catalog_ready(tasks) else "catalog_short")
        return 0

    if args.command == "check":
        problems = check(tasks)
        print("\n".join(gap_lines(tasks)))
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print("gold trajectories ok")
        return 0

    if args.command == "episode":
        if not args.path:
            print("episode expects a JSON file of calls", file=sys.stderr)
            return 2
        calls = json.loads(open(args.path, encoding="utf-8").read())
        _state, results = execute(calls)
        print(json.dumps(results))
        return 0

    if args.command == "report":
        if not args.path:
            print("report expects a JSONL file of {id, calls}", file=sys.stderr)
            return 2
        predictions = []
        for line in open(args.path, encoding="utf-8"):
            stripped = line.strip()
            if stripped:
                predictions.append(json.loads(stripped))
        return report(tasks, predictions)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
