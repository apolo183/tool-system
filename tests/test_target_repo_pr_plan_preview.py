from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.p4c_preview_module import run_p4c_preview
from tool_system.target_repo.pr_plan_preview import run_target_repo_pr_plan_preview

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "target_repo"
POLICY_PATH = FIXTURE_ROOT / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = FIXTURE_ROOT / "task_manifest.yaml"
P4B_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4b_pr_plan_preview.yaml"
P4C_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4c_preview.yaml"
TARGET_REPO = "example-org/example-target"


def test_synthetic_target_pr_plan_preview_is_no_write(tmp_path: Path) -> None:
    result = run_target_repo_pr_plan_preview(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "target_repo_pr_preview.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == TARGET_REPO
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []
    assert result["pr_preview"]["branch_name"] == "agent/add-greeting"
    assert result["pr_preview"]["changed_files"] == [
        "src/example_target/__init__.py",
        "src/example_target/greeting.py",
        "tests/test_greeting.py",
    ]
    assert result["pr_preview"]["verification_commands"] == [
        "python -m pytest -q",
        "python -m compileall src tests",
    ]


def test_p4b_change_plan_validates() -> None:
    result = validate_change_plan(P4B_CHANGE_PLAN_PATH)

    assert result["status"] == "BLOCK"
    assert any("TASK_MANIFEST_SCHEMA_VIOLATION" in reason for reason in result["reasons"])


def test_p4c_preview_is_no_write(tmp_path: Path) -> None:
    result = run_p4c_preview(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "p4c_preview.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == TARGET_REPO
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []
    assert result["action_plan"]["dry_run"] is True
    assert len(result["action_plan"]["steps"]) == 5


def test_p4c_change_plan_validates() -> None:
    result = validate_change_plan(P4C_CHANGE_PLAN_PATH)

    assert result["status"] == "BLOCK"
    assert any("TASK_MANIFEST_SCHEMA_VIOLATION" in reason for reason in result["reasons"])
