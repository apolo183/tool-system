from __future__ import annotations

import json
from pathlib import Path

from tool_system.ai_worker.live_evidence import build_packet_validation_evidence
from tool_system.ai_worker.live_provider import (
    build_p14c_execution_packet,
    build_p14c_synthetic_request,
    validate_p14c_execution_packet,
)
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
REPORT = ROOT / "docs" / "reports" / "p14c_bounded_real_model_provider_execution.md"
LIVE_PROVIDER = ROOT / "src" / "tool_system" / "ai_worker" / "live_provider.py"
LIVE_EVIDENCE = ROOT / "src" / "tool_system" / "ai_worker" / "live_evidence.py"


def test_p14c_source_authorization_does_not_claim_live_execution_or_acceptance() -> (
    None
):
    blueprint = load_yaml_file(BLUEPRINT)
    execution = blueprint["active_phase_execution"]
    p14c = blueprint["p14c_source_implementation"]
    report = REPORT.read_text(encoding="utf-8")

    assert execution["current_stage"] == ("P14MR_MILESTONE_MODULE_INVARIANT")
    assert execution["next_stage"] == "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    assert execution["next_stage_authorized"] is False
    assert p14c["implementation_authorization_packet"] == "P14C-IMPL-v2"
    assert p14c["source_implementation_authorized"] is True
    assert p14c["source_implementation_status"] == (
        "corrected_source_merged_live_execution_not_run_not_accepted"
    )
    assert p14c["p14c_stage_accepted"] is False
    assert p14c["live_model_provider_execution_authorized"] is False
    assert p14c["credential_value_access_authorized"] is False
    assert p14c["downstream_repository_access_authorized"] is False
    assert p14c["remote_target_mutation_authorized"] is False
    assert p14c["production_deployment_authorized"] is False
    assert (
        "CORRECTED_SOURCE_MERGED_LIVE_EXECUTION_NOT_RUN_NOT_ACCEPTED" in report
    )
    assert "P14C-CORR-v1" in report
    assert "P14C-CORR-READY-v1" in report
    assert "P14C-CORR-MERGE-v1" in report
    assert "#143" in report
    assert "352b2638bb9a1cf7504a224c0571062072b32db1" in report
    assert "provider_call_count=0" in report
    assert "credential_value_access_count=0" in report
    assert "transport_call_count=0" in report


def test_packet_binds_exact_provider_network_secret_reference_and_budgets() -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)

    assert validate_p14c_execution_packet(packet) == ()
    assert packet.packet_id == "P14C-IMPL-v2"
    assert packet.tool_system_base == ("637fe60782ed9e15d58795a0113b84965d6664d2")
    assert "central_" + "governance_base" not in packet.canonical_record()
    assert (packet.provider_id, packet.model_id) == ("openai", "gpt-5.6-luna")
    assert (packet.method, packet.host, packet.path) == (
        "POST",
        "api.openai.com",
        "/v1/responses",
    )
    assert packet.credential_reference == "env:OPENAI_API_KEY"
    assert packet.reasoning_effort == "none"
    assert packet.store is packet.tools_allowed is False
    assert (
        packet.per_attempt_input_tokens,
        packet.per_attempt_output_tokens,
        packet.per_attempt_total_tokens,
    ) == (4_096, 512, 4_608)
    assert packet.max_attempts == 2
    assert packet.cumulative_token_ceiling == 9_216
    assert packet.request_timeout_ms == 20_000
    assert packet.total_wall_clock_ms == 45_000
    assert packet.cumulative_cost_microusd == 20_000
    assert request.execution_mode == "live"
    assert request.writes_target_repo is False
    assert request.executes_target_repo_mutation is False
    assert request.production_deployment is False
    assert request.inputs[0].sensitivity == "public"


def test_packet_only_evidence_is_redacted_and_has_no_execution_path() -> None:
    evidence = build_packet_validation_evidence()
    rendered = json.dumps(evidence, sort_keys=True)
    source = LIVE_EVIDENCE.read_text(encoding="utf-8")

    assert evidence["status"] == "PASS"
    assert evidence["credential_value_access_count"] == 0
    assert evidence["provider_call_count"] == 0
    assert evidence["transport_call_count"] == 0
    assert evidence["live_provider_execution_authorized"] is False
    assert "OPENAI_API_KEY=" not in rendered
    assert "--validate-packet-only" in source
    assert "--execute" not in source


def test_live_source_uses_injected_boundary_and_no_embedded_secret() -> None:
    source = LIVE_PROVIDER.read_text(encoding="utf-8")

    assert "self._credential_resolver.resolve" in source
    assert "self._transport.send" in source
    assert "HTTPSConnection(" in source
    assert "ssl.create_default_context()" in source
    assert "urllib" not in source
    assert "requests." not in source
    assert "OPENAI_API_KEY=" not in source
    assert "test-key-never-log" not in source
    assert "live_execution_" + "authorized" not in source
    assert "_issue_p14c_fake_transport_capability" in source
    assert 'transport_kind = "live_network"' in source
