from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest
import yaml

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import (
    validate_task_graph_process_authority_file,
)
from tool_system.process_authority.contract import (
    AUTHORITY_FIELDS,
    REPLAY_FIELDS,
    build_replay_snapshot,
    validate_explicit_task_pair,
    validate_process_authority,
    validate_replay_snapshot,
)
from tool_system.runner.stage_runner import run_stage_pipeline
from tool_system.runner.task_graph_runner import run_task_graph_pipeline
from tool_system.runner.task_runner import (
    run_batch_file,
    run_batch_pipeline,
    run_task_pipeline,
)
from tool_system.runtime.role_runtime import build_role_runtime_plan


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "config" / "process_authority_v1.yaml"
AUTHORITY_SCHEMA = ROOT / "config" / "process_authority_schema_v1.json"
REPLAY = ROOT / "config" / "replay_snapshot_v1.yaml"
ACTIVE_GATES = ROOT / "examples" / "active_gates.yaml"
GRAPH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_run_entry.yaml"
PLAN = ROOT / "examples" / "change_plans" / "tool_system_run_entry.yaml"
OTHER_MANIFEST = (
    ROOT / "examples" / "task_manifests" / "tool_system_audit_bundle.yaml"
)


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _replay_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    manifest = root / "fixtures" / "manifest.yaml"
    plan = root / "fixtures" / "plan.yaml"
    index = root / "examples" / "active_gates.yaml"
    _write_yaml(manifest, {"task_id": "fixture"})
    _write_yaml(
        plan,
        {
            "plan_id": "fixture-plan",
            "task_manifest": manifest.as_posix(),
        },
    )
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix()],
            "change_plans": [plan.as_posix()],
        },
    )
    computed = build_replay_snapshot(index)
    snapshot = root / "config" / "replay_snapshot_v1.yaml"
    _write_yaml(
        snapshot,
        {
            "snapshot_contract_version": "replay_snapshot_v1",
            "snapshot_id": "tool_system_legacy_pair_replay",
            "blueprint_objective_ref": "product_objective",
            "source_repository": "apolo183/tool-system",
            "source_head_sha": "1" * 40,
            "source_tree_sha": "2" * 40,
            "source_index_path": "examples/active_gates.yaml",
            **computed,
            "capture_algorithm": "sha256_sorted_manifest_hash_plan_hash_v1",
            "authority": False,
            "replay_only": True,
            "execute": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
            "production_deployment": False,
            "cleanup_execution": False,
        },
    )
    return snapshot, plan


def test_current_process_authority_and_canonical_replay_pass() -> None:
    result = validate_process_authority(AUTHORITY, ROOT)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["current_task_input_mode"] == (
        "explicit_manifest_change_plan_pair"
    )
    assert result["implicit_repository_index_allowed"] is False
    assert result["legacy_authority"] is False
    assert result["replay_result"]["status"] == "PASS"
    assert result["replay_result"]["pair_count"] == 108
    assert result["executes_target_repo_mutation"] is False
    assert result["production_deployment"] is False
    assert result["cleanup_execution"] is False


def test_authority_schema_and_yaml_register_the_same_top_level_fields() -> None:
    authority = load_yaml_file(AUTHORITY)
    schema = json.loads(AUTHORITY_SCHEMA.read_text(encoding="utf-8"))

    assert set(authority) == AUTHORITY_FIELDS
    assert set(schema["required"]) == AUTHORITY_FIELDS
    assert set(schema["properties"]) == AUTHORITY_FIELDS
    assert authority["module"] == {
        "module_id": "process-authority",
        "module_version": "2.0.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.0.0",
    }
    assert schema["properties"]["module"]["properties"] == {
        "module_id": {"const": "process-authority"},
        "module_version": {"const": "2.0.0"},
        "public_interface_id": {"const": "process-authority-api"},
        "public_interface_version": {"const": "2.0.0"},
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("module_id", "process_authority"),
        ("module_id", "unknown-module"),
        ("module_version", "1.9.0"),
        ("public_interface_id", "unknown-interface"),
        ("public_interface_version", "1.0.0"),
    ],
)
def test_current_authority_rejects_legacy_unknown_and_stale_identity(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    authority = copy.deepcopy(load_yaml_file(AUTHORITY))
    authority["module"][field] = value
    path = tmp_path / "process_authority_v1.yaml"
    _write_yaml(path, authority)

    result = validate_process_authority(path, ROOT)

    assert result["status"] == "BLOCK"
    assert any("module must identify process-authority" in reason for reason in result["reasons"])


def test_current_authority_rejects_mixed_identity(tmp_path: Path) -> None:
    authority = copy.deepcopy(load_yaml_file(AUTHORITY))
    authority["module"]["compatibility_module_id"] = "process_authority"
    path = tmp_path / "process_authority_v1.yaml"
    _write_yaml(path, authority)

    result = validate_process_authority(path, ROOT)

    assert result["status"] == "BLOCK"
    assert any("module must contain exactly" in reason for reason in result["reasons"])


def test_current_authority_rejects_duplicate_yaml_identity_key(tmp_path: Path) -> None:
    payload = AUTHORITY.read_text(encoding="utf-8").replace(
        "  module_version: 2.0.0\n",
        "  module_id: process_authority\n  module_version: 2.0.0\n",
    )
    path = tmp_path / "process_authority_v1.yaml"
    path.write_text(payload, encoding="utf-8")

    result = validate_process_authority(path, ROOT)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "unable to read process authority: duplicate process authority key: module_id"
    ]


