# Model Provider Portfolio and Economics Contract v1

## Metadata

- repo_rel_path: `docs/model_provider_portfolio_and_economics_contract_v1.md`
- role: active roadmap and product-control contract for provider/model selection and development economics
- status: `ROADMAP_CONTRACT_ACTIVE_NO_RUNTIME_CLAIM`
- module_id: `adaptive_model_portfolio_and_economics`
- module_version: `1`
- public_interface_version: `1`
- blueprint_objective_ref: `blueprint/tool_system_v0.yaml:product_objective`
- authority_scope: tool-system only
- created_at: 2026-07-13 UTC+09:00
- updated_at: 2026-08-06 00:21 UTC+09:00

## 1. Outcome and authority boundary

Supported ChatGPT/Codex subscription mode is the ordinary development route.
Every metered large-model API is a dormant backup route and is disabled by
default, including OpenAI, DeepSeek, Qwen, and future providers. Subscription
access is not API credit and must not be automated by browser-session scraping
or authentication-material extraction.

When an operator explicitly enables API mode, tool-system supports replaceable
provider adapters and selects only among routes enabled by repository-external
configuration. The optimization target remains expected total economic cost per
accepted module, with critical-path completion time treated as the largest
configurable economic driver after all hard constraints pass.

This contract records the product target and successor roadmap. It does not
implement a provider, call a live model, authorize a credential, mutate a target
repository, authorize P15 or P16 phase entry, or authorize production deployment.
The accepted P14C historical proof remains valid evidence only; it does not make
any API a daily route or default-enabled provider.

Safety, output quality, data handling, authorization, and repository boundaries
are hard constraints. No cost or schedule advantage may override them.

## 2. Durable module and interface boundary

The durable portfolio module has one responsibility: when API mode is explicitly
enabled, select an eligible authorized provider/model route from the operator's
repository-external enabled-route snapshot and record evidence needed to improve
later selections. Its public inputs are a structured task profile, an
authorization envelope, enabled-route metadata, private billing and economics
references, and current benchmark/health evidence. Its public outputs are a
route decision, skipped-provider dispositions, a bounded failover/escalation
plan, a stable stop reason, evidence references, and an economic outcome record.

The module has no authority to execute its selected route. Execution remains an
independent worker-runtime responsibility and must revalidate the authorization
envelope immediately before each external side effect.

The replaceable surface is:

```text
adaptive_model_portfolio_and_economics
├── TaskComplexityAssessorAgent     # advisory structured task profile
├── DeterministicProviderRouter     # final policy-owned route decision
├── ModelPortfolioOptimizer         # benchmark and economics proposals
└── AIWorkerProvider adapters       # independently replaceable providers
    ├── CodexChatGPTProvider        # supported subscription surface, daily route
    ├── OpenAIApiProvider           # API credential reference and token billing
    ├── DeepSeekApiProvider         # candidate domestic metered API
    ├── QwenApiProvider             # candidate domestic metered API
    ├── GlmApiProvider              # candidate domestic metered API
    ├── KimiApiProvider             # candidate domestic metered API
    └── LocalModelProvider          # future local inference, including DGX
```

The names above are portfolio candidates, not enabled routes. The API candidates
are not completion dependencies. Every provider-specific adapter must implement the versioned
`AIWorkerProvider` boundary and pass injected fake-I/O contract tests. Adding,
enabling, skipping, or replacing an adapter must not require unrelated modules
to change. A ChatGPT/Codex adapter may use only a supported product authorization
surface; it must not scrape a browser session, extract a private token, or treat
a subscription as API credit.

The runtime module contract keeps the following boundaries explicit:

- input and output schemas;
- stable error semantics;
- network, credential, data-residency, and retention policy;
- externally visible side effects;
- task-class capability and risk floors;
- time, token, monetary, retry, and cancellation limits;
- benchmark, rollback, replacement, and expiration evidence;
- upstream worker contract and downstream audit/economics interfaces.

## 3. Credential and public-repository contract

The public repository stores provider IDs, credential-reference schemas, policy,
disabled examples, redacted evidence, and fake-I/O validation fixtures only. It
never stores API keys,
ChatGPT/Codex authentication material, cookies, bearer tokens, raw credential
values, private billing records, or private operating-cost values.

