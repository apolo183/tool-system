from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise

from tool_system.ai_worker.contract import canonical_sha256
from tool_system.provider_portfolio.fixtures import (
    FailureClass,
    FailureDisposition,
    PortfolioFixtureError,
    RouteDecision,
    RouteDecisionStatus,
    classify_failure,
)
from tool_system.provider_portfolio.provider_mode import (
    ProviderModeDecision,
    ProviderModeDecisionStatus,
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ECONOMIC_COMPONENTS = (
    "provider_usage",
    "subscription_or_renewal_allocation",
    "critical_path_time",
    "local_compute_and_electricity",
    "verification",
    "retry",
    "rework",
    "recovery",
    "rollback",
    "opportunity_cost",
)
_ZERO_OPERATIONS = {
    "provider_invocations": 0,
    "credential_value_accesses": 0,
    "network_operations": 0,
    "target_mutations": 0,
    "cleanup_operations": 0,
    "rollback_operations": 0,
}


class FailureControlAction(str, Enum):
    AVAILABILITY_FAILOVER = "AVAILABILITY_FAILOVER"
    SAME_ROUTE_REPAIR = "SAME_ROUTE_REPAIR"
    QUALITY_ESCALATION = "QUALITY_ESCALATION"
    BLOCK_NO_PROVIDER_BYPASS = "BLOCK_NO_PROVIDER_BYPASS"
    STOP = "STOP"


class NoProgressStatus(str, Enum):
    CONTINUE = "CONTINUE"
    STOPPED_REPEATED_FINGERPRINT = "STOPPED_NO_PROGRESS_REPEATED_FINGERPRINT"
    STOPPED_TWO_CYCLES = "STOPPED_NO_PROGRESS_TWO_CYCLES"


@dataclass(frozen=True)
class CycleObservation:
    task_digest_sha256: str
    candidate_tree_sha256: str
    acceptance_digest_sha256: str
    blocker_ids: tuple[str, ...]
    satisfied_acceptance_items: tuple[str, ...]
    validation_results: tuple[str, ...]
    material_acceptance_result_sha256: str
    attempt_number: int

    def __post_init__(self) -> None:
        for name in (
            "task_digest_sha256",
            "candidate_tree_sha256",
            "acceptance_digest_sha256",
            "material_acceptance_result_sha256",
        ):
            _require_sha256(name, getattr(self, name))
        for name in (
            "blocker_ids",
            "satisfied_acceptance_items",
            "validation_results",
        ):
            _require_canonical_identifiers(name, getattr(self, name), allow_empty=True)
        _require_positive("attempt_number", self.attempt_number)

    def recurrence_record(self) -> dict[str, object]:
        return {
            "task_digest_sha256": self.task_digest_sha256,
            "candidate_tree_sha256": self.candidate_tree_sha256,
            "acceptance_digest_sha256": self.acceptance_digest_sha256,
            "blocker_ids": list(self.blocker_ids),
            "validation_results": list(self.validation_results),
        }

    @property
    def recurrence_fingerprint(self) -> str:
        return canonical_sha256(self.recurrence_record())

    def to_record(self) -> dict[str, object]:
        return {
            **self.recurrence_record(),
            "satisfied_acceptance_items": list(self.satisfied_acceptance_items),
            "material_acceptance_result_sha256": (
                self.material_acceptance_result_sha256
            ),
            "attempt_number": self.attempt_number,
            "recurrence_fingerprint": self.recurrence_fingerprint,
        }


@dataclass(frozen=True)
class NoProgressDecision:
    status: NoProgressStatus
    completed_cycles: int
    consecutive_no_progress_cycles: int
    latest_recurrence_fingerprint: str
    terminal: bool
    stable_reason: str
    evidence_sha256: str
    authority_effect: str = "none"

    def to_record(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "completed_cycles": self.completed_cycles,
            "consecutive_no_progress_cycles": self.consecutive_no_progress_cycles,
            "latest_recurrence_fingerprint": self.latest_recurrence_fingerprint,
            "terminal": self.terminal,
            "stable_reason": self.stable_reason,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "operations": dict(_ZERO_OPERATIONS),
        }


def evaluate_no_progress(cycles: tuple[CycleObservation, ...]) -> NoProgressDecision:
    if not isinstance(cycles, tuple) or not cycles:
        raise PortfolioFixtureError("cycles must be a non-empty tuple")
    if not all(isinstance(item, CycleObservation) for item in cycles):
        raise PortfolioFixtureError("cycles must contain CycleObservation")

    task_digests = {item.task_digest_sha256 for item in cycles}
    acceptance_digests = {item.acceptance_digest_sha256 for item in cycles}
    if len(task_digests) != 1 or len(acceptance_digests) != 1:
        raise PortfolioFixtureError("cycles must keep one frozen task and acceptance")
    if tuple(item.attempt_number for item in cycles) != tuple(
        range(1, len(cycles) + 1)
    ):
        raise PortfolioFixtureError("cycle attempt numbers must be contiguous")

    latest = cycles[-1]
    repeated = latest.recurrence_fingerprint in {
        item.recurrence_fingerprint for item in cycles[:-1]
    }
    progress_flags = tuple(
        _cycle_made_progress(previous, current)
        for previous, current in pairwise(cycles)
    )
    consecutive = 0
    for made_progress in reversed(progress_flags):
        if made_progress:
            break
        consecutive += 1

    if repeated:
        status = NoProgressStatus.STOPPED_REPEATED_FINGERPRINT
        stable_reason = "the recurrence fingerprint repeated"
    elif consecutive >= 2:
        status = NoProgressStatus.STOPPED_TWO_CYCLES
        stable_reason = "two consecutive completed cycles made no progress"
    else:
        status = NoProgressStatus.CONTINUE
        stable_reason = "the finite no-progress stop condition has not been met"

    body = {
        "cycles": [item.to_record() for item in cycles],
        "status": status.value,
        "consecutive_no_progress_cycles": consecutive,
        "recurrence_fingerprint_fields": [
            "task_digest_sha256",
            "candidate_tree_sha256",
            "acceptance_digest_sha256",
            "blocker_ids",
            "validation_results",
        ],
        "recurrence_fingerprint_excludes": [
            "attempt_number",
            "material_acceptance_result_sha256",
            "satisfied_acceptance_items",
            "status_text",
            "timestamps",
        ],
        "authority_effect": "none",
    }
    return NoProgressDecision(
        status=status,
        completed_cycles=len(cycles),
        consecutive_no_progress_cycles=consecutive,
        latest_recurrence_fingerprint=latest.recurrence_fingerprint,
        terminal=status is not NoProgressStatus.CONTINUE,
        stable_reason=stable_reason,
        evidence_sha256=canonical_sha256(body),
    )


def _cycle_made_progress(
    previous: CycleObservation,
    current: CycleObservation,
) -> bool:
    previous_blockers = set(previous.blocker_ids)
    current_blockers = set(current.blocker_ids)
    previous_satisfied = set(previous.satisfied_acceptance_items)
    current_satisfied = set(current.satisfied_acceptance_items)
    return (
        current_blockers < previous_blockers
        or current_satisfied > previous_satisfied
        or current.material_acceptance_result_sha256
        != previous.material_acceptance_result_sha256
    )


@dataclass(frozen=True)
class FailureControlRequest:
    route_decision: RouteDecision | ProviderModeDecision
    failure_class: FailureClass
    current_route_id: str
    attempted_route_ids: tuple[str, ...]
    total_attempts: int
    max_attempts: int
    same_route_repair_attempts: int
    no_progress_decision: NoProgressDecision | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.route_decision, (RouteDecision, ProviderModeDecision)):
            raise PortfolioFixtureError(
                "route_decision must be RouteDecision or ProviderModeDecision"
            )
        selected = (
            self.route_decision.status is RouteDecisionStatus.SELECTED
            if isinstance(self.route_decision, RouteDecision)
            else self.route_decision.status is ProviderModeDecisionStatus.SELECTED
        )
        if not selected:
            raise PortfolioFixtureError("route_decision must contain a selected route")
        if not isinstance(self.failure_class, FailureClass):
            raise PortfolioFixtureError("failure_class must be registered")
        _require_identifier("current_route_id", self.current_route_id)
        _require_ordered_unique_identifiers(
            "attempted_route_ids", self.attempted_route_ids, allow_empty=False
        )
        if self.current_route_id not in self.attempted_route_ids:
            raise PortfolioFixtureError("current_route_id must already be attempted")
        eligible_route_ids = set(self.route_decision.ordered_eligible_route_ids)
        if self.current_route_id not in eligible_route_ids:
            raise PortfolioFixtureError("current_route_id must be an eligible route")
        if not set(self.attempted_route_ids) <= eligible_route_ids:
            raise PortfolioFixtureError("attempted routes must already be eligible")
        _require_positive("total_attempts", self.total_attempts)
        _require_positive("max_attempts", self.max_attempts)
        _require_nonnegative(
            "same_route_repair_attempts", self.same_route_repair_attempts
        )
        if self.total_attempts < len(self.attempted_route_ids):
            raise PortfolioFixtureError(
                "total_attempts cannot be less than the unique attempted route count"
            )
        if self.same_route_repair_attempts > self.total_attempts:
            raise PortfolioFixtureError(
                "same_route_repair_attempts cannot exceed total_attempts"
            )
        if self.failure_class is FailureClass.NO_PROGRESS:
            if (
                self.no_progress_decision is None
                or not self.no_progress_decision.terminal
            ):
                raise PortfolioFixtureError(
                    "NO_PROGRESS requires a terminal no-progress decision"
                )
        elif self.no_progress_decision is not None:
            raise PortfolioFixtureError(
                "no_progress_decision is only valid for NO_PROGRESS"
            )


