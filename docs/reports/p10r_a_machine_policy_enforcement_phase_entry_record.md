# P10R-A Machine Policy Enforcement Phase Entry

status: PHASE_ENTRY_APPROVED_PACKET_PREPARATION_ONLY
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
parent: docs/reports/p10q_finance_us_final_post_merge_closure.md
created_at: 2026-07-11 UTC+08:00

## Decision

The user approved preparation of the P10R-A phase-entry record, implementation packet, task manifest, change plan, and active-gate registration in tool-system only.

```text
P10R_A_phase_entry_decision: APPROVED
authorized_scope: tool_system_packet_preparation_only
policy_or_source_mutation_authorized: false
finance_us_mutation_authorized: false
cleanup_authorized: false
PR_ready_authorized: false
PR_merge_authorized: false
```

## Locked current state

```text
repository: apolo183/tool-system
main: 8a7c28e92b83dbd1a8fac9e701f311c4b73094fe
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
phase_status: accepted
successor_phase_authorized: false
finance_us_main: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
finance_us_P1B_target_implementation_authorized: false
```

## Evidence-backed correction need

Current policy and controller evidence shows that:

- the active target-repository policy still names `apolo183/finance-os` and `src/finance_os/**` while the approved future P1B packet names `apolo183/finance-us` and `finance_us/**`;
- `bootstrap_direct_main_allowed` is declared in policy data but is not enforced by the current repository-policy validator;
- path allowlists are currently collected across mode-specific keys instead of being selected by write mode;
- the autonomy-policy validator requires `file_cleanup`, `pr_ready`, and `pr_merge` to be system-handled;
- the merge controller does not consume a scoped autonomy or named PR-lifecycle approval;
- the current action implementation supports squash merge but not a ready transition.

These findings require a bounded machine-policy correction before finance-us P1B target execution or a successor tool-system phase.

## P10R-A objective

Prepare a separately approvable implementation contract that will make repository identity, mode-specific path controls, bootstrap closure, approval scope, and downstream PR-lifecycle boundaries machine-enforced and test-protected.

P10R-A is corrective work under the accepted P10 boundary. It does not authorize P11, finance-us P1B implementation, production deployment, cleanup, rollback, or external worker execution.

## Current authorized artifacts

- this phase-entry record;
- `docs/reports/p10r_a_machine_policy_enforcement_implementation_packet.md`;
- `examples/task_manifests/tool_system_p10r_a_machine_policy_enforcement_packet.yaml`;
- `examples/change_plans/tool_system_p10r_a_machine_policy_enforcement_packet.yaml`;
- registration of that manifest and change plan in `examples/active_gates.yaml`.

## Residue disposition

```text
branch: dummy-unused
content_delta: none
disposition: retain_pending_cleanup_approval
cleanup_authorized_by_this_stage: false
```

## Stop condition

After one tool-system draft PR contains exactly the five authorized packet artifacts and CI evidence is collected, stop. Do not modify existing policy or source code, do not touch finance-us, and do not mark ready or merge.