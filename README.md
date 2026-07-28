# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-27 UTC+09:00

## Definition

tool-system is a domain-agnostic software factory for controlled agentic development.

It coordinates agents, harness workflows, CI checks, patch generation, review gates, and repository write controls. It does not contain finance logic, trading logic, portfolio logic, market-data logic, or investment decision logic.

Its permanent product objective is bounded blueprint-driven autonomous software development: given an approved project blueprint, repository snapshot, authorization envelope, acceptance requirements, authorized provider-model portfolio, and private economics context, the system must be able to profile task complexity, independent risk, and critical-path impact, select an eligible worker route from task-class evidence and expected total economic cost, produce an executable task graph, implement code in an isolated workspace through a real AI worker, test and repair the result, verify both parent and global-objective alignment, create a bounded local Git history, and produce auditable acceptance evidence.

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
- Qualify replaceable provider adapters and select models per task class under hard safety, quality, data, and authorization floors.
- Optimize expected total economic cost per accepted module, including critical-path time and avoidable renewal cost, without committing private economic values.

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.
- Production deployment without separate explicit approval.

## Provider portfolio and development economics

The provider architecture is pluggable behind the versioned `AIWorkerProvider` interface. Roadmap candidates include a supported ChatGPT/Codex subscription surface, OpenAI's metered API, separately qualified domestic metered APIs such as DeepSeek, Qwen, GLM, and Kimi, and future local inference. Naming a candidate does not enable it. Each live provider, exact model, network route, credential reference, data policy, and execution limit remains separately controlled.

A dedicated task-complexity assessor produces an advisory profile; deterministic policy makes the final route decision. Complexity and operational risk are independent. Provider availability failures use bounded failover among already eligible authorized routes, while output-quality failures use bounded repair and evidence-backed model escalation. Policy, data, budget, authorization, and stale-precondition failures block rather than switch around the control.

Models are scored per task class from exact-version benchmark, reliability, time-to-acceptance, availability, and economic evidence. New models enter quarantine and qualification rather than becoming active from version number or launch price alone. Repeated failures demote a model only from affected task classes when possible; accepted replacements are published atomically and history remains auditable.

The soft objective is expected total economic cost per accepted module. It includes provider usage, future renewals caused by delay, critical-path operating burn, local compute and electricity, verification, retry, rework, recovery, rollback, and opportunity cost. Safety, quality, data, and authorization remain hard constraints. Exact salaries, rent, electricity rates, subscription dates, billing values, and revenue assumptions are private installation inputs and never public-repository constants. The detailed contract is `docs/model_provider_portfolio_and_economics_contract_v1.md`.

P14 remains the provider-neutral autonomous-development core plus one separately authorized bounded real-provider proof. P15 owns multi-provider qualification and benchmark acceptance. P16 owns continuous model discovery, price/health refresh, portfolio lifecycle, renewal forecasting, and production-operations acceptance. P15 and P16 remain roadmap-only until separately authorized.

## Current phase state

Current phase: `P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT`.

Status: `active`.

P10 was accepted as a successful controlled, no-production, draft-pull-request pilot. The acceptance demonstrates bounded target-repository planning, named execution approvals, fresh-state checks, exact file allowlists, draft PR creation, local validation handoff, fail-closed correction handling, audit evidence, and rollback references.

P10R is closed, P11 Real Worker Runtime is accepted at the local fixture-only application-guarded scope, and P12 Durable Orchestrator is accepted and closed at the single-host local-fixture SQLite scope. P13 Security and Reliability Hardening is accepted and closed at the application-guarded local fixture-worker and single-host SQLite hardening scope. P14B Provider-Neutral AI Worker Contract is accepted and closed. P14 Blueprint-to-Code Autonomous Development remains active; P14MR is retained as acceptance evidence while durable local module rules are owned by the blueprint and local principles. P15 Multi-project Benchmark and P16 Production Operations and Acceptance remain roadmap-only until separately authorized.

P11 evidence proves an allowlisted Python fixture process with ephemeral workspace isolation, scrubbed environment, application-level network/process/file guards, resource limits, bounded output, timeout, cancellation, process-group termination, and cleanup. It does not prove hostile-code sandboxing, durable orchestration, remote target execution, or production readiness. Finance-us and every other remote target repository remain no-mutation, and production deployment remains prohibited.

P12 evidence proves persisted run/task state, lease recovery, checkpoints, retries, idempotency and attempt numbers, expected precondition SHA enforcement, a side-effect ledger, atomic completed markers and outbox insertion, and local fixture reconciliation across close/reopen and a simulated publisher crash. It grants no arbitrary external exactly-once guarantee, distributed or production claim, remote side effect, or target-repository authority.

P13 evidence hardens the accepted P11-P12 owners through a documented threat model, executable and entrypoint pinning, path/link/environment/network adversarial controls, durable-state resource bounds, transaction and concurrency fault injection, resource-exhaustion and cancellation stress, and local recovery evidence. It does not claim kernel-enforced hostile-code containment, remote target safety, autonomous blueprint-to-code completion, multi-project benchmark acceptance, or production readiness.

P14A locks the evidence-backed capability gaps, canonical inputs/outputs, development state machine, original P14A-P14I sequence, candidate natural owners, ten required acceptance fixtures, bounded product claim, and authorization gates. P14B implements a provider-neutral structured request/result contract and an in-memory deterministic fixture provider with budgets, cancellation, stable errors, redacted audit records, request/result integrity, replay-safe idempotency, and a fail-closed fixture-only provider boundary. P14MR supplies accepted evidence for tool-system's durable-module and milestone-change rules; it does not make milestones into modules or govern downstream repositories. P14C live model/provider execution, finance-us P1B, every remote target mutation, P15-P16, and production deployment remain unauthorized.

