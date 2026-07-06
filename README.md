# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and current controller contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-06 11:50 UTC+08:00

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

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.

## Current phase

Current phase: `P4_TARGET_REPO_DRY_RUN_ADAPTER`.

The active objective is target-repository dry-run adaptation: read target contract references, validate target repo boundaries, generate a no-write dry-run plan, and record an audit artifact.

## Repository contract

This repository is a tool layer. Business systems such as finance-os are downstream targets. tool-system may propose and apply code changes to target repositories only through explicit workflow, test, policy, and review gates. In P4, finance-os is still dry-run only: tool-system does not write finance-os.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `blueprint/tool_system_v0.yaml`: machine-readable active blueprint.
