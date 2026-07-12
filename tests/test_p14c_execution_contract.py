from __future__ import annotations

from pathlib import Path

from tool_system.ai_worker import (
    P14C_OPENAI_GPT56_LUNA_PACKET,
    p14c_packet_sha256,
)
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
REPORT = ROOT / "docs" / "reports" / "p14c_bounded_real_model_provider_execution.md"
MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14c_bounded_real_model_provider_execution.yaml"
)
CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14c_bounded_real_model_provider_execution.yaml"
)


def test_blueprint_authorizes_only_the_exact_p14c_packet() -> None:
    execution = load_yaml_file(BLUEPRINT)["active_phase_execution"]
    packet = execution["execution_packet"]

    assert execution["record"] == (
        "docs/reports/p14c_bounded_real_model_provider_execution.md"
    )
    assert execution["current_stage"] == ("P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION")
    assert execution["authorized_scope"] == (
        "bounded_openai_gpt56_luna_synthetic_fixture_only"
    )
    assert execution["phase_source_implementation_authorized"] is True
    assert execution["live_model_provider_execution_authorized"] is True
    assert execution["next_stage"] == "P14D_REPOSITORY_CONTEXT_NATURAL_OWNER"
    assert execution["next_stage_authorized"] is False
    assert execution["remote_target_mutation_authorized"] is False
    assert execution["production_deployment_authorized"] is False
    assert packet == {
        "packet_id": "p14c-openai-gpt56-luna-v1",
        "provider_id": "openai",
        "model_id": "gpt-5.6-luna",
        "api_method": "POST",
        "api_host": "api.openai.com",
        "api_port": 443,
        "api_path": "/v1/responses",
        "credential_reference": "env:OPENAI_API_KEY",
        "reasoning_effort": "none",
        "store": False,
        "tools_allowed": False,
        "input_scope": "exact_public_synthetic_fixture_P14C-001_only",
        "max_input_tokens_per_attempt": 4096,
        "max_output_tokens_per_attempt": 512,
        "max_total_tokens_per_attempt": 4608,
        "max_attempts": 2,
        "max_cumulative_tokens": 9216,
        "request_timeout_ms": 20_000,
        "live_evidence_wall_clock_ms": 45_000,
        "max_cumulative_cost_microusd": 20_000,
        "redirects_allowed": False,
        "provider_or_model_fallback_allowed": False,
    }


def test_stage_record_contains_complete_versioned_module_and_packet_contract() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for marker in (
        "module_id: P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION",
        "module_version: 1.0.0",
        "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT@1.0.0",
        "P14MR_MILESTONE_MODULE_INVARIANT@1.0.0",
        "public_interface: BoundedLiveAIWorkerRuntime.run",
        "authorization_envelope: p14c-openai-gpt56-luna-v1",
        "packet_id: p14c-openai-gpt56-luna-v1",
        "api_host: api.openai.com",
        "credential_reference: env:OPENAI_API_KEY",
        "max_cumulative_cost_microusd: 20000",
        "target_repo_mutation: false",
        "production_deployment: false",
        "stop at P14D",
    ):
        assert marker in report


def test_manifest_and_change_plan_match_exact_natural_owner_scope() -> None:
    manifest = load_yaml_file(MANIFEST)
    plan = load_yaml_file(CHANGE_PLAN)
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert manifest["target_repo"] == "apolo183/tool-system"
    assert manifest["target_branch"] == "p14c-bounded-real-provider"
    assert manifest["alignment"]["global"]["section_or_key"] == ("product_objective")
    assert set(plan["changed_files"]) == set(manifest["allowed_files"])
    assert set(manifest["scope"]["out_of_scope"]) >= {
        "repository content in the provider request",
        "finance-us or any target-repository read, branch, PR, write, ready, merge, or mutation",
        "P14D or later P14 implementation",
        "policy boundary modification",
        "cleanup execution, branch deletion, rollback execution, or production deployment",
    }
    assert manifest["approval"] == {
        "required": True,
        "approved_by": "user_approved_p14c_named_execution_packet_and_full_lifecycle",
        "execution_packet": "p14c-openai-gpt56-luna-v1",
        "external_worker_execution": True,
        "internal_pr_lifecycle": True,
        "remote_target_mutation": False,
        "production_deployment": False,
    }


def test_python_packet_is_content_addressed_and_matches_public_budget() -> None:
    packet = P14C_OPENAI_GPT56_LUNA_PACKET

    assert packet.packet_id == "p14c-openai-gpt56-luna-v1"
    assert packet.provider_id == "openai"
    assert packet.model_id == "gpt-5.6-luna"
    assert (packet.api_host, packet.api_port, packet.api_path) == (
        "api.openai.com",
        443,
        "/v1/responses",
    )
    assert packet.credential_reference == "env:OPENAI_API_KEY"
    assert packet.max_attempts == 2
    assert packet.max_cumulative_tokens == 9216
    assert packet.max_cumulative_cost_microusd == 20_000
    assert packet.remote_target_mutation_authorized is False
    assert packet.production_deployment_authorized is False
    assert packet.provider_or_model_fallback_allowed is False
    assert len(p14c_packet_sha256()) == 64


def test_public_docs_preserve_target_and_next_stage_boundaries() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for text in (agents, readme):
        assert "p14c-openai-gpt56-luna-v1" in text
        assert "gpt-5.6-luna" in text
        assert "finance-us" in text
        assert "production" in text.lower()
    assert "P14D or later P14 source implementation" in agents
    assert "P14D-P16" in readme
