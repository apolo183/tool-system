# Provider mode AI-worker-runtime realignment

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_RUNTIME_REALIGNMENT_NO_EXECUTION`

This is package 2 of
`PROVIDER-MODE-AND-ACCEPTANCE-REALIGNMENT-LIFECYCLE-v1`. It depends on the
accepted target/policy package at canonical main
`149296ff5e87e6b18a4982a9046012fd3edeb1b0` and changes only the
`ai_worker_runtime` module plus its direct configuration, contract, registry,
tests, and descriptive evidence closure.

## Frozen objective

- all large-model APIs and provider switches remain disabled by default;
- schema-3 repository-external settings own provider priority and requested
  model selection;
- key presence never enables or authorizes an API call;
- unavailable routes may be skipped with sanitized evidence;
- a bounded candidate chain stops after one eligible provider completes one
  deterministic public-fixture smoke case;
- no eligible route returns `NO_AVAILABLE_PROVIDER`;
- moving aliases do not create an exact-version completion blocker;
- schema-3 final-smoke mode reads no private downstream target;
- the generic worker runtime denies API execution unless the exact externally
  selected provider/model pair is supplied to its pre-invocation guard;
- legacy schema-1/2 exact-matrix behavior remains compatibility-only;
- every provider-specific adapter remains covered by injected fake-I/O.

## Implemented runtime boundary

Policy schema 3 adds `provider_priority` and `provider_model` to the owner-only
settings file. The public template has an empty priority, empty model values,
API mode disabled, every provider disabled, every transfer switch disabled,
and total and provider budgets set to zero. The loader rejects an enabled API
mode without an enabled prioritized route and requested model. Credential
lookup is lazy, so a key file is not touched until the active route, source,
budget, and transfer controls pass.

The schema-3 preflight loads the complete adapter catalog but selects only the
ordered routes enabled by external settings. Zero-budget, missing-credential,
invalid-key, unfunded, unavailable-model, rate-limit, outage, and transport
availability evidence may advance to the next already-enabled route. Policy,
transfer, hard-budget, source or policy drift, cancellation, request/response
integrity, and replay failures stop the chain. There is no same-route retry.
The chain returns `NO_AVAILABLE_PROVIDER` when no eligible or usable route
remains and stops immediately after one success.

Only the content-addressed deterministic public fixture is legal in schema 3;
the target packet and target snapshot are not loaded. A configured moving
alias is sent as requested, while any distinct provider-resolved model
identifier is validated and recorded separately rather than treated as a
missing exact-version blocker. Schema 1 and schema 2 retain their old
two-provider/two-case exact-matrix behavior for compatibility only.

The generic `AIWorkerRuntime` also exposes a pure route selector and a
default-disabled execution guard. The selector has no credential or transport
input, returns `API_DISABLED` unless API mode is explicit, skips disabled or
declared-unavailable routes, and selects at most one externally named
provider/model. The execution guard then rejects request or runtime identity
drift before provider invocation. The P15 schema-3 control plane remains the
authoritative owner of budget, expiry, transfer, credential, source-seal, and
availability classification.

## Draft continuity repair

Draft PR #185 and its branch already existed at the exact accepted base when
the sealed 18-path candidate reached publication. The draft contained the
generic runtime guard and its test as two additional natural-owner paths but
had an incomplete test closure and failing Hosted CI. The final manifest adopts
those paths plus the repository-manifest fixed-count consistency test, producing
an exact 21-path closure. While the guard ran, the draft advanced from 10
commits/8 paths at `598e75f79f9e52f2c7e4d9f50380b8badecf9cff` to 16
commits/9 paths at `a1104beea34aabfcbd712802204f60e0daa3f1aa`; both heads
failed Hosted CI. Publication pins the latter as the parent of one non-force,
fast-forward consolidation commit. It neither deletes nor rewrites history,
creates a duplicate PR, or changes main before the guarded squash merge.

## Preserved controls

External credentials, global and provider switches, budgets, expiry,
authorization, provider data-transfer switches, source seals, per-attempt token
and time limits, zero retry, cancellation, conservative reservation, atomic
usage ledger, response validation, no tools/search/proxy/storage, and redacted
audit records remain fail-closed. The adaptive provider packet and portfolio
module are unchanged in this package.

## Validation and zero-operation evidence

The sealed exact 21-path candidate passed 223 focused
owner/consumer/governance tests and 719 full-repository tests. Python
compilation, Ruff on every changed Python file, task-manifest and change-plan
validation, active gates, process authority, the current module registry, the
repository manifest, diff hygiene, forbidden-path review, and secret and
project-identity scans also passed. Hosted CI remains a required remote guard
and is not claimed by this local record. This package performs no provider,
credential-value, private-target, benchmark, downstream, mutation, production,
cleanup, rollback, P15 acceptance, P16 entry, or final live-smoke operation.

- credential_resolver_invocations: 0
- credential_value_accesses: 0
- provider_invocations: 0
- network_operations: 0
- benchmark_executions: 0
- private_target_reads: 0
- target_repository_accesses: 0
- target_mutations: 0
- production_operations: 0
- cleanup_operations: 0
- rollback_operations: 0
- p15_stage_accepted: false
- p16_stage_entered: false
- final_live_smoke_executed: false
