# P15B Adapter, Router, and Profiler Fixture Acceptance

Status: `P15B_ACCEPTED_ISOLATED_FIXTURE_NO_LIVE_PROVIDER`

## Decision

P15B accepts one durable module,
`adaptive_model_portfolio_and_economics@1.0.0`, behind
`adaptive-model-portfolio-and-economics-api@1.0.0`. The module builds advisory
task-profile fixtures, evaluates an exact provider-model catalog against an
exact isolated-fixture authorization envelope, applies every hard floor before
integer expected-total-economic-cost comparison, returns a deterministic route
decision, classifies bounded failure dispositions, and exposes structural
`AIWorkerProvider` fixtures.

This is isolated in-memory fixture evidence only. It enables no live provider,
credential value, network route, benchmark result, real repository, target
mutation, production, cleanup, or rollback capability. Every route decision has
`authority_effect: none` and zero operational counters.

## Parent, baseline, and global alignment

- Direct parent:
  `docs/reports/p15a_provider_portfolio_qualification_specification.md`.
- Canonical baseline commit:
  `f912add44845be9d60021333c6792e4ecf6a142b`.
- Canonical baseline tree:
  `493c5563cf4d95b1cc3e236e1453c8c9db5e3423`.
- Phase owner:
  `blueprint/tool_system_v0.yaml:milestones.P15_MULTI_PROJECT_BENCHMARK`.
- Stage owner:
  `blueprint/tool_system_v0.yaml:milestones.P15_MULTI_PROJECT_BENCHMARK.stage_plan.P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES`.
- Global owner: `blueprint/tool_system_v0.yaml:product_objective`.
- Authorization packet:
  `P15B-ADAPTER-ROUTER-AND-PROFILER-FIXTURES-LIFECYCLE-v1`.
- Execution boundary: `isolated_fixture_no_live_provider`.

Canonical main was identical to the frozen baseline before branch creation.
The blueprint and provider/economics roadmap contract remain unchanged.

## Exact module and dependency boundary

The natural owner contains exactly two source paths:

```text
src/tool_system/provider_portfolio/__init__.py
src/tool_system/provider_portfolio/fixtures.py
```

The module consumes `ai-worker-runtime-api@1.0.0` only for the existing
provider-neutral request, response, cancellation, canonical-hash, and
deterministic fixture boundary. `src/tool_system/ai_worker/**` is unchanged.
`docs/modules/ai-worker-runtime-contract-v1.md` changes only its direct-consumer
closure metadata, and its registry hash is re-sealed. There is no second
portfolio implementation or provider execution lane.

The frozen task scope contains exactly twenty-one paths: the two source files,
one module contract, one focused test, the upstream interface-closure contract,
registry and manifest owners, the task pair, this record, descriptive state,
and the necessary registry and stage-consistency tests.

## Advisory task-profile fixture

`build_task_profile_fixture` binds finite input fields into a canonical
`source_input_sha256` and reproducible profile ID. The profile keeps these
dimensions separate:

- task class, language, repository-context tokens, and dependency breadth;
- reasoning and implementation complexity;
- security, data, repository-mutation, and operational risk;
- required capabilities and minimum quality and confidence floors;
- verification and repair burden;
- critical-path flag, remaining slack, and delay sensitivity;
- evidence confidence and uncertainty reasons.

The profile rejects non-canonical tuples, malformed identifiers, invalid scales,
and non-integer micro-unit fields. Its fixed `authority_effect` is `none`; it
cannot choose a route or alter authorization.

## Catalog, hard floors, and deterministic routing

`CatalogSnapshot` contains exact policy, catalog, evidence, adapter, provider,
model, task-class, language, capability, qualification, context, output, risk,
data-policy, evidence-current, credential-reference, surface, duration,
strength, and economic fields. Candidate route IDs are unique and canonically
ordered. Only `ELIGIBLE` and `PRIMARY` may be selected.

`DeterministicProviderRouter` rejects mismatched policy, catalog, or evidence
versions and any authorization envelope that adds live provider, credential
value, real-repository, target-mutation, production, cleanup, or rollback
authority. For every candidate it evaluates, in hard-floor order:

1. qualification state, exact route, and isolated-fixture execution surface;
2. external-provider, network, and credential-use prohibitions;
3. task class, language, capabilities, context, token, and output floors;
4. independent quality, confidence, security, data, mutation, and operational
   risk floors;
