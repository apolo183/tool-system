from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.execution_state_snapshot import run_execution_state_snapshot


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_execution_state_snapshot.yaml"
PLANNED_FILES = [
    "pyproject.toml",
    "src/finance_os/__init__.py",
    "src/finance_os/ranking/__init__.py",
    "src/finance_os/ranking/top10.py",
    "tests/test_top10.py",
]


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def _approvals() -> dict[str, object]:
    return {
        "target_repo_approved": True,
        "target_repo_execution_approved": True,
        "approved_by": "apolo183",
    }


def _state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "target_repo": "apolo183/finance-os",
        "default_branch": "main",
        "default_branch_head_sha": "abc123",
        "base_commit_sha": "abc123",
        "target_branch": "p1b-minimal-ranking-code",
        "target_branch_exists": False,
        "file_states": {path: {"exists": False, "sha": None} for path in PLANNED_FILES},
        "open_prs": [],
        "collected_at": "2026-07-06T20:30:00+08:00",
    }
    state.update(overrides)
    return state


def test_state_snapshot_blocks_without_fresh_state(tmp_path: Path) -> None:
    result = run_execution_state_snapshot(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals=_approvals(),
        audit_path=tmp_path / "missing.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert "fresh target repository state snapshot is required" in result["reasons"]


def test_state_snapshot_blocks_if_target_branch_exists(tmp_path: Path) -> None:
    result = run_execution_state_snapshot(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals=_approvals(),
        target_state=_state(target_branch_exists=True),
        audit_path=tmp_path / "branch_exists.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert "target branch must not already exist before guarded creation" in result["reasons"]


def test_state_snapshot_passes_with_complete_fresh_state(tmp_path: Path) -> None:
    result = run_execution_state_snapshot(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals=_approvals(),
        target_state=_state(),
        audit_path=tmp_path / "pass.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["fresh_state_snapshot_valid"] is True
    assert result["approved_for_execution_planning"] is True
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["next_step_contract"]["may_execute_target_repo_mutation"] is False
    assert result["next_step_contract"]["requires_state_sha_match_before_execution"] is True


def test_state_snapshot_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
