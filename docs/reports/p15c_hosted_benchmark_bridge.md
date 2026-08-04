# P15C Hosted Benchmark Bridge

Status: `P15C_HOSTED_BRIDGE_SOURCE_IMPLEMENTED_PENDING_DRAFT_PR_BINDING_PRIVATE_BUNDLE_AND_PUBLICATION`

This record describes the generic Hosted execution bridge required to run the
already authorized P15C two-provider by two-case read-only matrix. It is source
evidence only. It does not accept P15C, authorize P15D, grant target mutation,
or serialize any operator-private target fact.

## Canonical basis

- Canonical source baseline: `432ab42b56e45a4fc469301cef17b7c35324e0f8`
- Canonical source tree: `283337d4429787d1cfe302ca7a7e37351d1fb15a`
- Accepted source PR: `#174`
- Retained source branch: `agent/p15c-runtime-control-plane-v1`
- Hosted bridge branch: `agent/p15c-hosted-benchmark-bridge-v1`
- Module replacement: `ai_worker_runtime@1.7.0` to interface-compatible
  `ai_worker_runtime@1.8.0`
- Aggregate interface: unchanged `ai-worker-runtime-api@1.0.0`

## Exact bridge

The bridge consumes three separately named GitHub repository Secret
references:

- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `P15C_PRIVATE_BUNDLE_B64`

The first two references already exist according to operator-supplied Secret
name evidence; their values were not read. The third is a bounded encrypted
operator bundle containing one exact private control object and its
content-addressed snapshot. Qwen and GLM are absent from the workflow.

`p15c_hosted.py` accepts only canonical base64 containing a bounded gzip tar.
The archive may contain exactly `control.json` and the regular snapshot files
named by its sorted allowlist. Traversal, absolute or non-canonical paths,
links, duplicate members, unknown roots, malformed JSON, duplicate JSON keys,
oversized input, and file-set drift block before the execution entry runs. The
validated projection is written only to a new owner-only ephemeral directory
outside the checkout.

The workflow is introduced by this change, so its activation uses the exact
`push` commit rather than a `pull_request.closed` event that requires the file
to have already existed on the default branch. The only executing job requires:

- push to `main`;
- `run_attempt == 1`;
- event `before` equal to the exact canonical baseline above;
- the squash title bound to this one Draft PR; and
- activation identifier `c5336d4bd331a747c00547f7b7d99558`.

The Draft PR number is bound after the PR is created and before Ready. A
no-drift merge is therefore the only ordinary event that can satisfy the job.
The source seal includes the workflow and Hosted helper, and the checkout uses
the pushed canonical SHA with persistent checkout credentials disabled.

The job materializes the private inputs once and invokes `p15c_entry --execute`
once. That execution embeds its own preflight and permits at most four provider
calls: exact OpenAI and DeepSeek packets over the deterministic and private
cases. There is no retry, fallback, tool call, provider web search, proxy,
target-repository checkout, response storage, or raw-response artifact.

Only `materialization.json` and `benchmark.json` under the public receipt root
may be uploaded, with a 14-day retention period. The private root, credential
store, policy, target packet, target snapshot, raw response, and usage ledger
are outside the artifact path.

## Frozen source scope

The corrected exact closure is 17 files:

1. `.github/workflows/p15c-read-only-benchmark.yml`
2. `REPO_MANIFEST.md`
3. `config/module_registry_v1.yaml`
4. `docs/modules/ai-worker-runtime-contract-v1.md`
5. `docs/reports/p15c_hosted_benchmark_bridge.md`
6. `docs/tool_system_module_registry_contract_v1.md`
7. `docs/tool_system_project_state_v1.yaml`
8. `examples/change_plans/tool_system_p15c_hosted_benchmark_bridge_v1.yaml`
9. `examples/task_manifests/tool_system_p15c_hosted_benchmark_bridge_v1.yaml`
10. `src/tool_system/ai_worker/p15c_benchmark.py`
11. `src/tool_system/ai_worker/p15c_hosted.py`
12. `tests/test_ai_worker_p15c_benchmark.py`
13. `tests/test_ai_worker_p15c_entry.py`
14. `tests/test_ai_worker_p15c_hosted.py`
15. `tests/test_module_registry.py`
16. `tests/test_p15c_hosted_benchmark_workflow.py`
17. `tests/test_repo_manifest.py`

The two consistency tests are the exact small-scope correction needed for the
new natural-owner and formal-file counts. No unrelated module or test is in the
closure.

## Source-stage evidence

- provider invocations: `0`
- provider network operations: `0`
- credential values read by this source task: `0`
- benchmark executions: `0`
- private target transfers: `0`
- target-repository accesses: `0`
- target mutations: `0`
- production operations: `0`
- cleanup operations: `0`
- rollback operations: `0`

## Remaining gate

Before Ready, the Draft PR number must replace the disabled `#0` workflow
binding, every local and Hosted check must pass on an unchanged main, and the
operator must add the generated one-line value as repository Secret
`P15C_PRIVATE_BUNDLE_B64`. The exact squash message then activates one Hosted
run. Any missing Secret, drift, validation failure, provider failure, or
non-PASS redacted receipt leaves P15C unaccepted and stops before P15D.
