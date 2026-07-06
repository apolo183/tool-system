from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.execution_approval import run_execution_approval_gate


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_execution_approval.yaml"


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def test_execution_gate_blocks_without_write_packet_approval(tmp_path: Path) -> None:
    result = run_execution_approval_gate(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        audit_path=tmp_path / "blocked.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["approved_for_next_step"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert "approved write packet is required" in result["reasons"]


def test_execution_gate_blocks_without_separate_execution_approval(tmp_path: Path) -> None:
    result = run_execution_approval_gate(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={"target_repo_approved": True, "approved_by": "apolo183"},
        audit_path=tmp_path / "blocked_execution.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["write_packet"]
    assert result["execution_approved"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert "separate target repository execution approval is required" in result["reasons"]


def test_execution_gate_passes_with_separate_approval_without_mutation(tmp_path: Path) -> None:
    result = run_execution_approval_gate(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={
            "target_repo_approved": True,
            "target_repo_execution_approved": True,
            "approved_by": "apolo183",
        },
        audit_path=tmp_path / "pass.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["approved_for_next_step"] is True
    assert result["execution_approved"] is True
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["next_step_contract"]["mutation_must_be_separate_step"] is True
    assert result["next_step_contract"]["direct_main_branch_write_allowed"] is False


def test_execution_approval_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
