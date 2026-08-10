# Subscription Worker Public-Entry Closure Specification v1

## Decision

The subscription-primary Core is not publicly reachable until one formal tool-system CLI path composes the accepted blueprint compiler, repository context, task graph, bounded development loop, worker adapter, isolated workspace, validation/review, and local Git modules. Existing no-mutation role planning and fixture-only process execution remain valid evidence but are not that closure.

## Required public flow

```text
approved blueprint + exact repository snapshot + manifest/change-plan authority
  -> compile bounded task graph
  -> freeze closure contract
  -> select subscription worker route
  -> create isolated workspace
  -> dispatch one injected subscription-worker adapter
  -> apply only structured allowed-scope patch
  -> test / bounded diagnose-repair / independent reviews
  -> seal accepted candidate
  -> create bounded local branch and commit
  -> emit audit and draft-PR plan
```

The formal entry must be an extension of an existing public CLI, not a demonstration-only parallel CLI.

## Subscription worker interface

The provider-neutral interface accepts only structured request metadata: task identity, role, repository-context digest, allowed paths, acceptance digest, finite token/time/cycle budgets, cancellation handle, workspace identity, and requested output schema. It returns structured patch, evidence, usage/capacity metadata, and a stable terminal status.

The Codex CLI adapter is repository-external executable configuration. Its existence does not authorize execution. It must use an argument vector without a shell, an owner-approved executable identity, a minimal environment, no credential extraction, no browser automation, no API key dependency, bounded stdout/stderr, timeout and process-group cancellation, and redacted audit evidence. ChatGPT Web remains an owner-operated subscription route and is not scraped or automated.

## Authority and effects

Default execution remains disabled. A current manifest/change-plan pair must authorize the exact public entry, repository snapshot, isolated workspace, allowed paths, validation set, budgets, and local-Git effect. Remote push, PR creation, Ready, merge, deployment, production, cleanup, rollback, real downstream access, and all API calls remain separate actions.

API providers—including funded providers—remain optional, default-off plugins behind `AIWorkerProvider`. Funding, keys, proxy variables, or credentials never authorize a call and never gate this milestone.

## Implementation packages

1. `SUBSCRIPTION-WORKER-ADAPTER-v1`: versioned interface, Codex subprocess adapter, injected fake process, cancellation and audit tests.
2. `SUBSCRIPTION-WORKER-PUBLIC-ENTRY-INTEGRATION-v1`: compose the existing public CLI with repository context, compiler, task graph, development loop, adapter and local Git.
3. `SUBSCRIPTION-WORKER-MULTI-STACK-ACCEPTANCE-v1`: isolated Python and TypeScript fixtures covering implementation, failing-test repair, scope denial, cancellation, replay, and local commit.
4. `SUBSCRIPTION-WORKER-PUBLIC-ENTRY-ACCEPTANCE-v1`: read-only closure decision. Real downstream execution remains separately authorized.

## Acceptance matrix

- Default invocation performs no external worker call and no mutation.
- Fake Codex process proves exact argv, minimal environment, bounded output, timeout and cancellation.
- Public CLI reaches the injected adapter only after all current authority and snapshot gates pass.
- Out-of-scope patches, symlink escapes, stale repositories, repeated no-progress states, and unsealed candidates fail closed before local Git commit.
- Successful isolated fixtures create exactly one bounded local commit and no remote effect.
- Hosted CI uses fake process and fake repositories only.
- API mode remains disabled and provider invocations remain zero.
