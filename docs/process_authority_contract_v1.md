# Process Authority Contract v1

Role: durable tool-system current-task authority and replay-boundary contract.

Owner: `process_authority` module.

Upstream: `blueprint/tool_system_v0.yaml:product_objective`, `blueprint/tool_system_v0.yaml:milestone_module_invariant`, and `docs/tool_system_global_development_principles_v1.md`.

Downstream: task planner, task runner, role runtime, CLI adapters, tests, and audit records.

## Current-task authority

`config/process_authority_v1.yaml` is the single local machine contract for task-pair authority. Current execution requires one task manifest and one change plan supplied explicitly for that invocation. The change plan must name the same manifest. A repository-wide implicit task index is not current execution authority.

Before any configured command runs, the task runner must pass the process-authority contract, manifest policy validation, explicit pair binding, and change-plan validation. A failed preflight runs no configured command.

## Canonical replay boundary

`config/replay_snapshot_v1.yaml` is content-addressed compatibility evidence for the legacy `examples/active_gates.yaml` pair set at source head `4445cb5ec3ddab0738560e0d5f4a64b9dd582bd7`. It records the source index SHA256 and a deterministic digest over the sorted manifest path/hash and change-plan path/hash tuples.

Replay validation reconstructs both digests from the current legacy inputs and blocks on any drift. The snapshot has `authority: false`, `replay_only: true`, and every execution, target-mutation, production, and cleanup flag set to false. It cannot authorize commands or become a fallback current-task route.

## Caller migration

Task, batch, graph, stage, and role-runtime defaults use explicit task pairs and `config/process_authority_v1.yaml`. The legacy `--active-gates` option remains only as an explicit replay-only compatibility input. It is never selected by default and is rejected when command execution is requested.

The legacy active-gate validator remains a consistency check for retained replay inputs, not an authority grant. CI validates the process-authority contract, the replay snapshot, the durable module registry, and legacy replay consistency independently.

## Cleanup and claim boundary

Existing reports, manifests, change plans, and `examples/active_gates.yaml` remain present. This contract does not delete, reclassify, move, or claim finance-governance process-file compliance for them. Cleanup requires a separate authorization and accepted disposition.

This contract grants no finance-us or other target-repository mutation, live provider execution, branch cleanup, production deployment, or governance activation. Rollback uses a named revert PR preserving Git and audit history.
