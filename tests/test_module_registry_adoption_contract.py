from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from tool_system.architecture.repo_manifest import FORMAL_COLUMNS, _table_rows
from tool_system.architecture.module_registry import extract_managed_import_graph
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "tool_system_module_registry_adoption_contract_v1.md"
REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
MANIFEST = ROOT / "REPO_MANIFEST.md"
SOURCE_ROOT = ROOT / "src"

CANONICAL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
BASE_COMMIT = "2b86079dbb82d0426240fd6b5836868e5b9c9697"
MAPPING_OWNER = "src/tool_system/architecture/module_registry.py"
TARGET_OWNER_DELTAS = {
    "src/tool_system/gate/command_runner.py": (
        "manifest_validation",
        "task_runner",
    ),
    "src/tool_system/gate/test_gate.py": (
        "manifest_validation",
        "task_runner",
    ),
}


class AdoptionContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdoptionContractError(message)


def _contract_text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _yaml_block(name: str, text: str | None = None) -> dict[str, Any]:
    source = _contract_text() if text is None else text
    start = f"<!-- {name}:BEGIN -->\n~~~yaml\n"
    end = f"\n~~~\n<!-- {name}:END -->"
    _require(source.count(start) == 1, f"{name} must have one start marker")
    _require(source.count(end) == 1, f"{name} must have one end marker")
    body = source.split(start, 1)[1].split(end, 1)[0]
    loaded = yaml.safe_load(body)
    _require(isinstance(loaded, dict), f"{name} must decode to a mapping")
    return loaded


def _registry() -> dict[str, Any]:
    return load_yaml_file(REGISTRY)


def _registry_by_id() -> dict[str, dict[str, Any]]:
    modules = _registry()["modules"]
    return {module["module_id"]: module for module in modules}


def _source_owners() -> dict[Path, str]:
    owners: dict[Path, str] = {}
    for module in _registry()["modules"]:
        module_id = module["module_id"]
        for pattern in module["natural_owner_paths"]:
            for path in ROOT.glob(pattern):
                resolved = path.resolve()
                if (
                    path.is_file()
                    and path.suffix == ".py"
                    and SOURCE_ROOT.resolve() in resolved.parents
                ):
                    _require(
                        resolved not in owners,
                        f"source has multiple current owners: {path}",
                    )
                    owners[resolved] = module_id
    expected = {
        path.resolve()
        for path in (SOURCE_ROOT / "tool_system").rglob("*.py")
        if path.is_file()
    }
    _require(set(owners) == expected, "current registry must own every Python source")
    for relative, (legacy_owner, target_owner) in TARGET_OWNER_DELTAS.items():
        path = (ROOT / relative).resolve()
        _require(
            owners.get(path) == legacy_owner,
            f"accepted legacy owner delta is unavailable: {relative}",
        )
        owners[path] = target_owner
    return owners


