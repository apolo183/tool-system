from __future__ import annotations

import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event, Timer

import pytest

from tool_system.agent_worker.process_runtime import (
    ProcessWorkerLimits,
    ProcessWorkerRequest,
    preflight_process_worker,
    run_process_worker,
)
from tool_system.orchestrator import (
    DurableOrchestratorStore,
    LeaseConflict,
    StateConflict,
)


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _request(
    tmp_path: Path,
    source: str,
    limits: ProcessWorkerLimits | None = None,
) -> ProcessWorkerRequest:
    tmp_path.mkdir(parents=True, exist_ok=True)
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    entrypoint = fixture_root / "worker.py"
    entrypoint.write_text(source, encoding="utf-8")
    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir()
    return ProcessWorkerRequest(
        request_id="p13d-integrated-local-evidence",
        entrypoint=entrypoint,
        allowed_fixture_root=fixture_root,
        workspace_root=workspace_root,
        forbidden_roots=(ROOT,),
        limits=limits or ProcessWorkerLimits(),
    )


def _store(tmp_path: Path, clock: Clock | None = None) -> DurableOrchestratorStore:
    return DurableOrchestratorStore(
        tmp_path / "state.sqlite3",
        forbidden_roots=(ROOT,),
        clock=clock or Clock(),
    )


def _task(store: DurableOrchestratorStore, task_id: str = "task") -> None:
    if store.get_run("run") is None:
        store.create_run("run", blueprint_ref="blueprint", manifest_ref="manifest")
    store.add_task(
        "run",
        task_id,
        idempotency_key=f"task-key:{task_id}",
        expected_precondition_sha=SHA,
    )


@pytest.mark.parametrize(
    "source",
    [
        "open('/etc/passwd', encoding='utf-8').read(1)\n",
        "import os\nos.symlink('/etc/passwd', 'escape')\n",
        "import socket\n",
        "import subprocess\n",
    ],
)
def test_integrated_adversarial_probes_fail_closed(
    tmp_path: Path, source: str
) -> None:
    request = _request(tmp_path, source)

    result = run_process_worker(request)

    assert result.status == "BLOCK"
    assert result.exit_code == 126
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production is False


def test_executable_substitution_and_secret_inheritance_remain_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request(
        tmp_path,
        "import os\nprint('P13D_FIXTURE_TOKEN' in os.environ)\n",
    )
    monkeypatch.setenv("P13D_FIXTURE_TOKEN", "must-not-cross-boundary")

    if Path("/bin/sh").exists():
        substituted = preflight_process_worker(
            request, python_executable=Path("/bin/sh")
        )
        assert substituted.status == "BLOCK"
        assert "python_executable must match" in " ".join(substituted.reasons)

    result = run_process_worker(request)
    assert result.status == "PASS"
    assert result.stdout == "False\n"
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []


@pytest.mark.parametrize(
    ("source", "limits", "expected_status"),
    [
        (
            "with open('large.bin', 'wb') as stream:\n"
            "    stream.write(b'x' * 8192)\n",
            ProcessWorkerLimits(max_file_bytes=512),
            "BLOCK",
        ),
        (
            "handles = []\n"
            "for index in range(64):\n"
            "    handles.append(open(str(index) + '.txt', 'w'))\n",
            ProcessWorkerLimits(max_open_files=12),
            "BLOCK",
        ),
        (
            "payload = b'x' * (256 * 1024 * 1024)\nprint(len(payload))\n",
            ProcessWorkerLimits(memory_bytes=64 * 1024 * 1024),
            "BLOCK",
        ),
        (
            "while True:\n    pass\n",
            ProcessWorkerLimits(timeout_seconds=3.0, cpu_seconds=1),
            "BLOCK",
        ),
        (
            "print('x' * 8192)\n",
            ProcessWorkerLimits(max_stdout_bytes=256),
            "OUTPUT_LIMIT",
        ),
        (
            "import os\nos.write(2, b'x' * 8192)\n",
            ProcessWorkerLimits(max_stderr_bytes=256),
            "OUTPUT_LIMIT",
        ),
    ],
)
def test_resource_pressure_is_bounded_and_workspace_is_removed(
    tmp_path: Path,
    source: str,
    limits: ProcessWorkerLimits,
    expected_status: str,
) -> None:
    request = _request(tmp_path, source, limits)

    result = run_process_worker(request)

    assert result.status == expected_status
    assert result.workspace_deleted is True
    assert list(request.workspace_root.iterdir()) == []
    assert result.stdout_bytes <= limits.max_stdout_bytes
    assert result.stderr_bytes <= limits.max_stderr_bytes


