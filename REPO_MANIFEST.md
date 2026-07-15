# REPO_MANIFEST.md

## Authority

This file is the repository-local formal-file-set registry for tool-system. It registers current tool-system authority, configuration, implementation, tests, CI, and deterministic fixtures without turning retained milestone or task process inputs into current authority.

This manifest is effective only in an accepted tool-system main commit. It does not activate finance-governance, replace `config/governance_reference_v1.yaml`, grant authority over another repository, authorize target mutation, authorize cleanup, or authorize production deployment.

## Set and Graph Semantics

- `path` is a repository-relative exact path or glob expression whose tracked regular-file expansion is the registered set.
- Every tracked path must belong to exactly one formal set or one retained non-authority set.
- `upstream` is the only source of directed formal-set dependency edges. Tokens are separated by semicolons.
- Exact token `ROOT` is exclusive and identifies the only local formal authority root.
- `downstream` is informational and grants no reverse authority.
- Formal files must be tracked, regular, non-empty, non-symlink files.
- Retained non-authority files are not runtime defaults, rollback authority, or current-task authority.
- Set registration is a tool-system local extension; it is not a claim that finance-governance `self-check` validates this downstream manifest.

## Formal File Sets

| path | role | purpose | owner | lifecycle | upstream | downstream | validation | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/tool_system_global_development_principles_v1.md | local engineering constitution | Define tool-system-local evidence, authority, modularity, safety, and rollback discipline. | tool-system governance owner | ACTIVE | ROOT | every formal tool-system set | current content, focused tests, full tests, diff, hosted CI | REGISTERED |
| blueprint/**/* | product blueprint | Define the product objective, milestone graph, authority boundaries, and machine blueprint schema. | blueprint owner | ACTIVE | docs/tool_system_global_development_principles_v1.md | configs, implementation, tests, fixtures, orientation | YAML and JSON parsing, alignment tests, full tests | REGISTERED |
| docs/tool_system_module_registry_adoption_contract_v1.md | S0 formal mapping owner | Freeze candidate module identities, aggregate interfaces, Python import boundaries, static import DAG, temporary adapter limits, and unknown ContractReferences without adopting the registry. | tool-system module-registry adoption S0 owner | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | separately authorized S1-S11 adoption stages | focused behavioral contract tests, full tests, diff, hosted CI | REGISTERED |
| config/governance_reference_v1.yaml | immutable candidate governance reference | Pin the exact finance-governance repository and commit without claiming activation. | governance-reference owner | ACTIVE | docs/tool_system_global_development_principles_v1.md | repository identity and central repo-check | exact five-field tests, pinned SHA checks, full tests | REGISTERED |
| config/module_registry* | durable module registry contract | Register module owners, versions, interfaces, path coverage, and dependency DAG. | architecture_registry module | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | implementation, tests, CI, repository manifest | module-registry validator, schema tests, import audit, full tests | REGISTERED |
| config/process_authority* | current-task authority contract | Require one explicit bound task pair and deny implicit repository-wide execution authority. | process_authority module | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/*; config/module_registry* | task planner, task runner, role runtime, CLI, replay snapshot | process-authority validator, schema validation, full tests | REGISTERED |
| config/replay_snapshot_v1.yaml | content-addressed replay boundary | Lock the retained legacy pair set for non-executing compatibility replay only. | process_authority module | ACTIVE | config/process_authority* | replay validation and legacy disposition evidence | source-index and pair-set SHA256 reconstruction | REGISTERED |
| docs/agent_role_taxonomy_v1.md | role contract | Define reusable agent roles and responsibility boundaries. | role_runtime module | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | runtime and role tests | content tests and full tests | REGISTERED |
| docs/model_provider_portfolio_and_economics_contract_v1.md | provider portfolio contract | Define provider selection, model qualification, failover, escalation, and total economic cost rules. | ai_worker_runtime roadmap owner | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | P14 to P16 provider work | contract tests and full tests | REGISTERED |
| docs/process_authority_contract_v1.md | process authority interface contract | Explain explicit current-task authority, replay compatibility, caller cutover, and cleanup boundary. | process_authority module | ACTIVE | docs/tool_system_global_development_principles_v1.md; config/process_authority*; config/replay_snapshot_v1.yaml | agents, operators, callers, tests | process-authority tests, docs alignment, full tests | REGISTERED |
| REPO_MANIFEST.md | repository formal-file-set registry | Classify every tracked path as formal or retained non-authority and define the formal set DAG. | architecture_registry module | ACTIVE | docs/tool_system_global_development_principles_v1.md; config/module_registry*; config/process_authority* | agents, CI, repository validation, central handoff | repository-manifest validator, coverage tests, full tests | REGISTERED |
| AGENTS.md | agent entrypoint | Route agents through current local and pinned governance, process authority, module registry, and safety boundaries. | tool-system governance owner | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/*; config/module_registry*; config/process_authority*; REPO_MANIFEST.md | scoped agent work | content tests, full tests, diff, hosted CI | REGISTERED |
| README.md | repository identity document | State product scope, current phase, durable modules, process authority, governance reference, and non-claims. | documentation owner | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/*; config/module_registry*; config/process_authority*; REPO_MANIFEST.md | users and repository orientation | content tests, full tests, diff | REGISTERED |
| pyproject.toml | Python package and CLI contract | Define supported Python, package dependencies, test settings, and command entrypoints. | package maintainer | ACTIVE | docs/tool_system_global_development_principles_v1.md | CI, source package, tests, operators | editable install, CLI tests, full tests | REGISTERED |
| .github/workflows/**/* | hosted verification workflow | Run full tests and current machine validators on pull requests and protected pushes. | CI owner | ACTIVE | pyproject.toml; config/module_registry*; config/process_authority*; REPO_MANIFEST.md | pull-request and main acceptance evidence | hosted Actions verify job | REGISTERED |
| .gitignore | repository generated-file exclusion contract | Exclude local generated state without hiding tracked authority or evidence. | repository maintainer | ACTIVE | docs/tool_system_global_development_principles_v1.md | local worktrees and CI | current content and clean status | REGISTERED |
| harness/**/* | task-manifest schema | Define the reusable structural contract for task manifests. | manifest_validation module | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | policy and manifest validation | JSON parsing, manifest tests, full tests | REGISTERED |
| policy/**/* | local policy contracts | Define autonomy and repository-write constraints for tool-system and named targets. | manifest_validation module | ACTIVE | docs/tool_system_global_development_principles_v1.md; blueprint/**/* | validators, controller, runner, target adapters | policy tests, active-gate compatibility validation, full tests | REGISTERED |
| src/tool_system/**/* | implementation source | Implement all registered tool-system modules and public interfaces. | natural owners in config/module_registry_v1.yaml | ACTIVE | blueprint/**/*; config/module_registry*; config/process_authority*; policy/**/*; pyproject.toml | CLIs, tests, fixtures, audit outputs | module registry, process authority, unit tests, full tests, Ruff | REGISTERED |
| tests/**/* | executable acceptance suite | Verify formal contracts, module boundaries, security controls, replay, orchestration, and no-mutation claims; the S0 adoption-contract test is validation evidence only and has no governance authority. | test maintainers and module owners | ACTIVE | src/tool_system/**/*; blueprint/**/*; config/module_registry*; config/process_authority*; policy/**/* | local and hosted acceptance evidence | pytest full suite and focused negative fixtures | REGISTERED |
| examples/batches/**/* | deterministic batch fixtures | Exercise explicit and replay-only batch behavior without remote mutation. | task_runner module | ACTIVE | src/tool_system/**/*; blueprint/**/*; config/process_authority* | batch tests | fixture tests and full tests | REGISTERED |
| examples/cleanup/**/* | cleanup-planning fixture | Exercise non-executing residue classification and cleanup planning. | cleanup_planner module | ACTIVE | src/tool_system/**/*; blueprint/**/*; policy/**/* | cleanup planner tests | cleanup tests and full tests | REGISTERED |
| examples/gate_decisions/**/* | gate-decision fixture | Provide deterministic local decision input for gate tests. | manifest_validation module | ACTIVE | src/tool_system/**/*; policy/**/* | gate tests | focused gate tests and full tests | REGISTERED |
| examples/github_states/**/* | GitHub-state fixture | Provide deterministic hosted-state input without a live mutation. | repository_controller module | ACTIVE | src/tool_system/**/*; policy/**/* | controller tests | focused controller tests and full tests | REGISTERED |
| examples/repo_write_decisions/**/* | repository-write decision fixture | Provide deterministic policy decision evidence without executing writes. | repository_controller module | ACTIVE | src/tool_system/**/*; policy/**/* | controller and policy tests | focused policy tests and full tests | REGISTERED |
| examples/requirements/**/* | requirement compiler fixture | Provide structured local requirement input with explicit task-pair references. | task_planner module | ACTIVE | blueprint/**/*; config/process_authority* | planner and stage tests | planner tests and full tests | REGISTERED |
| examples/task_graphs/**/* | task-graph fixture | Provide a deterministic DAG whose tasks declare explicit manifest/change-plan pairs. | task_planner module | ACTIVE | blueprint/**/*; config/process_authority* | graph, role-runtime, and stage tests | graph tests and full tests | REGISTERED |

