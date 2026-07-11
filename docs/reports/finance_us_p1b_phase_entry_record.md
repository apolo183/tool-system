# Finance-US P1B Phase-Entry Record

status: PHASE_ENTRY_APPROVED_PACKET_PREPARATION_ONLY
parent: docs/reports/p10q_finance_us_final_post_merge_closure.md
created_at: 2026-07-11 UTC+08:00

## Decision

The user approved entry into `P1B_MINIMAL_RANKING_CODE` for governance and packet preparation in tool-system only.

```text
P1B_phase_entry_decision: APPROVED
phase_entry_scope: tool_system_records_and_packet_only
finance_us_target_write_authorized: false
finance_us_branch_or_pr_authorized: false
P1B_implementation_authorized: false
P1B_merge_authorized: false
```

## Entry evidence

```text
repository: apolo183/finance-us
locked_main: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
P1A_accepted: true
P1A_content_on_main: true
P1A_strict_validation_complete: true
P1A_closure_complete: true
```

The P10Q closure states that P1B is ready for a new explicit decision while implementation remains unauthorized.

## P1B objective

Implement a deterministic, in-memory ranking function over a contract-validated US-equity input frame, with a smoke test.

The objective is intentionally limited to ranking logic. It does not include data adapters, downloads, database access, feature research, model training, scoring pipelines, backtests, schedulers, artifact publication, portfolio construction, broker integration, live trading, or investment claims.

## Governing contracts

P1B must remain consistent with:

- `blueprint/finance_us_phase_1_v0.yaml`;
- `contracts/data_input_contract.yaml`;
- `contracts/ranking_output_contract.yaml`;
- `contracts/cutoff_contract.yaml`;
- `contracts/evaluation_contract.yaml`.

The ranking-output contract already requires:

```text
primary_sort: score descending
tie_breakers: exchange ascending, symbol ascending
max_rows: 10
duplicate_symbol_exchange: fail_closed
non_numeric_score: fail_closed
purpose: observation_only
```

## Current authorized work

Only these tool-system artifacts may be prepared in this stage:

- this phase-entry record;
- an independent P1B implementation packet;
- one task manifest;
- one change plan;
- active-gate registration.

No finance-us file, branch, pull request, PR metadata, or repository setting may be changed by this phase-entry authorization.

## Boundary

The finance-us repository may continue to display P1A as its current milestone until a separately approved P1B target execution updates the target governance files. This record does not authorize target mutation, implementation, PR creation, ready transition, merge, P1C entry, production/data/model/trading operations, rollback, cleanup, branch deletion, real external workers, or Codex-replacement claims.
