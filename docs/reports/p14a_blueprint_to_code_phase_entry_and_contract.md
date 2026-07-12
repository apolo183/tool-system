# P14A Blueprint-to-Code Phase Entry and End-to-End Contract

status: ACTIVE
phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT
stage: P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION
parent: docs/reports/p14r_blueprint_product_objective_roadmap_reconciliation.md
validated_main: 2d3dd10e622959a1cb5d124e58b1ba0b53b9ca51
authorized_by: user_authorized_next_step_p14_phase_entry

## Single objective

Enter P14 and lock the end-to-end product contract, evidence-backed capability gaps, short-stage dependency sequence, natural-owner boundaries, acceptance fixtures, authorization gates, and P15 stop condition before any P14 implementation begins.

P14A changes governance, blueprint state, public contracts, and alignment tests only. It does not implement or call a model provider, inspect or mutate a downstream target, run an autonomous coding worker, or deploy anything.

## Accepted starting point

P11-P13 provide the bounded foundation that P14 may build on:

- application-guarded local Python fixture execution with bounded resources and cleanup;
- single-host durable task, lease, checkpoint, retry, side-effect-ledger, and outbox state;
- path, executable, environment, resource, transaction, concurrency, integrity, and recovery hardening;
- task-graph validation, role records, policy gates, audit records, and controlled repository-write primitives.

These foundations are accepted only at their recorded scopes and are not evidence that blueprint-to-code autonomous development already works.

## Current capability-gap evidence

| Required product link | Current audited behavior | P14 disposition |
| --- | --- | --- |
| blueprint-to-task decomposition | `requirement_graph.py` requires caller-supplied `work_items`, roles, and task-manifest paths | P14E must derive bounded milestones/tasks from the approved blueprint and repository evidence |
| real AI implementation | default `NoMutationAgentWorker` returns record-only results | P14B-P14C must add a provider-neutral contract, deterministic fixture provider, and separately gated real provider |
| external worker adapter | `DryRunWorkerAdapter` blocks `calls_external_worker=true` | retain fail-closed default; enable only the exact P14C execution packet |
| repository understanding | no repository-context index or natural-owner discovery implementation is present in the audited owners | P14D owns bounded context collection, relevance selection, and owner evidence |
| actual role execution | `role_runtime.py` emits `execute=false` role records | P14F-P14G must execute only approved local-fixture development actions |
| patch/test/repair loop | stage runner executes predeclared batches but does not generate patches or feed test failures back to an AI worker | P14F owns structured patch, validation, diagnosis, bounded repair, and independent review |
| durable end-to-end orchestration | durable SQLite exists but is not integrated with the stage runner as a complete development state machine | P14G binds P14 actions to leases, attempts, checkpoints, side-effect markers, and resume |
| Git development workflow | controlled remote-write primitives exist, but no accepted isolated local branch/commit/conflict workflow completes a project | P14G owns local Git fixtures; remote publishing stays separately gated |
| end-to-end product evidence | no accepted fixture proves blueprint through code, tests, repair, Git history, and closure | P14H supplies multi-stack isolated fixture evidence before P14I closure |

## Canonical input contract

Every P14 run starts with immutable or content-addressed references to:

```text
approved_project_blueprint
repository_snapshot_and_expected_head
repository_governance_documents
authorization_envelope
validation_and_acceptance_requirements
resource_cost_and_retry_limits
```

The system must reject missing, internally inconsistent, stale, or unauthorized inputs before an implementation side effect.

## Canonical output contract

A successful bounded run produces:

```text
repository_context_and_natural_owner_evidence
milestone_hierarchy_and_executable_task_DAG
phase_documents_task_manifests_and_change_plans
structured_AI_worker_requests_and_results
bounded_code_patches
test_failure_diagnosis_and_repair_history
parent_and_global_product_alignment_reviews
durable_attempt_checkpoint_and_side_effect_records
local_branch_and_commit_history
draft_PR_plan
acceptance_or_fail_closed_record
cleanup_and_rollback_disposition
```

An externally published draft pull request is an optional later side effect and requires a separate repository/action/base/head authorization. It is not required for P14 acceptance.

## Development state machine

```text
INGEST
  -> PREFLIGHT
  -> CONTEXT_READY
  -> PLAN_READY
  -> IMPLEMENTING
  -> VERIFYING
  -> REPAIRING (bounded loop back to VERIFYING)
  -> REVIEWING
  -> LOCAL_GIT_READY
  -> ACCEPTED | BLOCKED | ROLLED_BACK
```

Every transition requires:

- an idempotency key and attempt number;
- expected blueprint, repository, manifest, plan, and precondition hashes;
- direct-parent and global `product_objective` alignment;
- an authorization check for the next side effect;
- durable completion evidence before advancing;
- bounded errors and a cleanup/rollback disposition on failure.

## P14 short-stage sequence

