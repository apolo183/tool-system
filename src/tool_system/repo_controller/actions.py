from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any

GhRunner = Callable[[list[str]], dict[str, Any]]


class ControllerActionError(RuntimeError):
    """Raised when a controller action cannot be executed."""


def run_gh(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": args,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_action_plan(
    decision: dict[str, Any],
    pull_request: dict[str, Any],
) -> dict[str, object]:
    if decision.get("status") != "PASS":
        return {"status": "BLOCK", "actions": [], "reasons": decision.get("reasons", [])}

    pr_number = pull_request.get("number")
    head_sha = pull_request.get("head_sha")
    if not pr_number:
        return {"status": "BLOCK", "actions": [], "reasons": ["pull request number is required"]}
    if not head_sha:
        return {"status": "BLOCK", "actions": [], "reasons": ["pull request head_sha is required"]}

    actions = []
    if pull_request.get("draft") is True:
        actions.append({"action": "pr_ready", "pr_number": pr_number})
    actions.append(
        {
            "action": "pr_squash",
            "pr_number": pr_number,
            "expected_head_sha": head_sha,
            "merge_method": decision.get("merge_method", "squash"),
        }
    )
    return {"status": "PASS", "actions": actions, "reasons": []}


def _command_for_action(repository_full_name: str, action: dict[str, Any]) -> list[str]:
    action_name = action.get("action")
    pr_number = str(action.get("pr_number"))
    if action_name == "pr_ready":
        return ["pr", "ready", pr_number, "--repo", repository_full_name]
    if action_name == "pr_squash":
        command = ["pr", "merge", pr_number, "--repo", repository_full_name, "--squash"]
        expected_head_sha = action.get("expected_head_sha")
        if expected_head_sha:
            command.extend(["--match-head-commit", str(expected_head_sha)])
        return command
    raise ControllerActionError(f"unsupported controller action: {action_name}")


def execute_action_plan(
    repository_full_name: str,
    plan: dict[str, Any],
    runner: GhRunner = run_gh,
    dry_run: bool = True,
) -> dict[str, object]:
    if plan.get("status") != "PASS":
        return {"status": "BLOCK", "results": [], "reasons": plan.get("reasons", [])}

    results: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        command = _command_for_action(repository_full_name, action)
        if dry_run:
            results.append({"action": action, "command": command, "exit_code": 0, "dry_run": True})
            continue
        result = runner(command)
        result = {"action": action, "command": command, **result, "dry_run": False}
        results.append(result)
        if result.get("exit_code") != 0:
            return {
                "status": "BLOCK",
                "results": results,
                "reasons": [str(result.get("stderr") or result.get("stdout") or "controller action failed")],
            }
    return {"status": "PASS", "results": results, "reasons": []}
