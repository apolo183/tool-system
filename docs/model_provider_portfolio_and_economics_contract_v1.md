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

## 1. Outcome and authority boundary

tool-system will support a replaceable portfolio of authorized worker providers,
select a provider/model route from task complexity, risk, benchmark evidence, and
expected total economic cost, and adapt that route from recorded outcomes. The
optimization target is the expected total economic cost per accepted module,
with critical-path completion time treated as the largest configurable economic
driver.

This contract records the product target and successor roadmap. It does not
implement a provider, call a live model, authorize a credential, mutate a target
repository, authorize P15 or P16 phase entry, or authorize production deployment.
P14C still requires its separately named provider, model, network, credential
reference, token/time/cost, retry/cancellation, and redaction execution packet.

Safety, output quality, data handling, authorization, and repository boundaries
are hard constraints. No cost or schedule advantage may override them.

## 2. Durable module and interface boundary

The durable module has one responsibility: qualify and select an authorized
provider/model route and record evidence needed to improve later selections. Its
public inputs are a structured task profile, an authorization envelope, a
versioned provider/model catalog snapshot, private billing and economics
references, and current benchmark/health evidence. Its public outputs are a
route decision, bounded failover/escalation plan, stop reason, evidence
references, and an economic outcome record.

The module has no authority to execute its selected route. Execution remains an
independent worker-runtime responsibility and must revalidate the authorization
envelope immediately before each external side effect.

Candidate natural-owner boundaries for later implementation are:

```text
adaptive_model_portfolio_and_economics
├── TaskComplexityAssessorAgent     # advisory structured task profile
├── DeterministicProviderRouter     # final policy-owned route decision
├── ModelPortfolioOptimizer         # benchmark and economics proposals
└── AIWorkerProvider adapters       # independently replaceable providers
    ├── CodexChatGPTProvider        # supported ChatGPT/Codex authorization surface
    ├── OpenAIApiProvider           # API credential reference and token billing
    ├── DeepSeekApiProvider         # candidate domestic metered API
    ├── QwenApiProvider             # candidate domestic metered API
    ├── GlmApiProvider              # candidate domestic metered API
    ├── KimiApiProvider             # candidate domestic metered API
    └── LocalModelProvider          # future local inference, including DGX
```

The names above are portfolio candidates, not enabled routes. Every adapter must
implement the existing versioned `AIWorkerProvider` boundary. Adding, enabling,
or replacing an adapter must not require unrelated modules to change. A
ChatGPT/Codex adapter may use only a supported product authorization surface; it
must not scrape a browser session, extract a private token, or treat a ChatGPT
subscription as API credit.

The later runtime module contract must make the following boundaries explicit:

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
redacted examples, and validation fixtures only. It never stores API keys,
ChatGPT/Codex authentication material, cookies, bearer tokens, raw credential
values, private billing records, or private operating-cost values.

Each installation supplies its own credentials and subscription context through
an approved external secret store or operator environment. Logs and audit records
contain references and redacted metadata only. A public user cannot consume the
repository owner's quota unless the owner separately exposes a credential,
authenticated service, or CI secret; those exposures are prohibited by default.

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
final route decision from the advisory profile and the exact catalog snapshot.
The same inputs and policy version must reproduce the same route decision.

Selection is per task class, not by one global model ranking. The router chooses
the eligible route with the lowest expected total economic cost subject to all
hard constraints. A smaller or cheaper model is tried first only when it meets
the capability, risk, quality, data, time, and authorization floors. Uncertainty
or high risk may require a stronger minimum route even when estimated complexity
is low.

## 5. Failover, repair, escalation, and stop semantics

Provider availability and model quality are different failure classes:

1. Missing credential, insufficient balance, quota exhaustion, rate limiting,
   timeout, or provider outage may trigger bounded availability failover to the
   next eligible authorized route. The replacement need not be a stronger model.
2. A valid response that fails quality or acceptance checks receives a bounded
   same-route repair attempt when policy permits, followed by evidence-backed
   escalation to a stronger eligible route.
3. Policy denial, unauthorized data transfer, authorization mismatch, hard budget
   exhaustion, stale precondition, or missing required evidence blocks execution.
   Switching providers may not bypass the block.
