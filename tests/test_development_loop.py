from __future__ import annotations

import hashlib

from tool_system.development_loop import (
    DevelopmentLoopLimits,
    FrozenDevelopmentContract,
    evaluate_sealed_candidate_reopen,
    run_development_loop,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _contract() -> FrozenDevelopmentContract:
    return FrozenDevelopmentContract(
        task_digest="a" * 64,
        baseline_tree="b" * 40,
        allowed_scope=("src/app.py", "tests/test_app.py"),
        acceptance_set=("implementation-correct", "tests-pass"),
        validation_set=("pytest",),
    )


def _pass_validation(files: dict[str, str]) -> dict[str, object]:
    passed = "return 2" in files.get("src/app.py", "")
    return {
        "validation_results": {
            "pytest": {"status": "PASS" if passed else "BLOCK", "diagnostic": None if passed else "expected 2"}
        },
        "satisfied_acceptance_items": ["implementation-correct", "tests-pass"] if passed else [],
    }


def _clean_review(_: dict[str, object]) -> dict[str, object]:
    return {"violated_acceptance_items": [], "suggestions": ["optional wording"]}


def test_patch_validate_and_independent_review_seals_candidate() -> None:
    worker_calls: list[dict[str, object]] = []

    def worker(request: dict[str, object]) -> dict[str, object]:
        worker_calls.append(request)
        return {
            "operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}],
            "usage": {"duration_ms": 5, "cost_microunits": 7},
            "material_evidence": "fixture patch",
        }

    result = run_development_loop(
        contract=_contract(),
        baseline_files={"src/app.py": "return 1\n", "tests/test_app.py": "assert app() == 2\n"},
        worker=worker,
        validator=_pass_validation,
        code_reviewer=_clean_review,
        contract_reviewer=_clean_review,
    )

    assert result["status"] == "PASS"
    assert result["terminal_candidate_sealed"] is True
    assert result["candidate_files"]["src/app.py"] == "return 2\n"
    assert result["worker_call_count"] == 1
    assert result["cycles"][0]["reviews"][0]["suggestions_are_non_blocking"] is True
    assert all(result[key] is False for key in ("writes_filesystem", "calls_git", "calls_provider", "reads_credentials", "writes_target_repo"))


def test_failed_validation_is_diagnosed_and_repaired_within_budget() -> None:
    calls = 0

    def worker(request: dict[str, object]) -> dict[str, object]:
        nonlocal calls
        calls += 1
        current = "return 1\n" if calls == 1 else "return 0\n"
        target = "return 0\n" if calls == 1 else "return 2\n"
        if calls == 2:
            assert request["blockers"] == ["acceptance:implementation-correct", "acceptance:tests-pass", "validation:pytest"]
        return {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha(current), "content": target}], "usage": {"duration_ms": 1, "cost_microunits": 1}}

    result = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"}, worker=worker,
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
    )
    assert result["status"] == "PASS"
    assert result["worker_call_count"] == 2
    assert result["cycles"][0]["validation_results"]["pytest"]["status"] == "BLOCK"


def test_out_of_scope_patch_and_sha_mismatch_fail_atomically() -> None:
    for operation, expected_code in (
        ({"op": "add", "path": "README.md", "expected_sha256": None, "content": "x"}, "PATCH_OUTSIDE_FROZEN_SCOPE"),
        ({"op": "replace", "path": "src/app.py", "expected_sha256": "0" * 64, "content": "x"}, "PATCH_PRECONDITION_FAILED"),
    ):
        result = run_development_loop(
            contract=_contract(), baseline_files={"src/app.py": "return 1\n"},
            worker=lambda _: {"operations": [operation]}, validator=_pass_validation,
            code_reviewer=_clean_review, contract_reviewer=_clean_review,
        )
        assert result["status"] == "BLOCK"
        assert result["terminal_code"] == expected_code
        assert result["candidate_files"] == {"src/app.py": "return 1\n"}


def test_repeated_fingerprint_stops_without_attempt_number_escape() -> None:
    def worker(_: dict[str, object]) -> dict[str, object]:
        return {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 1\n"}]}

    result = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"}, worker=worker,
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
    )
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "STOPPED_NO_PROGRESS_REPEATED_FINGERPRINT"
    assert len(result["cycles"]) == 2
    assert result["cycles"][0]["recurrence_fingerprint"] == result["cycles"][1]["recurrence_fingerprint"]
    assert result["cycles"][0]["attempt_number"] != result["cycles"][1]["attempt_number"]


