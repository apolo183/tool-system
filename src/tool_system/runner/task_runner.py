from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.gate.command_runner import commands_from_change_plan, run_commands
from tool_system.gate.test_gate import build_gate_decision
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.artifact import write_jsonl_record


def _load_optional_plan(change_plan_path: Path | None) -> dict[str, Any] | None:
    if change_plan_path is None:
        return None
    return load_yaml_file(change_plan_path)


def _status_from_reasons(reasons: list[str]) -> str:
    return "PASS" if not reasons else "BLOCK"


def run_task_pipeline(
    task_manifest_path: str | Path,
    change_plan_path: str | Path | None = None,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    manifest_path = Path(task_manifest_path)
    plan_path = Path(change_plan_path) if change_plan_path is not None else None
    policy = Path(policy_path)
    autonomy_policy = Path(autonomy_policy_path)

    manifest_result = validate_task_manifest(manifest_path, policy, autonomy_policy)
    plan_result: dict[str, object] | None = None
    command_results: list[dict[str, Any]] = []
    gate_decision: dict[str, object] = {"status": "BLOCK", "reasons": ["change plan is required"]}

    if plan_path is not None:
        plan_result = validate_change_plan(plan_path)
        plan = _load_optional_plan(plan_path)
        if execute_commands:
            command_results = run_commands(commands_from_change_plan(plan or {}), cwd=cwd or Path.cwd())
            gate_decision = build_gate_decision(
                plan_ok=plan_result["status"] == "PASS",
                plan_reasons=list(plan_result.get("reasons") or []),
                command_results=command_results,
            )
        else:
            gate_decision = {
                "status": "PASS" if plan_result["status"] == "PASS" else "BLOCK",
                "reasons": list(plan_result.get("reasons") or []),
            }

    reasons: list[str] = []
    if manifest_result["status"] != "PASS":
        reasons.extend(str(reason) for reason in manifest_result.get("reasons", []))
    if gate_decision["status"] != "PASS":
        reasons.extend(str(reason) for reason in gate_decision.get("reasons", []))

    output = {
        "status": _status_from_reasons(reasons),
        "mode": "tool_system_task_runner",
        "task_manifest_path": str(manifest_path),
        "change_plan_path": str(plan_path) if plan_path is not None else None,
        "policy_path": str(policy),
        "autonomy_policy_path": str(autonomy_policy),
        "manifest_result": manifest_result,
        "change_plan_result": plan_result,
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
