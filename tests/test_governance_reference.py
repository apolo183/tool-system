from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "config" / "governance_reference_v1.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
PINNED_SHA = "f039a5355e1e5ea3fa865b827947b0c1153a2745"


def test_governance_reference_has_exact_v1_shape_and_values() -> None:
    reference = load_yaml_file(REFERENCE)

    assert reference == {
        "reference_contract_version": "governance_reference_v1",
        "downstream_canonical_repo_id": "tool-system",
        "governance_canonical_repo_id": "finance-governance",
        "governance_canonical_remote": (
            "git@github.com:apolo183/finance-governance.git"
        ),
        "governance_commit_sha": PINNED_SHA,
    }


def test_reference_is_pinned_but_does_not_claim_cutover() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    authority = blueprint["milestone_module_invariant"]["authority_scope"]

    assert authority["immutable_group_reference_effect"] == (
        "pinned_candidate_reference_pending_central_repo_check"
    )
    assert authority["group_reference_created_by_this_change"] is True
    assert authority["group_cutover_completed_by_this_change"] is False
    assert blueprint["active_phase_execution"]["authority_effect"] == (
        "tool_system_local_only"
    )


def test_public_contracts_state_the_same_pending_activation_boundary() -> None:
    for path in (AGENTS, README, PRINCIPLES):
        text = path.read_text(encoding="utf-8")
        assert "config/governance_reference_v1.yaml" in text
        assert PINNED_SHA in text
        assert "does not activate group governance" in text


def test_group_constitution_is_not_copied_into_tool_system() -> None:
    assert not (ROOT / "docs" / "global_development_principles_v1.md").exists()
    assert not (ROOT / "config" / "governance_reference_schema_v1.json").exists()
