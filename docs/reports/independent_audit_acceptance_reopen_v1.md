# Independent audit acceptance reopen v1

## Decision

At canonical `tool-system` `main@eab919368a1a35d6dc73f329f320700ca4df6c13`
(tree `955d64dfc85720377e6382c3bf7bae6708834134`), the independent audit
findings require governance stop-and-reopen treatment. This package therefore:

- reopens the current
  `accepted_subscription_worker_public_entry_core` conclusion;
- reopens the P16D recovery-planning acceptance contribution;
- retains only the demonstrated P16G capacity, renewal-review, and
  deterministic owner-reviewed channel-choice boundary;
- returns P16G completion forecast, total economic cost, quota,
  concentration-risk, and provider-outage outputs to unaccepted status; and
- marks the dependent P16H and P16I closure as requiring revalidation.

This is a descriptive governance correction with `authority_effect: none`. It
does not revert Git history or discard valid implementation evidence. It adds no
runtime lifecycle enum and changes no runtime code, module contract, blueprint,
policy, or workflow.

## Finding register

| ID | Classification | Current disposition | Evidence boundary |
| --- | --- | --- | --- |
| TS-B01 | confirmed blocker | Blocks real-repository execution; public-entry acceptance reopened. | At the frozen base, the code reviewer checks candidate shape, string contents, and allowed scope, while the contract reviewer accepts PASS validation plus the copied acceptance list. Neither binds an acceptance item to independent diff or behavioral evidence. The audit's adversarial wrong-implementation/PASS-validation reproduction therefore remains material. |
| TS-B02 | confirmed blocker | Blocks real-repository execution; public-entry acceptance reopened. | `src/tool_system/gate/command_runner.py` invokes ordinary host `subprocess.run(..., shell=False, ...)`; `shell=False` is not filesystem, process, or network isolation. Public zero-side-effect fields are constructed boundary values rather than OS audit observations, and the worker executable is configured by command name rather than a resolved binary identity and digest. |
| TS-H01 | confirmed high-risk defect | Uncorrected. | The v2 closeout records zero actual validation commands but a public count of one, plus terminal task `FAILED` while the durable run remains `ACTIVE`. The current task-runner counter is derived from the validation-set size and worker-call count, and its failure path does not terminally fail the run. The real-worker timeout cause remains unknown. |
| TS-H02 | confirmed high-risk defect | P16D acceptance contribution reopened. | `BackupVerification` has no canonical manifest identity and `plan_restore()` does not bind a PASS verification to the supplied manifest. A verification for one manifest can therefore be paired with another manifest. |
| TS-H03 | confirmed high-risk acceptance mismatch | Broad P16G outputs reopened; narrow evidence retained. | `src/tool_system/subscription_capacity/policy.py` implements caller-supplied integer-PPM capacity decisions, renewal review, and deterministic owner-reviewed channel choice. It does not implement completion forecast, total economic cost, quota, concentration risk, or provider-outage outputs previously claimed by the P16 acceptance mapping. |
| TS-M01 | pending reliability risk | Uncorrected. | Command and worker output is fully buffered before `max_output_bytes` is evaluated, so the configured ceiling is not a streaming memory bound. |
| TS-M02 | pending CI/supply-chain risk | Uncorrected. | The current workflow covers Python 3.11 pytest and four governance validators, but not the proposed Python matrix, Ruff, dependency audit, secret scanning, immutable Action SHAs, or a dependency lock. |

The two blocker findings are sufficient to prohibit real-repository public-entry
execution. The high- and medium-risk findings remain separately scoped future
work. This package authorizes none of their implementation corrections.

## Historical evidence retained without rollback

The following canonical merges remain valid historical implementation or test
evidence and are not reverted:

| PR | Canonical commit | Evidence retained |
| --- | --- | --- |
| #217 | `983e225377fdef23a18368c9e662f8231d6aaec8` | completed-receipt replay ordering correction |
| #218 | `8be8950937407bbca0c562b77348c67aba6b5685` | deterministic Python and TypeScript fake-I/O acceptance evidence |
| #219 | `0c710929e292b340538845a5e9e87c03c36f5794` | historical public-entry acceptance record, now reopened by this decision |
| #220 | `027dbb3fb83c38def70e81d58712f80dbe613483` | durable pre-dispatch call accounting and covering-lease correction |

Their source changes and receipts remain in history. Reopening means only that
the active acceptance conclusion may no longer be consumed as proof that the
public entry is safe for a real repository.

## P16 affected-closure disposition

P16D is reopened because restore readiness can consume verification from a
different backup manifest. Its existing exact-entry verification and non-live
planning evidence remains historical, but it is unavailable to a dependent
acceptance until manifest identity is bound and revalidated.

P16G retains only this demonstrated narrow boundary:

1. caller-supplied integer-PPM capacity status;
2. pre-renewal review status without purchase or renewal authority; and
3. deterministic eligible-channel selection that still requires owner review.

Completion forecast, total economic cost, quota, concentration risk, and
provider-outage outputs are unaccepted. Because the P16H readiness aggregation
and P16I decision consumed the broader P16D/P16G closure, both require affected
downstream closure revalidation. Their prior reports, publication receipts, and
non-live evidence remain historical; their current acceptance effect does not.

## Authority and stop boundary

This package performed only deterministic repository reads, governance edits,
tests, and authorized PR publication. It authorizes zero real Codex worker,
ChatGPT web automation, API/provider, credential-value, real-downstream,
runtime-remote, production, deployment, cleanup, or rollback operations.

Real Codex Worker execution, real downstream access, and v3 isolated acceptance
remain unauthorized. No TS-B01, TS-B02, TS-H01, TS-H02, TS-H03,
TS-M01, or TS-M02 implementation correction is part of this package. After the
governance package merges, work stops pending separately authorized correction
packages.