## Retained Non-Authority Sets

| path | classification | authority | runtime_default | disposition | validation |
| --- | --- | --- | --- | --- | --- |
| docs/reports/**/* | retained legacy milestone and task evidence | false | false | pending separate cleanup authorization | file-level disposition audit required before any deletion or reconstruction |
| examples/active_gates.yaml | retained legacy pair index | false | false | pending separate cleanup authorization | content-addressed by config/replay_snapshot_v1.yaml and accepted only for explicit non-executing replay |
| examples/change_plans/**/* | retained legacy task process inputs | false | false | pending separate cleanup authorization | content-addressed replay consistency plus file-level disposition audit |
| examples/task_manifests/**/* | retained legacy task process inputs | false | false | pending separate cleanup authorization | content-addressed replay consistency plus file-level disposition audit |
| examples/target_repo_dry_runs/**/* | retained generated dry-run evidence | false | false | pending separate cleanup authorization | no current runtime caller and file-level disposition audit required |
| examples/target_repo_pr_previews/**/* | retained generated preview evidence | false | false | pending separate cleanup authorization | no current runtime caller and file-level disposition audit required |

## Current Boundary

The retained sets above prevent a finance-governance process-file-compliance claim. They remain tracked only because destructive cleanup and file-level disposition have not been authorized. Their registration here is an exclusion from formal authority, not a retention endorsement or fallback route.

This manifest grants no finance-us or other target-repository mutation, cleanup execution, branch deletion, live provider execution, production deployment, or group-governance activation.
