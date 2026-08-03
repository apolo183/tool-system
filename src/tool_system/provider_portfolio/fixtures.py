from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from tool_system.ai_worker.contract import (
    AIWorkerError,
    AIWorkerErrorCode,
    AIWorkerRequest,
    AIWorkerUsage,
    CancellationSignal,
    ProviderResponse,
    canonical_sha256,
)
from tool_system.ai_worker.fixture_provider import (
    DeterministicFixtureProvider,
    FixtureScenario,
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_MICRO_MAX = 1_000_000
_ELIGIBLE_STATES = frozenset({"ELIGIBLE", "PRIMARY"})


class PortfolioFixtureError(ValueError):
    """Stable fail-closed validation error for P15B fixture inputs."""


class QualificationState(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUARANTINED = "QUARANTINED"
    BENCHMARKING = "BENCHMARKING"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    ELIGIBLE = "ELIGIBLE"
    PRIMARY = "PRIMARY"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"


class RouteDecisionStatus(str, Enum):
    SELECTED = "SELECTED"
    BLOCKED = "BLOCKED"


class FailureClass(str, Enum):
    MISSING_CREDENTIAL_REFERENCE = "MISSING_CREDENTIAL_REFERENCE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    PROVIDER_OUTAGE = "PROVIDER_OUTAGE"
    QUALITY_REJECTED = "QUALITY_REJECTED"
    ACCEPTANCE_REJECTED = "ACCEPTANCE_REJECTED"
    POLICY_DENIED = "POLICY_DENIED"
    DATA_POLICY_DENIED = "DATA_POLICY_DENIED"
    AUTHORIZATION_MISMATCH = "AUTHORIZATION_MISMATCH"
    HARD_BUDGET_EXHAUSTED = "HARD_BUDGET_EXHAUSTED"
    STALE_PRECONDITION = "STALE_PRECONDITION"
    MISSING_REQUIRED_EVIDENCE = "MISSING_REQUIRED_EVIDENCE"
    EMPTY_ELIGIBLE_SET = "EMPTY_ELIGIBLE_SET"
    ATTEMPT_EXHAUSTED = "ATTEMPT_EXHAUSTED"
    CANCELLED = "CANCELLED"
    NO_PROGRESS = "NO_PROGRESS"


class FailureDisposition(str, Enum):
    AVAILABILITY_FAILOVER = "AVAILABILITY_FAILOVER"
    SAME_ROUTE_REPAIR_THEN_ESCALATE = "SAME_ROUTE_REPAIR_THEN_ESCALATE"
    BLOCK_NO_PROVIDER_BYPASS = "BLOCK_NO_PROVIDER_BYPASS"
    STOP = "STOP"


@dataclass(frozen=True)
class TaskProfile:
    profile_id: str
    task_id: str
    task_class: str
    language: str
    repository_context_tokens: int
    dependency_breadth: int
    reasoning_complexity: int
    implementation_complexity: int
    security_risk: int
    data_risk: int
    repository_mutation_risk: int
    operational_risk: int
    required_capabilities: tuple[str, ...]
    minimum_quality_micros: int
    minimum_confidence_micros: int
    verification_burden: int
    repair_burden: int
    critical_path: bool
    remaining_slack_ms: int
    delay_sensitivity_micros: int
    evidence_confidence_micros: int
    uncertainty_reasons: tuple[str, ...]
    source_input_sha256: str
    authority_effect: str = "none"

    def __post_init__(self) -> None:
        for name in ("profile_id", "task_id", "task_class", "language"):
            _require_identifier(name, getattr(self, name))
        _require_sha256("source_input_sha256", self.source_input_sha256)
        _require_canonical_strings(
            "required_capabilities", self.required_capabilities, allow_empty=False
        )
        _require_canonical_strings(
            "uncertainty_reasons", self.uncertainty_reasons, allow_empty=True
        )
        for name in ("repository_context_tokens", "dependency_breadth", "remaining_slack_ms"):
            _require_nonnegative(name, getattr(self, name))
        for name in (
            "reasoning_complexity",
            "implementation_complexity",
            "security_risk",
            "data_risk",
            "repository_mutation_risk",
            "operational_risk",
            "verification_burden",
            "repair_burden",
        ):
            _require_scale(name, getattr(self, name))
        for name in (
            "minimum_quality_micros",
            "minimum_confidence_micros",
            "delay_sensitivity_micros",
            "evidence_confidence_micros",
        ):
            _require_micros(name, getattr(self, name))
        if not isinstance(self.critical_path, bool):
            raise PortfolioFixtureError("critical_path must be boolean")
        if self.authority_effect != "none":
            raise PortfolioFixtureError("task profile cannot grant authority")

    def to_record(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "task_id": self.task_id,
            "task_class": self.task_class,
            "language": self.language,
            "repository_context_tokens": self.repository_context_tokens,
            "dependency_breadth": self.dependency_breadth,
            "reasoning_complexity": self.reasoning_complexity,
            "implementation_complexity": self.implementation_complexity,
            "security_risk": self.security_risk,
            "data_risk": self.data_risk,
            "repository_mutation_risk": self.repository_mutation_risk,
            "operational_risk": self.operational_risk,
            "required_capabilities": list(self.required_capabilities),
            "minimum_quality_micros": self.minimum_quality_micros,
            "minimum_confidence_micros": self.minimum_confidence_micros,
            "verification_burden": self.verification_burden,
            "repair_burden": self.repair_burden,
            "critical_path": self.critical_path,
            "remaining_slack_ms": self.remaining_slack_ms,
            "delay_sensitivity_micros": self.delay_sensitivity_micros,
            "evidence_confidence_micros": self.evidence_confidence_micros,
            "uncertainty_reasons": list(self.uncertainty_reasons),
            "source_input_sha256": self.source_input_sha256,
            "authority_effect": self.authority_effect,
        }

    def sha256(self) -> str:
        return canonical_sha256(self.to_record())


def build_task_profile_fixture(
    *,
    task_id: str,
    task_class: str,
    language: str,
    repository_context_tokens: int,
    dependency_breadth: int,
    reasoning_complexity: int,
    implementation_complexity: int,
    security_risk: int,
    data_risk: int,
    repository_mutation_risk: int,
    operational_risk: int,
    required_capabilities: tuple[str, ...],
    minimum_quality_micros: int,
    minimum_confidence_micros: int,
    verification_burden: int,
    repair_burden: int,
    critical_path: bool,
    remaining_slack_ms: int,
    delay_sensitivity_micros: int,
    evidence_confidence_micros: int,
    uncertainty_reasons: tuple[str, ...] = (),
) -> TaskProfile:
    """Build the same advisory profile for the same finite fixture inputs."""

    source = {
        "task_id": task_id,
        "task_class": task_class,
        "language": language,
        "repository_context_tokens": repository_context_tokens,
        "dependency_breadth": dependency_breadth,
        "reasoning_complexity": reasoning_complexity,
        "implementation_complexity": implementation_complexity,
        "security_risk": security_risk,
        "data_risk": data_risk,
        "repository_mutation_risk": repository_mutation_risk,
        "operational_risk": operational_risk,
        "required_capabilities": list(required_capabilities),
        "minimum_quality_micros": minimum_quality_micros,
        "minimum_confidence_micros": minimum_confidence_micros,
        "verification_burden": verification_burden,
        "repair_burden": repair_burden,
        "critical_path": critical_path,
        "remaining_slack_ms": remaining_slack_ms,
        "delay_sensitivity_micros": delay_sensitivity_micros,
        "evidence_confidence_micros": evidence_confidence_micros,
        "uncertainty_reasons": list(uncertainty_reasons),
    }
    source_sha256 = canonical_sha256(source)
    return TaskProfile(
        profile_id=f"fixture-profile-{source_sha256[:24]}",
        task_id=task_id,
        task_class=task_class,
        language=language,
        repository_context_tokens=repository_context_tokens,
        dependency_breadth=dependency_breadth,
        reasoning_complexity=reasoning_complexity,
        implementation_complexity=implementation_complexity,
        security_risk=security_risk,
        data_risk=data_risk,
        repository_mutation_risk=repository_mutation_risk,
        operational_risk=operational_risk,
        required_capabilities=required_capabilities,
        minimum_quality_micros=minimum_quality_micros,
        minimum_confidence_micros=minimum_confidence_micros,
        verification_burden=verification_burden,
        repair_burden=repair_burden,
        critical_path=critical_path,
        remaining_slack_ms=remaining_slack_ms,
        delay_sensitivity_micros=delay_sensitivity_micros,
        evidence_confidence_micros=evidence_confidence_micros,
        uncertainty_reasons=uncertainty_reasons,
        source_input_sha256=source_sha256,
    )


@dataclass(frozen=True)
class EconomicEstimate:
    metered_usage_microunits: int
    verification_microunits: int
    retry_microunits: int
    rework_microunits: int
    recovery_microunits: int
    critical_path_time_microunits: int
    avoidable_renewal_microunits: int
    allocated_operating_microunits: int
    local_infrastructure_microunits: int
    opportunity_cost_microunits: int

    def __post_init__(self) -> None:
        for name, value in self.to_record().items():
            _require_nonnegative(name, value)

    @property
    def total_microunits(self) -> int:
        return sum(self.to_record().values())

    def to_record(self) -> dict[str, int]:
        return {
            "metered_usage_microunits": self.metered_usage_microunits,
            "verification_microunits": self.verification_microunits,
            "retry_microunits": self.retry_microunits,
            "rework_microunits": self.rework_microunits,
            "recovery_microunits": self.recovery_microunits,
            "critical_path_time_microunits": self.critical_path_time_microunits,
            "avoidable_renewal_microunits": self.avoidable_renewal_microunits,
            "allocated_operating_microunits": self.allocated_operating_microunits,
            "local_infrastructure_microunits": self.local_infrastructure_microunits,
            "opportunity_cost_microunits": self.opportunity_cost_microunits,
        }


@dataclass(frozen=True)
class CatalogCandidate:
    provider_id: str
    model_id: str
    adapter_version: str
    interface_version: str
    execution_surface_id: str
    qualification_state: QualificationState
    task_classes: tuple[str, ...]
    supported_languages: tuple[str, ...]
    capabilities: tuple[str, ...]
    context_window_tokens: int
    max_output_tokens: int
    quality_micros: int
    confidence_micros: int
    maximum_security_risk: int
    maximum_data_risk: int
    maximum_repository_mutation_risk: int
    maximum_operational_risk: int
    data_policy_id: str
    evidence_snapshot_id: str
    evidence_current: bool
    credential_reference_id: str | None
    requires_credentials: bool
    calls_external_provider: bool
    network_access: bool
    logical_duration_ms: int
    strength_rank: int
    economics: EconomicEstimate

    def __post_init__(self) -> None:
        for name in (
            "provider_id",
            "model_id",
            "execution_surface_id",
            "data_policy_id",
            "evidence_snapshot_id",
        ):
            _require_identifier(name, getattr(self, name))
        for name in ("adapter_version", "interface_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SEMVER_RE.fullmatch(value) is None:
                raise PortfolioFixtureError(f"{name} must be exact semantic version")
        if not isinstance(self.qualification_state, QualificationState):
            raise PortfolioFixtureError("qualification_state must be registered")
        for name in ("task_classes", "supported_languages", "capabilities"):
            _require_canonical_strings(name, getattr(self, name), allow_empty=False)
        for name in (
            "context_window_tokens",
            "max_output_tokens",
            "logical_duration_ms",
            "strength_rank",
        ):
            _require_positive(name, getattr(self, name))
        for name in ("quality_micros", "confidence_micros"):
            _require_micros(name, getattr(self, name))
        for name in (
            "maximum_security_risk",
            "maximum_data_risk",
            "maximum_repository_mutation_risk",
            "maximum_operational_risk",
        ):
            _require_scale(name, getattr(self, name))
        for name in (
            "evidence_current",
            "requires_credentials",
            "calls_external_provider",
            "network_access",
        ):
            if not isinstance(getattr(self, name), bool):
                raise PortfolioFixtureError(f"{name} must be boolean")
        if self.requires_credentials:
            _require_identifier("credential_reference_id", self.credential_reference_id)
        elif self.credential_reference_id is not None:
            raise PortfolioFixtureError(
                "credential_reference_id requires requires_credentials true"
            )
        if not isinstance(self.economics, EconomicEstimate):
            raise PortfolioFixtureError("economics must be EconomicEstimate")

    @property
    def route_id(self) -> str:
        return f"{self.provider_id}/{self.model_id}@{self.adapter_version}"

    def to_record(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "adapter_version": self.adapter_version,
            "interface_version": self.interface_version,
            "execution_surface_id": self.execution_surface_id,
            "qualification_state": self.qualification_state.value,
            "task_classes": list(self.task_classes),
            "supported_languages": list(self.supported_languages),
            "capabilities": list(self.capabilities),
            "context_window_tokens": self.context_window_tokens,
            "max_output_tokens": self.max_output_tokens,
            "quality_micros": self.quality_micros,
            "confidence_micros": self.confidence_micros,
            "maximum_security_risk": self.maximum_security_risk,
            "maximum_data_risk": self.maximum_data_risk,
            "maximum_repository_mutation_risk": self.maximum_repository_mutation_risk,
            "maximum_operational_risk": self.maximum_operational_risk,
            "data_policy_id": self.data_policy_id,
            "evidence_snapshot_id": self.evidence_snapshot_id,
            "evidence_current": self.evidence_current,
            "credential_reference_id": self.credential_reference_id,
            "requires_credentials": self.requires_credentials,
            "calls_external_provider": self.calls_external_provider,
            "network_access": self.network_access,
            "logical_duration_ms": self.logical_duration_ms,
            "strength_rank": self.strength_rank,
            "economics": self.economics.to_record(),
            "expected_total_economic_cost_microunits": self.economics.total_microunits,
        }


@dataclass(frozen=True)
class CatalogSnapshot:
    catalog_version: str
    policy_version: str
    evidence_snapshot_id: str
    candidates: tuple[CatalogCandidate, ...]

    def __post_init__(self) -> None:
        for name in ("catalog_version", "policy_version", "evidence_snapshot_id"):
            _require_identifier(name, getattr(self, name))
        if not isinstance(self.candidates, tuple) or not self.candidates:
            raise PortfolioFixtureError("candidates must be a non-empty tuple")
        if not all(isinstance(item, CatalogCandidate) for item in self.candidates):
            raise PortfolioFixtureError("candidates must contain CatalogCandidate")
        route_ids = tuple(item.route_id for item in self.candidates)
        if route_ids != tuple(sorted(route_ids)) or len(route_ids) != len(set(route_ids)):
            raise PortfolioFixtureError(
                "candidates must have unique route IDs in canonical order"
            )

    def to_record(self) -> dict[str, object]:
        return {
            "catalog_version": self.catalog_version,
            "policy_version": self.policy_version,
            "evidence_snapshot_id": self.evidence_snapshot_id,
            "candidates": [candidate.to_record() for candidate in self.candidates],
        }


@dataclass(frozen=True)
class FixtureAuthorizationEnvelope:
    authorization_id: str
    policy_version: str
    catalog_version: str
    evidence_snapshot_id: str
    authorized_route_ids: tuple[str, ...]
    permitted_execution_surfaces: tuple[str, ...]
    permitted_data_policy_ids: tuple[str, ...]
    permitted_credential_reference_ids: tuple[str, ...]
    max_total_tokens: int
    max_output_tokens: int
    max_cost_microunits: int
    max_duration_ms: int
    max_attempts: int
    max_retries: int
    route_selection_authorized: bool = True
    isolated_fixture_execution_authorized: bool = True
    live_provider_execution_authorized: bool = False
    credential_value_access_authorized: bool = False
    real_repository_access_authorized: bool = False
    target_mutation_authorized: bool = False
    production_operation_authorized: bool = False
    cleanup_execution_authorized: bool = False
    rollback_execution_authorized: bool = False

    def __post_init__(self) -> None:
        for name in (
            "authorization_id",
            "policy_version",
            "catalog_version",
            "evidence_snapshot_id",
        ):
            _require_identifier(name, getattr(self, name))
        for name in (
            "authorized_route_ids",
            "permitted_execution_surfaces",
            "permitted_data_policy_ids",
        ):
            _require_canonical_strings(name, getattr(self, name), allow_empty=False)
        _require_canonical_strings(
            "permitted_credential_reference_ids",
            self.permitted_credential_reference_ids,
            allow_empty=True,
        )
        for name in (
            "max_total_tokens",
            "max_output_tokens",
            "max_duration_ms",
            "max_attempts",
        ):
            _require_positive(name, getattr(self, name))
        for name in ("max_cost_microunits", "max_retries"):
            _require_nonnegative(name, getattr(self, name))
        if self.max_output_tokens > self.max_total_tokens:
            raise PortfolioFixtureError("max_output_tokens exceeds max_total_tokens")
        for name in (
            "route_selection_authorized",
            "isolated_fixture_execution_authorized",
            "live_provider_execution_authorized",
            "credential_value_access_authorized",
            "real_repository_access_authorized",
            "target_mutation_authorized",
            "production_operation_authorized",
            "cleanup_execution_authorized",
            "rollback_execution_authorized",
        ):
            if not isinstance(getattr(self, name), bool):
                raise PortfolioFixtureError(f"{name} must be boolean")

    def to_record(self) -> dict[str, object]:
        return {
            "authorization_id": self.authorization_id,
            "policy_version": self.policy_version,
            "catalog_version": self.catalog_version,
            "evidence_snapshot_id": self.evidence_snapshot_id,
            "authorized_route_ids": list(self.authorized_route_ids),
            "permitted_execution_surfaces": list(self.permitted_execution_surfaces),
            "permitted_data_policy_ids": list(self.permitted_data_policy_ids),
            "permitted_credential_reference_ids": list(
                self.permitted_credential_reference_ids
            ),
            "max_total_tokens": self.max_total_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_cost_microunits": self.max_cost_microunits,
            "max_duration_ms": self.max_duration_ms,
            "max_attempts": self.max_attempts,
            "max_retries": self.max_retries,
            "route_selection_authorized": self.route_selection_authorized,
            "isolated_fixture_execution_authorized": self.isolated_fixture_execution_authorized,
            "live_provider_execution_authorized": self.live_provider_execution_authorized,
            "credential_value_access_authorized": self.credential_value_access_authorized,
            "real_repository_access_authorized": self.real_repository_access_authorized,
            "target_mutation_authorized": self.target_mutation_authorized,
            "production_operation_authorized": self.production_operation_authorized,
            "cleanup_execution_authorized": self.cleanup_execution_authorized,
            "rollback_execution_authorized": self.rollback_execution_authorized,
        }


@dataclass(frozen=True)
class RouteEvaluation:
    route_id: str
    eligible: bool
    hard_floor_reasons: tuple[str, ...]
    expected_total_economic_cost_microunits: int
    logical_duration_ms: int
    strength_rank: int

    def to_record(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "eligible": self.eligible,
            "hard_floor_reasons": list(self.hard_floor_reasons),
            "expected_total_economic_cost_microunits": self.expected_total_economic_cost_microunits,
            "logical_duration_ms": self.logical_duration_ms,
            "strength_rank": self.strength_rank,
        }


@dataclass(frozen=True)
class RouteDecision:
    status: RouteDecisionStatus
    policy_version: str
    catalog_version: str
    authorization_id: str
    profile_sha256: str
    selected_route_id: str | None
    ordered_eligible_route_ids: tuple[str, ...]
    availability_failover_route_ids: tuple[str, ...]
    quality_escalation_route_ids: tuple[str, ...]
    same_route_repair_limit: int
    evaluations: tuple[RouteEvaluation, ...]
    stop_reason: str | None
    evidence_sha256: str
    authority_effect: str = "none"
    provider_invocations: int = 0
    network_operations: int = 0
    credential_value_accesses: int = 0

    def to_record(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "policy_version": self.policy_version,
            "catalog_version": self.catalog_version,
            "authorization_id": self.authorization_id,
            "profile_sha256": self.profile_sha256,
            "selected_route_id": self.selected_route_id,
            "ordered_eligible_route_ids": list(self.ordered_eligible_route_ids),
            "availability_failover_route_ids": list(
                self.availability_failover_route_ids
            ),
            "quality_escalation_route_ids": list(self.quality_escalation_route_ids),
            "same_route_repair_limit": self.same_route_repair_limit,
            "evaluations": [evaluation.to_record() for evaluation in self.evaluations],
            "stop_reason": self.stop_reason,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "side_effects": {
                "provider_invocations": self.provider_invocations,
                "network_operations": self.network_operations,
                "credential_value_accesses": self.credential_value_accesses,
            },
        }


class DeterministicProviderRouter:
    """Select one isolated fixture route after every hard floor passes."""

    def __init__(self, policy_version: str) -> None:
        _require_identifier("policy_version", policy_version)
        self.policy_version = policy_version

    def route(
        self,
        profile: TaskProfile,
        authorization: FixtureAuthorizationEnvelope,
        catalog: CatalogSnapshot,
    ) -> RouteDecision:
        if not isinstance(profile, TaskProfile):
            raise PortfolioFixtureError("profile must be TaskProfile")
        if not isinstance(authorization, FixtureAuthorizationEnvelope):
            raise PortfolioFixtureError(
                "authorization must be FixtureAuthorizationEnvelope"
            )
        if not isinstance(catalog, CatalogSnapshot):
            raise PortfolioFixtureError("catalog must be CatalogSnapshot")

        global_reasons = self._global_reasons(authorization, catalog)
        evaluations = tuple(
            self._evaluate(candidate, profile, authorization, catalog, global_reasons)
            for candidate in catalog.candidates
        )
        eligible = sorted(
            (evaluation for evaluation in evaluations if evaluation.eligible),
            key=lambda item: (
                item.expected_total_economic_cost_microunits,
                item.logical_duration_ms,
                item.route_id,
            ),
        )
        selected = eligible[0] if eligible else None
        selected_id = selected.route_id if selected is not None else None
        remaining_attempts = max(0, authorization.max_attempts - 1)
        failover = tuple(
            item.route_id for item in eligible[1 : 1 + remaining_attempts]
        )
        escalation: tuple[str, ...] = ()
        if selected is not None:
            stronger = sorted(
                (
                    item
                    for item in eligible
                    if item.route_id != selected.route_id
                    and item.strength_rank > selected.strength_rank
                ),
                key=lambda item: (
                    item.strength_rank,
                    item.expected_total_economic_cost_microunits,
                    item.route_id,
                ),
            )
            escalation = tuple(
                item.route_id for item in stronger[:remaining_attempts]
            )
        stop_reason = None
        if selected is None:
            stop_reason = (
                global_reasons[0] if global_reasons else FailureClass.EMPTY_ELIGIBLE_SET.value
            )
        decision_body = {
            "policy_version": self.policy_version,
            "profile": profile.to_record(),
            "authorization": authorization.to_record(),
            "catalog": catalog.to_record(),
            "evaluations": [evaluation.to_record() for evaluation in evaluations],
            "selected_route_id": selected_id,
            "ordered_eligible_route_ids": [item.route_id for item in eligible],
            "availability_failover_route_ids": list(failover),
            "quality_escalation_route_ids": list(escalation),
            "same_route_repair_limit": (
                min(1, authorization.max_retries) if selected is not None else 0
            ),
            "stop_reason": stop_reason,
            "authority_effect": "none",
        }
        return RouteDecision(
            status=(
                RouteDecisionStatus.SELECTED
                if selected is not None
                else RouteDecisionStatus.BLOCKED
            ),
            policy_version=self.policy_version,
            catalog_version=catalog.catalog_version,
            authorization_id=authorization.authorization_id,
            profile_sha256=profile.sha256(),
            selected_route_id=selected_id,
            ordered_eligible_route_ids=tuple(item.route_id for item in eligible),
            availability_failover_route_ids=failover,
            quality_escalation_route_ids=escalation,
            same_route_repair_limit=(
                min(1, authorization.max_retries) if selected is not None else 0
            ),
            evaluations=evaluations,
            stop_reason=stop_reason,
            evidence_sha256=canonical_sha256(decision_body),
        )

    def _global_reasons(
        self,
        authorization: FixtureAuthorizationEnvelope,
        catalog: CatalogSnapshot,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if not authorization.route_selection_authorized:
            reasons.append("ROUTE_SELECTION_NOT_AUTHORIZED")
        if not authorization.isolated_fixture_execution_authorized:
            reasons.append("ISOLATED_FIXTURE_EXECUTION_NOT_AUTHORIZED")
        if (
            authorization.live_provider_execution_authorized
            or authorization.credential_value_access_authorized
            or authorization.real_repository_access_authorized
            or authorization.target_mutation_authorized
            or authorization.production_operation_authorized
            or authorization.cleanup_execution_authorized
            or authorization.rollback_execution_authorized
        ):
            reasons.append("P15B_EXTERNAL_AUTHORITY_FORBIDDEN")
        if authorization.policy_version != self.policy_version:
            reasons.append("POLICY_VERSION_MISMATCH")
        if catalog.policy_version != self.policy_version:
            reasons.append("CATALOG_POLICY_VERSION_MISMATCH")
        if authorization.catalog_version != catalog.catalog_version:
            reasons.append("CATALOG_VERSION_MISMATCH")
        if authorization.evidence_snapshot_id != catalog.evidence_snapshot_id:
            reasons.append("EVIDENCE_SNAPSHOT_MISMATCH")
        return tuple(reasons)

    def _evaluate(
        self,
        candidate: CatalogCandidate,
        profile: TaskProfile,
        authorization: FixtureAuthorizationEnvelope,
        catalog: CatalogSnapshot,
        global_reasons: tuple[str, ...],
    ) -> RouteEvaluation:
        reasons = list(global_reasons)
        if candidate.qualification_state.value not in _ELIGIBLE_STATES:
            reasons.append("QUALIFICATION_STATE_INELIGIBLE")
        if candidate.route_id not in authorization.authorized_route_ids:
            reasons.append("ROUTE_NOT_AUTHORIZED")
        if candidate.execution_surface_id != "isolated-fixture":
            reasons.append("NON_FIXTURE_SURFACE_FORBIDDEN")
        if candidate.execution_surface_id not in authorization.permitted_execution_surfaces:
            reasons.append("EXECUTION_SURFACE_NOT_AUTHORIZED")
        if candidate.calls_external_provider:
            reasons.append("EXTERNAL_PROVIDER_FORBIDDEN")
        if candidate.network_access:
            reasons.append("NETWORK_ACCESS_FORBIDDEN")
        if candidate.requires_credentials:
            reasons.append("CREDENTIAL_USE_FORBIDDEN")
            if candidate.credential_reference_id not in (
                authorization.permitted_credential_reference_ids
            ):
                reasons.append("CREDENTIAL_REFERENCE_NOT_AUTHORIZED")
        if profile.task_class not in candidate.task_classes:
            reasons.append("TASK_CLASS_UNSUPPORTED")
        if profile.language not in candidate.supported_languages:
            reasons.append("LANGUAGE_UNSUPPORTED")
        if not set(profile.required_capabilities) <= set(candidate.capabilities):
            reasons.append("CAPABILITY_FLOOR_UNMET")
        if profile.repository_context_tokens > candidate.context_window_tokens:
            reasons.append("CONTEXT_FLOOR_UNMET")
        if authorization.max_total_tokens > candidate.context_window_tokens:
            reasons.append("TOKEN_ENVELOPE_EXCEEDS_CONTEXT")
        if authorization.max_output_tokens > candidate.max_output_tokens:
            reasons.append("OUTPUT_FLOOR_UNMET")
        if candidate.quality_micros < profile.minimum_quality_micros:
            reasons.append("QUALITY_FLOOR_UNMET")
        if candidate.confidence_micros < profile.minimum_confidence_micros:
            reasons.append("CONFIDENCE_FLOOR_UNMET")
        for profile_value, candidate_value, code in (
            (profile.security_risk, candidate.maximum_security_risk, "SECURITY_RISK_FLOOR_UNMET"),
            (profile.data_risk, candidate.maximum_data_risk, "DATA_RISK_FLOOR_UNMET"),
            (
                profile.repository_mutation_risk,
                candidate.maximum_repository_mutation_risk,
                "REPOSITORY_MUTATION_RISK_FLOOR_UNMET",
            ),
            (
                profile.operational_risk,
                candidate.maximum_operational_risk,
                "OPERATIONAL_RISK_FLOOR_UNMET",
            ),
        ):
            if profile_value > candidate_value:
                reasons.append(code)
        if candidate.data_policy_id not in authorization.permitted_data_policy_ids:
            reasons.append("DATA_POLICY_NOT_AUTHORIZED")
        if not candidate.evidence_current:
            reasons.append("STALE_EVIDENCE")
        if candidate.evidence_snapshot_id != catalog.evidence_snapshot_id:
            reasons.append("CANDIDATE_EVIDENCE_SNAPSHOT_MISMATCH")
        if candidate.logical_duration_ms > authorization.max_duration_ms:
            reasons.append("TIME_BUDGET_EXCEEDED")
        if candidate.economics.total_microunits > authorization.max_cost_microunits:
            reasons.append("HARD_COST_BUDGET_EXCEEDED")
        stable_reasons = tuple(sorted(set(reasons)))
        return RouteEvaluation(
            route_id=candidate.route_id,
            eligible=not stable_reasons,
            hard_floor_reasons=stable_reasons,
            expected_total_economic_cost_microunits=(
                candidate.economics.total_microunits
            ),
            logical_duration_ms=candidate.logical_duration_ms,
            strength_rank=candidate.strength_rank,
        )


@dataclass(frozen=True)
class FailurePolicy:
    failure_class: FailureClass
    disposition: FailureDisposition
    availability_failover_allowed: bool
    same_route_repair_allowed: bool
    stronger_route_escalation_allowed: bool
    provider_switch_allowed: bool
    terminal: bool
    stable_reason: str

    def to_record(self) -> dict[str, object]:
        return {
            "failure_class": self.failure_class.value,
            "disposition": self.disposition.value,
            "availability_failover_allowed": self.availability_failover_allowed,
            "same_route_repair_allowed": self.same_route_repair_allowed,
            "stronger_route_escalation_allowed": self.stronger_route_escalation_allowed,
            "provider_switch_allowed": self.provider_switch_allowed,
            "terminal": self.terminal,
            "stable_reason": self.stable_reason,
        }


_AVAILABILITY_FAILURES = frozenset(
    {
        FailureClass.MISSING_CREDENTIAL_REFERENCE,
        FailureClass.INSUFFICIENT_BALANCE,
        FailureClass.QUOTA_EXHAUSTED,
        FailureClass.RATE_LIMIT,
        FailureClass.TIMEOUT,
        FailureClass.PROVIDER_OUTAGE,
    }
)
_QUALITY_FAILURES = frozenset(
    {FailureClass.QUALITY_REJECTED, FailureClass.ACCEPTANCE_REJECTED}
)
_BLOCKING_FAILURES = frozenset(
    {
        FailureClass.POLICY_DENIED,
        FailureClass.DATA_POLICY_DENIED,
        FailureClass.AUTHORIZATION_MISMATCH,
        FailureClass.HARD_BUDGET_EXHAUSTED,
        FailureClass.STALE_PRECONDITION,
        FailureClass.MISSING_REQUIRED_EVIDENCE,
    }
)
_STOP_FAILURES = frozenset(
    {
        FailureClass.EMPTY_ELIGIBLE_SET,
        FailureClass.ATTEMPT_EXHAUSTED,
        FailureClass.CANCELLED,
        FailureClass.NO_PROGRESS,
    }
)


def classify_failure(failure_class: FailureClass) -> FailurePolicy:
    if not isinstance(failure_class, FailureClass):
        raise PortfolioFixtureError("failure_class must be registered")
    if failure_class in _AVAILABILITY_FAILURES:
        return FailurePolicy(
            failure_class=failure_class,
            disposition=FailureDisposition.AVAILABILITY_FAILOVER,
            availability_failover_allowed=True,
            same_route_repair_allowed=False,
            stronger_route_escalation_allowed=False,
            provider_switch_allowed=True,
            terminal=False,
            stable_reason="availability failure may use the next already eligible route",
        )
    if failure_class in _QUALITY_FAILURES:
        return FailurePolicy(
            failure_class=failure_class,
            disposition=FailureDisposition.SAME_ROUTE_REPAIR_THEN_ESCALATE,
            availability_failover_allowed=False,
            same_route_repair_allowed=True,
            stronger_route_escalation_allowed=True,
            provider_switch_allowed=True,
            terminal=False,
            stable_reason="quality failure uses bounded same-route repair before stronger-route escalation",
        )
    if failure_class in _BLOCKING_FAILURES:
        return FailurePolicy(
            failure_class=failure_class,
            disposition=FailureDisposition.BLOCK_NO_PROVIDER_BYPASS,
            availability_failover_allowed=False,
            same_route_repair_allowed=False,
            stronger_route_escalation_allowed=False,
            provider_switch_allowed=False,
            terminal=True,
            stable_reason="hard block cannot be bypassed by switching providers",
        )
    if failure_class in _STOP_FAILURES:
        return FailurePolicy(
            failure_class=failure_class,
            disposition=FailureDisposition.STOP,
            availability_failover_allowed=False,
            same_route_repair_allowed=False,
            stronger_route_escalation_allowed=False,
            provider_switch_allowed=False,
            terminal=True,
            stable_reason="bounded execution stops without another route attempt",
        )
    raise PortfolioFixtureError("failure_class has no disposition")


class PortfolioFixtureAdapter:
    """Structural AIWorkerProvider implementation with no external capability."""

    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def __init__(
        self,
        candidate: CatalogCandidate,
        scenarios: Mapping[str, FixtureScenario],
    ) -> None:
        if not isinstance(candidate, CatalogCandidate):
            raise PortfolioFixtureError("candidate must be CatalogCandidate")
        if (
            candidate.execution_surface_id != "isolated-fixture"
            or candidate.calls_external_provider
            or candidate.network_access
            or candidate.requires_credentials
        ):
            raise PortfolioFixtureError("FIXTURE_ADAPTER_EXTERNAL_SURFACE_FORBIDDEN")
        self._candidate = candidate
        self._delegate = DeterministicFixtureProvider(scenarios)

    @property
    def provider_id(self) -> str:
        return self._candidate.provider_id

    @property
    def model_id(self) -> str:
        return self._candidate.model_id

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._candidate.capabilities

    @property
    def call_count(self) -> int:
        return self._delegate.call_count

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: CancellationSignal | None = None,
    ) -> ProviderResponse:
        if not isinstance(request, AIWorkerRequest):
            return _adapter_error(
                AIWorkerErrorCode.INVALID_REQUEST,
                "fixture adapter requires AIWorkerRequest",
            )
        if (
            request.model.provider_id != self.provider_id
            or request.model.model_id != self.model_id
        ):
            return _adapter_error(
                AIWorkerErrorCode.PROVIDER_MISMATCH,
                "fixture adapter provider or model mismatch",
            )
        if (
            request.execution_mode != "fixture"
            or request.writes_target_repo
            or request.executes_target_repo_mutation
            or request.production_deployment
        ):
            return _adapter_error(
                AIWorkerErrorCode.INVALID_REQUEST,
                "fixture adapter rejects live or mutation authority",
            )
        return self._delegate.invoke(request, cancellation)


def _adapter_error(code: AIWorkerErrorCode, message: str) -> ProviderResponse:
    return ProviderResponse(
        output=None,
        usage=AIWorkerUsage(),
        error=AIWorkerError(code=code, message=message),
    )


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise PortfolioFixtureError(f"{name} must be a bounded identifier")


def _require_sha256(name: str, value: object) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PortfolioFixtureError(f"{name} must be lowercase SHA-256")


def _require_canonical_strings(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
        raise PortfolioFixtureError(f"{name} must be a tuple of strings")
    if not allow_empty and not value:
        raise PortfolioFixtureError(f"{name} must be non-empty")
    if value != tuple(sorted(value)) or len(value) != len(set(value)):
        raise PortfolioFixtureError(f"{name} must be unique and canonically ordered")
    for item in value:
        _require_identifier(name, item)


def _require_nonnegative(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PortfolioFixtureError(f"{name} must be a non-negative integer")


def _require_positive(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise PortfolioFixtureError(f"{name} must be a positive integer")


def _require_scale(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
        raise PortfolioFixtureError(f"{name} must be an integer from zero to five")


def _require_micros(name: str, value: object) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= _MICRO_MAX
    ):
        raise PortfolioFixtureError(
            f"{name} must be an integer from zero to one million"
        )
