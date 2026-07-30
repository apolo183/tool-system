# P14C PR Authorization Gate

Status: `IMPLEMENTED_LOCAL_VALIDATION_PASS_DRAFT_PR_PENDING`

This record controls the narrow `P14C-PR-AUTH-GATE-v1` correction. It is an
implementation and evidence record, not lifecycle authority, P14C acceptance,
or authority for a provider, credential, downstream repository, cleanup,
rollback, or production action.

## Parent and global alignment

The immediate parent is
`docs/reports/p14c_bounded_real_model_provider_execution.md`: corrected P14C
source is merged, while live execution and acceptance remain blocked. The
global owner is `blueprint/tool_system_v0.yaml:product_objective`, which
requires repository publication to remain separately authorized and every
change to be traceable to exact authority.

The natural owner is `repository-controller`. This is an
interface-compatible fail-closed hardening from module `1.0.0` to `1.1.0`; the
aggregate `repository-controller-api@1.0.0` decision and result shapes remain
stable. Direct consumers are revalidated without changing their unrelated
responsibilities. Fresh dependency tracing also requires the canonical module
mapping in `docs/tool_system_module_registry_contract_v1.md` to record the
module-version and rollback-identity change; this is registry metadata for the
same natural-owner change, not a second module implementation.
The registry's exact byte and semantic seals in
`tests/test_module_registry.py` are re-derived from that same final registry
state.
The three new retained non-authority task/evidence files also update the
repository-manifest count seal without changing any formal authority row.

## Reproduced defect

On the current parent tree, a tool-system lifecycle decision returns `PASS`
even when the task-manifest approval is populated with the wrong repository,
`pr_ready` action, wrong base, and stale head. The tool-system repository policy
uses the legacy `manifest` lifecycle mode, so those fields are not bound by the
shared validator.

Separately, a passing action plan can call the injected action runner with no
independent mutation capability. Green CI and a caller-created mapping therefore
do not form an independent repository-action boundary.

## Locked implementation

The repository controller will:

1. require lifecycle approval as a parameter separate from the task manifest;
2. bind it to the exact repository, PR number, `pr_merge` action, base branch,
   current head SHA, named record, approver, source, timestamp, and reason;
3. derive a canonical SHA-256 digest of the bound record and carry that digest
   into the action plan and audit result;
4. require every non-dry-run action to consume one opaque capability bound to
   the repository, PR, squash action, base, head, approval digest, and runner
   kind;
5. consume the capability before invoking the runner and reject replay;
6. provide only a private injected-test capability issuer in this source.

The final point is intentional. Current CI, task manifests, PR bodies, and chat
citations are not authenticated lifecycle-authority sources. A future live
issuer must be separately designed, must authenticate an external authority,
and must materialize an exact one-shot capability. Until then, the supported
controller path can evaluate and dry-run but cannot execute a real GitHub
mutation.

PR Ready remains unsupported. A Draft-creation approval cannot be interpreted
as Ready or merge authority.

## Verification and evidence

The implementation base is tool-system
`632132b87d10c2cf705149fbcc6832e7d165acd9`; the single planned branch is
`agent/p14c-pr-auth-gate-v1`.

Local validation recorded on 2026-07-31:

- task manifest and exact change-plan binding: `PASS`;
- focused repository-controller, consumer, registry, and manifest suite:
  `113 passed`;
- full repository suite: `509 passed`, executed as three non-overlapping
  complete file partitions (`162 + 113 + 234`) to remain within the execution
  host's per-call yield limit;
- Ruff on every changed Python file: `PASS`;
- source and test compilation: `PASS`;
- legacy active-gate replay: `PASS`;
- process-authority validation: `PASS`, including `108` replay-only pairs and
  no execution authority;
- current module-registry validation: `PASS`, with `14` modules, `100` owned
  paths, and `152` contract references;
- repository-manifest validation: `PASS`, with `204` formal paths, `295`
  retained non-authority paths, `499` tracked paths, and zero unclassified
  paths;
- exact scope comparison: only the `21` paths in the current change plan
  differ from the implementation base;
- real GitHub mutation, provider call, credential-value access, downstream
  access, cleanup, rollback, and production action counts: all `0`.

Hosted CI remains required after Draft PR publication.

## Stop condition and non-claims

Stop if the implementation needs a live capability issuer, real GitHub
mutation, provider or credential access, P14C live proof or acceptance, P14D,
downstream access, cleanup, branch deletion, rollback execution, or production
deployment.

This milestone does not claim that CI can authenticate a ChatGPT authorization,
does not grant a repository mutation capability, and does not accept or close
P14C.
