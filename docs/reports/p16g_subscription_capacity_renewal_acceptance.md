# P16G Subscription Capacity and Renewal Review Acceptance

Status: core non-live subscription-capacity contract implemented; purchase, renewal, account inspection, and channel switching remain unauthorized.

The subscription-capacity module evaluates caller-supplied ChatGPT Web and Codex CLI capacity snapshots using deterministic integer PPM thresholds, explicit enablement, reset and renewal chronology, and owner-gated channel recommendations.

It reads no account, calls no provider, purchases or renews nothing, switches no channel, and grants no external authority. Disabled or exhausted channels fail closed. Renewal proximity only produces a review requirement.

Focused tests cover healthy, conserve, block, disabled, renewal-review, deterministic portfolio choice, invalid snapshots, duplicate channels, and false authority. Registry, contract, import DAG, repository manifest, focused, and full Hosted CI form the acceptance boundary.

Real account inspection, purchasing, renewal, plan changes, channel switching, API capacity, credentials, and external billing require separate authorization. P16 remains unaccepted. The next package is P16H operator runbook and production readiness.
