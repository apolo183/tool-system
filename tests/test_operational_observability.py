from __future__ import annotations

import pytest

from tool_system.operational_observability import (
    AlertPolicy, AlertSeverity, IncidentObservation, IncidentState,
    SloPolicy, SloStatus, TelemetrySample, advance_incident,
    evaluate_alert, evaluate_slo,
)
from tool_system.release_governance import SemanticVersion

def _sample(success: int = 999, latency: int = 995) -> TelemetrySample:
    return TelemetrySample(
        service_id="core", release_version=SemanticVersion(1, 0, 0),
        window_start_utc=100, window_end_utc=200,
        successful_events=success, total_events=1000,
        latency_good_events=latency,
    )

def test_slo_uses_deterministic_integer_ppm() -> None:
    result = evaluate_slo(
        sample=_sample(), policy=SloPolicy(999_000, 995_000)
    )
    assert result.status is SloStatus.PASS
    assert result.availability_ppm == 999_000
    assert result.latency_good_ppm == 995_000
    assert result.alert_delivery_authorized is False

def test_breaches_produce_ordered_non_delivering_alert() -> None:
    slo = evaluate_slo(
        sample=_sample(900, 800), policy=SloPolicy(999_000, 995_000)
    )
    assert slo.reasons == (
        "AVAILABILITY_SLO_BREACH", "LATENCY_SLO_BREACH"
    )
    alert = evaluate_alert(slo=slo, policy=AlertPolicy())
    assert alert.severity is AlertSeverity.CRITICAL
    assert alert.delivery_authorized is False

def test_incident_state_machine_requires_evidence_and_never_acts() -> None:
    alert = evaluate_alert(
        slo=evaluate_slo(
            sample=_sample(900, 800), policy=SloPolicy(999_000, 995_000)
        ),
        policy=AlertPolicy(),
    )
    first = advance_incident(IncidentObservation(IncidentState.OBSERVED, alert))
    assert first.next_state is IncidentState.TRIAGE_REQUIRED
    assert first.external_action_authorized is False
    held = advance_incident(
        IncidentObservation(IncidentState.TRIAGE_REQUIRED, alert)
    )
    assert held.reasons == ("TRIAGE_EVIDENCE_MISSING",)
    escalated = advance_incident(
        IncidentObservation(
            IncidentState.TRIAGE_REQUIRED, alert, triage_recorded=True
        )
    )
    assert escalated.next_state is IncidentState.ESCALATION_REQUIRED
    assert escalated.external_action_authorized is False

def test_invalid_telemetry_and_policy_fail_closed() -> None:
    with pytest.raises(ValueError):
        TelemetrySample(
            "core", SemanticVersion(1, 0, 0), 2, 1, 1, 1, 1
        )
    with pytest.raises(ValueError):
        SloPolicy(1_000_001, 1)
