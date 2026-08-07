"""Deterministic, non-executing state migration planning."""

from .planner import (
    CompatibilityRange,
    MigrationDirection,
    MigrationPlan,
    MigrationRegistry,
    MigrationStatus,
    MigrationStep,
    StateCompatibility,
    evaluate_state_compatibility,
    plan_migration,
)

__all__ = [
    "CompatibilityRange", "MigrationDirection", "MigrationPlan",
    "MigrationRegistry", "MigrationStatus", "MigrationStep",
    "StateCompatibility", "evaluate_state_compatibility", "plan_migration",
]