5. data-policy, current-evidence, time, and hard-cost envelopes.

Only candidates with no hard-floor reason enter the soft comparison. Economics
uses non-negative integer microunits for metered usage, verification, retry,
rework, recovery, critical-path time, avoidable renewal, allocated operating,
local infrastructure, and opportunity cost. The deterministic order is total
cost, logical duration, then exact route ID. No float score or private economic
value is used.

The selected decision content-addresses the exact profile, authorization,
catalog, per-candidate evaluation, selected route, eligible routes, bounded
availability fallbacks, stronger-route escalations, same-route repair limit, and
stop reason. Same inputs reproduce the same evidence hash.

## Provider-neutral fixture adapter

`PortfolioFixtureAdapter` structurally implements the existing
`AIWorkerProvider` contract and runs through the accepted default
`AIWorkerRuntime` fixture guard. It exposes:

```text
provider_kind: deterministic_fixture
execution_mode: fixture
calls_external_provider: false
uses_credentials: false
network_access: false
```

Construction rejects any non-fixture surface, external-provider flag, network
flag, or credential requirement. Invocation rejects provider/model mismatch,
live execution mode, repository-write or mutation flags, and production flags
before delegating to the existing in-memory deterministic scenario engine.

## Failure-classification fixture

The stable classifications are distinct:

| Failure family | Disposition | Provider switching |
| --- | --- | --- |
| missing credential reference, balance, quota, rate limit, timeout, outage | `AVAILABILITY_FAILOVER` | only the next already eligible bounded route |
| quality or acceptance rejection | `SAME_ROUTE_REPAIR_THEN_ESCALATE` | no availability bypass; one bounded same-route repair then stronger eligible route |
| policy, data, authorization, hard budget, stale precondition, missing evidence | `BLOCK_NO_PROVIDER_BYPASS` | forbidden |
| empty eligible set, exhausted attempts, cancellation, no progress | `STOP` | forbidden |

The classifier creates no attempt and consumes no budget. Route decisions only
describe bounded candidate IDs for a separately authorized future caller.

## Acceptance matrix

| P15B objective | Evidence | Result |
| --- | --- | --- |
| provider-neutral adapter fixtures | structural adapter runs through existing default fixture runtime and rejects live/external construction | PASS |
| task-profile fixtures | canonical advisory profile with independent complexity, risk, verification, critical-path, confidence, and uncertainty fields | PASS |
| deterministic routing | exact inputs reproduce selected route, evaluations, bounded fallback/escalation, and evidence hash | PASS |
| catalog fixtures | exact versions, qualification states, limits, evidence, surface, and integer economics fail closed on drift | PASS |
| hard capability floors | all authorization, data, capability, context, output, quality, risk, evidence, time, and cost floors precede economics | PASS |
| failure classification | availability, quality, hard block, and terminal stop semantics are stable and non-bypassable | PASS |
| module closure | registry, compound contracts, static import DAG, repository manifest, and upstream consumer closure agree | PASS |
| authority boundary | no live provider, credential value, real repository, benchmark, target, production, cleanup, or rollback operation | PASS |

## Validation and zero-operation evidence

The frozen baseline passed `622` tests plus active-gate, process-authority,
current-module-registry, and repository-manifest validation before source work.
The exact twenty-one-path local candidate passed `158` focused closure tests and
`632` full tests, source compilation, both task-pair validators, active gates,
process authority, the current nineteen-module registry, and the repository
manifest with `240` exact formal paths. Final publication still requires
whitespace and forbidden-diff review, Hosted CI, unchanged-base Ready
transition, and squash merge.

```text
blueprint_changes: 0
existing_ai_worker_source_changes: 0
live_provider_adapters_added_or_modified: 0
provider_candidates_enabled_for_live_execution: 0
benchmark_executions: 0
provider_invocations: 0
provider_network_operations: 0
credential_resolver_invocations: 0
credential_value_accesses: 0
real_downstream_repository_accesses: 0
remote_fixture_operations: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
P15C_authorized: false
```

## State transition and stop condition

After merge, descriptive state keeps P15 active, records P15B as the last
accepted stage, and names `P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK` as next with
authorization false. P15C crosses into separately authorized live-provider and
read-only real-repository execution. P15B stops before that boundary and grants
no authority to enter it.
