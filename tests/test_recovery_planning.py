from __future__ import annotations

from dataclasses import replace

import pytest

from tool_system.recovery_planning import (
    BackupEntry,
    BackupManifest,
    BackupVerification,
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


@pytest.mark.parametrize(
    "changes",
    [
        {"format_version": 2},
        {"state_version": "3.0.1"},
        {"snapshot_at_utc": 1_001},
        {"source_seal_sha256": SHA_B},
        {"entries": tuple(reversed(_manifest().entries))},
        {"entries": (BackupEntry("other.sqlite3", SHA_A, 12), _manifest().entries[1])},
        {"entries": (BackupEntry("state.sqlite3", SHA_B, 12), _manifest().entries[1])},
        {"entries": (BackupEntry("state.sqlite3", SHA_A, 13), _manifest().entries[1])},
        {"entries": (_manifest().entries[0],)},
        {"entries": _manifest().entries + (BackupEntry("extra.json", SHA_A, 1),)},
    ],
    ids=["format", "state", "time", "seal", "order", "name", "hash", "length", "missing", "extra"],
)
def test_restore_rejects_verification_from_another_manifest(changes) -> None:
    original = _manifest()
    verification = verify_backup(manifest=original, observed_entries=original.entries)
    supplied = replace(original, **changes)

    result = plan_restore(
        manifest=supplied, verification=verification, migration_plan=_migration()
    )

    assert result.status is RestoreStatus.BLOCKED
    assert result.reasons == ("BACKUP_MANIFEST_IDENTITY_MISMATCH",)
    assert result.restore_order == ()
    assert result.execution_authorized is False


def test_restore_rejects_unbound_pass_without_breaking_legacy_construction() -> None:
    result = plan_restore(
        manifest=_manifest(),
        verification=BackupVerification(BackupVerificationStatus.PASS, ()),
        migration_plan=_migration(),
    )

    assert result.status is RestoreStatus.BLOCKED
    assert result.reasons == ("BACKUP_VERIFICATION_UNBOUND",)
    assert result.restore_order == ()
    assert result.execution_authorized is False


def test_verification_binding_is_value_based_and_observation_order_independent() -> None:
    manifest = _manifest()
    verification = verify_backup(manifest=manifest, observed_entries=manifest.entries)
    reconstructed = BackupManifest(
        manifest.format_version,
        manifest.state_version,
        manifest.snapshot_at_utc,
        manifest.source_seal_sha256,
        tuple(replace(entry) for entry in manifest.entries),
    )
    second = verify_backup(
        manifest=reconstructed, observed_entries=tuple(reversed(reconstructed.entries))
    )

    assert second == verification
    assert len(verification.manifest_sha256) == 64
    assert set(verification.manifest_sha256) <= set("0123456789abcdef")
    result = plan_restore(
        manifest=reconstructed, verification=verification, migration_plan=_migration()
    )
    assert result.status is RestoreStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    assert result.restore_order == ("state.sqlite3", "audit.jsonl")
    assert result.execution_authorized is False


def test_restore_rejects_pass_with_failure_reasons_even_when_manifest_matches() -> None:
    manifest = _manifest()
    verified = verify_backup(manifest=manifest, observed_entries=manifest.entries)
    result = plan_restore(
        manifest=manifest,
        verification=replace(verified, reasons=("MISSING:state.sqlite3",)),
        migration_plan=_migration(),
    )

    assert result.status is RestoreStatus.BLOCKED
    assert result.reasons == ("BACKUP_VERIFICATION_BLOCKED",)
    assert result.restore_order == ()
    assert result.execution_authorized is False


def test_bound_failed_verification_still_blocks_restore() -> None:
    manifest = _manifest()
    verified = verify_backup(manifest=manifest, observed_entries=())
    result = plan_restore(
        manifest=manifest, verification=verified, migration_plan=_migration()
    )

    assert verified.manifest_sha256 is not None
    assert verified.status is BackupVerificationStatus.BLOCKED
    assert result.status is RestoreStatus.BLOCKED
    assert result.reasons == ("BACKUP_VERIFICATION_BLOCKED",)
    assert result.restore_order == ()
    assert result.execution_authorized is False


@pytest.mark.parametrize("digest", ["", "not-a-sha256", "f" * 64])
def test_restore_rejects_invalid_or_unrelated_binding(digest: str) -> None:
    manifest = _manifest()
    verified = verify_backup(manifest=manifest, observed_entries=manifest.entries)
    result = plan_restore(
        manifest=manifest,
        verification=replace(verified, manifest_sha256=digest),
        migration_plan=_migration(),
    )

    assert result.status is RestoreStatus.BLOCKED
    assert result.reasons == ("BACKUP_MANIFEST_IDENTITY_MISMATCH",)
    assert result.restore_order == ()
    assert result.execution_authorized is False
