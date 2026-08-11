from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_local_git_orchestrator import (
    _contract as _local_contract,
)
from test_local_git_orchestrator import (
    _git,
)
from test_local_git_orchestrator import (
    _review as _local_review,
)
from test_local_git_orchestrator import (
    _validator as _local_validator,
)
from test_local_git_orchestrator import (
    _worker as _local_worker,
)

from tool_system.development_loop import DevelopmentLoopLimits
from tool_system.local_git import LocalGitIdentity, run_durable_local_git
from tool_system.orchestrator import DurableOrchestratorStore, StateConflict

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class LocalIdempotentSink:
    """A persistent fixture sink that applies each durable key once."""

    def __init__(self, receipt_path: Path) -> None:
        self.receipt_path = receipt_path
        self.calls = 0

    def __call__(self, event: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        key = str(event["idempotency_key"])
        applied = (
            json.loads(self.receipt_path.read_text(encoding="utf-8"))
            if self.receipt_path.exists()
            else []
        )
        already_applied = key in applied
        if not already_applied:
            applied.append(key)
            self.receipt_path.write_text(
                json.dumps(applied, sort_keys=True), encoding="utf-8"
            )
        return {
            "idempotency_key": key,
            "already_applied": already_applied,
            "applied_count": len(applied),
        }

    def applied(self) -> list[str]:
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))


def _local_fixture(
    tmp_path: Path,
    *,
    clock: Clock,
) -> tuple[Path, DurableOrchestratorStore, LocalGitIdentity]:
    root = tmp_path / "fixture"
    root.mkdir()
    _git(root, "init", "-b", "main")
    (root / "app.txt").write_text("old\n", encoding="utf-8")
    _git(root, "add", "app.txt")
    _git(
        root,
        "-c",
        "user.name=fixture",
        "-c",
        "user.email=f@x.invalid",
        "commit",
        "-m",
        "base",
    )
    database_parent = tmp_path / "local-state"
    database_parent.mkdir(mode=0o700)
    store = DurableOrchestratorStore(
        database_parent / "p14g.sqlite3",
        forbidden_roots=(root,),
        clock=clock,
    )
    identity = LocalGitIdentity(
        expected_head_sha=_git(root, "rev-parse", "HEAD"),
        expected_tree_sha=_git(root, "rev-parse", "HEAD^{tree}"),
        branch_name="agent/p14g-fixture-v1",
        commit_message="P14G fixture change",
    )
    return root, store, identity


def _store(database: Path, clock: Clock) -> DurableOrchestratorStore:
    return DurableOrchestratorStore(
        database,
        forbidden_roots=(ROOT,),
        clock=clock,
    )


def _active_task(
    database: Path, clock: Clock, *, max_attempts: int = 3
) -> DurableOrchestratorStore:
    store = _store(database, clock)
    store.create_run("run", blueprint_ref="blueprint", manifest_ref="manifest")
    store.add_task(
        "run",
        "task",
        idempotency_key="task-key",
        expected_precondition_sha=SHA,
        max_attempts=max_attempts,
        checkpoint={"step": 0},
    )
    store.claim_task("run", "task", lease_owner="worker-1", lease_seconds=10)
    return store


def _completed_effect(store: DurableOrchestratorStore) -> None:
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    store.begin_side_effect("effect-1", lease_owner="worker-1", task_attempt=1)
    store.complete_side_effect(
        "effect-1",
        lease_owner="worker-1",
        task_attempt=1,
        expected_precondition_sha=SHA,
        result={"receipt": "complete"},
        event_kind="fixture.completed",
        event_payload={"effect_id": "effect-1"},
    )


