from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file


MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
INTERFACE_VERSION_RE = re.compile(r"^[1-9][0-9]*$")
LIFECYCLES = {"ACTIVE", "PLANNED", "RETIRED"}
STATUSES = {"REGISTERED", "DEGRADED", "RETIRED"}
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


def validate_module_registry(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    path = Path(registry_path)
    root = Path(repo_root).resolve() if repo_root is not None else path.resolve().parents[1]
    try:
        registry = load_yaml_file(path)
    except (OSError, ValueError) as exc:
        return {
            "status": "BLOCK",
            "registry_path": str(path),
            "module_count": 0,
            "execution_order": [],
            "reasons": [f"unable to read module registry: {exc}"],
        }

    reasons: list[str] = []
    if set(registry) != {"registry_version", "blueprint_objective_ref", "modules"}:
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
