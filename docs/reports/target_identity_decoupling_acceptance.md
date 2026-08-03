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

## Candidate evidence

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
- Draft pull request: `apolo183/tool-system#171`, with 31 changed paths and
  candidate commit `89730ca1ab8e6f5eb5d3a78025a905df3cb568a8` / tree
  `008e2deaf5378e3d8052a657aff1b7d35b0d22d5` based directly on canonical
  `main@5e964adfd40502a3798630b98fb0d876bbd01d91`.
- Hosted CI: `tool-system-ci` run `30811492314` (`#1066`) passed. Its `verify`
  job completed tests plus active-gates, process-authority, current module-
  registry, and repository-manifest validation successfully.

The evidence-sync commit, its Hosted CI replay, final no-drift check, squash
merge, and retained-branch disposition remain pending and must be verified
before lifecycle completion.
