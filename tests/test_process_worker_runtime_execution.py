from __future__ import annotations

import json
from pathlib import Path

from tool_system.agent_worker.process_runtime import (
    ProcessWorkerRequest,
    preflight_process_worker,
    run_process_worker,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
ENTRYPOINT = FIXTURE_ROOT / "p11_worker_fixture.py"


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
    assert result.guard_mode == "python_audit_guard_v1"
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production is False
    assert payload == {
        "cwd_matches_workspace": True,
        "home_inherited": False,
        "mode": "p11_fixture_only",
        "network_mode": "disabled",
        "outside_read_blocked": True,
        "path_inherited": False,
        "secret_like_environment_names": [],
        "socket_import_blocked": True,
        "subprocess_import_blocked": True,
        "workspace_write_succeeded": True,
    }
    assert list(workspace_root.iterdir()) == []
