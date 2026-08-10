# Subscription Worker Task-Runner Pipeline Core v1

This package composes the guarded Codex CLI subscription-worker adapter with the bounded in-memory development loop through the task-runner module. The task runner rejects every other adapter kind before invocation, preserves structured-result-only handling, and returns explicit zero API-provider, provider-credential, target-repository, remote-repository, local-Git, and production effect evidence.

Hosted CI exercises the real guarded adapter with an injected fake subprocess and an in-memory fixture repository. It proves one structured patch reaches validation and independent review, seals the accepted candidate, and proves an optional-API adapter kind is rejected without invocation.

Initial Hosted CI correctly exposed stale module-identity consumer mappings and historical DAG/effect counts; the exact closure includes their descriptive and test-oracle alignment without changing runtime behavior.

This package closes only the task-runner pipeline core. It does not yet provide the formal CLI parser/authority entry, repository-context and blueprint/task-graph composition, isolated filesystem workspace, or bounded local branch and commit. Those remain subsequent packages under the authorized subscription-worker public-entry production-closure lifecycle. No real Codex, API, credential, repository, Git, remote, production, cleanup, or rollback operation occurs.
