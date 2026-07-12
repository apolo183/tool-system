# tool-system Global Development Principles v1

## Metadata

- repo_rel_path: `docs/tool_system_global_development_principles_v1.md`
- role: active project-wide engineering discipline contract for tool-system
- purpose: define mandatory evidence, documentation-first execution, blueprint alignment, durable replaceable modules, milestone discipline, scope, file disposition, cleanup, validation, rollback, side-effect tool use, and claims rules for tool-system work
- author: ChatGPT / apolo183
- created_at: 2026-07-08 09:20 UTC+08:00
- updated_at: 2026-07-13 UTC+09:00

## 1. Authority

This file is the repository-local discipline contract for tool-system and governs only tool-system work. It does not govern another repository. A tool-system local rule cannot change another repository's owner, authority, status, responsibility, or write authorization. Narrower tool-system task manifests, change plans, tests, runbooks, and PR descriptions may add constraints but must not silently override this file. A conflict stops work until a cross-document disposition is recorded.

The authorized immutable reference at `config/governance_reference_v1.yaml` pins candidate finance-governance commit `f039a5355e1e5ea3fa865b827947b0c1153a2745`. The reference is an immutable pointer and does not activate group governance, report central cutover state, or replace current tool-system-local authority by itself. Until the required finance-governance `repo-check` passes and central cutover is confirmed, these local principles remain the active tool-system authority. After activation, local rules may add constraints but may not override the pinned group governance.

## 2. Evidence hierarchy

Fact priority is: current user logs/files/commands/evidence packages > current repo files, branch, commits, PR diffs, CI state, and active docs > active project-wide contracts > active milestone or stage contracts > closed evidence and receipts > history or memory as retrieval hints only. Old drafts, stale branches, prior chat, and search summaries never override current repo evidence.

## 3. Evidence gate

No engineering fact, readiness claim, cleanup decision, implementation plan, or file disposition may be asserted without current repo, commit, diff, PR, command, CI, evidence, or active-contract support. Before modifying or judging a file, read the natural-owner file plus relevant caller, callee, upstream, downstream, and tests. Unread objects are `UNKNOWN`.

## 4. Drift gate

Every material step must verify that it follows the active contract and shortest correct tool-system path, does not switch to a legacy or fallback route, does not use stale output as authority, and does not expand write, deletion, runtime, target-repository, external, or production scope. Unresolved drift stops with a blocker, missing evidence, protected scope at risk, smallest readonly audit needed, and corrected next step.

## 5. Authorization gate

A document, PR, green test, audit, or dry-run authorizes only its explicit scope. Target-repository mutation, production deployment, destructive cleanup, remote writes outside tool-system, and downstream business-system changes require current user authorization plus active contract evidence. No planner or runner output grants execution authority by itself.

## 6. Formal and process file discipline

Formal files are active contracts, source, configs, tests, runbooks, docs, examples, and audit interfaces required to run, validate, operate, audit, or roll back tool-system. Process files are notes, temporary scripts, dry-run outputs, proposal drafts, patch plans, debug logs, and intermediate evidence. Process files must use the narrowest project-local task root such as `tmp/<task_id>/`, `reports/<task_id>/`, or `artifacts/<task_id>/`, unless an explicit exception names path, reason, retention, side effects, and cleanup responsibility.

The caller and reference audit is complete. `config/process_authority_v1.yaml` is the local current-task authority contract and requires one explicitly supplied manifest/change-plan pair with exact binding. No repository-wide task index is implicit execution authority. `config/replay_snapshot_v1.yaml` content-addresses the retained legacy pair set, and `examples/active_gates.yaml` may be selected only for non-executing replay. Existing `docs/reports/**`, `examples/task_manifests/**`, `examples/change_plans/**`, and the legacy index remain present pending a separately authorized disposition and cleanup step. Their presence is not a claim of finance-governance process-file compliance.

`REPO_MANIFEST.md` is the local tracked-path registry. It must classify every tracked path exactly once as a formal file-set member or a retained non-authority member, maintain one acyclic formal upstream graph with one root, and fail closed on gaps or overlap. Registering a retained set does not make it formal, authorize cleanup, or establish finance-governance process-file compliance.

## 7. File disposition

