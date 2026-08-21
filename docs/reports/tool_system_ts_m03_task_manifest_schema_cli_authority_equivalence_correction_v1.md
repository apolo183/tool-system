# TS-M03 Task-Manifest Schema/CLI Authority Equivalence Correction v1

## Decision and boundary

This report records the implementation evidence for
`TOOL-SYSTEM-TS-M03-TASK-MANIFEST-SCHEMA-CLI-AUTHORITY-EQUIVALENCE-CORRECTION-v1`
against canonical base `427046c7c99dea569b67f2768fa1577dfe838faf` and tree
`3a41ecfd6ff65737fb30366a5791ce77579acbd8`. It grants no execution,
repository mutation, lifecycle, cleanup, or public-acceptance authority.

The correction makes `harness/task_manifest.schema.json` the sole structural
authority used by the shared task-manifest validation boundary. It does not
migrate retained historical manifests and does not alter their non-authority
classification.

## Implemented correction

- `validate_manifest_structure()` lazily loads `jsonschema==4.26.0`, checks the
  local Draft 2020-12 Schema, and returns deterministic project-owned error
  codes without relaying upstream validator prose.
- The parsed-value guard rejects non-JSON values, non-finite numbers,
  non-string mapping keys, and cycles; shared acyclic objects remain valid.
- Local Schema preparation rejects unavailable, malformed, meta-invalid,
  remote, dynamic, recursive, and nested-identity Schema authority.
- The formal Schema adds only the frozen strict `alignment` and
  `historical_fixture` vocabulary. Unknown root and nested fields fail closed.
- One read-only, zero-command synthetic task/change-plan pair and strict active
  gate index replace retained examples as the Hosted positive smoke input.
- `manifest-validation` advances to `1.0.1`; its aggregate interface remains
  `manifest-validation-api@1.0.0`. The exact Schema and three synthetic data
  paths are registered as read-only module data.

## Dependency and license

The only new direct dependency is `jsonschema==4.26.0`, used through
`Draft202012Validator` and imported only inside structural validation. Its
upstream license is MIT. No lock, workflow action, runner, permission, or
supply-chain behavior is changed.

## Compatibility and safety evidence

The frozen-base shadow run reproduced exactly `127` Schema-induced failures
across the predicted `42` consumer test files. Those tests now distinguish the
strict active synthetic pair from retained historical evidence: retained byte,
scope, state, seal, report, and non-authority assertions remain intact, while
invalid historical CLI PASS claims become deterministic Schema BLOCK claims.

Subscription preflight, context, execution, and multi-stack public-entry tests
prove that unregistered root or binding fields block before worker, subprocess,
repository-context, Git-write, lease, call, receipt, provider, or remote effects.
There is no unsafe fallback to the removed hand-written validator.

## Verification record

Final local and Hosted verification results, exact commit/tree identities, and
publication evidence are recorded by the pull request checks. Required gates
are the focused Schema/consumer suite, full pytest, strict active-gate,
process-authority, module-registry, repository-manifest validators, exact
58-path/mode closure, and `git diff --check`.

## Preserved state and stop

TS-B02 remains a confirmed blocker; real repository execution remains closed.
TS-B01 corrected-pending-reacceptance, public-entry non-acceptance, and all
other audit findings remain unchanged. This correction does not start TS-B02A
or perform any real workload, Codex, subscription, provider, or repository
execution. After publication, work stops at the separately authorized TS-B02A
precondition.
