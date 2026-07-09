from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.worker_adapter.orchestration import build_adapter_orchestration_record
from tool_system.worker_adapter.contract import AdapterRequest


REQUIRED_FALSE_FLAGS = [
    "execute",
    "calls_external_worker",
    "writes_target_repo",
    "executes_target_repo_mutation",
    "production_deployment",
]


def _flag_reasons(label: str, record: dict[str, object]) -> list[str]:
    return [
        f"{label} {flag} must be false"
        for flag in REQUIRED_FALSE_FLAGS
        if record.get(flag) is not False
    ]


def _nested_records(record: dict[str, Any]) -> list[tuple[str, dict[str, object]]]:
    nested: list[tuple[str, dict[str, object]]] = []
    audit_record = record.get("audit_record")
    if isinstance(audit_record, dict):
        nested.append(("audit_record", audit_record))
        for request in audit_record.get("adapter_requests") or []:
            if isinstance(request, dict):
                nested.append((f"adapter_request {request.get('adapter_id')}", request))
        for result in audit_record.get("adapter_results") or []:
            if isinstance(result, dict):
                nested.append((f"adapter_result {result.get('adapter_id')}", result))
    rollback_bundle = record.get("rollback_bundle")
    if isinstance(rollback_bundle, dict):
        nested.append(("rollback_bundle", rollback_bundle))
    return nested


def evaluate_adapter_policy_gate(
    orchestration_record: dict[str, Any],
    gate_id: str = "worker-adapter-policy-gate",
) -> dict[str, object]:
    reasons = list(orchestration_record.get("reasons") or [])
    if orchestration_record.get("status") != "PASS":
        reasons.append("passing adapter orchestration record is required")
    if not orchestration_record.get("audit_record"):
        reasons.append("adapter orchestration audit record is required")
    if not orchestration_record.get("rollback_bundle"):
        reasons.append("adapter orchestration rollback bundle is required")

    reasons.extend(_flag_reasons("orchestration_record", orchestration_record))
    for label, record in _nested_records(orchestration_record):
        reasons.extend(_flag_reasons(label, record))

    status = "PASS" if not reasons else "BLOCK"
    return {
        "status": status,
        "mode": "tool_system_worker_adapter_policy_gate",
        "gate_id": gate_id,
        "orchestration_id": orchestration_record.get("orchestration_id"),
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "adapter_policy_gate_passed": status == "PASS",
        "next_required_intervention": "P9_MILESTONE_REVIEW" if status == "PASS" else None,
        "orchestration_record": orchestration_record,
        "reasons": reasons,
    }


def evaluate_adapter_policy_gate_for_requests(
    adapter_requests: list[AdapterRequest],
    gate_id: str = "worker-adapter-policy-gate",
    orchestration_id: str = "worker-adapter-orchestration",
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    orchestration_record = build_adapter_orchestration_record(
        adapter_requests=adapter_requests,
        orchestration_id=orchestration_id,
        rollback_reference=rollback_reference,
    )
    return evaluate_adapter_policy_gate(orchestration_record, gate_id=gate_id)


def write_adapter_policy_gate_record(
    adapter_requests: list[AdapterRequest],
    audit_path: str | Path,
    gate_id: str = "worker-adapter-policy-gate",
    orchestration_id: str = "worker-adapter-orchestration",
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    record = evaluate_adapter_policy_gate_for_requests(
        adapter_requests=adapter_requests,
        gate_id=gate_id,
        orchestration_id=orchestration_id,
        rollback_reference=rollback_reference,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
