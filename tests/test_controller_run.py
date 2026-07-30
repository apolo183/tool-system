from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.actions import (
    _issue_test_repository_action_capability,
)
from tool_system.repo_controller.controller_run import run_controller

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
GATE_DECISION = {"status": "PASS", "reasons": []}
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3e_controller_cli.yaml"
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p3e_controller_cli.yaml"


def fake_collector_runner(args: list[str]) -> Any:
    if args[:2] == ["pr", "view"]:
        return {
            "number": 9,
            "state": "OPEN",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "headRefOid": "abc123",
            "baseRefName": "main",
        }
    if args[:2] == ["run", "list"]:
        return [
            {
                "databaseId": 1001,
                "name": "tool-system-ci",
                "status": "completed",
                "conclusion": "success",
                "headSha": "abc123",
            }
        ]
    raise AssertionError(f"unexpected collector args: {args}")


def _manifest() -> dict[str, Any]:
    return load_yaml_file(MANIFEST_PATH)


def _change_plan() -> dict[str, Any]:
    return load_yaml_file(CHANGE_PLAN_PATH)


def _lifecycle_approval() -> dict[str, object]:
    return {
        "required": True,
        "approved_by": "external_test_authority",
        "approval_source": "external_authority:injected_fixture",
        "approved_at": "2026-07-31T00:00:00+09:00",
        "approval_record_id": "tool-system-pr-9-merge",
        "repository_full_name": "apolo183/tool-system",
        "pull_request_number": 9,
        "action": "pr_merge",
        "base_branch": "main",
        "expected_head_sha": "abc123",
        "approval_record_or_reason": "injected controller-run fixture",
    }


def _approval_sha256(approval: dict[str, object]) -> str:
    canonical = json.dumps(
        approval,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _action_capability(approval: dict[str, object], runner):
    return _issue_test_repository_action_capability(
        repository_full_name="apolo183/tool-system",
        pr_number=9,
        action="pr_squash",
        base_branch="main",
        expected_head_sha="abc123",
        approval_record_sha256=_approval_sha256(approval),
        runner=runner,
    )


def test_controller_dry_run_writes_audit_jsonl(tmp_path: Path) -> None:
    policy = load_yaml_file(POLICY_PATH)
    audit_path = tmp_path / "controller_audit.jsonl"
    approval = _lifecycle_approval()

    output = run_controller(
        repository_full_name="apolo183/tool-system",
        pr_number=9,
        gate_decision=GATE_DECISION,
        repo_policy=policy,
        audit_path=audit_path,
        task_manifest=_manifest(),
        change_plan=_change_plan(),
        lifecycle_approval=approval,
        dry_run=True,
        collector_runner=fake_collector_runner,
    )

    assert output["status"] == "PASS"
    assert output["action_result"]["status"] == "PASS"
    assert output["audit_path"] == str(audit_path)
    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["repository_full_name"] == "apolo183/tool-system"
    assert record["pr_number"] == 9
    assert record["head_sha"] == "abc123"
    assert record["dry_run"] is True


def test_controller_apply_uses_injected_action_runner(tmp_path: Path) -> None:
    policy = load_yaml_file(POLICY_PATH)
    calls: list[list[str]] = []
    approval = _lifecycle_approval()

    def action_runner(args: list[str]) -> dict[str, Any]:
        calls.append(args)
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}

    output = run_controller(
        repository_full_name="apolo183/tool-system",
        pr_number=9,
        gate_decision=GATE_DECISION,
        repo_policy=policy,
        audit_path=tmp_path / "controller_audit.jsonl",
        task_manifest=_manifest(),
        change_plan=_change_plan(),
        lifecycle_approval=approval,
        dry_run=False,
        collector_runner=fake_collector_runner,
        action_runner=action_runner,
        action_capability=_action_capability(approval, action_runner),
        action_runner_kind="injected_fake",
    )

    assert output["status"] == "PASS"
    assert calls == [[
        "pr",
        "merge",
        "9",
        "--repo",
        "apolo183/tool-system",
        "--squash",
        "--match-head-commit",
        "abc123",
    ]]


def test_controller_blocks_failed_action_and_writes_audit(tmp_path: Path) -> None:
    policy = load_yaml_file(POLICY_PATH)
    approval = _lifecycle_approval()

    def action_runner(args: list[str]) -> dict[str, Any]:
        return {"exit_code": 1, "stdout": "", "stderr": "failed"}

    audit_path = tmp_path / "controller_audit.jsonl"
    output = run_controller(
        repository_full_name="apolo183/tool-system",
        pr_number=9,
        gate_decision=GATE_DECISION,
        repo_policy=policy,
        audit_path=audit_path,
        task_manifest=_manifest(),
        change_plan=_change_plan(),
        lifecycle_approval=approval,
        dry_run=False,
        collector_runner=fake_collector_runner,
        action_runner=action_runner,
        action_capability=_action_capability(approval, action_runner),
        action_runner_kind="injected_fake",
    )

    assert output["status"] == "BLOCK"
    assert output["reasons"] == ["failed"]
    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["action_result"]["status"] == "BLOCK"


def test_controller_apply_without_capability_never_calls_runner(
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    def action_runner(args: list[str]) -> dict[str, Any]:
        calls.append(args)
        return {"exit_code": 0, "stdout": "unexpected", "stderr": ""}

    output = run_controller(
        repository_full_name="apolo183/tool-system",
        pr_number=9,
        gate_decision=GATE_DECISION,
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "controller_audit.jsonl",
        task_manifest=_manifest(),
        change_plan=_change_plan(),
        lifecycle_approval=_lifecycle_approval(),
        dry_run=False,
        collector_runner=fake_collector_runner,
        action_runner=action_runner,
        action_runner_kind="injected_fake",
    )

    assert output["status"] == "BLOCK"
    assert output["reasons"] == [
        "repository action capability is required before mutation"
    ]
    assert calls == []


def test_p3e_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
