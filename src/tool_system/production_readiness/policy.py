"""Pure P16 Core sustainable-operations readiness decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.operational_observability import IncidentState, SloStatus
from tool_system.record_retention import RetentionIndexEntry
from tool_system.recovery_planning import (
    BackupVerificationStatus,
    DisasterRecoveryStatus,
)
from tool_system.subscription_capacity import CapacityStatus, SubscriptionChannel


class CoreOperationsReadinessStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_P16_ACCEPTANCE_REVIEW = "READY_FOR_P16_ACCEPTANCE_REVIEW"


@dataclass(frozen=True)
class CoreOperationsEvidence:
    runbook_id: str
    runbook_version: str
    backup_verification_status: BackupVerificationStatus
    disaster_recovery_status: DisasterRecoveryStatus
    slo_status: SloStatus
    incident_state: IncidentState
    retention_index_entries: tuple[RetentionIndexEntry, ...]
    subscription_capacity: tuple[
        tuple[SubscriptionChannel, CapacityStatus], ...
    ]
    deprecation_policy_evidence_present: bool

    def __post_init__(self) -> None:
        if not self.runbook_id.strip() or not self.runbook_version.strip():
            raise ValueError("runbook identity and version must be explicit")
        channels = [channel for channel, _ in self.subscription_capacity]
        if len(channels) != len(set(channels)):
            raise ValueError("subscription channels must be unique")
        record_ids = [entry.record_id for entry in self.retention_index_entries]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("retention record ids must be unique")


@dataclass(frozen=True)
class CoreOperationsReadinessDecision:
    status: CoreOperationsReadinessStatus
    reasons: tuple[str, ...]
    operator_review_required: bool = True
    p16_acceptance_authorized: bool = False
    production_deployment_authorized: bool = False
    production_operation_authorized: bool = False
    external_action_authorized: bool = False


def evaluate_core_operations_readiness(
    evidence: CoreOperationsEvidence,
) -> CoreOperationsReadinessDecision:
    reasons: list[str] = []
    if evidence.backup_verification_status is not BackupVerificationStatus.PASS:
        reasons.append("BACKUP_VERIFICATION_BLOCKED")
    if evidence.disaster_recovery_status is not DisasterRecoveryStatus.PASS:
        reasons.append("DISASTER_RECOVERY_EVIDENCE_BLOCKED")
    if evidence.slo_status is not SloStatus.PASS:
        reasons.append("SLO_EVIDENCE_BLOCKED")
    if evidence.incident_state is not IncidentState.CLOSED:
        reasons.append("INCIDENT_NOT_CLOSED")
    if not evidence.retention_index_entries:
        reasons.append("RETENTION_INDEX_EVIDENCE_MISSING")
    eligible_capacity = {
        CapacityStatus.HEALTHY,
        CapacityStatus.CONSERVE,
    }
    if not any(
        status in eligible_capacity
        for _, status in evidence.subscription_capacity
    ):
        reasons.append("NO_ELIGIBLE_SUBSCRIPTION_CHANNEL")
    if not evidence.deprecation_policy_evidence_present:
        reasons.append("DEPRECATION_POLICY_EVIDENCE_MISSING")
    if reasons:
        return CoreOperationsReadinessDecision(
            CoreOperationsReadinessStatus.BLOCKED,
            tuple(reasons),
        )
    return CoreOperationsReadinessDecision(
        CoreOperationsReadinessStatus.READY_FOR_P16_ACCEPTANCE_REVIEW,
        ("SEPARATE_P16_ACCEPTANCE_DECISION_REQUIRED",),
    )
