from __future__ import annotations

import json
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.pr_plan_preview import run_target_repo_pr_plan_preview


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
PREVIEW_ARTIFACT_PATH = ROOT / "examples" / "target_repo_pr_previews" / "finance_os_p1b_minimal_ranking.jsonl"
P4B_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4b_pr_plan_preview.yaml"


def test_finance_os_pr_plan_preview_is_no_write(tmp_path: Path) -> None:
    result = run_target_repo_pr_plan_preview(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "finance_os_pr_preview.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == "apolo183/finance-os"
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []
    assert result["pr_preview"]["branch_name"] == "p1b-minimal-ranking-code"
    assert result["pr_preview"]["changed_files"] == [
        "pyproject.toml",
        "src/finance_os/__init__.py",
        "src/finance_os/ranking/__init__.py",
        "src/finance_os/ranking/top10.py",
        "tests/test_top10.py",
    ]
    assert result["pr_preview"]["verification_commands"] == [
        "python3 -m pytest -q",
        "python3 -m compileall src tests",
    ]


def test_committed_pr_preview_artifact_is_pass_no_write() -> None:
    record = json.loads(PREVIEW_ARTIFACT_PATH.read_text(encoding="utf-8").strip())

    assert record["status"] == "PASS"
    assert record["mode"] == "target_repo_pr_plan_preview"
    assert record["target_repo"] == "apolo183/finance-os"
    assert record["writes_target_repo"] is False
    assert record["reasons"] == []
    assert record["pr_preview"]["branch_name"] == "p1b-minimal-ranking-code"
    assert record["pr_preview"]["title"] == "Add deterministic in-memory shadow top10 ranking and smoke tests."


def test_p4b_change_plan_validates() -> None:
    result = validate_change_plan(P4B_CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
