# P15D prerequisite failure-control fixture implementation

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NON_EXECUTING_PREREQUISITE_FIXTURE`

This record describes one project-neutral, pure in-memory implementation that
uses the already frozen public failure/economics corpus as deterministic test
input. It does not enter or accept P15D, does not reclassify fixture evidence as
P15C evidence, and does not weaken the blueprint requirement that P15C must be
accepted before P15D begins.

## Frozen baseline and single-module boundary

- repository: `apolo183/tool-system`
- canonical baseline: `ca04839ec96009fe6a4205b8a0d99794c7531cce`
- canonical tree: `da1ce6dd7885a96a0bc1dc3a405a351debef0366`
- durable module: `adaptive_model_portfolio_and_economics` `1.2.0` to `1.3.0`
- aggregate interface: `adaptive-model-portfolio-and-economics-api` `1.0.0`
  unchanged
- natural owner added:
  `src/tool_system/provider_portfolio/failure_control.py`
- frozen prerequisite corpus modified: false

The implementation is an interface-compatible extension of the existing
portfolio module. It imports the accepted route-decision and failure-policy
types, consumes caller-owned immutable values, returns content-addressed plans,
and performs no filesystem, Git, process, YAML, credential, network, provider,
repository, or external-system operation.

## Deterministic fixture behavior

The failure-control planner keeps five actions distinct: availability failover,
same-route repair, stronger-route quality escalation, hard block without
provider bypass, and terminal stop. Every result is a plan only:
`dispatch_authorized` and `candidate_application_authorized` remain false.
Cancellation stops before either operation, and exhausted attempt envelopes do
not silently add another route.

Cycle observations content-address only the frozen task digest, candidate tree,
acceptance digest, blocker set, and validation results for recurrence. Attempt
number, satisfied-item bookkeeping, material-result bookkeeping, timestamps,
receipts, PR metadata, and status text do not change that fingerprint. A
repeated fingerprint or two consecutive completed no-progress transitions
returns the corresponding stable stop code.

The isolation planner stops the failed module output, pauses only the supplied
affected downstream closure, and preserves the supplied unrelated modules. It
adds no lifecycle status and keeps rollback and cleanup execution false.

The economics fixture accepts exactly ten non-negative integer microUSD
components, reconciles the frozen synthetic total of 17,000 microUSD, and
selects the lowest total only after the caller's hard-floor result is true. A
cheaper unqualified route is never selectable.

## Entry gate remains closed

The frozen corpus remains unchanged and non-authorizing. Accepted cross-provider
read-only benchmark evidence, exact redacted OpenAI/Qwen evidence, and accepted
real-repository read-only evidence are still missing. Therefore P15C remains
unaccepted, P15D remains unentered and unaccepted, and P15E remains
unauthorized. Funding and live execution are not required for this offline
prerequisite fixture and are not treated as resolved.

## Validation and terminal boundary

The candidate must pass exact task-pair validation, the focused failure-control,
corpus, existing portfolio, module-contract, import-graph, module-registry,
repository-manifest, phase-state, and repository-context suites, the full pytest
suite, Python compilation, Ruff 0.16.0, exact thirteen-path and forbidden-diff
checks, secret and project-neutrality scans, Hosted CI, and unchanged
base/head/scope guards before Ready and squash merge.

Local candidate validation completed with 149 focused tests and 700 full-suite
tests passing. Task-manifest, change-plan, active-gates, process-authority,
module-registry, and repository-manifest validators passed. Python compilation,
Ruff 0.16.0 checks, exact-scope, forbidden-diff, secret-pattern, frozen-corpus,
and project-neutrality checks passed. Hosted CI and lifecycle guards remain the
publication-time conditions rather than local claims.

- provider_invocations: 0
- credential_resolver_invocations: 0
- credential_value_accesses: 0
- network_operations: 0
- private_target_reads: 0
- target_repository_accesses: 0
- target_mutations: 0
- benchmark_executions: 0
- production_operations: 0
- cleanup_operations: 0
- rollback_operations: 0
- p15c_stage_accepted: false
- p15d_stage_entered: false
- p15d_stage_accepted: false
- p15e_authorized: false

After guarded merge, this fixture remains non-authorizing reusable module
capability. Formal P15D entry still waits for actual P15C acceptance.
