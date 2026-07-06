from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_agent_role_taxonomy_has_required_fine_grained_roles() -> None:
    blueprint = load_yaml_file(BLUEPRINT_PATH)
    agents = blueprint["agents"]

    required_roles = {
        "request_intake",
        "evidence_collector",
        "blueprint_architect",
        "task_decomposer",
        "dag_planner",
        "policy_guard",
        "change_planner",
        "patch_author",
        "test_engineer",
        "ci_operator",
        "code_reviewer",
        "contract_reviewer",
        "repo_controller",
        "target_repo_adapter",
        "target_repo_executor",
        "audit_recorder",
        "cleanup_owner",
    }

    assert required_roles.issubset(set(agents))
    assert blueprint["role_control_rules"]["dag_must_include_evidence_policy_verification_and_audit_nodes"] is True
    assert blueprint["role_control_rules"]["business_domain_roles_forbidden_in_tool_system"] is True


def test_target_executor_is_separate_from_approval_and_adapter_roles() -> None:
    blueprint = load_yaml_file(BLUEPRINT_PATH)
    agents = blueprint["agents"]

    assert agents["target_repo_executor"]["group"] == "target"
    assert agents["target_repo_adapter"]["group"] == "target"
    assert "execute_target_file_write_after_approval" in agents["target_repo_executor"]["permissions"]
    assert "produce_pr_write_plan" in agents["target_repo_adapter"]["permissions"]
    assert blueprint["role_control_rules"]["no_single_role_may_approve_and_execute_target_mutation"] is True
