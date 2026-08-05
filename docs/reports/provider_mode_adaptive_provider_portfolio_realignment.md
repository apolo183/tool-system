# Provider mode adaptive-provider-portfolio realignment

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_PORTFOLIO_REALIGNMENT_NO_EXECUTION`

This is package 3 of
`PROVIDER-MODE-AND-ACCEPTANCE-REALIGNMENT-LIFECYCLE-v1`. It depends on the
accepted target/policy and AI-worker-runtime packages at canonical main
`529001694c6d41ee819736293418cebfe455c392` and changes only the
`adaptive_model_portfolio_and_economics` module plus its direct contract,
registry, tests, and descriptive evidence closure.

## Frozen objective

- every large-model API remains disabled unless API mode is explicit;
- repository-external local configuration owns ordered provider and requested
  model selection;
- no key-presence or credential-value field exists in the portfolio input;
- disabled, unconfigured, unfunded, missing-key, invalid-key, expired-key,
  quota, rate-limit, or unavailable routes may be skipped;
- inactive or expired authorization, stale policy or source preconditions,
  cancellation, missing fake-I/O evidence, transfer denial, and hard-budget
  failures block without provider bypass;
- operator order is preserved and repository economics cannot replace the
  externally selected priority;
- a moving alias remains the requested model identity and creates no exact
  version completion gate;
- one eligible route is selected and an exhausted set returns
  `NO_AVAILABLE_PROVIDER`;
- the exact provider/model catalog and matrix remain compatibility-only, while
  the P15D corpus and existing integer economics remain unchanged;
- no live route, P15 acceptance, P16 entry, or final smoke is authorized.

## Implemented portfolio boundary

`provider_mode.py` accepts one immutable caller-owned snapshot. Disabled mode
returns `API_DISABLED` before evaluating activation controls. Enabled mode
requires active authorization, current policy and source preconditions, a
non-empty attempt envelope, and a positive total budget. Each route contains
only bounded non-secret provider/model identifiers, enablement, an availability
classification, transfer permission, fake-I/O evidence, integer budget and
reservation, logical duration, and strength rank.

The selector evaluates all routes without credentials, transport, filesystem,
process, or network access. Availability-only conditions become recorded
skips. Hard controls become `BLOCKED` and cannot be bypassed by another
provider. Otherwise the first eligible route in the external order is selected,
bounded failover and stronger-route plans are returned, and no dispatch
authority is granted. Failure control accepts this selected decision while
retaining its existing zero-I/O failover, repair, escalation, cancellation,
no-progress, isolation, rollback-plan, and integer economics semantics.

The former exact catalog router and frozen P15C packet are not deleted or
rewritten. They remain readable only for legacy schema and historical fixture
compatibility and do not define current project-completion gates.

## Preserved controls

All-API default-off behavior, external credentials, explicit authorization,
expiry state, provider transfer permission, total and per-provider budgets,
bounded attempts and retries, cancellation, deterministic evidence, redacted
audit inputs, hard-control non-bypass, and Hosted CI fake-I/O-only behavior stay
fail-closed. This module still has no filesystem, Git, network, credential-store,
billing-store, benchmark-store, downstream, mutation, production, cleanup, or
rollback capability.

## Validation and zero-operation evidence

The sealed exact 15-path candidate passed 167 focused
owner/consumer/governance tests and 745 full-repository tests. Python
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
