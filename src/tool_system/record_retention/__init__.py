"""Deterministic, non-executing record-retention decisions."""

from .policy import (
    ArchiveDecision, ArchiveStatus, DeletionDecision, DeletionStatus,
    RecordMetadata, RetentionClass, RetentionIndexEntry, RetentionPolicy,
    build_retention_index, evaluate_archive, evaluate_deletion,
)

__all__ = [
    "ArchiveDecision", "ArchiveStatus", "DeletionDecision", "DeletionStatus",
    "RecordMetadata", "RetentionClass", "RetentionIndexEntry",
    "RetentionPolicy", "build_retention_index", "evaluate_archive",
    "evaluate_deletion",
]
