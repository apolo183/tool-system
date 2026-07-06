from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.execution_approval import build_execution_approval_gate


def _commands_from_steps(steps: list[object]) -> list[dict[str, object]]:
    commands: list[dict[str, object]] = []
    for index, raw_step in enumerate(steps, start=1):
        if not isinstance(raw_step, dict):
            continue
        step = str(raw_step.get("step") or "unknown")
        command = {
            "index": index,
            "step": step,
            "repository_full_name": raw_step.get("repository_full_name"),
            "dry_run": True,
            "execute": False,
        }
        if step == "branch_preview":
            command["would_call"] = "create_branch"
            command["branch_name"] = raw_step.get("branch_name")
            command["base_ref"] = raw_step.get("base_ref")
        elif step == "file_change_preview":
            command["would_call"] = "create_or_update_file"
            command["path"] = raw_step.get("path")
            command["operation"] = raw_step.get("operation")
        elif step == "pull_request_preview":
            command["would_call"] = "create_pull_request"
            command["head"] = raw_step.get("head")
            command["base"] = raw_step.get("base")
            command["title"] = raw_step.get("title")
        else:
            command["would_call"] = "manual_review"
        commands.append(command)
    return commands


def build_mutation_command_packet(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    gate = build_execution_approval_gate(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    reasons = list(gate.get("reasons") or [])
    approved = gate.get("status") == "PASS" and bool(gate.get("approved_for_next_step"))
    write_packet = dict(gate.get("write_packet") or {})
    action_steps = list(write_packet.get("action_steps") or [])
    commands = _commands_from_steps(action_steps) if approved else []

    return {
        "status": "PASS" if approved else "BLOCK",
        "mode": "target_repo_mutation_command_packet_preview",
        "target_repo": gate.get("target_repo"),
        "target_branch": gate.get("target_branch"),
        "task_id": gate.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "approved_for_next_step": approved,
        "command_packet": {
            "dry_run": True,
            "execute": False,
            "commands": commands,
        },
        "next_step_contract": {
            "may_execute_target_repo_mutation": False,
            "requires_fresh_state_before_execution": True,
            "requires_new_explicit_execution_request": True,
            "direct_main_branch_write_allowed": False,
        },
        "reasons": reasons,
    }


def run_mutation_command_packet(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    packet = build_mutation_command_packet(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, packet)
    return {**packet, "audit_path": str(artifact_path)}
