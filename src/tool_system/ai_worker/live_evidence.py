from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from tool_system.ai_worker.contract import validate_ai_worker_request
from tool_system.ai_worker.live_provider import (
    build_p14c_execution_packet,
    build_p14c_synthetic_request,
    validate_p14c_execution_packet,
)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the P14C packet without resolving credentials or calling a provider."
    )
    parser.add_argument(
        "--validate-packet-only",
        action="store_true",
        help="validate the static P14C packet and public synthetic fixture",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.validate_packet_only:
        raise SystemExit("--validate-packet-only is required")
    evidence = build_packet_validation_evidence()
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
