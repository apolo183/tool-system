# TS-H04/H05 installation and behavior repair; H06 publication facts

This batch repairs installed Schema loading and restores the existing public-entry
behavior tests. It is authorized for one branch and one **Draft** pull request;
it does not authorize Ready, merge, auto-merge, deployment, real Codex, a provider,
or isolated-backend execution. `real_repository_execution_blocked: true` remains.

The parent objective is the existing task-runner public-input contract and the
project-neutral `product_objective` in `blueprint/tool_system_v0.yaml`. The exact
task pair is `ts_h04_h05_installation_and_behavior_repair_v1_task.yaml` and
`ts_h04_h05_installation_and_behavior_repair_v1_plan.yaml` in this directory.
Reasoning: **Extra high**. Continuous budget: 7,200 seconds; at most three repair
cycles and two complete regressions, counting local and hosted runs together.
No subagent or separate independent review is claimed.

## Baseline and changes

Canonical base: `75d005cee55a0e33bea17808faaba3085f740d8c`.
Base tree: `3f3263c305b1a5d50cb7760d9bb26d37c65d095e`.
Branch: `agent/ts-h04-h05-installation-and-tests-v1`.

| Finding | Baseline defect | Correction and limit |
| --- | --- | --- |
| TS-H04 | Runtime locates the Schema by walking to a source-checkout `harness` directory; that file is absent from installed packages. | A build-only hook copies the sole authored Schema into `tool_system.manifest`, includes its inputs in the sdist, and runtime reads the packaged resource. Only the known source layout uses the canonical checkout file. |
| TS-H05 | The closed root Schema rejects the two public-entry mappings already required by the task-runner contract; twelve test functions return before their intended behavioral assertions. | Closed typed definitions for both mappings, nested obligations and finite budgets; current valid base fixtures; removal of all twelve early returns. Runtime exact-binding, evidence, digest, policy and caller checks are unchanged. |
| TS-H06 | PR-body lifecycle restriction and later lifecycle events need a truthful reconciliation record. | Observed facts below; historical external authorization stays UNKNOWN. This is not retroactive approval or proof of an unauthorized action. |

There is no second authored Schema: the installed resource is a build projection
of `harness/task_manifest.schema.json`, checked for byte identity. The build hook
and installed-package test are package-maintainer responsibilities registered
exactly in REPO_MANIFEST. Existing module contracts and registry bytes remain
unchanged: the task-runner already specifies both public-entry mappings. No
contract is weakened to admit a new runtime effect. A structurally valid mapping
does not authorize execution.

The installed-artifact test builds an sdist and then a wheel from it, installs
non-editably, and imports outside the checkout with cwd, environment import paths
and editable `.pth` hooks disabled. It checks installed module/resource location,
canonical resource bytes, valid and invalid manifests, and missing-resource BLOCK.
CI runs that test explicitly, then the rest of the suite without duplicating it.

The recovered behavior assertions exercise context compilation, one fake-worker
local commit, timeout accounting, unknown-commit replay refusal, Python/TypeScript
implementation and repair, scope denial, cancellation, completed replay, and
unreceipted advancement. Worker adapters remain injected fakes in this evidence.
The byte-drift and stale-head negative tests now assert their actual runtime
rejection causes. Historical malformed-manifest rejection remains separate.

## H06: current observations, historical events, unknown authorization

Read-only GitHub API observations in this task on 2026-09-17 bind the following
facts. The timeline events themselves occurred on 2026-09-10; they are not
operations performed by this repair task.

