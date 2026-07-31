from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.policy.autonomy_policy import validate_autonomy_policy
from tool_system.repo_controller.controller import evaluate_repo_write

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY_PATH = ROOT / "policy" / "autonomy_policy.yaml"


def _pull_request() -> dict[str, object]:
    return {
        "repository": "apolo183/finance-us",
        "number": 3,
        "state": "open",
        "draft": False,
        "mergeable": True,
        "head_sha": "finance-us-head-sha",
        "base": "main",
    }


def _manifest() -> dict[str, object]:
    return {
        "task_id": "finance-us-p1b-merge",
        "task_type": "repo_write",
        "target_repo": "apolo183/finance-us",
        "target_branch": "p1b-minimal-ranking-code",
        "phase": "P1B_MINIMAL_RANKING_CODE",
        "approved_blueprint_refs": [
            {
                "repo": "apolo183/finance-us",
                "path": "blueprint/finance_us_phase_1_v0.yaml",
                "section_or_key": "milestones.P1B_MINIMAL_RANKING_CODE",
            }
        ],
        "scope": {"summary": "Merge an independently approved finance-us P1B PR."},
        "evidence": [
            {
                "repo": "apolo183/finance-us",
                "path": "finance_us/ranking.py",
                "why_relevant": "Bounded implementation under review.",
            }
        ],
        "allowed_files": ["finance_us/ranking.py", "tests/test_ranking.py"],
        "forbidden_files": ["broker/**", "live_runtime/**"],
        "write_mode": "pull_request",
        "verification": {"commands": ["python -m pytest -q"]},
        "rollback": {"method": "git_revert", "reference": "future merge commit"},
        "approval": {
            "required": True,
            "approved_by": "implementation_milestone_authorization",
        },
    }


def _change_plan() -> dict[str, object]:
    return {
        "plan_id": "finance-us-p1b-merge",
        "target_repo": "apolo183/finance-us",
        "task_manifest": "examples/task_manifests/finance_us_p1b_merge.yaml",
        "changed_files": ["finance_us/ranking.py", "tests/test_ranking.py"],
        "verification": {"commands": ["python -m pytest -q"]},
        "rollback": {"method": "git_revert", "reference": "future merge commit"},
    }


def _lifecycle_approval() -> dict[str, object]:
    return {
        "required": True,
        "approved_by": "user_explicit_finance_us_p1b_merge",
        "approval_source": "external_authority:injected_fixture",
        "approved_at": "2026-07-31T00:00:00+09:00",
        "approval_record_id": "finance-us-pr-3-merge",
        "repository_full_name": "apolo183/finance-us",
        "pull_request_number": 3,
        "action": "pr_merge",
        "base_branch": "main",
        "expected_head_sha": "finance-us-head-sha",
        "approval_record_or_reason": "named P1B merge authorization",
    }


def _evaluate(
    manifest: dict[str, object] | None = None,
    lifecycle_approval: dict[str, object] | None = None,
) -> dict[str, object]:
    return evaluate_repo_write(
        pull_request=_pull_request(),
        gate_decision={"status": "PASS", "reasons": []},
        repo_policy=load_yaml_file(POLICY_PATH),
        status_checks=[
            {
                "name": "finance-us-ci",
                "source_app": "github-actions",
                "head_sha": "finance-us-head-sha",
                "status": "completed",
                "conclusion": "success",
            }
        ],
        task_manifest=manifest or _manifest(),
        change_plan=_change_plan(),
        lifecycle_approval=(
            _lifecycle_approval()
            if lifecycle_approval is None
            else lifecycle_approval
        ),
    )


def test_named_finance_us_merge_approval_blocks_without_check_policy() -> None:
    decision = _evaluate()

    assert decision["status"] == "BLOCK"
    assert decision["reasons"] == [
        (
            "required status checks are not configured for repository: "
            "apolo183/finance-us"
        )
    ]


def test_packet_preparation_approval_cannot_authorize_merge() -> None:
    approval = _lifecycle_approval()
    approval["action"] = "packet_preparation"

    decision = _evaluate(lifecycle_approval=approval)

    assert decision["status"] == "BLOCK"
    assert "approval.action must match current lifecycle context" in decision["reasons"]
    assert (
        "lifecycle approval action must match current lifecycle context"
        in decision["reasons"]
    )


def test_target_implementation_approval_cannot_authorize_merge() -> None:
    approval = _lifecycle_approval()
    approval["action"] = "target_implementation"

    decision = _evaluate(lifecycle_approval=approval)

    assert decision["status"] == "BLOCK"
    assert "approval.action must match current lifecycle context" in decision["reasons"]


def test_stale_approval_head_sha_blocks() -> None:
    approval = _lifecycle_approval()
    approval["expected_head_sha"] = "stale-head-sha"

    decision = _evaluate(lifecycle_approval=approval)

    assert decision["status"] == "BLOCK"
    assert "approval.expected_head_sha must match current lifecycle context" in decision["reasons"]


def test_repository_mismatch_blocks() -> None:
    manifest = _manifest()
    manifest["target_repo"] = "apolo183/tool-system"

    decision = _evaluate(manifest)

    assert decision["status"] == "BLOCK"
    assert any("pull request repository must match" in reason for reason in decision["reasons"])


def test_missing_named_approval_fields_block() -> None:
    decision = _evaluate(lifecycle_approval={"required": True})

    assert decision["status"] == "BLOCK"
    assert "approval.approved_by is required for lifecycle action" in decision["reasons"]
    assert "approval.approval_record_or_reason is required" in decision["reasons"]
    assert any(
        reason.startswith("lifecycle approval missing fields:")
        for reason in decision["reasons"]
    )


def test_autonomy_policy_rejects_unscoped_ready_claim() -> None:
    policy = deepcopy(load_yaml_file(AUTONOMY_POLICY_PATH))
    policy["system_handled_when_manifest_allows"].append("pr_ready")

    ok, reasons = validate_autonomy_policy(policy)

    assert not ok
    assert reasons == ["unscoped system handled items are forbidden: pr_ready"]
