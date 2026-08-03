# Target Identity Decoupling Acceptance

## Scope

`TARGET-IDENTITY-DECOUPLING-v1` corrects the active public target-policy
boundary so tool-system remains reusable across projects. It does not access or
mutate a downstream repository and does not execute a provider, credential,
benchmark, production, cleanup, or rollback operation.

## Alignment

- Direct parent: the user-approved project-neutral decoupling requirement.
- Global objective: `blueprint/tool_system_v0.yaml:product_objective` requires
  an approved repository snapshot and authorization envelope while keeping
  downstream authority external.
- Module boundary: manifest-validation owns structural identity and injected
  policy validation; target-repo-adapter consumes that policy without a
  project-name branch. The atomic correction prevents an inconsistent partial
  publication between those two public boundaries.

## Frozen acceptance

- The task-manifest schema uses a bounded owner/repository pattern rather than
  a downstream-project enum.
- The checked-in repository-write policy contains tool-system self-policy only.
- External target identities, paths, lifecycle policy, and approvals are
  caller-supplied inputs; an unknown or incomplete target fails closed.
- Target precheck reads the approval requirement from the selected target
  policy and defaults to requiring approval.
- Active target-adapter tests use a synthetic repository identity and no
  retained historical target fixture.
- Retained evidence is unchanged and remains non-authoritative.
- P15C remains unauthorized.

## Accepted terminal evidence

- Exact closure: the working tree differs from the canonical baseline in the
  frozen 31 paths only; no path is missing or unexpected.
- Focused tests: 107 passed.
- Full test suite: 639 passed.
- Changed-file Ruff: passed.
- Active-gates, process-authority, current module-registry, repository-manifest,
  task-manifest, and change-plan validators: passed.
- Repository manifest: 245 formal paths, no unclassified tracked path.
- Retained evidence diff: only this report and the frozen task-manifest/change-
  plan pair are additions; existing retained evidence is unchanged.
- External operations: zero downstream-repository access, provider invocation,
  credential-value access, benchmark execution, mutation, production, cleanup,
  and rollback operations.
- Pull request: `apolo183/tool-system#171`, with the exact 31-path closure,
  final candidate commit `2dbd0c6735b4a0f081d1a064458750d73d870cfe`, and
  final candidate tree `7abd3b555d5c05f8bdf719c18619459ae9e06645`.
- Hosted CI: initial `tool-system-ci` run `30811492314` (`#1066`) and final-head
  run `30811800450` (`#1067`) both passed. The final run validated tests,
  active gates, process authority, current module registry, and repository
  manifest on the exact candidate head.
- Ready transition: completed only after canonical `main` remained at
  `5e964adfd40502a3798630b98fb0d876bbd01d91`, the final head and exact scope
  were rechecked, Hosted CI passed, and the PR was mergeable.
- Squash merge: the exact candidate tree was merged to canonical `main` as
  `1ede788b8b1c36bcc224cde15a5f6462c9b51938`.
- Retained branch: `agent/target-identity-decoupling-v1` exists and points to
  final candidate head `2dbd0c6735b4a0f081d1a064458750d73d870cfe`.

The lifecycle is accepted and closed. Its authority effect remains `none`, and
it does not enter or authorize P15C.
