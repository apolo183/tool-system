"""Durable architecture and module-registry contracts."""

from tool_system.architecture.module_registry import (
    CENTRAL_COMPATIBILITY_INPUT_MODE,
    LEGACY_REGISTRY_INPUT_MODE,
    REQUIRED_MODULE_FIELDS,
    compare_managed_import_graphs,
    extract_managed_import_graph,
    load_s0_identity_mapping,
    validate_module_registry,
)

__all__ = [
    "CENTRAL_COMPATIBILITY_INPUT_MODE",
    "LEGACY_REGISTRY_INPUT_MODE",
    "REQUIRED_MODULE_FIELDS",
    "compare_managed_import_graphs",
    "extract_managed_import_graph",
    "load_s0_identity_mapping",
    "validate_module_registry",
]
