from __future__ import annotations

import pytest

from tool_system.operational_observability import IncidentState
from tool_system.record_retention import (
    ArchiveStatus, DeletionStatus, RecordMetadata, RetentionClass,
    RetentionPolicy, build_retention_index, evaluate_archive,
    evaluate_deletion,
)

SHA = "a" * 64

def _record(**overrides):
    values = dict(
        record_id="audit-1", retention_class=RetentionClass.AUDIT,
        created_at_utc=100, content_sha256=SHA,
    )
    values.update(overrides)
    return RecordMetadata(**values)

def test_retention_index_is_deterministic() -> None:
    policy = RetentionPolicy(RetentionClass.AUDIT, 900, True)
    index = build_retention_index(record=_record(), policy=policy)
    assert index.expires_at_utc == 1000
    assert index.content_sha256 == SHA

def test_archive_is_non_executing_and_requires_separate_authority() -> None:
    decision = evaluate_archive(record=_record())
    assert decision.status is ArchiveStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    assert decision.execution_authorized is False
    assert evaluate_archive(record=_record(archived=True)).status is ArchiveStatus.BLOCKED

def test_deletion_fails_closed_for_hold_expiry_and_archive() -> None:
    policy = RetentionPolicy(RetentionClass.AUDIT, 900, True)
    decision = evaluate_deletion(
        record=_record(legal_hold=True), policy=policy, observed_at_utc=500
    )
    assert decision.status is DeletionStatus.BLOCKED
    assert decision.reasons == (
        "LEGAL_HOLD_ACTIVE", "RETENTION_NOT_EXPIRED",
        "ARCHIVE_EVIDENCE_MISSING",
    )
    ready = evaluate_deletion(
        record=_record(archived=True), policy=policy, observed_at_utc=1000
    )
    assert ready.status is DeletionStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    assert ready.execution_authorized is False

def test_open_incident_cannot_be_deleted() -> None:
    record = RecordMetadata(
        "incident-1", RetentionClass.INCIDENT, 0, SHA,
        archived=True, incident_state=IncidentState.TRIAGE_REQUIRED,
    )
    policy = RetentionPolicy(RetentionClass.INCIDENT, 1, True)
    decision = evaluate_deletion(
        record=record, policy=policy, observed_at_utc=2
    )
    assert decision.reasons == ("INCIDENT_NOT_CLOSED",)

def test_invalid_metadata_fails_closed() -> None:
    with pytest.raises(ValueError):
        _record(content_sha256="bad")
    with pytest.raises(ValueError):
        RecordMetadata("incident", RetentionClass.INCIDENT, 0, SHA)
