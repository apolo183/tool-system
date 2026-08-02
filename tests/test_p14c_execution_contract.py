from __future__ import annotations

import json
from pathlib import Path

from tool_system.ai_worker.live_evidence import (
    build_packet_validation_evidence,
    build_parser,
)
from tool_system.ai_worker.live_provider import (
    build_p14c_execution_packet,
    build_p14c_synthetic_request,
    validate_p14c_execution_packet,
)
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.process_authority.live_provider_approval import (
    P14C_CRITICAL_SOURCE_PATHS,
    P14C_SOURCE_MANIFEST_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
REPORT = ROOT / "docs" / "reports" / "p14c_bounded_real_model_provider_execution.md"
ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "p14c_bounded_real_provider_acceptance.md"
)
LIVE_ISSUER_REPORT = ROOT / "docs" / "reports" / "p14c_live_issuer_implementation.md"
SOURCE_HARDENING_REPORT = (
    ROOT / "docs" / "reports" / "p14c_source_seal_replay_hardening.md"
)
GATE_REPORT = ROOT / "docs" / "reports" / "p14c_pr_authorization_gate.md"
LIVE_PROVIDER = ROOT / "src" / "tool_system" / "ai_worker" / "live_provider.py"
LIVE_EVIDENCE = ROOT / "src" / "tool_system" / "ai_worker" / "live_evidence.py"
ENTRY_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14c_live_execution_entry_v1.yaml"
)
ENTRY_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14c_live_execution_entry_v1.yaml"
)
AUTH_DIAGNOSTICS_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14c_qwen_auth_diagnostics_v1.yaml"
)
AUTH_DIAGNOSTICS_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14c_qwen_auth_diagnostics_v1.yaml"
)
DEEPSEEK_RECOVERY_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14c_deepseek_recovery_v1.yaml"
)
DEEPSEEK_RECOVERY_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14c_deepseek_recovery_v1.yaml"
)
DEEPSEEK_ACCEPTANCE_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14c_deepseek_result_acceptance_v1.yaml"
)
DEEPSEEK_ACCEPTANCE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14c_deepseek_result_acceptance_v1.yaml"
)
ENTRY_FILES = {
    "README.md",
    "pyproject.toml",
    "config/module_registry_v1.yaml",
    "config/process_authority_schema_v1.json",
    "config/process_authority_v1.yaml",
    "docs/process_authority_contract_v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/modules/process-authority-contract-v1.md",
    "docs/reports/p14c_bounded_real_model_provider_execution.md",
    "src/tool_system/ai_worker/live_evidence.py",
    "src/tool_system/process_authority/contract.py",
    "src/tool_system/process_authority/live_provider_approval.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_p14c_live_issuer.py",
    "tests/test_module_registry.py",
    "tests/test_process_authority.py",
    "examples/task_manifests/tool_system_p14c_live_execution_entry_v1.yaml",
    "examples/change_plans/tool_system_p14c_live_execution_entry_v1.yaml",
}
AUTH_DIAGNOSTICS_FILES = {
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "src/tool_system/ai_worker/live_evidence.py",
    "src/tool_system/ai_worker/live_provider.py",
    "tests/test_ai_worker_live_provider.py",
    "tests/test_module_registry.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_phase_alignment.py",
    "examples/task_manifests/tool_system_p14c_qwen_auth_diagnostics_v1.yaml",
    "examples/change_plans/tool_system_p14c_qwen_auth_diagnostics_v1.yaml",
}
DEEPSEEK_RECOVERY_FILES = {
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "src/tool_system/ai_worker/live_evidence.py",
    "src/tool_system/ai_worker/live_provider.py",
    "tests/test_ai_worker_live_provider.py",
    "tests/test_module_registry.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_p14c_live_issuer.py",
    "tests/test_phase_alignment.py",
    "examples/task_manifests/tool_system_p14c_deepseek_recovery_v1.yaml",
    "examples/change_plans/tool_system_p14c_deepseek_recovery_v1.yaml",
}
DEEPSEEK_ACCEPTANCE_FILES = {
    "docs/reports/p14c_bounded_real_provider_acceptance.md",
    "docs/tool_system_project_state_v1.yaml",
    "tests/test_p14c_execution_contract.py",
    "tests/test_phase_alignment.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_p14_phase_entry_contract.py",
    "examples/task_manifests/"
    "tool_system_p14c_deepseek_result_acceptance_v1.yaml",
    "examples/change_plans/"
    "tool_system_p14c_deepseek_result_acceptance_v1.yaml",
}


