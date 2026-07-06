from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.write_packet import run_write_packet


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_write_packet.yaml"


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def test_write_packet_blocks_without_approval(tmp_path: Path) -> None:
    result = run_write_packet(task_manifest=_manifest(), repo_policy=_policy(), audit_path=tmp_path / "blocked.jsonl")

    assert result["status"] == "BLOCK"
    assert result["ready_for_execution"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["write_packet"] == {}


def test_write_packet_passes_with_approval(tmp_path: Path) -> None:
    result = run_write_packet(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={"target_repo_approved": True, "approved_by": "apolo183"},
        audit_path=tmp_path / "approved.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["ready_for_execution"] is True
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["write_packet"]["branch_name"] == "p1b-minimal-ranking-code"


def test_write_packet_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
