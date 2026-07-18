from __future__ import annotations

import ast
import copy
from pathlib import Path

import yaml

from test_module_registry import (
    EXPECTED_MANAGED_PYTHON_FILE_COUNT,
    TARGET_OWNER_DELTAS,
    central_registry_fixture,
    target_python_owner_by_path,
)
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


def _source_identity(
    path: Path,
    source_root: Path = SOURCE_ROOT,
) -> str:
    parts = list(path.relative_to(source_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _from_import_base(path: Path, node: ast.ImportFrom) -> str | None:
    current = _source_identity(path)
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


def _current_boundaries() -> tuple[
    dict[str, str],
    dict[str, list[str]],
]:
    registry = load_yaml_file(REGISTRY)
    owner_by_path = {
        path: str(mapping["canonical_module_id"])
        for path, current_owner in target_python_owner_by_path().items()
        for mapping in load_s0_identity_mapping(ROOT)
        if mapping["current_module_id"] == current_owner
    }
    declared: dict[str, set[str]] = {
        str(module["module_id"]): set() for module in registry["modules"]
    }
    provider_by_interface = {
        (interface["interface_id"], interface["interface_version"]): interface[
            "provider_module_id"
        ]
        for interface in registry["interfaces"]
    }
    for module in registry["modules"]:
        canonical_id = str(module["module_id"])
        for dependency in module["internal_dependencies"]:
            provider = provider_by_interface[
                (dependency["interface_id"], dependency["interface_version"])
            ]
            declared[str(provider)].add(canonical_id)
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
    graph: dict[str, set[str]] = {
        owner: set() for owner in owner_by_path.values()
    }

    for path in paths:
        consumer = owner_by_path[path.relative_to(ROOT).as_posix()]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_targets: set[Path] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "tool_system" or alias.name.startswith(
                        "tool_system."
                    ):
                        assert alias.name in by_identity
                        imported_targets.add(by_identity[alias.name])
            elif isinstance(node, ast.ImportFrom):
                base = _from_import_base(path, node)
                assert base is not None
                if base != "tool_system" and not base.startswith(
                    "tool_system."
                ):
                    continue
                assert base in by_identity
                for alias in node.names:
                    child = (
                        f"{base}.{alias.name}"
                        if alias.name != "*"
                        else ""
                    )
                    imported_targets.add(
                        by_identity[child]
                        if child in by_identity
                        else by_identity[base]
                    )
        for target in imported_targets:
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


def _fixture_graph(
    tmp_path: Path,
    sources: dict[str, tuple[str, str]],
) -> tuple[dict[str, list[str]], list[str]]:
    source_root = tmp_path / "src"
    owner_by_path: dict[str, str] = {}
    identities_by_owner: dict[str, list[str]] = {}
    for relative, (owner, source) in sources.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        owner_by_path[relative] = owner
        identities_by_owner.setdefault(owner, []).append(
            _source_identity(path, source_root)
        )
    mappings = [
        {
            "canonical_module_id": owner,
            "python_import_identities": [
                {"kind": "exact", "name": identity}
                for identity in sorted(identities)
            ],
        }
        for owner, identities in sorted(identities_by_owner.items())
    ]
    return extract_managed_import_graph(tmp_path, owner_by_path, mappings)


def test_real_managed_import_dag_matches_boundaries_s0_and_declarations() -> None:
    owner_by_path, declared_graph = _current_boundaries()
    independent_graph = _independent_observed_graph(owner_by_path)
    production_graph, reasons = extract_managed_import_graph(
        ROOT,
        owner_by_path,
        load_s0_identity_mapping(ROOT),
    )

    assert reasons == []
    assert len(owner_by_path) == EXPECTED_MANAGED_PYTHON_FILE_COUNT
    assert len(list((ROOT / "src" / "tool_system").rglob("*.py"))) == (
        EXPECTED_MANAGED_PYTHON_FILE_COUNT
    )
    assert {
        path: owner_by_path[path] for path in TARGET_OWNER_DELTAS
    } == {
        path: "task-runner" for path in TARGET_OWNER_DELTAS
    }
    assert independent_graph == production_graph
    assert independent_graph == declared_graph
    assert independent_graph == _s0_declared_graph()


def test_exact_file_module_import_passes(tmp_path: Path) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/provider.py": ("provider-module", ""),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "import tool_system.provider\n",
            ),
        },
    )

    assert reasons == []
    assert graph["provider-module"] == ["consumer-module"]
    assert graph["root-package"] == []


