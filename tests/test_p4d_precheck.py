from __future__ import annotations

import json
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.p4d_precheck import run_p4d_precheck
from tool_system.target_repo.p4e_record import run_p4e_intent_record


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
P4D_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4d_precheck.yaml"
P4E_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4e_record.yaml"


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def test_p4d_blocks_finance_os_without_explicit_approval(tmp_path: Path) -> None:
    result = run_p4d_precheck(task_manifest=_manifest(), repo_policy=_policy(), audit_path=tmp_path / "p4d_block.jsonl")
    assert result["status"] == "BLOCK"
    assert result["target_repo"] == "apolo183/finance-os"
    assert result["writes_target_repo"] is False


def test_p4d_passes_finance_os_with_explicit_approval(tmp_path: Path) -> None:
    result = run_p4d_precheck(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={"target_repo_approved": True, "approved_by": "apolo183"},
        audit_path=tmp_path / "p4d_pass.jsonl",
    )
    assert result["status"] == "PASS"
    record = json.loads(Path(result["audit_path"]).read_text(encoding="utf-8").strip())
    assert record["writes_target_repo"] is False


def test_p4d_change_plan_validates() -> None:
    result = validate_change_plan(P4D_CHANGE_PLAN_PATH)
    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_p4e_record_blocks_without_approval(tmp_path: Path) -> None:
    result = run_p4e_intent_record(task_manifest=_manifest(), repo_policy=_policy(), audit_path=tmp_path / "p4e.jsonl")
    assert result["status"] == "BLOCK"
    assert result["writes_target_repo"] is False


def test_p4e_change_plan_validates() -> None:
    result = validate_change_plan(P4E_CHANGE_PLAN_PATH)
    assert result["status"] == "PASS"
    assert result["reasons"] == []
