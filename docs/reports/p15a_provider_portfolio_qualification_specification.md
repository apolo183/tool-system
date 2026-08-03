# P15A Phase Entry and Provider Portfolio Qualification Specification

Status: `P15A_ACCEPTED_GOVERNANCE_ONLY_QUALIFICATION_SPECIFICATION`

## Decision

P15 enters only at
`P15A_PROVIDER_PORTFOLIO_QUALIFICATION_SPECIFICATION`. This record freezes the
provider-neutral interface, task profile, hard capability floors, economics,
benchmark corpus, credential-reference, evidence, and authorization contracts
that later P15 stages must implement or satisfy.

P15A is specification evidence only. It does not add or enable a provider,
route, adapter, credential, benchmark, repository read, target mutation, or
production capability. P15B remains separately unauthorized.

## Parent, baseline, and global alignment

- Direct parent: `docs/reports/p14i_blueprint_to_code_acceptance_closure.md`.
  P14 is accepted and closed only for the bounded isolated-fixture claim.
- Canonical baseline commit:
  `e3b02654edbe69850d0f801adb77a083c444b2d3`.
- Canonical baseline tree:
  `ef8de13cce5ce55b713ba8a083196142f6504ccd`.
- Phase owner:
  `blueprint/tool_system_v0.yaml:milestones.P15_MULTI_PROJECT_BENCHMARK`.
- Stage owner:
  `blueprint/tool_system_v0.yaml:milestones.P15_MULTI_PROJECT_BENCHMARK.stage_plan.P15A_PROVIDER_PORTFOLIO_QUALIFICATION_SPECIFICATION`.
- Global owner: `blueprint/tool_system_v0.yaml:product_objective`.
- Authorization packet:
  `P15A-PHASE-ENTRY-AND-QUALIFICATION-SPECIFICATION-LIFECYCLE-v1`.

The canonical main comparison was identical before branch creation. The stable
blueprint, provider/economics roadmap contract, module contracts, policies,
configuration, runtime source, and fixture corpus are read-only inputs and are
not changed by P15A.

## Read-only existing-surface inventory

| Surface | Current merged evidence | P15A disposition |
| --- | --- | --- |
| provider-neutral request/result | `src/tool_system/ai_worker/contract.py` — `AIWorkerRequest`, `AIWorkerResult`, `AIWorkerUsage`, and stable `AIWorkerErrorCode` | locked as the existing structured execution envelope; no schema or source change |
| provider protocol | `src/tool_system/ai_worker/contract.py` — `AIWorkerProvider` | locked fields: provider/model identity, capabilities, provider kind, execution mode, external-provider, credential, and network flags, plus `invoke(request, cancellation)` |
| runtime enforcement | `src/tool_system/ai_worker/runtime.py` — `AIWorkerRuntime` and default `FixtureOnlyExecutionGuard` | route execution remains independent and fail-closed; selection does not grant execution authority |
| module interface | `docs/modules/ai-worker-runtime-contract-v1.md` | current aggregate interface is `ai-worker-runtime-api@1.0.0`; P14C live behavior remains separately guarded and not reauthorized |
| portfolio selection contract | `docs/model_provider_portfolio_and_economics_contract_v1.md` | `adaptive_model_portfolio_and_economics@1` remains an active roadmap/product-control contract with no runtime claim |
| deterministic provider fixture | `src/tool_system/ai_worker/fixture_provider.py` | current no-network/no-credential fixture is evidence input only; it is not a benchmark result |
| accepted seed corpus | `tests/fixtures/p14h/**`, `tests/test_p14h_multi_stack_e2e.py`, and `docs/reports/p14h_multi_stack_fixture_acceptance.md` | accepted P14 fixture evidence may seed later corpus design but does not qualify any provider/model |
| bounded prior live proof | `docs/reports/p14c_bounded_real_provider_acceptance.md` | one historical bounded proof is evidence of interface viability only; it creates no current provider, credential, or network authority |

