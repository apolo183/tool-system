from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.worker_adapter.contract import (
    AdapterRequest,
    build_adapter_request_from_worker_request,
    run_adapter_requests,
)


def _no_mutation_violations(label: str, record: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if record.get("execute") is not False:
        reasons.append(f"{label} execute must be false")
    if record.get("calls_external_worker") is not False:
        reasons.append(f"{label} calls_external_worker must be false")
    if record.get("writes_target_repo") is not False:
        reasons.append(f"{label} writes_target_repo must be false")
    if record.get("executes_target_repo_mutation") is not False:
        reasons.append(f"{label} executes_target_repo_mutation must be false")
    if record.get("production_deployment") is not False:
        reasons.append(f"{label} production_deployment must be false")
    return reasons


def _adapter_request_record(request: AdapterRequest) -> dict[str, object]:
    return {
        "adapter_id": request.adapter_id,
        "role": request.role,
        "action": request.action,
        "task_id": request.task_id,
        "input_refs": list(request.input_refs),
        "execute": request.execute,
        "calls_external_worker": request.calls_external_worker,
        "writes_target_repo": request.writes_target_repo,
        "executes_target_repo_mutation": request.executes_target_repo_mutation,
        "production_deployment": request.production_deployment,
    }


def build_adapter_orchestration_record(
    adapter_requests: list[AdapterRequest],
    orchestration_id: str = "worker-adapter-orchestration",
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    request_records = [_adapter_request_record(request) for request in adapter_requests]
    adapter_results = run_adapter_requests(adapter_requests)
    reasons: list[str] = []

    for request in request_records:
        reasons.extend(_no_mutation_violations(f"adapter_request {request['adapter_id']}", request))
    for result in adapter_results:
        reasons.extend(_no_mutation_violations(f"adapter_result {result.get('adapter_id')}", result))
        for reason in result.get("reasons") or []:
            reasons.append(f"adapter_result {result.get('adapter_id')}: {reason}")

    if len(request_records) != len(adapter_results):
        reasons.append("adapter request count must match adapter result count")

    status = "PASS" if not reasons else "BLOCK"
    audit_record = {
        "orchestration_id": orchestration_id,
        "adapter_request_count": len(request_records),
        "adapter_result_count": len(adapter_results),
        "adapter_requests": request_records,
        "adapter_results": adapter_results,
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
    }
    rollback_bundle = {
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "method": "git_revert_or_close_pr_before_merge",
        "reference": rollback_reference,
        "restore_steps": [
            {"step": "close_adapter_orchestration_pr_if_open", "execute": False},
            {"step": "revert_adapter_orchestration_merge_if_merged", "execute": False},
            {"step": "restore_previous_adapter_artifact_if_needed", "execute": False},
        ],
    }

    return {
        "status": status,
        "mode": "tool_system_worker_adapter_orchestration",
        "orchestration_id": orchestration_id,
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "audit_record": audit_record if status == "PASS" else {},
        "rollback_bundle": rollback_bundle if status == "PASS" else {},
        "reasons": reasons,
    }


def build_adapter_orchestration_record_from_worker_requests(
    worker_requests: list[WorkerRequest],
    orchestration_id: str = "worker-adapter-orchestration",
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    adapter_requests = [
        build_adapter_request_from_worker_request(request)
        for request in worker_requests
    ]
    return build_adapter_orchestration_record(
        adapter_requests=adapter_requests,
        orchestration_id=orchestration_id,
        rollback_reference=rollback_reference,
    )


def write_adapter_orchestration_record(
    adapter_requests: list[AdapterRequest],
    audit_path: str | Path,
    orchestration_id: str = "worker-adapter-orchestration",
    rollback_reference: str = "branch commits or pull request reversal",
) -> dict[str, object]:
    record = build_adapter_orchestration_record(
        adapter_requests=adapter_requests,
        orchestration_id=orchestration_id,
        rollback_reference=rollback_reference,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
