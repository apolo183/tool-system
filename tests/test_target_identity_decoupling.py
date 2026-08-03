from __future__ import annotations

import json
import re
from pathlib import Path

from tool_system.architecture.repo_manifest import (
    EXACT_FORMAL_PARSER_MODE,
    parse_manifest_formal_rows,
)
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "REPO_MANIFEST.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
TASK_SCHEMA = ROOT / "harness" / "task_manifest.schema.json"
PUBLIC_POLICY = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "target_repo"
TARGET_MANIFEST = TARGET_FIXTURE_ROOT / "task_manifest.yaml"
TARGET_POLICY = TARGET_FIXTURE_ROOT / "repo_write_policy.yaml"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "target_identity_decoupling_acceptance.md"
)
GROUP_REPOSITORY_IDENTITY = re.compile(r"\bapolo183/[A-Za-z0-9_.-]+\b")
ALLOWED_PUBLIC_IDENTITIES = {
    "apolo183/tool-system",
    "apolo183/finance-governance",
}


def _formal_paths() -> list[str]:
    mode, rows, reasons = parse_manifest_formal_rows(
        MANIFEST.read_text(encoding="utf-8")
    )
    assert mode == EXACT_FORMAL_PARSER_MODE
    assert reasons == []
    return [row["path"] for row in rows]


def test_active_formal_files_serialize_no_downstream_project_identity() -> None:
    violations: dict[str, list[str]] = {}
    for relative_path in _formal_paths():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        identities = {
            value.removesuffix(".git")
            for value in GROUP_REPOSITORY_IDENTITY.findall(text)
        }
        unexpected = sorted(identities - ALLOWED_PUBLIC_IDENTITIES)
        if unexpected:
            violations[relative_path] = unexpected

    assert violations == {}


def test_task_manifest_repository_identity_is_structural_not_enumerated() -> None:
    schema = json.loads(TASK_SCHEMA.read_text(encoding="utf-8"))
    target_repo = schema["properties"]["target_repo"]
    fixture = load_yaml_file(TARGET_MANIFEST)

    assert "enum" not in target_repo
    assert target_repo["maxLength"] == 140
    assert re.fullmatch(target_repo["pattern"], fixture["target_repo"])


def test_public_policy_is_self_only_and_external_target_policy_is_injected() -> None:
    public_policy = load_yaml_file(PUBLIC_POLICY)
    fixture_policy = load_yaml_file(TARGET_POLICY)
    fixture_manifest = load_yaml_file(TARGET_MANIFEST)

    assert set(public_policy["allowed_target_repos"]) == {"apolo183/tool-system"}
    assert public_policy["external_target_policy"]["binding_mode"] == (
        "caller_supplied"
    )
    assert public_policy["external_target_policy"][
        "public_repository_serializes_downstream_identity"
    ] is False
    fixture_rules = fixture_policy["allowed_target_repos"][
        fixture_manifest["target_repo"]
    ]
    assert fixture_rules["target_repo_approval_required"] is True


def test_blueprint_and_state_record_project_neutral_boundary_without_authority() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    state = load_yaml_file(PROJECT_STATE)
    correction = state["target_identity_decoupling"]

    assert (
        "caller_supplied_target_repository_identity_and_policy"
        in blueprint["product_contract"]["inputs"]
    )
    assert (
        "downstream_project_identity_and_policy_are_caller_supplied"
        in blueprint["product_objective"]["completion_definition"]
    )
    assert correction["authority_effect"] == "none"
    assert correction["public_core_contract"][
        "downstream_repository_identity_serialized"
    ] is False
    assert correction["p15c_authorized"] is False


def test_state_and_report_record_terminal_decoupling_lifecycle() -> None:
    state = load_yaml_file(PROJECT_STATE)
    correction = state["target_identity_decoupling"]
    pull_request = correction["draft_pull_request"]
    ci = correction["hosted_ci"]
    terminal = correction["terminal_lifecycle"]
    report = ACCEPTANCE_REPORT.read_text(encoding="utf-8")

    assert correction["implementation_status"] == (
        "accepted_merged_terminal_evidence_verified"
    )
    assert pull_request["number"] == 171
    assert pull_request["final_head_commit"] == (
        "2dbd0c6735b4a0f081d1a064458750d73d870cfe"
    )
    assert pull_request["final_head_tree"] == (
        "7abd3b555d5c05f8bdf719c18619459ae9e06645"
    )
    assert correction["hosted_ci_status"] == "passed_on_final_head"
    assert ci["run_id"] == 30811800450
    assert ci["run_number"] == 1067
    assert ci["conclusion"] == "success"
    assert terminal["no_drift_ready_check"] == "passed"
    assert terminal["squash_merge_commit"] == (
        "1ede788b8b1c36bcc224cde15a5f6462c9b51938"
    )
    assert terminal["retained_branch"] == (
        "agent/target-identity-decoupling-v1"
    )
    assert terminal["retained_branch_verified"] is True
    assert "The lifecycle is accepted and closed" in report
    assert "P15C remains unauthorized" in report
