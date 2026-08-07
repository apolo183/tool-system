"""Pure release, compatibility, and deprecation decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering

_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

@total_ordering
@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("version components must be non-negative")

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        match = _VERSION.fullmatch(value)
        if match is None:
            raise ValueError("version must be canonical MAJOR.MINOR.PATCH")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

class CompatibilityDecision(str, Enum):
    SUPPORTED = "SUPPORTED"
    TOO_OLD = "TOO_OLD"
    FUTURE_MAJOR = "FUTURE_MAJOR"

@dataclass(frozen=True)
class DeprecationRecord:
    announced_at_utc: int
    removal_not_before_utc: int
    replacement: str

    def __post_init__(self) -> None:
        if self.announced_at_utc < 0 or self.removal_not_before_utc <= self.announced_at_utc:
            raise ValueError("deprecation timestamps must be non-negative and monotonic")
        if not self.replacement.strip():
            raise ValueError("replacement must be explicit")

class DeprecationDecision(str, Enum):
    ANNOUNCED = "ANNOUNCED"
    REMOVAL_ELIGIBLE = "REMOVAL_ELIGIBLE"

class ReleaseCandidateDecision(str, Enum):
    BLOCKED = "BLOCKED"
    ELIGIBLE_FOR_SEPARATE_AUTHORIZATION = "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION"

def evaluate_compatibility(*, candidate: SemanticVersion, minimum_supported: SemanticVersion, current: SemanticVersion) -> CompatibilityDecision:
    if minimum_supported > current:
        raise ValueError("minimum supported version cannot exceed current version")
    if candidate < minimum_supported:
        return CompatibilityDecision.TOO_OLD
    if candidate.major > current.major:
        return CompatibilityDecision.FUTURE_MAJOR
    return CompatibilityDecision.SUPPORTED

def evaluate_deprecation(record: DeprecationRecord, *, observed_at_utc: int) -> DeprecationDecision:
    if observed_at_utc < record.announced_at_utc:
        raise ValueError("observation cannot precede announcement")
    if observed_at_utc >= record.removal_not_before_utc:
        return DeprecationDecision.REMOVAL_ELIGIBLE
    return DeprecationDecision.ANNOUNCED

def evaluate_release_candidate(*, candidate: SemanticVersion, current: SemanticVersion, compatibility_checks: tuple[CompatibilityDecision, ...], evidence_sealed: bool, migration_evidence_complete: bool) -> tuple[ReleaseCandidateDecision, tuple[str, ...]]:
    reasons: list[str] = []
    if candidate <= current:
        reasons.append("VERSION_NOT_FORWARD")
    if not compatibility_checks or any(check is not CompatibilityDecision.SUPPORTED for check in compatibility_checks):
        reasons.append("COMPATIBILITY_NOT_CLOSED")
    if not evidence_sealed:
        reasons.append("EVIDENCE_NOT_SEALED")
    if candidate.major > current.major and not migration_evidence_complete:
        reasons.append("BREAKING_MIGRATION_EVIDENCE_MISSING")
    if reasons:
        return ReleaseCandidateDecision.BLOCKED, tuple(reasons)
    return ReleaseCandidateDecision.ELIGIBLE_FOR_SEPARATE_AUTHORIZATION, ()
