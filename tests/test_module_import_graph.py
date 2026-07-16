from __future__ import annotations

import ast
import copy
from pathlib import Path

import yaml

from test_module_registry import central_registry_fixture
from tool_system.architecture.module_registry import (
    compare_managed_import_graphs,
    extract_managed_import_graph,
    load_s0_identity_mapping,
    validate_module_registry,
)
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
SOURCE_ROOT = ROOT / "src"


def _source_identity(path: Path) -> str:
    parts = list(path.relative_to(SOURCE_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _from_imports(path: Path, node: ast.ImportFrom) -> list[str]:
    current = _source_identity(path)
    package = current if path.name == "__init__.py" else current.rpartition(".")[0]
    if node.level:
        parts = package.split(".") if package else []
        ascend = node.level - 1
        if ascend > len(parts):
            return []
        parts = parts[: len(parts) - ascend] if ascend else parts
        if node.module:
            parts.append(node.module)
        base = ".".join(parts)
    else:
        base = node.module or ""
    return [
        f"{base}.{alias.name}" if base else alias.name
        for alias in node.names
        if alias.name != "*"
    ]


def _current_boundaries() -> tuple[
    dict[str, str],
    dict[str, list[str]],
]:
    registry = load_yaml_file(REGISTRY)
    mappings = load_s0_identity_mapping(ROOT)
    canonical_by_current = {
        mapping["current_module_id"]: mapping["canonical_module_id"]
        for mapping in mappings
    }
    owner_by_path: dict[str, str] = {}
    declared: dict[str, set[str]] = {
        mapping["canonical_module_id"]: set() for mapping in mappings
    }
    for module in registry["modules"]:
        current_id = module["module_id"]
        canonical_id = canonical_by_current[current_id]
        for pattern in module["natural_owner_paths"]:
            for path in ROOT.glob(pattern):
                if not path.is_file() or not path.is_relative_to(
                    ROOT / "src" / "tool_system"
                ) or path.suffix != ".py":
                    continue
                relative = path.relative_to(ROOT).as_posix()
                assert relative not in owner_by_path
                owner_by_path[relative] = canonical_id
        for dependency in module[
            "upstream_dependency_module_ids_and_versions"
        ]:
            provider = canonical_by_current[dependency["module_id"]]
            declared[provider].add(canonical_id)
    return (
        owner_by_path,
        {
            provider: sorted(consumers)
            for provider, consumers in sorted(declared.items())
        },
    )


def _independent_observed_graph(
    owner_by_path: dict[str, str],
) -> dict[str, list[str]]:
    paths = sorted((SOURCE_ROOT / "tool_system").rglob("*.py"))
    by_identity = {_source_identity(path): path for path in paths}
    assert len(by_identity) == len(paths)
    identities = sorted(by_identity, key=len, reverse=True)
    graph: dict[str, set[str]] = {
        owner: set() for owner in owner_by_path.values()
    }

    def resolve(name: str) -> Path | None:
        for identity in identities:
            if name == identity or name.startswith(f"{identity}."):
                return by_identity[identity]
        return None

    for path in paths:
        consumer = owner_by_path[path.relative_to(ROOT).as_posix()]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_names.extend(_from_imports(path, node))
        for name in imported_names:
            target = resolve(name)
            if target is None:
                continue
            provider = owner_by_path[target.relative_to(ROOT).as_posix()]
            if provider != consumer:
                graph[provider].add(consumer)
    return {
        provider: sorted(consumers)
        for provider, consumers in sorted(graph.items())
    }


def _s0_declared_graph() -> dict[str, list[str]]:
    mappings = load_s0_identity_mapping(ROOT)
    canonical_by_current = {
        mapping["current_module_id"]: mapping["canonical_module_id"]
        for mapping in mappings
    }
    return {
        mapping["canonical_module_id"]: sorted(
            canonical_by_current[consumer]
            for consumer in mapping["current_observed_consumers"]
        )
        for mapping in mappings
    }


def _write_central_fixture(tmp_path: Path, registry: object) -> Path:
    path = tmp_path / "central_module_registry_fixture.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def test_real_managed_import_dag_matches_boundaries_s0_and_declarations() -> None:
    owner_by_path, declared_graph = _current_boundaries()
    independent_graph = _independent_observed_graph(owner_by_path)
    production_graph, reasons = extract_managed_import_graph(
        ROOT,
        owner_by_path,
        load_s0_identity_mapping(ROOT),
    )

    assert reasons == []
    assert len(owner_by_path) == len(
        list((ROOT / "src" / "tool_system").rglob("*.py"))
    )
    assert independent_graph == production_graph
    assert independent_graph == declared_graph
    assert independent_graph == _s0_declared_graph()


def test_observed_but_undeclared_real_edge_blocks() -> None:
    owner_by_path, declared_graph = _current_boundaries()
    observed_graph = _independent_observed_graph(owner_by_path)
    declared_graph["manifest-validation"].remove("architecture-registry")

    reasons = compare_managed_import_graphs(observed_graph, declared_graph)

    assert reasons == [
        "observed but undeclared managed import edge: "
        "manifest-validation -> architecture-registry"
    ]


def test_declared_but_unobserved_real_edge_blocks() -> None:
    owner_by_path, declared_graph = _current_boundaries()
    observed_graph = _independent_observed_graph(owner_by_path)
    declared_graph["architecture-registry"].append("ai-worker-runtime")

    reasons = compare_managed_import_graphs(observed_graph, declared_graph)

    assert reasons == [
        "declared but unobserved managed import edge: "
        "architecture-registry -> ai-worker-runtime"
    ]


def test_unknown_managed_module_owner_blocks() -> None:
    owner_by_path, _ = _current_boundaries()
    owner_by_path.pop("src/tool_system/ai_worker/__init__.py")

    _, reasons = extract_managed_import_graph(
        ROOT,
        owner_by_path,
        load_s0_identity_mapping(ROOT),
    )

    assert (
        "unknown module owner for managed source: "
        "src/tool_system/ai_worker/__init__.py"
    ) in reasons


def test_duplicate_central_path_owner_blocks(tmp_path: Path) -> None:
    registry = central_registry_fixture()
    duplicate = copy.deepcopy(registry["modules"][0]["boundaries"]["code"][0])
    registry["modules"][1]["boundaries"]["code"].append(duplicate)

    result = validate_module_registry(
        _write_central_fixture(tmp_path, registry),
        ROOT,
    )

    assert result["status"] == "BLOCK"
    assert any(
        reason.startswith("duplicate path owner:")
        for reason in result["reasons"]
    )


def test_import_identity_collision_blocks() -> None:
    owner_by_path, _ = _current_boundaries()
    mappings = copy.deepcopy(load_s0_identity_mapping(ROOT))
    mappings[0]["python_import_identities"].append(
        {"kind": "exact", "name": "tool_system.ai_worker"}
    )

    _, reasons = extract_managed_import_graph(ROOT, owner_by_path, mappings)

    assert any(
        reason.startswith("managed import identity collision")
        for reason in reasons
    )


def test_unmanaged_hidden_dependency_blocks(tmp_path: Path) -> None:
    source = tmp_path / "src" / "tool_system" / "managed.py"
    source.parent.mkdir(parents=True)
    source.write_text("import tool_system.hidden\n", encoding="utf-8")
    owner_by_path = {
        "src/tool_system/managed.py": "managed-module",
    }
    mappings = [
        {
            "canonical_module_id": "managed-module",
            "python_import_identities": [
                {"kind": "exact", "name": "tool_system.managed"}
            ],
        }
    ]

    _, reasons = extract_managed_import_graph(
        tmp_path,
        owner_by_path,
        mappings,
    )

    assert reasons == [
        "unmanaged or hidden tool_system dependency in "
        "src/tool_system/managed.py: tool_system.hidden"
    ]
