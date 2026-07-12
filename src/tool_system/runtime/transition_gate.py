from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.runtime.audit_bundle import build_runtime_audit_bundle_file


def _flag_is_false(record: dict[str, object], key: str) -> bool:
    return record.get(key) is False


def _require_no_mutation_record(label: str, record: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if not _flag_is_false(record, "execute"):
        reasons.append(f"{label} execute must be false")
    if not _flag_is_false(record, "writes_target_repo"):
        reasons.append(f"{label} writes_target_repo must be false")
    if not _flag_is_false(record, "executes_target_repo_mutation"):
        reasons.append(f"{label} executes_target_repo_mutation must be false")
    return reasons


def build_role_transition_gate(
    runtime_audit_record: dict[str, Any],
    transition_name: str = "p8_runtime_to_milestone_review",
) -> dict[str, object]:
    reasons = list(runtime_audit_record.get("reasons") or [])
    audit_bundle = dict(runtime_audit_record.get("audit_bundle") or {})
    rollback_bundle = dict(runtime_audit_record.get("rollback_bundle") or {})

    if runtime_audit_record.get("status") != "PASS":
        reasons.append("passing runtime audit bundle is required")
    if runtime_audit_record.get("ready_for_role_transition_gate") is not True:
        reasons.append("runtime audit bundle must be ready for role transition gate")
    if not audit_bundle:
        reasons.append("runtime audit bundle payload is required")
    if not rollback_bundle:
        reasons.append("runtime rollback bundle payload is required")

    reasons.extend(_require_no_mutation_record("runtime_audit_record", runtime_audit_record))
    if audit_bundle:
        reasons.extend(_require_no_mutation_record("audit_bundle", audit_bundle))
    if rollback_bundle:
        reasons.extend(_require_no_mutation_record("rollback_bundle", rollback_bundle))

    status = "PASS" if not reasons else "BLOCK"
    return {
        "status": status,
        "mode": "tool_system_role_transition_gate",
        "transition_name": transition_name,
        "graph_id": runtime_audit_record.get("graph_id"),
        "phase": runtime_audit_record.get("phase"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "allows_execution": False,
        "allows_downstream_mutation": False,
        "allows_production_deployment": False,
        "role_transition_gate_passed": status == "PASS",
        "next_required_intervention": "P8_MILESTONE_REVIEW" if status == "PASS" else None,
        "runtime_audit_record": runtime_audit_record,
        "reasons": reasons,
    }


def build_role_transition_gate_file(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    audit_path: str | Path | None = None,
    rollback_reference: str = "branch commits or pull request reversal",
    transition_name: str = "p8_runtime_to_milestone_review",
) -> dict[str, object]:
    runtime_audit_record = build_runtime_audit_bundle_file(
        graph_path=graph_path,
        blueprint_path=blueprint_path,
        process_authority_path=process_authority_path,
        rollback_reference=rollback_reference,
    )
    record = {
        **build_role_transition_gate(runtime_audit_record, transition_name=transition_name),
        "graph_path": str(graph_path),
        "blueprint_path": str(blueprint_path),
        "process_authority_path": str(process_authority_path),
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, record)
        record["audit_path"] = str(artifact_path)
    return record