def test_repeated_timeout_and_cancellation_remove_every_workspace(
    tmp_path: Path,
) -> None:
    for index in range(3):
        timeout_request = _request(
            tmp_path / f"timeout-{index}",
            "while True:\n    pass\n",
            ProcessWorkerLimits(timeout_seconds=0.15, cpu_seconds=2),
        )
        timeout_result = run_process_worker(timeout_request)
        assert timeout_result.status == "TIMEOUT"
        assert list(timeout_request.workspace_root.iterdir()) == []

        cancel_request = _request(
            tmp_path / f"cancel-{index}",
            "while True:\n    pass\n",
            ProcessWorkerLimits(timeout_seconds=2.0, cpu_seconds=2),
        )
        cancellation = Event()
        timer = Timer(0.05, cancellation.set)
        timer.start()
        try:
            cancel_result = run_process_worker(
                cancel_request, cancellation=cancellation
            )
        finally:
            timer.cancel()
        assert cancel_result.status == "CANCELLED"
        assert list(cancel_request.workspace_root.iterdir()) == []


def test_repeated_concurrent_claims_have_exactly_one_winner(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    contenders = 6

    for task_index in range(6):
        task_id = f"task-{task_index}"
        _task(store, task_id)
        barrier = Barrier(contenders)

        def claim(owner: str) -> str:
            barrier.wait()
            try:
                store.claim_task(
                    "run", task_id, lease_owner=owner, lease_seconds=30
                )
            except LeaseConflict:
                return "conflict"
            return owner

        with ThreadPoolExecutor(max_workers=contenders) as executor:
            futures = [
                executor.submit(claim, f"worker-{index}")
                for index in range(contenders)
            ]
            outcomes = [future.result() for future in futures]

        assert outcomes.count("conflict") == contenders - 1
        assert len(set(outcomes) - {"conflict"}) == 1


def test_task_and_outbox_leases_recover_after_reopen(tmp_path: Path) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    _task(store)
    store.claim_task("run", "task", lease_owner="worker", lease_seconds=5)
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker",
        task_attempt=1,
    )
    store.begin_side_effect("effect", lease_owner="worker", task_attempt=1)
    store.complete_side_effect(
        "effect",
        lease_owner="worker",
        task_attempt=1,
        expected_precondition_sha=SHA,
        result={"receipt": "ok"},
        event_kind="fixture.completed",
        event_payload={"effect_id": "effect"},
    )
    store.claim_outbox_event(
        "effect:completed", lease_owner="publisher", lease_seconds=5
    )
    clock.advance(6)

    reopened = _store(tmp_path, clock)
    assert reopened.recover_expired_leases()[0]["status"] == "READY"
    assert reopened.recover_expired_outbox_leases()[0]["state"] == "PENDING"
    published = reopened.reconcile_outbox(
        lambda event: {"published": event["event_id"]},
        lease_owner="publisher-2",
    )
    assert published[0]["status"] == "PUBLISHED"
    assert reopened.get_outbox_event("effect:completed")["state"] == "PUBLISHED"  # type: ignore[index]


def test_atomic_fault_and_integrity_failures_remain_detectable(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    _task(store)
    store.claim_task("run", "task", lease_owner="worker", lease_seconds=100)
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={},
        lease_owner="worker",
        task_attempt=1,
    )
    store.begin_side_effect("effect", lease_owner="worker", task_attempt=1)
    database = tmp_path / "state.sqlite3"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """
            CREATE TRIGGER reject_outbox BEFORE INSERT ON outbox
            BEGIN SELECT RAISE(ABORT, 'p13d fault'); END
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="p13d fault"):
        store.complete_side_effect(
            "effect",
            lease_owner="worker",
            task_attempt=1,
            expected_precondition_sha=SHA,
            result={"receipt": "ok"},
            event_kind="fixture.completed",
            event_payload={},
        )
    assert store.get_side_effect("effect")["state"] == "IN_PROGRESS"  # type: ignore[index]
    assert store.get_outbox_event("effect:completed") is None

    connection = sqlite3.connect(database)
    try:
        connection.execute("DROP TRIGGER reject_outbox")
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO tasks(
                run_id, task_id, status, attempt, max_attempts,
                idempotency_key, checkpoint_json, expected_precondition_sha,
                lease_owner, lease_expires_at, created_at, updated_at
            ) VALUES('missing', 'orphan', 'READY', 0, 1, 'orphan-key', '{}', ?,
                NULL, NULL, 1, 1)
            """,
            (SHA,),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(StateConflict, match="integrity check failed"):
        store.integrity_check()

    with database.open("r+b") as stream:
        stream.write(b"p13d-corrupt-database")
    with pytest.raises(sqlite3.DatabaseError):
        store.integrity_check()
