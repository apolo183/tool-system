from __future__ import annotations

from pathlib import Path

from tool_system.runtime.transition_gate import (
    build_role_transition_gate,
    build_role_transition_gate_file,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_role_transition_gate_file_passes_without_execution(tmp_path: Path) -> None:
    result = build_role_transition_gate_file(
        graph_path=GRAPH_PATH,
        blueprint_path=BLUEPRINT_PATH,
        audit_path=tmp_path / "role_transition_gate.jsonl",
        rollback_reference="p8e-role-transition-gate branch commits",
    )

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_role_transition_gate"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["allows_execution"] is False
    assert result["allows_downstream_mutation"] is False
    assert result["allows_production_deployment"] is False
    assert result["role_transition_gate_passed"] is True
    assert result["next_required_intervention"] == "P8_MILESTONE_REVIEW"
    assert Path(result["audit_path"]).exists()


def test_role_transition_gate_blocks_failed_runtime_audit_record() -> None:
    result = build_role_transition_gate({
        "status": "BLOCK",
        "graph_id": "blocked-runtime-audit",
        "phase": "P8_MULTI_AGENT_RUNTIME",
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_role_transition_gate": False,
        "audit_bundle": {},
        "rollback_bundle": {},
        "reasons": ["upstream reason"],
    })

    assert result["status"] == "BLOCK"
    assert result["role_transition_gate_passed"] is False
    assert result["next_required_intervention"] is None
    assert "upstream reason" in result["reasons"]
    assert "passing runtime audit bundle is required" in result["reasons"]
    assert "runtime audit bundle must be ready for role transition gate" in result["reasons"]
    assert "runtime audit bundle payload is required" in result["reasons"]
    assert "runtime rollback bundle payload is required" in result["reasons"]


def test_role_transition_gate_blocks_mutating_bundle_payloads() -> None:
    result = build_role_transition_gate({
        "status": "PASS",
        "graph_id": "mutating-runtime-audit",
        "phase": "P8_MULTI_AGENT_RUNTIME",
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_role_transition_gate": True,
        "audit_bundle": {
            "execute": True,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
        },
        "rollback_bundle": {
            "execute": False,
            "writes_target_repo": True,
            "executes_target_repo_mutation": False,
        },
        "reasons": [],
    })

    assert result["status"] == "BLOCK"
    assert "runtime_audit_record execute must be false" in result["reasons"]
    assert "audit_bundle execute must be false" in result["reasons"]
    assert "rollback_bundle writes_target_repo must be false" in result["reasons"]