def test_exact_package_import_passes(tmp_path: Path) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/provider/__init__.py": ("provider-package", ""),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "import tool_system.provider\n",
            ),
        },
    )

    assert reasons == []
    assert graph["provider-package"] == ["consumer-module"]
    assert graph["root-package"] == []


def test_existing_package_missing_child_import_blocks(tmp_path: Path) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/provider/__init__.py": ("provider-package", ""),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "import tool_system.provider.hidden\n",
            ),
        },
    )

    assert graph["provider-package"] == []
    assert graph["root-package"] == []
    assert reasons == [
        "unmanaged or hidden tool_system dependency in "
        "src/tool_system/consumer.py: tool_system.provider.hidden"
    ]


def test_import_from_symbol_without_child_resolves_to_base(
    tmp_path: Path,
) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/provider/__init__.py": (
                "provider-package",
                "exported_symbol = object()\n",
            ),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "from tool_system.provider import exported_symbol\n",
            ),
        },
    )

    assert reasons == []
    assert graph["provider-package"] == ["consumer-module"]
    assert graph["root-package"] == []


def test_import_from_existing_child_resolves_to_child(
    tmp_path: Path,
) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/provider/__init__.py": ("provider-package", ""),
            "src/tool_system/provider/child.py": ("child-module", ""),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "from tool_system.provider import child\n",
            ),
        },
    )

    assert reasons == []
    assert graph["child-module"] == ["consumer-module"]
    assert graph["provider-package"] == []


def test_missing_import_from_base_blocks(tmp_path: Path) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/consumer.py": (
                "consumer-module",
                "from tool_system.hidden import exported_symbol\n",
            ),
        },
    )

    assert graph["root-package"] == []
    assert reasons == [
        "unmanaged or hidden tool_system dependency in "
        "src/tool_system/consumer.py: tool_system.hidden"
    ]


def test_missing_relative_import_from_base_blocks(tmp_path: Path) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/package/__init__.py": ("package-module", ""),
            "src/tool_system/package/consumer.py": (
                "consumer-module",
                "from .hidden import exported_symbol\n",
            ),
        },
    )

    assert graph["package-module"] == []
    assert graph["root-package"] == []
    assert reasons == [
        "unmanaged or hidden tool_system dependency in "
        "src/tool_system/package/consumer.py: tool_system.package.hidden"
    ]


def test_multilevel_and_relative_import_from_resolve_exactly(
    tmp_path: Path,
) -> None:
    graph, reasons = _fixture_graph(
        tmp_path,
        {
            "src/tool_system/__init__.py": ("root-package", ""),
            "src/tool_system/package/__init__.py": ("package-module", ""),
            "src/tool_system/package/sibling.py": ("sibling-module", ""),
            "src/tool_system/package/deep/__init__.py": (
                "deep-package",
                "exported_symbol = object()\n",
            ),
            "src/tool_system/package/deep/leaf.py": ("leaf-module", ""),
            "src/tool_system/absolute_consumer.py": (
                "consumer-module",
                "from tool_system.package.deep import leaf\n",
            ),
            "src/tool_system/package/relative_consumer.py": (
                "consumer-module",
                "from .deep import leaf\n",
            ),
            "src/tool_system/package/deep/nested_consumer.py": (
                "consumer-module",
                "from .. import sibling\n",
            ),
            "src/tool_system/package/deep/symbol_consumer.py": (
                "consumer-module",
                "from . import exported_symbol\n",
            ),
        },
    )

    assert reasons == []
    assert graph["leaf-module"] == ["consumer-module"]
    assert graph["sibling-module"] == ["consumer-module"]
    assert graph["deep-package"] == ["consumer-module"]
    assert graph["package-module"] == []


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
    package = tmp_path / "src" / "tool_system" / "__init__.py"
    source = tmp_path / "src" / "tool_system" / "managed.py"
    source.parent.mkdir(parents=True)
    package.write_text("", encoding="utf-8")
    source.write_text("import tool_system.hidden\n", encoding="utf-8")
    owner_by_path = {
        "src/tool_system/__init__.py": "root-package",
        "src/tool_system/managed.py": "managed-module",
    }
    mappings = [
        {
            "canonical_module_id": "root-package",
            "python_import_identities": [
                {"kind": "exact", "name": "tool_system"},
            ],
        },
        {
            "canonical_module_id": "managed-module",
            "python_import_identities": [
                {"kind": "exact", "name": "tool_system.managed"},
            ],
        },
    ]

    graph, reasons = extract_managed_import_graph(
        tmp_path,
        owner_by_path,
        mappings,
    )

    assert graph["root-package"] == []
    assert reasons == [
        "unmanaged or hidden tool_system dependency in "
        "src/tool_system/managed.py: tool_system.hidden"
    ]
