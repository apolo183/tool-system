from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

import tool_system.architecture.module_registry as module_registry
from tool_system.architecture.module_registry import (
    CENTRAL_COMPATIBILITY_INPUT_MODE,
    LEGACY_REGISTRY_INPUT_MODE,
    LIFECYCLES,
    REQUIRED_MODULE_FIELDS,
    STATUSES,
    load_s0_identity_mapping,
    validate_module_registry,
)
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
SCHEMA = ROOT / "config" / "module_registry_schema_v1.json"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
S0_CONTRACT = (
    ROOT / "docs" / "tool_system_module_registry_adoption_contract_v1.md"
)

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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract_reference() -> dict[str, str]:
    return {
        "repo_relative_path": S0_CONTRACT.relative_to(ROOT).as_posix(),
        "sha256": _sha256(S0_CONTRACT),
        "format_identity": "markdown-v1",
        "schema_identity": "tool-system-module-registry-adoption-v1",
    }


def central_registry_fixture() -> dict[str, object]:
    legacy = _registry()
    legacy_modules = _modules_by_id(legacy)
    mappings = load_s0_identity_mapping(ROOT)
    mapping_by_current = {
        mapping["current_module_id"]: mapping for mapping in mappings
    }
    reference = _contract_reference()
    modules: list[dict[str, object]] = []
    interfaces: list[dict[str, object]] = []

    for mapping in mappings:
        current_id = mapping["current_module_id"]
        canonical_id = mapping["canonical_module_id"]
        legacy_module = legacy_modules[current_id]
        owned_paths = sorted(
            {
                path.relative_to(ROOT).as_posix()
                for pattern in legacy_module["natural_owner_paths"]
                for path in ROOT.glob(pattern)
                if path.is_file()
            }
        )
        code_boundaries = [
            {
                "boundary_id": f"{canonical_id}-code-{index}",
                "location_kind": "repository_local",
                "path_kind": "exact",
                "path": path,
            }
            for index, path in enumerate(owned_paths, start=1)
        ]
        dependencies = [
            {
                "interface_id": mapping_by_current[
                    dependency["module_id"]
                ]["aggregate_interface_id"],
                "interface_version": mapping_by_current[
                    dependency["module_id"]
                ]["aggregate_interface_version"],
            }
            for dependency in legacy_module[
                "upstream_dependency_module_ids_and_versions"
            ]
        ]
        modules.append(
            {
                "module_id": canonical_id,
                "module_version": mapping["current_module_version"],
                "role": legacy_module["single_responsibility"],
                "owner": legacy_module["owner"],
                "public_interface_refs": [
                    {
                        "interface_id": mapping["aggregate_interface_id"],
                        "interface_version": mapping[
                            "aggregate_interface_version"
                        ],
                    }
                ],
                "internal_dependencies": dependencies,
                "external_dependencies": [],
                "boundaries": {
                    "code": code_boundaries,
                    "data": [],
                    "tests": [
                        {
                            "boundary_id": f"{canonical_id}-test-evidence",
                            "location_kind": "repository_local",
                            "path_kind": "exact",
                            "path": "tests/test_module_registry.py",
                        }
                    ],
                    "runtime_artifacts": [],
                    "cleanup": [],
                },
                "permitted_side_effects": [],
                "rollback_boundary": copy.deepcopy(reference),
                "replacement_boundary": copy.deepcopy(reference),
            }
        )
        interfaces.append(
            {
                "interface_id": mapping["aggregate_interface_id"],
                "interface_version": mapping["aggregate_interface_version"],
                "provider_module_id": canonical_id,
                "consumers": [
                    {
                        "consumer_module_id": mapping_by_current[consumer][
                            "canonical_module_id"
                        ]
                    }
                    for consumer in mapping["current_observed_consumers"]
                ],
                "input_contract": copy.deepcopy(reference),
                "output_contract": copy.deepcopy(reference),
                "error_contract": copy.deepcopy(reference),
                "side_effect_contract": copy.deepcopy(reference),
                "compatibility_policy": copy.deepcopy(reference),
                "replacement_revalidation_boundary": copy.deepcopy(
                    reference
                ),
            }
        )

    return {
        "registry_contract_version": "module_registry_v1",
        "canonical_repo_id": "tool-system",
        "modules": modules,
        "interfaces": interfaces,
    }


