from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.audit_log import build_audit_record, validate_audit_record
from tool_system.repo_controller.controller import evaluate_repo_write


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
INPUT_PATH = ROOT / "examples" / "repo_write_decisions" / "tool_system_p3_pass.yaml"


def _load_input() -> dict[str, object]:
    return load_yaml_file(INPUT_PATH)


def test_repo_write_controller_passes_valid_input() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
    )

    assert decision["status"] == "PASS"
    assert decision["reasons"] == []
    assert decision["merge_method"] == "squash"


def test_repo_write_controller_blocks_draft_pr() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)
    value["pull_request"]["draft"] = True

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
    )

    assert decision["status"] == "BLOCK"
    assert "pull request must not be draft" in decision["reasons"]


def test_repo_write_controller_blocks_failed_check() -> None:
    value = _load_input()
    policy = load_yaml_file(POLICY_PATH)
    value["status_checks"] = [{"name": "ci", "status": "completed", "conclusion": "failure"}]

    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
    )

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == ["ci conclusion is failure"]


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
