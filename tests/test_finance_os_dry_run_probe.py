from __future__ import annotations

import json
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.dry_run_adapter import run_target_repo_dry_run


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "finance_os_p1b_minimal_ranking.yaml"
PROBE_ARTIFACT_PATH = ROOT / "examples" / "target_repo_dry_runs" / "finance_os_p1b_minimal_ranking.jsonl"
P4A_CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p4a_finance_os_probe.yaml"


def test_finance_os_manifest_probe_writes_no_target_repo(tmp_path: Path) -> None:
    result = run_target_repo_dry_run(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=tmp_path / "finance_os_probe.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == "apolo183/finance-os"
    assert result["target_branch"] == "p1b-minimal-ranking-code"
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []


def test_committed_probe_artifact_is_pass_no_write() -> None:
    record = json.loads(PROBE_ARTIFACT_PATH.read_text(encoding="utf-8").strip())

    assert record["status"] == "PASS"
    assert record["target_repo"] == "apolo183/finance-os"
    assert record["writes_target_repo"] is False
    assert record["reasons"] == []
    assert record["planned_files"] == [
        "pyproject.toml",
        "src/finance_os/__init__.py",
        "src/finance_os/ranking/__init__.py",
        "src/finance_os/ranking/top10.py",
        "tests/test_top10.py",
    ]


def test_p4a_change_plan_validates() -> None:
    result = validate_change_plan(P4A_CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