@dataclass(frozen=True)
class FailureControlDecision:
    action: FailureControlAction
    failure_class: FailureClass
    current_route_id: str
    planned_route_id: str | None
    terminal: bool
    provider_switch_planned: bool
    same_route_repair_planned: bool
    stronger_route_escalation_planned: bool
    dispatch_authorized: bool
    candidate_application_authorized: bool
    stable_reason: str
    evidence_sha256: str
    authority_effect: str = "none"

    def to_record(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "failure_class": self.failure_class.value,
            "current_route_id": self.current_route_id,
            "planned_route_id": self.planned_route_id,
            "terminal": self.terminal,
            "provider_switch_planned": self.provider_switch_planned,
            "same_route_repair_planned": self.same_route_repair_planned,
            "stronger_route_escalation_planned": (
                self.stronger_route_escalation_planned
            ),
            "dispatch_authorized": self.dispatch_authorized,
            "candidate_application_authorized": (self.candidate_application_authorized),
            "stable_reason": self.stable_reason,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "operations": dict(_ZERO_OPERATIONS),
        }


def plan_failure_control(request: FailureControlRequest) -> FailureControlDecision:
    if not isinstance(request, FailureControlRequest):
        raise PortfolioFixtureError("request must be FailureControlRequest")
    policy = classify_failure(request.failure_class)

    action: FailureControlAction
    planned_route_id: str | None = None
    stable_reason: str

    if policy.disposition is FailureDisposition.BLOCK_NO_PROVIDER_BYPASS:
        action = FailureControlAction.BLOCK_NO_PROVIDER_BYPASS
        stable_reason = policy.stable_reason
    elif policy.disposition is FailureDisposition.STOP:
        action = FailureControlAction.STOP
        if request.failure_class is FailureClass.CANCELLED:
            stable_reason = (
                "cancellation stops before dispatch or candidate application"
            )
        elif request.failure_class is FailureClass.NO_PROGRESS:
            assert request.no_progress_decision is not None
            stable_reason = request.no_progress_decision.stable_reason
        else:
            stable_reason = policy.stable_reason
    elif request.total_attempts >= request.max_attempts:
        action = FailureControlAction.STOP
        stable_reason = "the finite total-attempt envelope is exhausted"
    elif policy.disposition is FailureDisposition.AVAILABILITY_FAILOVER:
        planned_route_id = _next_unattempted(
            request.route_decision.availability_failover_route_ids,
            request.attempted_route_ids,
        )
        if planned_route_id is None:
            action = FailureControlAction.STOP
            stable_reason = "no already eligible availability failover route remains"
        else:
            action = FailureControlAction.AVAILABILITY_FAILOVER
            stable_reason = policy.stable_reason
    else:
        assert policy.disposition is FailureDisposition.SAME_ROUTE_REPAIR_THEN_ESCALATE
        if (
            request.same_route_repair_attempts
            < request.route_decision.same_route_repair_limit
        ):
            action = FailureControlAction.SAME_ROUTE_REPAIR
            planned_route_id = request.current_route_id
            stable_reason = "one bounded same-route repair is planned before escalation"
        else:
            planned_route_id = _next_unattempted(
                request.route_decision.quality_escalation_route_ids,
                request.attempted_route_ids,
            )
            if planned_route_id is None:
                action = FailureControlAction.STOP
                stable_reason = "no stronger already eligible escalation route remains"
            else:
                action = FailureControlAction.QUALITY_ESCALATION
                stable_reason = policy.stable_reason

    terminal = action in {
        FailureControlAction.BLOCK_NO_PROVIDER_BYPASS,
        FailureControlAction.STOP,
    }
    body = {
        "request": {
            "route_decision_sha256": request.route_decision.evidence_sha256,
            "failure_class": request.failure_class.value,
            "current_route_id": request.current_route_id,
            "attempted_route_ids": list(request.attempted_route_ids),
            "total_attempts": request.total_attempts,
            "max_attempts": request.max_attempts,
            "same_route_repair_attempts": request.same_route_repair_attempts,
            "no_progress_evidence_sha256": (
                request.no_progress_decision.evidence_sha256
                if request.no_progress_decision is not None
                else None
            ),
        },
        "action": action.value,
        "planned_route_id": planned_route_id,
        "terminal": terminal,
        "stable_reason": stable_reason,
        "dispatch_authorized": False,
        "candidate_application_authorized": False,
        "authority_effect": "none",
    }
    return FailureControlDecision(
        action=action,
        failure_class=request.failure_class,
        current_route_id=request.current_route_id,
        planned_route_id=planned_route_id,
        terminal=terminal,
        provider_switch_planned=(
            planned_route_id is not None
            and planned_route_id != request.current_route_id
        ),
        same_route_repair_planned=(action is FailureControlAction.SAME_ROUTE_REPAIR),
        stronger_route_escalation_planned=(
            action is FailureControlAction.QUALITY_ESCALATION
        ),
        dispatch_authorized=False,
        candidate_application_authorized=False,
        stable_reason=stable_reason,
        evidence_sha256=canonical_sha256(body),
    )


