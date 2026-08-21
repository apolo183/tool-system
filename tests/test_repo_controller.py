from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.audit_log import (
    build_audit_record,
    validate_audit_record,
)
from tool_system.repo_controller.controller import evaluate_repo_write

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
INPUT_PATH = ROOT / "examples" / "repo_write_decisions" / "tool_system_p3_pass.yaml"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_task_manifest_v1.yaml"
CHANGE_PLAN_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_change_plan_v1.yaml"


def _load_input() -> dict[str, object]:
    return load_yaml_file(INPUT_PATH)


def _lifecycle_approval(value: dict[str, object]) -> dict[str, object]:
    pull_request = value["pull_request"]
    return {
        "required": True,
        "approved_by": "external_test_authority",
        "approval_source": "external_authority:injected_fixture",
        "approved_at": "2026-07-31T00:00:00+09:00",
        "approval_record_id": "tool-system-pr-5-merge",
        "repository_full_name": pull_request["repository"],
        "pull_request_number": pull_request["number"],
        "action": "pr_merge",
        "base_branch": pull_request["base"],
        "expected_head_sha": pull_request["head_sha"],
        "approval_record_or_reason": "injected controller lifecycle fixture",
    }


def _evaluate(
    value: dict[str, object],
    policy: dict[str, object] | None = None,
    lifecycle_approval: dict[str, object] | None = None,
) -> dict[str, object]:
    return evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy or load_yaml_file(POLICY_PATH),
        status_checks=value["status_checks"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        lifecycle_approval=lifecycle_approval or _lifecycle_approval(value),
    )


def test_repo_write_controller_passes_valid_input() -> None:
    value = _load_input()

    decision = _evaluate(value)

    assert decision["status"] == "PASS"
    assert decision["reasons"] == []
    assert decision["merge_method"] == "squash"
    assert len(decision["approval_record_sha256"]) == 64


def test_repo_write_controller_blocks_draft_pr() -> None:
    value = _load_input()
    value["pull_request"]["draft"] = True

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert "pull request must not be draft" in decision["reasons"]


def test_repo_write_controller_blocks_failed_check() -> None:
    value = _load_input()
    value["status_checks"][0]["conclusion"] = "failure"

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == ["verify conclusion is failure"]


@pytest.mark.parametrize("conclusion", ["success", "neutral", "skipped"])
def test_repo_write_controller_preserves_github_passing_conclusions(
    conclusion: str,
) -> None:
    value = _load_input()
    value["status_checks"][0]["conclusion"] = conclusion

    decision = _evaluate(value)

    assert decision["status"] == "PASS"
    assert decision["reasons"] == []


def test_repo_write_controller_requires_exact_check_name() -> None:
    value = _load_input()
    value["status_checks"][0]["name"] = "unrelated-check"

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "required status check missing: verify from github-actions"
    ]


def test_repo_write_controller_requires_exact_check_source() -> None:
    value = _load_input()
    value["status_checks"][0]["source_app"] = "untrusted-app"

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "required status check verify must come from github-actions"
    ]


def test_repo_write_controller_requires_current_head_check() -> None:
    value = _load_input()
    value["status_checks"][0]["head_sha"] = "stale-head"

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "verify head_sha must match current pull request head"
    ]


def test_repo_write_controller_blocks_duplicate_required_check() -> None:
    value = _load_input()
    value["status_checks"].append(deepcopy(value["status_checks"][0]))

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "status check has duplicate binding: verify from github-actions"
    ]


def test_repo_write_controller_blocks_malformed_required_check_policy() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)
    policy["allowed_target_repos"]["apolo183/tool-system"][
        "required_status_checks"
    ] = [{"name": "verify"}]

    decision = _evaluate(value, policy=policy)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "required status check 0 missing fields: source_app",
        "required status check 0 source_app is required",
    ]


def test_repo_write_controller_blocks_non_mapping_check() -> None:
    value = _load_input()
    value["status_checks"] = ["not-a-mapping"]

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        "status check 0 must be a mapping",
        "required status check missing: verify from github-actions",
    ]


def test_repo_write_controller_blocks_inactive_policy() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)
    policy["status"] = "draft"

    decision = _evaluate(value, policy=policy)

    assert decision["status"] == "BLOCK"
    assert "repo_write_policy.status must be active" in decision["reasons"]


def test_repo_write_controller_requires_manifest_context() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
    )

    assert decision["status"] == "BLOCK"
    assert "task manifest is required for repo write decision" in decision["reasons"]
    assert "change plan is required for repo write decision" in decision["reasons"]


def test_task_manifest_approval_alone_cannot_authorize_lifecycle_action() -> None:
    value = _load_input()

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=load_yaml_file(POLICY_PATH),
        status_checks=value["status_checks"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
    )

    assert decision["status"] == "BLOCK"
    assert decision["approval_record_sha256"] is None
    assert any(
        "separate lifecycle approval is required" in reason
        for reason in decision["reasons"]
    )


def test_lifecycle_approval_is_bound_to_current_pr_context() -> None:
    value = _load_input()
    approval = _lifecycle_approval(value)
    approval["action"] = "pr_ready"
    approval["base_branch"] = "stale-base"
    approval["expected_head_sha"] = "stale-head"

    decision = _evaluate(value, lifecycle_approval=approval)

    assert decision["status"] == "BLOCK"
    assert decision["approval_record_sha256"] is None
    assert "lifecycle approval action must match current lifecycle context" in (
        decision["reasons"]
    )
    assert "lifecycle approval base_branch must match current lifecycle context" in (
        decision["reasons"]
    )
    assert (
        "lifecycle approval expected_head_sha must match current lifecycle context"
        in decision["reasons"]
    )


def test_lifecycle_approval_requires_external_source_and_exact_fields() -> None:
    value = _load_input()
    approval = _lifecycle_approval(value)
    approval["approval_source"] = "task_manifest"
    approval["unexpected"] = "value"

    decision = _evaluate(value, lifecycle_approval=approval)

    assert decision["status"] == "BLOCK"
    assert (
        "lifecycle approval approval_source must identify an external authority"
        in decision["reasons"]
    )
    assert "lifecycle approval has unexpected fields: unexpected" in decision["reasons"]


def test_repo_write_controller_blocks_change_plan_outside_manifest_scope() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)
    change_plan = deepcopy(load_yaml_file(CHANGE_PLAN_PATH))
    change_plan["changed_files"].append("finance/not_allowed.py")

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=change_plan,
    )

    assert decision["status"] == "BLOCK"
    assert "blocked changed file: finance/not_allowed.py" in decision["reasons"]
    assert "changed file outside manifest allowlist: finance/not_allowed.py" in decision["reasons"]


def test_audit_record_passes_validation() -> None:
    value = _load_input()
    decision = {"status": "PASS", "merge_method": "squash", "reasons": []}

    record = build_audit_record(
        pull_request=value["pull_request"],
        decision=decision,
        rollback=value["rollback"],
        created_at="2026-07-05T00:00:00+00:00",
    )
    ok, reasons = validate_audit_record(record)

    assert ok, reasons
    assert record["decision_status"] == "PASS"
