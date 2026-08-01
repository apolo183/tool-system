from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tool_system.ai_worker.contract import canonical_sha256, validate_ai_worker_request
from tool_system.ai_worker.live_provider import (
    EnvironmentCredentialResolver,
    OpenAIResponsesProvider,
    OpenAIResponsesTransport,
    P14CLiveExecutionGuard,
    build_p14c_execution_packet,
    build_p14c_live_execution_binding,
    build_p14c_synthetic_request,
    issue_p14c_live_network_capability,
    validate_p14c_execution_packet,
)
from tool_system.process_authority.live_provider_approval import (
    P14C_APPROVAL_MAX_TTL_SECONDS,
    build_p14c_execution_source_seal,
    build_p14c_live_execution_approval_body,
    open_p14c_live_execution_ledger,
)

P14C_PREPARE_DEFAULT_TTL_SECONDS = 600
P14C_PREPARE_MIN_TTL_SECONDS = 60


class _CountingEnvironmentCredentialResolver:
    """Count resolution attempts without retaining or exposing the value."""

    def __init__(self) -> None:
        self._delegate = EnvironmentCredentialResolver()
        self.attempt_count = 0

    def resolve(self, reference: str) -> str:
        self.attempt_count += 1
        return self._delegate.resolve(reference)


def build_packet_validation_evidence() -> dict[str, object]:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    packet_reasons = validate_p14c_execution_packet(packet)
    request_validation = validate_ai_worker_request(request)
    reasons = list(packet_reasons) + list(request_validation.reasons)
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "validate-packet-only",
        "packet_id": packet.packet_id,
        "packet_sha256": packet.sha256(),
        "request_id": request.request_id,
        "request_sha256": request.sha256(),
        "fixture_id": packet.fixture_id,
        "provider_id": packet.provider_id,
        "model_id": packet.model_id,
        "credential_reference": packet.credential_reference,
        "credential_value_access_count": 0,
        "provider_call_count": 0,
        "transport_call_count": 0,
        "source_implementation_authorized": True,
        "live_provider_execution_authorized": False,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "reasons": reasons,
    }