4. An empty eligible set, exhausted attempt/time/cost envelope, cancellation, or
   no-progress condition returns a stable blocked or failed outcome.

Every attempt records an idempotency key, attempt number, selected exact model
version, catalog and policy versions, precondition snapshot, bounded usage,
redacted error class, validation outcome, and reason for failover, escalation, or
stop. Target-repository mutations remain governed by their independent action-
scoped approvals.

## 6. Model qualification and lifecycle contract

Provider and model discovery may be automated, but discovery never activates a
route. Model records use exact provider/version identifiers and a dated price and
policy snapshot; moving aliases cannot serve as reproducible acceptance evidence.

The following states are scoped only to provider-model portfolio qualification.
They do not alter tool-system phase, milestone, task, or module lifecycle values:

```text
DISCOVERED -> QUARANTINED -> BENCHMARKING -> SHADOW -> CANARY
           -> ELIGIBLE -> PRIMARY
           -> DEGRADED -> RETIRED
```

Promotion requires compatible data policy, current authorization, task-class
benchmarks, reliability evidence, economics evidence, and an explicit policy
decision. A newly released higher-numbered or temporarily cheaper model does not
skip qualification. A model that repeatedly fails one task class is demoted or
removed from that class and may remain eligible for lower-complexity classes only
when current evidence still meets their floors. An older active route is removed
only after an accepted replacement and atomic route publication. Catalog,
benchmark, audit, and Git history remain available for diagnosis and rollback.

The catalog must record provider, execution surface, exact model ID, capability
tags, eligible task classes, context and output limits, availability, quota,
price snapshot, data policy, benchmark results, confidence, qualification state,
effective and expiration times, and replacement relationship.

## 7. Economic objective

The primary soft objective is:

```text
minimize expected_total_economic_cost_per_accepted_module
```

Expected total economic cost includes, without double counting:

- provider token/request charges and other metered usage;
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
risk remain explicit.

Only critical-path delay, or delay that consumes enough slack to become critical,
gets the full time-cost weight. Faster completion of a non-critical task is not
credited as equivalent project acceleration. Private currency amounts, salary,
rent, electricity rates, revenue assumptions, subscription renewal dates, and
weights are installation configuration supplied through private references; they
must not be hard-coded in this public repository.

## 8. Recalculation and portfolio maintenance cadence

The production roadmap uses layered recalculation rather than constant full
benchmarking:

- event-driven: ingest approved model releases, deprecations, price/policy
  changes, quota changes, and provider-health incidents;
- every 24 hours: recompute lightweight availability, quota, price, critical-path,
  and expected-economic-cost scores;
- every 72 hours: run incremental benchmarks for changed, new, degraded, or
  expiring provider-model records;
- weekly: review task-class routing, failure and repair rates, time-to-acceptance,
  concentration risk, and promotion/demotion proposals;
- before each billing renewal and at least monthly: review completion forecast,
  avoidable renewal cost, capacity alternatives, and cancellation decisions.

All cadence values are policy defaults and may be configured. An outage, security
advisory, material price change, or severe regression triggers immediate review.
Catalog publication is versioned and atomic, with rollback to the last accepted
snapshot.

## 9. Roadmap ownership

- P14 remains provider-neutral autonomous blueprint-to-code development plus one
  separately authorized bounded real-provider proof. It does not claim an
  adaptive multi-provider optimizer.
- P15 owns provider-adapter qualification, task profiling, cross-provider and
  cross-project benchmarks, bounded failover/escalation evidence, total-economic-
  cost comparison, and release-candidate acceptance.
- P16 owns continuous discovery, health/price refresh, portfolio lifecycle,
  renewal forecasting, observability, incident response, and sustainable
  production-operations acceptance.

Each stage must still satisfy the durable-module, parent-alignment, global-
objective-alignment, authorization, evidence, and replacement rules. P15 and P16
remain roadmap-only until separately authorized.

## 10. Acceptance and stop condition for this contract

This documentation milestone is accepted only when the blueprint, README,
AGENTS.md, global principles, and machine alignment tests agree on the product
target and authority boundary. Its stop condition is the documented roadmap and
green contract tests. Runtime implementation, external credentials, live model
calls, target-repository mutation, cleanup, PR readiness/merge, and production
deployment are outside this change.
