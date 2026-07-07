# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-07 22:45 UTC+08:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

## 2. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

## 3. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, and milestone acceptance.

## 4. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

tool-system remains separate from business-domain repositories.

## 5. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 6. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 7. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 8. Current phase

Current phase: P7_BLUEPRINT_TO_DAG_PLANNER.

Allowed now: build and validate blueprint-to-DAG planning, role-assigned task graph generation, deterministic planner contracts, and local runner integration after P6 runner productization.

Not allowed now: direct target-repository main-branch mutation, direct downstream repository mutation without separate explicit approval, production deployment, or business-domain implementation outside a valid approved workflow.