Each installation supplies its own credentials and subscription context through
an approved external secret store or operator environment. Provider and model
selection also comes from repository-external operator configuration. The
presence of a key never enables API mode, enables a provider, creates a budget,
opens data transfer, or grants call authority. Logs and audit records contain
references and redacted metadata only. A public user cannot consume the
repository owner's quota unless the owner separately exposes a credential,
authenticated service, or CI secret; those exposures are prohibited by default.

Every live API call requires all of the following to be affirmative at dispatch:

- the global API switch;
- the selected provider switch;
- the current authorization and unexpired execution window;
- a nonzero bounded provider budget and shared budget capacity;
- the exact current data-transfer permission;
- a resolvable credential reference without logging its value;
- token, time, retry, cancellation, redaction, and source-precondition controls.

## 4. Task profile and deterministic decision contract

`TaskComplexityAssessorAgent` produces an advisory structured profile. At minimum
the profile records:

- task class, language, repository context size, and dependency breadth;
- reasoning and implementation complexity;
- security, data, repository-mutation, and operational risk independently from
  complexity;
- required capabilities and minimum quality/confidence floor;
- expected verification and repair burden;
- critical-path status, remaining slack, and delay sensitivity;
- evidence confidence and reasons for uncertainty.

The assessor cannot choose its own execution authority, lower a risk floor, add
a credential, or activate a provider. A deterministic policy engine makes the
final route decision from the advisory profile and the repository-external
enabled-route snapshot. The same inputs and policy version must reproduce the
same route decision.

Selection is per task class, not by one global model ranking. The router chooses
the eligible route with the lowest expected total economic cost subject to all
hard constraints. A smaller or cheaper model is tried first only when it meets
the capability, risk, quality, data, time, and authorization floors. Uncertainty
or high risk may require a stronger minimum route even when estimated complexity
is low. Public source never hard-codes a mandatory provider/model. If API mode is
off, no API route is considered.

## 5. Failover, repair, escalation, and stop semantics

Provider availability and model quality are different failure classes:

1. An unconfigured, unfunded, invalid, expired, or unavailable provider is
   recorded as skipped. Missing credential, insufficient balance, quota
   exhaustion, rate limiting, timeout, or provider outage may trigger bounded
   availability failover only to the next already enabled, eligible, and
   authorized route. The replacement need not be a stronger model.
2. A valid response that fails quality or acceptance checks receives a bounded
   same-route repair attempt when policy permits, followed by evidence-backed
   escalation to a stronger eligible route.
3. Policy denial, unauthorized data transfer, authorization mismatch, hard budget
   exhaustion, stale precondition, or missing required evidence blocks execution.
   Switching providers may not bypass the block.
4. API mode disabled returns a stable disabled outcome. An enabled API mode with
   an empty eligible set returns `NO_AVAILABLE_PROVIDER`. Exhausted
   attempt/time/cost envelope, cancellation, or no-progress returns a stable
   blocked or failed outcome.

Every attempt records an idempotency key, attempt number, the provider/model
actually requested, enabled-route and policy versions, precondition snapshot,
bounded usage, redacted error class, validation outcome, and reason for skip,
failover, escalation, or stop. Target-repository mutations remain governed by
their independent action-scoped approvals.

## 6. Model qualification and lifecycle contract

Provider and model discovery may be automated, but discovery never activates a
route. When an enabled provider exposes an exact immutable model version, evidence
records it. When a provider exposes only a moving model identifier, public source
does not invent or pin a nonexistent exact version; the audit records the
requested identifier and dated response metadata. A moving alias is not a
project-completion blocker.

The following optional states are scoped only to enabled provider-model portfolio
qualification. They do not alter tool-system phase, milestone, task, or module
lifecycle values:

```text
DISCOVERED -> QUARANTINED -> BENCHMARKING -> SHADOW -> CANARY
           -> ELIGIBLE -> PRIMARY
           -> DEGRADED -> RETIRED
```

Promotion of an enabled reusable route requires compatible data policy, current
authorization, task-class evidence, reliability evidence, economics evidence,
and an explicit policy decision. A newly released higher-numbered or temporarily
cheaper model does not skip those controls. A model that repeatedly fails one
task class is demoted or removed from that class and may remain eligible for
other classes while current evidence meets their floors. Audit and Git evidence
remain available for diagnosis and rollback.

