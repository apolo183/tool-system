"""Pure backup verification, restore planning, and non-live DR evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.state_migration import MigrationPlan, MigrationStatus

def _sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{label} must be a lowercase SHA256")

@dataclass(frozen=True)
class BackupEntry:
    logical_name: str
    sha256: str
    byte_length: int

    def __post_init__(self) -> None:
        if not self.logical_name.strip():
            raise ValueError("backup logical name must be explicit")
        _sha256(self.sha256, "backup entry sha256")
        if self.byte_length < 0:
            raise ValueError("backup entry byte length must be non-negative")

@dataclass(frozen=True)
class BackupManifest:
    format_version: int
    state_version: str
    snapshot_at_utc: int
    source_seal_sha256: str
    entries: tuple[BackupEntry, ...]

    def __post_init__(self) -> None:
        if self.format_version < 1:
            raise ValueError("backup format version must be positive")
        if not self.state_version.strip():
            raise ValueError("backup state version must be explicit")
        if self.snapshot_at_utc < 0:
            raise ValueError("backup snapshot time must be non-negative")
        _sha256(self.source_seal_sha256, "backup source seal")
        if not self.entries:
            raise ValueError("backup manifest must contain entries")
        names = [entry.logical_name for entry in self.entries]
        if len(names) != len(set(names)):
            raise ValueError("backup logical names must be unique")

class BackupVerificationStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class BackupVerification:
    status: BackupVerificationStatus
    reasons: tuple[str, ...]

def verify_backup(
    *, manifest: BackupManifest, observed_entries: tuple[BackupEntry, ...]
) -> BackupVerification:
    observed: dict[str, BackupEntry] = {}
    for entry in observed_entries:
        if entry.logical_name in observed:
            raise ValueError("observed backup logical names must be unique")
        observed[entry.logical_name] = entry
    expected = {entry.logical_name: entry for entry in manifest.entries}
    reasons: list[str] = []
    for name in sorted(expected):
        actual = observed.get(name)
        if actual is None:
            reasons.append(f"MISSING:{name}")
        elif actual.sha256 != expected[name].sha256:
            reasons.append(f"SHA256_MISMATCH:{name}")
        elif actual.byte_length != expected[name].byte_length:
            reasons.append(f"BYTE_LENGTH_MISMATCH:{name}")
    for name in sorted(set(observed) - set(expected)):
        reasons.append(f"UNEXPECTED:{name}")
    status = (
        BackupVerificationStatus.PASS
        if not reasons
        else BackupVerificationStatus.BLOCKED
    )
    return BackupVerification(status=status, reasons=tuple(reasons))

class RestoreStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION = (
        "READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION"
    )

@dataclass(frozen=True)
class RestorePlan:
    status: RestoreStatus
    restore_order: tuple[str, ...]
    reasons: tuple[str, ...]
    execution_authorized: bool = False

def plan_restore(
    *,
    manifest: BackupManifest,
    verification: BackupVerification,
    migration_plan: MigrationPlan,
) -> RestorePlan:
    reasons: list[str] = []
    if verification.status is not BackupVerificationStatus.PASS:
        reasons.append("BACKUP_VERIFICATION_BLOCKED")
    if (
        migration_plan.status
        is not MigrationStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION
    ):
        reasons.append("STATE_MIGRATION_BLOCKED")
    if migration_plan.execution_authorized:
        reasons.append("MIGRATION_PLAN_MUST_BE_NON_AUTHORIZING")
    if reasons:
        return RestorePlan(
            status=RestoreStatus.BLOCKED,
            restore_order=(),
            reasons=tuple(reasons),
        )
    return RestorePlan(
        status=RestoreStatus.READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION,
        restore_order=tuple(entry.logical_name for entry in manifest.entries),
        reasons=("SEPARATE_RESTORE_AUTHORIZATION_REQUIRED",),
    )

@dataclass(frozen=True)
class RecoveryObjectives:
    rpo_seconds: int
    rto_seconds: int

    def __post_init__(self) -> None:
        if self.rpo_seconds < 0 or self.rto_seconds < 0:
            raise ValueError("recovery objectives must be non-negative")

@dataclass(frozen=True)
class DrillObservation:
    disaster_at_utc: int
    recovered_through_utc: int
    recovery_completed_at_utc: int

    def __post_init__(self) -> None:
        if self.recovered_through_utc > self.disaster_at_utc:
            raise ValueError("recovered-through time cannot follow disaster time")
        if self.recovery_completed_at_utc < self.disaster_at_utc:
            raise ValueError("recovery completion cannot precede disaster time")

class DisasterRecoveryStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class DisasterRecoveryDecision:
    status: DisasterRecoveryStatus
    measured_rpo_seconds: int
    measured_rto_seconds: int
    reasons: tuple[str, ...]
    execution_authorized: bool = False

def evaluate_non_live_drill(
    *, objectives: RecoveryObjectives, observation: DrillObservation
) -> DisasterRecoveryDecision:
    measured_rpo = observation.disaster_at_utc - observation.recovered_through_utc
    measured_rto = observation.recovery_completed_at_utc - observation.disaster_at_utc
    reasons: list[str] = []
    if measured_rpo > objectives.rpo_seconds:
        reasons.append("RPO_EXCEEDED")
    if measured_rto > objectives.rto_seconds:
        reasons.append("RTO_EXCEEDED")
    status = (
        DisasterRecoveryStatus.PASS
        if not reasons
        else DisasterRecoveryStatus.BLOCKED
    )
    return DisasterRecoveryDecision(
        status=status,
        measured_rpo_seconds=measured_rpo,
        measured_rto_seconds=measured_rto,
        reasons=tuple(reasons),
    )
