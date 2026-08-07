from __future__ import annotations

import pytest

from tool_system.recovery_planning import (
    BackupEntry,
    BackupManifest,
    BackupVerificationStatus,
    DisasterRecoveryStatus,
    DrillObservation,
    RecoveryObjectives,
    RestoreStatus,
    evaluate_non_live_drill,
    plan_restore,
    verify_backup,
)
from tool_system.state_migration import (
    MigrationDirection,
    MigrationPlan,
    MigrationStatus,
)

SHA_A = "a" * 64
SHA_B = "b" * 64

def _manifest() -> BackupManifest:
    return BackupManifest(
        format_version=1,
        state_version="3.0.0",
        snapshot_at_utc=1_000,
        source_seal_sha256=SHA_A,
        entries=(
            BackupEntry("state.sqlite3", SHA_A, 12),
            BackupEntry("audit.jsonl", SHA_B, 9),
        ),
    )

def _migration(status=MigrationStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION):
    return MigrationPlan(
        status=status,
        direction=MigrationDirection.NOOP,
        step_ids=(),
        reasons=(),
    )

def test_backup_verification_is_exact_and_deterministic() -> None:
    manifest = _manifest()
    result = verify_backup(
        manifest=manifest,
        observed_entries=tuple(reversed(manifest.entries)),
    )
    assert result.status is BackupVerificationStatus.PASS
    assert result.reasons == ()

    blocked = verify_backup(
        manifest=manifest,
        observed_entries=(
            BackupEntry("state.sqlite3", SHA_B, 12),
            BackupEntry("unexpected", SHA_A, 1),
        ),
    )
    assert blocked.status is BackupVerificationStatus.BLOCKED
    assert blocked.reasons == (
        "MISSING:audit.jsonl",
        "SHA256_MISMATCH:state.sqlite3",
        "UNEXPECTED:unexpected",
    )

def test_restore_plan_requires_verified_backup_and_separate_authority() -> None:
    manifest = _manifest()
    verification = verify_backup(
        manifest=manifest, observed_entries=manifest.entries
    )
    ready = plan_restore(
        manifest=manifest,
        verification=verification,
        migration_plan=_migration(),
    )
    assert ready.status is RestoreStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    assert ready.restore_order == ("state.sqlite3", "audit.jsonl")
    assert ready.execution_authorized is False

    blocked = plan_restore(
        manifest=manifest,
        verification=verification,
        migration_plan=_migration(MigrationStatus.BLOCKED),
    )
    assert blocked.status is RestoreStatus.BLOCKED
    assert blocked.restore_order == ()
    assert blocked.execution_authorized is False

def test_non_live_drill_evaluates_rpo_and_rto_without_authorizing_execution() -> None:
    objectives = RecoveryObjectives(rpo_seconds=60, rto_seconds=120)
    passing = evaluate_non_live_drill(
        objectives=objectives,
        observation=DrillObservation(1_000, 950, 1_100),
    )
    assert passing.status is DisasterRecoveryStatus.PASS
    assert passing.measured_rpo_seconds == 50
    assert passing.measured_rto_seconds == 100
    assert passing.execution_authorized is False

    blocked = evaluate_non_live_drill(
        objectives=objectives,
        observation=DrillObservation(1_000, 900, 1_130),
    )
    assert blocked.status is DisasterRecoveryStatus.BLOCKED
    assert blocked.reasons == ("RPO_EXCEEDED", "RTO_EXCEEDED")

def test_invalid_manifests_and_observations_fail_closed() -> None:
    with pytest.raises(ValueError):
        BackupEntry("", SHA_A, 0)
    with pytest.raises(ValueError):
        BackupEntry("state", "not-a-hash", 0)
    with pytest.raises(ValueError):
        BackupManifest(1, "3", 0, SHA_A, ())
    with pytest.raises(ValueError):
        DrillObservation(10, 11, 12)
