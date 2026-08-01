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
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
REPORT = ROOT / "docs" / "reports" / "p14c_bounded_real_model_provider_execution.md"
LIVE_ISSUER_REPORT = ROOT / "docs" / "reports" / "p14c_live_issuer_implementation.md"
GATE_REPORT = ROOT / "docs" / "reports" / "p14c_pr_authorization_gate.md"
LIVE_PROVIDER = ROOT / "src" / "tool_system" / "ai_worker" / "live_provider.py"
LIVE_EVIDENCE = ROOT / "src" / "tool_system" / "ai_worker" / "live_evidence.py"


def test_p14c_source_authorization_does_not_claim_live_execution_or_acceptance() -> (
    None
):
    project_state = load_yaml_file(PROJECT_STATE)
    current_phase = project_state["current_phase"]
    p14c = project_state["p14c"]
    boundaries = project_state["authorization_boundaries"]
    report = REPORT.read_text(encoding="utf-8")
    live_issuer_report = LIVE_ISSUER_REPORT.read_text(encoding="utf-8")

    assert current_phase["last_accepted_stage"] == (
        "P14MR_MILESTONE_MODULE_INVARIANT"
    )
    assert current_phase["next_stage"] == "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    assert current_phase["next_stage_authorized"] is False
    assert p14c["implementation_authorization_packet"] == "P14C-IMPL-v2"
    assert p14c["source_status"] == (
        "corrected_source_and_live_issuer_merged_no_execution_not_accepted"
    )
    assert (
        p14c["live_issuer_implementation_authorization_packet"]
        == "P14C-LIVE-ISSUER-IMPL-v1"
    )
    assert (
        p14c["live_issuer_lifecycle_authorization_packet"]
        == "P14C-LIVE-ISSUER-LIFECYCLE-v1"
    )
    live_source = p14c["live_issuer_source"]
    assert live_source["head"] == (
        "46e66481447fd64ac9a0916b179eb652aef647ad"
    )
    assert live_source["pull_request"] == 148
    assert live_source["merge"] == (
        "20cbb13feb934ce95f2624dafc4510efcd04f1da"
    )
    assert live_source["tree"] == (
        "b2263ba1c8121bb7d2f30b96b88cebabfa880872"
    )
    assert live_source["publication_status"] == (
        "merged_hosted_ci_validated"
    )
    assert live_source["pull_request_ci_run_id"] == 30_616_081_875
    assert live_source["main_ci_run_id"] == 30_616_558_561
    assert live_source["branch_retained"] is True
    assert p14c["trust_root"] == "github_owner_issue_comment"
    assert p14c["real_live_approval_record_created"] is False
    assert p14c["live_capability_issued"] is False
    assert p14c["stage_accepted"] is False
    assert boundaries["state_file_grants_authority"] is False
    assert boundaries["live_model_provider_execution_authorized"] is False
    assert boundaries["credential_value_access_authorized"] is False
    assert boundaries["downstream_repository_access_authorized"] is False
    assert boundaries["remote_target_mutation_authorized"] is False
    assert boundaries["production_deployment_authorized"] is False
    assert (
        "CORRECTED_SOURCE_AND_LIVE_ISSUER_MERGED_NO_EXECUTION_NOT_ACCEPTED"
        in report
    )
    assert "P14C-CORR-v1" in report
    assert "P14C-CORR-READY-v1" in report
    assert "P14C-CORR-MERGE-v1" in report
    assert "#143" in report
    assert "352b2638bb9a1cf7504a224c0571062072b32db1" in report
    assert "provider_call_count=0" in report
    assert "credential_value_access_count=0" in report
    assert "transport_call_count=0" in report
    assert (
        "SOURCE_MERGED_HOSTED_CI_VALIDATED_NO_LIVE_EXECUTION_NOT_ACCEPTED"
        in live_issuer_report
    )
    assert "pull request: `#148`" in " ".join(live_issuer_report.split())
    assert "30616081875" in live_issuer_report
    assert "30616558561" in live_issuer_report
    assert "real approval records created or edited by this change: `0`" in (
        live_issuer_report
    )
    assert "real provider calls: `0`" in live_issuer_report
    assert "not evidence gaps filled by this Draft PR" not in live_issuer_report
    assert "DRAFT_PR_PENDING" not in live_issuer_report
    assert "Hosted CI remains pending" not in live_issuer_report
    assert (
        "the source-publication evidence recorded here does not close them"
        in " ".join(live_issuer_report.split())
    )


def test_merged_pr_gate_evidence_keeps_p14c_and_live_mutation_blocked() -> None:
    report = GATE_REPORT.read_text(encoding="utf-8")
    normalized_report = " ".join(report.split())

    assert "MERGED_AND_HOSTED_CI_VALIDATED_P14C_STILL_BLOCKED" in report
    assert "PR `#145`" in report
    assert "PR `#146`" in report
    assert "0a8ec193b5e8945703f2f6ca7bbce323ee127645" in report
    assert "3256e17c416394ac7d209f9cafc529a3fb72504d" in report
    assert (
        "Hosted CI run `#1014` (`30602453765`) completed with `success`"
        in normalized_report
    )
    assert "does not create a live capability issuer" in normalized_report
    assert "does not accept or close P14C" in normalized_report
    assert "MERGED_GATE_HARDENING_DRAFT_PR_PENDING" not in report
    assert "Hosted CI remains required after Draft PR publication" not in report


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
