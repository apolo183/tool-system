# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-08 09:45 UTC+08:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

## 2. Mandatory first step

Before material tool-system engineering work, read:

```text
docs/tool_system_global_development_principles_v1.md
```

## 3. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

Material engineering work follows the evidence hierarchy, drift gate, authorization gate, file disposition, cleanup, rollback, and claims rules in `docs/tool_system_global_development_principles_v1.md`.

## 4. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, milestone acceptance, cleanup execution, and first real downstream target-repository mutation.

## 5. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

tool-system remains separate from business-domain repositories.

## 6. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 7. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 8. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 9. Current phase

Current phase: P8_MULTI_AGENT_RUNTIME.

Allowed now: build and validate a no-mutation multi-role runtime that consumes validated task graphs, assigns agent roles, executes dry-run role steps, records evidence, and prepares audit and rollback bundles after P7 gates pass.

Not allowed now: direct target-repository main-branch mutation, direct downstream repository mutation without separate explicit approval, production deployment, business-domain implementation outside a valid approved workflow, cleanup execution without a separate execution gate, or autonomous patch execution outside approved tool-system branches.
