from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.dry_run_adapter import (
    build_target_repo_dry_run_plan,
    run_target_repo_dry_run,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "target_repo"
POLICY_PATH = FIXTURE_ROOT / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = FIXTURE_ROOT / "task_manifest.yaml"
P4_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4_target_repo_dry_run.yaml"
TARGET_REPO = "example-org/example-target"


def _policy() -> dict[str, Any]:
    return load_yaml_file(POLICY_PATH)


def _target_manifest() -> dict[str, Any]:
    return load_yaml_file(TARGET_MANIFEST_PATH)


def test_target_repo_dry_run_passes_synthetic_manifest() -> None:
    plan = build_target_repo_dry_run_plan(_target_manifest(), _policy())

    assert plan["status"] == "PASS"
    assert plan["target_repo"] == TARGET_REPO
    assert plan["writes_target_repo"] is False
    assert plan["reasons"] == []


def test_target_repo_dry_run_blocks_missing_target_agents_evidence() -> None:
    manifest = deepcopy(_target_manifest())
    manifest["evidence"] = [item for item in manifest["evidence"] if item.get("path") != "AGENTS.md"]

    plan = build_target_repo_dry_run_plan(manifest, _policy())

    assert plan["status"] == "BLOCK"
    assert "target repo AGENTS.md evidence is required" in plan["reasons"]


def test_target_repo_dry_run_blocks_change_plan_forbidden_path() -> None:
    manifest = _target_manifest()
    change_plan = {
        "plan_id": "example-target-invalid-plan",
        "target_repo": TARGET_REPO,
        "task_manifest": "operator-private:example-target-manifest",
        "changed_files": ["tool_harness/not_allowed.py"],
        "verification": {"commands": ["python3 -m pytest -q"]},
        "rollback": {"method": "git_revert", "reference": "dry-run"},
    }

    plan = build_target_repo_dry_run_plan(manifest, _policy(), change_plan=change_plan)

    assert plan["status"] == "BLOCK"
    assert "blocked changed file: tool_harness/not_allowed.py" in plan["reasons"]
    assert (
        "changed file outside manifest allowlist: tool_harness/not_allowed.py"
        in plan["reasons"]
    )


def test_target_repo_dry_run_writes_audit_jsonl(tmp_path: Path) -> None:
    audit_path = tmp_path / "target_repo_dry_run.jsonl"

    result = run_target_repo_dry_run(
        task_manifest=_target_manifest(),
        repo_policy=_policy(),
        audit_path=audit_path,
    )

    assert result["status"] == "PASS"
    assert result["audit_path"] == str(audit_path)
    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["target_repo"] == TARGET_REPO
    assert record["writes_target_repo"] is False


def test_p4_change_plan_validates() -> None:
    result = validate_change_plan(P4_CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
