# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-11 UTC+08:00

## Definition

tool-system is a domain-agnostic software factory for controlled agentic development.

It coordinates agents, harness workflows, CI checks, patch generation, review gates, and repository write controls. It does not contain finance logic, trading logic, portfolio logic, market-data logic, or investment decision logic.

## System boundary

### In scope

- Parse machine-readable blueprints and execution specs.
- Decompose approved specs into bounded implementation tasks.
- Generate patches through controlled agents.
- Run tests, lint, type checks, and policy checks.
- Block writes when tests or policy checks fail.
- Create auditable repository changes.
- Collect pull request and workflow state for repo write decisions.
- Execute approved repository write actions through explicit controller gates.
- Validate downstream target-repository task manifests in dry-run mode.
- Prepare approved downstream target-repository pull-request write flows after explicit gates pass.
- Run local task-manifest and change-plan gates through productized runner commands.
- Plan bounded task graphs with dependency ordering and agent role assignments.
- Run role-assigned task graph steps through an auditable no-mutation runtime.
- Build no-mutation worker adapter contracts and orchestration records.
- Define and operate controlled target-repository PR pilot gates after explicit execution approval.

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.
- Production deployment without separate explicit approval.

## Current phase state

Current phase: `P10_CONTROLLED_TARGET_REPO_PR_PILOT`.

Status: `accepted`.

P10 was accepted as a successful controlled, no-production, draft-pull-request pilot. The acceptance demonstrates bounded target-repository planning, named execution approvals, fresh-state checks, exact file allowlists, draft PR creation, local validation handoff, fail-closed correction handling, audit evidence, and rollback references.

No successor tool-system phase is authorized. P10R-A machine-policy enforcement correction is implemented on `main`; P10R-B governance-state synchronization is the current bounded corrective stage. Preparation of a separately approvable P11-P15 successor roadmap is allowed, but no successor implementation is authorized by the accepted P10 state.

## Repository contract

This repository is a tool layer. Business systems are downstream targets. tool-system may propose and apply changes to target repositories only through explicit workflow, test, policy, review, execution-approval, and rollback gates.

P10 acceptance does not authorize unrestricted downstream mutation, target PR ready transition, target PR merge, production deployment, real external worker execution, or Codex replacement claims. Each such action remains separately gated.

Finance-us P1A is accepted, merged, strictly validated, and closed on target `main` at `7101847826e6701a4d8cc7f0a6208fb9aee2cc4e`. The finance-us P1B phase-entry record and implementation packet are prepared and merged in tool-system. P1B target implementation remains blocked pending a named, action-scoped target execution approval; P1B ready and merge remain separately gated.

The canonical active downstream identity is `apolo183/finance-us`. The legacy `apolo183/finance-os` route is retired and retained only as a closed, no-write compatibility fixture. Direct bootstrap on tool-system and finance-us is disabled, and downstream merge approval is bound to repository, action, base branch, and expected head SHA.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `docs/tool_system_global_development_principles_v1.md`: project-wide engineering discipline contract for evidence, scope, cleanup planning, validation, rollback, and claims.
- `blueprint/tool_system_v0.yaml`: machine-readable blueprint and accepted P10 state.
