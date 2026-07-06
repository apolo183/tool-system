from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.mutation_command_packet import run_mutation_command_packet


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_mutation_command_packet.yaml"


def _manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _policy() -> dict[str, object]:
    return load_yaml_file(POLICY_PATH)


def test_mutation_command_packet_blocks_without_execution_approval(tmp_path: Path) -> None:
    result = run_mutation_command_packet(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={"target_repo_approved": True, "approved_by": "apolo183"},
        audit_path=tmp_path / "blocked.jsonl",
    )

    assert result["status"] == "BLOCK"
    assert result["approved_for_next_step"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["command_packet"]["commands"] == []


def test_mutation_command_packet_previews_commands_without_execution(tmp_path: Path) -> None:
    result = run_mutation_command_packet(
        task_manifest=_manifest(),
        repo_policy=_policy(),
        approvals={
            "target_repo_approved": True,
            "target_repo_execution_approved": True,
            "approved_by": "apolo183",
        },
        audit_path=tmp_path / "packet.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["approved_for_next_step"] is True
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["command_packet"]["dry_run"] is True
    assert result["command_packet"]["execute"] is False
    commands = result["command_packet"]["commands"]
    assert [command["would_call"] for command in commands] == [
        "create_branch",
        "create_or_update_file",
        "create_or_update_file",
        "create_or_update_file",
        "create_or_update_file",
        "create_or_update_file",
        "create_pull_request",
    ]
    assert all(command["execute"] is False for command in commands)
    assert result["next_step_contract"]["may_execute_target_repo_mutation"] is False
    assert result["next_step_contract"]["requires_new_explicit_execution_request"] is True


def test_mutation_command_packet_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
