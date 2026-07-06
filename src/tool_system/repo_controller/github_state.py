from __future__ import annotations

from typing import Any

from tool_system.repo_controller.audit_log import build_audit_record
from tool_system.repo_controller.controller import evaluate_repo_write


def normalize_pull_request(
    pull_request: dict[str, Any],
    repository_full_name: str | None = None,
) -> dict[str, Any]:
    return {
        "repository": repository_full_name
        or pull_request.get("repository")
        or pull_request.get("repository_full_name"),
        "number": pull_request.get("number"),
        "state": pull_request.get("state"),
        "draft": bool(pull_request.get("draft", False)),
        "mergeable": pull_request.get("mergeable"),
        "head_sha": pull_request.get("head_sha") or pull_request.get("headRefOid"),
        "base": pull_request.get("base") or pull_request.get("baseRefName"),
    }


def normalize_workflow_runs(workflow_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for run in workflow_runs:
        checks.append(
            {
                "name": str(run.get("name") or f"workflow-run-{run.get('id', 'unknown')}"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
            }
        )
    return checks


def normalize_workflow_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for job in jobs:
        checks.append(
            {
                "name": str(job.get("name") or f"workflow-job-{job.get('id', 'unknown')}"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
            }
        )
    return checks


def build_repo_write_input_from_github_state(
    pull_request: dict[str, Any],
    gate_decision: dict[str, Any],
    workflow_runs: list[dict[str, Any]] | None = None,
    workflow_jobs: list[dict[str, Any]] | None = None,
    rollback: dict[str, Any] | None = None,
    merge_method: str = "squash",
    repository_full_name: str | None = None,
    task_manifest: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status_checks = normalize_workflow_jobs(workflow_jobs or [])
    if not status_checks:
        status_checks = normalize_workflow_runs(workflow_runs or [])

    return {
        "pull_request": normalize_pull_request(pull_request, repository_full_name),
        "gate_decision": gate_decision,
        "status_checks": status_checks,
        "merge_method": merge_method,
        "rollback": rollback or {},
        "task_manifest": task_manifest,
        "change_plan": change_plan,
    }


def evaluate_github_state(
    pull_request: dict[str, Any],
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    workflow_runs: list[dict[str, Any]] | None = None,
    workflow_jobs: list[dict[str, Any]] | None = None,
    rollback: dict[str, Any] | None = None,
    merge_method: str = "squash",
    repository_full_name: str | None = None,
    task_manifest: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    repo_write_input = build_repo_write_input_from_github_state(
        pull_request=pull_request,
        gate_decision=gate_decision,
        workflow_runs=workflow_runs,
        workflow_jobs=workflow_jobs,
        rollback=rollback,
        merge_method=merge_method,
        repository_full_name=repository_full_name,
        task_manifest=task_manifest,
        change_plan=change_plan,
    )
    decision = evaluate_repo_write(
        pull_request=repo_write_input["pull_request"],
        gate_decision=repo_write_input["gate_decision"],
        repo_policy=repo_policy,
        status_checks=repo_write_input["status_checks"],
        merge_method=repo_write_input["merge_method"],
        task_manifest=repo_write_input["task_manifest"],
        change_plan=repo_write_input["change_plan"],
    )
    audit_record = build_audit_record(
        pull_request=repo_write_input["pull_request"],
        decision=decision,
        rollback=repo_write_input["rollback"],
    )
    return {
        "decision": decision,
        "audit_record": audit_record,
        "repo_write_input": repo_write_input,
    }
