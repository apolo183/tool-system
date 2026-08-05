from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from tool_system.ai_worker.contract import canonical_sha256

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")


class ProviderModeError(ValueError):
    """Stable fail-closed validation error for repository-external route inputs."""


class ProviderAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNCONFIGURED = "UNCONFIGURED"
    UNFUNDED = "UNFUNDED"
    MISSING_CREDENTIAL = "MISSING_CREDENTIAL"
    INVALID_CREDENTIAL = "INVALID_CREDENTIAL"
    EXPIRED_CREDENTIAL = "EXPIRED_CREDENTIAL"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"


class ProviderAuthorizationState(str, Enum):
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class ProviderModeEvaluationDisposition(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class ProviderModeDecisionStatus(str, Enum):
    API_DISABLED = "API_DISABLED"
    SELECTED = "SELECTED"
    NO_AVAILABLE_PROVIDER = "NO_AVAILABLE_PROVIDER"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ProviderModeRoute:
    """One operator-ordered provider/model route with no credential material."""

    provider_id: str
    requested_model_id: str = ""
    enabled: bool = False
    availability_state: ProviderAvailabilityState = (
        ProviderAvailabilityState.UNCONFIGURED
    )
    provider_data_transfer_authorized: bool = False
    adapter_fake_io_contract_passed: bool = False
    provider_budget_microunits: int = 0
    reserved_cost_microunits: int = 0
    logical_duration_ms: int = 0
    strength_rank: int = 0

    def __post_init__(self) -> None:
        _require_identifier("provider_id", self.provider_id)
        if self.requested_model_id:
            _require_identifier("requested_model_id", self.requested_model_id)
        for name in (
            "enabled",
            "provider_data_transfer_authorized",
            "adapter_fake_io_contract_passed",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ProviderModeError(f"{name} must be boolean")
        if not isinstance(self.availability_state, ProviderAvailabilityState):
            raise ProviderModeError("availability_state must be registered")
        for name in (
            "provider_budget_microunits",
            "reserved_cost_microunits",
            "logical_duration_ms",
            "strength_rank",
        ):
            _require_nonnegative(name, getattr(self, name))

    @property
    def route_id(self) -> str:
        model_id = self.requested_model_id or "UNCONFIGURED"
        return f"{self.provider_id}/{model_id}"

    def to_record(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "provider_id": self.provider_id,
            "requested_model_id": self.requested_model_id or None,
            "enabled": self.enabled,
            "availability_state": self.availability_state.value,
            "provider_data_transfer_authorized": (
                self.provider_data_transfer_authorized
            ),
            "adapter_fake_io_contract_passed": (
                self.adapter_fake_io_contract_passed
            ),
            "provider_budget_microunits": self.provider_budget_microunits,
            "reserved_cost_microunits": self.reserved_cost_microunits,
            "logical_duration_ms": self.logical_duration_ms,
            "strength_rank": self.strength_rank,
        }


@dataclass(frozen=True)
class ProviderModeSnapshot:
    """Caller-owned snapshot of repository-external API-backup controls."""

    configuration_version: str
    policy_version: str
    authorization_id: str
    routes: tuple[ProviderModeRoute, ...]
    api_mode_enabled: bool = False
    authorization_state: ProviderAuthorizationState = (
        ProviderAuthorizationState.NOT_AUTHORIZED
    )
    policy_preconditions_current: bool = False
    source_preconditions_current: bool = False
    cancellation_requested: bool = False
    total_budget_microunits: int = 0
    max_attempts: int = 0
    max_retries: int = 0

    def __post_init__(self) -> None:
        for name in ("configuration_version", "policy_version", "authorization_id"):
            _require_identifier(name, getattr(self, name))
        if not isinstance(self.routes, tuple) or not all(
            isinstance(route, ProviderModeRoute) for route in self.routes
        ):
            raise ProviderModeError("routes must be a tuple of ProviderModeRoute")
        provider_ids = tuple(route.provider_id for route in self.routes)
        if len(provider_ids) != len(set(provider_ids)):
            raise ProviderModeError("routes must contain unique provider IDs")
        for name in (
            "api_mode_enabled",
            "policy_preconditions_current",
            "source_preconditions_current",
            "cancellation_requested",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ProviderModeError(f"{name} must be boolean")
        if not isinstance(self.authorization_state, ProviderAuthorizationState):
            raise ProviderModeError("authorization_state must be registered")
        for name in ("total_budget_microunits", "max_attempts", "max_retries"):
            _require_nonnegative(name, getattr(self, name))
        if self.max_retries > self.max_attempts:
            raise ProviderModeError("max_retries cannot exceed max_attempts")

    def to_record(self) -> dict[str, object]:
        return {
            "configuration_version": self.configuration_version,
            "policy_version": self.policy_version,
            "authorization_id": self.authorization_id,
            "routes": [route.to_record() for route in self.routes],
            "api_mode_enabled": self.api_mode_enabled,
            "authorization_state": self.authorization_state.value,
            "policy_preconditions_current": self.policy_preconditions_current,
            "source_preconditions_current": self.source_preconditions_current,
            "cancellation_requested": self.cancellation_requested,
            "total_budget_microunits": self.total_budget_microunits,
            "max_attempts": self.max_attempts,
            "max_retries": self.max_retries,
        }


@dataclass(frozen=True)
class ProviderModeEvaluation:
    route_id: str
    disposition: ProviderModeEvaluationDisposition
    reasons: tuple[str, ...]
    reserved_cost_microunits: int
    logical_duration_ms: int
    strength_rank: int

    @property
    def eligible(self) -> bool:
        return self.disposition is ProviderModeEvaluationDisposition.ELIGIBLE

    def to_record(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "disposition": self.disposition.value,
            "reasons": list(self.reasons),
            "reserved_cost_microunits": self.reserved_cost_microunits,
            "logical_duration_ms": self.logical_duration_ms,
            "strength_rank": self.strength_rank,
        }


@dataclass(frozen=True)
class ProviderModeDecision:
    status: ProviderModeDecisionStatus
    policy_version: str
    configuration_version: str
    authorization_id: str
    selected_route_id: str | None
    selected_provider_id: str | None
    requested_model_id: str | None
    ordered_eligible_route_ids: tuple[str, ...]
    availability_failover_route_ids: tuple[str, ...]
    quality_escalation_route_ids: tuple[str, ...]
    skipped_route_ids: tuple[str, ...]
    same_route_repair_limit: int
    evaluations: tuple[ProviderModeEvaluation, ...]
    stop_reason: str | None
    evidence_sha256: str
    authority_effect: str = "none"
    dispatch_authorized: bool = False
    provider_invocations: int = 0
    network_operations: int = 0
    credential_resolver_invocations: int = 0
    credential_value_accesses: int = 0

    def to_record(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "policy_version": self.policy_version,
            "configuration_version": self.configuration_version,
            "authorization_id": self.authorization_id,
            "selected_route_id": self.selected_route_id,
            "selected_provider_id": self.selected_provider_id,
            "requested_model_id": self.requested_model_id,
            "ordered_eligible_route_ids": list(self.ordered_eligible_route_ids),
            "availability_failover_route_ids": list(
                self.availability_failover_route_ids
            ),
            "quality_escalation_route_ids": list(
                self.quality_escalation_route_ids
            ),
            "skipped_route_ids": list(self.skipped_route_ids),
            "same_route_repair_limit": self.same_route_repair_limit,
            "evaluations": [evaluation.to_record() for evaluation in self.evaluations],
            "stop_reason": self.stop_reason,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "dispatch_authorized": self.dispatch_authorized,
            "operations": {
                "provider_invocations": self.provider_invocations,
                "network_operations": self.network_operations,
                "credential_resolver_invocations": self.credential_resolver_invocations,
                "credential_value_accesses": self.credential_value_accesses,
            },
        }


def select_provider_mode_route(snapshot: ProviderModeSnapshot) -> ProviderModeDecision:
    """Select one external-configured route without credentials, transport, or I/O."""

    if not isinstance(snapshot, ProviderModeSnapshot):
        raise ProviderModeError("snapshot must be ProviderModeSnapshot")
    if not snapshot.api_mode_enabled:
        evaluations = tuple(
            _evaluation(
                route,
                ProviderModeEvaluationDisposition.SKIPPED,
                ("API_MODE_DISABLED",),
            )
            for route in snapshot.routes
        )
        return _decision(
            snapshot,
            ProviderModeDecisionStatus.API_DISABLED,
            evaluations,
            stop_reason="API_DISABLED",
        )

    global_reasons = _global_block_reasons(snapshot)
    if global_reasons:
        evaluations = tuple(
            _evaluation(
                route,
                ProviderModeEvaluationDisposition.BLOCKED,
                global_reasons,
            )
            for route in snapshot.routes
        )
        return _decision(
            snapshot,
            ProviderModeDecisionStatus.BLOCKED,
            evaluations,
            stop_reason=global_reasons[0],
        )

    evaluations = tuple(_evaluate_route(route, snapshot) for route in snapshot.routes)
    blocked = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.disposition is ProviderModeEvaluationDisposition.BLOCKED
    )
    if blocked:
        return _decision(
            snapshot,
            ProviderModeDecisionStatus.BLOCKED,
            evaluations,
            stop_reason=blocked[0].reasons[0],
        )
    eligible = tuple(evaluation for evaluation in evaluations if evaluation.eligible)
    if not eligible:
        return _decision(
            snapshot,
            ProviderModeDecisionStatus.NO_AVAILABLE_PROVIDER,
            evaluations,
            stop_reason="NO_AVAILABLE_PROVIDER",
        )
    return _decision(
        snapshot,
        ProviderModeDecisionStatus.SELECTED,
        evaluations,
        stop_reason=None,
    )


def _global_block_reasons(snapshot: ProviderModeSnapshot) -> tuple[str, ...]:
    reasons: list[str] = []
    if snapshot.authorization_state is ProviderAuthorizationState.EXPIRED:
        reasons.append("AUTHORIZATION_EXPIRED")
    elif snapshot.authorization_state is not ProviderAuthorizationState.ACTIVE:
        reasons.append("AUTHORIZATION_NOT_ACTIVE")
    if not snapshot.policy_preconditions_current:
        reasons.append("POLICY_PRECONDITION_STALE")
    if not snapshot.source_preconditions_current:
        reasons.append("SOURCE_PRECONDITION_STALE")
    if snapshot.cancellation_requested:
        reasons.append("CANCELLED")
    if snapshot.total_budget_microunits == 0:
        reasons.append("HARD_BUDGET_EXHAUSTED")
    if snapshot.max_attempts == 0:
        reasons.append("ATTEMPT_ENVELOPE_EMPTY")
    return tuple(reasons)


def _evaluate_route(
    route: ProviderModeRoute,
    snapshot: ProviderModeSnapshot,
) -> ProviderModeEvaluation:
    if not route.enabled:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.SKIPPED,
            ("PROVIDER_DISABLED",),
        )
    if not route.adapter_fake_io_contract_passed:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.BLOCKED,
            ("FAKE_IO_CONTRACT_UNVERIFIED",),
        )
    if not route.requested_model_id:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.SKIPPED,
            ("PROVIDER_UNCONFIGURED",),
        )
    if route.availability_state is not ProviderAvailabilityState.AVAILABLE:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.SKIPPED,
            (f"PROVIDER_{route.availability_state.value}",),
        )
    if route.provider_budget_microunits == 0:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.SKIPPED,
            ("PROVIDER_UNFUNDED",),
        )

    reasons: list[str] = []
    if not route.provider_data_transfer_authorized:
        reasons.append("PROVIDER_TRANSFER_NOT_AUTHORIZED")
    if route.reserved_cost_microunits > route.provider_budget_microunits:
        reasons.append("PROVIDER_POLICY_BUDGET")
    if route.reserved_cost_microunits > snapshot.total_budget_microunits:
        reasons.append("HARD_BUDGET_EXHAUSTED")
    if reasons:
        return _evaluation(
            route,
            ProviderModeEvaluationDisposition.BLOCKED,
            tuple(reasons),
        )
    return _evaluation(route, ProviderModeEvaluationDisposition.ELIGIBLE, ())


