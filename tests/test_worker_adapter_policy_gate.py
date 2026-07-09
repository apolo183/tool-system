from __future__ import annotations

from pathlib import Path

from tool_system.worker_adapter.contract import AdapterRequest
from tool_system.worker_adapter.orchestration import build_adapter_orchestration_record
from tool_system.worker_adapter.policy_gate import (
    evaluate_adapter_policy_gate,
    evaluate_adapter_policy_gate_for_requests,
    write_adapter_policy_gate_record,
)


def test_adapter_policy_gate_passes_for_no_mutation_orchestration() -> None:
    orchestration = build_adapter_orchestration_record([
        AdapterRequest(
            adapter_id="adapter-role-step-001",
            role="evidence_collector",
            action="collect_evidence",
        )
    ])

    result = evaluate_adapter_policy_gate(orchestration)

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_worker_adapter_policy_gate"
    assert result["execute"] is False
    assert result["calls_external_worker"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["production_deployment"] is False
    assert result["adapter_policy_gate_passed"] is True
    assert result["next_required_intervention"] == "P9_MILESTONE_REVIEW"
    assert result["reasons"] == []


def test_adapter_policy_gate_blocks_failed_orchestration() -> None:
    result = evaluate_adapter_policy_gate({
        "status": "BLOCK",
        "orchestration_id": "blocked-orchestration",
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "audit_record": {},
        "rollback_bundle": {},
        "reasons": ["upstream failure"],
    })

    assert result["status"] == "BLOCK"
    assert result["adapter_policy_gate_passed"] is False
    assert result["next_required_intervention"] is None
    assert "upstream failure" in result["reasons"]
    assert "passing adapter orchestration record is required" in result["reasons"]
    assert "adapter orchestration audit record is required" in result["reasons"]
    assert "adapter orchestration rollback bundle is required" in result["reasons"]


def test_adapter_policy_gate_blocks_nested_mutation_flags() -> None:
    result = evaluate_adapter_policy_gate({
        "status": "PASS",
        "orchestration_id": "bad-nested-flags",
        "execute": False,
        "calls_external_worker": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "audit_record": {
            "execute": False,
            "calls_external_worker": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
            "production_deployment": False,
            "adapter_requests": [
                {
                    "adapter_id": "adapter-role-step-002",
                    "execute": True,
                    "calls_external_worker": False,
                    "writes_target_repo": False,
                    "executes_target_repo_mutation": False,
                    "production_deployment": False,
                }
            ],
            "adapter_results": [
                {
                    "adapter_id": "adapter-role-step-002",
                    "execute": False,
                    "calls_external_worker": True,
                    "writes_target_repo": False,
                    "executes_target_repo_mutation": False,
                    "production_deployment": False,
                }
            ],
        },
        "rollback_bundle": {
            "execute": False,
            "calls_external_worker": False,
            "writes_target_repo": True,
            "executes_target_repo_mutation": False,
            "production_deployment": False,
        },
        "reasons": [],
    })

    assert result["status"] == "BLOCK"
    assert "adapter_request adapter-role-step-002 execute must be false" in result["reasons"]
    assert "adapter_result adapter-role-step-002 calls_external_worker must be false" in result["reasons"]
    assert "rollback_bundle writes_target_repo must be false" in result["reasons"]


def test_adapter_policy_gate_for_requests_and_write_record(tmp_path: Path) -> None:
    adapter_requests = [
        AdapterRequest(
            adapter_id="adapter-role-step-003",
            role="audit_recorder",
            action="record_audit",
        )
    ]

    result = evaluate_adapter_policy_gate_for_requests(adapter_requests)
    written = write_adapter_policy_gate_record(
        adapter_requests=adapter_requests,
        audit_path=tmp_path / "adapter_policy_gate.jsonl",
    )

    assert result["status"] == "PASS"
    assert written["status"] == "PASS"
    assert Path(written["audit_path"]).exists()