Allowed dispositions are `KEEP`, `MODIFY`, `REPLACE`, `DELETE`, `ADD`, and `UNKNOWN`. `KEEP` means correct, active, necessary, or valid evidence. `MODIFY` means necessary but stale or wrong. `REPLACE` means superseded by validated replacement and then removed. `DELETE` means obsolete, wrong, duplicate, garbage, superseded, or process-only. `ADD` means a required formal artifact is missing. `UNKNOWN` means unread or impact not verified. Do not preserve invalid objects by moving them to archive, deprecated, fallback, backup, or history directories.

## 8. Simplification and cleanup

Priority is the shortest correct controlled automation path: active contract, natural-owner implementation, focused tests, CI gate, audit record, and rollback reference. Keep one active contract path per responsibility and one natural-owner implementation path per runtime responsibility. Remove or supersede duplicate mainlines, obsolete process docs, transitional scripts, and outdated tests once their replacement and rollback are evidence-backed.

## 9. Reuse and ownership

Prefer `MODIFY` on the natural owner path. Do not create parallel lanes unless a contract proves why replacement is required and defines the deletion or migration point. Reusable tool-system components must parameterize repository, branch, manifest, change plan, graph, output root, and execution options rather than hard-coding downstream business logic.

## 10. Claims boundary

Do not claim Codex replacement, production readiness, autonomous target-repository execution readiness, downstream mutation approval, or milestone closure without current runtime evidence, CI evidence, active closeout criteria, and rollback evidence. Dry-runs, fixtures, planner output, and green unit tests are scoped evidence only.

## 11. Rollback, tests, temp roots, and commands

Non-trivial implementation uses a separate branch and PR. Failed branch state requires a failed branch/base/status/diff record, clean-base return, and redesign. Tests must protect active behavior; tests for obsolete routes are deleted or rewritten. Commands must state directory, environment, purpose, write scope, target-repository impact, deletion status, and rollback when they are material or dangerous.

## 12. Cross-document compliance

Later milestone, planner, runner, cleanup, and target-repository documents must either inherit this file or explicitly record a conflict requiring cross-document disposition. This file grants no implementation, target-repository mutation, destructive cleanup, production deployment, or external-system write authority by itself.

## 13. Documentation-first execution loop

Do not rely on long conversation context as execution authority. Each stage is controlled by active documents and must follow this loop:

1. read the active blueprint, global principles, milestone document, task manifest, and change plan;
2. design or update the narrow current-stage document;
3. verify the current-stage document against the immediate parent document, the active blueprint, active requirements, and this file;
4. execute only the documented scope;
5. create evidence showing what actually happened;
6. compare actual evidence against the stage document and change plan;
7. compare the stage document against both its immediate parent and the active blueprint or requirement source before designing the next stage.

No document means no execution. No evidence means no acceptance. Detected drift stops feature work and requires documentation or process correction first.

## 14. Short-stage rule

A stage should be short, single-objective, and auditable. The default stage unit is one natural objective, one branch, one task manifest, one change plan, one evidence record, one CI result, and one explicit stop condition. If more than one objective appears necessary, split the work into multiple stages unless an active document explains why bundling is safer.

## 15. Blueprint alignment invariant

Every milestone, sub-milestone, task manifest, change plan, evidence record, and acceptance record must prove two alignments:

1. parent alignment: the document follows its immediate parent milestone, stage, manifest, or change plan;
2. global alignment: the document still follows the active blueprint or requirement source.

Parent alignment alone is insufficient. A long chain of small local deviations can accumulate into material blueprint drift. Each stage therefore must explicitly check both its parent and the active blueprint or requirement source, and must stop if either alignment is missing or ambiguous.

For nested work, the expected proof shape is:

```text
blueprint or requirement source
  -> major milestone
    -> sub-milestone
      -> task manifest
        -> change plan
          -> execution evidence
```

Each level must identify its parent, identify the active blueprint or requirement source, and record why the level does not expand or redirect scope beyond either one.

## 16. Script and automation control by documents

Scripts, CLIs, agents, and repository-control tools execute documents; they do not define scope by themselves. A script may only run when the active blueprint or requirement source, milestone document, task manifest, and change plan authorize its purpose, inputs, outputs, side effects, and stop condition. Script output is evidence only after it is compared with the controlling documents and the active blueprint.

## 17. Side-effect tool preflight

Before any tool call that creates, updates, deletes, merges, labels, comments on, or otherwise mutates GitHub or repository state, the agent must verify:

- intent;
- target repository;
- target branch or PR;
- expected side effect;
- duplicate check;
- active manifest/change-plan authorization;
- parent alignment;
- global blueprint or requirement alignment;
- stop condition;
- whether the selected tool matches the documented action.