def test_two_distinct_no_progress_cycles_stop_even_without_recurrence() -> None:
    contents = iter(("return 0\n", "return -1\n", "return -2\n"))

    def worker(request: dict[str, object]) -> dict[str, object]:
        current = request["candidate_tree"]
        del current
        before = worker.current
        after = next(contents)
        worker.current = after
        return {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/app.py",
                    "expected_sha256": _sha(before),
                    "content": after,
                }
            ]
        }

    worker.current = "return 1\n"
    result = run_development_loop(
        contract=_contract(),
        baseline_files={"src/app.py": "return 1\n"},
        worker=worker,
        validator=_pass_validation,
        code_reviewer=_clean_review,
        contract_reviewer=_clean_review,
    )
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "STOPPED_NO_PROGRESS_TWO_CYCLES"
    assert len({cycle["recurrence_fingerprint"] for cycle in result["cycles"]}) == 3
    assert [cycle["progress"] for cycle in result["cycles"]] == [True, False, False]


def test_unsealed_resume_preserves_progress_history() -> None:
    first = run_development_loop(
        contract=_contract(),
        baseline_files={"src/app.py": "return 1\n"},
        worker=lambda _: {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/app.py",
                    "expected_sha256": _sha("return 1\n"),
                    "content": "return 0\n",
                }
            ]
        },
        validator=_pass_validation,
        code_reviewer=_clean_review,
        contract_reviewer=_clean_review,
        limits=DevelopmentLoopLimits(max_cycles=1, max_worker_calls=1),
    )

    contents = iter(("return -1\n", "return -2\n"))

    def worker(_: dict[str, object]) -> dict[str, object]:
        before = worker.current
        after = next(contents)
        worker.current = after
        return {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/app.py",
                    "expected_sha256": _sha(before),
                    "content": after,
                }
            ]
        }

    worker.current = "return 0\n"
    resumed = run_development_loop(
        contract=_contract(),
        baseline_files={"src/app.py": "return 1\n"},
        worker=worker,
        validator=_pass_validation,
        code_reviewer=_clean_review,
        contract_reviewer=_clean_review,
        limits=DevelopmentLoopLimits(max_cycles=3, max_worker_calls=3),
        resume_state=first,
    )
    assert resumed["terminal_code"] == "STOPPED_NO_PROGRESS_TWO_CYCLES"
    assert [cycle["progress"] for cycle in resumed["cycles"]] == [True, False, False]


def test_review_can_block_only_frozen_acceptance_and_cannot_add_obligation() -> None:
    violation = lambda _: {"violated_acceptance_items": ["tests-pass"], "suggestions": []}
    result = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"},
        worker=lambda _: {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}]},
        validator=_pass_validation, code_reviewer=violation, contract_reviewer=_clean_review,
        limits=DevelopmentLoopLimits(max_cycles=1, max_worker_calls=1),
    )
    assert result["status"] == "BLOCK"
    assert "review:code:tests-pass" in result["cycles"][0]["blocker_set"]

    expansion = lambda _: {"violated_acceptance_items": ["new-obligation"], "suggestions": []}
    blocked = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"},
        worker=lambda _: {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}]},
        validator=_pass_validation, code_reviewer=expansion, contract_reviewer=_clean_review,
    )
    assert blocked["terminal_code"] == "REVIEW_ACCEPTANCE_EXPANSION"


def test_sealed_candidate_is_not_reopened_by_stale_metadata() -> None:
    sealed = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"},
        worker=lambda _: {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}]},
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
    )
    stale = evaluate_sealed_candidate_reopen(sealed, {"pull_request_status": "stale", "material_evidence": False})
    assert stale == {"status": "PASS", "reopen": False, "reason": "EVIDENCE_CANNOT_REOPEN"}
    material = evaluate_sealed_candidate_reopen(sealed, {"material_evidence": True, "violated_acceptance_items": ["tests-pass"]})
    assert material["reopen"] is True
    explicit = evaluate_sealed_candidate_reopen(sealed, {}, explicit_user_authorized=True)
    assert explicit["reason"] == "EXPLICIT_USER_AUTHORIZATION"


def test_resume_of_sealed_state_does_not_call_worker_again() -> None:
    calls = 0

    def worker(_: dict[str, object]) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}]}

    sealed = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"}, worker=worker,
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
    )
    resumed = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"}, worker=worker,
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
        resume_state=sealed,
    )
    assert resumed == sealed
    assert calls == 1


def test_worker_cannot_redefine_frozen_acceptance() -> None:
    result = run_development_loop(
        contract=_contract(), baseline_files={"src/app.py": "return 1\n"},
        worker=lambda _: {"operations": [{"op": "replace", "path": "src/app.py", "expected_sha256": _sha("return 1\n"), "content": "return 2\n"}], "acceptance_set": ["invented"]},
        validator=_pass_validation, code_reviewer=_clean_review, contract_reviewer=_clean_review,
    )
    assert result["terminal_code"] == "WORKER_AUTHORITY_EXPANSION"
