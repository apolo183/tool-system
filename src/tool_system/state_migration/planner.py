"""Pure product-wide state migration registry and dry-run planner."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.release_governance import SemanticVersion

@dataclass(frozen=True)
class MigrationStep:
    step_id: str
    from_version: SemanticVersion
    to_version: SemanticVersion
    reversible: bool

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("migration step id must be explicit")
        if self.from_version >= self.to_version:
            raise ValueError("migration steps must move forward")

@dataclass(frozen=True)
class MigrationRegistry:
    steps: tuple[MigrationStep, ...]

    def __post_init__(self) -> None:
        identifiers: set[str] = set()
        outgoing: dict[SemanticVersion, SemanticVersion] = {}
        incoming: dict[SemanticVersion, SemanticVersion] = {}
        for step in self.steps:
            if step.step_id in identifiers:
                raise ValueError("migration step ids must be unique")
            if step.from_version in outgoing or step.to_version in incoming:
                raise ValueError("migration registry must be a linear non-branching graph")
            identifiers.add(step.step_id)
            outgoing[step.from_version] = step.to_version
            incoming[step.to_version] = step.from_version
        for start in outgoing:
            seen: set[SemanticVersion] = set()
            cursor = start
            while cursor in outgoing:
                if cursor in seen:
                    raise ValueError("migration registry must be acyclic")
                seen.add(cursor)
                cursor = outgoing[cursor]

@dataclass(frozen=True)
class CompatibilityRange:
    product_version: SemanticVersion
    minimum_state_version: SemanticVersion
    maximum_state_version: SemanticVersion

    def __post_init__(self) -> None:
        if self.minimum_state_version > self.maximum_state_version:
            raise ValueError("compatibility range is inverted")

class StateCompatibility(str, Enum):
    SUPPORTED = "SUPPORTED"
    TOO_OLD = "TOO_OLD"
    TOO_NEW = "TOO_NEW"
    PRODUCT_UNKNOWN = "PRODUCT_UNKNOWN"

class MigrationDirection(str, Enum):
    UPGRADE = "UPGRADE"
    DOWNGRADE = "DOWNGRADE"
    NOOP = "NOOP"

class MigrationStatus(str, Enum):
    READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION = "READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class MigrationPlan:
    status: MigrationStatus
    direction: MigrationDirection
    step_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    execution_authorized: bool = False

def _range_by_product(matrix: tuple[CompatibilityRange, ...]) -> dict[SemanticVersion, CompatibilityRange]:
    result: dict[SemanticVersion, CompatibilityRange] = {}
    for entry in matrix:
        if entry.product_version in result:
            raise ValueError("compatibility matrix product versions must be unique")
        result[entry.product_version] = entry
    return result

def evaluate_state_compatibility(*, product_version: SemanticVersion, state_version: SemanticVersion, matrix: tuple[CompatibilityRange, ...]) -> StateCompatibility:
    entry = _range_by_product(matrix).get(product_version)
    if entry is None:
        return StateCompatibility.PRODUCT_UNKNOWN
    if state_version < entry.minimum_state_version:
        return StateCompatibility.TOO_OLD
    if state_version > entry.maximum_state_version:
        return StateCompatibility.TOO_NEW
    return StateCompatibility.SUPPORTED

def plan_migration(*, registry: MigrationRegistry, current_state_version: SemanticVersion, target_state_version: SemanticVersion, target_product_version: SemanticVersion, compatibility_matrix: tuple[CompatibilityRange, ...], allow_downgrade: bool = False) -> MigrationPlan:
    compatibility = evaluate_state_compatibility(product_version=target_product_version, state_version=target_state_version, matrix=compatibility_matrix)
    if target_state_version == current_state_version:
        direction = MigrationDirection.NOOP
    elif target_state_version > current_state_version:
        direction = MigrationDirection.UPGRADE
    else:
        direction = MigrationDirection.DOWNGRADE
    reasons: list[str] = []
    if compatibility is not StateCompatibility.SUPPORTED:
        reasons.append(f"TARGET_STATE_{compatibility.value}")
    by_from = {step.from_version: step for step in registry.steps}
    by_to = {step.to_version: step for step in registry.steps}
    selected: list[MigrationStep] = []
    cursor = current_state_version
    if direction is MigrationDirection.UPGRADE:
        while cursor < target_state_version and cursor in by_from:
            step = by_from[cursor]
            selected.append(step)
            cursor = step.to_version
        if cursor != target_state_version:
            reasons.append("MIGRATION_PATH_INCOMPLETE")
    elif direction is MigrationDirection.DOWNGRADE:
        if not allow_downgrade:
            reasons.append("DOWNGRADE_NOT_EXPLICITLY_ALLOWED")
        while cursor > target_state_version and cursor in by_to:
            step = by_to[cursor]
            selected.append(step)
            cursor = step.from_version
        if cursor != target_state_version:
            reasons.append("MIGRATION_PATH_INCOMPLETE")
        if any(not step.reversible for step in selected):
            reasons.append("DOWNGRADE_PATH_IRREVERSIBLE")
    if reasons:
        return MigrationPlan(MigrationStatus.BLOCKED, direction, tuple(step.step_id for step in selected), tuple(reasons))
    ids = tuple(step.step_id if direction is not MigrationDirection.DOWNGRADE else f"{step.step_id}:reverse" for step in selected)
    return MigrationPlan(MigrationStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION, direction, ids, ())
