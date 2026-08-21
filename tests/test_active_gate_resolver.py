from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.runner.active_gate_resolver import resolve_change_plan_from_active_gates
from tool_system.runner.task_runner import run_batch_file, run_task_pipeline


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ACTIVE_GATES = ROOT / "examples" / "active_gates.yaml"
ACTIVE_GATES = (
    ROOT
    / "tests"
    / "fixtures"
    / "manifest_validation"
    / "strict_active_gates_v1.yaml"
)
MANIFEST = (
    ROOT
    / "tests"
    / "fixtures"
    / "manifest_validation"
    / "forward_valid_task_manifest_v1.yaml"
)
RESOLVED_PLAN = Path(
    "tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml"
)
BATCH = ROOT / "examples" / "batches" / "tool_system_resolved_batch.yaml"
P6E_PLAN = ROOT / "examples" / "change_plans" / "tool_system_active_gate_resolver.yaml"
P2_MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_p2_gate_foundation.yaml"
P2B_MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_p2b_runner_foundation.yaml"
P2_PLAN = Path("examples/change_plans/tool_system_p2_gate_foundation.yaml")


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _git_index_path() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "index"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    index_path = Path(result.stdout.strip())
    return index_path if index_path.is_absolute() else ROOT / index_path


def _pair(tmp_path: Path, name: str) -> tuple[Path, Path, Path]:
    manifest = tmp_path / "manifests" / f"{name}.yaml"
    plan = tmp_path / "plans" / f"{name}.yaml"
    index = tmp_path / "active_gates.yaml"
    _write_yaml(manifest, {"task_id": f"fixture-{name}"})
    _write_yaml(
        plan,
        {
            "plan_id": f"fixture-{name}-plan",
            "task_manifest": manifest.as_posix(),
            "verification": {"commands": []},
        },
    )
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix()],
            "change_plans": [plan.as_posix()],
        },
    )
    return manifest, plan, index


def test_resolves_change_plan_from_active_gates() -> None:
    resolved = resolve_change_plan_from_active_gates(MANIFEST, ACTIVE_GATES)

    assert resolved == RESOLVED_PLAN


def test_current_p2_pairing_resolves_uniquely_without_repo_changes() -> None:
    protected_paths = [
        LEGACY_ACTIVE_GATES,
        P2_MANIFEST,
        P2B_MANIFEST,
        ROOT / P2_PLAN,
        _git_index_path(),
    ]
    before = {path: path.read_bytes() for path in protected_paths}

    resolved = resolve_change_plan_from_active_gates(
        P2_MANIFEST, LEGACY_ACTIVE_GATES
    )

    assert resolved == P2_PLAN
    assert {path: path.read_bytes() for path in protected_paths} == before


def test_resolver_blocks_registered_manifest_without_plan(tmp_path: Path) -> None:
    manifest, plan, index = _pair(tmp_path, "paired")
    orphan = tmp_path / "manifests" / "orphan.yaml"
    _write_yaml(orphan, {"task_id": "fixture-orphan"})
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix(), orphan.as_posix()],
            "change_plans": [plan.as_posix()],
        },
    )

    with pytest.raises(
        ValueError,
        match="registered task manifest has no change plan",
    ):
        resolve_change_plan_from_active_gates(orphan, index)


def test_resolver_blocks_multiple_matching_plans(tmp_path: Path) -> None:
    manifest, first_plan, index = _pair(tmp_path, "multiple")
    second_plan = tmp_path / "plans" / "multiple-second.yaml"
    _write_yaml(
        second_plan,
        {
            "plan_id": "fixture-multiple-second-plan",
            "task_manifest": manifest.as_posix(),
        },
    )
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix()],
            "change_plans": [first_plan.as_posix(), second_plan.as_posix()],
        },
    )

    with pytest.raises(
        ValueError,
        match="registered task manifest has multiple change plans",
    ):
        resolve_change_plan_from_active_gates(manifest, index)