def build_prepare_approval_evidence(
    *,
    repository_root: str | Path,
    ledger_path: str | Path,
    ttl_seconds: int = P14C_PREPARE_DEFAULT_TTL_SECONDS,
    _now: datetime | None = None,
    _nonce: str | None = None,
) -> dict[str, object]:
    """Prepare exact public approval JSON without reading GitHub or credentials."""

    if (
        not isinstance(ttl_seconds, int)
        or isinstance(ttl_seconds, bool)
        or not P14C_PREPARE_MIN_TTL_SECONDS
        <= ttl_seconds
        <= P14C_APPROVAL_MAX_TTL_SECONDS
    ):
        raise ValueError("ttl_seconds must be an integer from 60 through 900")
    now = _now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("current time must be timezone-aware")
    expires_at_utc = (now.astimezone(timezone.utc) + timedelta(seconds=ttl_seconds))
    expires_at_text = expires_at_utc.replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    nonce = _nonce or secrets.token_hex(32)
    ledger = open_p14c_live_execution_ledger(
        ledger_path,
        repository_root=repository_root,
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    source_seal = build_p14c_execution_source_seal(repository_root, ledger)
    binding = build_p14c_live_execution_binding(packet, request, source_seal)
    approval_body = build_p14c_live_execution_approval_body(
        binding,
        expires_at_utc=expires_at_text,
        nonce=nonce,
    )
    return {
        "status": "PASS",
        "mode": "prepare-approval",
        "approval_body": approval_body,
        "approval_body_sha256": hashlib.sha256(
            approval_body.encode("utf-8")
        ).hexdigest(),
        "approval_expires_at_utc": expires_at_text,
        "packet_id": packet.packet_id,
        "packet_sha256": packet.sha256(),
        "request_id": request.request_id,
        "request_sha256": request.sha256(),
        "source_seal": source_seal.canonical_record(),
        "source_seal_sha256": source_seal.sha256(),
        "ledger_initialized": True,
        "github_approval_read_count": 0,
        "github_approval_write_count": 0,
        "credential_value_access_count": 0,
        "provider_invocation_count": 0,
        "transport_attempt_count": 0,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "p14d_authorized": False,
    }


def execute_p14c_live_entry(
    *,
    repository_root: str | Path,
    ledger_path: str | Path,
    comment_id: int,
) -> dict[str, object]:
    """Consume one exact owner approval and return a redacted provider receipt."""

    if (
        not isinstance(comment_id, int)
        or isinstance(comment_id, bool)
        or comment_id <= 0
    ):
        raise ValueError("comment_id must be a positive integer")
    ledger = open_p14c_live_execution_ledger(
        ledger_path,
        repository_root=repository_root,
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = OpenAIResponsesTransport()
    capability = issue_p14c_live_network_capability(
        comment_id=comment_id,
        packet=packet,
        request=request,
        transport=transport,
        repository_root=repository_root,
        replay_ledger=ledger,
    )
    credential_resolver = _CountingEnvironmentCredentialResolver()
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=credential_resolver,
        execution_capability=capability,
    )
    guard = P14CLiveExecutionGuard(
        packet_sha256=packet.sha256(),
        capability=capability,
    )
    guard_reasons = guard.validate(request, provider)
    if guard_reasons:
        return {
            **_execution_receipt_base(packet, request, capability, comment_id),
            "status": "BLOCK",
            "provider_invocation_count": 0,
            "credential_resolution_attempt_count": 0,
            "usage": None,
            "output_sha256": None,
            "error": {
                "code": "execution_guard_blocked",
                "retryable": False,
                "reason_count": len(guard_reasons),
            },
        }

    response = provider.invoke(request)
    output_sha256 = (
        canonical_sha256(response.output) if response.output is not None else None
    )
    return {
        **_execution_receipt_base(packet, request, capability, comment_id),
        "status": "PASS" if response.error is None else "BLOCK",
        "provider_invocation_count": 1,
        "credential_resolution_attempt_count": (
            credential_resolver.attempt_count
        ),
        "transport_attempt_ceiling": packet.max_attempts,
        "usage": response.usage.to_record(),
        "output_sha256": output_sha256,
        "error": (
            response.error.to_record(audit=True)
            if response.error is not None
            else None
        ),
    }


def _execution_receipt_base(
    packet: object,
    request: object,
    capability: object,
    comment_id: int,
) -> dict[str, object]:
    source_seal = getattr(capability, "source_seal", None)
    source_record = (
        source_seal.canonical_record() if source_seal is not None else None
    )
    source_sha256 = source_seal.sha256() if source_seal is not None else None
    return {
        "mode": "execute",
        "packet_id": getattr(packet, "packet_id"),
        "packet_sha256": packet.sha256(),
        "request_id": getattr(request, "request_id"),
        "request_sha256": request.sha256(),
        "approval_comment_id": comment_id,
        "approval_issue_number": getattr(
            capability, "approval_issue_number", None
        ),
        "approval_record_sha256": getattr(
            capability, "approval_record_sha256", None
        ),
        "authorization_id": getattr(capability, "authorization_id", None),
        "approval_durably_consumed": True,
        "source_seal": source_record,
        "source_seal_sha256": source_sha256,
        "credential_reference": getattr(packet, "credential_reference"),
        "credential_value_included": False,
        "raw_provider_output_included": False,
        "github_approval_write_count": 0,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "p14d_authorized": False,
    }


def _blocked_entry_evidence(mode: str, error: Exception) -> dict[str, object]:
    return {
        "status": "BLOCK",
        "mode": mode,
        "error": {
            "code": "entry_preflight_failed",
            "type": type(error).__name__,
            "retryable": False,
        },
        "credential_value_included": False,
        "raw_provider_output_included": False,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "p14d_authorized": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate, prepare approval for, or execute the bounded P14C provider path."
        )
    )
    parser.add_argument(
        "--validate-packet-only",
        action="store_true",
        help="validate the static P14C packet and public synthetic fixture",
    )
    commands = parser.add_subparsers(dest="command")
    prepare = commands.add_parser(
        "prepare-approval",
        help="prepare exact owner-comment JSON without reading GitHub or credentials",
    )
    prepare.add_argument("--repository-root", type=Path, required=True)
    prepare.add_argument("--ledger", type=Path, required=True)
    prepare.add_argument(
        "--ttl-seconds",
        type=int,
        default=P14C_PREPARE_DEFAULT_TTL_SECONDS,
    )
    execute = commands.add_parser(
        "execute",
        help="consume one exact owner approval and run the bounded provider path",
    )
    execute.add_argument("--repository-root", type=Path, required=True)
    execute.add_argument("--ledger", type=Path, required=True)
    execute.add_argument("--comment-id", type=int, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.validate_packet_only and args.command is not None:
        parser.error("--validate-packet-only cannot be combined with a command")
    try:
        if args.validate_packet_only:
            evidence = build_packet_validation_evidence()
        elif args.command == "prepare-approval":
            evidence = build_prepare_approval_evidence(
                repository_root=args.repository_root,
                ledger_path=args.ledger,
                ttl_seconds=args.ttl_seconds,
            )
        elif args.command == "execute":
            evidence = execute_p14c_live_entry(
                repository_root=args.repository_root,
                ledger_path=args.ledger,
                comment_id=args.comment_id,
            )
        else:
            parser.error(
                "--validate-packet-only, prepare-approval, or execute is required"
            )
    except Exception as exc:  # noqa: BLE001 - operator failures are redacted
        evidence = _blocked_entry_evidence(args.command or "packet-validation", exc)
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
