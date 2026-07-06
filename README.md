# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-06 18:05 UTC+08:00

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

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.

## Current phase

Current phase: `P5_TARGET_REPO_APPROVED_PR_WRITE_FLOW`.

The active objective is approved target-repository pull-request write-flow preparation: require P4 dry-run, PR preview, action preview, write precheck, and write-intent audit records before any downstream target repository mutation is attempted.

## Repository contract

This repository is a tool layer. Business systems such as finance-os are downstream targets. tool-system may propose and apply code changes to target repositories only through explicit workflow, test, policy, and review gates. In P5, finance-os still requires a separate explicit approval before the first real target-repository mutation.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `blueprint/tool_system_v0.yaml`: machine-readable active blueprint.