def test_resolver_blocks_plan_for_unregistered_manifest(tmp_path: Path) -> None:
    manifest, plan, index = _pair(tmp_path, "registered")
    unregistered = tmp_path / "manifests" / "unregistered.yaml"
    _write_yaml(unregistered, {"task_id": "fixture-unregistered"})
    plan_value = yaml.safe_load(plan.read_text(encoding="utf-8"))
    plan_value["task_manifest"] = unregistered.as_posix()
    _write_yaml(plan, plan_value)

    with pytest.raises(
        ValueError,
        match="change plan references unregistered task manifest",
    ):
        resolve_change_plan_from_active_gates(manifest, index)


def test_resolver_blocks_duplicate_plan_path(tmp_path: Path) -> None:
    manifest, plan, index = _pair(tmp_path, "duplicate")
    _write_yaml(
        index,
        {
            "task_manifests": [manifest.as_posix()],
            "change_plans": [plan.as_posix(), plan.as_posix()],
        },
    )

    with pytest.raises(ValueError, match="duplicate change plan path"):
        resolve_change_plan_from_active_gates(manifest, index)


def test_resolver_returns_none_for_unregistered_request(tmp_path: Path) -> None:
    _, _, index = _pair(tmp_path, "active")

    assert (
        resolve_change_plan_from_active_gates(
            tmp_path / "manifests" / "not-active.yaml", index
        )
        is None
    )


def test_resolver_does_not_execute_verification_command(tmp_path: Path) -> None:
    manifest, plan, index = _pair(tmp_path, "no-execution")
    marker = tmp_path / "verification-command-ran"
    plan_value = yaml.safe_load(plan.read_text(encoding="utf-8"))
    plan_value["verification"] = {
        "commands": [
            "python -c 'from pathlib import Path; "
            f'Path("{marker.as_posix()}").write_text("ran")\''
        ]
    }
    _write_yaml(plan, plan_value)
    before = {path: path.read_bytes() for path in (manifest, plan, index)}

    resolved = resolve_change_plan_from_active_gates(manifest, index)

    assert resolved == plan
    assert not marker.exists()
    assert {path: path.read_bytes() for path in (manifest, plan, index)} == before


def test_resolver_blocks_invalid_active_gate_structure(tmp_path: Path) -> None:
    index = tmp_path / "active_gates.yaml"
    _write_yaml(
        index,
        {"task_manifests": "not-a-list", "change_plans": ["plan.yaml"]},
    )

    with pytest.raises(ValueError, match="task_manifests must be a non-empty list"):
        resolve_change_plan_from_active_gates("manifest.yaml", index)


def test_task_runner_blocks_noncanonical_implicit_replay_when_plan_omitted(
    tmp_path: Path,
) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        active_gates_path=ACTIVE_GATES,
        audit_path=tmp_path / "resolved.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert result["change_plan_path"] is None
    assert result["change_plan_resolution_source"] == "legacy_replay_blocked"
    assert "legacy replay requires the canonical examples/active_gates.yaml index" in result["reasons"]
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_batch_runner_blocks_omitted_plans_outside_legacy_replay(
    tmp_path: Path,
) -> None:
    batch = tmp_path / "strict_batch.yaml"
    _write_yaml(
        batch,
        {
            "batch_id": "strict-resolved-batch",
            "halt_on_failure": True,
            "tasks": [
                {"task_manifest": MANIFEST.as_posix()},
                {"task_manifest": MANIFEST.as_posix()},
            ],
        },
    )
    result = run_batch_file(
        batch_path=batch,
        active_gates_path=ACTIVE_GATES,
        audit_path=tmp_path / "resolved_batch.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert result["completed_task_count"] == 1
    assert all(
        task["change_plan_resolution_source"] == "legacy_replay_blocked"
        for task in result["task_results"]
    )


def test_task_runner_accepts_explicit_strict_pair_without_commands(
    tmp_path: Path,
) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        change_plan_path=ROOT / RESOLVED_PLAN,
        audit_path=tmp_path / "explicit.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["change_plan_resolution_source"] == "explicit_process_input"
    assert result["command_results"] == []


def test_active_gate_resolver_change_plan_validates() -> None:
    result = validate_change_plan(P6E_PLAN)

    assert result["status"] == "BLOCK"
    assert any("TASK_MANIFEST_SCHEMA_VIOLATION" in reason for reason in result["reasons"])
