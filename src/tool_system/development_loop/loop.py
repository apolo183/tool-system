"""Pure bounded patch, validation, repair, and review execution.

The module operates on an in-memory repository mapping and injected fixture
callbacks.  It owns no filesystem, Git, process, network, provider, credential,
database, or remote-repository operation.  Returned state is canonical JSON and
can be persisted later by the P14G durable orchestration owner.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TREE_ID = re.compile(r"^[0-9a-f]{40,64}$")
_STATUSES = {"PASS", "BLOCK"}
_TERMINAL_PREDICATE = "all_frozen_acceptance_validation_and_reviews_pass"
_WORKER_TERMINAL_KEY = "subscription_worker_bridge_blocked"
_TERMINAL_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class DevelopmentLoopError(ValueError):
    """Fail-closed development-loop input or callback error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DevelopmentLoopLimits:
    max_cycles: int = 4
    max_worker_calls: int = 4
    max_patch_operations_per_cycle: int = 32
    max_total_duration_ms: int = 30_000
    max_total_cost_microunits: int = 20_000

    def validate(self) -> None:
        if any(not isinstance(value, int) or value <= 0 for value in asdict(self).values()):
            raise DevelopmentLoopError("INVALID_FINITE_BUDGETS")
        if self.max_worker_calls > self.max_cycles:
            raise DevelopmentLoopError("INVALID_FINITE_BUDGETS")


@dataclass(frozen=True)
class FrozenDevelopmentContract:
    task_digest: str
    baseline_tree: str
    allowed_scope: tuple[str, ...]
    acceptance_set: tuple[str, ...]
    validation_set: tuple[str, ...]
    terminal_predicate: str = _TERMINAL_PREDICATE

    def validate(self) -> None:
        if _SHA256.fullmatch(self.task_digest) is None:
            raise DevelopmentLoopError("INVALID_TASK_DIGEST")
        if _TREE_ID.fullmatch(self.baseline_tree) is None:
            raise DevelopmentLoopError("INVALID_BASELINE_TREE")
        _unique_strings(self.allowed_scope, "INVALID_ALLOWED_SCOPE", paths=True)
        _unique_strings(self.acceptance_set, "INVALID_ACCEPTANCE_SET")
        _unique_strings(self.validation_set, "INVALID_VALIDATION_SET")
        if self.terminal_predicate != _TERMINAL_PREDICATE:
            raise DevelopmentLoopError("INVALID_TERMINAL_PREDICATE")


Worker = Callable[[Mapping[str, object]], Mapping[str, object]]
Validator = Callable[[Mapping[str, str]], Mapping[str, object]]
Reviewer = Callable[[Mapping[str, object]], Mapping[str, object]]
CancellationRequested = Callable[[], bool]


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DevelopmentLoopError("NON_CANONICAL_VALUE") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise DevelopmentLoopError("INVALID_REPOSITORY_PATH")
    if value.startswith("/") or posixpath.normpath(value) != value:
        raise DevelopmentLoopError("INVALID_REPOSITORY_PATH")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise DevelopmentLoopError("INVALID_REPOSITORY_PATH")
    return value


