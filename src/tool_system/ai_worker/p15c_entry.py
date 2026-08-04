from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.ai_worker.p15c_benchmark import (
    P15CBenchmarkError,
    P15CBenchmarkExecutor,
    P15CDirectTLSTransport,
    assert_p15c_provider_packets_execution_eligible,
    build_p15c_private_case,
    load_p15c_deterministic_case,
    load_p15c_provider_packets,
)
from tool_system.ai_worker.p15c_controls import (
    OwnerOnlyCredentialResolver,
    P15C_DEFAULT_CREDENTIALS_PATH,
    P15C_DEFAULT_LEDGER_PATH,
    P15C_DEFAULT_SETTINGS_PATH,
    P15C_DEFAULT_TARGET_PACKET_PATH,
    P15CControlError,
    P15CUsageLedger,
    load_target_packet,
    load_target_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the source-sealed P15C read-only benchmark control plane."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--packet-only",
        action="store_true",
        help="Validate and print public packet metadata with zero private access.",
    )
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Validate private controls and credentials without provider calls.",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Run the exact two-provider by two-case read-only matrix once.",
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument(
        "--packet-config",
        default="config/p15c_execution_packet_freeze_v1.yaml",
    )
    parser.add_argument(
        "--settings",
        "--policy",
        dest="settings",
        default=str(P15C_DEFAULT_SETTINGS_PATH),
        help="Owner-only operator settings TOML; --policy remains a compatible alias.",
    )
    parser.add_argument(
        "--credentials",
        default=str(P15C_DEFAULT_CREDENTIALS_PATH),
        help="Owner-only provider credential TOML.",
    )
    parser.add_argument(
        "--target-packet",
        default=str(P15C_DEFAULT_TARGET_PACKET_PATH),
        help="Owner-only content-addressed target packet JSON.",
    )
    parser.add_argument(
        "--ledger",
        default=str(P15C_DEFAULT_LEDGER_PATH),
        help="Owner-only cumulative usage ledger.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    repository_root = Path(arguments.repository_root).resolve()
    packet_config = Path(arguments.packet_config)
    if not packet_config.is_absolute():
        packet_config = repository_root / packet_config
    try:
        packets = load_p15c_provider_packets(packet_config)
        if arguments.packet_only:
            _print_json(
                {
                    "status": "PASS",
                    "mode": "packet-only",
                    "packets": [packet.public_record() for packet in packets],
                    "provider_invocations": 0,
                    "network_operations": 0,
                    "credential_resolver_invocations": 0,
                    "credential_value_accesses": 0,
                    "target_snapshot_reads": 0,
                    "benchmark_executions": 0,
                    "target_mutations": 0,
                    "production_operations": 0,
                    "cleanup_operations": 0,
                    "rollback_operations": 0,
                }
            )
            return 0
        assert_p15c_provider_packets_execution_eligible(packets)
        private_paths = {
            "settings": arguments.settings,
            "credentials": arguments.credentials,
            "target_packet": arguments.target_packet,
            "ledger": arguments.ledger,
        }
        target_packet = load_target_packet(private_paths["target_packet"])
        target_snapshot = load_target_snapshot(target_packet)
        deterministic_case = load_p15c_deterministic_case(
            repository_root,
            packet_config,
        )
        private_case = build_p15c_private_case(target_packet, target_snapshot)
        cases = (deterministic_case, private_case)
        resolver = OwnerOnlyCredentialResolver(private_paths["credentials"])
        ledger = P15CUsageLedger(private_paths["ledger"])
        executor = P15CBenchmarkExecutor(
            repository_root=repository_root,
            packet_config_path=packet_config,
            policy_path=private_paths["settings"],
            credential_resolver=resolver,
            ledger=ledger,
            transport=P15CDirectTLSTransport(),
            target_packet=target_packet,
        )
        preflight = executor.preflight(packets, cases)
        if arguments.preflight:
            _print_json({"mode": "preflight", **preflight})
            return 0
        outcomes = []
        matrix_blocked = False
        for packet in packets:
            for case in cases:
                outcome = executor.execute(packet, case)
                outcomes.append(outcome)
                if outcome.status != "PASS":
                    matrix_blocked = True
                    break
            if matrix_blocked:
                break
        records = [outcome.public_record() for outcome in outcomes]
        total_charge = sum(outcome.charged_micro_usd for outcome in outcomes)
        passed = all(outcome.status == "PASS" for outcome in outcomes)
        _print_json(
            {
                "status": "PASS" if passed else "BENCHMARK_BLOCKED",
                "mode": "execute",
                "authorization_id": preflight["authorization_id"],
                "policy_sha256": preflight["policy_sha256"],
                "source_seal": preflight["source_seal"],
                "request_set_sha256": preflight["request_set_sha256"],
                "target_packet_sha256": preflight["target_packet_sha256"],
                "attempts": records,
                "provider_invocations": len(outcomes),
                "benchmark_executions": len(outcomes),
                "charged_micro_usd": total_charge,
                "configured_budget_micro_usd": preflight[
                    "total_budget_micro_usd"
                ],
                "credential_values_recorded": 0,
                "raw_provider_outputs_recorded": 0,
                "private_target_identity_recorded": False,
                "private_target_paths_recorded": False,
                "target_mutations": 0,
                "production_operations": 0,
                "cleanup_operations": 0,
                "rollback_operations": 0,
                "ledger": ledger.summary(),
            }
        )
        return 0 if passed else 2
    except KeyboardInterrupt:
        _print_json(
            {
                "status": "BENCHMARK_BLOCKED",
                "failure_code": "INTERRUPTED",
                "credential_values_recorded": 0,
                "raw_provider_outputs_recorded": 0,
                "private_target_identity_recorded": False,
                "private_target_paths_recorded": False,
                "target_mutations": 0,
            }
        )
        return 130
    except (P15CControlError, P15CBenchmarkError) as exc:
        record = {
            "status": "BENCHMARK_BLOCKED",
            "failure_code": exc.code,
            "credential_values_recorded": 0,
            "raw_provider_outputs_recorded": 0,
            "private_target_identity_recorded": False,
            "private_target_paths_recorded": False,
            "target_mutations": 0,
        }
        if exc.code == "PROVIDER_EXACT_VERSION_UNPINNABLE":
            record.update(
                {
                    "credential_resolver_invocations": 0,
                    "credential_value_accesses": 0,
                    "target_packet_reads": 0,
                    "target_snapshot_reads": 0,
                    "provider_invocations": 0,
                    "network_operations": 0,
                    "benchmark_executions": 0,
                }
            )
        _print_json(record)
        return 2


def _print_json(value: object) -> None:
    print(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