The machine-readable durable inventory is `config/module_registry_v1.yaml`, whose current file uses the central four-field top-level shape and is validated by `tool-system-validate-module-registry`. It registers 14 current tool-system modules, their exact natural-owner and repository-local boundary paths, versioned interfaces, reciprocal dependency edges, evidence boundaries, and authorization envelopes. The local validator fails closed on malformed identities and contracts, unclaimed required source/config paths, owner or boundary overlap, ContractReference SHA-256 drift, managed Python import edges that disagree with declared consumers, invalid side-effect target bindings, stale dependency versions, non-reciprocal edges, and declared cycles. This is local structural and source-graph validation only; it does not claim a real central `module-registry-check` PASS, runtime containment, behavioral interface compatibility, automatic module replacement, or cutover.

Every P14-P16 milestone must identify the exact missing link it closes in the global product flow, prove alignment to its immediate parent, and independently prove alignment to `blueprint/tool_system_v0.yaml:product_objective`. Missing either alignment is a fail-closed condition.

## Durable module architecture and milestone discipline

Within tool-system, a module is a persistent, replaceable, single-responsibility functional boundary with a versioned public interface. A milestone is a controlled change and acceptance unit, not a durable module merely because it existed. As a rule, one milestone adds, modifies, or replaces one durable module or one versioned public interface.

Modules communicate only through versioned public interfaces; hidden dependencies, cross-module access to internal state, and parallel active implementations are prohibited. A failed or drifted module is isolated and its outputs stop propagating; dependent consumption pauses pending current revalidation while unrelated modules and accepted evidence remain valid. An interface-compatible replacement changes no unaffected module and requires current replacement, boundary, and affected downstream-closure evidence; an incompatible replacement uses an explicit versioned migration and dependency-derived impact set.

`finance-governance` is the active group authority after its independently completed central closeout. Ordinary central gates consume the current verified committed finance-governance `HEAD`; the exact five-field `config/governance_reference_v1.yaml` records repository identity and a compatibility/audit SHA only. Its `governance_commit_sha` does not select or pin current rules, need not equal the current governance `HEAD`, and a central SHA change alone does not require a tool-system update or PR. The central repository registry supplies identity only; the caller supplies the target root, and no central path, status, or execution evidence is written into the registry. The reference neither controls central `authority_status` nor proves tool-system cutover. S8 completed only the compatibility/audit reference record. Until S9 passes the real central `module-registry-check` and S10 is separately accepted, do not claim tool-system cutover. Active group rules govern now; these repository-local rules may add narrower constraints but must not override them. No copied finance-governance constitution is local authority.

The caller and reference audit is complete. `config/process_authority_v1.yaml` is the local current execution contract for canonical `process-authority@2.0.0` and `process-authority-api@2.0.0`. It requires one explicitly supplied manifest/change-plan pair with exact binding. The protected dispatcher revalidates the real authority, manifest, plan, policy, working-directory, and timeout inputs, requires captured input bytes to remain equal immediately before dispatch, and extracts commands from those same validated plan bytes; no caller-created PASS value, receipt, token, or unchecked command list is accepted. Repository-wide implicit task authority is disabled. `config/replay_snapshot_v1.yaml` content-addresses the retained legacy pair set; `examples/active_gates.yaml` is explicit, non-executing replay input only. Existing reports, manifests, plans, and the legacy index remain present and are not claimed finance-governance process-file compliant. Do not delete or reclassify them without separate cleanup authorization.

Existing reports, task manifests, change plans, and `examples/active_gates.yaml` remain present for the separately gated disposition step. Their presence is not a claim of finance-governance process-file compliance, and this migration does not delete or reclassify them.

`REPO_MANIFEST.md` now registers every current formal authority/config/source/test/CI/fixture path as one exact central-format `Formal Files` row and separately classifies every retained legacy path as non-authority. Its validator preserves the legacy set parser only as bounded compatibility, activates the exact-file mode for the current manifest, rejects overlap, gaps, symlinks, empty formal files, invalid table fields, and cycles, and proves every tracked path is classified exactly once. The retained legacy sets still block a finance-governance process-file-compliance claim; this manifest authorizes neither their cleanup nor their continued use as current authority.

## Repository contract

This repository is a tool layer. Business systems are downstream targets. tool-system may propose or apply changes to target repositories only through their explicit authority, workflow, test, policy, review, execution-approval, and rollback gates. A local tool-system contract cannot grant or alter downstream write authority.

P10 acceptance does not authorize unrestricted downstream mutation, target PR ready transition, target PR merge, production deployment, real external worker execution, or Codex replacement claims. Each such action remains separately gated.

Finance-us P1A is accepted, merged, strictly validated, and closed on target `main` at `7101847826e6701a4d8cc7f0a6208fb9aee2cc4e`. The finance-us P1B phase-entry record and implementation packet are prepared and merged in tool-system. P1B target implementation remains blocked pending a named, action-scoped target execution approval; P1B ready and merge remain separately gated.

The canonical active downstream identity is `apolo183/finance-us`. The legacy `apolo183/finance-os` route is retired and retained only as a closed, no-write compatibility fixture. Direct bootstrap on tool-system and finance-us is disabled, and downstream merge approval is bound to repository, action, base branch, and expected head SHA.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `docs/tool_system_global_development_principles_v1.md`: project-wide engineering discipline contract for evidence, scope, cleanup planning, validation, rollback, and claims.
- `blueprint/tool_system_v0.yaml`: machine-readable blueprint and current accepted lifecycle state.