def test_reopen_preserves_run_task_attempt_checkpoint_and_live_lease(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    first = _active_task(database, clock)
    first.checkpoint_task(
        "run",
        "task",
        lease_owner="worker-1",
        attempt=1,
        checkpoint={"step": 4, "cursor": "fixture-17"},
    )

    reopened = _store(database, clock)

    assert reopened.get_run("run")["status"] == "ACTIVE"  # type: ignore[index]
    task = reopened.get_task("run", "task")
    assert task is not None
    assert task["status"] == "RUNNING"
    assert task["attempt"] == 1
    assert task["checkpoint"] == {"step": 4, "cursor": "fixture-17"}
    assert task["lease_owner"] == "worker-1"
    assert task["lease_expires_at"] == 1_010.0


def test_expired_lease_recovers_and_reclaims_with_next_attempt(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    _active_task(database, clock)
    clock.advance(11)

    reopened = _store(database, clock)
    recovered = reopened.recover_expired_leases()
    reclaimed = reopened.claim_task(
        "run", "task", lease_owner="worker-2", lease_seconds=10
    )

    assert recovered[0]["status"] == "READY"
    assert recovered[0]["attempt"] == 1
    assert reclaimed["status"] == "RUNNING"
    assert reclaimed["attempt"] == 2
    assert reclaimed["lease_owner"] == "worker-2"


def test_retry_exhaustion_is_terminal_across_reopen(tmp_path: Path) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock, max_attempts=2)
    first_failure = store.fail_task(
        "run", "task", lease_owner="worker-1", attempt=1, retryable=True
    )
    assert first_failure["status"] == "READY"
    store.claim_task("run", "task", lease_owner="worker-2", lease_seconds=10)
    second_failure = store.fail_task(
        "run", "task", lease_owner="worker-2", attempt=2, retryable=True
    )

    reopened = _store(database, clock)

    assert second_failure["status"] == "FAILED"
    assert reopened.get_task("run", "task")["status"] == "FAILED"  # type: ignore[index]
    with pytest.raises(StateConflict, match="terminal task"):
        reopened.claim_task(
            "run", "task", lease_owner="worker-3", lease_seconds=10
        )


def test_duplicate_effect_registration_is_stable_and_mismatch_blocks_after_reopen(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    first = store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    reopened = _store(database, clock)
    same = reopened.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )

    assert same == first
    with pytest.raises(StateConflict, match="different side-effect content"):
        reopened.plan_side_effect(
            "run",
            "task",
            effect_id="effect-1",
            effect_kind="fixture_write",
            action="different_action",
            resource_scope="local_fixture",
            idempotency_key="effect-key",
            expected_precondition_sha=SHA,
            payload={"value": 1},
            lease_owner="worker-1",
            task_attempt=1,
        )
    with pytest.raises(StateConflict, match="precondition SHA"):
        reopened.plan_side_effect(
            "run",
            "task",
            effect_id="effect-1",
            effect_kind="fixture_write",
            action="write_fixture_receipt",
            resource_scope="local_fixture",
            idempotency_key="effect-key",
            expected_precondition_sha="b" * 40,
            payload={"value": 1},
            lease_owner="worker-1",
            task_attempt=1,
        )


def test_completion_and_pending_outbox_survive_reopen_without_effect_reexecution(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    _completed_effect(store)

    reopened = _store(database, clock)

    assert reopened.get_side_effect("effect-1")["state"] == "COMPLETED"  # type: ignore[index]
    assert reopened.get_outbox_event("effect-1:completed")["state"] == "PENDING"  # type: ignore[index]
    replay = reopened.begin_side_effect(
        "effect-1", lease_owner="worker-1", task_attempt=1
    )
    assert replay["already_completed"] is True
    assert replay["attempt"] == 1


def test_publisher_crash_reconciles_through_idempotent_local_sink_once(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    _completed_effect(store)
    sink = LocalIdempotentSink(tmp_path / "sink_receipts.json")

    claimed = store.claim_outbox_event(
        "effect-1:completed", lease_owner="publisher-1", lease_seconds=5
    )
    first_receipt = sink(claimed)
    assert first_receipt["already_applied"] is False
    # Simulated crash: deliberately omit mark_outbox_published.
    clock.advance(6)

    reopened = _store(database, clock)
    assert reopened.get_outbox_event("effect-1:completed")["state"] == "DELIVERING"  # type: ignore[index]
    recovered = reopened.recover_expired_outbox_leases()
    replay = reopened.reconcile_outbox(sink, lease_owner="publisher-2")
    no_repeat = reopened.reconcile_outbox(sink, lease_owner="publisher-2")

    assert recovered[0]["state"] == "PENDING"
    assert replay[0]["status"] == "PUBLISHED"
    assert replay[0]["receipt"]["already_applied"] is True  # type: ignore[index]
    assert reopened.get_outbox_event("effect-1:completed")["attempt"] == 2  # type: ignore[index]
    assert sink.calls == 2
    assert sink.applied() == ["effect-key:completed"]
    assert no_repeat == []


def test_ambiguous_in_progress_effect_remains_fail_closed_after_reopen(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    store.begin_side_effect("effect-1", lease_owner="worker-1", task_attempt=1)

    reopened = _store(database, clock)

    with pytest.raises(StateConflict, match="reconcile by idempotency key"):
        reopened.begin_side_effect(
            "effect-1", lease_owner="worker-1", task_attempt=1
        )


def test_controlled_fake_clock_renewal_covers_all_local_stages(
    tmp_path: Path,
) -> None:
    clock = Clock()
    root, store, identity = _local_fixture(tmp_path, clock=clock)

    def advancing_worker(request: object) -> dict[str, object]:
        clock.advance(6)
        return _local_worker(request)

    def advancing_validator(files: object) -> dict[str, object]:
        clock.advance(6)
        return _local_validator(files)

    def advancing_review(review: object) -> dict[str, object]:
        clock.advance(6)
        return _local_review(review)

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="renewed-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_local_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=advancing_worker,
        validator=advancing_validator,
        code_reviewer=advancing_review,
        contract_reviewer=advancing_review,
        lease_seconds=10,
    )

    assert result["status"] == "PASS"
    assert result["worker_call_count"] == 1
    assert store.worker_calls("renewed-run", "local-change")[0]["state"] == (
        "COMPLETED"
    )


def test_crash_before_worker_return_consumes_total_budget_across_retry(
    tmp_path: Path,
) -> None:
    clock = Clock()
    root, store, identity = _local_fixture(tmp_path, clock=clock)

    class Crash(RuntimeError):
        pass

    def crashing_worker(_: object) -> dict[str, object]:
        calls = store.worker_calls("crash-run", "local-change")
        assert [(call["ordinal"], call["state"]) for call in calls] == [
            (1, "STARTED")
        ]
        raise Crash("simulated worker-process crash")

    try:
        run_durable_local_git(
            repository_root=root,
            store=store,
            run_id="crash-run",
            task_id="local-change",
            lease_owner="worker-before-crash",
            identity=identity,
            contract=_local_contract(),
            baseline_files={"app.txt": "old\n"},
            worker=crashing_worker,
            validator=_local_validator,
            code_reviewer=_local_review,
            contract_reviewer=_local_review,
            limits=DevelopmentLoopLimits(max_cycles=1, max_worker_calls=1),
            lease_seconds=10,
        )
    except Crash:
        pass
    else:
        raise AssertionError("simulated crash did not escape the process boundary")

    clock.advance(11)
    resumed_worker_calls = 0

    def forbidden_retry_worker(_: object) -> dict[str, object]:
        nonlocal resumed_worker_calls
        resumed_worker_calls += 1
        raise AssertionError("consumed total call budget must block retry dispatch")

    resumed = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="crash-run",
        task_id="local-change",
        lease_owner="worker-after-crash",
        identity=identity,
        contract=_local_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=forbidden_retry_worker,
        validator=_local_validator,
        code_reviewer=_local_review,
        contract_reviewer=_local_review,
        limits=DevelopmentLoopLimits(max_cycles=1, max_worker_calls=1),
        lease_seconds=10,
    )

    assert resumed["status"] == "BLOCK"
    assert resumed["terminal_code"] == "WORKER_CALL_BUDGET_EXHAUSTED"
    assert resumed["worker_call_count"] == 1
    assert resumed_worker_calls == 0
    assert store.worker_call_count("crash-run", "local-change") == 1


def test_expired_lease_preserves_observed_worker_timeout_and_call_count(
    tmp_path: Path,
) -> None:
    clock = Clock()
    root, store, identity = _local_fixture(tmp_path, clock=clock)

    def timed_out_worker(_: object) -> dict[str, object]:
        clock.advance(11)
        return {
            "subscription_worker_bridge_blocked": {
                "terminal_code": "SUBSCRIPTION_WORKER_TIMEOUT"
            }
        }

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="timeout-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_local_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=timed_out_worker,
        validator=_local_validator,
        code_reviewer=_local_review,
        contract_reviewer=_local_review,
        lease_seconds=10,
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "SUBSCRIPTION_WORKER_TIMEOUT"
    assert result["worker_call_count"] == 1
    assert store.worker_calls("timeout-run", "local-change")[0]["state"] == (
        "STARTED"
    )


def test_unsafe_worker_terminal_detail_is_never_persisted_or_propagated(
    tmp_path: Path,
) -> None:
    clock = Clock()
    root, store, identity = _local_fixture(tmp_path, clock=clock)

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="unsafe-terminal-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_local_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=lambda _: {
            "subscription_worker_bridge_blocked": {
                "terminal_code": "raw timeout detail"
            }
        },
        validator=lambda _: (_ for _ in ()).throw(
            AssertionError("invalid worker result must not enter validation")
        ),
        code_reviewer=_local_review,
        contract_reviewer=_local_review,
        lease_seconds=10,
    )

    durable_call = store.worker_calls("unsafe-terminal-run", "local-change")[0]
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "INVALID_WORKER_TERMINAL_RESULT"
    assert result["worker_call_count"] == 1
    assert durable_call["state"] == "BLOCKED"
    assert durable_call["terminal_code"] == "INVALID_WORKER_TERMINAL_RESULT"
    assert "raw timeout detail" not in str(durable_call)