def _next_unattempted(
    route_ids: tuple[str, ...],
    attempted_route_ids: tuple[str, ...],
) -> str | None:
    attempted = set(attempted_route_ids)
    return next((route_id for route_id in route_ids if route_id not in attempted), None)


@dataclass(frozen=True)
class ModuleIsolationPlan:
    failed_module_id: str
    paused_downstream_module_ids: tuple[str, ...]
    preserved_unrelated_module_ids: tuple[str, ...]
    rollback_reference: str
    evidence_sha256: str
    authority_effect: str = "none"
    machine_lifecycle_status_added: bool = False
    rollback_execution_authorized: bool = False
    cleanup_execution_authorized: bool = False

    def to_record(self) -> dict[str, object]:
        return {
            "failed_module_id": self.failed_module_id,
            "stopped_output_module_ids": [self.failed_module_id],
            "paused_downstream_module_ids": list(self.paused_downstream_module_ids),
            "preserved_unrelated_module_ids": list(self.preserved_unrelated_module_ids),
            "rollback_reference": self.rollback_reference,
            "machine_lifecycle_status_added": self.machine_lifecycle_status_added,
            "rollback_execution_authorized": self.rollback_execution_authorized,
            "cleanup_execution_authorized": self.cleanup_execution_authorized,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "operations": dict(_ZERO_OPERATIONS),
        }


