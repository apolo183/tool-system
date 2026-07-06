from __future__ import annotations

import json
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.p4c_preview_module import run_p4c_preview


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
PREVIEW_ARTIFACT_PATH = ROOT / "examples" / "p4c_previews" / "finance_os_p1b_minimal_ranking.jsonl"
P4C_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4c_preview.yaml"


def test_p4c_preview_is_no_write(tmp_path: Path) -> None:
    result = run_p4c_preview(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "p4c_preview.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == "apolo183/finance-os"
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []
    assert result["action_plan"]["dry_run"] is True
    steps = result["action_plan"]["steps"]
    assert len(steps) == 7
    assert all(step["dry_run"] is True for step in steps)


def test_committed_p4c_artifact_is_pass_no_write() -> None:
    record = json.loads(PREVIEW_ARTIFACT_PATH.read_text(encoding="utf-8").strip())

    assert record["status"] == "PASS"
    assert record["target_repo"] == "apolo183/finance-os"
    assert record["writes_target_repo"] is False
    assert record["reasons"] == []
    assert record["action_plan"]["dry_run"] is True


def test_p4c_change_plan_validates() -> None:
    result = validate_change_plan(P4C_CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
