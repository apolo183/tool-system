from __future__ import annotations

import pytest

from tool_system.release_governance import (
    CompatibilityDecision, DeprecationDecision, DeprecationRecord,
    ReleaseCandidateDecision, SemanticVersion, evaluate_compatibility,
    evaluate_deprecation, evaluate_release_candidate,
)

def test_semantic_versions_are_canonical_and_ordered() -> None:
    assert SemanticVersion.parse("1.2.3") < SemanticVersion.parse("2.0.0")
    assert str(SemanticVersion.parse("0.1.0")) == "0.1.0"
    for value in ("1", "1.2", "01.2.3", "1.2.3-beta"):
        with pytest.raises(ValueError):
            SemanticVersion.parse(value)

def test_compatibility_window_is_inclusive_and_fail_closed() -> None:
    minimum = SemanticVersion.parse("1.2.0")
    current = SemanticVersion.parse("1.9.0")
    assert evaluate_compatibility(candidate=minimum, minimum_supported=minimum, current=current) is CompatibilityDecision.SUPPORTED
    assert evaluate_compatibility(candidate=SemanticVersion.parse("1.1.9"), minimum_supported=minimum, current=current) is CompatibilityDecision.TOO_OLD
    assert evaluate_compatibility(candidate=SemanticVersion.parse("2.0.0"), minimum_supported=minimum, current=current) is CompatibilityDecision.FUTURE_MAJOR

def test_deprecation_uses_only_caller_supplied_monotonic_time() -> None:
    record = DeprecationRecord(announced_at_utc=100, removal_not_before_utc=200, replacement="new-api")
    assert evaluate_deprecation(record, observed_at_utc=199) is DeprecationDecision.ANNOUNCED
    assert evaluate_deprecation(record, observed_at_utc=200) is DeprecationDecision.REMOVAL_ELIGIBLE
    with pytest.raises(ValueError):
        evaluate_deprecation(record, observed_at_utc=99)

def test_release_decision_is_deterministic_non_authorizing_and_ordered() -> None:
    current = SemanticVersion.parse("1.2.3")
    candidate = SemanticVersion.parse("2.0.0")
    decision, reasons = evaluate_release_candidate(candidate=candidate, current=current, compatibility_checks=(CompatibilityDecision.SUPPORTED,), evidence_sealed=False, migration_evidence_complete=False)
    assert decision is ReleaseCandidateDecision.BLOCKED
    assert reasons == ("EVIDENCE_NOT_SEALED", "BREAKING_MIGRATION_EVIDENCE_MISSING")
    decision, reasons = evaluate_release_candidate(candidate=candidate, current=current, compatibility_checks=(CompatibilityDecision.SUPPORTED,), evidence_sealed=True, migration_evidence_complete=True)
    assert decision is ReleaseCandidateDecision.ELIGIBLE_FOR_SEPARATE_AUTHORIZATION
    assert reasons == ()