def build_module_isolation_plan(
    *,
    failed_module_id: str,
    affected_downstream_module_ids: tuple[str, ...],
    unrelated_module_ids: tuple[str, ...],
    rollback_reference: str,
) -> ModuleIsolationPlan:
    _require_identifier("failed_module_id", failed_module_id)
    _require_canonical_identifiers(
        "affected_downstream_module_ids",
        affected_downstream_module_ids,
        allow_empty=True,
    )
    _require_canonical_identifiers(
        "unrelated_module_ids", unrelated_module_ids, allow_empty=True
    )
    _require_identifier("rollback_reference", rollback_reference)
    affected = set(affected_downstream_module_ids)
    unrelated = set(unrelated_module_ids)
    if failed_module_id in affected | unrelated:
        raise PortfolioFixtureError("failed module must be isolated from supplied sets")
    if affected & unrelated:
        raise PortfolioFixtureError(
            "affected and unrelated module sets must be disjoint"
        )
    body = {
        "failed_module_id": failed_module_id,
        "stopped_output_module_ids": [failed_module_id],
        "paused_downstream_module_ids": list(affected_downstream_module_ids),
        "preserved_unrelated_module_ids": list(unrelated_module_ids),
        "rollback_reference": rollback_reference,
        "machine_lifecycle_status_added": False,
        "rollback_execution_authorized": False,
        "cleanup_execution_authorized": False,
        "authority_effect": "none",
    }
    return ModuleIsolationPlan(
        failed_module_id=failed_module_id,
        paused_downstream_module_ids=affected_downstream_module_ids,
        preserved_unrelated_module_ids=unrelated_module_ids,
        rollback_reference=rollback_reference,
        evidence_sha256=canonical_sha256(body),
    )


