from __future__ import annotations

from pathlib import Path

import tomllib

from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
MODEL_CONTRACT = ROOT / "docs" / "model_provider_portfolio_and_economics_contract_v1.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
OPERATOR_SETTINGS = (
    ROOT / "examples" / "operator_config" / "tool_system_settings.example.toml"
)
P15A_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p15a_provider_portfolio_qualification_specification.md"
)
P15B_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p15b_adapter_router_profiler_fixture_acceptance.md"
)


def test_provider_portfolio_contract_is_product_control_not_runtime_authority() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)
    contract = MODEL_CONTRACT.read_text(encoding="utf-8")

    assert "status: `ROADMAP_CONTRACT_ACTIVE_NO_RUNTIME_CLAIM`" in contract
    assert "module_id: `adaptive_model_portfolio_and_economics`" in contract
    assert "AIWorkerProvider adapters" in contract
    assert "CodexChatGPTProvider" in contract
    assert "OpenAIApiProvider" in contract
    assert "DeepSeekApiProvider" in contract
    assert "QwenApiProvider" in contract
    assert "GlmApiProvider" in contract
    assert "KimiApiProvider" in contract
    assert "LocalModelProvider" in contract
    assert "The names above are portfolio candidates, not enabled routes." in contract

    boundaries = project_state["authorization_boundaries"]
    assert boundaries["live_model_provider_execution_authorized"] is True
    assert boundaries["remote_target_mutation_authorized"] is False
    assert boundaries["production_deployment_authorized"] is False
    p14c = project_state["p14c"]
    assert p14c["implementation_authorization_packet"] == "P14C-IMPL-v2"
    assert p14c["stage_accepted"] is True
    p15a = project_state["p15a"]
    assert p15a["specification_status"] == "accepted_governance_only"
    assert p15a["provider_candidates_enabled"] == 0
    assert p15a["provider_invocations"] == 0
    assert p15a["credential_value_accesses"] == 0
    assert p15a["p15b_authorized"] is False
    p15b = project_state["p15b"]
    assert p15b["implementation_status"] == (
        "accepted_isolated_fixture_no_live_provider"
    )
    assert p15b["module"]["current_module_id"] == (
        "adaptive_model_portfolio_and_economics"
    )
    assert p15b["module"]["aggregate_interface_id"] == (
        "adaptive-model-portfolio-and-economics-api"
    )
    assert p15b["hard_floors_evaluated_before_economics"] is True
    assert p15b["provider_invocations"] == 0
    assert p15b["credential_value_accesses"] == 0
    assert p15b["p15c_authorized"] is False
    assert p15b["stage_accepted"] is True
    report = P15A_REPORT.read_text(encoding="utf-8")
    assert "P15A_ACCEPTED_GOVERNANCE_ONLY_QUALIFICATION_SPECIFICATION" in report
    assert "expected_total_economic_cost_per_accepted_module" in report
    p15b_report = P15B_REPORT.read_text(encoding="utf-8")
    assert "P15B_ACCEPTED_ISOLATED_FIXTURE_NO_LIVE_PROVIDER" in p15b_report
    assert "P15C_authorized: false" in p15b_report
    assert "active_phase_execution" not in blueprint
    assert "p14c_source_implementation" not in blueprint


def test_credentials_and_private_economics_stay_out_of_public_contracts() -> None:
    contract = MODEL_CONTRACT.read_text(encoding="utf-8")
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (MODEL_CONTRACT, PRINCIPLES, README, AGENTS)
    )

    assert "credential-reference schemas" in contract
    assert "never stores API keys" in contract
    assert "must not scrape a browser session" in contract
    assert "must not be hard-coded in this public repository" in contract
    assert "$2,000" not in combined
    assert "$200" not in combined
    assert "OPENAI_API_KEY=" not in combined


