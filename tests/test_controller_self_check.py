from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.self_check import (
    context_from_event_file,
    resolve_self_check_context,
    run_self_check,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
GATE_DECISION = {"status": "PASS", "reasons": []}
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3f_controller_self_check.yaml"
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p3f_controller_self_check.yaml"


def write_event(path: Path, number: int = 10) -> Path:
    path.write_text(
        json.dumps({"repository": {"full_name": "apolo183/tool-system"}, "pull_request": {"number": number}}),
        encoding="utf-8",
    )
    return path


def fake_collector_runner(args: list[str]) -> Any:
    if args[:2] == ["pr", "view"]:
        return {
            "number": 10,
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


def test_context_from_event_file_reads_repo_and_pr_number(tmp_path: Path) -> None:
    event_path = write_event(tmp_path / "event.json")

    assert context_from_event_file(event_path) == {
        "repository_full_name": "apolo183/tool-system",
        "pr_number": 10,
    }


def test_resolve_context_prefers_explicit_values(tmp_path: Path) -> None:
    event_path = write_event(tmp_path / "event.json")

    assert resolve_self_check_context(
        repository_full_name="apolo183/tool-system",
        pr_number=99,
        event_path=event_path,
    ) == {"repository_full_name": "apolo183/tool-system", "pr_number": 99}


def test_run_self_check_is_dry_run_and_writes_audit(tmp_path: Path) -> None:
    policy = load_yaml_file(POLICY_PATH)
    event_path = write_event(tmp_path / "event.json")
    audit_path = tmp_path / "self_check.jsonl"

    output = run_self_check(
        event_path=event_path,
        gate_decision=GATE_DECISION,
        repo_policy=policy,
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
        audit_path=audit_path,
        collector_runner=fake_collector_runner,
    )

    assert output["status"] == "PASS"
    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["dry_run"] is True
    assert record["pr_number"] == 10
    assert record["head_sha"] == "abc123"


def test_p3f_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
