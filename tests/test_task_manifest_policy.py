from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tool_system.cli.validate_task_manifest import validate
from tool_system.manifest.task_manifest import load_yaml_file, validate_manifest_structure
from tool_system.policy.autonomy_policy import validate_autonomy_policy
from tool_system.policy.repo_write_policy import validate_repo_write_policy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY_PATH = ROOT / "policy" / "autonomy_policy.yaml"
LEGACY_EXAMPLE_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
TOOL_SYSTEM_EXAMPLE_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p3_repo_controller.yaml"


def _finance_us_manifest() -> dict[str, object]:
    manifest = deepcopy(load_yaml_file(LEGACY_EXAMPLE_PATH))
    manifest["task_id"] = "finance-us-p1b-minimal-ranking"
    manifest["target_repo"] = "apolo183/finance-us"
    manifest["target_branch"] = "p1b-minimal-ranking-code"
    manifest["write_mode"] = "pull_request"
    manifest.pop("historical_fixture", None)
    manifest["allowed_files"] = [
        "README.md",
        "AGENTS.md",
        "blueprint/finance_us_phase_1_v0.yaml",
        "finance_us/__init__.py",
        "finance_us/ranking.py",
        "tests/test_ranking.py",
    ]
    return manifest


def test_canonical_finance_us_manifest_passes_structure_and_policy() -> None:
    manifest = _finance_us_manifest()
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
    result = validate(TOOL_SYSTEM_EXAMPLE_PATH, POLICY_PATH, AUTONOMY_POLICY_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_policy_rejects_legacy_finance_os_target() -> None:
    manifest = deepcopy(load_yaml_file(LEGACY_EXAMPLE_PATH))
    policy = load_yaml_file(POLICY_PATH)
    manifest.pop("historical_fixture")
    manifest["write_mode"] = "pull_request"

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert "retired target repo is not allowed for new work" in reasons


def test_closed_legacy_finance_os_fixture_remains_no_write_compatible() -> None:
    manifest = load_yaml_file(LEGACY_EXAMPLE_PATH)
    policy = load_yaml_file(POLICY_PATH)

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert policy_ok, reasons
    assert manifest["write_mode"] == "patch_only"
    assert manifest["historical_fixture"]["new_work_authorized"] is False


def test_policy_blocks_finance_us_harness_path() -> None:
    manifest = _finance_us_manifest()
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


def test_policy_blocks_disabled_direct_bootstrap() -> None:
    manifest = _finance_us_manifest()
    policy = load_yaml_file(POLICY_PATH)
    manifest["write_mode"] = "direct_bootstrap"
    manifest["allowed_files"] = ["README.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert "direct bootstrap is disabled for target repo: apolo183/finance-us" in reasons


def test_bootstrap_paths_do_not_leak_into_pull_request_mode() -> None:
    manifest = _finance_us_manifest()
    policy = load_yaml_file(POLICY_PATH)
    policy["allowed_target_repos"]["apolo183/finance-us"]["allowed_paths_by_mode"]["pull_request"] = [
        "finance_us/**"
    ]
    manifest["allowed_files"] = ["README.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert reasons == ["path outside allowlist: README.md"]
