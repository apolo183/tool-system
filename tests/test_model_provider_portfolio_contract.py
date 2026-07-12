from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
MODEL_CONTRACT = ROOT / "docs" / "model_provider_portfolio_and_economics_contract_v1.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"


def test_provider_portfolio_contract_is_product_control_not_runtime_authority() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
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

    execution = blueprint["active_phase_execution"]
    assert execution["next_stage"] == "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    assert execution["next_stage_authorized"] is False
    assert execution["live_model_provider_execution_authorized"] is False
    assert execution["remote_target_mutation_authorized"] is False
    assert execution["production_deployment_authorized"] is False
    assert blueprint["successor_authorization"]["next_phase_entry_authorized"] is False


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
    assert "exact provider/version identifiers" in normalized
    assert "expected_total_economic_cost_per_accepted_module" in contract
    assert "avoidable future subscription renewal" in normalized
    assert "critical-path delay" in normalized
    assert "local compute depreciation allocation, electricity" in normalized


def test_recalculation_cadence_and_roadmap_owners_are_locked() -> None:
    contract = MODEL_CONTRACT.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)
    p15 = blueprint["milestones"]["P15_MULTI_PROJECT_BENCHMARK"]
    p16 = blueprint["milestones"]["P16_PRODUCTION_OPERATIONS_ACCEPTANCE"]

    assert "every 24 hours" in contract
    assert "every 72 hours" in contract
    assert "weekly" in contract
    assert "before each billing renewal and at least monthly" in contract
    assert "provider-adapter qualification" in contract
    assert "continuous discovery" in contract
    assert p15["stage_plan"][-1]["stage"] == "P15F_BENCHMARK_ACCEPTANCE_CLOSURE"
    assert "versioned atomic portfolio publication and rollback" in p16["outputs"]


def test_public_contracts_point_to_the_detailed_contract() -> None:
    contract_path = "docs/model_provider_portfolio_and_economics_contract_v1.md"

    assert contract_path in README.read_text(encoding="utf-8")
    assert contract_path in AGENTS.read_text(encoding="utf-8")
    assert contract_path in PRINCIPLES.read_text(encoding="utf-8")
