from __future__ import annotations

import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.dry_run_adapter import run_target_repo_dry_run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "target_repo"
POLICY_PATH = FIXTURE_ROOT / "repo_write_policy.yaml"
TARGET_MANIFEST_PATH = FIXTURE_ROOT / "task_manifest.yaml"
TARGET_REPO = "example-org/example-target"


def test_synthetic_manifest_probe_writes_no_target_repo(tmp_path: Path) -> None:
    audit_path = tmp_path / "target_repo_probe.jsonl"
    result = run_target_repo_dry_run(
        task_manifest=load_yaml_file(TARGET_MANIFEST_PATH),
        repo_policy=load_yaml_file(POLICY_PATH),
        audit_path=audit_path,
    )

    assert result["status"] == "PASS"
    assert result["target_repo"] == TARGET_REPO
    assert result["target_branch"] == "agent/add-greeting"
    assert result["writes_target_repo"] is False
    assert result["reasons"] == []

    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["status"] == "PASS"
    assert record["target_repo"] == TARGET_REPO
    assert record["writes_target_repo"] is False
    assert record["planned_files"] == [
        "src/example_target/__init__.py",
        "src/example_target/greeting.py",
        "tests/test_greeting.py",
    ]
