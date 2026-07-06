from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.mutation_command_packet import build_mutation_command_packet


REQUIRED_STATE_KEYS = {
    "target_repo",
    "default_branch",
    "default_branch_head_sha",
    "base_commit_sha",
    "target_branch",
    "target_branch_exists",
    "file_states",
    "open_prs",
    "collected_at",
}


def _planned_file_paths(command_packet: dict[str, object]) -> list[str]:
    raw_commands = command_packet.get("commands") or []
    paths: list[str] = []
    if not isinstance(raw_commands, list):
        return paths
    for command in raw_commands:
        if not isinstance(command, dict):
            continue
        if command.get("would_call") == "create_or_update_file" and isinstance(command.get("path"), str):
            paths.append(str(command["path"]))
    return paths


def _has_open_pr_for_branch(open_prs: object, target_branch: object) -> bool:
    if not isinstance(open_prs, list):
        return False
    for pr in open_prs:
        if not isinstance(pr, dict):
            continue
        state = pr.get("state", "open")
        head = pr.get("head") or pr.get("head_branch")
        if state != "closed" and head == target_branch:
            return True
    return False


def _validate_snapshot(snapshot: dict[str, Any], packet: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_STATE_KEYS - set(snapshot))
    if missing:
        reasons.append("missing target repo state keys: " + ", ".join(missing))

    if snapshot.get("target_repo") != packet.get("target_repo"):
        reasons.append("target_repo state must match command packet")
    if snapshot.get("target_branch") != packet.get("target_branch"):
        reasons.append("target_branch state must match command packet")
    if not snapshot.get("default_branch_head_sha"):
        reasons.append("default_branch_head_sha is required")
    if not snapshot.get("base_commit_sha"):
        reasons.append("base_commit_sha is required")
    if snapshot.get("target_branch_exists") is True:
        reasons.append("target branch must not already exist before guarded creation")
    if not isinstance(snapshot.get("open_prs"), list):
        reasons.append("open_prs must be a list")
    elif _has_open_pr_for_branch(snapshot.get("open_prs"), snapshot.get("target_branch")):
        reasons.append("open pull request already exists for target branch")

    file_states = snapshot.get("file_states")
    if not isinstance(file_states, dict):
        reasons.append("file_states must be a mapping")
        return reasons

    for path in _planned_file_paths(dict(packet.get("command_packet") or {})):
        state = file_states.get(path)
        if not isinstance(state, dict):
            reasons.append(f"missing file state for planned path: {path}")
            continue
        if state.get("exists") is True and not state.get("sha"):
            reasons.append(f"sha is required for existing planned path: {path}")
    return reasons


def build_execution_state_snapshot(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    target_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    packet = build_mutation_command_packet(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    reasons = list(packet.get("reasons") or [])
    if packet.get("status") != "PASS":
        reasons.append("passing mutation command packet is required")

    snapshot_reasons: list[str] = []
    if not isinstance(target_state, dict):
        snapshot_reasons.append("fresh target repository state snapshot is required")
        snapshot: dict[str, Any] = {}
    else:
        snapshot = target_state
        snapshot_reasons.extend(_validate_snapshot(snapshot, packet))
    reasons.extend(snapshot_reasons)

    status = "PASS" if not reasons else "BLOCK"
    return {
        "status": status,
        "mode": "target_repo_execution_state_snapshot",
        "target_repo": packet.get("target_repo"),
        "target_branch": packet.get("target_branch"),
        "task_id": packet.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "fresh_state_snapshot_valid": not snapshot_reasons,
        "approved_for_execution_planning": status == "PASS",
        "command_packet": packet.get("command_packet", {}),
        "state_snapshot": snapshot,
        "next_step_contract": {
            "may_execute_target_repo_mutation": False,
            "requires_state_sha_match_before_execution": True,
            "requires_new_explicit_execution_request": True,
            "direct_main_branch_write_allowed": False,
        },
        "reasons": reasons,
    }


def run_execution_state_snapshot(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    target_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    record = build_execution_state_snapshot(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        target_state=target_state,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
