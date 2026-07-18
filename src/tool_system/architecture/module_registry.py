from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from tool_system.manifest.task_manifest import load_yaml_file


MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CANONICAL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
EXACT_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
INTERFACE_VERSION_RE = re.compile(r"^[1-9][0-9]*$")
LEGACY_REGISTRY_INPUT_MODE = "legacy_module_registry"
CENTRAL_COMPATIBILITY_INPUT_MODE = "central_module_registry"
CURRENT_REGISTRY_PATH = "config/module_registry_v1.yaml"
S0_MAPPING_CONTRACT_PATH = (
    "docs/tool_system_module_registry_adoption_contract_v1.md"
)
S0_MAPPING_OWNER = "src/tool_system/architecture/module_registry.py"
LIFECYCLES = {"ACTIVE", "PLANNED", "RETIRED"}
STATUSES = {"REGISTERED", "DEGRADED", "RETIRED"}
LEGACY_TOP_LEVEL_FIELDS = {
    "registry_version",
    "blueprint_objective_ref",
    "modules",
}
CENTRAL_TOP_LEVEL_FIELDS = {
    "registry_contract_version",
    "canonical_repo_id",
    "modules",
    "interfaces",
}
DEPENDENCY_FIELDS = {
    "module_id",
    "module_version",
    "public_interface_version",
}
REQUIRED_MODULE_FIELDS = {
    "module_id",
    "module_version",
    "owner",
    "lifecycle",
    "status",
    "single_responsibility",
    "blueprint_objective_ref",
    "natural_owner_paths",
    "public_interface_version",
    "input_contract",
    "output_contract",
    "error_semantics",
    "externally_visible_side_effects",
    "code_boundary",
    "data_boundary",
    "test_boundary",
    "runtime_artifact_boundary",
    "cleanup_boundary",
    "upstream_dependency_module_ids_and_versions",
    "downstream_dependency_module_ids_and_versions",
    "content_hashes_and_expected_preconditions",
    "authorization_envelope",
    "acceptance_evidence",
    "rollback_evidence",
    "replacement_evidence",
}
CENTRAL_MODULE_FIELDS = {
    "module_id",
    "module_version",
    "role",
    "owner",
    "public_interface_refs",
    "internal_dependencies",
    "external_dependencies",
    "boundaries",
    "permitted_side_effects",
    "rollback_boundary",
    "replacement_boundary",
}
CENTRAL_INTERFACE_FIELDS = {
    "interface_id",
    "interface_version",
    "provider_module_id",
    "consumers",
    "input_contract",
    "output_contract",
    "error_contract",
    "side_effect_contract",
    "compatibility_policy",
    "replacement_revalidation_boundary",
}
CENTRAL_INTERFACE_REF_FIELDS = {"interface_id", "interface_version"}
CENTRAL_BOUNDARY_GROUP_FIELDS = {
    "code",
    "data",
    "tests",
    "runtime_artifacts",
    "cleanup",
}
CENTRAL_CODE_BOUNDARY_FIELDS = {
    "boundary_id",
    "location_kind",
    "path_kind",
    "path",
}
S0_MAPPING_CONTRACT_FIELDS = {
    "mapping_version",
    "module_count",
    "identity_mapping_owner",
    "mappings",
}
S0_MAPPING_RECORD_FIELDS = {
    "current_module_id",
    "canonical_module_id",
    "current_module_version",
    "aggregate_interface_id",
    "aggregate_interface_version",
    "runtime_id_preserved_during_s0",
    "python_import_identities",
    "current_observed_consumers",
    "migration_risk",
    "rollback_identity",
}
NON_EMPTY_LIST_FIELDS = {
    "natural_owner_paths",
    "input_contract",
    "output_contract",
    "error_semantics",
    "externally_visible_side_effects",
    "code_boundary",
    "data_boundary",
    "test_boundary",
    "runtime_artifact_boundary",
    "cleanup_boundary",
    "content_hashes_and_expected_preconditions",
    "authorization_envelope",
    "acceptance_evidence",
    "rollback_evidence",
    "replacement_evidence",
}


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_repo_pattern(value: str) -> bool:
    if value.startswith(("/", "-")) or "\\" in value:
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def _safe_repo_exact_path(value: str) -> bool:
    return (
        _safe_repo_pattern(value)
        and PurePosixPath(value).as_posix() == value
        and not any(character in value for character in "*?[]{}")
    )


def _contract_yaml_block(text: str, name: str) -> dict[str, Any]:
    start = f"<!-- {name}:BEGIN -->\n~~~yaml\n"
    end = f"\n~~~\n<!-- {name}:END -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"{name} must have exactly one YAML block")
    body = text.split(start, 1)[1].split(end, 1)[0]
    value = yaml.safe_load(body)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must decode to a mapping")
    return value


