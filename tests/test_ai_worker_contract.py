from __future__ import annotations

import json
from dataclasses import replace

from tool_system.ai_worker import (
    AIModelSpec,
    AIWorkerBudget,
    AIWorkerErrorCode,
    AIWorkerRequest,
    ContentAddressedInput,
    PromptSpec,
    canonical_sha256,
    validate_ai_worker_request,
)


def _request() -> AIWorkerRequest:
    payload = {
        "blueprint": "build a deterministic CLI",
        "acceptance": ["tests pass"],
    }
    return AIWorkerRequest(
        request_id="request-001",
        idempotency_key="fixture:request-001",
        attempt_number=1,
        operation="generate-patch",
        model=AIModelSpec(
            provider_id="deterministic-fixture",
            model_id="fixture-v1",
            capabilities=("structured-output", "tool-free-generation"),
            context_window_tokens=256,
        ),
        prompt=PromptSpec(
            prompt_id="implementation-prompt",
            prompt_version="v1",
        ),
        inputs=(
            ContentAddressedInput.build(
                input_id="blueprint",
                kind="approved-blueprint",
                media_type="application/json",
                payload=payload,
            ),
        ),
        required_capabilities=("structured-output",),
        required_output_keys=("patch", "summary"),
        budget=AIWorkerBudget(
            max_input_tokens=64,
            max_output_tokens=64,
            max_total_tokens=128,
            timeout_ms=100,
            max_cost_microunits=0,
        ),
        metadata={"trace_id": "private-trace-value"},
    )


def test_content_address_is_canonical_and_request_is_valid() -> None:
    first = {"b": [2, 3], "a": 1}
    second = {"a": 1, "b": [2, 3]}

    assert canonical_sha256(first) == canonical_sha256(second)
    validation = validate_ai_worker_request(_request())
    assert validation.ok is True
    assert validation.error_code is None
    assert validation.reasons == ()


def test_input_integrity_mismatch_fails_closed() -> None:
    request = _request()
    bad_input = replace(request.inputs[0], payload_sha256="0" * 64)

    validation = validate_ai_worker_request(replace(request, inputs=(bad_input,)))

    assert validation.ok is False
    assert validation.error_code is AIWorkerErrorCode.INPUT_INTEGRITY
    assert validation.reasons == ("input blueprint payload_sha256 mismatch",)


def test_secret_and_non_finite_inputs_are_rejected() -> None:
    request = _request()
    secret_input = replace(request.inputs[0], sensitivity="secret")
    invalid_payload = replace(
        request.inputs[0],
        input_id="non-finite",
        payload=float("nan"),
        payload_sha256="0" * 64,
    )

    secret_validation = validate_ai_worker_request(
        replace(
            request,
            inputs=(secret_input,),
            metadata={"api_key": "must-never-enter-contract"},
        )
    )
    payload_validation = validate_ai_worker_request(
        replace(request, inputs=(invalid_payload,))
    )

    assert secret_validation.error_code is AIWorkerErrorCode.INVALID_REQUEST
    assert "input blueprint sensitivity must not be secret" in secret_validation.reasons
    assert "metadata key is secret-like: api_key" in secret_validation.reasons
    assert payload_validation.error_code is AIWorkerErrorCode.INVALID_REQUEST
    assert "input non-finite payload must be finite canonical JSON" in (
        payload_validation.reasons
    )


def test_capability_budget_and_authority_violations_are_classified() -> None:
    request = _request()
    capability = validate_ai_worker_request(
        replace(request, required_capabilities=("code-generation",))
    )
    budget = validate_ai_worker_request(
        replace(
            request,
            budget=AIWorkerBudget(
                max_input_tokens=1,
                max_output_tokens=1,
                max_total_tokens=2,
                timeout_ms=100,
                max_cost_microunits=0,
            ),
        )
    )
    authority = validate_ai_worker_request(
        replace(
            request,
            execution_mode="live",
            writes_target_repo=True,
            executes_target_repo_mutation=True,
            production_deployment=True,
        )
    )
    non_boolean_authority = validate_ai_worker_request(
        replace(request, writes_target_repo=0)  # type: ignore[arg-type]
    )

    assert capability.error_code is AIWorkerErrorCode.CAPABILITY_MISMATCH
    assert budget.error_code is AIWorkerErrorCode.BUDGET_EXCEEDED
    assert authority.error_code is AIWorkerErrorCode.INVALID_REQUEST
    assert set(authority.reasons) >= {
        "execution_mode must be fixture in P14B",
        "writes_target_repo must be false in P14B",
        "executes_target_repo_mutation must be false in P14B",
        "production_deployment must be false in P14B",
    }
    assert non_boolean_authority.error_code is AIWorkerErrorCode.INVALID_REQUEST


def test_request_audit_contains_hashes_but_no_payload_or_metadata_values() -> None:
    marker = "payload-must-not-appear-in-audit"
    request = _request()
    protected_input = ContentAddressedInput.build(
        input_id="source",
        kind="repository-source",
        media_type="text/plain",
        payload={"source": marker},
    )
    request = replace(
        request,
        inputs=(protected_input,),
        metadata={"trace_id": "metadata-must-not-appear-in-audit"},
    )

    rendered = json.dumps(request.audit_record(), sort_keys=True)

    assert marker not in rendered
    assert "metadata-must-not-appear-in-audit" not in rendered
    assert request.idempotency_key not in rendered
    assert protected_input.payload_sha256 in rendered
    assert "idempotency_key_sha256" in rendered
    assert '"metadata_keys": ["trace_id"]' in rendered


def test_error_taxonomy_is_exact_and_stable() -> None:
    assert {code.value for code in AIWorkerErrorCode} == {
        "INVALID_REQUEST",
        "INPUT_INTEGRITY",
        "CAPABILITY_MISMATCH",
        "PROVIDER_MISMATCH",
        "BUDGET_EXCEEDED",
        "CANCELLED",
        "TIMEOUT",
        "PROVIDER_FAILURE",
        "INVALID_RESPONSE",
        "REPLAY_CONFLICT",
        "INTERNAL_FAILURE",
    }


def test_malformed_nested_contract_is_rejected_without_exception() -> None:
    request = replace(_request(), model=None)  # type: ignore[arg-type]

    validation = validate_ai_worker_request(request)

    assert validation.error_code is AIWorkerErrorCode.INVALID_REQUEST
    assert validation.reasons == ("model must be AIModelSpec",)