If the documented action is file creation or file update but the selected tool is branch creation, merge, deletion, cleanup, or any other mismatched mutation, the agent must stop before the tool call. If a duplicate branch, PR, file, or plan exists, reuse or stop; do not create numbered variants unless an active document explicitly authorizes replacement and records disposition.

## 18. Branch single-flight rule

Each stage may create at most one working branch. The branch name must be defined or implied by the stage document. If branch creation succeeds, all later writes for that stage use that branch. If branch creation fails because the branch already exists, the agent must inspect and either reuse it or stop for disposition. Creating branch variants such as `name2`, `name3`, or `retry` is prohibited without an explicit incident or replacement document.

## 19. Incident and residue rule

Any accidental branch, PR, file, label, comment, or other side effect is residue. The next action is an incident or cleanup plan, not continued feature expansion. Residue cleanup must be handled through a separate cleanup gate/PR when it requires deletion, branch deletion, history-affecting action, or any destructive cleanup.

## 20. Durable module and milestone discipline

A module is a persistent, replaceable functional boundary inside tool-system with one responsibility and one versioned public interface. A milestone is a controlled unit of change and acceptance. A milestone does not become a persistent module merely because it existed. As a rule, one milestone adds, modifies, or replaces one durable module or one versioned public interface.

Each active tool-system module requires a stable identity, owner, single responsibility, version, versioned public interface, input and output contracts, error semantics, externally visible side effects, code/data/test/runtime-artifact/cleanup boundaries, explicit upstream and downstream dependency edges, and acceptance, rollback, and replacement evidence.

Modules depend only on accepted public interfaces and recorded outputs. Hidden dependencies, interface bypasses, cross-module access to private state, undeclared dependency edges, circular dependencies, and more than one active implementation for the same responsibility are prohibited. Shared foundations must be minimized, stable, versioned, narrowly responsible, and assigned an explicit blast-radius review.

The durable rule owners are this file and `blueprint/tool_system_v0.yaml`. `docs/reports/p14mr_milestone_module_invariant.md` remains existing P14MR acceptance evidence only; it is not the permanent rule owner.

`config/module_registry_v1.yaml` is the machine-readable inventory of current tool-system modules and public dependency declarations. Its validator enforces the registered field set, natural-owner coverage without overlap, dependency version/interface references, reciprocal edges, and an acyclic declared graph. It is an implementation of local structural registration, not evidence that Python import edges are derived automatically, runtime state is isolated by module, interfaces are behaviorally compatible, or replacement is performed automatically.

## 21. Failure isolation without new lifecycle status

An implementation defect with a still-correct module objective and public contract is repaired inside that module boundary and reaccepted. When a module fails, drifts from its approved objective or public interface, or loses valid evidence, isolate that module and stop its outputs before further dependent execution.

Dependent modules pause consumption and wait for current revalidation. The affected downstream dependency closure is revalidated, while unrelated modules and existing unrelated acceptance evidence remain valid. Discovery of a hidden dependency expands the explicit impact set and is itself a governance defect; it does not justify an undocumented whole-project rewrite.

Terms such as isolate, pause consumption, replace, and revalidate are ordinary rule language here. This file defines no new machine lifecycle or status enumeration; any such values require a separately authorized applicable schema.

## 22. Compatible replacement and bounded blast radius

An interface-compatible replacement must preserve the approved interface version, inputs, outputs, error semantics, and externally visible side effects. It must not require code or contract changes in unaffected modules. The replacement itself, its public upstream and downstream boundaries, and the affected downstream dependency closure are revalidated; dependents are not reimplemented by default. An interface-incompatible replacement requires a new version, an explicit migration plan, and a dependency-derived impact set. A product-blueprint change requires replanning only the impacted module set, while a shared-foundation change requires an explicit wider blast-radius review.

The replacement must prove direct-parent and global-blueprint alignment and pass its acceptance suite before an atomic active-graph swap. After acceptance, the superseded route is removed from the active tree so two mainlines do not persist. Git and audit evidence remain available for diagnosis and rollback; invalid code, documents, tests, or routes are not retained as active fallback, archive, or compatibility paths.

## 23. Replacement activation and cleanup