def _import_identity(path: Path) -> str:
    parts = list(path.relative_to(SOURCE_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _selector_matches(selector: dict[str, str], import_name: str) -> bool:
    _require(
        set(selector) == {"kind", "name"},
        "Python import selectors must contain exactly kind and name",
    )
    kind = selector["kind"]
    name = selector["name"]
    _require(kind in {"exact", "prefix"}, "Python import selector kind is invalid")
    _require(
        name == "tool_system" or name.startswith("tool_system."),
        "Python import identity must remain in the tool_system package",
    )
    if kind == "exact":
        return import_name == name
    return import_name == name or import_name.startswith(f"{name}.")


def _static_provider_consumers() -> dict[str, list[str]]:
    records = _yaml_block("S0-IDENTITY-MAPPING")["mapping_contract"]["mappings"]
    canonical_by_current = {
        record["current_module_id"]: record["canonical_module_id"]
        for record in records
    }
    current_by_canonical = {
        canonical: current for current, canonical in canonical_by_current.items()
    }
    owner_by_path = {
        path.relative_to(ROOT).as_posix(): canonical_by_current[current_owner]
        for path, current_owner in _source_owners().items()
    }
    graph, reasons = extract_managed_import_graph(ROOT, owner_by_path, records)
    _require(reasons == [], f"managed import graph must resolve exactly: {reasons}")
    return {
        current_by_canonical[provider]: sorted(
            current_by_canonical[consumer] for consumer in consumers
        )
        for provider, consumers in graph.items()
    }


def _declared_provider_consumers() -> dict[str, list[str]]:
    return {
        module["module_id"]: sorted(
            dependency["module_id"]
            for dependency in module[
                "downstream_dependency_module_ids_and_versions"
            ]
        )
        for module in _registry()["modules"]
    }


def _validate_mapping_data(data: dict[str, Any]) -> None:
    mapping = data.get("mapping_contract")
    _require(isinstance(mapping, dict), "mapping_contract is required")
    records = mapping.get("mappings")
    _require(isinstance(records, list), "mappings must be a list")
    _require(mapping.get("module_count") == 14, "module_count must remain 14")
    _require(len(records) == 14, "all fourteen mapping rows are required")
    _require(
        mapping.get("identity_mapping_owner") == MAPPING_OWNER,
        "the mapping owner must remain the temporary adapter natural owner",
    )

    registry = _registry_by_id()
    observed = _static_provider_consumers()
    current_ids = [record.get("current_module_id") for record in records]
    canonical_ids = [record.get("canonical_module_id") for record in records]
    interface_ids = [record.get("aggregate_interface_id") for record in records]
    _require(len(current_ids) == len(set(current_ids)), "current IDs must be unique")
    _require(
        len(canonical_ids) == len(set(canonical_ids)),
        "canonical IDs must be unique",
    )
    _require(
        len(interface_ids) == len(set(interface_ids)),
        "aggregate interface IDs must be unique",
    )
    _require(set(current_ids) == set(registry), "mapping IDs must equal the registry")

    records_by_id = {record["current_module_id"]: record for record in records}
    for current_id, module in registry.items():
        record = records_by_id[current_id]
        canonical_id = record.get("canonical_module_id")
        _require(
            canonical_id == current_id.replace("_", "-"),
            f"{current_id} must use the explicit underscore-to-hyphen rule",
        )
        _require("_" not in canonical_id, "canonical module IDs cannot use underscore")
        _require(
            CANONICAL_ID_RE.fullmatch(canonical_id) is not None,
            "canonical module ID syntax is invalid",
        )
        _require(
            record.get("current_module_version") == module["module_version"],
            f"{current_id} module version drifted",
        )
        _require(
            record.get("aggregate_interface_id") == f"{canonical_id}-api",
            f"{current_id} aggregate interface identity drifted",
        )
        expected_interface_version = f"{module['public_interface_version']}.0.0"
        _require(
            record.get("aggregate_interface_version")
            == expected_interface_version,
            f"{current_id} aggregate interface version drifted",
        )
        _require(
            SEMVER_RE.fullmatch(record["aggregate_interface_version"]) is not None,
            "aggregate interface version must be exact three-part semver",
        )
        _require(
            record.get("runtime_id_preserved_during_s0") is True,
            "S0 must preserve current runtime identifiers",
        )
        consumers = record.get("current_observed_consumers")
        _require(isinstance(consumers, list), "observed consumers must be a list")
        _require(
            consumers == observed[current_id],
            f"{current_id} consumers must match the current AST graph",
        )
        _require(
            len(consumers) == len(set(consumers)),
            "observed consumers must be unique",
        )
        _require(
            isinstance(record.get("migration_risk"), str)
            and bool(record["migration_risk"].strip()),
            "each mapping needs a migration risk",
        )
        expected_rollback = (
            f"tool-system@{BASE_COMMIT}:{current_id}@{module['module_version']}"
        )
        _require(
            record.get("rollback_identity") == expected_rollback,
            f"{current_id} rollback identity drifted",
        )
        selectors = record.get("python_import_identities")
        _require(
            isinstance(selectors, list) and bool(selectors),
            f"{current_id} needs Python import identities",
        )

    source_owners = _source_owners()
    import_names = {_import_identity(path): owner for path, owner in source_owners.items()}
    selector_match_count: dict[tuple[str, int], int] = {}
    for import_name, expected_owner in import_names.items():
        matches: list[str] = []
        for record in records:
            for index, selector in enumerate(record["python_import_identities"]):
                if _selector_matches(selector, import_name):
                    matches.append(record["current_module_id"])
                    key = (record["current_module_id"], index)
                    selector_match_count[key] = selector_match_count.get(key, 0) + 1
        _require(
            matches == [expected_owner],
            f"{import_name} must map exactly once to its S4 target module owner",
        )
        _require("-" not in import_name, "Python imports must not become formal IDs")

    for record in records:
        for index, _selector in enumerate(record["python_import_identities"]):
            _require(
                selector_match_count.get((record["current_module_id"], index), 0) > 0,
                "every Python identity selector must match current source",
            )


def _validate_adapter_data(data: dict[str, Any]) -> None:
    adapter = data.get("compatibility_adapter")
    _require(isinstance(adapter, dict), "compatibility_adapter is required")
    _require(adapter.get("natural_owner") == MAPPING_OWNER, "adapter owner drifted")
    _require(adapter.get("authority") is False, "adapter cannot be authoritative")
    _require(adapter.get("persistence") == "none", "adapter cannot persist")
    _require(
        adapter.get("translation_boundary") == "memory_only",
        "adapter translation must remain memory-only",
    )
    _require(
        adapter.get("registry_paths_read") == ["config/module_registry_v1.yaml"],
        "adapter must read exactly one registry path",
    )
    for key in (
        "generated_projection",
        "persistent_projection",
        "cache_registry",
        "legacy_registry",
        "second_registry_authority",
        "second_schema_authority",
    ):
        _require(adapter.get(key) is False, f"adapter {key} must remain false")
    _require(adapter.get("removal_stage") == "S11", "adapter removal belongs to S11")
    _require(
        "no_remaining_underscore_formal_ID_callers"
        in adapter.get("exit_conditions", []),
        "adapter exit requires removal of underscore formal-ID callers",
    )


def _validate_reference_data(data: dict[str, Any]) -> None:
    reference_set = data.get("module_owned_contract_references")
    _require(isinstance(reference_set, dict), "ContractReference set is required")
    _require(
        reference_set.get("materialization_stage") == "S3",
        "ContractReferences can materialize only in S3",
    )
    records = reference_set.get("records")
    _require(isinstance(records, list), "ContractReference records must be a list")
    _require(len(records) == 14, "all fourteen ContractReferences are required")
    ids = [record.get("module_id") for record in records]
    _require(len(ids) == len(set(ids)), "ContractReference module IDs must be unique")
    _require(set(ids) == set(_registry_by_id()), "ContractReferences must cover registry")
    unknown_fields = (
        "repo_relative_path",
        "git_blob_sha",
        "sha256",
        "format_identity",
        "schema_identity",
    )
    for record in records:
        if record.get("ready") is True:
            relative = record.get("repo_relative_path")
            _require(
                isinstance(relative, str) and (ROOT / relative).is_file(),
                "a ready ContractReference path must exist",
            )
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            _require(record.get("sha256") == digest, "ready SHA256 must match bytes")
        _require(record.get("ready") is False, "S0 ContractReferences cannot be ready")
        for field in unknown_fields:
            _require(
                record.get(field) == "UNKNOWN",
                f"S0 ContractReference {field} must remain UNKNOWN",
            )


def _validate_non_claims_data(data: dict[str, Any]) -> None:
    non_claims = data.get("non_claims")
    _require(isinstance(non_claims, dict), "non_claims is required")
    _require(bool(non_claims), "non_claims cannot be empty")
    for claim, value in non_claims.items():
        _require(value is False, f"S0 cannot make positive claim: {claim}")


def test_fixed_sources_status_and_dual_anchors_are_exact() -> None:
    sources = _yaml_block("S0-SOURCES")["source_contract"]
    text = _contract_text()

    assert sources["tool_system_repository_commit"] == BASE_COMMIT
    assert sources["tool_system_registry_sha256"] == hashlib.sha256(
        REGISTRY.read_bytes()
    ).hexdigest()
    assert sources["tool_system_local_schema_sha256"] == hashlib.sha256(
        (ROOT / "config" / "module_registry_schema_v1.json").read_bytes()
    ).hexdigest()
    assert sources["blueprint_sha256"] == hashlib.sha256(
        BLUEPRINT.read_bytes()
    ).hexdigest()
    assert sources["blueprint_section"] == "product_objective"
    assert sources["blueprint_product_objective_id"] == load_yaml_file(BLUEPRINT)[
        "product_objective"
    ]["id"]
    assert sources["finance_governance_repository_commit"] == (
        "04ca9d558f59dae17603d7976727aa29782253aa"
    )
    assert sources["finance_governance_schema_sha256"] == (
        "fba270a7ddf8b38dda7cb21263cee8cd96c5b549f0d0b5d364395964b7ecaf67"
    )
    assert "status: S0_IDENTITY_INTERFACE_MAPPING_AUTHORITY" in text
    assert "adoption_state: CANDIDATE_ADOPTION_INPUT" in text
    assert "current_registry_adoption: false" in text
    assert "runtime_activation: false" in text
    assert "central_cutover: false" in text
    assert "accepted TOOL_SYSTEM_MODULE_REGISTRY_ADOPTION_DESIGN_V1" in text
    assert "blueprint/tool_system_v0.yaml:product_objective" in text


def test_mapping_matches_dynamic_registry_and_separates_python_identity() -> None:
    data = _yaml_block("S0-IDENTITY-MAPPING")

    _validate_mapping_data(data)

    records = data["mapping_contract"]["mappings"]
    assert {record["current_module_id"] for record in records} == set(
        _registry_by_id()
    )
    assert all(
        record["canonical_module_id"]
        == record["current_module_id"].replace("_", "-")
        for record in records
    )
    assert all(
        record["canonical_module_id"] != record["current_module_id"]
        for record in records
    )
    target_owners = _source_owners()
    assert {
        relative: target_owners[(ROOT / relative).resolve()]
        for relative in TARGET_OWNER_DELTAS
    } == {
        relative: "task_runner" for relative in TARGET_OWNER_DELTAS
    }


def test_aggregate_interface_identities_and_versions_are_unique() -> None:
    records = _yaml_block("S0-IDENTITY-MAPPING")["mapping_contract"]["mappings"]
    interface_ids = [record["aggregate_interface_id"] for record in records]
    interface_versions = [
        (record["aggregate_interface_id"], record["aggregate_interface_version"])
        for record in records
    ]

    assert len(interface_ids) == len(set(interface_ids)) == 14
    assert len(interface_versions) == len(set(interface_versions)) == 14
    assert all(
        SEMVER_RE.fullmatch(record["aggregate_interface_version"])
        for record in records
    )


def test_static_ast_import_graph_matches_contract_and_declared_dag() -> None:
    dag = _yaml_block("S0-STATIC-DAG")["static_import_dag"]
    observed = _static_provider_consumers()

    assert dag["basis"] == "python_ast_import_nodes_in_s4_target_owned_source"
    assert dag["direction"] == "provider_to_direct_consumer"
    assert dag["providers"] == observed
    assert observed == _declared_provider_consumers()


def test_static_dag_preserves_zero_consumers_and_has_required_non_claim() -> None:
    dag = _yaml_block("S0-STATIC-DAG")["static_import_dag"]
    observed = _static_provider_consumers()
    zero_consumers = sorted(
        module_id for module_id, consumers in observed.items() if not consumers
    )
    non_claim = dag["non_claim"].lower()

    assert sorted(dag["zero_consumer_modules"]) == zero_consumers
    for concept in (
        "dynamic imports",
        "cli",
        "data",
        "configuration",
        "network",
        "hidden dependencies",
    ):
        assert concept in non_claim


def test_adapter_is_non_authoritative_memory_only_and_exits_at_s11() -> None:
    data = _yaml_block("S0-ADAPTER")

    _validate_adapter_data(data)

    adapter = data["compatibility_adapter"]
    assert adapter["implementation_status"] == "NOT_IMPLEMENTED_IN_S0"
    assert adapter["current_formal_registry_owner"] == (
        "config/module_registry_v1.yaml"
    )
    assert "S10_explicit_cutover_accepted" in adapter["exit_conditions"]
    assert "S11_adapter_removal_validation_passes" in adapter["exit_conditions"]


def test_all_module_owned_contract_references_remain_unknown() -> None:
    data = _yaml_block("S0-CONTRACT-REFERENCES")

    _validate_reference_data(data)

    records = data["module_owned_contract_references"]["records"]
    assert all(record["repo_relative_path"] == "UNKNOWN" for record in records)
    assert all(record["git_blob_sha"] == "UNKNOWN" for record in records)
    assert all(record["sha256"] == "UNKNOWN" for record in records)
    assert all(record["ready"] is False for record in records)


def test_manifest_registers_mapping_owner_and_evidence_only_test() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    formal, reasons = _table_rows(text, "## Formal File Sets", FORMAL_COLUMNS)
    rows = {row["path"]: row for row in formal}
    contract_path = "docs/tool_system_module_registry_adoption_contract_v1.md"

    assert reasons == []
    assert text.splitlines().count("## Formal File Sets") == 1
    assert "## Formal Files" not in text.splitlines()
    assert rows[contract_path]["role"] == "S0 formal mapping owner"
    assert rows[contract_path]["owner"] == (
        "tool-system module-registry adoption S0 owner"
    )
    assert "without adopting the registry" in rows[contract_path]["purpose"]
    assert not any(character in contract_path for character in "*?[]{}")
    tests_row = rows["tests/**/*"]
    assert "validation evidence only" in tests_row["purpose"]
    assert "no governance authority" in tests_row["purpose"]
    assert (ROOT / "tests" / "test_module_registry_adoption_contract.py").is_file()


def test_stage_sequence_stops_after_s0_and_non_claims_are_false() -> None:
    text = _contract_text()
    positions = [text.index(f"{index}. S{index - 1} ") for index in range(1, 13)]
    assert positions == sorted(positions)
    assert "S0 completion is a mandatory stop" in text
    assert "Each later stage needs its own authorization" in text

    data = _yaml_block("S0-NON-CLAIMS")
    _validate_non_claims_data(data)
    non_claims = data["non_claims"]
    assert non_claims["current_registry_changed"] is False
    assert non_claims["module_registry_check_executed"] is False
    assert non_claims["module_registry_check_pass_claimed"] is False
    assert non_claims["governance_activated"] is False
    assert non_claims["central_cutover_completed"] is False
    assert non_claims["S1_through_S11_started"] is False


def test_invalid_identity_and_consumer_mappings_are_rejected() -> None:
    original = _yaml_block("S0-IDENTITY-MAPPING")
    invalid_cases: list[dict[str, Any]] = []

    duplicate_current = copy.deepcopy(original)
    duplicate_current["mapping_contract"]["mappings"][1]["current_module_id"] = (
        duplicate_current["mapping_contract"]["mappings"][0]["current_module_id"]
    )
    invalid_cases.append(duplicate_current)

    duplicate_canonical = copy.deepcopy(original)
    duplicate_canonical["mapping_contract"]["mappings"][1]["canonical_module_id"] = (
        duplicate_canonical["mapping_contract"]["mappings"][0][
            "canonical_module_id"
        ]
    )
    invalid_cases.append(duplicate_canonical)

    duplicate_interface = copy.deepcopy(original)
    duplicate_interface["mapping_contract"]["mappings"][1][
        "aggregate_interface_id"
    ] = duplicate_interface["mapping_contract"]["mappings"][0][
        "aggregate_interface_id"
    ]
    invalid_cases.append(duplicate_interface)

    underscore_canonical = copy.deepcopy(original)
    underscore_canonical["mapping_contract"]["mappings"][0][
        "canonical_module_id"
    ] = "architecture_registry"
    invalid_cases.append(underscore_canonical)

    missing_row = copy.deepcopy(original)
    missing_row["mapping_contract"]["mappings"].pop()
    invalid_cases.append(missing_row)

    invented_consumer = copy.deepcopy(original)
    invented_consumer["mapping_contract"]["mappings"][0][
        "current_observed_consumers"
    ] = ["cli_frontend"]
    invalid_cases.append(invented_consumer)

    legacy_broad_gate = copy.deepcopy(original)
    manifest = next(
        record
        for record in legacy_broad_gate["mapping_contract"]["mappings"]
        if record["current_module_id"] == "manifest_validation"
    )
    manifest["python_import_identities"][1] = {
        "kind": "prefix",
        "name": "tool_system.gate",
    }
    invalid_cases.append(legacy_broad_gate)

    duplicate_exact_owner = copy.deepcopy(original)
    manifest = next(
        record
        for record in duplicate_exact_owner["mapping_contract"]["mappings"]
        if record["current_module_id"] == "manifest_validation"
    )
    manifest["python_import_identities"].append(
        {"kind": "exact", "name": "tool_system.gate.command_runner"}
    )
    invalid_cases.append(duplicate_exact_owner)

    legacy_exact_owner = copy.deepcopy(original)
    manifest = next(
        record
        for record in legacy_exact_owner["mapping_contract"]["mappings"]
        if record["current_module_id"] == "manifest_validation"
    )
    task_runner = next(
        record
        for record in legacy_exact_owner["mapping_contract"]["mappings"]
        if record["current_module_id"] == "task_runner"
    )
    transferred_selectors = [
        selector
        for selector in task_runner["python_import_identities"]
        if selector["name"]
        in {
            "tool_system.gate.command_runner",
            "tool_system.gate.test_gate",
        }
    ]
    task_runner["python_import_identities"] = [
        selector
        for selector in task_runner["python_import_identities"]
        if selector not in transferred_selectors
    ]
    manifest["python_import_identities"].extend(transferred_selectors)
    invalid_cases.append(legacy_exact_owner)

    prefix_exact_overlap = copy.deepcopy(original)
    task_runner = next(
        record
        for record in prefix_exact_overlap["mapping_contract"]["mappings"]
        if record["current_module_id"] == "task_runner"
    )
    task_runner["python_import_identities"].append(
        {"kind": "prefix", "name": "tool_system.gate.command_runner"}
    )
    invalid_cases.append(prefix_exact_overlap)

    for invalid in invalid_cases:
        with pytest.raises(AdoptionContractError):
            _validate_mapping_data(invalid)


def test_authoritative_adapter_and_positive_cutover_claims_are_rejected() -> None:
    adapter_data = _yaml_block("S0-ADAPTER")
    adapter_data["compatibility_adapter"]["authority"] = True
    with pytest.raises(AdoptionContractError):
        _validate_adapter_data(adapter_data)

    original = _yaml_block("S0-NON-CLAIMS")
    for key in (
        "module_registry_check_pass_claimed",
        "governance_activated",
        "central_cutover_completed",
    ):
        invalid = copy.deepcopy(original)
        invalid["non_claims"][key] = True
        with pytest.raises(AdoptionContractError):
            _validate_non_claims_data(invalid)


def test_nonexistent_contract_reference_readiness_is_rejected() -> None:
    data = _yaml_block("S0-CONTRACT-REFERENCES")
    record = data["module_owned_contract_references"]["records"][0]
    record.update(
        {
            "repo_relative_path": "docs/does-not-exist-module-contract.md",
            "git_blob_sha": "0" * 40,
            "sha256": "0" * 64,
            "format_identity": "module-contract-v1",
            "schema_identity": "module-contract-schema-v1",
            "ready": True,
        }
    )

    with pytest.raises(AdoptionContractError, match="path must exist"):
        _validate_reference_data(data)