### P14A Phase Entry and End-to-End Specification

Lock this contract, capability baseline, stage sequence, owners, evidence, claim limits, and authorization state. Governance only.

### P14B Provider-Neutral AI Worker Contract

Implement structured AI request/result, model capability and prompt-version metadata, token/time/cost ceilings, cancellation, error taxonomy, secret boundaries, deterministic fixture provider, and replay-safe idempotency. No live provider call.

### P14C Bounded Real Model Provider Execution

Execute the first real model call only after a named provider/model/credential/cost/network packet is approved. Prove timeout, cancellation, retry, redaction, response validation, audit, and no repository mutation.

### P14D Repository Context and Natural-Owner Discovery

Build a bounded repository index, governance/blueprint reader, dependency and test mapping, relevance selection, evidence sufficiency gate, natural-owner proposal, context-size limits, and stale-snapshot detection.

### P14E Blueprint Compiler

Derive milestones, short stages, executable task DAGs, phase documents, manifests, change plans, dependencies, acceptance checks, rollback nodes, and dual-alignment references from an approved blueprint plus repository context.

### P14F Autonomous Patch-Test-Repair-Review Loop

Generate structured patches, enforce exact file scope and preconditions, run tests, classify failures, feed bounded diagnostics back to the worker, repair with retry/no-progress limits, and perform independent code/contract review.

### P14G Durable Local Git Orchestration

Integrate the P14 state machine with durable leases, checkpoints, attempts, side-effect ledger, cancellation, crash resume, isolated local Git branches/commits, conflict handling, rollback, and creator cleanup. No remote repository.

### P14H Multi-Stack End-to-End Fixture Acceptance

Prove the entire blueprint-to-code flow on isolated greenfield and existing-project fixtures, including Python and TypeScript, successful development, test repair, ambiguous input blocking, scope escape, crash resume, rollback, and deterministic replay.

### P14I Acceptance and Closure

Accept P14 only if all required links and fixtures pass and the system's claims remain bounded. Stop at P15 authorization.

## Candidate natural-owner boundaries

```text
src/tool_system/ai_worker/**
tests/test_ai_worker_*.py

src/tool_system/repository_context/**
tests/test_repository_context_*.py

src/tool_system/blueprint_compiler/**
tests/test_blueprint_compiler_*.py

src/tool_system/development_loop/**
tests/test_development_loop_*.py

src/tool_system/local_git/**
tests/test_local_git_*.py
```

Existing planner, runtime, process-worker, durable-orchestrator, gate, policy, and repository-controller owners may be changed only by a later stage whose evidence shows that owner is necessary. P14A creates none of these candidate modules.

## Required P14 acceptance fixtures

1. a greenfield Python CLI generated from an approved blueprint;
2. a change to an existing Python library with correct natural-owner selection;
3. a TypeScript package proving language-neutral planning and command configuration;
4. an initially failing test repaired within a bounded attempt budget;
5. an ambiguous or insufficient blueprint blocked before code mutation;
6. a requested out-of-scope file change blocked and rolled back;
7. a worker timeout/cancellation with cleanup and resumable durable state;
8. a simulated crash after a completed local side effect without duplicate replay;
9. a local Git conflict that blocks or resolves only through the documented policy;
10. a deterministic replay that produces the same plan and logical result for the same content-addressed inputs.

## P14 acceptance claims

P14 may eventually claim only:

> Given an approved bounded blueprint and isolated repository fixture, tool-system can autonomously plan, implement, test, repair, review, and record a local Git software change through an auditable, resumable, fail-closed workflow.

P14 does not prove or authorize:

- safe autonomous mutation of arbitrary real repositories;
- production deployment or operations readiness;
- hostile arbitrary-code containment;
- unlimited model spend, retries, context, or network access;
- business-requirement invention;
- multi-project benchmark acceptance;
- Codex replacement.

## P14A authorization record

```text
P14_phase_entry_authorized: true
P14A_governance_lifecycle_authorized: true
P14B_source_implementation_authorized: false
live_model_provider_execution_authorized: false
remote_target_mutation_authorized: false
finance_us_P1B_implementation_authorized: false
P15_phase_entry_authorized: false
production_deployment_authorized: false
```

## P14A acceptance

P14A passes only when the blueprint, README, AGENTS, this record, task manifest, change plan, active gates, and machine tests agree on the contract, stage sequence, capability gaps, and authorization boundary; full tests and CI must pass.

## Stop condition

After P14A merge, stop at P14B source-implementation authorization. No model/provider call or target-repository action occurs.

## Local validation evidence

```text
phase_product_and_contract_tests: PASS_10
full_repository_tests: PASS_272
task_manifest: PASS
change_plan: PASS
active_gates: PASS
named_local_test_dependencies_cache_and_basetemp_removed: true
model_provider_execution: false
remote_target_mutation: false
finance_us_mutation: false
branch_cleanup: false
production: false
```
