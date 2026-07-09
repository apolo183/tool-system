# P9A Worker Adapter Contract Record

repo_rel_path: docs/reports/p9a_worker_adapter_contract_record.md  
role: implementation evidence record  
purpose: record P9A worker adapter contract scope and boundaries  
status: ACTIVE  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00

## Scope

P9A adds a no-mutation worker adapter contract and dry-run adapter harness.

Evidence artifacts:

- `src/tool_system/worker_adapter/contract.py`
- `tests/test_worker_adapter_contract.py`
- `examples/task_manifests/tool_system_worker_adapter_contract.yaml`
- `examples/change_plans/tool_system_worker_adapter_contract.yaml`

## Boundary

P9A does not approve or perform:

- external worker calls;
- downstream repository writes;
- target repository mutation;
- production deployment;
- business-domain implementation;
- Codex replacement claims.

## Validation

```bash
python -m pytest -q tests/test_worker_adapter_contract.py tests/test_agent_worker_interface.py
python -m tool_system.cli.validate_change_plan examples/change_plans/tool_system_worker_adapter_contract.yaml
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
```
