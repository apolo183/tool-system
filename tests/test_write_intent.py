from __future__ import annotations

import json
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.write_intent_record import run_write_intent_record


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_write_intent_record.yaml"


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def test_write_intent_blocks_without_approval(tmp_path: Path) -> None:
    result = run_write_intent_record(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        audit_path=tmp_path / "blocked_intent.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["intent_status"] == "BLOCKED"
    assert result["target_repo"] == "apolo183/finance-os"
    assert result["writes_target_repo"] is False
    assert result["planned_intent"]["execute"] is False
    assert "explicit target repo approval is required for apolo183/finance-os" in result["reasons"]


def test_write_intent_records_approval_without_mutation(tmp_path: Path) -> None:
    result = run_write_intent_record(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={"target_repo_approved": True, "approved_by": "apolo183"},
        audit_path=tmp_path / "approved_intent.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["intent_status"] == "APPROVED"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["reasons"] == []
    record = json.loads(Path(result["audit_path"]).read_text(encoding="utf-8").strip())
    assert record["intent_status"] == "APPROVED"
    assert record["writes_target_repo"] is False


def test_write_intent_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
