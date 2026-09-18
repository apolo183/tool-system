# TS-H02 recovery verification binding repair

Reasoning: Extra high

Base: `cf696a62c14fbc70cd6204653179d3dbb9b8897e`

Base tree: `ab80752dc398de9b1428e3d634e82ee2933d037a`

`plan_restore()` previously accepted any PASS verification with any supplied
manifest. This correction binds verification to the complete ordered manifest
before a ready restore plan can be returned. It remains a pure, non-executing
planner; P16 reacceptance and real restore authority remain closed.

## Alignment and scope

The direct requirement is TS-H02 in
`docs/reports/independent_audit_acceptance_reopen_v1.md`. The existing module
contract already requires exact-set content-addressed verification and rejection
of ambiguous identities. The global parent is
`blueprint/tool_system_v0.yaml:product_objective`: bounded recovery decisions must
use evidence for the object actually being planned.

The active task manifest and change plan are
`docs/reports/ts_h02_recovery_binding_v1_task.yaml` and
`docs/reports/ts_h02_recovery_binding_v1_plan.yaml`. The user's standing instruction
authorizes autonomous ordinary development and publication up to a necessary
intervention or major milestone. This is one source correction, with a 90-minute
ceiling, two repair cycles, two full regressions, one branch and one PR maximum.
The original eight-path allowlist is unchanged; six paths actually change. The
formal module contract and registry are KEEP after author review. Previous tasks,
source packages, CI receipts and budgets are not reopened.

## Result and compatibility

`BackupVerification` gains optional `manifest_sha256=None` after its existing
fields. Existing two-argument construction still works, but an unbound result
returns `BACKUP_VERIFICATION_UNBOUND`. `verify_backup()` fills the binding for
both PASS and BLOCKED results. A digest mismatch returns
`BACKUP_MANIFEST_IDENTITY_MISMATCH`. Any denial has an empty restore order and
`execution_authorized=false`; nonempty failure reasons also prevent a PASS
result from being used.

The digest is SHA256 of the ASCII domain prefix
`tool-system-backup-manifest-v1\n` followed by JSON with sorted object keys,
compact separators, ASCII escapes and NaN prohibited. It covers
`format_version`, `state_version`, `snapshot_at_utc`, `source_seal_sha256` and
ordered `entries`, each with `logical_name`, `sha256` and `byte_length`.
Manifest order is bound because it controls restore order. Observation order is
not part of the identity; separately reconstructed equal manifest values work.

The public function signatures and module/interface versions remain unchanged.
The direct production-readiness consumer imports status enums only and requires
no source change. Existing migration gating and non-live RPO/RTO calculations
are preserved. The formal contract's existing ambiguous-identity rejection is
being implemented, not relaxed.

This unkeyed digest binds caller-supplied metadata. It does not authenticate the
caller or observations, read physical backup bytes, establish backup durability,
or grant execution authority. Those are not claims of this correction.

## Verification

Before production-source edits, the new manifest-substitution and unbound-PASS
assertions produced **11 failures in 0.09 seconds**, demonstrating acceptance of
an unrelated or unbound verification. The first repaired focused suite passed
**61 tests in 2.40 seconds**, covering recovery planning, state migration,
production readiness and phase-alignment boundaries.

The first full run produced **1111 passes and one failure in 138.95 seconds**.
The failure was the registry's fixed raw SHA256 seal after explanatory changes
to the module contract and registry. Review confirmed the original contract
already states the needed fail-closed identity requirement, so both formal files
were restored exactly to the base and kept. Their tests and seals were not
modified, and the file scope was not expanded. Encoding details are documented
here instead. Production source and recovery tests were unchanged by this
in-scope documentation correction.

Final full regression: **1112 passed in 136.65 seconds**, including the installed-distribution test and the focused tests above. Their counts are not added together.

Final governance and scope verification: all four current-source validators PASS; the explicit task pair, whitespace check and six-file diff within the original eight-path allowlist PASS. No test, declaration or registry seal was weakened.

The existing interpreter was reused without dependency installation. Initial
standalone governance invocations resolved an older editable checkout; they were
repeated with `PYTHONPATH=src` and the current import root asserted. The current
four validators passed. Pytest uses the current repository's `pythonpath=src`.
Final evidence is tied to the candidate bytes, not the initial editable result.
Author review is not represented as independent review.

## Remaining boundary and rollback

The new project-state record describes this correction separately from the
sealed historical audit and acceptance snapshots. P16D and dependent acceptance
remain false. TS-B02 real isolation, lifecycle control, deadline, full cleanup
and runtime entry remain separate blocked work. Real Worker/provider calls,
DGX/backend effects, backup/restore, deployment, historical data migration,
branch deletion and rollback execution are zero.

`real_repository_execution_blocked=true`.

The task retains the base, exact diff and command evidence. A later rollback can
revert the published source change under its own authorization. Publication and
CI facts are recorded in the PR and external receipt; this source report does
not prefill a future PR number, commit or main CI result.
