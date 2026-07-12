"""Durable architecture and module-registry contracts."""

from tool_system.architecture.module_registry import (
    REQUIRED_MODULE_FIELDS,
    validate_module_registry,
)

__all__ = ["REQUIRED_MODULE_FIELDS", "validate_module_registry"]
