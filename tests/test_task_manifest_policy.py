from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_task_manifest import validate
from tool_system.manifest.task_manifest import load_yaml_file, validate_manifest_structure
from tool_system.policy.autonomy_policy import validate_autonomy_policy
from tool_system.policy.repo_write_policy import validate_repo_write_policy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY_PATH = ROOT / "policy" / "autonomy_policy.yaml"
EXAMPLE_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"


def test_example_manifest_passes_structure_and_policy() -> None:
    manifest = load_yaml_file(EXAMPLE_PATH)
    policy = load_yaml_file(POLICY_PATH)

    structure_ok, structure_reasons = validate_manifest_structure(manifest)
    policy_ok, policy_reasons = validate_repo_write_policy(manifest, policy)

    assert structure_ok, structure_reasons
    assert policy_ok, policy_reasons


def test_autonomy_policy_passes() -> None:
    autonomy_policy = load_yaml_file(AUTONOMY_POLICY_PATH)

    autonomy_ok, reasons = validate_autonomy_policy(autonomy_policy)

    assert autonomy_ok, reasons


def test_cli_validate_returns_pass_for_example_manifest() -> None:
    result = validate(EXAMPLE_PATH, POLICY_PATH, AUTONOMY_POLICY_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_policy_blocks_finance_os_harness_path() -> None:
    manifest = load_yaml_file(EXAMPLE_PATH)
    policy = load_yaml_file(POLICY_PATH)
    manifest["allowed_files"] = ["harness/agent_loop.py"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert any("blocked path" in reason or "outside allowlist" in reason for reason in reasons)


def test_autonomy_policy_blocks_per_pr_human_review() -> None:
    autonomy_policy = load_yaml_file(AUTONOMY_POLICY_PATH)
    autonomy_policy["authorization_model"]["per_pr_human_review_required"] = True

    autonomy_ok, reasons = validate_autonomy_policy(autonomy_policy)

    assert not autonomy_ok
    assert any("per_pr_human_review_required" in reason for reason in reasons)
