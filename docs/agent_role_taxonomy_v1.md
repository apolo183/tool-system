# Agent Role Taxonomy v1

repo_rel_path: docs/agent_role_taxonomy_v1.md
role: agent governance contract
purpose: define stable, fine-grained agent roles for future task DAG orchestration
author: ChatGPT / apolo183
created_at: 2026-07-06 20:20 UTC+08:00
updated_at: 2026-07-06 20:20 UTC+08:00

## Boundary

This taxonomy is for tool-system orchestration only. It does not add finance, trading, market-data, portfolio, broker, or production ownership to tool-system.

## Control principle

Large tasks should not be routed to generic planner/coder/tester labels alone. The runtime should split work into explicit roles so that scope, evidence, policy, tests, repository mutation, audit, and rollback are independently checked.

## Required role groups

| group | role | responsibility | may write repo | may write target repo |
| --- | --- | --- | --- | --- |
| intake | request_intake | normalize user request and identify milestone boundary | no | no |
| evidence | evidence_collector | read repo files, logs, PRs, CI, and target contract refs | no | no |
| architecture | blueprint_architect | maintain blueprint, role taxonomy, and objective contracts | yes, via PR | no |
| planning | task_decomposer | split approved work into bounded tasks | no | no |
| planning | dag_planner | order tasks and dependencies into an executable DAG | no | no |
| policy | policy_guard | enforce no-go boundaries and approval requirements | no | no |
| implementation | change_planner | produce file-scoped change plans and rollback references | yes, via PR | no |
| implementation | patch_author | modify approved files only | yes, via PR | only through approved target flow |
| verification | test_engineer | run or define tests and evaluate failures | no | no |
| verification | ci_operator | collect workflow state and CI logs | no | no |
| review | code_reviewer | check diff, imports, behavior, and tests | no | no |
| review | contract_reviewer | check blueprint, manifest, policy, and active gates | no | no |
| repository | repo_controller | create branches, PRs, merge after gates | yes, via gates | no |
| target | target_repo_adapter | prepare target repo dry-run, precheck, packets | yes, audit only | no |
| target | target_repo_executor | execute approved target repo branch/file/PR mutation | no | only after explicit execution approval |
| audit | audit_recorder | write audit records, rollback references, and residual checks | yes, audit only | no |
| cleanup | cleanup_owner | identify and remove temporary branch/file residue after evidence | yes, via PR or branch ref operation | no |

## Anti-drift rules

1. No single role may both approve and execute a target-repository mutation.
2. Target-repository mutation requires fresh state, execution approval, and rollback reference.
3. Business-domain implementation is outside tool-system roles.
4. Runtime DAGs must include evidence, policy, verification, and audit nodes, not only coding nodes.
5. Temporary artifacts and branches must be assigned to cleanup_owner before milestone completion.
