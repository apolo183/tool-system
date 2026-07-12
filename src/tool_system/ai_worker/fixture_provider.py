from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Mapping

from tool_system.ai_worker.contract import (
    AIWorkerError,
    AIWorkerErrorCode,
    AIWorkerRequest,
    AIWorkerUsage,
    CancellationSignal,
    ProviderResponse,
    canonical_json_bytes,
    estimate_input_tokens,
    estimate_json_tokens,
)


@dataclass(frozen=True)
class FixtureScenario:
    output: Mapping[str, object] | None = None
    error_code: AIWorkerErrorCode | None = None
    retryable: bool = False
    logical_duration_ms: int = 1
    cost_microunits: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None


class DeterministicFixtureProvider:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def __init__(self, scenarios: Mapping[str, FixtureScenario]) -> None:
        self._scenarios = dict(scenarios)
        self._call_count = 0
        self._lock = threading.Lock()

    @property
    def call_count(self) -> int:
        with self._lock:
            return self._call_count

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: CancellationSignal | None = None,
    ) -> ProviderResponse:
        with self._lock:
            self._call_count += 1

        if cancellation is not None and cancellation.is_cancelled():
            return ProviderResponse(
                output=None,
                usage=AIWorkerUsage(),
                error=AIWorkerError(
                    code=AIWorkerErrorCode.CANCELLED,
                    message="fixture invocation cancelled",
                ),
            )

        scenario = self._scenarios.get(request.operation)
        if scenario is None:
            return ProviderResponse(
                output=None,
                usage=AIWorkerUsage(input_tokens=estimate_input_tokens(request.inputs)),
                error=AIWorkerError(
                    code=AIWorkerErrorCode.PROVIDER_FAILURE,
                    message="fixture scenario not found",
                ),
            )

        output = _canonical_output(scenario.output)
        usage = AIWorkerUsage(
            input_tokens=(
                scenario.input_tokens
                if scenario.input_tokens is not None
                else estimate_input_tokens(request.inputs)
            ),
            output_tokens=(
                scenario.output_tokens
                if scenario.output_tokens is not None
                else (estimate_json_tokens(output) if output is not None else 0)
            ),
            duration_ms=scenario.logical_duration_ms,
            cost_microunits=scenario.cost_microunits,
        )

        if cancellation is not None and cancellation.is_cancelled():
            return ProviderResponse(
                output=None,
                usage=usage,
                error=AIWorkerError(
                    code=AIWorkerErrorCode.CANCELLED,
                    message="fixture invocation cancelled",
                ),
            )
        if scenario.error_code is not None:
            return ProviderResponse(
                output=None,
                usage=usage,
                error=AIWorkerError(
                    code=scenario.error_code,
                    message=f"fixture returned {scenario.error_code.value}",
                    retryable=scenario.retryable,
                ),
            )
        return ProviderResponse(output=output, usage=usage)


def _canonical_output(
    output: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if output is None:
        return None
    return json.loads(canonical_json_bytes(dict(output)).decode("utf-8"))