@pytest.mark.parametrize("payload", ["module: [", "", "[]"])
def test_current_authority_rejects_malformed_or_nonmapping_yaml(
    tmp_path: Path,
    payload: str,
) -> None:
    path = tmp_path / "process_authority_v1.yaml"
    path.write_text(payload, encoding="utf-8")

    result = validate_process_authority(path, ROOT)

    assert result["status"] == "BLOCK"
    assert result["reasons"]


def test_current_authority_rejects_missing_file(tmp_path: Path) -> None:
    result = validate_process_authority(tmp_path / "missing.yaml", ROOT)

    assert result["status"] == "BLOCK"
    assert any("unable to read process authority" in reason for reason in result["reasons"])


def test_replay_snapshot_has_exact_non_authoritative_contract() -> None:
    snapshot = load_yaml_file(REPLAY)
    computed = build_replay_snapshot(ACTIVE_GATES)

    assert set(snapshot) == REPLAY_FIELDS
    assert snapshot["source_head_sha"] == (
        "4445cb5ec3ddab0738560e0d5f4a64b9dd582bd7"
    )
    assert snapshot["pair_count"] == 108
    assert snapshot["source_index_sha256"] == computed["source_index_sha256"]
    assert snapshot["pair_set_sha256"] == computed["pair_set_sha256"]
    assert snapshot["authority"] is False
    assert snapshot["replay_only"] is True
    assert snapshot["execute"] is False


def test_replay_snapshot_blocks_changed_source_pair(tmp_path: Path) -> None:
    snapshot, plan = _replay_fixture(tmp_path)
    plan.write_text(plan.read_text(encoding="utf-8") + "changed: true\n", encoding="utf-8")

    result = validate_replay_snapshot(snapshot, snapshot.parents[1])

    assert result["status"] == "BLOCK"
    assert "replay snapshot pair_set_sha256 does not match source inputs" in result[
        "reasons"
    ]


def test_replay_snapshot_rejects_source_path_outside_root(tmp_path: Path) -> None:
    snapshot, _ = _replay_fixture(tmp_path)
    root = snapshot.parents[1]
    index = root / "examples" / "active_gates.yaml"
    outside = tmp_path / "outside.yaml"
    _write_yaml(outside, {"task_id": "outside"})
    value = load_yaml_file(index)
    value["task_manifests"] = [outside.as_posix()]
    _write_yaml(index, value)

    with pytest.raises(ValueError, match="escapes replay source root"):
        build_replay_snapshot(index, root)


def test_explicit_task_pair_binding_passes_and_mismatch_blocks() -> None:
    passing = validate_explicit_task_pair(MANIFEST, PLAN)
    blocked = validate_explicit_task_pair(OTHER_MANIFEST, PLAN)

    assert passing["status"] == "PASS"
    assert passing["binding_mode"] == "explicit_manifest_change_plan_pair"
    assert blocked["status"] == "BLOCK"
    assert any("different task manifest" in reason for reason in blocked["reasons"])


def test_explicit_pair_rejects_symlink_inputs(tmp_path: Path) -> None:
    manifest_link = tmp_path / "manifest.yaml"
    plan_link = tmp_path / "plan.yaml"
    manifest_link.symlink_to(MANIFEST)
    plan_link.symlink_to(PLAN)

    result = validate_explicit_task_pair(manifest_link, plan_link)

    assert result["status"] == "BLOCK"
    assert any("task manifest must not be a symlink" in reason for reason in result["reasons"])
    assert any("change plan must not be a symlink" in reason for reason in result["reasons"])


