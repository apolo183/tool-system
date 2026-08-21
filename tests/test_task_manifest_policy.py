from __future__ import annotations

import builtins
import json
from datetime import datetime
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tool_system.cli.validate_task_manifest import validate
from tool_system.manifest import task_manifest as task_manifest_module
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
FORWARD_VALID_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "manifest_validation"
    / "forward_valid_task_manifest_v1.yaml"
)
RETAINED_TOOL_SYSTEM_EXAMPLE_PATH = (
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
        FORWARD_VALID_PATH,
        PUBLIC_POLICY_PATH,
        AUTONOMY_POLICY_PATH,
    )

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_policy_allows_formal_repo_manifest_in_pull_request_mode() -> None:
    manifest = deepcopy(load_yaml_file(FORWARD_VALID_PATH))
    policy = load_yaml_file(PUBLIC_POLICY_PATH)
    manifest["write_mode"] = "pull_request"
    manifest["allowed_files"] = ["REPO_MANIFEST.md"]

    policy_ok, reasons = validate_repo_write_policy(manifest, policy)

    assert policy_ok, reasons


def test_policy_allows_tool_system_config_in_pull_request_mode() -> None:
    manifest = deepcopy(load_yaml_file(FORWARD_VALID_PATH))
    policy = load_yaml_file(PUBLIC_POLICY_PATH)
    manifest["write_mode"] = "pull_request"
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


def _direct_schema_errors(manifest: dict[str, object]) -> tuple[object, ...]:
    schema = json.loads(
        (ROOT / "harness" / "task_manifest.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return tuple(Draft202012Validator(schema).iter_errors(manifest))


def _assert_structure_equivalence(manifest: dict[str, object]) -> None:
    structure_ok, _ = validate_manifest_structure(manifest)
    assert structure_ok is (not _direct_schema_errors(manifest))


def test_retained_permissive_manifest_is_classified_but_strictly_blocked() -> None:
    retained = load_yaml_file(RETAINED_TOOL_SYSTEM_EXAMPLE_PATH)

    structure_ok, reasons = validate_manifest_structure(retained)

    assert not structure_ok
    assert all(reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION ") for reason in reasons)


@pytest.mark.parametrize(
    "required_key",
    [
        "task_id",
        "task_type",
        "target_repo",
        "target_branch",
        "phase",
        "approved_blueprint_refs",
        "scope",
        "evidence",
        "allowed_files",
        "forbidden_files",
        "write_mode",
        "verification",
        "rollback",
        "approval",
    ],
)
def test_required_field_deletion_matches_formal_schema(required_key: str) -> None:
    manifest = _target_manifest()
    manifest.pop(required_key)
    _assert_structure_equivalence(manifest)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("unexpected",), True),
        (("scope", "unexpected"), True),
        (("approval", "unexpected"), True),
        (("alignment", "unexpected"), True),
        (("rollback", "execution_authorized"), False),
        (("evidence", 0, "ref"), "retained-only"),
    ],
)
def test_unknown_fields_match_formal_schema(
    path: tuple[object, ...], value: object
) -> None:
    manifest = _target_manifest()
    if path[0] == "alignment":
        manifest["alignment"] = {
            "parent": {
                "document": "parent",
                "section_or_key": "scope",
                "scope": "x",
            },
            "global": {
                "document": "blueprint",
                "section_or_key": "product_objective",
                "scope": "x",
            },
        }
    current: object = manifest
    for part in path[:-1]:
        current = current[part]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]
    _assert_structure_equivalence(manifest)


def test_alignment_and_historical_fixture_are_strictly_typed() -> None:
    manifest = _target_manifest()
    manifest["alignment"] = {
        "parent": {"document": "parent", "section_or_key": "scope", "scope": "x"},
        "global": {"document": "blueprint", "section_or_key": "product_objective", "scope": "x"},
    }
    manifest["historical_fixture"] = {
        "closed": True,
        "new_work_authorized": False,
    }
    _assert_structure_equivalence(manifest)
    manifest["historical_fixture"]["new_work_authorized"] = True
    _assert_structure_equivalence(manifest)
    assert not validate_manifest_structure(manifest)[0]


@pytest.mark.parametrize("value", [("tuple",), b"bytes", {"set"}, datetime(2026, 8, 21)])
def test_non_json_values_fail_before_schema(value: object) -> None:
    manifest = _target_manifest()
    manifest["scope"]["summary"] = value

    structure_ok, reasons = validate_manifest_structure(manifest)

    assert not structure_ok
    assert reasons[0].startswith("TASK_MANIFEST_NON_JSON_VALUE ")


def test_non_string_key_non_finite_and_cycle_fail_deterministically() -> None:
    manifest = _target_manifest()
    manifest[1] = "bad"  # type: ignore[index]
    manifest["scope"]["summary"] = float("inf")
    manifest["scope"]["in_scope"].append(manifest)

    structure_ok, reasons = validate_manifest_structure(manifest)

    assert not structure_ok
    assert reasons == sorted(reasons)
    assert {reason.rsplit("type=", 1)[1] for reason in reasons} == {
        "CYCLIC_CONTAINER",
        "NON_FINITE_FLOAT",
        "NON_STRING_KEY",
    }


def test_shared_acyclic_alias_dag_is_not_treated_as_cycle() -> None:
    manifest = _target_manifest()
    shared = ["same"]
    manifest["scope"]["in_scope"] = shared
    manifest["scope"]["out_of_scope"] = shared

    structure_ok, reasons = validate_manifest_structure(manifest)

    assert structure_ok, reasons


def test_missing_dependency_blocks_without_hand_written_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _target_manifest()
    real_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "jsonschema":
            raise ImportError("synthetic missing dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    assert validate_manifest_structure(manifest) == (
        False,
        ["TASK_MANIFEST_SCHEMA_UNAVAILABLE detail=dependency_missing"],
    )


@pytest.mark.parametrize(
    ("schema_text", "expected_detail"),
    [
        ("{", "preparation_failed"),
        ('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":7}', "metaschema_failed"),
        ('{"$schema":"https://json-schema.org/draft/2020-12/schema","$ref":"https://example.invalid/schema"}', "preparation_failed"),
        ('{"$schema":"https://json-schema.org/draft/2020-12/schema","$dynamicRef":"#x"}', "preparation_failed"),
        ('{"$schema":"https://json-schema.org/draft/2020-12/schema","allOf":[{"$id":"nested"}]}', "preparation_failed"),
    ],
)
def test_invalid_or_remotely_resolving_schema_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    schema_text: str,
    expected_detail: str,
) -> None:
    schema_path = tmp_path / "task_manifest.schema.json"
    schema_path.write_text(schema_text, encoding="utf-8")
    monkeypatch.setattr(task_manifest_module, "_TASK_MANIFEST_SCHEMA_PATH", schema_path)

    assert validate_manifest_structure(_target_manifest()) == (
        False,
        [f"TASK_MANIFEST_SCHEMA_INVALID detail={expected_detail}"],
    )


def test_schema_absence_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        task_manifest_module,
        "_TASK_MANIFEST_SCHEMA_PATH",
        tmp_path / "missing.schema.json",
    )

    assert validate_manifest_structure(_target_manifest()) == (
        False,
        ["TASK_MANIFEST_SCHEMA_UNAVAILABLE detail=read_failed"],
    )


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
