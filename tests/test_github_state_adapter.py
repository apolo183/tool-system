from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.github_state import (
    build_repo_write_input_from_github_state,
    evaluate_github_state,
    normalize_workflow_jobs,
    normalize_workflow_runs,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
INPUT_PATH = ROOT / "examples" / "github_states" / "tool_system_p3b_pass.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3b_controller_adapter.yaml"


def test_github_state_evaluation_passes_successful_workflow_run() -> None:
    value = load_yaml_file(INPUT_PATH)
    policy = load_yaml_file(POLICY_PATH)

    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        workflow_runs=value["workflow_runs"],
        rollback=value["rollback"],
        repository_full_name=value["repository_full_name"],
    )

    assert output["decision"]["status"] == "PASS"
    assert output["repo_write_input"]["pull_request"]["repository"] == "apolo183/tool-system"
    assert output["audit_record"]["decision_status"] == "PASS"


def test_github_state_evaluation_blocks_failed_workflow_run() -> None:
    value = load_yaml_file(INPUT_PATH)
    policy = load_yaml_file(POLICY_PATH)
    value["workflow_runs"][0]["conclusion"] = "failure"

    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        workflow_runs=value["workflow_runs"],
        rollback=value["rollback"],
        repository_full_name=value["repository_full_name"],
    )

    assert output["decision"]["status"] == "BLOCK"
    assert output["decision"]["reasons"] == ["tool-system-ci conclusion is failure"]


def test_github_state_uses_workflow_jobs_when_available() -> None:
    value = load_yaml_file(INPUT_PATH)
    output = build_repo_write_input_from_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        workflow_runs=[{"name": "run", "status": "completed", "conclusion": "failure"}],
        workflow_jobs=[{"name": "verify", "status": "completed", "conclusion": "success"}],
        repository_full_name=value["repository_full_name"],
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


def test_p3b_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
