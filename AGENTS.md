# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents may inspect, modify, test, and publish changes in tool-system  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-05 20:00 UTC+08:00

## 1. Mission

tool-system builds and controls agentic software-development workflows. It is domain-agnostic infrastructure.

Agents operating in this repository must preserve the separation between:

- tool-system: agent orchestration, harness, CI, patch control, repo control.
- finance-os: market data, ranking, signal generation, risk, portfolio, execution.

## 2. Evidence-first rule

Before modifying any existing file, an agent must read the current file and cite the relevant path and content region in its plan.

If evidence is missing, the agent must stop and request the smallest missing artifact or run a read-only inspection.

## 3. Write boundaries

Agents may add or modify files only when the change is tied to an approved blueprint item.

Agents must not:

- introduce finance-domain logic into tool-system;
- modify target repositories without an explicit workflow gate;
- write directly to main outside an approved bootstrap or controlled maintenance action;
- bypass tests or policy checks;
- mutate blueprint files unless explicitly authorized.

## 4. Required change record

Every non-trivial change must state:

- scope;
- files touched;
- reason;
- verification command;
- rollback method.

## 5. Testing policy

Phase 0 has documentation-only bootstrap files. Later implementation phases must add CI before enabling autonomous patch application.

Minimum future gates:

- unit tests;
- formatting/lint;
- type checks where applicable;
- spec compliance checks;
- dry-run patch application.

## 6. Rollback policy

Rollback must be based on Git history, commit SHAs, pull requests, or explicit patch reversal. Do not preserve broken implementations as active fallbacks.

## 7. Current phase

Current phase: `P0_BLUEPRINT_BOOTSTRAP`.

Allowed now:

- create blueprint and governance documentation;
- define module boundaries;
- define future milestones.

Not allowed now:

- autonomous repo mutation loop;
- cross-repo write automation;
- production scheduler;
- finance-specific business logic.
