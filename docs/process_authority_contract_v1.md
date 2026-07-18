# Process Authority Contract v1

Role: durable tool-system current-task authority and replay-boundary contract.

Owner: canonical `process-authority` module.

Upstream: `blueprint/tool_system_v0.yaml:product_objective`, `blueprint/tool_system_v0.yaml:milestone_module_invariant`, and `docs/tool_system_global_development_principles_v1.md`.

Downstream: task planner, task runner, role runtime, CLI adapters, tests, and audit records.

## Current-task authority

`config/process_authority_v1.yaml` is the single local machine contract for task-pair authority. Current execution requires one task manifest and one change plan supplied explicitly for that invocation. The change plan must name the same manifest. A repository-wide implicit task index is not current execution authority.

Its machine module identity is exactly `process-authority@2.0.0`, exposing
`process-authority-api@2.0.0`. The historical compatibility ID
`process_authority` is not accepted in the current authority file. The Python
package remains `tool_system.process_authority`; that language-level underscore
does not create a second module authority or an identity alias.

Before any configured command runs, the task runner must pass the process-authority contract, manifest policy validation, explicit pair binding, and change-plan validation. A failed preflight runs no configured command.

The public command-dispatch API receives the real authority, manifest, plan,
repo-write policy, autonomy-policy, working-directory, and timeout inputs. It
revalidates those inputs internally and accepts no caller-created PASS value,
receipt, token, or unchecked command list. It captures the validated file bytes,
compares them again immediately before dispatch, and extracts commands from the
same captured plan bytes. Any validation failure or byte drift blocks before
`subprocess.run`.

## Canonical replay boundary

`config/replay_snapshot_v1.yaml` is content-addressed compatibility evidence for the legacy `examples/active_gates.yaml` pair set at source head `4445cb5ec3ddab0738560e0d5f4a64b9dd582bd7`. It records the source index SHA256 and a deterministic digest over the sorted manifest path/hash and change-plan path/hash tuples.

Replay validation reconstructs both digests from the current legacy inputs and blocks on any drift. The snapshot has `authority: false`, `replay_only: true`, and every execution, target-mutation, production, and cleanup flag set to false. It cannot authorize commands or become a fallback current-task route.

## Caller migration

Task, batch, graph, stage, and role-runtime defaults use explicit task pairs and `config/process_authority_v1.yaml`. The legacy `--active-gates` option remains only as an explicit replay-only compatibility input. It is never selected by default and is rejected when command execution is requested.

The legacy active-gate validator remains a consistency check for retained replay inputs, not an authority grant. CI validates the process-authority contract, the replay snapshot, the durable module registry, and legacy replay consistency independently.

The retained replay boundary contains no compatibility module-ID input and
cannot authorize the protected command-dispatch API.

## Cleanup and claim boundary

Existing reports, manifests, change plans, and `examples/active_gates.yaml` remain present. This contract does not delete, reclassify, move, or claim finance-governance process-file compliance for them. Cleanup requires a separate authorization and accepted disposition.

This contract grants no finance-us or other target-repository mutation, live provider execution, branch cleanup, production deployment, or governance activation. Rollback uses a named revert PR preserving Git and audit history.