def _validate_s0_mapping_records(
    mapping: dict[str, Any],
) -> list[dict[str, Any]]:
    reasons: list[str] = []
    if set(mapping) != S0_MAPPING_CONTRACT_FIELDS:
        reasons.append("S0 mapping contract fields are incomplete or unrecognized")
    if mapping.get("mapping_version") != "s0-identity-interface-mapping-v1":
        reasons.append("S0 mapping version is not recognized")
    if mapping.get("identity_mapping_owner") != S0_MAPPING_OWNER:
        reasons.append("S0 identity mapping owner does not match the adapter owner")
    raw_records = mapping.get("mappings")
    if not isinstance(raw_records, list) or not raw_records:
        reasons.append("S0 mappings must be a non-empty list")
        raw_records = []

    records: list[dict[str, Any]] = []
    current_ids: set[str] = set()
    canonical_ids: set[str] = set()
    interface_ids: set[str] = set()
    for index, raw_record in enumerate(raw_records):
        label = f"S0 mapping[{index}]"
        if not isinstance(raw_record, dict):
            reasons.append(f"{label} must be a mapping")
            continue
        if set(raw_record) != S0_MAPPING_RECORD_FIELDS:
            reasons.append(f"{label} fields are incomplete or unrecognized")
            continue

        current_id = raw_record.get("current_module_id")
        canonical_id = raw_record.get("canonical_module_id")
        interface_id = raw_record.get("aggregate_interface_id")
        module_version = raw_record.get("current_module_version")
        interface_version = raw_record.get("aggregate_interface_version")
        if (
            not isinstance(current_id, str)
            or MODULE_ID_RE.fullmatch(current_id) is None
        ):
            reasons.append(f"{label}.current_module_id is invalid")
            continue
        if current_id in current_ids:
            reasons.append(f"duplicate S0 current module ID: {current_id}")
        current_ids.add(current_id)
        if (
            not isinstance(canonical_id, str)
            or CANONICAL_ID_RE.fullmatch(canonical_id) is None
        ):
            reasons.append(f"{label}.canonical_module_id is invalid")
            continue
        if canonical_id in canonical_ids:
            reasons.append(f"duplicate S0 canonical module ID: {canonical_id}")
        canonical_ids.add(canonical_id)
        if canonical_id != current_id.replace("_", "-"):
            reasons.append(f"S0 identity mapping collision for {current_id}")
        if (
            not isinstance(interface_id, str)
            or CANONICAL_ID_RE.fullmatch(interface_id) is None
        ):
            reasons.append(f"{label}.aggregate_interface_id is invalid")
            continue
        if interface_id in interface_ids:
            reasons.append(f"duplicate S0 aggregate interface ID: {interface_id}")
        interface_ids.add(interface_id)
        if interface_id != f"{canonical_id}-api":
            reasons.append(f"S0 aggregate interface mapping drifted for {canonical_id}")
        if (
            not isinstance(module_version, str)
            or EXACT_SEMVER_RE.fullmatch(module_version) is None
        ):
            reasons.append(f"{label}.current_module_version is invalid")
        if (
            not isinstance(interface_version, str)
            or EXACT_SEMVER_RE.fullmatch(interface_version) is None
        ):
            reasons.append(f"{label}.aggregate_interface_version is invalid")
        if raw_record.get("runtime_id_preserved_during_s0") is not True:
            reasons.append(f"{label} must preserve the Python runtime ID")

        selectors = raw_record.get("python_import_identities")
        if not isinstance(selectors, list) or not selectors:
            reasons.append(f"{label}.python_import_identities must be non-empty")
        else:
            for selector_index, selector in enumerate(selectors):
                selector_label = (
                    f"{label}.python_import_identities[{selector_index}]"
                )
                if not isinstance(selector, dict) or set(selector) != {
                    "kind",
                    "name",
                }:
                    reasons.append(
                        f"{selector_label} must contain exactly kind and name"
                    )
                    continue
                if selector.get("kind") not in {"exact", "prefix"}:
                    reasons.append(f"{selector_label}.kind is invalid")
                name = selector.get("name")
                if not isinstance(name, str) or not (
                    name == "tool_system"
                    or name.startswith("tool_system.")
                ):
                    reasons.append(f"{selector_label}.name is invalid")

        consumers = raw_record.get("current_observed_consumers")
        if not isinstance(consumers, list) or not all(
            isinstance(consumer, str) for consumer in consumers
        ):
            reasons.append(
                f"{label}.current_observed_consumers must be a string list"
            )
        elif len(consumers) != len(set(consumers)):
            reasons.append(
                f"{label}.current_observed_consumers must be unique"
            )
        if not _non_empty_string(raw_record.get("migration_risk")):
            reasons.append(f"{label}.migration_risk must be non-empty")
        if not _non_empty_string(raw_record.get("rollback_identity")):
            reasons.append(f"{label}.rollback_identity must be non-empty")
        records.append(raw_record)

    if mapping.get("module_count") != len(records):
        reasons.append("S0 module_count does not match the mapping rows")
    for record in records:
        consumers = record.get("current_observed_consumers")
        if isinstance(consumers, list):
            unknown = sorted(set(consumers) - current_ids)
            if unknown:
                reasons.append(
                    "S0 mapping has unknown observed consumers for "
                    f"{record['current_module_id']}: {', '.join(unknown)}"
                )
    if reasons:
        raise ValueError("; ".join(reasons))
    return records


def load_s0_identity_mapping(
    repo_root: str | Path,
) -> list[dict[str, Any]]:
    root = Path(repo_root).resolve()
    contract_path = root / S0_MAPPING_CONTRACT_PATH
    text = contract_path.read_text(encoding="utf-8")
    block = _contract_yaml_block(text, "S0-IDENTITY-MAPPING")
    mapping = block.get("mapping_contract")
    if not isinstance(mapping, dict):
        raise ValueError("S0 mapping_contract is missing")
    return _validate_s0_mapping_records(mapping)


