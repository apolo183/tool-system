from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from tool_system.agent_worker import NoMutationAgentWorker
from tool_system.agent_worker.process_runtime import (
    ProcessWorkerLimits,
    ProcessWorkerRequest,
    audit_event_denial_reason,
    preflight_process_worker,
    required_resource_limit_names,
    terminal_status_for_trigger,
)


def _request(tmp_path: Path, **overrides: object) -> ProcessWorkerRequest:
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir(exist_ok=True)
    entrypoint = fixture_root / "worker.py"
    entrypoint.write_text("print('fixture')\n", encoding="utf-8")
    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir(exist_ok=True)
    values: dict[str, object] = {
        "request_id": "preflight-fixture",
        "entrypoint": entrypoint,
        "allowed_fixture_root": fixture_root,
        "workspace_root": workspace_root,
        "forbidden_roots": (tmp_path / "forbidden",),
    }
    (tmp_path / "forbidden").mkdir(exist_ok=True)
    values.update(overrides)
    return ProcessWorkerRequest(**values)  # type: ignore[arg-type]


def test_safe_fixture_preflight_passes_without_starting_process(tmp_path: Path) -> None:
    result = preflight_process_worker(_request(tmp_path))

    assert result.status == "PASS"
    assert result.reasons == ()
    assert result.starts_process is False
    assert result.workspace_cleanup_required is True
    assert result.guard_mode == "python_audit_guard_v1"
    assert result.argv_template[0] == str(Path(sys.executable).resolve())
    assert result.argv_template[1:4] == ("-I", "-S", "-B")
    assert "PATH" not in result.environment_names
    assert not any(
        marker in name
        for name in result.environment_names
        for marker in ("TOKEN", "KEY", "SECRET", "PASSWORD", "AUTH", "COOKIE")
    )


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"network_mode": "enabled"}, "network_mode must be disabled"),
        ({"writes_target_repo": True}, "writes_target_repo must be false"),
        (
            {"executes_target_repo_mutation": True},
            "executes_target_repo_mutation must be false",
        ),
        ({"production": True}, "production must be false"),
        ({"forbidden_roots": ()}, "forbidden_roots must be non-empty"),
    ],
)
def test_mutation_network_and_production_requests_block(
    tmp_path: Path, changes: dict[str, object], reason: str
) -> None:
    result = preflight_process_worker(_request(tmp_path, **changes))

    assert result.status == "BLOCK"
    assert reason in result.reasons


def test_entrypoint_outside_fixture_root_blocks(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')\n", encoding="utf-8")

    result = preflight_process_worker(_request(tmp_path, entrypoint=outside))

    assert result.status == "BLOCK"
    assert "entrypoint must resolve under allowed_fixture_root" in result.reasons


def test_entrypoint_symlink_blocks(tmp_path: Path) -> None:
    request = _request(tmp_path)
    link = request.allowed_fixture_root / "link.py"
    link.symlink_to(request.entrypoint)

    result = preflight_process_worker(
        ProcessWorkerRequest(**{**request.__dict__, "entrypoint": link})
    )

    assert result.status == "BLOCK"
    assert "entrypoint must not be a symlink" in result.reasons


def test_oversized_entrypoint_blocks(tmp_path: Path) -> None:
    request = _request(tmp_path)
    request.entrypoint.write_bytes(b"x" * 20)
    limits = ProcessWorkerLimits(max_fixture_bytes=10)

    result = preflight_process_worker(
        ProcessWorkerRequest(**{**request.__dict__, "limits": limits})
    )

    assert result.status == "BLOCK"
    assert "entrypoint exceeds limits.max_fixture_bytes" in result.reasons


def test_workspace_inside_forbidden_root_blocks(tmp_path: Path) -> None:
    request = _request(tmp_path)

    result = preflight_process_worker(
        ProcessWorkerRequest(
            **{
                **request.__dict__,
                "forbidden_roots": (tmp_path,),
            }
        )
    )

    assert result.status == "BLOCK"
    assert "workspace_root must be outside every forbidden_root" in result.reasons


def test_resource_and_termination_contract_is_complete(tmp_path: Path) -> None:
    result = preflight_process_worker(_request(tmp_path))

    assert set(required_resource_limit_names()).issubset(result.resource_limits)
    assert set(result.termination_triggers) == {
        "timeout",
        "cancellation",
        "stdout_limit",
        "stderr_limit",
    }
    assert terminal_status_for_trigger("timeout", None) == "TIMEOUT"
    assert terminal_status_for_trigger("cancellation", None) == "CANCELLED"
    assert terminal_status_for_trigger("stdout_limit", None) == "OUTPUT_LIMIT"
    assert terminal_status_for_trigger(None, 0) == "PASS"
    assert terminal_status_for_trigger(None, 7) == "BLOCK"


def test_audit_policy_blocks_network_process_and_outside_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    stdlib = tmp_path / "stdlib"
    stdlib.mkdir()

    assert audit_event_denial_reason("socket.connect", workspace=workspace)
    assert audit_event_denial_reason("subprocess.Popen", workspace=workspace)
    assert audit_event_denial_reason("os.system", workspace=workspace)
    assert audit_event_denial_reason(
        "import", workspace=workspace, import_name="ctypes.util"
    )
    assert audit_event_denial_reason(
        "open", path="/etc/passwd", workspace=workspace
    )
    assert audit_event_denial_reason(
        "open", path=stdlib / "module.py", workspace=workspace, stdlib_roots=(stdlib,)
    ) is None
    assert audit_event_denial_reason(
        "open",
        path=stdlib / "module.py",
        workspace=workspace,
        stdlib_roots=(stdlib,),
        write=True,
    )
    assert audit_event_denial_reason(
        "open", path=workspace / "result.json", workspace=workspace, write=True
    ) is None


def test_existing_worker_default_remains_no_mutation() -> None:
    assert NoMutationAgentWorker.worker_kind == "no_mutation_agent_worker"


def test_preflight_does_not_fork_or_spawn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("preflight must not start a process")

    monkeypatch.setattr(os, "fork", forbidden)

    assert preflight_process_worker(_request(tmp_path)).status == "PASS"
