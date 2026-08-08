# Tool-System P16 Core Operator Runbook and Deprecation Policy v1

Status: versioned non-production operator procedure. This document grants no P16 acceptance, deployment, production operation, provider call, credential access, cleanup, or rollback authority.

## 1. Scope and authority

This runbook covers the subscription-primary P16 Core. ChatGPT Web and Codex CLI remain the default mainline. OPTIONAL-API-PROVIDER-PLUGIN-v2 remains default-off, independently deferred, and outside the P16 Core hard gate. Any API-specific step applies only after separate repository-external enablement and authorization.

An operator may use this runbook to assemble evidence and obtain an in-memory `READY_FOR_P16_ACCEPTANCE_REVIEW` decision. That result is not P16 acceptance and cannot authorize deployment or production operation.

## 2. Ordered preflight

1. Seal the canonical commit, tree, clean worktree, release version, schema version, and applicable manifest/change-plan identities.
2. Confirm compatibility and deprecation decisions from release governance.
3. Confirm state migration and downgrade decisions are non-executing and either blocked or ready only for separate execution authorization.
4. Verify backup manifest identity and non-live disaster-recovery evidence.
5. Evaluate caller-supplied telemetry against SLO policy; resolve incident evidence to `CLOSED`.
6. Build retention indexes and preserve legal-hold, archival, expiry, and incident-closure gates.
7. Evaluate explicitly enabled ChatGPT Web and Codex CLI capacity snapshots. Capacity observations never authorize renewal, purchase, or channel switching.
8. Evaluate P16 Core operations readiness. Stop if any reason is returned.

## 3. Stop and escalation rules

Stop and require owner review on source-seal drift, incompatible release, blocked migration, failed backup verification, failed recovery evidence, SLO breach, open incident, missing retention index, no eligible subscription channel, missing deprecation evidence, or any unexpected object or state.

No step may silently retry, switch channels, enable an API, access a credential, mutate a downstream repository, deploy, operate production, delete records, restore data, or execute rollback. Each such action requires its own applicable authority.

## 4. Deprecation lifecycle

The only lifecycle is `SUPPORTED -> DEPRECATED -> REMOVED`.

- SUPPORTED: normal compatibility evidence is current.
- DEPRECATED: replacement identity, migration guidance, owner, review date, and removal condition are explicit; existing consumers remain supported within the stated window.
- REMOVED: all affected consumers have current replacement evidence, required migration evidence is complete, and a separately authorized release performs removal.

Skipping a state, silently shortening a window, leaving an unidentified consumer, or treating documentation as execution authority fails closed. An incompatible change requires a new interface version and affected downstream closure revalidation.

## 5. Evidence handoff

The operator retains redacted identities, hashes, statuses, ordered reasons, timestamps, and CI evidence. Private account, subscription, billing, renewal, salary, credential, proxy, or provider data must remain outside the repository.

P16I consumes only the non-live P16 Core evidence and this runbook to form a separate acceptance decision record. Production deployment and real-environment validation remain separately authorized after that decision.