@dataclass(frozen=True)
class TotalEconomicCost:
    provider_usage: int
    subscription_or_renewal_allocation: int
    critical_path_time: int
    local_compute_and_electricity: int
    verification: int
    retry: int
    rework: int
    recovery: int
    rollback: int
    opportunity_cost: int

    def __post_init__(self) -> None:
        for name, value in self.to_record().items():
            _require_nonnegative(name, value)

    @classmethod
    def from_fixture_mapping(cls, value: Mapping[str, object]) -> TotalEconomicCost:
        if not isinstance(value, Mapping):
            raise PortfolioFixtureError("economic fixture must be a mapping")
        expected_keys = set(_ECONOMIC_COMPONENTS) | {"expected_total"}
        if set(value) != expected_keys:
            raise PortfolioFixtureError("economic fixture keys must be exact")
        instance = cls(**{name: value[name] for name in _ECONOMIC_COMPONENTS})  # type: ignore[arg-type]
        expected_total = value["expected_total"]
        _require_nonnegative("expected_total", expected_total)
        if instance.total_micro_usd != expected_total:
            raise PortfolioFixtureError("economic fixture total does not reconcile")
        return instance

    @property
    def total_micro_usd(self) -> int:
        return sum(self.to_record().values())

    def to_record(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in _ECONOMIC_COMPONENTS}