A failed or drifted module may not continue producing active outputs. A replacement must pass its acceptance suite and boundary revalidation before one atomic active-route swap; afterward exactly one active authority and route remains. Creator-owned temporary files are removed by their creator. Destructive cleanup, branch deletion, history-affecting action, or rollback still requires its applicable gate and authorization. Replacing a module means removing the wrong route from the current system after the replacement passes, not erasing Git history or bypassing evidence requirements.

## 24. Tooling and downstream authority boundary

tool-system may provide module-planning tools, validators, or recommendations to another repository. Their use remains controlled by that repository's own authority and explicit authorization. A tool-system contract, blueprint, test, planner result, or recommendation cannot impose governance on another repository or change its owner, authority, status, responsibility, or write authorization.

Declared module-graph structure now has a local machine validator. Source-import edge derivation, runtime module isolation, task planning from the graph, blueprint compilation, behavioral interface compatibility evidence, fault-isolation impact records, automated replacement, multi-project acceptance, benchmarks, and production review remain future tool-system product responsibilities. Registry declaration alone is not sufficient for final product acceptance: P14E owns compiler and runtime-flow integration and P15 owns separately authorized multi-project evidence. Neither stage receives downstream governance or write authority from this file.

## 25. Provider portfolio, model routing, and development economics

Provider integrations are replaceable adapters behind a versioned worker interface. Provider-specific credentials, billing, transport, retry behavior, and data policy must not leak into the task planner or unrelated modules. The public repository stores credential references, schemas, redacted fixtures, and policy only; it never stores secret values, browser session material, private billing records, or private operating-cost values. ChatGPT/Codex subscription access and metered APIs are different execution surfaces and accounting models. A supported subscription surface must not be treated as API credit or implemented by scraping authentication material.

A dedicated task-complexity assessor may produce an advisory structured profile, but a deterministic policy engine owns the final provider/model route. Complexity, operational risk, data sensitivity, repository-mutation risk, required capability, confidence, verification burden, and critical-path impact are distinct inputs. Cost cannot lower a capability, safety, data, quality, or authorization floor. The same profile, portfolio snapshot, and policy version must reproduce the same route decision.

Provider unavailability and output-quality failure are distinct. Missing credentials, quota, balance, rate limit, timeout, or outage may trigger bounded failover to another eligible authorized route; the replacement need not be stronger. Quality failure may receive bounded same-route repair and then evidence-backed escalation to a stronger eligible route. Policy denial, unauthorized data transfer, stale precondition, hard budget exhaustion, or missing required evidence blocks execution and cannot be bypassed through provider switching.

Models are qualified per task class rather than by one global ranking. Discovery does not activate a model, version number does not prove superiority, and moving aliases are not reproducible evidence. Promotion, demotion, degradation, and retirement use exact model IDs plus dated price, policy, health, and benchmark snapshots. A repeatedly failing model is removed from affected task classes and may serve lower-complexity classes only while current evidence meets their floors. Replacing an active route requires an accepted replacement, one atomic publication, and retention of catalog, benchmark, audit, and Git evidence.

The primary soft optimization objective is expected total economic cost per accepted module. It includes metered provider usage, avoidable future subscription renewals caused by delay, critical-path personnel/rent/operating burn, local compute and electricity, verification, retry, rework, failure recovery, rollback, incident handling, lost revenue, and opportunity cost without double counting. An already committed non-refundable current-period payment is sunk for the current decision; a future renewal crossed because of delay is avoidable step cost. Full time-cost weight applies only to critical-path delay or consumed slack that becomes critical.

Provider and economics defaults are maintained by event-driven updates, a 24-hour lightweight score refresh, a 72-hour changed-model incremental benchmark, a weekly portfolio review, and a monthly plus pre-renewal forecast review. Severe outages, security advisories, material price changes, or regressions trigger immediate review. Exact private currency values and weights remain installation configuration outside the public repository.

`docs/model_provider_portfolio_and_economics_contract_v1.md` owns the detailed roadmap contract. P14 remains the provider-neutral blueprint-to-code core plus one separately authorized bounded real-provider proof. P15 owns multi-provider qualification and benchmark acceptance. P16 owns continuous portfolio operations. This principle grants no live provider, credential, target-repository, phase-entry, or production authority.

## 26. Final state

Status: ACTIVE. Applies only to tool-system, including its blueprint, durable modules, milestone-change planning, provider/model portfolio roadmap, development economics, docs, source, tests, examples, policies, cleanup planning, repository-control work, side-effect tool use, and target-repository adapters. P14 remains active and P14C remains unauthorized.