def test_p14c_bounded_deepseek_receipt_is_accepted_without_new_authority() -> None:
    project_state = load_yaml_file(PROJECT_STATE)
    current_phase = project_state["current_phase"]
    p14c = project_state["p14c"]
    boundaries = project_state["authorization_boundaries"]
    report = REPORT.read_text(encoding="utf-8")
    live_issuer_report = LIVE_ISSUER_REPORT.read_text(encoding="utf-8")
    source_hardening_report = SOURCE_HARDENING_REPORT.read_text(encoding="utf-8")
    acceptance_report = ACCEPTANCE_REPORT.read_text(encoding="utf-8")

    assert current_phase["last_accepted_stage"] == (
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    )
    assert current_phase["last_accepted_stage_record"] == (
        "docs/reports/p14c_bounded_real_provider_acceptance.md"
    )
    assert current_phase["next_stage"] == "P14D_REPOSITORY_CONTEXT_NATURAL_OWNER"
    assert current_phase["next_stage_authorized"] is False
    assert p14c["implementation_authorization_packet"] == "P14C-IMPL-v2"
    assert p14c["source_status"] == "bounded_deepseek_live_provider_proof_accepted"
    assert p14c["acceptance_record"] == (
        "docs/reports/p14c_bounded_real_provider_acceptance.md"
    )
    assert p14c["acceptance_authorization_packet"] == (
        "P14C-DEEPSEEK-RESULT-ACCEPTANCE-v1"
    )
    assert p14c["acceptance_status"] == "accepted"
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
    assert p14c["source_hardening_authorization_packet"] == (
        "P14C-SOURCE-SEAL-REPLAY-LIFECYCLE-v1"
    )
    assert p14c["approval_contract_version"] == (
        "p14c-live-execution-approval-v2"
    )
    assert p14c["execution_source_seal_required"] is True
    assert p14c["durable_replay_boundary"] == (
        "single_host_sqlite_burn_on_claim_at_most_once"
    )
    assert p14c["multi_host_exactly_once_claimed"] is False
    first_attempt = p14c["first_live_attempt"]
    assert first_attempt["packet_id"] == "P14C-IMPL-v2"
    assert first_attempt["provider_id"] == "openai"
    assert first_attempt["approval_comment_id"] == 5_152_284_946
    assert first_attempt["approval_durably_consumed"] is True
    assert first_attempt["live_capability_issued"] is True
    assert first_attempt["provider_invocation_count"] == 1
    assert first_attempt["redacted_error_code"] == "PROVIDER_FAILURE"
    assert first_attempt["output_received"] is False
    assert first_attempt["credential_value_recorded"] is False
    assert first_attempt["acceptance_effect"] == "none"
    assert p14c["real_live_approval_record_created"] is True
    assert p14c["live_capability_issued"] is True
    assert p14c["prior_recovery_implementation_packet"] == (
        "P14C-QWEN-RECOVERY-v1"
    )
    prior_recovery = p14c["prior_recovery_attempt"]
    assert prior_recovery["provider_id"] == "qwen"
    assert prior_recovery["model_id"] == "qwen3.7-plus-2026-05-26"
    assert prior_recovery["api_access_mode"] == "one_explicit_execute_only"
    assert prior_recovery["fallback_allowed"] is False
    assert prior_recovery["live_execution_attempted"] is True
    assert prior_recovery["live_execution_succeeded"] is False
    assert prior_recovery["approval_comment_id"] == 5_156_628_612
    assert prior_recovery["approval_durably_consumed"] is True
    assert prior_recovery["credential_resolution_attempt_count"] == 1
    assert prior_recovery["provider_invocation_count"] == 1
    assert prior_recovery["redacted_failure_class"] == "AUTH_FAILED"
    assert prior_recovery["failure_detail"] == (
        "ambiguous_http_401_or_403_under_legacy_classifier"
    )
    assert prior_recovery["output_received"] is False
    assert prior_recovery["credential_value_recorded"] is False
    assert prior_recovery["usage_tokens"] == 0
    assert prior_recovery["cost_microunits"] == 0
    assert prior_recovery["acceptance_effect"] == "none"
    assert p14c["recovery_implementation_packet"] == (
        "P14C-DEEPSEEK-RECOVERY-v1"
    )
    recovery = p14c["recovery_route"]
    assert recovery["provider_id"] == "deepseek"
    assert recovery["model_id"] == "deepseek-v4-flash"
    assert recovery["endpoint"] == (
        "https://api.deepseek.com/chat/completions"
    )
    assert recovery["credential_reference"] == (
        "file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key"
    )
    assert recovery["api_access_mode"] == "one_explicit_execute_only"
    assert recovery["fallback_allowed"] is False
    assert recovery["live_execution_attempted"] is True
    assert recovery["live_execution_succeeded"] is True
    assert recovery["approval_conversation"] == 157
    assert recovery["approval_comment_id"] == 5_158_008_082
    assert recovery["approval_record_sha256"] == (
        "61715c0b87e46b871016265cf88a0ca6c8b9e4383c444ea41db5374192173e5d"
    )
    assert recovery["approval_durably_consumed"] is True
    assert recovery["credential_resolution_attempt_count"] == 1
    assert recovery["provider_invocation_count"] == 1
    assert recovery["transport_attempt_ceiling"] == 1
    assert recovery["usage"] == {
        "input_tokens": 106,
        "output_tokens": 39,
        "total_tokens": 145,
        "cost_microunits": 184,
        "duration_ms": 1770,
    }
    assert recovery["output_sha256"] == (
        "16a6f16328aad19a4d64aa4ff329c7e78e02a09a270e2b55bb3f795a3e6bba33"
    )
    source_seal = recovery["source_seal"]
    assert source_seal["execution_commit_sha"] == (
        "55ed92e336d2aa110e50e197c5eefb8fa80896a8"
    )
    assert source_seal["execution_tree_sha"] == (
        "2e6ce267738a396f52a5847052f91edafea74af9"
    )
    assert source_seal["execution_host_id"] == "apolo-9004"
    assert source_seal["source_seal_sha256"] == (
        "1d7688faf8be7950ff88b359af2d726ccaea52e832a33796defd08c3793f2019"
    )
    assert recovery["credential_value_recorded"] is False
    assert recovery["raw_provider_output_recorded"] is False
    assert recovery["acceptance_effect"] == (
        "p14c_bounded_real_model_provider_execution_accepted"
    )
    assert p14c["stage_accepted"] is True
    assert boundaries["state_file_grants_authority"] is False
    assert boundaries["live_model_provider_execution_authorized"] is False
    assert boundaries["credential_value_access_authorized"] is False
    assert boundaries["downstream_repository_access_authorized"] is False
    assert boundaries["remote_target_mutation_authorized"] is False
    assert boundaries["production_deployment_authorized"] is False
    assert boundaries["cleanup_execution_authorized"] is False
    assert boundaries["rollback_execution_authorized"] is False
    assert (
        "P14C_SOURCE_ONLY_NO_EXECUTION_NOT_ACCEPTED"
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
    assert "SOURCE_HARDENED_FAKE_IO_ONLY_NO_EXECUTION_NOT_ACCEPTED" in (
        source_hardening_report
    )
    assert "real GitHub approval reads: `0`" in source_hardening_report
    assert "credential-value accesses: `0`" in source_hardening_report
    assert "real provider calls: `0`" in source_hardening_report
    assert "single-host at-most-once" in source_hardening_report
    assert "does not accept P14C" in source_hardening_report
    assert "P14C_ACCEPTED_BOUNDED_DEEPSEEK_PROOF" in acceptance_report
    assert "P14C-DEEPSEEK-RESULT-ACCEPTANCE-v1" in acceptance_report
    assert "5158008082" in acceptance_report
    assert "145" in acceptance_report
    assert "184 microUSD" in acceptance_report
    assert "does not authorize another provider call or entry to P14D" in (
        " ".join(acceptance_report.split())
    )
    assert "No provider was called" in acceptance_report


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
    assert packet.packet_id == "P14C-DEEPSEEK-RECOVERY-v1"
    assert packet.implementation_authorization_base_sha == (
        "d9c211324487e3bfd31c1276763ed2ed781cc085"
    )
    assert "central_" + "governance_base" not in packet.canonical_record()
    assert (packet.provider_id, packet.model_id) == (
        "deepseek",
        "deepseek-v4-flash",
    )
    assert (packet.method, packet.host, packet.path) == (
        "POST",
        "api.deepseek.com",
        "/chat/completions",
    )
    assert packet.credential_reference == (
        "file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key"
    )
    assert packet.reasoning_effort == "none"
    assert packet.store is packet.tools_allowed is False
    assert (
        packet.per_attempt_input_tokens,
        packet.per_attempt_output_tokens,
        packet.per_attempt_total_tokens,
    ) == (1_024, 128, 1_152)
    assert packet.max_attempts == 1
    assert packet.cumulative_token_ceiling == 1_152
    assert packet.request_timeout_ms == 20_000
    assert packet.total_wall_clock_ms == 25_000
    assert packet.cumulative_cost_microusd == 2_000
    assert request.execution_mode == "live"
    assert request.writes_target_repo is False
    assert request.executes_target_repo_mutation is False
    assert request.production_deployment is False
    assert request.inputs[0].sensitivity == "public"


def test_packet_only_evidence_is_redacted_and_operator_entry_is_explicit() -> None:
    evidence = build_packet_validation_evidence()
    rendered = json.dumps(evidence, sort_keys=True)
    source = LIVE_EVIDENCE.read_text(encoding="utf-8")
    parser = build_parser()

    assert evidence["status"] == "PASS"
    assert evidence["credential_value_access_count"] == 0
    assert evidence["provider_call_count"] == 0
    assert evidence["transport_call_count"] == 0
    assert evidence["live_provider_execution_authorized"] is False
    assert "api_key =" not in rendered
    assert "--validate-packet-only" in source
    assert "prepare-approval" in source
    assert '"execute"' in source
    assert parser.parse_args(["--validate-packet-only"]).validate_packet_only is True
    assert parser.parse_args(
        [
            "prepare-approval",
            "--repository-root",
            ".",
            "--ledger",
            "/var/lib/tool-system/p14c.sqlite3",
        ]
    ).command == "prepare-approval"
    assert parser.parse_args(
        [
            "execute",
            "--repository-root",
            ".",
            "--ledger",
            "/var/lib/tool-system/p14c.sqlite3",
            "--comment-id",
            "1",
        ]
    ).command == "execute"


def test_operator_entry_pair_freezes_exact_source_only_scope() -> None:
    manifest = load_yaml_file(ENTRY_MANIFEST)
    plan = load_yaml_file(ENTRY_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert set(manifest["allowed_files"]) == ENTRY_FILES
    assert set(manifest["scope"]["in_scope"]) == ENTRY_FILES
    assert set(plan["changed_files"]) == ENTRY_FILES
    assert closure["baseline_commit"] == (
        "999cb60d20a15730dbf0096ad20a598f3bf0fa5c"
    )
    assert closure["baseline_tree"] == (
        "43e8790a3d4df3cc58985237599ac1a2b3aaff7e"
    )
    assert closure["finite_budgets"]["real_github_approval_reads"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["transport_attempts"] == 0
    assert closure["allowed_scope"] == "exact_19_paths_listed_below"
    assert "P14C-LIVE-ENTRY-SCOPE-CORR-v1" in manifest["approval"][
        "approval_source"
    ]
    assert "attempt_number" not in manifest["bounded_closure"][
        "recurrence_fingerprint"
    ]
    assert "blueprint/tool_system_v0.yaml" not in ENTRY_FILES
    assert "docs/tool_system_project_state_v1.yaml" not in ENTRY_FILES
    assert "src/tool_system/ai_worker/live_provider.py" not in ENTRY_FILES


def test_qwen_auth_diagnostics_pair_freezes_exact_zero_live_io_scope() -> None:
    manifest = load_yaml_file(AUTH_DIAGNOSTICS_MANIFEST)
    plan = load_yaml_file(AUTH_DIAGNOSTICS_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert set(manifest["allowed_files"]) == AUTH_DIAGNOSTICS_FILES
    assert set(manifest["scope"]["in_scope"]) == AUTH_DIAGNOSTICS_FILES
    assert set(plan["changed_files"]) == AUTH_DIAGNOSTICS_FILES
    assert closure["baseline_commit"] == (
        "1d0100be219e991fdebc3f138477e948b6517511"
    )
    assert closure["baseline_tree"] == (
        "b1988b14e0a09fb69023eaa991b8a4e4d513c52d"
    )
    assert closure["allowed_scope"] == "exact_12_paths_listed_below"
    assert closure["finite_budgets"]["real_github_approval_reads"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["transport_attempts"] == 0
    assert "attempt_number" not in manifest["bounded_closure"][
        "recurrence_fingerprint"
    ]
    assert "blueprint/tool_system_v0.yaml" not in AUTH_DIAGNOSTICS_FILES
    assert "config/process_authority_v1.yaml" not in AUTH_DIAGNOSTICS_FILES


def test_deepseek_recovery_pair_freezes_exact_zero_live_io_scope() -> None:
    manifest = load_yaml_file(DEEPSEEK_RECOVERY_MANIFEST)
    plan = load_yaml_file(DEEPSEEK_RECOVERY_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert set(manifest["allowed_files"]) == DEEPSEEK_RECOVERY_FILES
    assert set(manifest["scope"]["in_scope"]) == DEEPSEEK_RECOVERY_FILES
    assert set(plan["changed_files"]) == DEEPSEEK_RECOVERY_FILES
    assert closure["baseline_commit"] == (
        "d9c211324487e3bfd31c1276763ed2ed781cc085"
    )
    assert closure["baseline_tree"] == (
        "2632892774fe5f6587568349e3d6dbf10410b25e"
    )
    assert closure["allowed_scope"] == "exact_13_paths_listed_below"
    assert closure["finite_budgets"]["real_github_approval_reads"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["transport_attempts"] == 0
    assert "attempt_number" not in manifest["bounded_closure"][
        "recurrence_fingerprint"
    ]
    assert "blueprint/tool_system_v0.yaml" not in DEEPSEEK_RECOVERY_FILES
    assert "config/process_authority_v1.yaml" not in DEEPSEEK_RECOVERY_FILES


def test_deepseek_acceptance_pair_freezes_exact_nine_file_scope() -> None:
    manifest = load_yaml_file(DEEPSEEK_ACCEPTANCE_MANIFEST)
    plan = load_yaml_file(DEEPSEEK_ACCEPTANCE_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert set(manifest["allowed_files"]) == DEEPSEEK_ACCEPTANCE_FILES
    assert set(manifest["scope"]["in_scope"]) == DEEPSEEK_ACCEPTANCE_FILES
    assert set(plan["changed_files"]) == DEEPSEEK_ACCEPTANCE_FILES
    assert closure["baseline_commit"] == (
        "55ed92e336d2aa110e50e197c5eefb8fa80896a8"
    )
    assert closure["baseline_tree"] == (
        "2e6ce267738a396f52a5847052f91edafea74af9"
    )
    assert closure["allowed_scope"] == "exact_9_paths_listed_below"
    assert closure["finite_budgets"]["real_github_approval_reads"] == 1
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["transport_attempts"] == 0
    assert "attempt_number" not in manifest["bounded_closure"][
        "recurrence_fingerprint"
    ]
    assert all(not path.startswith("src/") for path in DEEPSEEK_ACCEPTANCE_FILES)
    assert "blueprint/tool_system_v0.yaml" not in DEEPSEEK_ACCEPTANCE_FILES
    assert "config/process_authority_v1.yaml" not in DEEPSEEK_ACCEPTANCE_FILES


def test_operator_entry_is_part_of_critical_source_manifest_v2() -> None:
    assert P14C_SOURCE_MANIFEST_VERSION == "p14c-critical-runtime-source-v2"
    assert "src/tool_system/ai_worker/live_evidence.py" in (
        P14C_CRITICAL_SOURCE_PATHS
    )


def test_live_source_uses_injected_boundary_and_no_embedded_secret() -> None:
    source = LIVE_PROVIDER.read_text(encoding="utf-8")

    assert "self._credential_resolver.resolve" in source
    assert "self._transport.send" in source
    assert "HTTPSConnection(" in source
    assert "ssl.create_default_context()" in source
    assert "urllib" not in source
    assert "requests." not in source
    assert "api_key =" not in source
    assert "test-key-never-log" not in source
    assert "live_execution_" + "authorized" not in source
    assert "_issue_p14c_fake_transport_capability" in source
    assert 'transport_kind = "live_network"' in source
