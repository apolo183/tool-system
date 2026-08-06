# P16A sustainable-operations acceptance specification

## Decision

P16A is a governance-only inventory. It does not accept P16 and does not grant deployment authority. The baseline is `tool-system@83b6d96a8f81519d5188c00cac8d2a209eac33b4`.

The repository already has credible local safety primitives: a schema-versioned transactional SQLite orchestrator with integrity and recovery operations, bounded redacted audit records, CI observation records, and deterministic fake-I/O provider economics and failure controls. These claims are inherited only at their tested boundaries. They are not production release, fleet migration, backup/restore, SLO, incident-response, retention, or operator-runbook systems.

## Acceptance model

Every P16 blueprint output is classified in `p16a_sustainable_operations_inventory_v1.yaml` as complete inheritable evidence, a primitive not production-closed, a missing natural-owner module/interface, an API-only conditional capability, or work requiring separate production authority. A later package may move an item only by naming its public interface, persistence boundary, failure and recovery semantics, direct tests, and non-live acceptance evidence.

## Core dependency order

1. P16B freezes release, version compatibility, and deprecation contracts.
2. P16C builds product-wide state migration and compatibility planning on P16B.
3. P16D builds backup, restore verification, and disaster-recovery evidence on P16C.
4. P16E defines production-neutral telemetry, SLI/SLO, alerts, and incident state.
5. P16F defines audit/run retention and archival on the observable record model.
6. P16G defines subscription capacity, completion forecast, renewal review, and production-neutral economics.
7. P16H integrates the preceding evidence into the operator runbook and readiness checklist.
8. P16I may form a production-operations acceptance decision; deployment and real-environment validation still require separate authorization.

`OPTIONAL-API-PROVIDER-PLUGIN-v2` is an independent default-disabled branch of work. Provider health refresh, changed-route benchmarks, lifecycle publication, and provider-specific economics apply only when API mode is explicitly enabled. They cannot block P16 Core.

## Production validation boundary

Repository tests may validate deterministic state machines, temporary stores, fake telemetry, fake alerts, synthetic backups, and restore plans. Actual deployment, backup/restore drills, disaster-recovery drills, production alert delivery, real downstream access, provider calls, credential access, cleanup, and rollback are outside P16A and require later explicit authority.

## P16A stop

This package changes no runtime, provider adapter, configuration template, or blueprint. After guarded merge, the next permitted action is a separate user authorization for P16B. P16 remains active and unaccepted; production deployment remains unauthorized.
