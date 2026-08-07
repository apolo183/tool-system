from __future__ import annotations

import pytest

from tool_system.release_governance import SemanticVersion
from tool_system.state_migration import (
    CompatibilityRange, MigrationDirection, MigrationRegistry, MigrationStatus,
    MigrationStep, StateCompatibility, evaluate_state_compatibility,
    plan_migration,
)

def v(value: str) -> SemanticVersion:
    return SemanticVersion.parse(value)

def registry(*, reversible_second: bool = True) -> MigrationRegistry:
    return MigrationRegistry((
        MigrationStep("state-1-to-2", v("1.0.0"), v("2.0.0"), True),
        MigrationStep("state-2-to-3", v("2.0.0"), v("3.0.0"), reversible_second),
    ))

def matrix() -> tuple[CompatibilityRange, ...]:
    return (CompatibilityRange(v("4.0.0"), v("2.0.0"), v("3.0.0")),)

def test_registry_rejects_duplicate_branch_and_non_forward_steps() -> None:
    with pytest.raises(ValueError, match="unique"):
        MigrationRegistry((MigrationStep("same", v("1.0.0"), v("2.0.0"), True), MigrationStep("same", v("2.0.0"), v("3.0.0"), True)))
    with pytest.raises(ValueError, match="non-branching"):
        MigrationRegistry((MigrationStep("a", v("1.0.0"), v("2.0.0"), True), MigrationStep("b", v("1.0.0"), v("3.0.0"), True)))
    with pytest.raises(ValueError, match="move forward"):
        MigrationStep("backward", v("2.0.0"), v("1.0.0"), True)

def test_compatibility_matrix_is_inclusive_and_unknown_fails_closed() -> None:
    assert evaluate_state_compatibility(product_version=v("4.0.0"), state_version=v("2.0.0"), matrix=matrix()) is StateCompatibility.SUPPORTED
    assert evaluate_state_compatibility(product_version=v("4.0.0"), state_version=v("1.0.0"), matrix=matrix()) is StateCompatibility.TOO_OLD
    assert evaluate_state_compatibility(product_version=v("9.0.0"), state_version=v("2.0.0"), matrix=matrix()) is StateCompatibility.PRODUCT_UNKNOWN

def test_upgrade_plan_is_ordered_and_non_executing() -> None:
    plan = plan_migration(registry=registry(), current_state_version=v("1.0.0"), target_state_version=v("3.0.0"), target_product_version=v("4.0.0"), compatibility_matrix=matrix())
    assert plan.status is MigrationStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    assert plan.direction is MigrationDirection.UPGRADE
    assert plan.step_ids == ("state-1-to-2", "state-2-to-3")
    assert plan.execution_authorized is False

def test_downgrade_requires_explicit_opt_in_and_every_step_reversible() -> None:
    blocked = plan_migration(registry=registry(), current_state_version=v("3.0.0"), target_state_version=v("2.0.0"), target_product_version=v("4.0.0"), compatibility_matrix=matrix())
    assert blocked.reasons == ("DOWNGRADE_NOT_EXPLICITLY_ALLOWED",)
    irreversible = plan_migration(registry=registry(reversible_second=False), current_state_version=v("3.0.0"), target_state_version=v("2.0.0"), target_product_version=v("4.0.0"), compatibility_matrix=matrix(), allow_downgrade=True)
    assert irreversible.reasons == ("DOWNGRADE_PATH_IRREVERSIBLE",)
    ready = plan_migration(registry=registry(), current_state_version=v("3.0.0"), target_state_version=v("2.0.0"), target_product_version=v("4.0.0"), compatibility_matrix=matrix(), allow_downgrade=True)
    assert ready.step_ids == ("state-2-to-3:reverse",)
    assert ready.execution_authorized is False

def test_gap_and_incompatible_target_fail_closed_with_ordered_reasons() -> None:
    plan = plan_migration(registry=MigrationRegistry(()), current_state_version=v("1.0.0"), target_state_version=v("3.0.0"), target_product_version=v("9.0.0"), compatibility_matrix=matrix())
    assert plan.status is MigrationStatus.BLOCKED
    assert plan.reasons == ("TARGET_STATE_PRODUCT_UNKNOWN", "MIGRATION_PATH_INCOMPLETE")