def _evaluation(
    route: ProviderModeRoute,
    disposition: ProviderModeEvaluationDisposition,
    reasons: tuple[str, ...],
) -> ProviderModeEvaluation:
    return ProviderModeEvaluation(
        route_id=route.route_id,
        disposition=disposition,
        reasons=reasons,
        reserved_cost_microunits=route.reserved_cost_microunits,
        logical_duration_ms=route.logical_duration_ms,
        strength_rank=route.strength_rank,
    )


def _decision(
    snapshot: ProviderModeSnapshot,
    status: ProviderModeDecisionStatus,
    evaluations: tuple[ProviderModeEvaluation, ...],
    *,
    stop_reason: str | None,
) -> ProviderModeDecision:
    eligible = tuple(evaluation for evaluation in evaluations if evaluation.eligible)
    selected = eligible[0] if status is ProviderModeDecisionStatus.SELECTED else None
    selected_route = (
        next(
            route for route in snapshot.routes if route.route_id == selected.route_id
        )
        if selected is not None
        else None
    )
    remaining_attempts = max(0, snapshot.max_attempts - 1)
    failover = tuple(
        evaluation.route_id for evaluation in eligible[1 : 1 + remaining_attempts]
    )
    quality_escalation = (
        tuple(
            evaluation.route_id
            for evaluation in eligible[1:]
            if evaluation.strength_rank > selected.strength_rank
        )[:remaining_attempts]
        if selected is not None
        else ()
    )
    skipped = tuple(
        evaluation.route_id
        for evaluation in evaluations
        if evaluation.disposition is ProviderModeEvaluationDisposition.SKIPPED
    )
    body = {
        "snapshot": snapshot.to_record(),
        "status": status.value,
        "evaluations": [evaluation.to_record() for evaluation in evaluations],
        "selected_route_id": selected.route_id if selected is not None else None,
        "ordered_eligible_route_ids": [item.route_id for item in eligible],
        "availability_failover_route_ids": list(failover),
        "quality_escalation_route_ids": list(quality_escalation),
        "skipped_route_ids": list(skipped),
        "stop_reason": stop_reason,
        "external_priority_preserved": True,
        "moving_alias_exact_version_required": False,
        "key_presence_grants_authority": False,
        "authority_effect": "none",
        "dispatch_authorized": False,
    }
    return ProviderModeDecision(
        status=status,
        policy_version=snapshot.policy_version,
        configuration_version=snapshot.configuration_version,
        authorization_id=snapshot.authorization_id,
        selected_route_id=selected.route_id if selected is not None else None,
        selected_provider_id=(
            selected_route.provider_id if selected_route is not None else None
        ),
        requested_model_id=(
            selected_route.requested_model_id if selected_route is not None else None
        ),
        ordered_eligible_route_ids=tuple(item.route_id for item in eligible),
        availability_failover_route_ids=failover,
        quality_escalation_route_ids=quality_escalation,
        skipped_route_ids=skipped,
        same_route_repair_limit=snapshot.max_retries,
        evaluations=evaluations,
        stop_reason=stop_reason,
        evidence_sha256=canonical_sha256(body),
    )


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise ProviderModeError(f"{name} must be a bounded identifier")


def _require_nonnegative(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProviderModeError(f"{name} must be a non-negative integer")
