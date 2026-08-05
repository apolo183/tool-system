# P15 Non-Live Multi-Project and Isolation Evidence

## Frozen objective

Qualify representative project and task classes only through committed isolated fixtures. This package reuses the accepted blueprint-to-code development loop and adds a machine-readable P15 matrix; it does not access a real downstream repository or execute a provider.

## Representative projects

- Python CLI fixture: greenfield addition, bounded modification, repair, validation, stale-status convergence, and local fixture commit.
- TypeScript package fixture: bounded add/modify/delete topology, validation, and local fixture commit.

The two projects use distinct copied repository roots, independent Git histories, independent orchestrator state databases, caller-supplied project identities, and distinct task branches.

## Generalization and failure coverage

The matrix binds existing executable cases for ambiguous blueprint rejection, out-of-scope patch rejection, invented milestone rejection, cancellation, deterministic resume, two-cycle no-progress, sealed-evidence non-reopening, crash recovery, exactly-once commit behavior, and conflicting-branch blocking.

## Metrics boundary

Quality is represented by accepted isolated projects and rejected unauthorized cases. Time is measured as bounded logical development cycles; wall-clock CI duration is advisory. Economics use integer synthetic microunits with no private values. Recovery and policy metrics are explicit counts. All external operation counts remain zero.

## Acceptance effect

This package supplies representative multi-project, cross-project isolation, and generalization evidence. It does not accept P15, enter P16, authorize rollback execution, read credentials, call any provider, access a private target, run an investment benchmark, perform production or cleanup, or execute the final live smoke.