def _source_import_identity(source_root: Path, path: Path) -> str:
    parts = list(path.relative_to(source_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _selector_matches(selector: dict[str, Any], import_name: str) -> bool:
    name = str(selector["name"])
    if selector["kind"] == "exact":
        return import_name == name
    return import_name == name or import_name.startswith(f"{name}.")


def _resolve_from_import_base(
    source_root: Path,
    path: Path,
    node: ast.ImportFrom,
) -> str | None:
    current = _source_import_identity(source_root, path)
    package = current if path.name == "__init__.py" else current.rpartition(".")[0]
    if not node.level:
        return node.module

    parts = package.split(".") if package else []
    ascend = node.level - 1
    if ascend >= len(parts):
        return None
    base_parts = parts[: len(parts) - ascend] if ascend else parts
    if node.module:
        base_parts.extend(node.module.split("."))
    return ".".join(base_parts)


def extract_managed_import_graph(
    repo_root: str | Path,
    owner_by_path: dict[str, str],
    mapping_records: list[dict[str, Any]],
) -> tuple[dict[str, list[str]], list[str]]:
    root = Path(repo_root).resolve()
    source_root = root / "src"
    managed_paths = sorted(
        path
        for path in (source_root / "tool_system").rglob("*.py")
        if path.is_file()
    )
    canonical_ids = {
        str(record["canonical_module_id"]) for record in mapping_records
    }
    graph: dict[str, set[str]] = {
        canonical_id: set() for canonical_id in canonical_ids
    }
    reasons: list[str] = []
    import_name_to_path: dict[str, Path] = {}

    for path in managed_paths:
        relative = path.relative_to(root).as_posix()
        owner = owner_by_path.get(relative)
        if owner not in canonical_ids:
            reasons.append(f"unknown module owner for managed source: {relative}")
        import_name = _source_import_identity(source_root, path)
        previous = import_name_to_path.get(import_name)
        if previous is not None and previous != path:
            reasons.append(f"managed import identity collision: {import_name}")
        else:
            import_name_to_path[import_name] = path

        selector_matches: list[str] = []
        for record in mapping_records:
            canonical_id = str(record["canonical_module_id"])
            for selector in record["python_import_identities"]:
                if _selector_matches(selector, import_name):
                    selector_matches.append(canonical_id)
        if len(selector_matches) != 1:
            reasons.append(
                "managed import identity collision or missing mapping: "
                f"{import_name} maps to {sorted(selector_matches)}"
            )
        elif owner is not None and selector_matches[0] != owner:
            reasons.append(
                f"managed import identity owner mismatch: {import_name} maps to "
                f"{selector_matches[0]} but boundary owner is {owner}"
            )

    hidden_dependencies: set[tuple[str, str]] = set()
    invalid_relative_imports: set[tuple[str, int, str]] = set()
    for path in managed_paths:
        relative = path.relative_to(root).as_posix()
        consumer = owner_by_path.get(relative)
        if consumer not in canonical_ids:
            continue
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )
        except (OSError, SyntaxError) as exc:
            reasons.append(f"unable to parse managed source {relative}: {exc}")
            continue
        imported_targets: set[Path] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = import_name_to_path.get(alias.name)
                    if target is not None:
                        imported_targets.add(target)
                    elif alias.name == "tool_system" or alias.name.startswith(
                        "tool_system."
                    ):
                        hidden_dependencies.add((relative, alias.name))
            elif isinstance(node, ast.ImportFrom):
                base = _resolve_from_import_base(source_root, path, node)
                if base is None:
                    invalid_relative_imports.add(
                        (relative, node.level, node.module or "")
                    )
                    continue
                base_target = import_name_to_path.get(base)
                if base_target is None:
                    if base == "tool_system" or base.startswith(
                        "tool_system."
                    ):
                        hidden_dependencies.add((relative, base))
                    continue
                for alias in node.names:
                    child_target = (
                        import_name_to_path.get(f"{base}.{alias.name}")
                        if alias.name != "*"
                        else None
                    )
                    imported_targets.add(child_target or base_target)
        for target in sorted(imported_targets):
            provider_relative = target.relative_to(root).as_posix()
            provider = owner_by_path.get(provider_relative)
            if provider not in canonical_ids:
                reasons.append(
                    "unknown module owner for imported managed source: "
                    f"{provider_relative}"
                )
                continue
            if provider != consumer:
                graph[provider].add(consumer)

    for relative, import_name in sorted(hidden_dependencies):
        reasons.append(
            f"unmanaged or hidden tool_system dependency in {relative}: "
            f"{import_name}"
        )
    for relative, level, module in sorted(invalid_relative_imports):
        reasons.append(
            f"unresolvable relative import in {relative}: "
            f"level={level}, module={module}"
        )
    return (
        {
            module_id: sorted(consumers)
            for module_id, consumers in sorted(graph.items())
        },
        reasons,
    )


def compare_managed_import_graphs(
    observed_graph: dict[str, list[str]],
    declared_graph: dict[str, list[str]],
) -> list[str]:
    observed_edges = {
        (provider, consumer)
        for provider, consumers in observed_graph.items()
        for consumer in consumers
    }
    declared_edges = {
        (provider, consumer)
        for provider, consumers in declared_graph.items()
        for consumer in consumers
    }
    reasons = [
        f"observed but undeclared managed import edge: {provider} -> {consumer}"
        for provider, consumer in sorted(observed_edges - declared_edges)
    ]
    reasons.extend(
        f"declared but unobserved managed import edge: {provider} -> {consumer}"
        for provider, consumer in sorted(declared_edges - observed_edges)
    )
    return reasons


def _validate_string_list(
    module_id: str,
    module: dict[str, Any],
    field: str,
    reasons: list[str],
) -> list[str]:
    value = module.get(field)
    if not isinstance(value, list) or not value:
        reasons.append(f"{module_id}.{field} must be a non-empty list")
        return []
    if not all(_non_empty_string(item) for item in value):
        reasons.append(f"{module_id}.{field} entries must be non-empty strings")
        return []
    strings = [str(item) for item in value]
    if len(strings) != len(set(strings)):
        reasons.append(f"{module_id}.{field} entries must be unique")
    return strings


def _validate_dependencies(
    module_id: str,
    module: dict[str, Any],
    field: str,
    reasons: list[str],
) -> list[dict[str, str]]:
    value = module.get(field)
    if not isinstance(value, list):
        reasons.append(f"{module_id}.{field} must be a list")
        return []
    dependencies: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, dependency in enumerate(value):
        label = f"{module_id}.{field}[{index}]"
        if not isinstance(dependency, dict):
            reasons.append(f"{label} must be a mapping")
            continue
        if set(dependency) != DEPENDENCY_FIELDS:
            reasons.append(f"{label} must contain exactly {sorted(DEPENDENCY_FIELDS)}")
            continue
        dependency_id = dependency.get("module_id")
        module_version = dependency.get("module_version")
        interface_version = dependency.get("public_interface_version")
        if not isinstance(dependency_id, str) or MODULE_ID_RE.fullmatch(dependency_id) is None:
            reasons.append(f"{label}.module_id is invalid")
            continue
        if not isinstance(module_version, str) or SEMVER_RE.fullmatch(module_version) is None:
            reasons.append(f"{label}.module_version is invalid")
            continue
        if (
            not isinstance(interface_version, str)
            or INTERFACE_VERSION_RE.fullmatch(interface_version) is None
        ):
            reasons.append(f"{label}.public_interface_version is invalid")
            continue
        if dependency_id in seen:
            reasons.append(f"{module_id}.{field} repeats module {dependency_id}")
            continue
        seen.add(dependency_id)
        dependencies.append(
            {
                "module_id": dependency_id,
                "module_version": module_version,
                "public_interface_version": interface_version,
            }
        )
    return dependencies


def _expand_owner_paths(
    repo_root: Path,
    module_id: str,
    patterns: list[str],
    lifecycle: object,
    owner_by_path: dict[str, str],
    reasons: list[str],
) -> None:
    for pattern in patterns:
        if not _safe_repo_pattern(pattern):
            reasons.append(f"{module_id}.natural_owner_paths has unsafe pattern: {pattern}")
            continue
        matches = sorted(
            path
            for path in repo_root.glob(pattern)
            if path.is_file() and ".git" not in path.relative_to(repo_root).parts
        )
        if lifecycle == "ACTIVE" and not matches:
            reasons.append(f"{module_id}.natural_owner_paths has no match: {pattern}")
        for path in matches:
            relative = path.relative_to(repo_root).as_posix()
            if path.is_symlink():
                reasons.append(
                    f"{module_id}.natural_owner_paths must not claim symlink: {relative}"
                )
                continue
            previous = owner_by_path.get(relative)
            if previous is not None and previous != module_id:
                reasons.append(
                    f"natural owner overlap: {relative} belongs to {previous} and {module_id}"
                )
            else:
                owner_by_path[relative] = module_id


def _topological_order(
    module_ids: set[str],
    upstream_ids: dict[str, set[str]],
) -> list[str]:
    downstream: dict[str, set[str]] = {module_id: set() for module_id in module_ids}
    indegree = {module_id: len(upstream_ids[module_id]) for module_id in module_ids}
    for module_id, upstream in upstream_ids.items():
        for dependency_id in upstream:
            if dependency_id in downstream:
                downstream[dependency_id].add(module_id)
    ready = sorted(module_id for module_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        module_id = ready.pop(0)
        order.append(module_id)
        for dependent in sorted(downstream[module_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    return order


def _compatibility_metadata(
    registry_path: Path,
    *,
    applied: bool,
) -> dict[str, object]:
    return {
        "applied": applied,
        "authority": False,
        "persistence": "none",
        "translation_boundary": "memory_only",
        "caller_boundary": "registry_loader_and_validator_entrypoints_only",
        "registry_files_read": [str(registry_path)],
        "mapping_owner_path": S0_MAPPING_CONTRACT_PATH,
        "generated_projection": False,
        "persistent_projection": False,
        "cache_registry": False,
        "serializes_projection": False,
        "second_registry_authority": False,
        "second_schema_authority": False,
        "current_formal_registry_owner": CURRENT_REGISTRY_PATH,
        "removal_stage": "S11",
        "central_schema_compliance_claimed": False,
        "central_gate_compliance_claimed": False,
        "registry_adoption_claimed": False,
        "governance_activation_claimed": False,
    }


def _current_registry_authority(
    registry_path: Path,
    repo_root: Path,
    input_mode: str,
) -> bool:
    candidate = (
        registry_path
        if registry_path.is_absolute()
        else Path.cwd() / registry_path
    ).absolute()
    expected = (repo_root / CURRENT_REGISTRY_PATH).absolute()
    return (
        input_mode == CENTRAL_COMPATIBILITY_INPUT_MODE
        and candidate == expected
        and not candidate.is_symlink()
    )


def _with_compatibility_metadata(
    result: dict[str, object],
    *,
    registry_path: Path,
    repo_root: Path,
    input_mode: str,
) -> dict[str, object]:
    return {
        **result,
        "registry_input_mode": input_mode,
        "current_registry_authority": _current_registry_authority(
            registry_path,
            repo_root,
            input_mode,
        ),
        "validation_scope": (
            "tool_system_current_central_registry"
            if _current_registry_authority(registry_path, repo_root, input_mode)
            else "tool_system_local_compatibility_only"
        ),
        "compatibility_adapter": _compatibility_metadata(
            registry_path,
            applied=input_mode == LEGACY_REGISTRY_INPUT_MODE,
        ),
    }


def _shape_mode(registry: dict[str, Any]) -> tuple[str | None, list[str]]:
    fields = set(registry)
    legacy_unique = LEGACY_TOP_LEVEL_FIELDS - {"modules"}
    central_unique = CENTRAL_TOP_LEVEL_FIELDS - {"modules"}
    has_legacy = bool(fields & legacy_unique)
    has_central = bool(fields & central_unique)
    if has_legacy and has_central:
        return None, ["mixed legacy/central top-level shape is not permitted"]
    if fields == LEGACY_TOP_LEVEL_FIELDS or has_legacy:
        return LEGACY_REGISTRY_INPUT_MODE, []
    if fields == CENTRAL_TOP_LEVEL_FIELDS or has_central:
        return CENTRAL_COMPATIBILITY_INPUT_MODE, []
    return None, ["module registry shape is partial or unrecognized"]


def _central_boundary_paths(
    repo_root: Path,
    module_id: str,
    raw_boundaries: object,
    owner_by_path: dict[str, str],
    reasons: list[str],
) -> None:
    if not isinstance(raw_boundaries, dict):
        reasons.append(f"{module_id}.boundaries must be a mapping")
        return
    if set(raw_boundaries) != CENTRAL_BOUNDARY_GROUP_FIELDS:
        reasons.append(
            f"{module_id}.boundaries fields are incomplete or unrecognized"
        )
    for group in CENTRAL_BOUNDARY_GROUP_FIELDS:
        value = raw_boundaries.get(group)
        if not isinstance(value, list):
            reasons.append(f"{module_id}.boundaries.{group} must be a list")
    code_boundaries = raw_boundaries.get("code")
    if not isinstance(code_boundaries, list) or not code_boundaries:
        reasons.append(f"{module_id}.boundaries.code must be a non-empty list")
        return

    boundary_ids: set[str] = set()
    for index, raw_boundary in enumerate(code_boundaries):
        label = f"{module_id}.boundaries.code[{index}]"
        if not isinstance(raw_boundary, dict):
            reasons.append(f"{label} must be a mapping")
            continue
        if set(raw_boundary) != CENTRAL_CODE_BOUNDARY_FIELDS:
            reasons.append(f"{label} fields are incomplete or unrecognized")
            continue
        boundary_id = raw_boundary.get("boundary_id")
        if (
            not isinstance(boundary_id, str)
            or CANONICAL_ID_RE.fullmatch(boundary_id) is None
        ):
            reasons.append(f"{label}.boundary_id is invalid")
        elif boundary_id in boundary_ids:
            reasons.append(f"{module_id} repeats code boundary ID: {boundary_id}")
        else:
            boundary_ids.add(boundary_id)
        if raw_boundary.get("location_kind") != "repository_local":
            reasons.append(
                f"{label}.location_kind must be repository_local"
            )
        path_kind = raw_boundary.get("path_kind")
        if path_kind not in {"exact", "directory_prefix"}:
            reasons.append(f"{label}.path_kind is invalid")
            continue
        boundary_path = raw_boundary.get("path")
        if (
            not isinstance(boundary_path, str)
            or not _safe_repo_exact_path(boundary_path)
        ):
            reasons.append(f"{label}.path is not a safe exact repository path")
            continue
        absolute = repo_root / boundary_path
        if path_kind == "exact":
            matches = [absolute] if absolute.is_file() else []
        else:
            matches = (
                sorted(path for path in absolute.rglob("*") if path.is_file())
                if absolute.is_dir()
                else []
            )
        if not matches:
            reasons.append(f"{label} has no file match: {boundary_path}")
            continue
        for path in matches:
            relative = path.relative_to(repo_root).as_posix()
            if path.is_symlink():
                reasons.append(f"{label} must not claim symlink: {relative}")
                continue
            previous = owner_by_path.get(relative)
            if previous is not None:
                reasons.append(
                    f"duplicate path owner: {relative} belongs to "
                    f"{previous} and {module_id}"
                )
            else:
                owner_by_path[relative] = module_id


def _iter_central_contract_references(
    registry: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    references: list[tuple[str, dict[str, Any]]] = []
    for module_index, module in enumerate(registry.get("modules", [])):
        if not isinstance(module, dict):
            continue
        base = f"modules[{module_index}]"
        for field in ("rollback_boundary", "replacement_boundary"):
            reference = module.get(field)
            if isinstance(reference, dict):
                references.append((f"{base}.{field}", reference))
        boundaries = module.get("boundaries")
        if isinstance(boundaries, dict):
            for category in CENTRAL_BOUNDARY_GROUP_FIELDS:
                values = boundaries.get(category)
                if not isinstance(values, list):
                    continue
                for boundary_index, boundary in enumerate(values):
                    if isinstance(boundary, dict) and isinstance(
                        boundary.get("root_contract"), dict
                    ):
                        references.append(
                            (
                                f"{base}.boundaries.{category}"
                                f"[{boundary_index}].root_contract",
                                boundary["root_contract"],
                            )
                        )
        effects = module.get("permitted_side_effects")
        if isinstance(effects, list):
            for effect_index, effect in enumerate(effects):
                if isinstance(effect, dict) and isinstance(
                    effect.get("effect_contract"), dict
                ):
                    references.append(
                        (
                            f"{base}.permitted_side_effects"
                            f"[{effect_index}].effect_contract",
                            effect["effect_contract"],
                        )
                    )
    for interface_index, interface in enumerate(registry.get("interfaces", [])):
        if not isinstance(interface, dict):
            continue
        for field in (
            "input_contract",
            "output_contract",
            "error_contract",
            "side_effect_contract",
            "compatibility_policy",
            "replacement_revalidation_boundary",
        ):
            reference = interface.get(field)
            if isinstance(reference, dict):
                references.append(
                    (f"interfaces[{interface_index}].{field}", reference)
                )
    return references


def _validate_central_contract_references(
    registry: dict[str, Any],
    root: Path,
    reasons: list[str],
) -> int:
    required_fields = {
        "repo_relative_path",
        "sha256",
        "format_identity",
        "schema_identity",
    }
    identities_by_path: dict[str, tuple[str, str, str]] = {}
    references = _iter_central_contract_references(registry)
    for location, reference in references:
        if set(reference) != required_fields:
            reasons.append(f"{location} fields are incomplete or unrecognized")
            continue
        relative = reference.get("repo_relative_path")
        digest = reference.get("sha256")
        format_identity = reference.get("format_identity")
        schema_identity = reference.get("schema_identity")
        if not isinstance(relative, str) or not _safe_repo_exact_path(relative):
            reasons.append(f"{location}.repo_relative_path is unsafe")
            continue
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            reasons.append(f"{location}.sha256 is invalid")
            continue
        if not _non_empty_string(format_identity) or not _non_empty_string(
            schema_identity
        ):
            reasons.append(f"{location} contract identity is incomplete")
            continue
        identity = (digest, str(format_identity), str(schema_identity))
        previous = identities_by_path.setdefault(relative, identity)
        if previous != identity:
            reasons.append(f"contract reference identity conflicts for {relative}")
        path = root / relative
        if not path.is_file() or path.is_symlink():
            reasons.append(f"contract reference path is missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            reasons.append(
                f"contract reference SHA256 mismatch: {relative}; "
                f"expected={digest}; actual={actual}"
            )
    return len(references)


def _validate_central_effect_targets(
    module_id: str,
    module: dict[str, Any],
    reasons: list[str],
) -> None:
    boundaries = module.get("boundaries")
    if not isinstance(boundaries, dict):
        return
    boundary_ids: list[str] = []
    for category in CENTRAL_BOUNDARY_GROUP_FIELDS:
        values = boundaries.get(category)
        if isinstance(values, list):
            boundary_ids.extend(
                str(boundary.get("boundary_id"))
                for boundary in values
                if isinstance(boundary, dict)
                and isinstance(boundary.get("boundary_id"), str)
            )
    duplicate_boundaries = sorted(
        boundary_id
        for boundary_id in set(boundary_ids)
        if boundary_ids.count(boundary_id) > 1
    )
    for boundary_id in duplicate_boundaries:
        reasons.append(f"{module_id} repeats boundary ID: {boundary_id}")

    effects = module.get("permitted_side_effects")
    if not isinstance(effects, list):
        return
    effect_ids: list[str] = []
    for index, effect in enumerate(effects):
        if not isinstance(effect, dict):
            reasons.append(f"{module_id}.permitted_side_effects[{index}] must be a mapping")
            continue
        effect_id = effect.get("effect_id")
        if isinstance(effect_id, str):
            effect_ids.append(effect_id)
        target = effect.get("target_boundary_id")
        if not isinstance(target, str) or target not in set(boundary_ids):
            reasons.append(
                f"{module_id}.permitted_side_effects[{index}] references "
                f"unknown target boundary: {target}"
            )
    duplicate_effects = sorted(
        effect_id
        for effect_id in set(effect_ids)
        if effect_ids.count(effect_id) > 1
    )
    for effect_id in duplicate_effects:
        reasons.append(f"{module_id} repeats effect ID: {effect_id}")


def _validate_central_boundary_overlap(
    registry: dict[str, Any],
    root: Path,
    reasons: list[str],
) -> None:
    coverage: dict[str, list[str]] = {}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        module_id = str(module.get("module_id"))
        boundaries = module.get("boundaries")
        if not isinstance(boundaries, dict):
            continue
        for category in CENTRAL_BOUNDARY_GROUP_FIELDS:
            values = boundaries.get(category)
            if not isinstance(values, list):
                continue
            for index, boundary in enumerate(values):
                if not isinstance(boundary, dict) or boundary.get(
                    "location_kind"
                ) != "repository_local":
                    continue
                boundary_path = boundary.get("path")
                path_kind = boundary.get("path_kind")
                if (
                    not isinstance(boundary_path, str)
                    or not _safe_repo_exact_path(boundary_path)
                    or path_kind not in {"exact", "directory_prefix"}
                ):
                    continue
                absolute = root / boundary_path
                if path_kind == "exact":
                    matches = [absolute] if absolute.is_file() else []
                else:
                    matches = (
                        sorted(path for path in absolute.rglob("*") if path.is_file())
                        if absolute.is_dir()
                        else []
                    )
                owner = f"{module_id}:{category}:{index}"
                for path in matches:
                    relative = path.relative_to(root).as_posix()
                    coverage.setdefault(relative, []).append(owner)
    for relative, owners in sorted(coverage.items()):
        if len(owners) > 1:
            reasons.append(
                f"repository-local boundary overlap: {relative} belongs to "
                + " and ".join(sorted(owners))
            )


def _central_interface_reference(
    value: object,
    label: str,
    reasons: list[str],
) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        reasons.append(f"{label} must be a mapping")
        return None
    if set(value) != CENTRAL_INTERFACE_REF_FIELDS:
        reasons.append(f"{label} fields are incomplete or unrecognized")
        return None
    interface_id = value.get("interface_id")
    interface_version = value.get("interface_version")
    if (
        not isinstance(interface_id, str)
        or CANONICAL_ID_RE.fullmatch(interface_id) is None
    ):
        reasons.append(f"{label}.interface_id is invalid")
        return None
    if (
        not isinstance(interface_version, str)
        or EXACT_SEMVER_RE.fullmatch(interface_version) is None
    ):
        reasons.append(f"{label}.interface_version is invalid")
        return None
    return interface_id, interface_version


def _validate_central_registry(
    registry: dict[str, Any],
    path: Path,
    root: Path,
) -> dict[str, object]:
    reasons: list[str] = []
    if set(registry) != CENTRAL_TOP_LEVEL_FIELDS:
        reasons.append(
            "central module registry must contain exactly "
            "registry_contract_version, canonical_repo_id, modules, and interfaces"
        )
    if registry.get("registry_contract_version") != "module_registry_v1":
        reasons.append("registry_contract_version must be module_registry_v1")
    if registry.get("canonical_repo_id") != "tool-system":
        reasons.append("canonical_repo_id must be tool-system")

    try:
        mapping_records = load_s0_identity_mapping(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        mapping_records = []
        reasons.append(f"unable to load the S0 identity mapping owner: {exc}")
    mapping_by_canonical = {
        str(record["canonical_module_id"]): record
        for record in mapping_records
    }
    mapping_by_interface = {
        (
            str(record["aggregate_interface_id"]),
            str(record["aggregate_interface_version"]),
        ): record
        for record in mapping_records
    }
    current_to_canonical = {
        str(record["current_module_id"]): str(record["canonical_module_id"])
        for record in mapping_records
    }

    raw_modules = registry.get("modules")
    if not isinstance(raw_modules, list) or not raw_modules:
        reasons.append("modules must be a non-empty list")
        raw_modules = []
    modules_by_id: dict[str, dict[str, Any]] = {}
    current_ids: set[str] = set()
    owners: set[str] = set()
    owner_by_path: dict[str, str] = {}
    module_dependencies: dict[str, set[tuple[str, str]]] = {}

    for index, raw_module in enumerate(raw_modules):
        label = f"modules[{index}]"
        if not isinstance(raw_module, dict):
            reasons.append(f"{label} must be a mapping")
            continue
        fields = set(raw_module)
        if fields & (REQUIRED_MODULE_FIELDS - CENTRAL_MODULE_FIELDS):
            reasons.append(f"{label} has mixed module field shape")
        if fields != CENTRAL_MODULE_FIELDS:
            reasons.append(f"{label} fields are incomplete or unrecognized")
        module_id = raw_module.get("module_id")
        if (
            not isinstance(module_id, str)
            or CANONICAL_ID_RE.fullmatch(module_id) is None
        ):
            reasons.append(f"{label}.module_id is invalid")
            continue
        if module_id in modules_by_id:
            reasons.append(f"duplicate canonical module ID: {module_id}")
            continue
        modules_by_id[module_id] = raw_module

        mapping = mapping_by_canonical.get(module_id)
        if mapping is None:
            reasons.append(f"missing or unknown S0 mapping for module: {module_id}")
        else:
            current_id = str(mapping["current_module_id"])
            if current_id in current_ids:
                reasons.append(
                    f"duplicate current module ID after mapping: {current_id}"
                )
            current_ids.add(current_id)
            if raw_module.get("module_version") != mapping.get(
                "current_module_version"
            ):
                reasons.append(
                    f"{module_id}.module_version does not match the S0 mapping"
                )
        if not _non_empty_string(raw_module.get("role")):
            reasons.append(f"{module_id}.role must be a non-empty string")
        owner = raw_module.get("owner")
        if not _non_empty_string(owner):
            reasons.append(f"{module_id}.owner must be a non-empty string")
        elif owner in owners:
            reasons.append(f"duplicate central module owner: {owner}")
        else:
            owners.add(str(owner))
        if raw_module.get("external_dependencies") != []:
            reasons.append(
                f"{module_id}.external_dependencies are outside this local adapter"
            )
        for field in ("permitted_side_effects",):
            if not isinstance(raw_module.get(field), list):
                reasons.append(f"{module_id}.{field} must be a list")
        for field in ("rollback_boundary", "replacement_boundary"):
            if not isinstance(raw_module.get(field), dict):
                reasons.append(f"{module_id}.{field} must be a mapping")

        public_refs = raw_module.get("public_interface_refs")
        if not isinstance(public_refs, list) or len(public_refs) != 1:
            reasons.append(
                f"{module_id}.public_interface_refs must contain exactly one "
                "S0 aggregate interface"
            )
        else:
            reference = _central_interface_reference(
                public_refs[0],
                f"{module_id}.public_interface_refs[0]",
                reasons,
            )
            if mapping is not None and reference != (
                mapping["aggregate_interface_id"],
                mapping["aggregate_interface_version"],
            ):
                reasons.append(
                    f"{module_id}.public_interface_refs does not match the S0 mapping"
                )

        dependencies = raw_module.get("internal_dependencies")
        parsed_dependencies: set[tuple[str, str]] = set()
        if not isinstance(dependencies, list):
            reasons.append(f"{module_id}.internal_dependencies must be a list")
        else:
            for dependency_index, dependency in enumerate(dependencies):
                reference = _central_interface_reference(
                    dependency,
                    (
                        f"{module_id}.internal_dependencies"
                        f"[{dependency_index}]"
                    ),
                    reasons,
                )
                if reference is None:
                    continue
                if reference in parsed_dependencies:
                    reasons.append(
                        f"{module_id}.internal_dependencies repeats "
                        f"{reference[0]}@{reference[1]}"
                    )
                parsed_dependencies.add(reference)
        module_dependencies[module_id] = parsed_dependencies
        _central_boundary_paths(
            root,
            module_id,
            raw_module.get("boundaries"),
            owner_by_path,
            reasons,
        )
        _validate_central_effect_targets(module_id, raw_module, reasons)

    expected_canonical_ids = set(mapping_by_canonical)
    missing_modules = sorted(expected_canonical_ids - set(modules_by_id))
    if missing_modules:
        reasons.append(
            "central registry is missing S0 mapped modules: "
            + ", ".join(missing_modules)
        )

    raw_interfaces = registry.get("interfaces")
    if not isinstance(raw_interfaces, list) or not raw_interfaces:
        reasons.append("interfaces must be a non-empty list")
        raw_interfaces = []
    interfaces: dict[tuple[str, str], dict[str, Any]] = {}
    interface_consumers: dict[tuple[str, str], set[str]] = {}
    for index, raw_interface in enumerate(raw_interfaces):
        label = f"interfaces[{index}]"
        if not isinstance(raw_interface, dict):
            reasons.append(f"{label} must be a mapping")
            continue
        if set(raw_interface) != CENTRAL_INTERFACE_FIELDS:
            reasons.append(f"{label} fields are incomplete or unrecognized")
        interface_id = raw_interface.get("interface_id")
        interface_version = raw_interface.get("interface_version")
        if (
            not isinstance(interface_id, str)
            or CANONICAL_ID_RE.fullmatch(interface_id) is None
            or not isinstance(interface_version, str)
            or EXACT_SEMVER_RE.fullmatch(interface_version) is None
        ):
            reasons.append(f"{label} interface identity is invalid")
            continue
        key = (interface_id, interface_version)
        if key in interfaces:
            reasons.append(
                f"duplicate central interface identity: "
                f"{interface_id}@{interface_version}"
            )
            continue
        interfaces[key] = raw_interface
        mapping = mapping_by_interface.get(key)
        if mapping is None:
            reasons.append(
                f"missing or unknown S0 mapping for interface: "
                f"{interface_id}@{interface_version}"
            )
        provider_id = raw_interface.get("provider_module_id")
        if (
            not isinstance(provider_id, str)
            or CANONICAL_ID_RE.fullmatch(provider_id) is None
        ):
            reasons.append(
                f"{interface_id}.provider_module_id is invalid"
            )
        elif provider_id not in modules_by_id:
            reasons.append(
                f"{interface_id} references unknown provider module: {provider_id}"
            )
        elif mapping is not None and provider_id != mapping.get(
            "canonical_module_id"
        ):
            reasons.append(
                f"{interface_id}.provider_module_id does not match the S0 mapping"
            )
        consumers = raw_interface.get("consumers")
        local_consumers: set[str] = set()
        if not isinstance(consumers, list):
            reasons.append(f"{interface_id}.consumers must be a list")
        else:
            for consumer_index, consumer in enumerate(consumers):
                consumer_label = (
                    f"{interface_id}.consumers[{consumer_index}]"
                )
                if not isinstance(consumer, dict) or set(consumer) != {
                    "consumer_module_id"
                }:
                    reasons.append(
                        f"{consumer_label} must be one closed local consumer"
                    )
                    continue
                consumer_id = consumer.get("consumer_module_id")
                if (
                    not isinstance(consumer_id, str)
                    or CANONICAL_ID_RE.fullmatch(consumer_id) is None
                ):
                    reasons.append(
                        f"{consumer_label}.consumer_module_id is invalid"
                    )
                    continue
                if consumer_id not in modules_by_id:
                    reasons.append(
                        f"{interface_id} references unknown consumer module: "
                        f"{consumer_id}"
                    )
                    continue
                if consumer_id in local_consumers:
                    reasons.append(
                        f"{interface_id} repeats consumer module: {consumer_id}"
                    )
                local_consumers.add(str(consumer_id))
        interface_consumers[key] = local_consumers

    missing_interfaces = sorted(set(mapping_by_interface) - set(interfaces))
    if missing_interfaces:
        reasons.append(
            "central registry is missing S0 mapped interfaces: "
            + ", ".join(
                f"{interface_id}@{version}"
                for interface_id, version in missing_interfaces
            )
        )

    declared_graph: dict[str, set[str]] = {
        module_id: set() for module_id in modules_by_id
    }
    upstream_ids: dict[str, set[str]] = {
        module_id: set() for module_id in modules_by_id
    }
    dependency_consumers: dict[tuple[str, str], set[str]] = {
        key: set() for key in interfaces
    }
    for consumer_id, dependencies in module_dependencies.items():
        for dependency in dependencies:
            interface = interfaces.get(dependency)
            if interface is None:
                reasons.append(
                    f"{consumer_id} references unknown internal interface: "
                    f"{dependency[0]}@{dependency[1]}"
                )
                continue
            provider_id = interface.get("provider_module_id")
            if not isinstance(provider_id, str) or provider_id not in modules_by_id:
                continue
            if provider_id == consumer_id:
                reasons.append(f"{consumer_id} cannot depend on itself")
                continue
            declared_graph[provider_id].add(consumer_id)
            upstream_ids[consumer_id].add(provider_id)
            dependency_consumers[dependency].add(consumer_id)
    for key in sorted(set(interfaces) | set(dependency_consumers)):
        if interface_consumers.get(key, set()) != dependency_consumers.get(
            key,
            set(),
        ):
            reasons.append(
                f"{key[0]}@{key[1]} provider/consumer declarations do not close"
            )

    required_owned_paths = {
        source.relative_to(root).as_posix()
        for source in (root / "src" / "tool_system").rglob("*.py")
        if source.is_file()
    }
    required_owned_paths.update(
        relative
        for relative in (
            "config/module_registry_schema_v1.json",
            CURRENT_REGISTRY_PATH,
        )
        if (root / relative).is_file()
    )
    for relative in sorted(required_owned_paths - set(owner_by_path)):
        reasons.append(f"required module-owned path is unclaimed: {relative}")

    observed_graph, import_reasons = extract_managed_import_graph(
        root,
        owner_by_path,
        mapping_records,
    )
    reasons.extend(import_reasons)
    declared_graph_lists = {
        module_id: sorted(consumers)
        for module_id, consumers in sorted(declared_graph.items())
    }
    reasons.extend(
        compare_managed_import_graphs(
            observed_graph,
            declared_graph_lists,
        )
    )

    for record in mapping_records:
        provider = str(record["canonical_module_id"])
        expected_consumers = sorted(
            current_to_canonical[current]
            for current in record["current_observed_consumers"]
            if current in current_to_canonical
        )
        if observed_graph.get(provider, []) != expected_consumers:
            reasons.append(
                f"managed import graph does not match the S0 mapping for {provider}"
            )

    execution_order = _topological_order(set(modules_by_id), upstream_ids)
    if len(execution_order) != len(modules_by_id):
        reasons.append("module dependency graph must be acyclic")

    contract_reference_count = _validate_central_contract_references(
        registry,
        root,
        reasons,
    )
    _validate_central_boundary_overlap(registry, root, reasons)

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "registry_path": str(path),
        "module_count": len(modules_by_id),
        "execution_order": execution_order,
        "owned_path_count": len(owner_by_path),
        "required_owned_path_count": len(required_owned_paths),
        "contract_reference_count": contract_reference_count,
        "external_provider_count": 0,
        "declared_import_graph": declared_graph_lists,
        "observed_import_graph": observed_graph,
        "reasons": reasons,
    }


def _validate_legacy_registry(
    registry: dict[str, Any],
    path: Path,
    root: Path,
) -> dict[str, object]:
    reasons: list[str] = []
    if set(registry) != LEGACY_TOP_LEVEL_FIELDS:
        reasons.append(
            "module registry must contain exactly registry_version, "
            "blueprint_objective_ref, and modules"
        )
    if registry.get("registry_version") != "module_registry_v1":
        reasons.append("registry_version must be module_registry_v1")
    if registry.get("blueprint_objective_ref") != "product_objective":
        reasons.append("blueprint_objective_ref must be product_objective")
    raw_modules = registry.get("modules")
    if not isinstance(raw_modules, list) or not raw_modules:
        reasons.append("modules must be a non-empty list")
        raw_modules = []

    modules_by_id: dict[str, dict[str, Any]] = {}
    upstream_records: dict[str, list[dict[str, str]]] = {}
    downstream_records: dict[str, list[dict[str, str]]] = {}
    owner_by_path: dict[str, str] = {}

    for index, raw_module in enumerate(raw_modules):
        if not isinstance(raw_module, dict):
            reasons.append(f"modules[{index}] must be a mapping")
            continue
        if set(raw_module) & (CENTRAL_MODULE_FIELDS - REQUIRED_MODULE_FIELDS):
            reasons.append(f"modules[{index}] has mixed module field shape")
        module_id_value = raw_module.get("module_id")
        module_id = (
            str(module_id_value)
            if isinstance(module_id_value, str)
            else f"modules[{index}]"
        )
        if set(raw_module) != REQUIRED_MODULE_FIELDS:
            reasons.append(f"{module_id} must contain exactly the registered module fields")
        if not isinstance(module_id_value, str) or MODULE_ID_RE.fullmatch(module_id_value) is None:
            reasons.append(f"{module_id}.module_id is invalid")
            continue
        if module_id in modules_by_id:
            reasons.append(f"duplicate module_id: {module_id}")
            continue
        modules_by_id[module_id] = raw_module

        module_version = raw_module.get("module_version")
        if not isinstance(module_version, str) or SEMVER_RE.fullmatch(module_version) is None:
            reasons.append(f"{module_id}.module_version is invalid")
        interface_version = raw_module.get("public_interface_version")
        if (
            not isinstance(interface_version, str)
            or INTERFACE_VERSION_RE.fullmatch(interface_version) is None
        ):
            reasons.append(f"{module_id}.public_interface_version is invalid")
        for field in ("owner", "single_responsibility"):
            if not _non_empty_string(raw_module.get(field)):
                reasons.append(f"{module_id}.{field} must be a non-empty string")
        if raw_module.get("lifecycle") not in LIFECYCLES:
            reasons.append(f"{module_id}.lifecycle is not registered")
        if raw_module.get("status") not in STATUSES:
            reasons.append(f"{module_id}.status is not registered")
        if raw_module.get("blueprint_objective_ref") != "product_objective":
            reasons.append(f"{module_id}.blueprint_objective_ref must be product_objective")

        string_lists = {
            field: _validate_string_list(module_id, raw_module, field, reasons)
            for field in NON_EMPTY_LIST_FIELDS
        }
        _expand_owner_paths(
            root,
            module_id,
            string_lists["natural_owner_paths"],
            raw_module.get("lifecycle"),
            owner_by_path,
            reasons,
        )
        upstream_records[module_id] = _validate_dependencies(
            module_id,
            raw_module,
            "upstream_dependency_module_ids_and_versions",
            reasons,
        )
        downstream_records[module_id] = _validate_dependencies(
            module_id,
            raw_module,
            "downstream_dependency_module_ids_and_versions",
            reasons,
        )

    module_ids = set(modules_by_id)
    upstream_ids: dict[str, set[str]] = {module_id: set() for module_id in module_ids}
    declared_downstream: dict[str, set[str]] = {module_id: set() for module_id in module_ids}
    expected_downstream: dict[str, set[str]] = {module_id: set() for module_id in module_ids}

    for module_id, dependencies in upstream_records.items():
        for dependency in dependencies:
            dependency_id = dependency["module_id"]
            if dependency_id == module_id:
                reasons.append(f"{module_id} cannot depend on itself")
                continue
            target = modules_by_id.get(dependency_id)
            if target is None:
                reasons.append(f"{module_id} references unknown upstream module: {dependency_id}")
                continue
            if dependency["module_version"] != target.get("module_version"):
                reasons.append(f"{module_id} has stale module_version for {dependency_id}")
            if dependency["public_interface_version"] != target.get("public_interface_version"):
                reasons.append(
                    f"{module_id} has stale public_interface_version for {dependency_id}"
                )
            upstream_ids[module_id].add(dependency_id)
            expected_downstream[dependency_id].add(module_id)

    for module_id, dependencies in downstream_records.items():
        for dependency in dependencies:
            dependency_id = dependency["module_id"]
            target = modules_by_id.get(dependency_id)
            if target is None:
                reasons.append(
                    f"{module_id} references unknown downstream module: {dependency_id}"
                )
                continue
            if dependency["module_version"] != target.get("module_version"):
                reasons.append(
                    f"{module_id} has stale downstream module_version for {dependency_id}"
                )
            if dependency["public_interface_version"] != target.get("public_interface_version"):
                reasons.append(
                    f"{module_id} has stale downstream public_interface_version "
                    f"for {dependency_id}"
                )
            declared_downstream[module_id].add(dependency_id)

    for module_id in sorted(module_ids):
        if declared_downstream[module_id] != expected_downstream[module_id]:
            reasons.append(
                f"{module_id}.downstream dependencies do not match reciprocal "
                "upstream declarations"
            )

    required_owned_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "src" / "tool_system").rglob("*.py")
        if path.is_file()
    }
    required_owned_paths.update(
        relative
        for relative in (
            "config/module_registry_schema_v1.json",
            "config/module_registry_v1.yaml",
        )
        if (root / relative).is_file()
    )
    for relative in sorted(required_owned_paths - set(owner_by_path)):
        reasons.append(f"required module-owned path is unclaimed: {relative}")

    execution_order = _topological_order(module_ids, upstream_ids)
    if len(execution_order) != len(module_ids):
        reasons.append("module dependency graph must be acyclic")

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "registry_path": str(path),
        "module_count": len(modules_by_id),
        "execution_order": execution_order,
        "owned_path_count": len(owner_by_path),
        "required_owned_path_count": len(required_owned_paths),
        "reasons": reasons,
    }


def validate_module_registry(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    require_current_authority: bool = False,
) -> dict[str, object]:
    path = Path(registry_path)
    root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else path.resolve().parents[1]
    )
    try:
        registry = load_yaml_file(path)
    except (OSError, ValueError) as exc:
        return {
            "status": "BLOCK",
            "registry_path": str(path),
            "module_count": 0,
            "execution_order": [],
            "reasons": [f"unable to read module registry: {exc}"],
            "registry_input_mode": "unrecognized",
            "current_registry_authority": False,
            "validation_scope": "none",
            "compatibility_adapter": _compatibility_metadata(
                path,
                applied=False,
            ),
        }

    input_mode, shape_reasons = _shape_mode(registry)
    if input_mode is None:
        return {
            "status": "BLOCK",
            "registry_path": str(path),
            "module_count": 0,
            "execution_order": [],
            "owned_path_count": 0,
            "required_owned_path_count": 0,
            "reasons": shape_reasons,
            "registry_input_mode": "unrecognized",
            "current_registry_authority": False,
            "validation_scope": "none",
            "compatibility_adapter": _compatibility_metadata(
                path,
                applied=False,
            ),
        }

    if input_mode == LEGACY_REGISTRY_INPUT_MODE:
        result = _validate_legacy_registry(registry, path, root)
    else:
        result = _validate_central_registry(registry, path, root)
    result = _with_compatibility_metadata(
        result,
        registry_path=path,
        repo_root=root,
        input_mode=input_mode,
    )
    if require_current_authority and not result["current_registry_authority"]:
        result["status"] = "BLOCK"
        result["reasons"] = [
            *list(result["reasons"]),
            "non-authoritative compatibility result cannot satisfy current "
            "registry authority",
        ]
    return result
