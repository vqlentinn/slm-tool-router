import os
import shutil
import subprocess
from pathlib import Path

from toolrouter.catalog import BY_NAME, CATALOG
from toolrouter.keyword import keyword_hits, plan
from toolrouter.score import execute, is_stagnant, score_episode
from toolrouter.tasks import HELD_OUT_TOOLS, catalog_ready, load_instructions, load_tasks, tool_sets
from toolrouter.tools import FUNCTIONS, fresh_world

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_matches_dispatcher():
    assert set(FUNCTIONS) == set(BY_NAME) == {spec["name"] for spec in CATALOG}


def test_every_gold_trajectory_succeeds():
    tasks = load_tasks()
    assert {task["split"] for task in tasks} == {"train", "transfer"}
    for task in tasks:
        result = score_episode(task["calls"], task["calls"])
        assert result["success"], (task["id"], result)
        assert result["tool_errors"] == 0


def test_instructions_do_not_carry_gold():
    for row in load_instructions():
        assert "calls" not in row


def test_held_out_tools_stay_out_of_train():
    tasks = load_tasks()
    train_tools, transfer_tools = tool_sets(tasks)
    assert HELD_OUT_TOOLS <= transfer_tools - train_tools
    assert catalog_ready(tasks)


def test_quote_does_not_refund():
    world = fresh_world()
    state, results = execute([{"tool": "quote_refund", "args": {"order_id": "A100"}}], world)
    assert results[0]["ok"] is True
    assert results[0]["amount_eur"] == 40
    assert "refunded" not in state["orders"]["A100"]


def test_commit_hook_rejects_a_foreign_author(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / ".githooks", repo / ".githooks")
    shutil.copytree(ROOT / "config", repo / "config")
    os.chmod(repo / ".githooks" / "commit-msg", 0o755)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "note.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.txt"], cwd=repo, check=True, capture_output=True)
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Someone Else",
            "GIT_AUTHOR_EMAIL": "someone@example.com",
            "GIT_COMMITTER_NAME": "Someone Else",
            "GIT_COMMITTER_EMAIL": "someone@example.com",
        }
    )
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=.githooks", "commit", "-m", "a note"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_wrong_sequence_is_not_exact():
    tasks = load_tasks()
    task = next(item for item in tasks if item["id"] == "t02")
    swapped = list(reversed(task["calls"]))
    result = score_episode(swapped, task["calls"])
    assert result["exact_match"] is False
    assert result["success"] is False


def test_repeated_failure_is_stagnation():
    calls = [
        {"tool": "issue_refund", "args": {"order_id": "B200", "amount_eur": 120}},
        {"tool": "lookup_order", "args": {"order_id": "B200"}},
        {"tool": "issue_refund", "args": {"order_id": "B200", "amount_eur": 120}},
    ]
    _state, results = execute(calls)
    assert results[0]["ok"] is False
    assert is_stagnant(calls, results) is True


def test_immediate_repeat_is_stagnation():
    calls = [
        {"tool": "lookup_order", "args": {"order_id": "A100"}},
        {"tool": "lookup_order", "args": {"order_id": "A100"}},
    ]
    _state, results = execute(calls)
    assert is_stagnant(calls, results) is True


def test_keyword_baseline_scores_all_tasks():
    tasks = load_tasks()
    for task in tasks:
        predicted = plan(task["instruction"])
        result = score_episode(predicted, task["calls"])
        assert result["success"], (task["id"], result)
    assert keyword_hits("lookup order status", "lookup_order") >= 1


def test_refund_mutates_a_copy():
    world = fresh_world()
    execute(
        [{"tool": "issue_refund", "args": {"order_id": "A100", "amount_eur": 40}}],
        world,
    )
    assert world["orders"]["A100"]["refunded"] is True
    assert "refunded" not in fresh_world()["orders"]["A100"]