def test_task_runner_requires_explicit_pair_by_default(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        audit_path=tmp_path / "missing-plan.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert result["change_plan_path"] is None
    assert result["legacy_active_gates_path"] is None
    assert "change plan is required" in result["reasons"]


def test_task_runner_accepts_explicit_bound_pair_without_commands(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        change_plan_path=PLAN,
        audit_path=tmp_path / "explicit-pair.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["change_plan_resolution_source"] == "explicit_process_input"
    assert result["pair_binding_result"]["status"] == "PASS"
    assert result["process_authority_result"]["status"] == "PASS"


def test_failed_explicit_pair_preflight_runs_no_command(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-run-explicit"
    plan = load_yaml_file(PLAN)
    plan["task_manifest"] = OTHER_MANIFEST.as_posix()
    plan["verification"] = {
        "commands": [
            "python -c 'from pathlib import Path; "
            f'Path("{marker.as_posix()}").write_text("ran")\''
        ]
    }
    plan_path = tmp_path / "mismatched-plan.yaml"
    _write_yaml(plan_path, plan)

    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        change_plan_path=plan_path,
        execute_commands=True,
    )

    assert result["status"] == "BLOCK"
    assert result["pair_binding_result"]["status"] == "BLOCK"
    assert result["command_results"] == []
    assert not marker.exists()


def test_legacy_index_is_replay_only_and_cannot_execute(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-run"
    plan = tmp_path / "plan.yaml"
    manifest = tmp_path / "manifest.yaml"
    index = tmp_path / "active_gates.yaml"
    _write_yaml(manifest, {"task_id": "fixture"})
    _write_yaml(
        plan,
        {
            "task_manifest": manifest.as_posix(),
            "verification": {
                "commands": [
                    "python -c 'from pathlib import Path; "
                    f'Path("{marker.as_posix()}").write_text("ran")\''
                ]
            },
        },
    )
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix()],
            "change_plans": [plan.as_posix()],
        },
    )

    result = run_task_pipeline(
        task_manifest_path=manifest,
        active_gates_path=index,
        execute_commands=True,
    )

    assert result["status"] == "BLOCK"
    assert result["change_plan_resolution_source"] == "legacy_replay_blocked"
    assert any("replay-only" in reason for reason in result["reasons"])
    assert not marker.exists()


def test_noncanonical_legacy_index_cannot_be_used_for_replay(tmp_path: Path) -> None:
    index = tmp_path / "active_gates.yaml"
    _write_yaml(index, {"task_manifests": [], "change_plans": []})

    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        active_gates_path=index,
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert result["change_plan_resolution_source"] == "legacy_replay_blocked"
    assert any("canonical examples/active_gates.yaml" in reason for reason in result["reasons"])


def test_task_graph_uses_explicit_process_authority_pairs() -> None:
    result = validate_task_graph_process_authority_file(
        GRAPH,
        BLUEPRINT,
        AUTHORITY,
    )

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_task_graph_process_authority_validation"
    assert result["process_authority_result"]["status"] == "PASS"
    assert len(result["process_authority_checks"]) == 4
    assert all(
        check["status"] == "PASS"
        for check in result["process_authority_checks"]
    )


def test_process_authority_contract_denies_legacy_authority(tmp_path: Path) -> None:
    authority = copy.deepcopy(load_yaml_file(AUTHORITY))
    authority["legacy_compatibility"]["authority"] = True
    path = tmp_path / "process_authority_v1.yaml"
    _write_yaml(path, authority)

    result = validate_process_authority(path, ROOT)

    assert result["status"] == "BLOCK"
    assert any("replay-only and non-authoritative" in reason for reason in result["reasons"])


def test_primary_runtime_callers_have_no_implicit_legacy_index() -> None:
    for caller in (
        run_task_pipeline,
        run_batch_pipeline,
        run_batch_file,
        run_task_graph_pipeline,
        run_stage_pipeline,
    ):
        parameter = inspect.signature(caller).parameters["active_gates_path"]
        assert parameter.default is None

    role_parameter = inspect.signature(build_role_runtime_plan).parameters[
        "process_authority_path"
    ]
    assert role_parameter.default == "config/process_authority_v1.yaml"


def test_packaging_and_hosted_ci_validate_new_authority_contracts() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (
        ROOT / ".github" / "workflows" / "tool-system-ci.yml"
    ).read_text(encoding="utf-8")

    assert (
        'tool-system-validate-process-authority = "tool_system.cli.validate_process_authority:main"'
        in pyproject
    )
    assert (
        "python -m tool_system.cli.validate_process_authority "
        "config/process_authority_v1.yaml"
    ) in workflow
    assert (
        "python -m tool_system.cli.validate_module_registry "
        "config/module_registry_v1.yaml"
    ) in workflow
