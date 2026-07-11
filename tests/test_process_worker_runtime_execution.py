from __future__ import annotations

import json
from pathlib import Path
from threading import Event, Timer

from tool_system.agent_worker.process_runtime import (
    ProcessWorkerLimits,
    ProcessWorkerRequest,
    preflight_process_worker,
    run_process_worker,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
ENTRYPOINT = FIXTURE_ROOT / "p11_worker_fixture.py"


def _dynamic_request(
    tmp_path: Path,
    source: str,
    limits: ProcessWorkerLimits,
) -> ProcessWorkerRequest:
    fixture_root = tmp_path / "dynamic-fixtures"
    fixture_root.mkdir()
    entrypoint = fixture_root / "worker.py"
    entrypoint.write_text(source, encoding="utf-8")
    workspace_root = tmp_path / "dynamic-workspaces"
    workspace_root.mkdir()
    return ProcessWorkerRequest(
        request_id="p11d2-termination-evidence",
        entrypoint=entrypoint,
        allowed_fixture_root=fixture_root,
        workspace_root=workspace_root,
        forbidden_roots=(ROOT,),
        limits=limits,
    )


def test_fixture_worker_runs_with_minimum_baseline(tmp_path: Path) -> None:
    workspace_root = tmp_path / "isolated-workspaces"
    workspace_root.mkdir()
    request = ProcessWorkerRequest(
        request_id="p11d-fixture-execution",
        entrypoint=ENTRYPOINT,
        allowed_fixture_root=FIXTURE_ROOT,
        workspace_root=workspace_root,
        forbidden_roots=(ROOT,),
    )

    preflight = preflight_process_worker(request)
    assert preflight.status == "PASS"
    assert preflight.starts_process is False

    result = run_process_worker(request)
    payload = json.loads(result.stdout)

    assert result.status == "PASS"
    assert result.reasons == ()
    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.workspace_deleted is True
    assert result.network_mode == "disabled"
    assert result.guard_mode == "python_audit_guard_v2"
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production is False
    assert payload == {
        "cwd_matches_workspace": True,
        "denied_probes_run_in_dedicated_processes": True,
        "guard_mode": "python_audit_guard_v2",
        "home_inherited": False,
        "mode": "p13_hardened_fixture_only",
        "network_mode": "disabled",
        "path_inherited": False,
        "secret_like_environment_names": [],
        "workspace_write_succeeded": True,
    }
    assert list(workspace_root.iterdir()) == []


def test_wall_timeout_kills_fixture_process_group_and_cleans_workspace(
    tmp_path: Path,
) -> None:
    request = _dynamic_request(
        tmp_path,
        "while True:\n    pass\n",
        ProcessWorkerLimits(timeout_seconds=0.25, cpu_seconds=2),
    )

    result = run_process_worker(request)

    assert result.status == "TIMEOUT"
    assert result.reasons == ("worker terminated by timeout",)
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []


def test_cancellation_kills_fixture_process_group_and_cleans_workspace(
    tmp_path: Path,
) -> None:
    request = _dynamic_request(
        tmp_path,
        "while True:\n    pass\n",
        ProcessWorkerLimits(timeout_seconds=2.0, cpu_seconds=2),
    )
    cancellation = Event()
    timer = Timer(0.1, cancellation.set)
    timer.start()
    try:
        result = run_process_worker(request, cancellation=cancellation)
    finally:
        timer.cancel()

    assert result.status == "CANCELLED"
    assert result.reasons == ("worker terminated by cancellation",)
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []


def test_output_limit_kills_fixture_process_group_and_caps_evidence(
    tmp_path: Path,
) -> None:
    limits = ProcessWorkerLimits(max_stdout_bytes=128, max_stderr_bytes=128)
    request = _dynamic_request(tmp_path, "print('x' * 4096)\n", limits)

    result = run_process_worker(request)

    assert result.status == "OUTPUT_LIMIT"
    assert result.reasons == ("worker terminated by stdout_limit",)
    assert result.stdout_bytes == 128
    assert len(result.stdout.encode("utf-8")) == 128
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []
