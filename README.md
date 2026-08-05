# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-08-06 00:21 UTC+09:00

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

Supported ChatGPT/Codex subscription mode is the daily development route. It is not OpenAI API credit and is never automated by scraping a browser session or extracting authentication material.

All large-model APIs are optional backup routes and are disabled by default, including OpenAI, DeepSeek, Qwen, and future providers. A stored key does not enable a provider or authorize a call. Only repository-external owner configuration may explicitly enable API mode, enable a provider, select the currently available provider/model, and set the existing budget, expiry, transfer, retry, cancellation, and audit controls. Public source does not hard-code which provider or model must be used.

The provider architecture remains pluggable behind the versioned `AIWorkerProvider` interface. Every provider-specific adapter must pass injected fake-I/O contract tests. Unconfigured, unfunded, invalid, expired, or unavailable providers are skipped; another eligible enabled provider may be used, and the subscription route is unaffected. When no enabled API route is usable, the API backup path returns a stable unavailable result rather than silently enabling a provider.

A dedicated task-complexity assessor produces an advisory profile; deterministic policy makes the final route decision. Complexity and operational risk are independent. Availability failures use bounded failover among already enabled, eligible, and authorized routes, while output-quality failures use bounded repair and evidence-backed escalation. Policy, data, budget, authorization, and stale-precondition failures block rather than switch around the control.

The project-level live proof for the dormant API backup requires one explicitly enabled and currently usable key to complete one controlled smoke test on the then-canonical main. It does not require OpenAI and Qwen together, Qwen funding, simultaneous multi-provider availability, or a date-pinned version for a provider that exposes only a moving model ID. Each actual live audit records the provider/model requested and the redacted result.

The soft objective is expected total economic cost per accepted module. It includes subscription capacity, enabled-provider usage, future renewals caused by delay, critical-path operating burn, local compute and electricity, verification, retry, rework, recovery, rollback, and opportunity cost. Safety, quality, data, and authorization remain hard constraints. Exact salaries, rent, electricity rates, subscription dates, billing values, and revenue assumptions are private installation inputs and never public-repository constants. The detailed contract is `docs/model_provider_portfolio_and_economics_contract_v1.md`.

P14 remains the provider-neutral autonomous-development core plus its accepted bounded historical provider proof. P15 owns multi-project product evidence, fake-I/O adapter qualification, failure/economics evidence, and the final single-provider backup smoke gate. P16 owns sustainable operations; provider/model discovery, price/health refresh, and portfolio cadence apply only when API mode is explicitly enabled and are not default-off completion gates. P15 and P16 still require their separate acceptance and entry decisions.

## Current project state

The blueprint is the stable description of the completed product and its
acceptance structure; it intentionally contains no current phase, authorization,
pull-request, commit, CI, or branch-status receipts. The single machine-readable
descriptive progress record is `docs/tool_system_project_state_v1.yaml`, with
stage-specific proof retained in `docs/reports/`.

The project-state file has no authority effect. Current work is authorized only
through the explicit manifest/change-plan pair validated by
`config/process_authority_v1.yaml`; descriptive state, README text, reports, PRs,
branches, commits, or CI results cannot grant a provider call, repository
mutation, lifecycle transition, cleanup, rollback, or production action.

The machine-readable durable inventory is `config/module_registry_v1.yaml`, whose four-field top-level shape is owned by tool-system and validated by `tool-system-validate-module-registry`. It registers 14 current tool-system modules, their exact natural-owner and repository-local boundary paths, versioned interfaces, reciprocal dependency edges, evidence boundaries, and authorization envelopes. The local validator fails closed on malformed identities and contracts, unclaimed required source/config paths, owner or boundary overlap, ContractReference SHA-256 drift, managed Python import edges that disagree with declared consumers, invalid side-effect target bindings, stale dependency versions, non-reciprocal edges, and declared cycles. This structural and source-graph evidence does not prove runtime containment, behavioral interface compatibility, or automatic module replacement.

Every P14-P16 milestone must identify the exact missing link it closes in the global product flow, prove alignment to its immediate parent, and independently prove alignment to `blueprint/tool_system_v0.yaml:product_objective`. Missing either alignment is a fail-closed condition.

## Durable module architecture and milestone discipline

Within tool-system, a module is a persistent, replaceable, single-responsibility functional boundary with a versioned public interface. A milestone is a controlled change and acceptance unit, not a durable module merely because it existed. As a rule, one milestone adds, modifies, or replaces one durable module or one versioned public interface.

Modules communicate only through versioned public interfaces; hidden dependencies, cross-module access to internal state, and parallel active implementations are prohibited. A failed or drifted module is isolated and its outputs stop propagating; dependent consumption pauses pending current revalidation while unrelated modules and accepted evidence remain valid. An interface-compatible replacement changes no unaffected module and requires current replacement, boundary, and affected downstream-closure evidence; an incompatible replacement uses an explicit versioned migration and dependency-derived impact set.

For every important engineering task, read the current `main` branch directly
from the canonical central remote
`git@github.com:apolo183/finance-governance.git`, using only
`docs/global_development_principles_v1.md` and
`config/repo_registry_v1.yaml`. Do not pin a central commit SHA, use a local
central checkout path, or treat central pull requests or history as policy.
Central rules prevail on conflict; repository-local rules may add only
tool-system-specific constraints. The central principles are consumed at source,
not copied here, and tool-system project state is not written back to the
identity-only central registry.

The current-task caller audit is complete. `config/process_authority_v1.yaml` is the local current execution contract for canonical `process-authority@2.3.0` and `process-authority-api@2.1.0`. It requires one explicitly supplied manifest/change-plan pair with exact binding. The protected dispatcher revalidates the real authority, manifest, plan, policy, working-directory, and timeout inputs, requires captured input bytes to remain equal immediately before dispatch, and extracts commands from those same validated plan bytes; no caller-created PASS value, receipt, token, or unchecked command list is accepted. Repository-wide implicit task authority is disabled. Version `2.3.0` also owns the P14C approval-v2 verifier and seals the committed `tool-system-p14c-live` operator entry: `prepare-approval` initializes or reopens the hardened ledger and emits exact public owner-comment JSON with no GitHub, credential, or provider read, while `execute` accepts only a positive comment ID, authenticates and durably burns that exact comment, and emits a redacted receipt around the already bounded public synthetic provider path. Before any grant, the verifier binds the comment to the exact clean execution commit, tree, fixed critical-source manifest including the operator entry, actual host, and one immutable single-host ledger identity. A committed burn is never released after caller failure, and the resulting capability revalidates the same source immediately before credential access. The entry source and fake-I/O tests are not a real approval record, provider execution, multi-host exactly-once completion, or P14C acceptance. `config/replay_snapshot_v1.yaml` content-addresses the retained legacy pair set; `examples/active_gates.yaml` is explicit, non-executing replay input only. Existing reports, manifests, plans, and the legacy index remain retained non-authority inputs. Do not delete or reclassify them without separate cleanup authorization.

Existing reports, task manifests, change plans, and `examples/active_gates.yaml` remain present for the separately gated disposition step. They are not current authority, and this alignment does not delete or reclassify them.

`REPO_MANIFEST.md` registers every current formal authority/config/source/test/CI/fixture path as one exact local `Formal Files` row and separately classifies every retained legacy path as non-authority. Its validator preserves the legacy set parser only as bounded compatibility, activates the exact-file mode for the current manifest, rejects overlap, gaps, symlinks, empty formal files, invalid table fields, and cycles, and proves every tracked path is classified exactly once. This manifest authorizes neither retained-set cleanup nor their use as current authority.

## Repository contract

This repository is a tool layer. Business systems are downstream targets. tool-system may propose or apply changes to target repositories only through their explicit authority, workflow, test, policy, review, execution-approval, and rollback gates. A local tool-system contract cannot grant or alter downstream write authority.

P10 acceptance does not authorize unrestricted downstream mutation, target PR ready transition, target PR merge, production deployment, real external worker execution, or Codex replacement claims. Each such action remains separately gated.

The public core serializes no active downstream project identity. A target
repository identity, exact snapshot, path policy, lifecycle policy, and
authorization envelope are caller-supplied inputs and are validated together
at the execution boundary. The checked-in write policy governs tool-system
itself; operator-private target bindings do not become source constants.

Historical target reports and fixtures remain only in the manifest's retained
non-authority sets. They are not current defaults, policy entries, or execution
authority, and this correction does not rewrite or delete them.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `docs/tool_system_global_development_principles_v1.md`: project-wide engineering discipline contract for evidence, scope, cleanup planning, validation, rollback, and claims.
- `blueprint/tool_system_v0.yaml`: machine-readable target-state blueprint; current progress is recorded separately in `docs/tool_system_project_state_v1.yaml`.
