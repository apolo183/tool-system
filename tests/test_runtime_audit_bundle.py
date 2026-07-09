from __future__ import annotations

from pathlib import Path

from tool_system.runtime.audit_bundle import (
    build_runtime_audit_bundle,
    build_runtime_audit_bundle_file,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_runtime_audit_bundle_file_builds_no_mutation_bundles(tmp_path: Path) -> None:
    result = build_runtime_audit_bundle_file(
        graph_path=GRAPH_PATH,
        blueprint_path=BLUEPRINT_PATH,
        audit_path=tmp_path / "runtime_audit_bundle.jsonl",
        rollback_reference="p8d-runtime-audit-bundle branch commits",
    )

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_runtime_audit_bundle"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["ready_for_role_transition_gate"] is True
    assert result["ready_for_milestone_review"] is False
    assert result["audit_bundle"]["execute"] is False
    assert result["audit_bundle"]["writes_target_repo"] is False
    assert result["audit_bundle"]["executes_target_repo_mutation"] is False
    assert result["rollback_bundle"]["execute"] is False
    assert result["rollback_bundle"]["writes_target_repo"] is False
    assert result["rollback_bundle"]["executes_target_repo_mutation"] is False
    assert result["audit_bundle"]["role_step_count"] == result["runtime_plan"]["role_step_count"]
    assert result["audit_bundle"]["worker_result_count"] == result["runtime_plan"]["worker_result_count"]
    assert Path(result["audit_path"]).exists()


def test_runtime_audit_bundle_blocks_mutating_runtime_plan() -> None:
    result = build_runtime_audit_bundle({
        "status": "PASS",
        "graph_id": "bad-runtime-plan",
        "phase": "P8_MULTI_AGENT_RUNTIME",
        "execute": True,
        "writes_target_repo": True,
        "executes_target_repo_mutation": True,
        "role_steps": [
            {
                "step_id": "role-step-001",
                "task_id": "mutating-step",
                "role": "patch_author",
                "action": "prepare_patch_preview",
                "execute": True,
                "writes_target_repo": False,
                "executes_target_repo_mutation": False,
            }
        ],
        "worker_results": [
            {
                "step_id": "role-step-001",
                "task_id": "mutating-step",
                "role": "patch_author",
                "action": "prepare_patch_preview",
                "status": "PASS",
                "worker_kind": "test_worker",
                "execute": False,
                "writes_target_repo": True,
                "executes_target_repo_mutation": False,
            }
        ],
        "reasons": [],
    })

    assert result["status"] == "BLOCK"
    assert result["audit_bundle"] == {}
    assert result["rollback_bundle"] == {}
    assert "runtime plan execute must be false" in result["reasons"]
    assert "runtime plan writes_target_repo must be false" in result["reasons"]
    assert "runtime plan executes_target_repo_mutation must be false" in result["reasons"]
    assert "role_step role-step-001 execute must be false" in result["reasons"]
    assert "worker_result role-step-001 writes_target_repo must be false" in result["reasons"]


def test_runtime_audit_bundle_requires_worker_result_parity() -> None:
    result = build_runtime_audit_bundle({
        "status": "PASS",
        "graph_id": "missing-worker-result",
        "phase": "P8_MULTI_AGENT_RUNTIME",
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "role_steps": [
            {
                "step_id": "role-step-001",
                "task_id": "evidence",
                "role": "evidence_collector",
                "action": "collect_evidence",
                "execute": False,
                "writes_target_repo": False,
                "executes_target_repo_mutation": False,
            }
        ],
        "worker_results": [],
        "reasons": [],
    })

    assert result["status"] == "BLOCK"
    assert "role step count must match worker result count" in result["reasons"]