def _unique_strings(
    values: Sequence[object], code: str, *, paths: bool = False
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or not values:
        raise DevelopmentLoopError(code)
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise DevelopmentLoopError(code)
        normalized.append(_path(value) if paths else value)
    if len(normalized) != len(set(normalized)):
        raise DevelopmentLoopError(code)
    return tuple(normalized)


def _files(value: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise DevelopmentLoopError("INVALID_VIRTUAL_REPOSITORY")
    result: dict[str, str] = {}
    for raw_path, content in value.items():
        path = _path(raw_path)
        if not isinstance(content, str):
            raise DevelopmentLoopError("INVALID_VIRTUAL_REPOSITORY")
        result[path] = content
    return dict(sorted(result.items()))


def _candidate_tree(files: Mapping[str, str]) -> str:
    return _digest({path: hashlib.sha256(content.encode()).hexdigest() for path, content in sorted(files.items())})


def _apply_patch(
    files: Mapping[str, str],
    patch: Mapping[str, object],
    *,
    allowed_scope: set[str],
    max_operations: int,
) -> tuple[dict[str, str], dict[str, int]]:
    if not isinstance(patch, Mapping):
        raise DevelopmentLoopError("INVALID_WORKER_OUTPUT")
    forbidden = set(patch) - {"operations", "usage", "material_evidence"}
    if forbidden:
        raise DevelopmentLoopError("WORKER_AUTHORITY_EXPANSION")
    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        raise DevelopmentLoopError("INVALID_STRUCTURED_PATCH")
    if len(operations) > max_operations:
        raise DevelopmentLoopError("PATCH_OPERATION_LIMIT_EXCEEDED")
    usage = patch.get("usage", {})
    if not isinstance(usage, Mapping):
        raise DevelopmentLoopError("INVALID_WORKER_USAGE")
    duration = usage.get("duration_ms", 0)
    cost = usage.get("cost_microunits", 0)
    if any(not isinstance(item, int) or item < 0 for item in (duration, cost)):
        raise DevelopmentLoopError("INVALID_WORKER_USAGE")
    result = dict(files)
    seen: set[str] = set()
    for operation in operations:
        if not isinstance(operation, Mapping):
            raise DevelopmentLoopError("INVALID_STRUCTURED_PATCH")
        op = operation.get("op")
        path = _path(operation.get("path"))
        if path not in allowed_scope:
            raise DevelopmentLoopError("PATCH_OUTSIDE_FROZEN_SCOPE")
        if path in seen:
            raise DevelopmentLoopError("DUPLICATE_PATCH_PATH")
        seen.add(path)
        current = result.get(path)
        expected = operation.get("expected_sha256")
        if op == "add":
            if current is not None or expected is not None or not isinstance(operation.get("content"), str):
                raise DevelopmentLoopError("PATCH_PRECONDITION_FAILED")
            result[path] = str(operation["content"])
        elif op in {"replace", "delete"}:
            if current is None or not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
                raise DevelopmentLoopError("PATCH_PRECONDITION_FAILED")
            if hashlib.sha256(current.encode()).hexdigest() != expected:
                raise DevelopmentLoopError("PATCH_PRECONDITION_FAILED")
            if op == "replace":
                if not isinstance(operation.get("content"), str):
                    raise DevelopmentLoopError("INVALID_STRUCTURED_PATCH")
                result[path] = str(operation["content"])
            else:
                if "content" in operation:
                    raise DevelopmentLoopError("INVALID_STRUCTURED_PATCH")
                del result[path]
        else:
            raise DevelopmentLoopError("INVALID_PATCH_OPERATION")
    return dict(sorted(result.items())), {"duration_ms": duration, "cost_microunits": cost}


def _worker_terminal_code(patch: object) -> str | None:
    if not isinstance(patch, Mapping):
        raise DevelopmentLoopError("INVALID_WORKER_OUTPUT")
    if _WORKER_TERMINAL_KEY not in patch:
        return None
    if set(patch) != {_WORKER_TERMINAL_KEY}:
        raise DevelopmentLoopError("INVALID_WORKER_TERMINAL_RESULT")
    terminal = patch[_WORKER_TERMINAL_KEY]
    if not isinstance(terminal, Mapping) or set(terminal) != {"terminal_code"}:
        raise DevelopmentLoopError("INVALID_WORKER_TERMINAL_RESULT")
    code = terminal["terminal_code"]
    if not isinstance(code, str) or _TERMINAL_CODE.fullmatch(code) is None:
        raise DevelopmentLoopError("INVALID_WORKER_TERMINAL_RESULT")
    return code


def _validation(
    result: Mapping[str, object], contract: FrozenDevelopmentContract
) -> tuple[dict[str, dict[str, object]], list[str], list[str]]:
    if not isinstance(result, Mapping):
        raise DevelopmentLoopError("INVALID_VALIDATION_RESULT")
    raw_results = result.get("validation_results")
    satisfied = result.get("satisfied_acceptance_items")
    if not isinstance(raw_results, Mapping) or set(raw_results) != set(contract.validation_set):
        raise DevelopmentLoopError("VALIDATION_SET_DRIFT")
    if not isinstance(satisfied, list) or not all(isinstance(item, str) for item in satisfied):
        raise DevelopmentLoopError("INVALID_ACCEPTANCE_RESULT")
    if not set(satisfied) <= set(contract.acceptance_set):
        raise DevelopmentLoopError("ACCEPTANCE_SET_DRIFT")
    normalized: dict[str, dict[str, object]] = {}
    blockers: list[str] = []
    for validation_id in sorted(raw_results):
        record = raw_results[validation_id]
        if not isinstance(record, Mapping) or record.get("status") not in _STATUSES:
            raise DevelopmentLoopError("INVALID_VALIDATION_RESULT")
        diagnostic = record.get("diagnostic")
        if diagnostic is not None and not isinstance(diagnostic, str):
            raise DevelopmentLoopError("INVALID_VALIDATION_RESULT")
        normalized[validation_id] = {"status": record["status"], "diagnostic": diagnostic}
        if record["status"] != "PASS":
            blockers.append(f"validation:{validation_id}")
    missing = sorted(set(contract.acceptance_set) - set(satisfied))
    blockers.extend(f"acceptance:{item}" for item in missing)
    return normalized, sorted(set(satisfied)), blockers


def _review(
    reviewer: Reviewer,
    review_input: Mapping[str, object],
    acceptance_set: set[str],
    label: str,
) -> tuple[dict[str, object], list[str]]:
    raw = reviewer(review_input)
    if not isinstance(raw, Mapping):
        raise DevelopmentLoopError("INVALID_REVIEW_RESULT")
    violations = raw.get("violated_acceptance_items", [])
    suggestions = raw.get("suggestions", [])
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        raise DevelopmentLoopError("INVALID_REVIEW_RESULT")
    if not set(violations) <= acceptance_set:
        raise DevelopmentLoopError("REVIEW_ACCEPTANCE_EXPANSION")
    if not isinstance(suggestions, list) or not all(isinstance(item, str) for item in suggestions):
        raise DevelopmentLoopError("INVALID_REVIEW_RESULT")
    record = {
        "reviewer": label,
        "violated_acceptance_items": sorted(set(violations)),
        "suggestions": list(suggestions),
        "suggestions_are_non_blocking": True,
    }
    return record, [f"review:{label}:{item}" for item in sorted(set(violations))]


def _fingerprint(
    contract: FrozenDevelopmentContract,
    candidate_tree: str,
    blockers: Sequence[str],
    validation_results: Mapping[str, object],
) -> str:
    return _digest(
        {
            "task_digest": contract.task_digest,
            "candidate_tree": candidate_tree,
            "acceptance_digest": _digest(list(contract.acceptance_set)),
            "blocker_set": sorted(blockers),
            "validation_results": validation_results,
        }
    )


def _blocked(code: str, contract: FrozenDevelopmentContract | None = None) -> dict[str, object]:
    return {
        "status": "BLOCK",
        "terminal_code": code,
        "frozen_contract": asdict(contract) if contract is not None else None,
        "candidate_files": None,
        "candidate_tree": None,
        "terminal_candidate_sealed": False,
        "cycles": [],
        "worker_call_count": 0,
        "writes_filesystem": False,
        "calls_git": False,
        "calls_provider": False,
        "reads_credentials": False,
        "writes_target_repo": False,
    }


def _is_cancelled(callback: CancellationRequested | None) -> bool:
    if callback is None:
        return False
    if not callable(callback):
        raise DevelopmentLoopError("INVALID_CANCELLATION_SIGNAL")
    try:
        result = callback()
    except Exception as exc:
        raise DevelopmentLoopError("INVALID_CANCELLATION_SIGNAL") from exc
    if type(result) is not bool:
        raise DevelopmentLoopError("INVALID_CANCELLATION_SIGNAL")
    return result


def run_development_loop(
    *,
    contract: FrozenDevelopmentContract,
    baseline_files: Mapping[str, object],
    worker: Worker,
    validator: Validator,
    code_reviewer: Reviewer,
    contract_reviewer: Reviewer,
    limits: DevelopmentLoopLimits | None = None,
    resume_state: Mapping[str, object] | None = None,
    initial_worker_call_count: int = 0,
    cancellation_requested: CancellationRequested | None = None,
) -> dict[str, object]:
    """Run a finite, deterministic fixture development loop."""

    limits = limits or DevelopmentLoopLimits()
    try:
        contract.validate()
        limits.validate()
        files = _files(baseline_files)
        if (
            type(initial_worker_call_count) is not int
            or initial_worker_call_count < 0
        ):
            raise DevelopmentLoopError("INVALID_INITIAL_WORKER_CALL_COUNT")
        if cancellation_requested is not None and not callable(
            cancellation_requested
        ):
            raise DevelopmentLoopError("INVALID_CANCELLATION_SIGNAL")
    except DevelopmentLoopError as exc:
        return _blocked(exc.code, contract)
    allowed_scope = set(contract.allowed_scope)
    acceptance_set = set(contract.acceptance_set)
    cycles: list[dict[str, object]] = []
    fingerprints: set[str] = set()
    total_duration = 0
    total_cost = 0
    worker_calls = 0
    no_progress_count = 0
    previous_blockers: set[str] | None = None
    previous_satisfied: set[str] = set()
    previous_validation_digest: str | None = None
    if resume_state is not None:
        if not isinstance(resume_state, Mapping):
            return _blocked("INVALID_RESUME_STATE", contract)
        if resume_state.get("task_digest") != contract.task_digest or resume_state.get("baseline_tree") != contract.baseline_tree:
            return _blocked("RESUME_IDENTITY_MISMATCH", contract)
        if resume_state.get("status") == "PASS" and resume_state.get("terminal_candidate_sealed") is True:
            return dict(resume_state)
        try:
            files = _files(resume_state.get("candidate_files", {}))
            cycles = list(resume_state.get("cycles", []))
            fingerprints = {str(item["recurrence_fingerprint"]) for item in cycles if isinstance(item, Mapping)}
            total_duration = int(resume_state.get("total_duration_ms", 0))
            total_cost = int(resume_state.get("total_cost_microunits", 0))
            worker_calls = int(resume_state.get("worker_call_count", 0))
            no_progress_count = int(resume_state.get("no_progress_count", 0))
            if cycles:
                last_cycle = cycles[-1]
                if not isinstance(last_cycle, Mapping):
                    raise DevelopmentLoopError("INVALID_RESUME_STATE")
                previous_blockers = set(last_cycle.get("blocker_set", []))
                previous_satisfied = set(
                    last_cycle.get("satisfied_acceptance_items", [])
                )
                previous_validation_digest = _digest(
                    last_cycle.get("validation_results", {})
                )
        except (TypeError, ValueError, DevelopmentLoopError):
            return _blocked("INVALID_RESUME_STATE", contract)
    worker_calls = max(worker_calls, initial_worker_call_count)
    for attempt in range(len(cycles) + 1, limits.max_cycles + 1):
        try:
            if _is_cancelled(cancellation_requested):
                terminal_code = "CANCELLED_BY_CALLER"
                break
        except DevelopmentLoopError as exc:
            terminal_code = exc.code
            break
        if worker_calls >= limits.max_worker_calls:
            terminal_code = "WORKER_CALL_BUDGET_EXHAUSTED"
            break
        request = {
            "task_digest": contract.task_digest,
            "baseline_tree": contract.baseline_tree,
            "candidate_tree": _candidate_tree(files),
            "candidate_files": dict(files),
            "allowed_scope": list(contract.allowed_scope),
            "acceptance_set": list(contract.acceptance_set),
            "validation_set": list(contract.validation_set),
            "terminal_predicate": contract.terminal_predicate,
            "attempt_number": attempt,
            "diagnostics": cycles[-1]["validation_results"] if cycles else {},
            "blockers": cycles[-1]["blocker_set"] if cycles else [],
        }
        try:
            worker_calls += 1
            patch = worker(request)
            terminal_code = _worker_terminal_code(patch)
            if terminal_code is not None:
                raise DevelopmentLoopError(terminal_code)
            if _is_cancelled(cancellation_requested):
                terminal_code = "CANCELLED_BY_CALLER"
                break
            candidate, usage = _apply_patch(
                files,
                patch,
                allowed_scope=allowed_scope,
                max_operations=limits.max_patch_operations_per_cycle,
            )
            total_duration += usage["duration_ms"]
            total_cost += usage["cost_microunits"]
            if total_duration > limits.max_total_duration_ms:
                terminal_code = "TIME_BUDGET_EXHAUSTED"
                break
            if total_cost > limits.max_total_cost_microunits:
                terminal_code = "COST_BUDGET_EXHAUSTED"
                break
            validation_results, satisfied, blockers = _validation(validator(candidate), contract)
            reviews: list[dict[str, object]] = []
            if not blockers:
                review_input = {
                    "task_digest": contract.task_digest,
                    "candidate_tree": _candidate_tree(candidate),
                    "candidate_files": candidate,
                    "acceptance_set": list(contract.acceptance_set),
                    "validation_results": validation_results,
                }
                for label, reviewer in (("code", code_reviewer), ("contract", contract_reviewer)):
                    review_record, review_blockers = _review(reviewer, review_input, acceptance_set, label)
                    reviews.append(review_record)
                    blockers.extend(review_blockers)
        except DevelopmentLoopError as exc:
            return {
                **_blocked(exc.code, contract),
                "candidate_files": dict(files),
                "candidate_tree": _candidate_tree(files),
                "worker_call_count": worker_calls,
                "total_duration_ms": total_duration,
                "total_cost_microunits": total_cost,
            }
        candidate_tree = _candidate_tree(candidate)
        fingerprint = _fingerprint(contract, candidate_tree, blockers, validation_results)
        validation_digest = _digest(validation_results)
        blocker_set = set(blockers)
        satisfied_set = set(satisfied)
        progress = (
            previous_blockers is None
            or blocker_set < previous_blockers
            or satisfied_set > previous_satisfied
            or validation_digest != previous_validation_digest
        )
        cycle = {
            "attempt_number": attempt,
            "candidate_tree": candidate_tree,
            "acceptance_digest": _digest(list(contract.acceptance_set)),
            "blocker_set": sorted(blockers),
            "satisfied_acceptance_items": satisfied,
            "validation_results": validation_results,
            "reviews": reviews,
            "material_evidence": patch.get("material_evidence"),
            "recurrence_fingerprint": fingerprint,
            "progress": progress,
        }
        cycles.append(cycle)
        files = candidate
        if not blockers:
            return {
                "status": "PASS",
                "terminal_code": "TERMINAL_PREDICATE_SATISFIED",
                "frozen_contract": asdict(contract),
                "task_digest": contract.task_digest,
                "baseline_tree": contract.baseline_tree,
                "candidate_files": files,
                "candidate_tree": candidate_tree,
                "terminal_candidate_sealed": True,
                "cycles": cycles,
                "worker_call_count": worker_calls,
                "total_duration_ms": total_duration,
                "total_cost_microunits": total_cost,
                "no_progress_count": no_progress_count,
                "writes_filesystem": False,
                "calls_git": False,
                "calls_provider": False,
                "reads_credentials": False,
                "writes_target_repo": False,
            }
        if fingerprint in fingerprints:
            terminal_code = "STOPPED_NO_PROGRESS_REPEATED_FINGERPRINT"
            break
        fingerprints.add(fingerprint)
        no_progress_count = 0 if progress else no_progress_count + 1
        if no_progress_count >= 2:
            terminal_code = "STOPPED_NO_PROGRESS_TWO_CYCLES"
            break
        previous_blockers = blocker_set
        previous_satisfied = satisfied_set
        previous_validation_digest = validation_digest
    else:
        terminal_code = "CYCLE_BUDGET_EXHAUSTED"
    return {
        "status": "BLOCK",
        "terminal_code": terminal_code,
        "frozen_contract": asdict(contract),
        "task_digest": contract.task_digest,
        "baseline_tree": contract.baseline_tree,
        "candidate_files": files,
        "candidate_tree": _candidate_tree(files),
        "terminal_candidate_sealed": False,
        "cycles": cycles,
        "worker_call_count": worker_calls,
        "total_duration_ms": total_duration,
        "total_cost_microunits": total_cost,
        "no_progress_count": no_progress_count,
        "writes_filesystem": False,
        "calls_git": False,
        "calls_provider": False,
        "reads_credentials": False,
        "writes_target_repo": False,
    }


def evaluate_sealed_candidate_reopen(
    sealed_result: Mapping[str, object],
    evidence: Mapping[str, object],
    *,
    explicit_user_authorized: bool = False,
) -> dict[str, object]:
    """Apply evidence non-reopening semantics to a sealed result."""

    if sealed_result.get("status") != "PASS" or sealed_result.get("terminal_candidate_sealed") is not True:
        return {"status": "BLOCK", "reopen": False, "reason": "CANDIDATE_NOT_SEALED"}
    contract = sealed_result.get("frozen_contract")
    if not isinstance(contract, Mapping):
        return {"status": "BLOCK", "reopen": False, "reason": "MISSING_FROZEN_CONTRACT"}
    if explicit_user_authorized:
        return {"status": "PASS", "reopen": True, "reason": "EXPLICIT_USER_AUTHORIZATION"}
    if not isinstance(evidence, Mapping):
        return {"status": "PASS", "reopen": False, "reason": "NON_MATERIAL_EVIDENCE"}
    violations = evidence.get("violated_acceptance_items", [])
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        return {"status": "BLOCK", "reopen": False, "reason": "INVALID_EVIDENCE"}
    acceptance = set(contract.get("acceptance_set", []))
    if evidence.get("material_evidence") is True and violations and set(violations) <= acceptance:
        return {"status": "PASS", "reopen": True, "reason": "ORIGINAL_ACCEPTANCE_VIOLATION"}
    return {"status": "PASS", "reopen": False, "reason": "EVIDENCE_CANNOT_REOPEN"}
