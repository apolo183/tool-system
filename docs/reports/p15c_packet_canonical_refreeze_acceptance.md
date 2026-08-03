# P15C Packet Canonical Re-Freeze Acceptance

Status: `ACCEPTED_ON_GUARDED_SQUASH_MERGE_NO_P15C_AUTHORITY`

## Decision

`P15C-PACKET-CANONICAL-REFREEZE-v1` re-anchors the already accepted,
non-executing P15C packet to canonical `tool-system` main at
`1ede788b8b1c36bcc224cde15a5f6462c9b51938`, tree
`7abd3b555d5c05f8bdf719c18619459ae9e06645`. The previous anchor was
`81be20f8cdf2d588993347fa11ca090dc9f17135`, tree
`23addb451399ae89cc99e2c740115596f5e763c0`.

The intervening change was the accepted target-identity decoupling correction.
It made the public tooling boundary more project-neutral and did not change the
P15C provider packets, models, price or policy snapshots, deterministic corpus,
private-control boundaries, target-packet contract, limits, or activation
gates. The normalized packet SHA-256 after removing only the
`tool_system_baseline` mapping is unchanged at
`03f99a7e43ce7f3a381d59231c8a9d31ec1a9324922639126fa2268ff6d42626`.

## Predecessor terminal evidence

- PR #171 merged the exact final candidate tree as canonical commit
  `1ede788b8b1c36bcc224cde15a5f6462c9b51938`.
- Final candidate head: `2dbd0c6735b4a0f081d1a064458750d73d870cfe`.
- Final-head Hosted CI: `tool-system-ci` run `30811800450` (`#1067`), success.
- Retained branch: `agent/target-identity-decoupling-v1`, verified at the final
  candidate head.

## Exact closure

This correction changes exactly nine paths: the packet configuration and
report, the predecessor report, descriptive project state, two consistency
tests, this record, and the retained manifest/change-plan pair. No blueprint,
runtime source, provider module, policy, fixture, credential store, or target
repository path is included.

## Acceptance predicate

This tracked record is accepted when its exact branch is published as a Draft
PR from the frozen canonical baseline, local and Hosted CI validation pass, the
base remains unchanged through Ready, and the exact candidate is squash-merged
while retaining the feature branch. Terminal publication identifiers belong to
the immutable GitHub PR and commit evidence so this record does not require a
self-referential post-merge source edit.

```text
provider_document_reads: 0
credential_value_accesses: 0
provider_invocations: 0
target_repository_accesses: 0
benchmark_executions: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
P15C_authorized: false
P15C_accepted: false
```
