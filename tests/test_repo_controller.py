from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.audit_log import build_audit_record, validate_audit_record
from tool_system.repo_controller.controller import evaluate_repo_write


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
INPUT_PATH = ROOT / "examples" / "repo_write_decisions" / "tool_system_p3_pass.yaml"
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p3_repo_controller.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3_repo_controller.yaml"


def _load_input() -> dict[str, object]:
    return load_yaml_file(INPUT_PATH)


def _evaluate(value: dict[str, object], policy: dict[str, object] | None = None) -> dict[str, object]:
    return evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy or load_yaml_file(POLICY_PATH),
        status_checks=value["status_checks"],
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
    )


def test_repo_write_controller_passes_valid_input() -> None:
    value = _load_input()

    decision = _evaluate(value)

    assert decision["status"] == "PASS"
    assert decision["reasons"] == []
    assert decision["merge_method"] == "squash"


def test_repo_write_controller_blocks_draft_pr() -> None:
    value = _load_input()
    value["pull_request"]["draft"] = True

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert "pull request must not be draft" in decision["reasons"]


def test_repo_write_controller_blocks_failed_check() -> None:
    value = _load_input()
    value["status_checks"] = [{"name": "ci", "status": "completed", "conclusion": "failure"}]

    decision = _evaluate(value)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == ["ci conclusion is failure"]


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
