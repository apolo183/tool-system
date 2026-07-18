from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.gate.command_runner import run_commands
from tool_system.gate.test_gate import build_gate_decision
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.process_authority.contract import (
    validate_explicit_task_pair,
    validate_process_authority,
)
from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.runner.active_gate_resolver import (
    paths_match,
    resolve_change_plan_from_active_gates,
)


def _status_from_reasons(reasons: list[str]) -> str:
    return "PASS" if not reasons else "BLOCK"


def _resolved_plan_path(
    task_manifest_path: Path,
    change_plan_path: str | Path | None,
    active_gates_path: str | Path | None,
    execute_commands: bool,
) -> tuple[Path | None, str | None, list[str]]:
    if change_plan_path is not None:
        return Path(change_plan_path), "explicit_process_input", []
    if active_gates_path is None:
        return None, None, []
    if execute_commands:
        return None, "legacy_replay_blocked", [
            "legacy active-gate resolution is replay-only and cannot authorize command execution"
        ]
    if not paths_match(active_gates_path, "examples/active_gates.yaml"):
        return None, "legacy_replay_blocked", [
            "legacy replay requires the canonical examples/active_gates.yaml index"
        ]
    resolved = resolve_change_plan_from_active_gates(task_manifest_path, active_gates_path)
    return resolved, "legacy_replay" if resolved is not None else None, []


def run_task_pipeline(
    task_manifest_path: str | Path,
    change_plan_path: str | Path | None = None,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    manifest_path = Path(task_manifest_path)
    plan_path, plan_resolution_source, resolution_reasons = _resolved_plan_path(
        manifest_path,
        change_plan_path,
        active_gates_path,
        execute_commands,
    )
    policy = Path(policy_path)
    autonomy_policy = Path(autonomy_policy_path)
    process_authority = Path(process_authority_path)

    manifest_result = validate_task_manifest(manifest_path, policy, autonomy_policy)
    process_authority_result = validate_process_authority(process_authority)
    plan_result: dict[str, object] | None = None
    pair_binding_result: dict[str, object] | None = None
    protected_execution_result: dict[str, object] | None = None
    command_results: list[dict[str, Any]] = []
    preflight_reasons = list(resolution_reasons)
    if manifest_result["status"] != "PASS":
        preflight_reasons.extend(
            str(reason) for reason in manifest_result.get("reasons", [])
        )
    if process_authority_result["status"] != "PASS":
        preflight_reasons.extend(
            str(reason) for reason in process_authority_result.get("reasons", [])
        )

    if plan_path is not None:
        pair_binding_result = validate_explicit_task_pair(manifest_path, plan_path)
        plan_result = validate_change_plan(plan_path)
        if pair_binding_result["status"] != "PASS":
            preflight_reasons.extend(
                str(reason) for reason in pair_binding_result.get("reasons", [])
            )
        if plan_result["status"] != "PASS":
            preflight_reasons.extend(
                str(reason) for reason in plan_result.get("reasons", [])
            )
    else:
        preflight_reasons.append("change plan is required")

    if execute_commands and not preflight_reasons and plan_path is not None:
        protected_execution_result = run_commands(
            task_manifest_path=manifest_path,
            change_plan_path=plan_path,
            process_authority_path=process_authority,
            policy_path=policy,
            autonomy_policy_path=autonomy_policy,
            cwd=cwd or Path.cwd(),
        )
        command_results = list(
            protected_execution_result.get("command_results") or []
        )
        if protected_execution_result["status"] == "PASS":
            gate_decision = build_gate_decision(
                plan_ok=True,
                plan_reasons=[],
                command_results=command_results,
            )
        else:
            gate_decision = {
                "status": "BLOCK",
                "reasons": list(
                    protected_execution_result.get("reasons") or []
                ),
            }
    else:
        gate_decision = {
            "status": "PASS" if not preflight_reasons else "BLOCK",
            "reasons": preflight_reasons,
        }

    reasons = (
        []
        if gate_decision["status"] == "PASS"
        else [str(reason) for reason in gate_decision.get("reasons", [])]
    )

    output = {
        "status": _status_from_reasons(reasons),
        "mode": "tool_system_task_runner",
        "task_manifest_path": str(manifest_path),
        "change_plan_path": str(plan_path) if plan_path is not None else None,
        "change_plan_resolution_source": plan_resolution_source,
        "process_authority_path": str(process_authority),
        "legacy_active_gates_path": (
            str(active_gates_path) if active_gates_path is not None else None
        ),
        "policy_path": str(policy),
        "autonomy_policy_path": str(autonomy_policy),
        "manifest_result": manifest_result,
        "process_authority_result": process_authority_result,
        "pair_binding_result": pair_binding_result,
        "change_plan_result": plan_result,
        "protected_execution_result": protected_execution_result,
        "gate_decision": gate_decision,
        "command_results": command_results,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output


def _resolve_batch_path(raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    return Path(raw_path)


def run_batch_pipeline(
    batch: dict[str, Any],
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    reasons: list[str] = []
    raw_tasks = batch.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        reasons.append("batch.tasks must be a non-empty list")
        raw_tasks = []

    halt_on_failure = batch.get("halt_on_failure", True) is not False
    task_results: list[dict[str, object]] = []
    for index, entry in enumerate(raw_tasks):
        if not isinstance(entry, dict):
            reasons.append(f"batch task {index} must be a mapping")
            if halt_on_failure:
                break
            continue
        manifest_path = _resolve_batch_path(entry.get("task_manifest"))
        if manifest_path is None:
            reasons.append(f"batch task {index} requires task_manifest")
            if halt_on_failure:
                break
            continue
        plan_path = _resolve_batch_path(entry.get("change_plan"))
        result = run_task_pipeline(
            task_manifest_path=manifest_path,
            change_plan_path=plan_path,
            policy_path=policy_path,
            autonomy_policy_path=autonomy_policy_path,
            process_authority_path=process_authority_path,
            active_gates_path=entry.get("active_gates") or active_gates_path,
            cwd=entry.get("cwd") or cwd,
            execute_commands=execute_commands,
        )
        task_results.append(result)
        if result["status"] != "PASS":
            reasons.append(f"batch task {index} failed")
            reasons.extend(str(reason) for reason in result.get("reasons", []))
            if halt_on_failure:
                break

    output = {
        "status": _status_from_reasons(reasons),
        "mode": "tool_system_batch_runner",
        "task_count": len(raw_tasks),
        "completed_task_count": len(task_results),
        "process_authority_path": str(process_authority_path),
        "legacy_active_gates_path": (
            str(active_gates_path) if active_gates_path is not None else None
        ),
        "task_results": task_results,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output


def run_batch_file(
    batch_path: str | Path,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    batch_file = Path(batch_path)
    batch = load_yaml_file(batch_file)
    output = run_batch_pipeline(
        batch=batch,
        policy_path=policy_path,
        autonomy_policy_path=autonomy_policy_path,
        process_authority_path=process_authority_path,
        active_gates_path=active_gates_path,
        cwd=cwd,
        audit_path=audit_path,
        execute_commands=execute_commands,
    )
    return {**output, "batch_path": str(batch_file)}
