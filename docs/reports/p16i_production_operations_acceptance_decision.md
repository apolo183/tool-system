# P16I Production Operations Acceptance Decision

Decision on guarded merge: `accepted_subscription_primary_sustainable_operations_core`.

## Accepted boundary

P16 Core accepts the sustainable-operations capability of the subscription-primary product route: ChatGPT Web and Codex CLI remain the ordinary mainline. P16B through P16H provide deterministic, non-live, fail-closed release governance, state-migration planning, backup/restore and disaster-recovery planning, observability/SLO/incident policy, audit/run retention policy, subscription-capacity review, and the versioned operator runbook with a production-readiness review interface.

The P16H interface reaches only `READY_FOR_P16_ACCEPTANCE_REVIEW`; this separately authorized P16I decision converts the complete current canonical evidence set into the P16 Core acceptance record. The exact sixteen-output disposition is frozen in `docs/reports/p16_final_acceptance_mapping_v1.yaml`: nine Core outputs are accepted, six API-mode-only outputs remain conditionally deferred, and this document supplies the final decision record.

## Evidence closure

The accepted evidence is the current canonical P16B through P16H reports, their registered module contracts and public interfaces, the validated dependency DAG, fail-closed negative cases, and full Hosted CI. PR #203 at head `e48d7c2cda714c5fe578333eb5110b5c084f8c8c` changed exactly nineteen paths, passed Hosted CI run 1199, squash-merged as `02699469bf96024bb481980712d47494a4ef08ff`, and its feature branch was restored and retained.

The prior P16H project-state phrase `core_non_live_runbook_and_readiness_contract_implemented_pending_hosted_ci` was stale descriptive metadata. It is corrected to `merged_hosted_ci_passed_ready_for_p16_acceptance_review`; the stale text is not treated as a capability defect and does not reopen the sealed P16H source.

## Optional API disposition

Every large-model API remains disabled by default. OPTIONAL-API-PROVIDER-PLUGIN-v2 remains an independent, deferred, unreleased module and is not a P16 Core acceptance gate. Disabled, unavailable, unfunded, unconfigured, invalid, or unreleased API routes do not block this acceptance.

## Non-claims and stop boundary

This acceptance grants no production deployment, production operation, real-environment validation, provider call, credential access, live smoke, benchmark, downstream access, backup/restore drill, disaster-recovery drill, cleanup, or rollback authority. No such operation occurred in this package.

Successful publication closes P16 Core and stops before every production deployment, real-environment validation, or OPTIONAL-API-PROVIDER-PLUGIN-v2 implementation action. Each remains a separately authorized future lifecycle.
