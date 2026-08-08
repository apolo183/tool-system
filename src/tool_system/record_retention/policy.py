"""Pure audit/run retention, archival, and deletion decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.operational_observability import IncidentState

class RetentionClass(str, Enum):
    AUDIT = "AUDIT"
    RUN = "RUN"
    INCIDENT = "INCIDENT"

@dataclass(frozen=True)
class RetentionPolicy:
    retention_class: RetentionClass
    retention_seconds: int
    archive_before_deletion: bool

    def __post_init__(self) -> None:
        if self.retention_seconds < 1:
            raise ValueError("retention duration must be positive")

@dataclass(frozen=True)
class RecordMetadata:
    record_id: str
    retention_class: RetentionClass
    created_at_utc: int
    content_sha256: str
    legal_hold: bool = False
    archived: bool = False
    incident_state: IncidentState | None = None

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record id must be explicit")
        if self.created_at_utc < 0:
            raise ValueError("record creation time must be non-negative")
        if len(self.content_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.content_sha256
        ):
            raise ValueError("record content hash must be lowercase SHA256")
        if self.retention_class is RetentionClass.INCIDENT:
            if self.incident_state is None:
                raise ValueError("incident records require incident state")
        elif self.incident_state is not None:
            raise ValueError("non-incident records cannot carry incident state")

@dataclass(frozen=True)
class RetentionIndexEntry:
    record_id: str
    retention_class: RetentionClass
    expires_at_utc: int
    content_sha256: str
    legal_hold: bool
    archived: bool

def build_retention_index(
    *, record: RecordMetadata, policy: RetentionPolicy
) -> RetentionIndexEntry:
    if record.retention_class is not policy.retention_class:
        raise ValueError("record and retention policy classes must match")
    return RetentionIndexEntry(
        record_id=record.record_id,
        retention_class=record.retention_class,
        expires_at_utc=record.created_at_utc + policy.retention_seconds,
        content_sha256=record.content_sha256,
        legal_hold=record.legal_hold,
        archived=record.archived,
    )

class ArchiveStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION = (
        "READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION"
    )

@dataclass(frozen=True)
class ArchiveDecision:
    status: ArchiveStatus
    reasons: tuple[str, ...]
    execution_authorized: bool = False

def evaluate_archive(*, record: RecordMetadata) -> ArchiveDecision:
    if record.archived:
        return ArchiveDecision(ArchiveStatus.BLOCKED, ("ALREADY_ARCHIVED",))
    return ArchiveDecision(
        ArchiveStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION,
        ("SEPARATE_ARCHIVE_AUTHORIZATION_REQUIRED",),
    )

class DeletionStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION = (
        "READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION"
    )

@dataclass(frozen=True)
class DeletionDecision:
    status: DeletionStatus
    reasons: tuple[str, ...]
    execution_authorized: bool = False

def evaluate_deletion(
    *,
    record: RecordMetadata,
    policy: RetentionPolicy,
    observed_at_utc: int,
) -> DeletionDecision:
    if observed_at_utc < 0:
        raise ValueError("observation time must be non-negative")
    index = build_retention_index(record=record, policy=policy)
    reasons: list[str] = []
    if record.legal_hold:
        reasons.append("LEGAL_HOLD_ACTIVE")
    if observed_at_utc < index.expires_at_utc:
        reasons.append("RETENTION_NOT_EXPIRED")
    if policy.archive_before_deletion and not record.archived:
        reasons.append("ARCHIVE_EVIDENCE_MISSING")
    if (
        record.retention_class is RetentionClass.INCIDENT
        and record.incident_state is not IncidentState.CLOSED
    ):
        reasons.append("INCIDENT_NOT_CLOSED")
    if reasons:
        return DeletionDecision(DeletionStatus.BLOCKED, tuple(reasons))
    return DeletionDecision(
        DeletionStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION,
        ("SEPARATE_DELETION_AUTHORIZATION_REQUIRED",),
    )