def test_current_registry_passes_with_declared_acyclic_execution_order() -> None:
    result = validate_module_registry(REGISTRY, ROOT)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["module_count"] == len(EXPECTED_MODULE_IDS)
    assert set(result["execution_order"]) == EXPECTED_MODULE_IDS
    assert result["registry_input_mode"] == LEGACY_REGISTRY_INPUT_MODE
    assert result["current_registry_authority"] is True
    assert result["compatibility_adapter"]["applied"] is False
    assert result["compatibility_adapter"]["authority"] is False


def test_central_shape_passes_local_compatibility_validation(
    tmp_path: Path,
) -> None:
    fixture = _write_registry(tmp_path, central_registry_fixture())

    result = validate_module_registry(fixture, ROOT)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["module_count"] == len(EXPECTED_MODULE_IDS)
    assert result["registry_input_mode"] == CENTRAL_COMPATIBILITY_INPUT_MODE
    assert result["current_registry_authority"] is False
    assert result["validation_scope"] == "tool_system_local_semantics_only"
    assert result["declared_import_graph"] == result["observed_import_graph"]
    assert result["compatibility_adapter"] == {
        "applied": True,
        "authority": False,
        "persistence": "none",
        "translation_boundary": "memory_only",
        "caller_boundary": "registry_loader_and_validator_entrypoints_only",
        "registry_files_read": [str(fixture)],
        "mapping_owner_path": (
            "docs/tool_system_module_registry_adoption_contract_v1.md"
        ),
        "generated_projection": False,
        "persistent_projection": False,
        "cache_registry": False,
        "serializes_projection": False,
        "second_registry_authority": False,
        "second_schema_authority": False,
        "current_formal_registry_owner": "config/module_registry_v1.yaml",
        "removal_stage": "S11",
        "central_schema_compliance_claimed": False,
        "central_gate_compliance_claimed": False,
        "registry_adoption_claimed": False,
        "governance_activation_claimed": False,
    }


def test_validator_blocks_mixed_top_level_shape(tmp_path: Path) -> None:
    registry = copy.deepcopy(_registry())
    registry["registry_contract_version"] = "module_registry_v1"

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "mixed legacy/central top-level shape is not permitted"
    ]


def test_validator_blocks_mixed_module_field_shape(tmp_path: Path) -> None:
    registry = central_registry_fixture()
    registry["modules"][0]["lifecycle"] = "ACTIVE"

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert any(
        "mixed module field shape" in reason for reason in result["reasons"]
    )


def test_validator_blocks_partial_or_unrecognized_shape(
    tmp_path: Path,
) -> None:
    fixture = _write_registry(tmp_path, {"modules": []})

    result = validate_module_registry(fixture, ROOT)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "module registry shape is partial or unrecognized"
    ]


def test_validator_blocks_duplicate_canonical_module_id(
    tmp_path: Path,
) -> None:
    registry = central_registry_fixture()
    registry["modules"].append(copy.deepcopy(registry["modules"][0]))

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert any(
        reason.startswith("duplicate canonical module ID:")
        for reason in result["reasons"]
    )


def test_validator_blocks_unknown_s0_mapping(tmp_path: Path) -> None:
    registry = central_registry_fixture()
    registry["modules"][0]["module_id"] = "unknown-module"

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert "missing or unknown S0 mapping for module: unknown-module" in result[
        "reasons"
    ]


def test_validator_blocks_unclosed_interface_consumers(
    tmp_path: Path,
) -> None:
    registry = central_registry_fixture()
    interface = next(
        item
        for item in registry["interfaces"]
        if item["interface_id"] == "manifest-validation-api"
    )
    interface["consumers"] = []

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert (
        "manifest-validation-api@1.0.0 provider/consumer declarations "
        "do not close"
    ) in result["reasons"]


