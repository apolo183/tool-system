from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from tool_system.architecture.module_registry import (
    LIFECYCLES,
    REQUIRED_MODULE_FIELDS,
    STATUSES,
    validate_module_registry,
)
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
SCHEMA = ROOT / "config" / "module_registry_schema_v1.json"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"

EXPECTED_MODULE_IDS = {
    "architecture_registry",
    "manifest_validation",
    "agent_worker_runtime",
    "ai_worker_runtime",
    "durable_orchestrator",
    "repository_controller",
    "process_authority",
    "task_planner",
    "task_runner",
    "role_runtime",
    "worker_adapter",
    "target_repo_adapter",
    "cleanup_planner",
    "cli_frontend",
}


def _registry() -> dict[str, object]:
    return load_yaml_file(REGISTRY)


def _modules_by_id(registry: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        module["module_id"]: module
        for module in registry["modules"]
    }


def _write_registry(tmp_path: Path, registry: dict[str, object]) -> Path:
    path = tmp_path / "module_registry_v1.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def _dependency(module_id: str) -> dict[str, str]:
    return {
        "module_id": module_id,
        "module_version": "1.0.0",
        "public_interface_version": "1",
    }


def test_current_registry_passes_with_declared_acyclic_execution_order() -> None:
    result = validate_module_registry(REGISTRY, ROOT)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["module_count"] == len(EXPECTED_MODULE_IDS)
    assert set(result["execution_order"]) == EXPECTED_MODULE_IDS


def test_registry_inventory_and_contract_fields_match_blueprint() -> None:
    registry = _registry()
    modules = registry["modules"]
    blueprint = load_yaml_file(BLUEPRINT)
    blueprint_fields = set(
        blueprint["milestone_module_invariant"]["required_module_contract_fields"]
    )

    assert {module["module_id"] for module in modules} == EXPECTED_MODULE_IDS
    assert REQUIRED_MODULE_FIELDS == blueprint_fields | {"owner", "lifecycle", "status"}
    assert all(set(module) == REQUIRED_MODULE_FIELDS for module in modules)
    assert all(module["blueprint_objective_ref"] == "product_objective" for module in modules)


def test_schema_and_python_validator_register_the_same_contract() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    module_schema = schema["$defs"]["module"]

    assert set(module_schema["required"]) == REQUIRED_MODULE_FIELDS
    assert set(module_schema["properties"]) == REQUIRED_MODULE_FIELDS
    assert set(module_schema["properties"]["lifecycle"]["enum"]) == LIFECYCLES
    assert set(module_schema["properties"]["status"]["enum"]) == STATUSES


def test_every_tool_system_source_file_has_exactly_one_natural_owner() -> None:
    registry = _registry()
    owners: dict[str, list[str]] = {}

    for module in registry["modules"]:
        for pattern in module["natural_owner_paths"]:
            for path in ROOT.glob(pattern):
                if (
                    path.is_file()
                    and path.suffix == ".py"
                    and "src/tool_system" in path.as_posix()
                ):
                    relative = path.relative_to(ROOT).as_posix()
                    owners.setdefault(relative, []).append(module["module_id"])

    expected = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src" / "tool_system").rglob("*.py")
    }
    assert set(owners) == expected
    assert all(len(module_ids) == 1 for module_ids in owners.values())


def test_validator_blocks_natural_owner_overlap(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    modules["architecture_registry"]["natural_owner_paths"].append(
        "src/tool_system/ai_worker/*.py"
    )

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert any("natural owner overlap" in reason for reason in result["reasons"])


def test_validator_blocks_unclaimed_source_path(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    modules["cli_frontend"]["natural_owner_paths"].remove(
        "src/tool_system/cli/main.py"
    )

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert (
        "required module-owned path is unclaimed: src/tool_system/cli/main.py"
        in result["reasons"]
    )


def test_validator_blocks_symlink_natural_owner(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    symlink = tmp_path / "module_link.py"
    symlink.symlink_to(ROOT / "src" / "tool_system" / "__init__.py")
    modules["architecture_registry"]["natural_owner_paths"].append(
        symlink.relative_to(tmp_path).as_posix()
    )

    result = validate_module_registry(_write_registry(tmp_path, registry), tmp_path)

    assert result["status"] == "BLOCK"
    assert any("must not claim symlink" in reason for reason in result["reasons"])


def test_validator_blocks_dependency_cycle(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    modules["ai_worker_runtime"]["upstream_dependency_module_ids_and_versions"] = [
        _dependency("durable_orchestrator")
    ]
    modules["durable_orchestrator"]["downstream_dependency_module_ids_and_versions"] = [
        _dependency("ai_worker_runtime")
    ]
    modules["durable_orchestrator"]["upstream_dependency_module_ids_and_versions"] = [
        _dependency("ai_worker_runtime")
    ]
    modules["ai_worker_runtime"]["downstream_dependency_module_ids_and_versions"] = [
        _dependency("durable_orchestrator")
    ]

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert "module dependency graph must be acyclic" in result["reasons"]


def test_validator_blocks_stale_dependency_version(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    modules["task_planner"]["upstream_dependency_module_ids_and_versions"][0][
        "module_version"
    ] = "0.9.0"

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert "task_planner has stale module_version for manifest_validation" in result["reasons"]


def test_validator_blocks_nonreciprocal_downstream_declaration(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    modules = _modules_by_id(registry)
    modules["manifest_validation"]["downstream_dependency_module_ids_and_versions"] = []

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert any(
        reason.startswith("manifest_validation.downstream dependencies do not match")
        for reason in result["reasons"]
    )


def test_registry_preserves_process_migration_and_cleanup_boundaries() -> None:
    modules = _modules_by_id(_registry())
    process = modules["process_authority"]

    assert process["module_version"] == "2.0.0"
    assert process["public_interface_version"] == "2"
    assert process["input_contract"] == [
        "explicit_manifest_change_plan_pair",
        "explicit_non_authoritative_legacy_replay_request",
    ]
    assert process["cleanup_boundary"] == [
        "legacy_input_retained_pending_cleanup_authorization"
    ]
    assert "legacy_replay_never_authorizes_execution" in process[
        "authorization_envelope"
    ]
    assert "deletion_or_cleanup_not_authorized" in process[
        "authorization_envelope"
    ]


def test_blueprint_claims_structural_not_runtime_enforcement() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    enforcement = blueprint["milestone_module_invariant"]["enforcement"]
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert enforcement["module_registry_path"] == "config/module_registry_v1.yaml"
    assert enforcement["module_registry_schema_path"] == (
        "config/module_registry_schema_v1.json"
    )
    assert enforcement["module_registry_structural_validation_implemented"] is True
    assert enforcement["declared_dependency_dag_validation_implemented"] is True
    assert enforcement["natural_owner_overlap_validation_implemented"] is True
    assert enforcement["source_ownership_coverage_validation_implemented"] is True
    assert enforcement["source_import_edge_enforcement_implemented"] is False
    assert enforcement["runtime_module_enforcement_implemented"] is False
    assert (
        'tool-system-validate-module-registry = "tool_system.cli.validate_module_registry:main"'
        in pyproject
    )
