from __future__ import annotations

import argparse
import json

from tool_system.ai_worker import (
    BoundedLiveAIWorkerRuntime,
    P14C_OPENAI_GPT56_LUNA_PACKET,
    build_p14c_synthetic_request,
    credential_reference_available,
    p14c_packet_sha256,
    validate_p14c_packet,
)


def _preflight_record() -> dict[str, object]:
    packet = P14C_OPENAI_GPT56_LUNA_PACKET
    reasons = validate_p14c_packet(packet)
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "packet_id": packet.packet_id,
        "packet_sha256": p14c_packet_sha256(),
        "provider_id": packet.provider_id,
        "model_id": packet.model_id,
        "api_destination": f"{packet.api_host}:{packet.api_port}{packet.api_path}",
        "credential_reference": packet.credential_reference,
        "credential_available": credential_reference_available(
            packet.credential_reference
        ),
        "network_attempted": False,
        "remote_target_mutation": False,
        "production_deployment": False,
        "reasons": list(reasons),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the exact P14C synthetic OpenAI live-evidence packet."
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate the exact packet and report credential-reference availability without network access.",
    )
    args = parser.parse_args()

    preflight = _preflight_record()
    if args.preflight_only:
        print(json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if preflight["status"] == "PASS" else 2
    if preflight["status"] != "PASS" or not preflight["credential_available"]:
        blocked = {
            **preflight,
            "status": "BLOCK",
            "error_code": "CREDENTIAL_UNAVAILABLE",
        }
        print(json.dumps(blocked, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    runtime = BoundedLiveAIWorkerRuntime()
    result = runtime.run(build_p14c_synthetic_request())
    record = {
        "status": result.status,
        "result": result.to_audit_record(),
        "live_execution": runtime.live_audit_record(),
        "remote_target_mutation": False,
        "production_deployment": False,
    }
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.status == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
