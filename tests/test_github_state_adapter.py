from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.github_state import (
    build_repo_write_input_from_github_state,
    evaluate_github_state,
    normalize_check_runs,
    normalize_workflow_jobs,
    normalize_workflow_runs,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
INPUT_PATH = ROOT / "examples" / "github_states" / "tool_system_p3b_pass.yaml"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_task_manifest_v1.yaml"
CHANGE_PLAN_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_change_plan_v1.yaml"


def _lifecycle_approval(value: dict[str, object]) -> dict[str, object]:
    pull_request = value["pull_request"]
    return {
        "required": True,
        "approved_by": "external_test_authority",
        "approval_source": "external_authority:injected_fixture",
        "approved_at": "2026-07-31T00:00:00+09:00",
        "approval_record_id": "tool-system-pr-6-merge",
        "repository_full_name": value["repository_full_name"],
        "pull_request_number": pull_request["number"],
        "action": "pr_merge",
        "base_branch": pull_request["base"],
        "expected_head_sha": pull_request["head_sha"],
        "approval_record_or_reason": "injected GitHub-state fixture",
    }


def test_github_state_evaluation_passes_successful_check_run() -> None:
    value = load_yaml_file(INPUT_PATH)
    policy = load_yaml_file(POLICY_PATH)

    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        check_runs=value["check_runs"],
        rollback=value["rollback"],
        repository_full_name=value["repository_full_name"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        lifecycle_approval=_lifecycle_approval(value),
    )

    assert output["decision"]["status"] == "PASS"
    assert output["repo_write_input"]["pull_request"]["repository"] == "apolo183/tool-system"
    assert output["audit_record"]["decision_status"] == "PASS"


def test_github_state_evaluation_blocks_failed_check_run() -> None:
    value = load_yaml_file(INPUT_PATH)
    policy = load_yaml_file(POLICY_PATH)
    value["check_runs"][0]["conclusion"] = "failure"

    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        check_runs=value["check_runs"],
        rollback=value["rollback"],
        repository_full_name=value["repository_full_name"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        lifecycle_approval=_lifecycle_approval(value),
    )

    assert output["decision"]["status"] == "BLOCK"
    assert output["decision"]["reasons"] == ["verify conclusion is failure"]


def test_github_state_uses_workflow_jobs_when_available() -> None:
    value = load_yaml_file(INPUT_PATH)
    output = build_repo_write_input_from_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        workflow_runs=[{"name": "run", "status": "completed", "conclusion": "failure"}],
        workflow_jobs=[{"name": "verify", "status": "completed", "conclusion": "success"}],
        repository_full_name=value["repository_full_name"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        lifecycle_approval=_lifecycle_approval(value),
    )

    assert output["status_checks"] == [
        {"name": "verify", "status": "completed", "conclusion": "success"}
    ]
    assert output["task_manifest"]["task_id"] == "manifest-validation-forward-valid-v1"
    assert output["change_plan"]["plan_id"] == "manifest-validation-forward-valid-v1"
    assert output["lifecycle_approval"]["approval_record_id"] == (
        "tool-system-pr-6-merge"
    )


def test_legacy_workflow_job_evidence_cannot_bypass_check_provenance() -> None:
    value = load_yaml_file(INPUT_PATH)
    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=load_yaml_file(POLICY_PATH),
        workflow_jobs=[
            {"name": "verify", "status": "completed", "conclusion": "success"}
        ],
        repository_full_name=value["repository_full_name"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        lifecycle_approval=_lifecycle_approval(value),
    )

    assert output["decision"]["status"] == "BLOCK"
    assert output["decision"]["reasons"] == [
        "verify source_app is required",
        "verify head_sha must match current pull request head",
        "required status check missing: verify from github-actions",
    ]


def test_existing_positional_workflow_arguments_keep_their_meaning() -> None:
    value = load_yaml_file(INPUT_PATH)
    output = build_repo_write_input_from_github_state(
        value["pull_request"],
        value["gate_decision"],
        [{"name": "run", "status": "completed", "conclusion": "failure"}],
        [{"name": "verify", "status": "completed", "conclusion": "success"}],
    )

    assert output["status_checks"] == [
        {"name": "verify", "status": "completed", "conclusion": "success"}
    ]


def test_workflow_normalizers_preserve_status_and_conclusion() -> None:
    assert normalize_workflow_runs([
        {"name": "tool-system-ci", "status": "completed", "conclusion": "success"}
    ]) == [{"name": "tool-system-ci", "status": "completed", "conclusion": "success"}]

    assert normalize_workflow_jobs([
        {"name": "verify", "status": "queued", "conclusion": None}
    ]) == [{"name": "verify", "status": "queued", "conclusion": None}]


def test_check_run_normalizer_preserves_provenance() -> None:
    assert normalize_check_runs([
        {
            "id": 1001,
            "name": "verify",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123",
            "app": {"slug": "github-actions"},
        }
    ]) == [
        {
            "id": 1001,
            "name": "verify",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123",
            "source_app": "github-actions",
        }
    ]


def test_explicit_empty_check_run_set_does_not_fall_back_to_workflow_runs() -> None:
    value = load_yaml_file(INPUT_PATH)
    output = build_repo_write_input_from_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        check_runs=[],
        workflow_runs=[
            {"name": "tool-system-ci", "status": "completed", "conclusion": "success"}
        ],
    )

    assert output["status_checks"] == []


def test_p3b_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