An enabled-route snapshot records provider, execution surface, the configured
model identifier, capability tags, eligible task classes, context and output
limits, availability, quota, price snapshot, data policy, benchmark results,
confidence, qualification state, effective and expiration times, and replacement
relationship when known. It remains repository-external operator input. The
public repository may retain redacted fixtures but does not select the live
provider/model for an installation.

## 7. Economic objective

The primary soft objective is:

```text
minimize expected_total_economic_cost_per_accepted_module
```

Expected total economic cost includes, without double counting:

- enabled-provider token/request charges and other metered usage;
- avoidable future subscription renewal caused by critical-path delay;
- allocated personnel, rent, and other operating burn during critical-path time;
- local compute depreciation allocation, electricity, and infrastructure usage;
- expected retry, review, rework, failure recovery, rollback, and incident cost;
- expected critical-path delay and lost-revenue or opportunity cost;
- verification cost required to reach an accepted module rather than merely
  produce an answer.

A prepaid, non-refundable amount already committed for the current billing
period is sunk for the current decision. A later renewal that becomes necessary
because completion crosses the billing boundary is avoidable step cost and must
be modeled. Subscription capacity already paid for may have near-zero marginal
usage cost, but it is not unlimited and its plan limits, availability, and delay
risk remain explicit. Disabled or skipped APIs incur no assumed live usage cost.

Only critical-path delay, or delay that consumes enough slack to become critical,
gets the full time-cost weight. Faster completion of a non-critical task is not
credited as equivalent project acceleration. Private currency amounts, salary,
rent, electricity rates, revenue assumptions, subscription renewal dates, and
weights are installation configuration supplied through private references; they
must not be hard-coded in this public repository.

## 8. Recalculation and portfolio maintenance cadence

API portfolio maintenance runs only when API mode is explicitly enabled. An
operator may configure event-driven discovery and health/price refresh,
lightweight availability and economic recomputation, changed-route incremental
fake or live benchmarks, task-class portfolio review, and pre-renewal forecast
review. The public repository does not impose a 24-hour, 72-hour, weekly, or
monthly live-call requirement.

An outage, security advisory, material price change, or severe regression still
triggers immediate review for enabled routes. Any enabled-route publication is
versioned and atomic, with rollback to the last accepted snapshot. When API mode
is disabled, these operations are skipped and do not block project completion.

## 9. Roadmap ownership

- P14 remains provider-neutral autonomous blueprint-to-code development plus one
  accepted bounded historical provider proof. It does not make that API a daily
  route or grant current execution authority.
- P15 owns multi-project core evidence, provider-specific fake-I/O adapter
  qualification, task profiling, bounded failover/escalation evidence,
  total-economic-cost comparison, and release-candidate acceptance. The final
  controlled single-provider live smoke belongs to an independent optional API
  plugin release, may be completed after the core product, and is not a P15 core
  or P16 entry gate. Simultaneous multi-provider availability, Qwen funding, and
  a provider's moving model alias are not acceptance gates.
- P16 owns sustainable observability, incident response, release and recovery
  operations. Discovery, health/price refresh, portfolio lifecycle, and renewal
  forecasting are conditional on API mode being enabled and are not default-off
  acceptance gates.

Each stage must still satisfy the durable-module, parent-alignment, global-
objective-alignment, authorization, evidence, and replacement rules. P15 and P16
remain roadmap-only until separately authorized.

## 10. Acceptance and stop condition for this contract

This documentation milestone is accepted only when the blueprint, README,
AGENTS.md, global principles, and machine alignment tests agree on the product
target and authority boundary: subscription mode is the daily route; every API is
default-off backup; key presence is not authority; provider/model selection is
repository-external; unavailable providers may be skipped; all adapters require
fake-I/O; and one live usable key is sufficient for the final backup-path smoke.
Its stop condition is the documented roadmap and green contract tests. Runtime
implementation, external credentials, live model calls, target-repository
mutation, cleanup, rollback, P15 acceptance, P16 entry, and production deployment
are outside this change.