@dataclass(frozen=True)
class EconomicCandidate:
    route_id: str
    hard_floors_passed: bool
    cost: TotalEconomicCost

    def __post_init__(self) -> None:
        _require_identifier("route_id", self.route_id)
        if not isinstance(self.hard_floors_passed, bool):
            raise PortfolioFixtureError("hard_floors_passed must be boolean")
        if not isinstance(self.cost, TotalEconomicCost):
            raise PortfolioFixtureError("cost must be TotalEconomicCost")

    def to_record(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "hard_floors_passed": self.hard_floors_passed,
            "cost_components_micro_usd": self.cost.to_record(),
            "total_micro_usd": self.cost.total_micro_usd,
        }


@dataclass(frozen=True)
class EconomicDecision:
    status: RouteDecisionStatus
    selected_route_id: str | None
    evaluations: tuple[EconomicCandidate, ...]
    stop_reason: str | None
    evidence_sha256: str
    authority_effect: str = "none"

    def to_record(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "selected_route_id": self.selected_route_id,
            "evaluations": [item.to_record() for item in self.evaluations],
            "stop_reason": self.stop_reason,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "operations": dict(_ZERO_OPERATIONS),
        }


def select_lowest_total_economic_cost(
    candidates: tuple[EconomicCandidate, ...],
) -> EconomicDecision:
    if not isinstance(candidates, tuple) or not candidates:
        raise PortfolioFixtureError("economic candidates must be a non-empty tuple")
    if not all(isinstance(item, EconomicCandidate) for item in candidates):
        raise PortfolioFixtureError(
            "economic candidates must contain EconomicCandidate"
        )
    route_ids = tuple(item.route_id for item in candidates)
    if route_ids != tuple(sorted(route_ids)) or len(route_ids) != len(set(route_ids)):
        raise PortfolioFixtureError(
            "economic candidates must have unique route IDs in canonical order"
        )
    eligible = tuple(item for item in candidates if item.hard_floors_passed)
    selected = min(
        eligible,
        key=lambda item: (item.cost.total_micro_usd, item.route_id),
        default=None,
    )
    body = {
        "evaluations": [item.to_record() for item in candidates],
        "selected_route_id": selected.route_id if selected is not None else None,
        "stop_reason": None if selected is not None else "EMPTY_ELIGIBLE_SET",
        "hard_floors_evaluated_before_economics": True,
        "currency": "microUSD",
        "authority_effect": "none",
    }
    return EconomicDecision(
        status=(
            RouteDecisionStatus.SELECTED
            if selected is not None
            else RouteDecisionStatus.BLOCKED
        ),
        selected_route_id=selected.route_id if selected is not None else None,
        evaluations=candidates,
        stop_reason=None if selected is not None else "EMPTY_ELIGIBLE_SET",
        evidence_sha256=canonical_sha256(body),
    )


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise PortfolioFixtureError(f"{name} must be a bounded identifier")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise PortfolioFixtureError(f"{name} must be lowercase SHA-256")


def _require_canonical_identifiers(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    _require_ordered_unique_identifiers(name, value, allow_empty=allow_empty)
    assert isinstance(value, tuple)
    if value != tuple(sorted(value)):
        raise PortfolioFixtureError(f"{name} must be canonically ordered")


def _require_ordered_unique_identifiers(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
        raise PortfolioFixtureError(f"{name} must be a tuple of identifiers")
    if not allow_empty and not value:
        raise PortfolioFixtureError(f"{name} must be non-empty")
    if len(value) != len(set(value)):
        raise PortfolioFixtureError(f"{name} must be unique")
    for item in value:
        _require_identifier(name, item)


def _require_nonnegative(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PortfolioFixtureError(f"{name} must be a non-negative integer")


def _require_positive(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise PortfolioFixtureError(f"{name} must be a positive integer")
