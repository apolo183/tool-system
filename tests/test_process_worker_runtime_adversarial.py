from __future__ import annotations

import os
from pathlib import Path

import pytest

import tool_system.agent_worker.process_runtime as runtime
from tool_system.agent_worker.process_runtime import (
    ProcessWorkerRequest,
    preflight_process_worker,
    run_process_worker,
)


ROOT = Path(__file__).resolve().parents[1]


def _request(tmp_path: Path, source: str) -> ProcessWorkerRequest:
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    entrypoint = fixture_root / "worker.py"
    entrypoint.write_text(source, encoding="utf-8")
    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir()
    return ProcessWorkerRequest(
        request_id="p13b-adversarial-fixture",
        entrypoint=entrypoint,
        allowed_fixture_root=fixture_root,
        workspace_root=workspace_root,
        forbidden_roots=(ROOT,),
    )


@pytest.mark.parametrize(
    ("source", "event"),
    [
        ("open('/etc/passwd', encoding='utf-8').read(1)\n", "open"),
        ("import os\nos.listdir('/etc')\n", "os.listdir"),
        ("import os\nos.open(os.__file__, os.O_WRONLY)\n", "open"),
        ("import os\nos.link('/etc/passwd', 'linked-secret')\n", "os.link"),
        ("import os\nos.symlink('/etc/passwd', 'linked-secret')\n", "os.symlink"),
        ("import os\nos.kill(os.getppid(), 0)\n", "os.kill"),
        ("import socket\n", "import:socket"),
        ("import subprocess\n", "import:subprocess"),
        ("import sys\nsys._getframe()\n", "sys._getframe"),
        ("import syslog\nsyslog.syslog('fixture')\n", "syslog.syslog"),
    ],
)
def test_denied_probe_terminates_process_and_cleans_workspace(
    tmp_path: Path, source: str, event: str
) -> None:
    request = _request(tmp_path, source)

    result = run_process_worker(request)

    assert result.status == "BLOCK"
    assert result.exit_code == 126
    assert result.reasons == ("worker exited with code 126",)
    assert result.stderr == f"tool-system guard denied: {event}\n"
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []


def test_outside_remove_is_denied_without_changing_file(tmp_path: Path) -> None:
    protected = tmp_path / "protected.txt"
    protected.write_text("keep", encoding="utf-8")
    request = _request(
        tmp_path,
        f"import os\nos.remove({str(protected)!r})\n",
    )

    result = run_process_worker(request)

    assert result.status == "BLOCK"
    assert result.stderr == "tool-system guard denied: os.remove\n"
    assert protected.read_text(encoding="utf-8") == "keep"


def test_host_secret_like_environment_is_not_inherited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("P13_FIXTURE_API_TOKEN", "must-not-cross-boundary")
    request = _request(
        tmp_path,
        "import os\nprint('P13_FIXTURE_API_TOKEN' in os.environ)\n",
    )

    result = run_process_worker(request)

    assert result.status == "PASS"
    assert result.stdout == "False\n"
    assert "must-not-cross-boundary" not in result.stdout
    assert "must-not-cross-boundary" not in result.stderr


def test_entrypoint_replacement_after_preflight_fails_before_process_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request(tmp_path, "print('original')\n")
    accepted = preflight_process_worker(request)
    outside = tmp_path / "replacement.py"
    outside.write_text("print('replacement')\n", encoding="utf-8")

    def replace_then_return(*args: object, **kwargs: object) -> object:
        request.entrypoint.unlink()
        request.entrypoint.symlink_to(outside)
        return accepted

    monkeypatch.setattr(runtime, "preflight_process_worker", replace_then_return)

    result = run_process_worker(request)

    assert result.status == "BLOCK"
    assert result.exit_code is None
    assert result.reasons[0].startswith("worker runtime failed closed: OSError:")
    assert result.stdout == ""
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []


def test_multi_link_entrypoint_blocks_before_execution(tmp_path: Path) -> None:
    request = _request(tmp_path, "print('must not run')\n")
    os.link(request.entrypoint, request.allowed_fixture_root / "second.py")

    result = run_process_worker(request)

    assert result.status == "BLOCK"
    assert "entrypoint must have exactly one hard link" in result.reasons
    assert result.exit_code is None
