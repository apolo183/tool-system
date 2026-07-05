from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from typing import Any

from tool_system.repo_controller.github_state import evaluate_github_state

GhJsonRunner = Callable[[list[str]], Any]


class GitHubCollectorError(RuntimeError):
    """Raised when GitHub state collection fails."""


def run_gh_json(args: list[str]) -> Any:
    completed = subprocess.run(
        ["gh", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise GitHubCollectorError(completed.stderr.strip() or completed.stdout.strip())
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubCollectorError("gh command did not return valid JSON") from exc


def _normal_state(value: Any) -> Any:
    if isinstance(value, str):
        return value.lower()
    return value


def _normal_mergeable(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        upper_value = value.upper()
        if upper_value == "MERGEABLE":
            return True
        if upper_value in {"CONFLICTING", "UNKNOWN"}:
            return False
    return None


def collect_pull_request_state(
    repository_full_name: str,
    pr_number: int,
    runner: GhJsonRunner = run_gh_json,
) -> dict[str, Any]:
    value = runner([
        "pr",
        "view",
        str(pr_number),
        "--repo",
        repository_full_name,
        "--json",
        "number,state,isDraft,mergeable,headRefOid,baseRefName",
    ])
    return {
        "repository": repository_full_name,
        "number": value.get("number"),
        "state": _normal_state(value.get("state")),
        "draft": bool(value.get("isDraft", False)),
        "mergeable": _normal_mergeable(value.get("mergeable")),
        "head_sha": value.get("headRefOid"),
        "base": value.get("baseRefName"),
    }


def collect_workflow_runs_for_commit(
    repository_full_name: str,
    commit_sha: str,
    runner: GhJsonRunner = run_gh_json,
    limit: int = 10,
) -> list[dict[str, Any]]:
    value = runner([
        "run",
        "list",
        "--repo",
        repository_full_name,
        "--commit",
        commit_sha,
        "--limit",
        str(limit),
        "--json",
        "databaseId,name,status,conclusion,headSha",
    ])
    if not isinstance(value, list):
        raise GitHubCollectorError("gh run list JSON root must be a list")
    return [
        {
            "id": run.get("databaseId"),
            "name": run.get("name"),
            "status": _normal_state(run.get("status")),
            "conclusion": _normal_state(run.get("conclusion")),
            "head_sha": run.get("headSha"),
        }
        for run in value
    ]


def collect_github_state_snapshot(
    repository_full_name: str,
    pr_number: int,
    gate_decision: dict[str, Any],
    runner: GhJsonRunner = run_gh_json,
    rollback: dict[str, Any] | None = None,
    merge_method: str = "squash",
) -> dict[str, Any]:
    pull_request = collect_pull_request_state(repository_full_name, pr_number, runner=runner)
    head_sha = pull_request.get("head_sha")
    if not isinstance(head_sha, str) or not head_sha:
        raise GitHubCollectorError("pull request head_sha is required")
    workflow_runs = collect_workflow_runs_for_commit(
        repository_full_name,
        head_sha,
        runner=runner,
    )
    return {
        "repository_full_name": repository_full_name,
        "pull_request": pull_request,
        "gate_decision": gate_decision,
        "workflow_runs": workflow_runs,
        "merge_method": merge_method,
        "rollback": rollback or {"method": "git_revert", "reference": head_sha},
    }


def evaluate_live_pull_request(
    repository_full_name: str,
    pr_number: int,
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    runner: GhJsonRunner = run_gh_json,
    rollback: dict[str, Any] | None = None,
    merge_method: str = "squash",
) -> dict[str, object]:
    snapshot = collect_github_state_snapshot(
        repository_full_name=repository_full_name,
        pr_number=pr_number,
        gate_decision=gate_decision,
        runner=runner,
        rollback=rollback,
        merge_method=merge_method,
    )
    output = evaluate_github_state(
        pull_request=snapshot["pull_request"],
        gate_decision=snapshot["gate_decision"],
        repo_policy=repo_policy,
        workflow_runs=snapshot["workflow_runs"],
        rollback=snapshot["rollback"],
        merge_method=snapshot["merge_method"],
        repository_full_name=snapshot["repository_full_name"],
    )
    return {"snapshot": snapshot, **output}
