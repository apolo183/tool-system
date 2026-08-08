from __future__ import annotations

import pytest

from tool_system.operational_observability import IncidentState, SloStatus
from tool_system.production_readiness import (
    CoreOperationsEvidence,
    CoreOperationsReadinessStatus,
    evaluate_core_operations_readiness,
)
from tool_system.record_retention import RetentionClass, RetentionIndexEntry
from tool_system.recovery_planning import (
    BackupVerificationStatus,
    DisasterRecoveryStatus,
)
from tool_system.subscription_capacity import CapacityStatus, SubscriptionChannel


def _evidence(**overrides):
    values = dict(
        runbook_id="tool-system-operator-runbook",
        runbook_version="1.0.0",
        backup_verification_status=BackupVerificationStatus.PASS,
        disaster_recovery_status=DisasterRecoveryStatus.PASS,
        slo_status=SloStatus.PASS,
        incident_state=IncidentState.CLOSED,
        retention_index_entries=(
            RetentionIndexEntry(
                record_id="audit-1",
                retention_class=RetentionClass.AUDIT,
                expires_at_utc=200,
                content_sha256="a" * 64,
                legal_hold=False,
                archived=True,
            ),
        ),
        subscription_capacity=(
            (SubscriptionChannel.CHATGPT_WEB, CapacityStatus.HEALTHY),
            (SubscriptionChannel.CODEX_CLI, CapacityStatus.CONSERVE),
        ),
        deprecation_policy_evidence_present=True,
    )
    values.update(overrides)
    return CoreOperationsEvidence(**values)


def test_complete_core_evidence_only_reaches_acceptance_review() -> None:
    result = evaluate_core_operations_readiness(_evidence())
    assert result.status is (
        CoreOperationsReadinessStatus.READY_FOR_P16_ACCEPTANCE_REVIEW
    )
    assert result.reasons == ("SEPARATE_P16_ACCEPTANCE_DECISION_REQUIRED",)
    assert result.operator_review_required is True
    assert result.p16_acceptance_authorized is False
    assert result.production_deployment_authorized is False
    assert result.production_operation_authorized is False
    assert result.external_action_authorized is False


@pytest.mark.parametrize(
    "overrides,reason",
    [
        (
            {"backup_verification_status": BackupVerificationStatus.BLOCKED},
            "BACKUP_VERIFICATION_BLOCKED",
        ),
        (
            {"disaster_recovery_status": DisasterRecoveryStatus.BLOCKED},
            "DISASTER_RECOVERY_EVIDENCE_BLOCKED",
        ),
        ({"slo_status": SloStatus.BREACH}, "SLO_EVIDENCE_BLOCKED"),
        (
            {"incident_state": IncidentState.TRIAGE_REQUIRED},
            "INCIDENT_NOT_CLOSED",
        ),
        ({"retention_index_entries": ()}, "RETENTION_INDEX_EVIDENCE_MISSING"),
        (
            {
                "subscription_capacity": (
                    (
                        SubscriptionChannel.CHATGPT_WEB,
                        CapacityStatus.BLOCK_NEW_WORK,
                    ),
                )
            },
            "NO_ELIGIBLE_SUBSCRIPTION_CHANNEL",
        ),
        (
            {"deprecation_policy_evidence_present": False},
            "DEPRECATION_POLICY_EVIDENCE_MISSING",
        ),
    ],
)
def test_each_missing_prerequisite_blocks(overrides, reason) -> None:
    result = evaluate_core_operations_readiness(_evidence(**overrides))
    assert result.status is CoreOperationsReadinessStatus.BLOCKED
    assert reason in result.reasons
    assert result.external_action_authorized is False


def test_duplicate_channels_and_retention_ids_fail_closed() -> None:
    with pytest.raises(ValueError):
        _evidence(
            subscription_capacity=(
                (SubscriptionChannel.CODEX_CLI, CapacityStatus.HEALTHY),
                (SubscriptionChannel.CODEX_CLI, CapacityStatus.CONSERVE),
            )
        )
    entry = _evidence().retention_index_entries[0]
    with pytest.raises(ValueError):
        _evidence(retention_index_entries=(entry, entry))
