from __future__ import annotations

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.worker_adapter.contract import (
    AdapterRequest,
    DryRunWorkerAdapter,
    build_adapter_request_from_worker_request,
    run_adapter_requests,
)


def test_dry_run_worker_adapter_records_pass_without_execution() -> None:
    request = AdapterRequest(
        adapter_id="adapter-role-step-001",
        role="evidence_collector",
        action="collect_evidence",
    )

    result = DryRunWorkerAdapter().run(request)

    assert result.status == "PASS"
    assert result.adapter_kind == "dry_run_worker_adapter"
    assert result.execute is False
    assert result.calls_external_worker is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production_deployment is False
    assert result.reasons == []
    assert result.output["mode"] == "dry_run_record_only"


def test_dry_run_worker_adapter_blocks_external_and_mutating_requests() -> None:
    request = AdapterRequest(
        adapter_id="adapter-role-step-002",
        role="patch_author",
        action="prepare_patch_preview",
        execute=True,
        calls_external_worker=True,
        writes_target_repo=True,
        executes_target_repo_mutation=True,
        production_deployment=True,
    )

    result = DryRunWorkerAdapter().run(request)

    assert result.status == "BLOCK"
    assert result.execute is False
    assert result.calls_external_worker is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production_deployment is False
    assert result.reasons == [
        "request.execute must be false",
        "request.calls_external_worker must be false",
        "request.writes_target_repo must be false",
        "request.executes_target_repo_mutation must be false",
        "request.production_deployment must be false",
    ]


def test_adapter_request_from_worker_request_preserves_no_mutation_boundary() -> None:
    worker_request = WorkerRequest(
        step_id="role-step-003",
        task_id="verify",
        role="test_engineer",
        action="prepare_verification",
        task_manifest="examples/task_manifests/tool_system_role_runtime.yaml",
        change_plan="examples/change_plans/tool_system_role_runtime.yaml",
    )

    adapter_request = build_adapter_request_from_worker_request(worker_request)

    assert adapter_request.adapter_id == "adapter-role-step-003"
    assert adapter_request.role == "test_engineer"
    assert adapter_request.action == "prepare_verification"
    assert adapter_request.input_refs == [
        "examples/task_manifests/tool_system_role_runtime.yaml",
        "examples/change_plans/tool_system_role_runtime.yaml",
    ]
    assert adapter_request.execute is False
    assert adapter_request.calls_external_worker is False
    assert adapter_request.writes_target_repo is False
    assert adapter_request.executes_target_repo_mutation is False
    assert adapter_request.production_deployment is False


def test_run_adapter_requests_uses_dry_run_adapter_by_default() -> None:
    records = run_adapter_requests([
        AdapterRequest(
            adapter_id="adapter-role-step-004",
            role="audit_recorder",
            action="record_audit",
        )
    ])

    assert records == [
        {
            "adapter_id": "adapter-role-step-004",
            "role": "audit_recorder",
            "action": "record_audit",
            "status": "PASS",
            "adapter_kind": "dry_run_worker_adapter",
            "execute": False,
            "calls_external_worker": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
            "production_deployment": False,
            "evidence": [
                "worker_adapter_contract.no_mutation_dry_run",
                "role=audit_recorder",
                "action=record_audit",
            ],
            "reasons": [],
            "output": {
                "mode": "dry_run_record_only",
                "requested_execute": False,
                "requested_calls_external_worker": False,
                "requested_writes_target_repo": False,
                "requested_executes_target_repo_mutation": False,
                "requested_production_deployment": False,
            },
        }
    ]
