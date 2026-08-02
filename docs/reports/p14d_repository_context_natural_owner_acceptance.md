# P14D Repository Context and Natural Owner Acceptance

Status: `P14D_ACCEPTED_ISOLATED_FIXTURE_ONLY`

## Decision

P14D is accepted for one versioned `repository-context@1.0.0` module and its
`repository-context-api@1.0.0` public interface. The accepted claim is limited
to deterministic, bounded, read-only construction of repository context and a
non-authorizing natural-owner proposal from clean local Git fixture snapshots.

This acceptance does not authorize P14E, access to a real downstream
repository, repository mutation, model-provider execution, credential access,
production operation, cleanup, rollback execution, or branch deletion.

## Frozen source and scope

- canonical repository: `apolo183/tool-system`
- baseline commit: `7e3a114a25d70c3ebecc952f13ce68b1adbbbc80`
- baseline tree: `7c36c0992a82098cf300942052b515139c7560bf`
- task identity: `P14D-REPOSITORY-CONTEXT-LIFECYCLE-v1`
- source owners:
  - `src/tool_system/repository_context/__init__.py`
  - `src/tool_system/repository_context/builder.py`
- compound contract:
  `docs/modules/repository-context-contract-v1.md`
- execution boundary: temporary isolated local Git fixture repositories only

The implementation and publication task is bound to the exact nineteen paths
listed by its task manifest and change plan. No blueprint, stable-principles,
provider, credential, process-authority, repository-controller, target-adapter,
or downstream path is modified.

## Accepted behavior

The module:

1. requires one exact repository top level, expected 40-character HEAD,
   clean worktree, tracked blueprint and governance evidence, query terms, and
   finite limits;
2. reads committed blobs through hardened local Git with optional locks, lazy
   fetch, replacement objects, hooks, prompts, and global/system configuration
   disabled;
3. builds a deterministic tracked-file index bound to HEAD, tree, tracked-set,
   selected-context, object, and content digests;
4. extracts local Python and TypeScript/JavaScript import relationships and
   maps related tests;
5. selects relevant context from mandatory evidence, query matches, explicit
   seed paths, dependency closure, and mapped tests under file and byte limits;
6. fails closed on stale or dirty state, unsafe or missing paths, unsupported
   tracked entries, symlink inputs, binary or non-UTF-8 required content,
   source parse failures, exceeded limits, or insufficient implementation
   evidence;
7. revalidates the snapshot after construction and exposes a later freshness
   check; and
8. returns a natural-owner proposal whose `authority_effect` is `none`.

## Fixture evidence

The focused acceptance suite covers:

- a Python package with local dependency and test mapping;
- a TypeScript package with relative dependency and test mapping;
- explicit seed evidence when a query does not match;
- deterministic repeated construction;
- dirty worktree, stale HEAD, missing evidence, invalid path, empty query, and
  non-top-level root rejection;
- binary, oversized, and symlink-root rejection;
- insufficient natural-owner evidence; and
- inspection of every module-owned Git subprocess environment and verb to
  prove the read-only, no-remote command boundary.

Module registry, compound-contract, static import graph, repository-manifest,
phase-alignment, focused P14D, and full-suite validation are required by the
frozen terminal predicate. Hosted CI must pass on the unchanged candidate
before merge; PR or CI metadata records the publication result but cannot
redefine or reopen this acceptance set.

## Zero-operation and non-claim evidence

- real downstream repository accesses: `0`
- repository writes by the module: `0`
- network operations by the module: `0`
- provider invocations: `0`
- credential-value accesses: `0`
- GitHub approval comments created or read: `0`
- production operations: `0`
- cleanup or rollback operations: `0`

The accepted fixtures prove the P14D bounded context and evidence boundary;
they do not prove end-to-end autonomous implementation, multi-repository
benchmark readiness, production readiness, or Codex replacement.

## Successor boundary

`P14E_BLUEPRINT_COMPILER` is the next blueprint stage and remains unauthorized.
Any P14E implementation requires a new exact current-main audit and its own
frozen single-problem task contract.
