from __future__ import annotations

from pathlib import Path

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.worker_adapter.contract import AdapterRequest
from tool_system.worker_adapter.orchestration import (
    build_adapter_orchestration_record,
    build_adapter_orchestration_record_from_worker_requests,
    write_adapter_orchestration_record,
)


def test_adapter_orchestration_record_passes_for_dry_run_requests() -> None:
    result = build_adapter_orchestration_record([
        AdapterRequest(
            adapter_id="adapter-role-step-001",
            role="evidence_collector",
            action="collect_evidence",
        ),
        AdapterRequest(
            adapter_id="adapter-role-step-002",
            role="audit_recorder",
            action="record_audit",
        ),
    ])

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_worker_adapter_orchestration"
    assert result["execute"] is False
    assert result["calls_external_worker"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["production_deployment"] is False
    assert result["audit_record"]["adapter_request_count"] == 2
    assert result["audit_record"]["adapter_result_count"] == 2
    assert result["rollback_bundle"]["execute"] is False
    assert result["reasons"] == []


def test_adapter_orchestration_blocks_mutating_or_external_request() -> None:
    result = build_adapter_orchestration_record([
        AdapterRequest(
            adapter_id="adapter-role-step-003",
            role="patch_author",
            action="prepare_patch_preview",
            execute=True,
            calls_external_worker=True,
            writes_target_repo=True,
            executes_target_repo_mutation=True,
            production_deployment=True,
        )
    ])

    assert result["status"] == "BLOCK"
    assert result["audit_record"] == {}
    assert result["rollback_bundle"] == {}
    assert "adapter_request adapter-role-step-003 execute must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 calls_external_worker must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 writes_target_repo must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 executes_target_repo_mutation must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 production_deployment must be false" in result["reasons"]
    assert "adapter_result adapter-role-step-003: request.execute must be false" in result["reasons"]


def test_adapter_orchestration_from_worker_requests() -> None:
    result = build_adapter_orchestration_record_from_worker_requests([
        WorkerRequest(
            step_id="role-step-004",
            task_id="verify",
            role="test_engineer",
            action="prepare_verification",
        )
    ])

    assert result["status"] == "PASS"
    assert result["audit_record"]["adapter_requests"][0]["adapter_id"] == "adapter-role-step-004"
    assert result["audit_record"]["adapter_results"][0]["adapter_kind"] == "dry_run_worker_adapter"


def test_write_adapter_orchestration_record(tmp_path: Path) -> None:
    result = write_adapter_orchestration_record(
        adapter_requests=[
            AdapterRequest(
                adapter_id="adapter-role-step-005",
                role="audit_recorder",
                action="record_audit",
            )
        ],
        audit_path=tmp_path / "adapter_orchestration.jsonl",
    )

    assert result["status"] == "PASS"
    assert Path(result["audit_path"]).exists()
