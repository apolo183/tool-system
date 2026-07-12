# P14MR Milestone Module Invariant

status: ACCEPTED_CLOSED
phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT
stage: P14MR_MILESTONE_MODULE_INVARIANT
parent: docs/reports/p14b_provider_neutral_ai_worker_contract.md
validated_main: 212af8228b8879dc5332fc1d3fab2c401ba6a280
authorized_by: user_authorized_global_milestone_module_invariant

## Single objective

Make every tool-system project, major milestone, and sub-milestone a versioned replaceable capability module so a defective or drifted module can be isolated and replaced without undocumented whole-project adjustment.

P14MR is governance-only. It changes no runtime source, policy boundary, model provider, credential, network path, downstream repository, cleanup action, or production state.

## Parent and global alignment

Parent alignment: accepted P14B is already a bounded capability module with a public contract and a P14C stop condition. P14MR generalizes that architecture before later P14 stages create more modules.

Global alignment: the permanent product objective requires blueprint-driven milestone decomposition, bounded implementation, repair, alignment review, and fail-closed operation. Replaceable module contracts contain drift and prevent one bad milestone from forcing an undocumented project-wide rewrite.

## Controlled architecture

```text
approved project blueprint
  -> versioned milestone-module DAG
       -> accepted module A public interface
       -> accepted module B public interface
       -> accepted module C public interface

if B drifts:
  B -> INVALIDATED -> ISOLATED -> REPLACED by B' -> REVALIDATED
  A and unrelated modules remain unchanged
  B dependents pause and revalidate against B'
```

Every module binds its objective, parents, version, hashes, public inputs and outputs, dependency versions, natural owners, authorization, acceptance, invalidation, rollback, cleanup, and replacement disposition.

## Repair versus replacement

- implementation defect with a correct objective and interface: repair inside the module boundary and reaccept;
- objective, interface, scope, evidence, or implementation drift from parent or global blueprint: invalidate, isolate, and replace the module;
- interface-compatible replacement: no changes to unaffected modules; direct dependents revalidate without reimplementation by default;
- interface-incompatible replacement: new version, explicit migration, and dependency-derived impact set;
- shared-foundation change: explicit wider blast-radius review;
- hidden dependency discovery: record it as a governance defect and add it to the impact set, not as justification for an unbounded rewrite.

## Active-route and evidence disposition

Only one implementation may be active for a module responsibility. The replacement must pass before an atomic active swap; then the superseded route leaves the active tree. Invalid code, docs, tests, or routes are not retained as active fallback or a second mainline. Git history and audit evidence remain available. Creator-owned temporary artifacts are cleaned by their creator, while destructive cleanup and branch deletion remain separately authorized.

## Universal adoption gate

The invariant applies to tool-system and every project it generates, controls, or adopts. A project must inherit the canonical invariant or embed an equivalent machine-readable contract before its next phase entry or controlled write. Existing external projects are not retroactively mutated by this governance PR.

P14E must implement compiler and module-graph enforcement. P15 must prove multi-project adoption and replacement behavior. Until those product stages are accepted, P14MR is a binding governance contract and machine-alignment baseline, not proof that automatic replacement already works end to end.

## Exact file scope

```text
AGENTS.md
README.md
blueprint/tool_system_v0.yaml
docs/tool_system_global_development_principles_v1.md
docs/reports/p14mr_milestone_module_invariant.md
examples/task_manifests/tool_system_p14mr_milestone_module_invariant.yaml
examples/change_plans/tool_system_p14mr_milestone_module_invariant.yaml
examples/active_gates.yaml
tests/test_milestone_module_invariant.py
tests/test_product_objective_alignment.py
tests/test_p14_phase_entry_contract.py
tests/test_phase_alignment.py
```

## Acceptance target

```text
blueprint_schema_version: 0.5
module_graph_required: true
versioned_public_interfaces_required: true
hidden_dependencies_allowed: false
parallel_active_mainlines_allowed: false
compatible_replacement_changes_unaffected_modules: false
dependent_revalidation_required: true
whole_project_rewrite_on_local_defect: prohibited
all_controlled_projects_adoption_gate: fail_closed
global_principles_AGENTS_README_blueprint_alignment: PASS
focused_tests: PASS
full_tests: PASS
active_gates: PASS
runtime_source_changes: none
live_provider_calls: 0
target_repo_mutation: false
production_deployment: false
```

## Local execution evidence

```text
blueprint_schema_version: 0.5
module_invariant_applicability_contract: PASS
required_module_fields_contract: PASS
lifecycle_and_defect_disposition_contract: PASS
failure_isolation_and_compatible_replacement_contract: PASS
replacement_cleanup_and_project_adoption_contract: PASS
global_public_contract_alignment: PASS
P14MR_P14C_P14E_P15_dependency_alignment: PASS
focused_governance_tests: PASS_17
full_repository_tests: PASS_302
change_plan: PASS
active_gates: PASS
git_diff_check: PASS
changed_files_match_plan: PASS_12
creator_owned_test_and_bytecode_roots: removed
runtime_source_changes: none
policy_changes: none
live_provider_calls: 0
target_repo_mutation: false
production_deployment: false
```

## CI acceptance and closure evidence

```text
candidate_remote_head: 759721590a4e172286fe2a9c6fcb67482ea28726
candidate_base: 212af8228b8879dc5332fc1d3fab2c401ba6a280
candidate_compare: ahead_1_behind_0
candidate_diff: 12_files_671_additions_39_deletions
github_actions_workflow: tool-system-ci
github_actions_run: 29183847936
github_actions_run_number: 940
github_actions_conclusion: success
closure_record_scope_delta: this_report_only
final_closure_gate: closure_head_CI_success_and_squash_merge_required
```

P14MR acceptance and closure are effective only when this closure-record head passes CI, the same PR squash-merges to `main`, and fresh-state verification confirms the merged state. The closure grants no P14C execution authority.

## Rollback and stop condition

Before merge, rollback is closing the unmerged P14MR PR while retaining head evidence. After merge, rollback requires a named revert packet and PR. This stage performs no branch cleanup or destructive deletion.

After focused tests, full tests, CI, squash merge, and fresh-main verification pass, P14MR is accepted and closed. Stop at P14C: no provider/model/network/credential/cost execution begins without its separately named authorization packet.
