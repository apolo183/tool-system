"""Worker adapter contracts and no-mutation dry-run harnesses."""

from tool_system.worker_adapter.contract import (
    AdapterRequest,
    AdapterResult,
    DryRunWorkerAdapter,
    WorkerAdapter,
    build_adapter_request_from_worker_request,
    run_adapter_requests,
)
from tool_system.worker_adapter.orchestration import (
    build_adapter_orchestration_record,
    build_adapter_orchestration_record_from_worker_requests,
    write_adapter_orchestration_record,
)
from tool_system.worker_adapter.policy_gate import (
    evaluate_adapter_policy_gate,
    evaluate_adapter_policy_gate_for_requests,
    write_adapter_policy_gate_record,
)

__all__ = [
    "AdapterRequest",
    "AdapterResult",
    "DryRunWorkerAdapter",
    "WorkerAdapter",
    "build_adapter_orchestration_record",
    "build_adapter_orchestration_record_from_worker_requests",
    "build_adapter_request_from_worker_request",
    "evaluate_adapter_policy_gate",
    "evaluate_adapter_policy_gate_for_requests",
    "run_adapter_requests",
    "write_adapter_orchestration_record",
    "write_adapter_policy_gate_record",
]