Named candidates in the portfolio roadmap are unqualified candidate names, not
enabled routes. P15A assigns no candidate a qualification state and publishes no
catalog snapshot.

## Locked provider/model qualification record

Every later candidate record must be versioned, content-addressed where
applicable, and contain at least:

- provider ID, execution-surface ID, exact model ID, and adapter/interface
  version;
- catalog version, policy version, qualification state, effective time, expiry,
  and replacement relation;
- task-class eligibility and exact capability tags;
- context, input, output, tool, structured-output, and concurrency limits;
- dated price, quota, data-policy, retention, residency, health, and availability
  snapshot references;
- credential-reference schema ID and authorization-envelope reference, never a
  credential value;
- benchmark case/result references, confidence, sample count, acceptance rate,
  reliability, and recency;
- explicit stop, demotion, retirement, and rollback-evidence references.

Moving model aliases cannot be reproducible evidence. Promotion states remain
the portfolio-only sequence already owned by the roadmap contract:

```text
DISCOVERED -> QUARANTINED -> BENCHMARKING -> SHADOW -> CANARY
           -> ELIGIBLE -> PRIMARY
           -> DEGRADED -> RETIRED
```

Discovery does not activate a route. No P15A record is promoted, demoted, or
retired.

## Locked task profile

Every later routing input must record, independently rather than collapsing
risk into complexity:

- task class, language, repository-context size, and dependency breadth;
- reasoning and implementation complexity;
- security, data, repository-mutation, and operational risk;
- required capabilities and minimum quality/confidence floor;
- expected verification, review, repair, and recovery burden;
- critical-path status, remaining slack, and delay sensitivity;
- evidence confidence and reasons for uncertainty.

The profile is advisory. It cannot select its own route, create authority,
lower a floor, add a credential, or activate a provider. The later router must
be deterministic for the same task profile, catalog snapshot, policy version,
authorization envelope, and evidence set.

## Locked hard floors and decision order

A route is ineligible if any hard floor fails. Floors are evaluated before
economics and cannot be repaired by choosing a cheaper or different provider:

1. explicit authorization packet and permitted execution surface;
2. data sensitivity, transfer, residency, retention, and provider-policy fit;
3. exact model identity, required capabilities, context, and output limits;
4. independent security, quality, confidence, and operational-risk floors;
5. time, token, cost, attempt, retry, cancellation, and no-progress ceilings;
6. current catalog, policy, benchmark, health, and repository preconditions;
7. credential-reference availability without reading the value during routing;
8. separately authorized repository access and target mutation boundaries.

An empty eligible set, stale or missing evidence, authorization mismatch, hard
budget exhaustion, cancellation, or no-progress condition produces a stable
block/stop result. Provider switching cannot bypass those conditions.

Availability failover, quality repair, and model escalation remain distinct:

- availability failure may choose the next eligible authorized route;
- quality failure may permit bounded same-route repair and then stronger-route
  escalation when evidence and policy allow;
- policy, data, authority, budget, stale-precondition, and evidence failures stop
  without provider bypass.

## Locked economics contract

The soft objective is
`expected_total_economic_cost_per_accepted_module`, evaluated only after every
hard floor passes. It includes metered usage, accepted-output verification,
retry/rework/recovery, critical-path time, avoidable renewal, allocated
operating, and local-infrastructure costs without double counting.

Public evidence may contain schemas, units, formulas, redacted examples, and
opaque references. Credential values, private billing records, salary, rent,
electricity rates, revenue assumptions, subscription dates, and private weights
remain outside the repository. P15A reads none of them and calculates no route
score.

## Locked benchmark corpus and metrics

The accepted P14H Python and TypeScript fixtures are seed specifications for
later isolated benchmark cases. The minimum corpus retains these case classes:

