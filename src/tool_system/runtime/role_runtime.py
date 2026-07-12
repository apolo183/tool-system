from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.agent_worker.interface import run_role_steps_with_worker
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import validate_task_graph_process_authority
from tool_system.repo_controller.artifact import write_jsonl_record


ROLE_STEP_ACTIONS = {
    "evidence_collector": "collect_evidence",
    "policy_guard": "evaluate_policy",
    "change_planner": "prepare_change_plan",
    "patch_author": "prepare_patch_preview",
    "test_engineer": "prepare_verification",
    "ci_operator": "collect_ci_state",
    "code_reviewer": "review_code",
    "contract_reviewer": "review_contract",
    "repo_controller": "prepare_repo_control",
    "audit_recorder": "record_audit",
    "cleanup_owner": "plan_cleanup",
}


def _role_step(task: dict[str, Any], index: int) -> dict[str, object]:
    role = str(task.get("role"))
    return {
        "step_id": f"role-step-{index + 1:03d}",
        "task_id": task.get("task_id"),
        "role": role,
        "action": ROLE_STEP_ACTIONS.get(role, "record_role_step"),
        "task_manifest": task.get("task_manifest"),
        "change_plan": task.get("change_plan"),
        "depends_on": task.get("depends_on") or [],
        "status": "PASS",
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
    }


def _worker_reasons(worker_results: list[dict[str, object]]) -> list[str]:
    reasons: list[str] = []
    for result in worker_results:
        for reason in result.get("reasons") or []:
            reasons.append(f"{result.get('step_id')}: {reason}")
    return reasons


def build_role_runtime_plan(
    graph: dict[str, Any],
    blueprint: dict[str, Any],
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
) -> dict[str, object]:
    validation = validate_task_graph_process_authority(
        graph,
        blueprint,
        process_authority_path,
    )
    validation_reasons = list(validation.get("reasons") or [])
    role_steps: list[dict[str, object]] = []
    worker_results: list[dict[str, object]] = []

    if validation["status"] == "PASS":
        role_steps = [
            _role_step(task, index)
            for index, task in enumerate(validation.get("execution_plan", []))
        ]
        worker_results = run_role_steps_with_worker(role_steps)

    reasons = validation_reasons + _worker_reasons(worker_results)

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_role_runtime_plan",
        "graph_id": graph.get("graph_id"),
        "phase": graph.get("phase"),
        "process_authority_path": str(process_authority_path),
        "validation": validation,
        "role_steps": role_steps,
        "role_step_count": len(role_steps),
        "worker_results": worker_results,
        "worker_result_count": len(worker_results),
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }


def build_role_runtime_plan_file(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    audit_path: str | Path | None = None,
) -> dict[str, object]:
    graph = load_yaml_file(graph_path)
    blueprint = load_yaml_file(blueprint_path)
    output = {
        **build_role_runtime_plan(graph, blueprint, process_authority_path),
        "graph_path": str(graph_path),
        "blueprint_path": str(blueprint_path),
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output