- [PR #234 body and identity](https://api.github.com/repos/apolo183/tool-system/pulls/234)
  identifies head `b62039d267abcf5fcbb3edcdffd0b6e07ed76263`, merge commit
  `75d005cee55a0e33bea17808faaba3085f740d8c`, and asks: “Keep this PR Draft.”
  It also explicitly withholds Ready/merge/auto-merge and host-operation authority.
- [PR #234 timeline](https://api.github.com/repos/apolo183/tool-system/issues/234/timeline)
  records `ready_for_review` at `2026-09-10T08:50:33Z`, `merged` at
  `2026-09-10T08:50:50Z`, and `head_ref_deleted` at `2026-09-10T08:50:52Z`;
  the actor field is `apolo183` for all three.
- [PR #234 reviews](https://api.github.com/repos/apolo183/tool-system/pulls/234/reviews)
  returned an empty array. AGENTS permits ordinary authorized implementation
  without per-PR human review, so absence of a review is not proof of missing
  lifecycle authority.

These API fields do not establish whether a separate user authorization existed
outside the PR body. **Historical external lifecycle authorization: UNKNOWN.**
The body/event discrepancy is documented, not erased. No old PR text, accepted
four-Gate contract, historical receipts, merge commit, or completed audit is
rewritten, reverted or reopened here. No conclusion about malicious or
unauthorized action is supported by the available record.

For this batch, user authorization is explicitly limited to a Draft PR. Ready,
merge and auto-merge remain unauthorized; any later publication decision must
identify the actual candidate and rely on the corresponding explicit authority,
not this descriptive report or a test result. The new project-state section has
`authority_effect: none` and preserves the existing reopened acceptance state.

## Validation and bounded repair record

Historical `1072 passed` at the base is historical evidence only. It is not the
result of this batch and does not cover TS-B02 or uncorrected audit findings.

- Initial focused run: **2 failed, 106 passed in 22.94s**. Failures exposed the
  build hook's source-layout resolution and an incorrect restored stale-head
  assertion. Cycle 1 corrected those; **108 passed in 28.87s**.
- Initial governance tests: **3 failed, 74 passed in 16.49s**. Newly added files
  were not staged for the tracked-path validator, and unnecessary explanatory
  contract edits changed an existing exact registry seal. The two new files were
  staged; cycle 2 removed the unnecessary contract/registry edits.
- Next governance tests: **1 failed, 76 passed in 16.97s**. The remaining test
  hard-coded 299 formal files. Cycle 3 synchronizes its two exact counts to 301
  for the two already authorized additions. No assertion is removed or weakened.
  This directly dependent test was omitted from the initial file enumeration;
  its exact two-line responsibility is recorded in the change plan. The original
  objective, acceptance, time and attempt budgets remain unchanged.
- The initial task-manifest serialization used an uppercase ID and invalid
  `source_change` task type; before implementation these were corrected to the
  existing lowercase ID and `code_modify` enum. This did not change scope,
  acceptance or authority. The original task record is retained in the task log.
- Final local full-suite, four-validator and hosted head-specific outcomes are
  recorded below when available. A pending check is not PASS.

## Final local evidence

| Check | Actual local result |
| --- | --- |
| Full repository suite, Python 3.12 | **1087 passed in 132.41s**, exit 0; no skipped cases. Complete regression 1 of 2. |
| Focused Schema, public-entry and installed-artifact suite | **108 passed in 28.87s**, exit 0. |
| Final module-registry and repository-manifest tests | **77 passed in 17.81s**, exit 0. |
| Active gates, process authority, current module registry, repository manifest | **4/4 PASS**, exit 0 for each. |
| Current task manifest and change plan | **PASS**, empty reasons. |
| Patch whitespace check | `git diff --check` passed. |

The local full-suite tree was `f49d661e0d6a79cddce40c090d0ae3eaff948070`;
only this report's observed-results paragraph is finalized after that run. The
published head is then checked by the hosted workflow as complete regression 2
of 2 (installed-artifact test plus all remaining tests). Its actual run and job
are recorded on the Draft PR; this prepublication report does not pre-fill CI
success or require a bookkeeping commit to record it. No further repair or
complete-regression budget is implied. Creating the Draft PR is not milestone
acceptance or merge approval.

## Remaining work and disposition

TS-B02 real isolation, independent hard deadline, complete resource cleanup,
real-worker entry and final DGX ARM64 acceptance remain unverified. Manifest
deep-recursion limits, bounded streaming command output, and unrelated static,
dependency or secret-scanning work are outside this repair batch and are not
claimed fixed. The kernel/systemd design tasks retain their sealed terminal
states and budgets. No real backend or provider operation was performed here.

Rollback is a separately authorized revert or disposition of the unmerged Draft
PR. This task performs no rollback, branch deletion, cleanup or merge.
