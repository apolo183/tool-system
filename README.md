# tool-system

repo_rel_path: README.md  
role: repository overview  
purpose: define the domain-agnostic tool system boundary and bootstrap contract  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-05 20:00 UTC+08:00

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

### Out of scope

- Trading decisions.
- Alpha or factor design.
- Backtest interpretation.
- Portfolio allocation.
- Market-data ingestion.
- Direct modification of business-system rules without explicit approval.

## First milestone

Phase 0 initializes only the blueprint and agent governance contract. No autonomous code-writing loop is active yet.

## Repository contract

This repository is a tool layer. Business systems such as finance-os are downstream targets. tool-system may propose and apply code changes to target repositories only through explicit workflow, test, and review gates.

## Bootstrap files

- `AGENTS.md`: operating contract for agents working in this repository.
- `blueprint/tool_system_v0.yaml`: machine-readable phase-0 blueprint.
