from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.runtime.role_runtime import build_role_runtime_plan_file


def _bool_flag_is_false(record: dict[str, object], key: str) -> bool:
    return record.get(key) is False


def _collect_no_mutation_reasons(prefix: str, records: list[dict[str, object]]) -> list[str]:
    reasons: list[str] = []
    for record in records:
        record_id = record.get("step_id") or record.get("task_id") or "unknown"
        if not _bool_flag_is_false(record, "execute"):
            reasons.append(f"{prefix} {record_id} execute must be false")
        if not _bool_flag_is_false(record, "writes_target_repo"):
            reasons.append(f"{prefix} {record_id} writes_target_repo must be false")
        if not _bool_flag_is_false(record, "executes_target_repo_mutation"):
            reasons.append(f"{prefix} {record_id} executes_target_repo_mutation must be false")
    return reasons


def _role_step_summary(role_steps: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "step_id": step.get("step_id"),
            "task_id": step.get("task_id"),
            "role": step.get("role"),
            "action": step.get("action"),
            "depends_on": list(step.get("depends_on") or []),
            "execute": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
        }
        for step in role_steps
    ]


def _worker_result_summary(worker_results: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "step_id": result.get("step_id"),
            "task_id": result.get("task_id"),
            "role": result.get("role"),
            "action": result.get("action"),
            "status": result.get("status"),
            "worker_kind": result.get("worker_kind"),
            "evidence": list(result.get("evidence") or []),
            "execute": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
        }
        for result in worker_results
    ]


def build_runtime_audit_bundle(
    runtime_plan: dict[str, Any],
    source_refs: list[str] | None = None,
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    role_steps = list(runtime_plan.get("role_steps") or [])
    worker_results = list(runtime_plan.get("worker_results") or [])
    reasons = list(runtime_plan.get("reasons") or [])

    if runtime_plan.get("status") != "PASS":
        reasons.append("passing role runtime plan is required")
    if len(role_steps) != len(worker_results):
        reasons.append("role step count must match worker result count")
    if runtime_plan.get("execute") is not False:
        reasons.append("runtime plan execute must be false")
    if runtime_plan.get("writes_target_repo") is not False:
        reasons.append("runtime plan writes_target_repo must be false")
    if runtime_plan.get("executes_target_repo_mutation") is not False:
        reasons.append("runtime plan executes_target_repo_mutation must be false")

    reasons.extend(_collect_no_mutation_reasons("role_step", role_steps))
    reasons.extend(_collect_no_mutation_reasons("worker_result", worker_results))

    status = "PASS" if not reasons else "BLOCK"
    audit_bundle = {
        "dry_run": True,
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "graph_id": runtime_plan.get("graph_id"),
        "phase": runtime_plan.get("phase"),
        "active_gates_path": runtime_plan.get("active_gates_path"),
        "role_step_count": len(role_steps),
        "worker_result_count": len(worker_results),
        "role_steps": _role_step_summary(role_steps),
        "worker_results": _worker_result_summary(worker_results),
        "source_refs": list(source_refs or []),
    }
    rollback_bundle = {
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "method": "git_revert_or_close_pr_before_merge",
        "reference": rollback_reference,
        "restore_steps": [
            {"step": "close_runtime_pr_if_open", "execute": False},
            {"step": "revert_runtime_merge_if_merged", "execute": False},
            {"step": "restore_previous_runtime_artifact_if_needed", "execute": False},
        ],
    }

    return {
        "status": status,
        "mode": "tool_system_runtime_audit_bundle",
        "graph_id": runtime_plan.get("graph_id"),
        "phase": runtime_plan.get("phase"),
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_role_transition_gate": status == "PASS",
        "ready_for_milestone_review": False,
        "runtime_plan": runtime_plan,
        "audit_bundle": audit_bundle if status == "PASS" else {},
        "rollback_bundle": rollback_bundle if status == "PASS" else {},
        "reasons": reasons,
    }


def build_runtime_audit_bundle_file(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
    active_gates_path: str | Path = "examples/active_gates.yaml",
    audit_path: str | Path | None = None,
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    runtime_plan = build_role_runtime_plan_file(
        graph_path=graph_path,
        blueprint_path=blueprint_path,
        active_gates_path=active_gates_path,
    )
    record = {
        **build_runtime_audit_bundle(
            runtime_plan=runtime_plan,
            source_refs=[str(graph_path), str(blueprint_path), str(active_gates_path)],
            rollback_reference=rollback_reference,
        ),
        "graph_path": str(graph_path),
        "blueprint_path": str(blueprint_path),
        "active_gates_path": str(active_gates_path),
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, record)
        record["audit_path"] = str(artifact_path)
    return record
