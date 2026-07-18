from __future__ import annotations

import inspect
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

import tool_system.gate.command_runner as command_runner
from tool_system.cli.execute_change_plan import main as execute_change_plan_main
from tool_system.gate.command_runner import (
    commands_from_change_plan,
    run_commands,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "config/process_authority_v1.yaml"
MANIFEST = ROOT / "examples/task_manifests/tool_system_run_entry.yaml"
OTHER_MANIFEST = ROOT / "examples/task_manifests/tool_system_audit_bundle.yaml"
PLAN = ROOT / "examples/change_plans/tool_system_run_entry.yaml"
POLICY = ROOT / "policy/repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy/autonomy_policy.yaml"


def _protected_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "task_manifest_path": MANIFEST,
        "change_plan_path": PLAN,
        "process_authority_path": AUTHORITY,
        "policy_path": POLICY,
        "autonomy_policy_path": AUTONOMY_POLICY,
        "cwd": ROOT,
        "timeout_seconds": 30,
    }
    values.update(overrides)
    return values


def _record_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="fixture-pass\n", stderr="")

    monkeypatch.setattr(command_runner.subprocess, "run", fake_run)
    return calls


def _copy_explicit_pair(tmp_path: Path) -> tuple[Path, Path]:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_bytes(MANIFEST.read_bytes())
    plan_value = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    plan_value["task_manifest"] = manifest.as_posix()
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump(plan_value, sort_keys=False), encoding="utf-8")
    return manifest, plan


def test_commands_from_change_plan_is_pure_parser() -> None:
    plan = {"verification": {"commands": ["python -V"]}}

    assert commands_from_change_plan(plan) == ["python -V"]


def test_protected_execution_revalidates_real_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _record_subprocess(monkeypatch)

    result = run_commands(**_protected_kwargs())

    assert result["status"] == "PASS"
    assert result["preflight"]["validation_to_dispatch_inputs_equal"] is True
    assert result["input_sha256_before"] == result["input_sha256_after"]
    assert result["subprocess_call_count"] == len(calls)
    assert len(calls) == len(result["command_results"])


@pytest.mark.parametrize(
    ("field", "missing_name"),
    [
        ("process_authority_path", "missing-authority.yaml"),
        ("task_manifest_path", "missing-manifest.yaml"),
        ("change_plan_path", "missing-plan.yaml"),
        ("policy_path", "missing-policy.yaml"),
        ("autonomy_policy_path", "missing-autonomy.yaml"),
    ],
)
def test_missing_preflight_input_blocks_without_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    missing_name: str,
) -> None:
    calls = _record_subprocess(monkeypatch)

    result = run_commands(
        **_protected_kwargs(**{field: tmp_path / missing_name})
    )

    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == 0
    assert calls == []


def test_mismatched_pair_blocks_without_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)

    result = run_commands(
        **_protected_kwargs(task_manifest_path=OTHER_MANIFEST)
    )

    assert result["status"] == "BLOCK"
    assert any("explicit pair" in reason for reason in result["reasons"])
    assert calls == []


def test_manifest_policy_block_runs_no_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("{}\n", encoding="utf-8")
    plan_value = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    plan_value["task_manifest"] = manifest.as_posix()
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump(plan_value, sort_keys=False), encoding="utf-8")

    result = run_commands(
        **_protected_kwargs(task_manifest_path=manifest, change_plan_path=plan)
    )

    assert result["status"] == "BLOCK"
    assert any("task manifest" in reason for reason in result["reasons"])
    assert calls == []


def test_change_plan_validation_block_runs_no_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)
    plan = tmp_path / "plan.yaml"
    plan.write_text("{}\n", encoding="utf-8")

    result = run_commands(
        **_protected_kwargs(change_plan_path=plan)
    )

    assert result["status"] == "BLOCK"
    assert any("change plan" in reason for reason in result["reasons"])
    assert calls == []


def test_no_forgeable_or_unchecked_execution_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)
    parameters = inspect.signature(run_commands).parameters

    assert command_runner.run_commands is run_commands
    assert not {
        "commands",
        "validated",
        "receipt",
        "token",
        "executor",
        "active_gates_path",
    } & set(parameters)
    with pytest.raises(TypeError):
        run_commands(  # type: ignore[call-arg]
            commands=["python -V"],
            validated=True,
        )
    assert calls == []


def test_execute_change_plan_cli_requires_authority_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)

    with pytest.raises(SystemExit) as exc_info:
        execute_change_plan_main([str(MANIFEST), str(PLAN)])

    assert exc_info.value.code == 2
    assert calls == []


@pytest.mark.parametrize(
    "target",
    [
        "process_authority",
        "task_manifest",
        "change_plan",
        "repo_write_policy",
        "autonomy_policy",
    ],
)
def test_input_mutation_between_validation_and_dispatch_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    calls = _record_subprocess(monkeypatch)
    manifest, plan = _copy_explicit_pair(tmp_path)
    authority = tmp_path / "authority.yaml"
    authority.write_bytes(AUTHORITY.read_bytes())
    policy = tmp_path / "repo_write_policy.yaml"
    policy.write_bytes(POLICY.read_bytes())
    autonomy = tmp_path / "autonomy_policy.yaml"
    autonomy.write_bytes(AUTONOMY_POLICY.read_bytes())
    authority_path = authority if target == "process_authority" else AUTHORITY
    paths = {
        "process_authority": authority_path,
        "task_manifest": manifest,
        "change_plan": plan,
        "repo_write_policy": policy,
        "autonomy_policy": autonomy,
    }

    original_capture = command_runner._capture_input_bytes
    capture_count = 0

    def mutate_before_final_capture(
        input_paths: dict[str, Path],
    ) -> tuple[dict[str, bytes], list[str]]:
        nonlocal capture_count
        capture_count += 1
        if capture_count == 2:
            paths[target].write_bytes(paths[target].read_bytes() + b"\n# drift\n")
        return original_capture(input_paths)

    monkeypatch.setattr(
        command_runner,
        "_capture_input_bytes",
        mutate_before_final_capture,
    )
    if target == "process_authority":
        original_validate_authority = command_runner.validate_process_authority

        def validate_authority_fixture(_: Path) -> dict[str, object]:
            return original_validate_authority(AUTHORITY, ROOT)

        monkeypatch.setattr(
            command_runner,
            "validate_process_authority",
            validate_authority_fixture,
        )

    result = run_commands(
        **_protected_kwargs(
            task_manifest_path=manifest,
            change_plan_path=plan,
            process_authority_path=authority_path,
            policy_path=policy,
            autonomy_policy_path=autonomy,
        )
    )

    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == 0
    assert any(target in reason for reason in result["reasons"])
    assert calls == []
