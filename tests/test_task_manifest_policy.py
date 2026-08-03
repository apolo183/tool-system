from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tool_system.cli.validate_task_manifest import validate
from tool_system.manifest.task_manifest import (
    load_yaml_file,
    validate_manifest_structure,
)
from tool_system.policy.autonomy_policy import validate_autonomy_policy
from tool_system.policy.repo_write_policy import validate_repo_write_policy

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY_PATH = ROOT / "policy" / "autonomy_policy.yaml"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "target_repo"
TARGET_POLICY_PATH = FIXTURE_ROOT / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = FIXTURE_ROOT / "task_manifest.yaml"
TOOL_SYSTEM_EXAMPLE_PATH = (
    ROOT / "examples" / "task_manifests" / "tool_system_p3_repo_controller.yaml"
)
TARGET_REPO = "example-org/example-target"


def _target_manifest() -> dict[str, object]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def _target_policy() -> dict[str, object]:
    return load_yaml_file(TARGET_POLICY_PATH)


def test_synthetic_target_manifest_passes_structure_and_injected_policy() -> None:
    manifest = _target_manifest()
    policy = _target_policy()

    structure_ok, structure_reasons = validate_manifest_structure(manifest)
    policy_ok, policy_reasons = validate_repo_write_policy(manifest, policy)

    assert structure_ok, structure_reasons
    assert policy_ok, policy_reasons


def test_public_policy_does_not_serialize_or_authorize_external_target() -> None:
    manifest = _target_manifest()
    policy = load_yaml_file(PUBLIC_POLICY_PATH)

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert reasons == [f"target repo not allowed: {TARGET_REPO}"]
    assert set(policy["allowed_target_repos"]) == {"apolo183/tool-system"}
    assert policy["external_target_policy"] == {
        "binding_mode": "caller_supplied",
        "public_repository_serializes_downstream_identity": False,
        "unknown_target_disposition": "block",
        "approval_requirement_default": "required",
        "required_per_target_fields": [
            "role",
            "default_write_mode",
            "bootstrap_direct_main_allowed",
            "allowed_paths_by_mode",
            "lifecycle_approval",
            "forbidden_paths",
        ],
    }


def test_autonomy_policy_passes() -> None:
    autonomy_policy = load_yaml_file(AUTONOMY_POLICY_PATH)

    autonomy_ok, reasons = validate_autonomy_policy(autonomy_policy)

    assert autonomy_ok, reasons


def test_cli_validate_returns_pass_for_tool_system_manifest() -> None:
    result = validate(
        TOOL_SYSTEM_EXAMPLE_PATH,
        PUBLIC_POLICY_PATH,
        AUTONOMY_POLICY_PATH,
    )

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_policy_allows_formal_repo_manifest_in_pull_request_mode() -> None:
    manifest = deepcopy(load_yaml_file(TOOL_SYSTEM_EXAMPLE_PATH))
    policy = load_yaml_file(PUBLIC_POLICY_PATH)
    manifest["allowed_files"] = ["REPO_MANIFEST.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert policy_ok, reasons


def test_policy_allows_tool_system_config_in_pull_request_mode() -> None:
    manifest = deepcopy(load_yaml_file(TOOL_SYSTEM_EXAMPLE_PATH))
    policy = load_yaml_file(PUBLIC_POLICY_PATH)
    manifest["allowed_files"] = [
        "config/module_registry_v1.yaml",
        "config/process_authority_v1.yaml",
    ]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert policy_ok, reasons


def test_policy_rejects_new_work_for_generic_retired_target() -> None:
    manifest = _target_manifest()
    policy = _target_policy()
    rules = policy["allowed_target_repos"][TARGET_REPO]
    rules["status"] = "retired"
    rules["historical_fixture"] = {
        "allowed_task_ids": [manifest["task_id"]],
        "allowed_modes": ["patch_only"],
    }

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert reasons == ["retired target repo is not allowed for new work"]


def test_closed_generic_retired_fixture_remains_no_write_compatible() -> None:
    manifest = _target_manifest()
    manifest["historical_fixture"] = {
        "closed": True,
        "new_work_authorized": False,
    }
    policy = _target_policy()
    rules = policy["allowed_target_repos"][TARGET_REPO]
    rules["status"] = "retired"
    rules["historical_fixture"] = {
        "allowed_task_ids": [manifest["task_id"]],
        "allowed_modes": ["patch_only"],
    }

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert policy_ok, reasons
    assert manifest["write_mode"] == "patch_only"
    assert manifest["historical_fixture"]["new_work_authorized"] is False


def test_injected_policy_blocks_target_harness_path() -> None:
    manifest = _target_manifest()
    policy = _target_policy()
    manifest["allowed_files"] = ["tool_harness/agent_loop.py"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert any("blocked path" in reason for reason in reasons)


def test_autonomy_policy_blocks_per_pr_human_review() -> None:
    autonomy_policy = load_yaml_file(AUTONOMY_POLICY_PATH)
    autonomy_policy["authorization_model"]["per_pr_human_review_required"] = True

    autonomy_ok, reasons = validate_autonomy_policy(autonomy_policy)

    assert not autonomy_ok
    assert any("per_pr_human_review_required" in reason for reason in reasons)


def test_injected_policy_blocks_disabled_direct_bootstrap() -> None:
    manifest = _target_manifest()
    policy = _target_policy()
    manifest["write_mode"] = "direct_bootstrap"
    manifest["allowed_files"] = ["AGENTS.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert f"direct bootstrap is disabled for target repo: {TARGET_REPO}" in reasons


def test_bootstrap_paths_do_not_leak_into_pull_request_mode() -> None:
    manifest = _target_manifest()
    policy = _target_policy()
    manifest["write_mode"] = "pull_request"
    policy["allowed_target_repos"][TARGET_REPO]["allowed_paths_by_mode"][
        "pull_request"
    ] = ["src/example_target/**"]
    manifest["allowed_files"] = ["AGENTS.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert not policy_ok
    assert reasons == ["path outside allowlist: AGENTS.md"]