- greenfield Python CLI and existing Python natural-owner change;
- TypeScript language-neutral add/modify/delete topology;
- bounded failing-test diagnosis and repair;
- ambiguous blueprint and invented-milestone pre-mutation block;
- out-of-scope patch block with preserved baseline;
- cancellation, unapplied-patch discard, resume, and no-progress stop;
- completed-side-effect crash resume without duplicate task/branch/commit;
- local branch conflict and deterministic content-addressed replay.

Later P15 corpus expansion must vary task class, language, project shape,
dependency breadth, context size, risk, verification burden, failure class, and
critical-path sensitivity while preserving cross-project isolation. Every
benchmark project must supply its own authorized durable-module contract.

Required later metrics are acceptance quality, first-pass and final acceptance,
time-to-acceptance, token and metered usage, expected total economic cost,
repair/failover/escalation counts, cancellation and recovery, deterministic
replay, isolation, policy-block correctness, and evidence completeness.

This section specifies cases and metrics only. P15A executes no benchmark,
creates no benchmark result, reads no real repository, and makes no
generalization claim.

## Credential-reference and evidence boundary

Only provider ID, secret-store kind, opaque credential-reference locator,
required ownership/permission metadata, permitted execution surface, and
redacted availability/error metadata may enter public evidence. Resolution of a
credential value is an execution-time side effect requiring a separately named
provider-model-network-credential-reference-limit packet after every other
preflight passes.

Later qualification evidence must bind the exact task profile, catalog and
policy versions, candidate record, benchmark case and corpus version, immutable
input/precondition digest, authorization envelope, bounded usage, redacted
failure class, validation outcome, and disposition reason. Status text, PR
metadata, receipts, or a documentation assertion cannot substitute for those
artifacts.

## Acceptance matrix

| P15A objective | Locked evidence | Result |
| --- | --- | --- |
| provider interfaces | existing `AIWorkerProvider` and `ai-worker-runtime-api@1.0.0` inventoried without source change | PASS |
| task profiles | minimum advisory profile and deterministic input binding frozen | PASS |
| hard floors | fail-closed eligibility order and non-bypass semantics frozen | PASS |
| economics | expected-total-economic-cost objective and private-reference boundary frozen | PASS |
| benchmark corpus | P14H seed case classes, future dimensions, and metrics frozen; no benchmark claim | PASS |
| credentials | public credential-reference-only schema and execution-time value boundary frozen | PASS |
| evidence | exact versioned qualification and benchmark evidence chain frozen | PASS |
| authorization | P15A governance-only authority and P15B/live/real-repository/target/production stop gates frozen | PASS |

## Validation and zero-operation evidence

Fresh validation before branch creation:

```text
baseline_commit: e3b02654edbe69850d0f801adb77a083c444b2d3
baseline_tree: ef8de13cce5ce55b713ba8a083196142f6504ccd
canonical_main_comparison: identical
full_pytest: PASS_620
active_gates: PASS
process_authority: PASS
current_module_registry: PASS
repository_manifest: PASS
working_tree_residue: none
```

P15A becomes current only when this exact ten-path candidate passes focused and
full tests, current validators, forbidden-diff review, Hosted CI, unchanged-base
Ready transition, squash merge, and canonical-main verification.

```text
blueprint_changes: 0
runtime_source_changes: 0
provider_adapters_added_or_modified: 0
provider_candidates_enabled: 0
provider_invocations: 0
benchmark_executions: 0
provider_or_benchmark_network_operations: 0
credential_value_accesses: 0
real_downstream_repository_accesses: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
P15B_authorized: false
```

## State transition and stop condition

After merge, descriptive project state records P15 as active, P15A as the last
accepted stage, and P15B as next with authorization false. P14 remains the
accepted direct predecessor through its P14I record. P15A grants no runtime or
external authority and stops before any P15B implementation, live provider,
credential value, real repository, benchmark, mutation, production, cleanup, or
rollback action.
