from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_audit_record(
    pull_request: dict[str, Any],
    decision: dict[str, Any],
    rollback: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, object]:
    return {
        "created_at": created_at or utc_now_iso(),
        "repository": pull_request.get("repository") or pull_request.get("repository_full_name"),
        "pull_request": pull_request.get("number"),
        "head_sha": pull_request.get("head_sha"),
        "base": pull_request.get("base"),
        "decision_status": decision.get("status"),
        "merge_method": decision.get("merge_method"),
        "reasons": decision.get("reasons", []),
        "rollback": rollback,
    }


def validate_audit_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    required = {"created_at", "pull_request", "head_sha", "decision_status", "rollback"}
    missing = sorted(required - set(record))
    if missing:
        reasons.append("missing audit fields: " + ", ".join(missing))
    if record.get("decision_status") not in {"PASS", "BLOCK"}:
        reasons.append("decision_status must be PASS or BLOCK")
    if not isinstance(record.get("rollback"), dict):
        reasons.append("rollback must be a mapping")
    return not reasons, reasons
