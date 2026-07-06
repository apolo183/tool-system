from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.execution_state_snapshot import build_execution_state_snapshot
from tool_system.target_repo.mutation_command_packet import build_mutation_command_packet


def _branch_sha(branches: object, branch_name: object) -> object:
    if not isinstance(branch_name, str):
        return None
    if isinstance(branches, dict):
        value = branches.get(branch_name)
        if isinstance(value, dict):
            return value.get("sha") or value.get("commit_sha")
        if isinstance(value, str):
            return value
    if isinstance(branches, list):
        for item in branches:
            if isinstance(item, dict) and item.get("name") == branch_name:
                return item.get("sha") or item.get("commit_sha")
    return None


def _branch_exists(branches: object, branch_name: object) -> bool:
    if not isinstance(branch_name, str):
        return False
    if isinstance(branches, dict):
        return branch_name in branches
    if isinstance(branches, list):
        return any(isinstance(item, dict) and item.get("name") == branch_name for item in branches)
    return False


def _normalize_file_states(observed: dict[str, Any]) -> dict[str, object]:
    raw = observed.get("file_states") or observed.get("files") or {}
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, object] = {}
    for path, state in raw.items():
        if not isinstance(path, str):
            continue
        if isinstance(state, dict):
            normalized[path] = {
                "exists": bool(state.get("exists")),
                "sha": state.get("sha") or state.get("blob_sha"),
            }
        elif state is None:
            normalized[path] = {"exists": False, "sha": None}
        elif isinstance(state, str):
            normalized[path] = {"exists": True, "sha": state}
    return normalized


def normalize_observed_target_state(
    observed: dict[str, Any],
    command_packet_record: dict[str, object],
) -> dict[str, object]:
    branches = observed.get("branches") or {}
    default_branch = observed.get("default_branch") or "main"
    target_branch = observed.get("target_branch") or command_packet_record.get("target_branch")
    default_branch_head_sha = observed.get("default_branch_head_sha") or _branch_sha(branches, default_branch)
    return {
        "target_repo": observed.get("target_repo") or command_packet_record.get("target_repo"),
        "default_branch": default_branch,
        "default_branch_head_sha": default_branch_head_sha,
        "base_commit_sha": observed.get("base_commit_sha") or default_branch_head_sha,
        "target_branch": target_branch,
        "target_branch_exists": observed.get("target_branch_exists")
        if isinstance(observed.get("target_branch_exists"), bool)
        else _branch_exists(branches, target_branch),
        "file_states": _normalize_file_states(observed),
        "open_prs": observed.get("open_prs") if isinstance(observed.get("open_prs"), list) else [],
        "collected_at": observed.get("collected_at"),
    }


def build_state_collector_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    command_packet = build_mutation_command_packet(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    collector_reasons: list[str] = []
    if not isinstance(observed_state, dict):
        collector_reasons.append("target repository observation is required")
        target_state = None
    else:
        target_state = normalize_observed_target_state(observed_state, command_packet)

    snapshot = build_execution_state_snapshot(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        target_state=target_state,
        change_plan=change_plan,
    )
    reasons = collector_reasons + list(snapshot.get("reasons") or [])
    status = "PASS" if not reasons else "BLOCK"
    return {
        "status": status,
        "mode": "target_repo_state_collector",
        "target_repo": command_packet.get("target_repo"),
        "target_branch": command_packet.get("target_branch"),
        "task_id": command_packet.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "collector_ready": status == "PASS",
        "state_snapshot": snapshot.get("state_snapshot", {}),
        "snapshot_gate": snapshot,
        "collection_contract": {
            "requires_default_branch_head": True,
            "requires_target_branch_status": True,
            "requires_planned_file_states": True,
            "requires_open_pr_snapshot": True,
            "requires_collected_at": True,
        },
        "reasons": reasons,
    }


def run_state_collector_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    record = build_state_collector_record(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        observed_state=observed_state,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