def test_compatibility_result_cannot_satisfy_authority(
    tmp_path: Path,
) -> None:
    fixture = _write_registry(tmp_path, central_registry_fixture())

    result = validate_module_registry(
        fixture,
        ROOT,
        require_current_authority=True,
    )

    assert result["status"] == "BLOCK"
    assert result["current_registry_authority"] is False
    assert (
        "non-authoritative compatibility result cannot satisfy current "
        "registry authority"
    ) in result["reasons"]


def test_registry_symlink_cannot_alias_current_authority(
    tmp_path: Path,
) -> None:
    alias = tmp_path / "module_registry_alias.yaml"
    alias.symlink_to(REGISTRY)

    result = validate_module_registry(alias, ROOT)

    assert result["status"] == "PASS"
    assert result["registry_input_mode"] == LEGACY_REGISTRY_INPUT_MODE
    assert result["current_registry_authority"] is False


def test_adapter_is_memory_only_and_does_not_mutate_registry_or_index(
    tmp_path: Path,
) -> None:
    fixture = _write_registry(tmp_path, central_registry_fixture())
    registry_sha = _sha256(REGISTRY)
    fixture_sha = _sha256(fixture)
    index_sha = _sha256(ROOT / ".git" / "index")
    repo_files = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    }

    result = validate_module_registry(fixture, ROOT)

    assert result["status"] == "PASS"
    assert _sha256(REGISTRY) == registry_sha
    assert _sha256(fixture) == fixture_sha
    assert _sha256(ROOT / ".git" / "index") == index_sha
    assert {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    } == repo_files
    assert [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*module_registry*.y*ml")
        if ".git" not in path.relative_to(ROOT).parts
    ] == ["config/module_registry_v1.yaml"]


def test_registry_validator_has_no_persistence_calls() -> None:
    source = (
        ROOT / "src" / "tool_system" / "architecture" / "module_registry.py"
    )
    tree = ast.parse(source.read_text(encoding="utf-8"))
    forbidden = {
        "dump",
        "dumps",
        "mkdir",
        "open",
        "safe_dump",
        "touch",
        "write",
        "write_bytes",
        "write_text",
    }
    observed = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert observed.isdisjoint(forbidden)


def test_duplicate_current_id_after_mapping_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = central_registry_fixture()
    mappings = copy.deepcopy(load_s0_identity_mapping(ROOT))
    mappings[1]["current_module_id"] = mappings[0]["current_module_id"]
    monkeypatch.setattr(
        "tool_system.architecture.module_registry.load_s0_identity_mapping",
        lambda _root: mappings,
    )

    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)

    assert result["status"] == "BLOCK"
    assert any(
        reason.startswith("duplicate current module ID after mapping:")
        for reason in result["reasons"]
    )


def test_s0_id_mapping_collision_blocks() -> None:
    mappings = copy.deepcopy(load_s0_identity_mapping(ROOT))
    mappings[1]["canonical_module_id"] = mappings[0]["canonical_module_id"]
    mapping_contract = {
        "mapping_version": "s0-identity-interface-mapping-v1",
        "module_count": len(mappings),
        "identity_mapping_owner": (
            "src/tool_system/architecture/module_registry.py"
        ),
        "mappings": mappings,
    }

    with pytest.raises(ValueError, match="mapping collision"):
        module_registry._validate_s0_mapping_records(mapping_contract)


def test_central_adapter_reads_exactly_one_registry_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _write_registry(tmp_path, central_registry_fixture())
    calls: list[Path] = []
    real_loader = module_registry.load_yaml_file

    def tracked_loader(path: str | Path) -> dict[str, object]:
        calls.append(Path(path).resolve())
        return real_loader(path)

    monkeypatch.setattr(module_registry, "load_yaml_file", tracked_loader)

    result = validate_module_registry(fixture, ROOT)

    assert result["status"] == "PASS"
    assert calls == [fixture.resolve()]


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
