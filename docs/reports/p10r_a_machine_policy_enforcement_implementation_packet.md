# P10R-A Machine Policy Enforcement Implementation Packet

status: EXECUTION_APPROVAL_REQUIRED
parent: docs/reports/p10r_a_machine_policy_enforcement_phase_entry_record.md
created_at: 2026-07-11 UTC+08:00

## Locked future target

```text
repository: apolo183/tool-system
implementation_base: fresh main required
proposed_branch: p10r-a-machine-policy-enforcement-implementation
milestone: P10R_A_MACHINE_POLICY_ENFORCEMENT_CORRECTION
write_mode: draft_pull_request
```

This packet grants no implementation or PR-lifecycle authority by itself.

## Single objective

Make the active repository-write and autonomy boundaries machine-enforced so that repository identity, write mode, allowed paths, approval scope, and downstream PR lifecycle cannot pass on stale or declarative-only policy.

Documentation-state synchronization belongs to a later P10R-B stage and is excluded here.

## Root causes to correct

1. The repository policy still authorizes the legacy target identity `apolo183/finance-os` and legacy package path `src/finance_os/**`.
2. `bootstrap_direct_main_allowed` is not evaluated by the natural-owner validator.
3. Mode-specific path lists are combined rather than selected by the requested write mode.
4. The autonomy-policy validator requires cleanup and PR lifecycle actions to be system-handled without repository or action scope.
5. The merge controller does not consume a named, action-scoped downstream lifecycle approval.
6. Manifest structure requires `approval.required: true` but does not itself require a named approver or bind approval to repository, action, branch, or expected head SHA.
7. The policy declares `pr_ready` as system-handled although the current controller action implementation has no ready action.

## Candidate exact future implementation allowlist

Only the following paths may change after a separate implementation approval and a fresh-state reread of every natural owner and test:

```text
docs/reports/p10r_a_machine_policy_enforcement_implementation_packet.md
examples/task_manifests/finance_os_p1b_minimal_ranking.yaml
policy/repo_write_policy.yaml
policy/autonomy_policy.yaml
src/tool_system/manifest/task_manifest.py
src/tool_system/policy/repo_write_policy.py
src/tool_system/policy/autonomy_policy.py
src/tool_system/repo_controller/controller.py
src/tool_system/repo_controller/controller_run.py
src/tool_system/repo_controller/github_state.py
src/tool_system/repo_controller/live_github_collector.py
src/tool_system/cli/controller_run.py
src/tool_system/cli/evaluate_repo_write.py
src/tool_system/cli/evaluate_github_state.py
src/tool_system/cli/validate_task_manifest.py
tests/test_repo_controller.py
tests/test_controller_run.py
tests/test_live_github_collector.py
tests/test_task_manifest_policy.py
tests/test_p10r_a_machine_policy_enforcement.py
```

If fresh-state dependency tracing proves that any listed path is unnecessary, omit it. If an unlisted natural owner is required, stop and revise this packet before writing it.

## Required policy semantics

### Repository identity

- allow the canonical downstream target `apolo183/finance-us`;
- reject the legacy target `apolo183/finance-os` for new work;
- preserve the business-repository role boundary;
- keep tool-system domain-agnostic.

### Write modes and paths

- select allowed paths by the manifest write mode and active phase rather than unioning all allowlists;
- enforce `bootstrap_direct_main_allowed` for `direct_bootstrap`;
- disable obsolete direct-main bootstrap for tool-system and finance-us unless a later named policy-boundary approval explicitly restores it;
- permit `finance_us/**` only inside the applicable finance-us phase envelope;
- continue to require the task manifest and change plan exact file sets as the narrower boundary;
- keep forbidden paths fail-closed.

### Approval scope

A lifecycle approval used by the controller must be named and bound at minimum to:

```text
approved_by
repository_full_name
action
base_branch
expected_head_sha
approval_record_or_reason
```

An approval for packet preparation, target implementation, PR creation, ready transition, merge, cleanup, rollback, or production is not interchangeable with any other action.

### Autonomy and implemented capability

- separate tool-system internal routine PR actions from downstream target-repository actions;
- require explicit approval for downstream target mutation, downstream ready, downstream merge, cleanup, rollback, real external worker execution, and production deployment;
- do not declare `pr_ready` system-handled until a matching implementation and tests exist;
- keep routine tool-system PR automation bounded by valid manifest, change plan, CI, rollback, and active milestone authority.

### Fresh-state merge gate

Immediately before a merge action, re-collect and bind:

```text
repository_full_name
PR number
state
draft state
base branch
head SHA
mergeability
required CI conclusions
named approval action
approval expected head SHA
```

Any mismatch or missing field blocks without fallback.

## Required tests

At minimum, tests must prove:

1. canonical `apolo183/finance-us` is accepted only within its scoped rules;
2. legacy `apolo183/finance-os` is rejected for new manifests;
3. `finance_us/ranking.py` can match the Phase 1 envelope while a path outside the manifest exact allowlist is rejected by plan/manifest validation;
4. `src/finance_os/**` does not remain an active finance-us route;
5. disabled bootstrap blocks `direct_bootstrap` even when the path matches a bootstrap list;
6. bootstrap paths do not leak into pull-request or Phase 1 path evaluation;
7. missing `approved_by` or mismatched repository, action, base branch, or expected head SHA blocks;
8. packet-preparation approval cannot authorize implementation, ready, merge, cleanup, or rollback;
9. target implementation approval cannot authorize target ready or merge;
10. downstream merge without a named merge approval blocks;
11. stale approval head SHA blocks after the PR head changes;
12. tool-system internal routine PR and downstream target PR follow different lifecycle rules;
13. autonomy policy cannot claim an unsupported ready action;
14. existing valid tool-system controller tests remain green;
15. policy and controller failures produce deterministic reasons and no action.

## Verification commands

```bash
git diff --check
python -m compileall src/tool_system tests
python -m pytest -q
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
```

Additional pass conditions:

```text
changed_paths: exact_packet_allowlist_or_narrower
legacy_finance_os_new_work_allowed: false
direct_main_bootstrap_allowed: false
downstream_lifecycle_approval_machine_enforced: true
finance_us_mutated: false
cleanup_executed: false
production_or_external_worker_execution: false
PR_state: open_draft_unmerged
```

## Authorized sequence after separate implementation approval

1. fresh-state verify tool-system main and all natural-owner files;
2. confirm the proposed branch and duplicate open PR do not exist;
3. revise this packet first if dependency tracing changes the required allowlist;
4. create one implementation branch;
5. modify only the approved paths;
6. run the full verification set and inspect the exact diff;
7. open one tool-system draft PR;
8. collect CI and audit evidence;
9. stop without ready, merge, cleanup, finance-us mutation, P11 entry, or production action.

## Forbidden actions

- no policy or source mutation without separate implementation approval;
- no finance-us file, branch, PR, or metadata mutation;
- no target P1B implementation;
- no ready transition or merge;
- no branch deletion or cleanup;
- no rollback execution;
- no P11 or later successor entry;
- no real external worker execution;
- no production deployment;
- no Codex-replacement or autonomous-production claim.

## Rollback

Before merge, close the draft implementation PR and retain its head SHA as evidence. Branch deletion requires a separate cleanup approval. After any future merge, rollback requires a named revert packet and revert PR; never reset or force-push main.
