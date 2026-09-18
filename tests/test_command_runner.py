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
MANIFEST = ROOT / "tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml"
OTHER_MANIFEST = ROOT / "examples/task_manifests/tool_system_audit_bundle.yaml"
PLAN = ROOT / "tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml"
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

    monkeypatch.setattr(command_runner, "_run_bounded_command", fake_run)
    return calls


def _copy_explicit_pair(
    tmp_path: Path,
    commands: list[str] | None = None,
) -> tuple[Path, Path]:
    manifest = tmp_path / "manifest.yaml"
    manifest_value = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    manifest_value["verification"]["commands"] = commands or []
    manifest.write_text(
        yaml.safe_dump(manifest_value, sort_keys=False), encoding="utf-8"
    )
    plan_value = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    plan_value["task_manifest"] = manifest.as_posix()
    plan_value["verification"]["commands"] = commands or []
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump(plan_value, sort_keys=False), encoding="utf-8")
    return manifest, plan


def test_commands_from_change_plan_is_pure_parser() -> None:
    plan = {"verification": {"commands": ["python -V"]}}

    assert commands_from_change_plan(plan) == ["python -V"]


@pytest.mark.parametrize("error", [FileNotFoundError, PermissionError])
def test_failed_process_dispatch_retains_attempt_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[OSError]
) -> None:
    manifest, plan = _copy_explicit_pair(tmp_path, ["missing-program", "python -V"])
    calls = []

    def failed(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        raise error("private executable details must not be returned")

    monkeypatch.setattr(command_runner, "_run_bounded_command", failed)
    result = run_commands(
        **_protected_kwargs(task_manifest_path=manifest, change_plan_path=plan)
    )
    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == len(calls) == 1
    assert result["command_results"] == []
    assert "private executable" not in str(result)


@pytest.mark.parametrize("command", ['python -c "unterminated', "   "])
def test_invalid_command_argv_does_not_count_as_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    manifest, plan = _copy_explicit_pair(tmp_path, [command])
    calls = _record_subprocess(monkeypatch)
    result = run_commands(
        **_protected_kwargs(task_manifest_path=manifest, change_plan_path=plan)
    )
    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == 0
    assert calls == []


def test_partial_command_dispatch_counts_timeout_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands = ["python -V", "python slow.py", "python not-reached.py"]
    manifest, plan = _copy_explicit_pair(tmp_path, commands)
    calls = []

    def partial(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if len(calls) == 2:
            raise subprocess.TimeoutExpired(args, 1)
        return subprocess.CompletedProcess(args, 0, stdout="first\n", stderr="")

    monkeypatch.setattr(command_runner, "_run_bounded_command", partial)
    result = run_commands(
        **_protected_kwargs(task_manifest_path=manifest, change_plan_path=plan)
    )
    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == len(calls) == 2
    assert len(result["command_results"]) == 1


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

def test_cancellation_blocks_before_command_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _record_subprocess(monkeypatch)
    manifest, plan = _copy_explicit_pair(tmp_path, ["python -V"])

    result = run_commands(
        **_protected_kwargs(
            task_manifest_path=manifest,
            change_plan_path=plan,
            cancellation_requested=lambda: True,
        )
    )

    assert result["status"] == "BLOCK"
    assert result["subprocess_call_count"] == 0
    assert result["reasons"] == ["command execution cancelled by caller"]
    assert calls == []


def test_command_output_limit_and_timeout_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, plan = _copy_explicit_pair(tmp_path, ["python -V"])
    def oversized(
        args: list[str],
        **_: Any,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args,
            0,
            stdout="x" * 33,
            stderr="",
        )

    monkeypatch.setattr(command_runner, "_run_bounded_command", oversized)
    limited = run_commands(
        **_protected_kwargs(
            task_manifest_path=manifest,
            change_plan_path=plan,
            max_output_bytes=32,
        )
    )
    assert limited["status"] == "BLOCK"
    assert limited["subprocess_call_count"] == 1
    assert limited["command_results"] == []
    assert limited["reasons"] == [
        "configured command output exceeded byte limit"
    ]

    def timeout(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(args, 1)

    monkeypatch.setattr(command_runner, "_run_bounded_command", timeout)
    timed_out = run_commands(
        **_protected_kwargs(
            task_manifest_path=manifest,
            change_plan_path=plan,
            timeout_seconds=1,
        )
    )
    assert timed_out["status"] == "BLOCK"
    assert timed_out["subprocess_call_count"] == 1
    assert timed_out["command_results"] == []
    assert timed_out["reasons"] == ["configured command exceeded timeout"]


def test_command_environment_excludes_provider_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, plan = _copy_explicit_pair(tmp_path, ["python -V"])
    observed_environments: list[dict[str, str]] = []

    def fake_run(
        args: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        observed_environments.append(dict(kwargs["env"]))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(command_runner, "_run_bounded_command", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "not-forwarded")
    result = run_commands(
        **_protected_kwargs(
            task_manifest_path=manifest,
            change_plan_path=plan,
        )
    )

    assert result["status"] == "PASS"
    assert observed_environments
    assert all(
        "OPENAI_API_KEY" not in environment
        for environment in observed_environments
    )


def _python_command(code: str) -> str:
    import shlex
    import sys
    return shlex.join([sys.executable, '-c', code])


@pytest.mark.parametrize('fd', [1, 2])
def test_streaming_overflow_stops_before_child_completion(tmp_path: Path, fd: int) -> None:
    command = _python_command(
        f'import os,time; os.write({fd}, b"x" * 4096); time.sleep(20)'
    )
    manifest, plan = _copy_explicit_pair(tmp_path, [command, _python_command('pass')])
    result = run_commands(**_protected_kwargs(
        task_manifest_path=manifest, change_plan_path=plan,
        max_output_bytes=32, timeout_seconds=1,
    ))
    assert result['reasons'] == ['configured command output exceeded byte limit']
    assert result['subprocess_call_count'] == 1
    assert result['command_results'] == []


@pytest.mark.parametrize('code', [
    'import os,time; os.close(1); os.close(2); time.sleep(20)',
    'import time; time.sleep(20)',
])
def test_streaming_timeout_reaps_direct_child(tmp_path: Path, monkeypatch, code: str) -> None:
    import time
    processes = []
    original = command_runner.subprocess.Popen
    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        processes.append(child)
        return child
    monkeypatch.setattr(command_runner.subprocess, 'Popen', capture)
    manifest, plan = _copy_explicit_pair(tmp_path, [_python_command(code)])
    started = time.monotonic()
    result = run_commands(**_protected_kwargs(
        task_manifest_path=manifest, change_plan_path=plan, timeout_seconds=1,
    ))
    assert result['reasons'] == ['configured command exceeded timeout']
    assert result['subprocess_call_count'] == 1
    assert time.monotonic() - started < 5
    assert processes[0].poll() is not None
    assert processes[0].stdout.closed and processes[0].stderr.closed


def test_dual_pipe_draining_and_exact_limits(tmp_path: Path) -> None:
    # More than a pipe capacity on each stream; sequential draining deadlocks.
    limit = 131072
    code = ('import os; '
            '[(os.write(2,b"e"*4096),os.write(1,b"o"*4096)) for _ in range(32)]')
    manifest, plan = _copy_explicit_pair(tmp_path, [_python_command(code)])
    result = run_commands(**_protected_kwargs(
        task_manifest_path=manifest, change_plan_path=plan,
        max_output_bytes=limit, timeout_seconds=5,
    ))
    assert result['status'] == 'PASS'
    assert result['command_results'][0]['stdout'] == 'o' * limit
    assert result['command_results'][0]['stderr'] == 'e' * limit


def test_continuous_output_has_bounded_reads_and_reaps(tmp_path: Path, monkeypatch) -> None:
    processes = []
    requests = []
    original_popen = command_runner.subprocess.Popen
    original_read = command_runner.os.read
    def capture(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        processes.append(child)
        return child
    def read(fd, count):
        if processes and fd in (processes[0].stdout.fileno(), processes[0].stderr.fileno()):
            requests.append(count)
            assert count <= 1025
        return original_read(fd, count)
    monkeypatch.setattr(command_runner.subprocess, 'Popen', capture)
    monkeypatch.setattr(command_runner.os, 'read', read)
    code = 'import os\nwhile True: os.write(1,b"x"*4096)'
    manifest, plan = _copy_explicit_pair(tmp_path, [_python_command(code)])
    result = run_commands(**_protected_kwargs(
        task_manifest_path=manifest, change_plan_path=plan,
        max_output_bytes=1024, timeout_seconds=5,
    ))
    assert result['reasons'] == ['configured command output exceeded byte limit']
    assert requests
    assert processes[0].poll() is not None
    assert processes[0].stdout.closed and processes[0].stderr.closed


def test_streaming_preserves_utf8_newlines_and_exit_status(tmp_path: Path) -> None:
    code = 'import os,sys; os.write(1,bytes([195,169,13,10])); os.write(2,b"err\\r"); sys.exit(7)'
    manifest, plan = _copy_explicit_pair(tmp_path, [_python_command(code)])
    result = run_commands(**_protected_kwargs(
        task_manifest_path=manifest, change_plan_path=plan, max_output_bytes=4,
    ))
    assert result['status'] == 'PASS'  # exit interpretation belongs to caller's gate
    record = result['command_results'][0]
    assert (record['stdout'], record['stderr'], record['exit_code']) == ('é\n', 'err\n', 7)


def test_real_failed_launch_count(tmp_path: Path) -> None:
    manifest, plan = _copy_explicit_pair(tmp_path, [str(tmp_path/'nonexistent-command')])
    result = run_commands(**_protected_kwargs(task_manifest_path=manifest, change_plan_path=plan))
    assert result['status'] == 'BLOCK'
    assert result['subprocess_call_count'] == 1
    assert result['command_results'] == []
