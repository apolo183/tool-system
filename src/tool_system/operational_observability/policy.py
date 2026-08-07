"""Pure telemetry, SLO, alert, and incident-response decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.release_governance import SemanticVersion

@dataclass(frozen=True)
class TelemetrySample:
    service_id: str
    release_version: SemanticVersion
    window_start_utc: int
    window_end_utc: int
    successful_events: int
    total_events: int
    latency_good_events: int

    def __post_init__(self) -> None:
        if not self.service_id.strip():
            raise ValueError("service id must be explicit")
        if self.window_start_utc < 0 or self.window_end_utc <= self.window_start_utc:
            raise ValueError("telemetry window must be positive and ordered")
        if self.total_events <= 0:
            raise ValueError("telemetry total events must be positive")
        if not 0 <= self.successful_events <= self.total_events:
            raise ValueError("successful events must be within total events")
        if not 0 <= self.latency_good_events <= self.total_events:
            raise ValueError("latency-good events must be within total events")

@dataclass(frozen=True)
class SloPolicy:
    minimum_availability_ppm: int
    minimum_latency_good_ppm: int

    def __post_init__(self) -> None:
        for value in (self.minimum_availability_ppm, self.minimum_latency_good_ppm):
            if not 0 <= value <= 1_000_000:
                raise ValueError("SLO thresholds must be parts per million")

class SloStatus(str, Enum):
    PASS = "PASS"
    BREACH = "BREACH"

@dataclass(frozen=True)
class SloDecision:
    status: SloStatus
    availability_ppm: int
    latency_good_ppm: int
    reasons: tuple[str, ...]
    alert_delivery_authorized: bool = False
    incident_action_authorized: bool = False

def evaluate_slo(*, sample: TelemetrySample, policy: SloPolicy) -> SloDecision:
    availability = sample.successful_events * 1_000_000 // sample.total_events
    latency = sample.latency_good_events * 1_000_000 // sample.total_events
    reasons: list[str] = []
    if availability < policy.minimum_availability_ppm:
        reasons.append("AVAILABILITY_SLO_BREACH")
    if latency < policy.minimum_latency_good_ppm:
        reasons.append("LATENCY_SLO_BREACH")
    return SloDecision(
        status=SloStatus.BREACH if reasons else SloStatus.PASS,
        availability_ppm=availability,
        latency_good_ppm=latency,
        reasons=tuple(reasons),
    )

class AlertSeverity(str, Enum):
    NONE = "NONE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class AlertPolicy:
    critical_reason_count: int = 2

    def __post_init__(self) -> None:
        if self.critical_reason_count < 1:
            raise ValueError("critical reason count must be positive")

@dataclass(frozen=True)
class AlertDecision:
    severity: AlertSeverity
    reasons: tuple[str, ...]
    delivery_authorized: bool = False

def evaluate_alert(*, slo: SloDecision, policy: AlertPolicy) -> AlertDecision:
    if slo.status is SloStatus.PASS:
        return AlertDecision(AlertSeverity.NONE, ())
    severity = (
        AlertSeverity.CRITICAL
        if len(slo.reasons) >= policy.critical_reason_count
        else AlertSeverity.WARNING
    )
    return AlertDecision(severity, slo.reasons)

class IncidentState(str, Enum):
    OBSERVED = "OBSERVED"
    TRIAGE_REQUIRED = "TRIAGE_REQUIRED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    RESOLUTION_EVIDENCE_REQUIRED = "RESOLUTION_EVIDENCE_REQUIRED"
    CLOSED = "CLOSED"

@dataclass(frozen=True)
class IncidentObservation:
    current_state: IncidentState
    alert: AlertDecision
    triage_recorded: bool = False
    escalation_recorded: bool = False
    resolution_evidence_recorded: bool = False

@dataclass(frozen=True)
class IncidentDecision:
    next_state: IncidentState
    reasons: tuple[str, ...]
    external_action_authorized: bool = False

def advance_incident(observation: IncidentObservation) -> IncidentDecision:
    state = observation.current_state
    alert = observation.alert
    if state is IncidentState.OBSERVED:
        if alert.severity is AlertSeverity.NONE:
            return IncidentDecision(IncidentState.CLOSED, ("NO_ALERT",))
        return IncidentDecision(IncidentState.TRIAGE_REQUIRED, ("TRIAGE_REQUIRED",))
    if state is IncidentState.TRIAGE_REQUIRED:
        if not observation.triage_recorded:
            return IncidentDecision(state, ("TRIAGE_EVIDENCE_MISSING",))
        if alert.severity is AlertSeverity.CRITICAL:
            return IncidentDecision(IncidentState.ESCALATION_REQUIRED, ("ESCALATION_REQUIRED",))
        return IncidentDecision(IncidentState.RESOLUTION_EVIDENCE_REQUIRED, ("RESOLUTION_EVIDENCE_REQUIRED",))
    if state is IncidentState.ESCALATION_REQUIRED:
        if not observation.escalation_recorded:
            return IncidentDecision(state, ("ESCALATION_EVIDENCE_MISSING",))
        return IncidentDecision(IncidentState.RESOLUTION_EVIDENCE_REQUIRED, ("RESOLUTION_EVIDENCE_REQUIRED",))
    if state is IncidentState.RESOLUTION_EVIDENCE_REQUIRED:
        if not observation.resolution_evidence_recorded:
            return IncidentDecision(state, ("RESOLUTION_EVIDENCE_MISSING",))
        return IncidentDecision(IncidentState.CLOSED, ("RESOLUTION_EVIDENCE_ACCEPTED",))
    return IncidentDecision(IncidentState.CLOSED, ("ALREADY_CLOSED",))
