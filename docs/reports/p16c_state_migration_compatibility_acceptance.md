# P16C State Migration and Compatibility Acceptance

P16C closes the product-wide planning gap identified by P16A without executing a
migration. The `state-migration` module consumes canonical semantic versions
from P16B and remains deterministic, provider-neutral, and free of I/O.

## Accepted core evidence

- A migration registry requires unique identifiers and a linear, non-branching,
  acyclic forward graph.
- A product compatibility matrix binds each product version to one inclusive
  supported state-version range.
- Upgrade plans contain an ordered, complete path or fail closed.
- Downgrades require explicit caller opt-in and every traversed step to be
  reversible; otherwise they fail closed with stable ordered reasons.
- Unknown product versions, incompatible target state, and registry gaps block.
- A successful result is only
  `READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION`; every returned plan records
  `execution_authorized=false`.
- Existing durable-orchestrator SQLite v2-to-v3 behavior remains an inherited
  local primitive and is not presented as a product-wide execution engine.

## Remaining boundary

No database, schema, state, artifact, backup, restore, deployment, production,
rollback, provider, or downstream operation was performed. P16 remains
unaccepted. P16D may now build backup, restore, and disaster-recovery evidence
on this planning interface.
