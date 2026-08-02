# P14C bounded real provider acceptance

Status: `P14C_ACCEPTED_BOUNDED_DEEPSEEK_PROOF`

## Decision

`P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION` is accepted under
`P14C-DEEPSEEK-RESULT-ACCEPTANCE-v1`.

The accepted proof is one source-sealed, owner-approved, single-host DeepSeek
execution. It satisfies the P14C objective of proving one bounded real AI-worker
path with explicit secret, network, timeout, retry, cost, validation, and audit
boundaries. It does not authorize another provider call or entry to P14D.

## Alignment

- Parent stage: `P14MR_MILESTONE_MODULE_INVARIANT`, previously accepted.
- Blueprint stage: `P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION`.
- Product objective: prove one bounded real AI worker without expanding target
  repository, production, or cleanup authority.
- Acceptance authority: the explicit user authorization packet
  `P14C-DEEPSEEK-RESULT-ACCEPTANCE-v1`; this report and the descriptive project
  state do not grant authority.

## Frozen source and publication evidence

- Canonical repository: `apolo183/tool-system`.
- Executed main commit: `55ed92e336d2aa110e50e197c5eefb8fa80896a8`.
- Executed tree: `2e6ce267738a396f52a5847052f91edafea74af9`.
- Recovery source PR: `#157`.
- Recovery source head: `e814f5d0e68e8819c8366019289c2bd26acdec76`.
- Recovery source Hosted CI: `#1037`, successful before merge.
- Execution host: `apolo-9004`.
- Source manifest SHA-256:
  `c2932b312b69804535dda1fde43caf90f7118f510870f19c00aa362641fdd112`.
- Source seal SHA-256:
  `1d7688faf8be7950ff88b359af2d726ccaea52e832a33796defd08c3793f2019`.
- Single-host replay-ledger instance:
  `1f8f11e844f5ab829e38cecfc1b988d9aedb897ee9af543df011dd9397228fde`.

The execution commit, tree, host, source manifest, and ledger instance all match
the prepared approval binding. The worktree was clean. No multi-host exactly-once
claim is made.

## Owner approval and durable consumption

- Approval issue/PR: `#157`.
- Approval comment ID: `5158008082`.
- GitHub owner: `apolo183`.
- Comment timestamps matched at the read-only audit boundary, so the comment was
  unedited.
- Approval record SHA-256:
  `61715c0b87e46b871016265cf88a0ca6c8b9e4383c444ea41db5374192173e5d`.
- Approval was durably consumed before credential resolution.
- The execute entry created zero GitHub approval comments. The one external
  owner comment was created by the operator and was read once for this acceptance
  audit; acceptance publication creates or reads no additional approval comment.

## Redacted PASS receipt

| Field | Accepted value |
| --- | --- |
| status | `PASS` |
| error | `null` |
| packet | `P14C-DEEPSEEK-RECOVERY-v1` |
| packet SHA-256 | `4ae138a24e9bf956b3ad00d665eb5413b45652e18eda9e4032666600e22a1376` |
| request ID | `p14c-001` |
| request SHA-256 | `6c78848329958f6e96255fdabe215cc06736ecdfb4e7a6c5524a5912efe9b777` |
| provider | `deepseek` |
| model | `deepseek-v4-flash` |
| endpoint | `https://api.deepseek.com/chat/completions` |
| credential reference | `file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key` |
| credential resolutions | `1` |
| provider invocations | `1` |
| transport-attempt ceiling | `1` |
| input tokens | `106` |
| output tokens | `39` |
| total tokens | `145` |
| duration | `1770 ms` |
| conservative cost | `184 microUSD` |
| output SHA-256 | `16a6f16328aad19a4d64aa4ff329c7e78e02a09a270e2b55bb3f795a3e6bba33` |

The receipt contains neither the credential value nor raw provider output. The
accepted values remain inside the frozen ceilings of 1152 total tokens, 25
seconds, 2000 microUSD, one provider invocation, and at most one transport
attempt. The receipt explicitly keeps target-repository mutation, production,
cleanup, and P14D authorization false.

## Acceptance boundary

This acceptance proves only the bounded DeepSeek connectivity and response path
described above. It does not prove or authorize:

- another real provider invocation or credential-value read;
- a provider pool, automatic fallback, model ranking, or P15 economics runtime;
- general production readiness or multi-host exactly-once execution;
- target-repository access or mutation;
- P14D work, downstream operations, deployment, cleanup, rollback, or branch
  deletion;
- retention of raw model output or disclosure of any secret.

The historical implementation reports remain historical evidence of their
source-only and failed-attempt boundaries. Current progress is owned only by
`docs/tool_system_project_state_v1.yaml`, whose `authority_effect` remains
`none`.

No provider was called and no credential value was read while auditing or
publishing this acceptance record.
