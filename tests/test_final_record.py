from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.p5h_record import run_p5h_record


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_final_record.yaml"
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


def _observed(**overrides: object) -> dict[str, object]:
    observed: dict[str, object] = {
        "target_repo": "apolo183/finance-os",
        "default_branch": "main",
        "branches": {"main": {"sha": "abc123"}},
        "target_branch": "p1b-minimal-ranking-code",
        "files": {path: {"exists": False, "sha": None} for path in PLANNED_FILES},
        "open_prs": [],
        "collected_at": "2026-07-06T22:00:00+08:00",
    }
    observed.update(overrides)
    return observed


def test_final_record_blocks_without_ready_collector(tmp_path: Path) -> None:
    result = run_p5h_record(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals=_approvals(),
        audit_path=tmp_path / "blocked.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["ready_for_explicit_execution_request"] is False
    assert result["final_plan"] == {}
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_final_record_passes_without_target_write(tmp_path: Path) -> None:
    result = run_p5h_record(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals=_approvals(),
        observed_state=_observed(),
        audit_path=tmp_path / "pass.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["ready_for_explicit_execution_request"] is True
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["final_plan"]["dry_run"] is True
    assert result["final_plan"]["execute"] is False
    assert result["final_plan"]["base_commit_sha"] == "abc123"
    assert result["next_step_contract"]["may_execute_target_repo_mutation"] is False
    assert result["next_step_contract"]["requires_new_explicit_execution_request"] is True


def test_final_record_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
