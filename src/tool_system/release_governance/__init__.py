"""Deterministic, non-authorizing release governance."""

from .policy import (
    CompatibilityDecision,
    DeprecationDecision,
    DeprecationRecord,
    ReleaseCandidateDecision,
    SemanticVersion,
    evaluate_compatibility,
    evaluate_deprecation,
    evaluate_release_candidate,
)

__all__ = [
    "CompatibilityDecision", "DeprecationDecision", "DeprecationRecord",
    "ReleaseCandidateDecision", "SemanticVersion", "evaluate_compatibility",
    "evaluate_deprecation", "evaluate_release_candidate",
]
