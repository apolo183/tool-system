from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.repo_controller.live_github_collector import collect_workflow_runs_for_commit, run_gh_json

PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}
FAILING_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required"}


def normalize_commit_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": run.get("id"),
        "name": str(run.get("name") or f"workflow-run-{run.get('id', 'unknown')}"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "head_sha": run.get("head_sha"),
    }


def evaluate_commit_runs(workflow_runs: list[dict[str, Any]]) -> dict[str, object]:
    normalized_runs = [normalize_commit_run(run) for run in workflow_runs]
    if not normalized_runs:
        return {
            "status": "UNAVAILABLE",
            "reasons": ["workflow runs unavailable for commit"],
            "workflow_runs": [],
        }

    reasons: list[str] = []
    pending = False
    saw_passing = False
    for run in normalized_runs:
        name = str(run["name"])
        status = run.get("status")
        conclusion = run.get("conclusion")
        if status != "completed":
            pending = True
            reasons.append(f"{name} status is {status}")
            continue
        if conclusion in PASSING_CONCLUSIONS:
            saw_passing = True
            continue
        if conclusion in FAILING_CONCLUSIONS:
            reasons.append(f"{name} conclusion is {conclusion}")
        else:
            reasons.append(f"{name} conclusion is {conclusion}")

    if any("conclusion" in reason for reason in reasons):
        status_value = "BLOCK"
    elif pending:
        status_value = "PENDING"
    elif saw_passing:
        status_value = "PASS"
    else:
        status_value = "UNAVAILABLE"
        reasons.append("no completed passing workflow run found")

    return {"status": status_value, "reasons": reasons, "workflow_runs": normalized_runs}


def build_main_ci_record(
    repository_full_name: str,
    commit_sha: str,
    evaluation: dict[str, object],
) -> dict[str, object]:
    return {
        "repository_full_name": repository_full_name,
        "commit_sha": commit_sha,
        "status": evaluation["status"],
        "reasons": evaluation["reasons"],
        "workflow_runs": evaluation["workflow_runs"],
    }


def observe_main_ci(
    repository_full_name: str,
    commit_sha: str,
    audit_path: str | Path,
    runner=run_gh_json,
) -> dict[str, object]:
    workflow_runs = collect_workflow_runs_for_commit(
        repository_full_name=repository_full_name,
        commit_sha=commit_sha,
        runner=runner,
    )
    evaluation = evaluate_commit_runs(workflow_runs)
    record = build_main_ci_record(
        repository_full_name=repository_full_name,
        commit_sha=commit_sha,
        evaluation=evaluation,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**evaluation, "audit_path": str(artifact_path)}