def test_subscription_primary_and_all_api_default_disabled_rules_are_locked() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)
    rules = blueprint["role_control_rules"]
    completion = set(blueprint["product_objective"]["completion_definition"])
    settings = tomllib.loads(OPERATOR_SETTINGS.read_text(encoding="utf-8"))
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (MODEL_CONTRACT, PRINCIPLES, README, AGENTS)
    )

    assert rules["chatgpt_codex_subscription_is_daily_default_route"] is True
    assert rules["every_large_model_api_is_default_disabled"] is True
    assert rules["api_key_presence_grants_call_authority"] is False
    assert rules["live_provider_and_model_are_repository_external_configuration"]
    assert rules["unavailable_providers_may_be_skipped"] is True
    assert rules["provider_specific_fake_io_contract_tests_required"] is True
    assert rules["one_enabled_usable_api_smoke_satisfies_backup_path_proof"] is True
    assert rules["simultaneous_multi_provider_availability_required_for_completion"] is False
    assert rules["named_provider_funding_required_for_completion"] is False
    assert rules["moving_alias_exact_version_required_for_completion"] is False
    assert {
        "chatgpt_codex_subscription_is_the_daily_development_route",
        "every_large_model_api_is_disabled_by_default",
        "api_key_presence_never_grants_call_authority",
        "live_provider_and_model_selection_is_repository_external",
        "unavailable_or_unfunded_api_providers_may_be_skipped",
        "every_provider_specific_adapter_passes_fake_io_contract_tests",
        "one_enabled_usable_api_key_smoke_proves_the_backup_path",
    } <= completion
    assert settings["p15c"]["enabled"] is False
    assert settings["p15c"]["provider_enabled"] == {
        "deepseek": False,
        "openai": False,
        "qwen": False,
    }
    assert set(settings["p15c"]["provider_budget_micro_usd"].values()) == {0}
    assert "ordinary development route" in combined
    assert "disabled by default" in combined
    assert "one controlled smoke test" in combined
    lifecycle = project_state["provider_mode_and_acceptance_realignment_lifecycle"]
    assert lifecycle["formal_rules"]["all_large_model_apis_default_disabled"]
    assert lifecycle["formal_rules"]["api_key_presence_grants_call_authority"] is False
    assert lifecycle["final_live_smoke_executed"] is False
    assert lifecycle["p15_stage_accepted"] is False
    assert lifecycle["p16_stage_entered"] is False
    assert set(lifecycle["source_stage_evidence"].values()) == {0}


def test_task_assessment_is_advisory_and_policy_route_is_deterministic() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    agents = blueprint["agents"]
    rules = blueprint["role_control_rules"]

    assert agents["task_complexity_assessor"]["group"] == "planning"
    assert "assess_task_complexity" in (
        agents["task_complexity_assessor"]["permissions"]
    )
    assert agents["model_portfolio_analyst"]["group"] == "optimization"
    assert rules["task_complexity_assessment_is_advisory_only"] is True
    assert rules["provider_model_route_decision_is_deterministic_policy_owned"] is True
    assert rules["risk_and_authorization_floors_cannot_be_downgraded_for_cost"] is True
    assert rules["policy_data_budget_or_precondition_failure_never_triggers_provider_bypass"] is True
    assert rules["critical_path_time_is_primary_soft_optimization_metric"] is True
    assert (
        rules["safety_quality_data_and_authorization_constraints_override_economics"]
        is True
    )


def test_failure_classes_lifecycle_and_economics_are_explicit() -> None:
    contract = MODEL_CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(contract.split())

    assert "bounded availability failover" in normalized
    assert "bounded same-route repair" in normalized
    assert "evidence-backed escalation" in normalized
    assert "Switching providers may not bypass the block" in normalized
    assert "DISCOVERED -> QUARANTINED -> BENCHMARKING -> SHADOW -> CANARY" in contract
    assert "ELIGIBLE -> PRIMARY" in contract
    assert "DEGRADED -> RETIRED" in contract
    assert "provider/model actually requested" in normalized
    assert "NO_AVAILABLE_PROVIDER" in contract
    assert "expected_total_economic_cost_per_accepted_module" in contract
    assert "avoidable future subscription renewal" in normalized
    assert "critical-path delay" in normalized
    assert "local compute depreciation allocation, electricity" in normalized


def test_conditional_api_maintenance_and_roadmap_owners_are_locked() -> None:
    contract = MODEL_CONTRACT.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)
    p15 = blueprint["milestones"]["P15_MULTI_PROJECT_BENCHMARK"]
    p16 = blueprint["milestones"]["P16_PRODUCTION_OPERATIONS_ACCEPTANCE"]

    assert "only when API mode is explicitly enabled" in contract
    assert "does not impose a 24-hour, 72-hour, weekly, or" in contract
    assert "monthly live-call requirement" in contract
    assert "provider-specific fake-I/O adapter" in contract
    assert "controlled single-provider live smoke" in contract
    assert "one live usable key is sufficient for the final backup-path smoke" in contract
    assert p15["stage_plan"][-1]["stage"] == "P15F_BENCHMARK_ACCEPTANCE_CLOSURE"
    assert (
        "versioned atomic enabled-route publication and rollback when API mode is enabled"
        in p16["outputs"]
    )
    assert (
        "proof that disabled or unavailable API providers and an unreleased optional API plugin do not block production-operations acceptance"
        in p16["outputs"]
    )


def test_public_contracts_point_to_the_detailed_contract() -> None:
    contract_path = "docs/model_provider_portfolio_and_economics_contract_v1.md"

    assert contract_path in README.read_text(encoding="utf-8")
    assert contract_path in AGENTS.read_text(encoding="utf-8")
    assert contract_path in PRINCIPLES.read_text(encoding="utf-8")
