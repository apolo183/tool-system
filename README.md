# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-12 UTC+09:00

## Definition

tool-system is a domain-agnostic software factory for controlled agentic development.

It coordinates agents, harness workflows, CI checks, patch generation, review gates, and repository write controls. It does not contain finance logic, trading logic, portfolio logic, market-data logic, or investment decision logic.

Its permanent product objective is bounded blueprint-driven autonomous software development: given an approved project blueprint, repository snapshot, authorization envelope, and acceptance requirements, the system must be able to produce an executable task graph, implement code in an isolated workspace through a real AI worker, test and repair the result, verify both parent and global-objective alignment, create a bounded local Git history, and produce auditable acceptance evidence.

## System boundary

### In scope

- Parse machine-readable blueprints and execution specs.
- Decompose approved specs into bounded implementation tasks.
- Generate patches through controlled agents.
- Run tests, lint, type checks, and policy checks.
- Block writes when tests or policy checks fail.
- Create auditable repository changes.
- Collect pull request and workflow state for repo write decisions.
- Execute approved repository write actions through explicit controller gates.
- Validate downstream target-repository task manifests in dry-run mode.
- Prepare approved downstream target-repository pull-request write flows after explicit gates pass.
- Run local task-manifest and change-plan gates through productized runner commands.
- Plan bounded task graphs with dependency ordering and agent role assignments.
- Run role-assigned task graph steps through an auditable no-mutation runtime.
- Build no-mutation worker adapter contracts and orchestration records.
- Define and operate controlled target-repository PR pilot gates after explicit execution approval.
- Execute a real local process-backed worker inside a controlled fixture-only runtime after minimum safety gates pass.
- Persist and reconcile single-host orchestration state inside the accepted local-fixture SQLite boundary.
- Build the missing blueprint-to-code autonomous implementation, test, repair, review, and local Git loop before multi-project benchmarking.

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.
- Production deployment without separate explicit approval.

## Current phase state

Current phase: `P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT`.

Status: `active`.

P10 was accepted as a successful controlled, no-production, draft-pull-request pilot. The acceptance demonstrates bounded target-repository planning, named execution approvals, fresh-state checks, exact file allowlists, draft PR creation, local validation handoff, fail-closed correction handling, audit evidence, and rollback references.

P10R is closed, P11 Real Worker Runtime is accepted at the local fixture-only application-guarded scope, and P12 Durable Orchestrator is accepted and closed at the single-host local-fixture SQLite scope. P13 Security and Reliability Hardening is accepted and closed at the application-guarded local fixture-worker and single-host SQLite hardening scope. P14B Provider-Neutral AI Worker Contract and P14MR Milestone Module Invariant are accepted and closed. P14 Blueprint-to-Code Autonomous Development is active at the exact P14C bounded real-provider module. P15 Multi-project Benchmark and P16 Production Operations and Acceptance remain roadmap-only until separately authorized.

P11 evidence proves an allowlisted Python fixture process with ephemeral workspace isolation, scrubbed environment, application-level network/process/file guards, resource limits, bounded output, timeout, cancellation, process-group termination, and cleanup. It does not prove hostile-code sandboxing, durable orchestration, remote target execution, or production readiness. Finance-us and every other remote target repository remain no-mutation, and production deployment remains prohibited.

P12 evidence proves persisted run/task state, lease recovery, checkpoints, retries, idempotency and attempt numbers, expected precondition SHA enforcement, a side-effect ledger, atomic completed markers and outbox insertion, and local fixture reconciliation across close/reopen and a simulated publisher crash. It grants no arbitrary external exactly-once guarantee, distributed or production claim, remote side effect, or target-repository authority.

P13 evidence hardens the accepted P11-P12 owners through a documented threat model, executable and entrypoint pinning, path/link/environment/network adversarial controls, durable-state resource bounds, transaction and concurrency fault injection, resource-exhaustion and cancellation stress, and local recovery evidence. It does not claim kernel-enforced hostile-code containment, remote target safety, autonomous blueprint-to-code completion, multi-project benchmark acceptance, or production readiness.

P14A locks the evidence-backed capability gaps, canonical inputs/outputs, development state machine, original P14A-P14I sequence, candidate natural owners, ten required acceptance fixtures, bounded product claim, and authorization gates. P14B implements a provider-neutral structured request/result contract and an in-memory deterministic fixture provider with budgets, cancellation, stable errors, redacted audit records, request/result integrity, replay-safe idempotency, and a fail-closed fixture-only provider boundary. P14MR inserts the universal replaceable milestone-module invariant before P14C. P14C is authorized only for `p14c-openai-gpt56-luna-v1`: one public synthetic fixture through `gpt-5.6-luna`, exact TLS endpoint and credential reference, at most two attempts, 45 seconds, 9216 cumulative tokens, and $0.02 cumulative cost. Repository content, finance-us P1B, every target mutation, P14D-P16, and production deployment remain unauthorized.

P14C extends the accepted P14B module through a versioned live execution guard while retaining the fixture-only runtime as the default. Unit tests use injected transports with no external IO. The only permitted live action is the formal synthetic evidence entry point, which stores no provider-side response state, exposes no tools, follows no redirect, records only redacted hashes and usage, and accepts no repository input.

Every P14-P16 milestone must identify the exact missing link it closes in the global product flow, prove alignment to its immediate parent, and independently prove alignment to `blueprint/tool_system_v0.yaml:product_objective`. Missing either alignment is a fail-closed condition.

## Replaceable milestone-module architecture

Every project generated, controlled, or adopted by tool-system is a DAG of versioned capability modules, and every major or minor milestone is one independently accepted module. Modules communicate only through versioned public input/output interfaces; hidden dependencies, cross-module access to internal state, and parallel active implementations are prohibited.

An implementation defect with a correct contract is repaired inside the module. Contract or blueprint drift invalidates and isolates that module, blocks dependent paths, and preserves unrelated modules. An interface-compatible replacement changes no unaffected module and requires only dependent revalidation; an incompatible replacement uses an explicit versioned migration and dependency-derived impact set. The wrong active route is removed after its replacement passes, while Git and audit evidence remain available.

Every controlled project must inherit `blueprint/tool_system_v0.yaml:milestone_module_invariant` or embed an equivalent machine-readable contract before its next phase entry or controlled write. Existing external projects are not silently changed by this rule.

## Repository contract

This repository is a tool layer. Business systems are downstream targets. tool-system may propose and apply changes to target repositories only through explicit workflow, test, policy, review, execution-approval, and rollback gates.

P10 acceptance does not authorize unrestricted downstream mutation, target PR ready transition, target PR merge, production deployment, real external worker execution, or Codex replacement claims. Each such action remains separately gated.

Finance-us P1A is accepted, merged, strictly validated, and closed on target `main` at `7101847826e6701a4d8cc7f0a6208fb9aee2cc4e`. The finance-us P1B phase-entry record and implementation packet are prepared and merged in tool-system. P1B target implementation remains blocked pending a named, action-scoped target execution approval; P1B ready and merge remain separately gated.

The canonical active downstream identity is `apolo183/finance-us`. The legacy `apolo183/finance-os` route is retired and retained only as a closed, no-write compatibility fixture. Direct bootstrap on tool-system and finance-us is disabled, and downstream merge approval is bound to repository, action, base branch, and expected head SHA.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `docs/tool_system_global_development_principles_v1.md`: project-wide engineering discipline contract for evidence, scope, cleanup planning, validation, rollback, and claims.
- `blueprint/tool_system_v0.yaml`: machine-readable blueprint and current accepted lifecycle state.
