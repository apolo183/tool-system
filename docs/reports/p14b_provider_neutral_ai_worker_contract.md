# P14B Provider-Neutral AI Worker Contract

status: ACCEPTED_CLOSED
phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT
stage: P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT
parent: docs/reports/p14a_blueprint_to_code_phase_entry_and_contract.md
validated_main: 9acac526c4579f69f792bd0770d962f6540ab5b1
authorized_by: user_authorized_p14b_source_implementation_lifecycle

## Single objective

Implement the provider-neutral, structured, content-addressed AI worker request/result boundary and a deterministic in-memory fixture provider with bounded resources, cancellation, stable errors, secret-free audit records, response validation, and replay-safe idempotency.

P14B supplies a contract and local deterministic evidence only. It makes no live model call, accepts no provider credential, opens no network connection, writes no project repository, mutates no remote target, and deploys nothing.

## Parent and global alignment

Parent alignment: P14A assigns P14B the exact missing link between record-only workers and a separately gated real model provider. This stage owns only that interface, its deterministic fixture, and contract evidence.

Global alignment: `blueprint/tool_system_v0.yaml:product_objective` requires structured AI worker requests/results, bounded execution, auditable evidence, deterministic replay, and no silent authority expansion before the later blueprint-to-code loop can be built. P14B closes only the provider-neutral contract portion of that flow.

## Natural owner and preserved owners

The new natural owner is:

```text
src/tool_system/ai_worker/**
tests/test_ai_worker_*.py
```

The accepted P11-P13 `agent_worker`, process runtime, worker adapter, durable orchestrator, policy, repository controller, and target-repository owners remain unchanged. The existing `NoMutationAgentWorker` remains the default role worker.

## Request contract

Every request binds:

```text
request_id
idempotency_key
attempt_number
operation
execution_mode=fixture
provider_id and model_id
declared model capabilities and context window
prompt_id and prompt_version
required capabilities
content-addressed structured inputs
required structured-output keys
positive integer input/output/total-token ceilings
positive integer timeout ceiling
non-negative integer cost ceiling in microunits
secret-free metadata
writes_target_repo=false
executes_target_repo_mutation=false
production_deployment=false
```

Input content is canonical JSON, and every supplied SHA-256 must match its payload before provider execution. Duplicate input ids, non-canonical values, secret sensitivity, secret-like metadata keys, missing model/prompt versions, capability mismatch, invalid budgets, or any mutation/production flag fail closed.

P14B deliberately has no credential field. A future live provider may receive a named credential reference only out of band under the separately authorized P14C execution packet; credential material must never enter this request, replay store, result, or audit contract.

## Result and audit contract

Every terminal result records a stable status, request and idempotency identity, request hash, provider/model/prompt metadata, structured output hash, integer usage, stable error code and retryability, replay marker, and bounded evidence.

Audit records include input ids, kinds, media types, sensitivities, byte counts, and payload hashes, but never input payloads or metadata values. Result audit records include the output hash but never output content or raw provider exception text.

The stable error taxonomy is:

```text
INVALID_REQUEST
INPUT_INTEGRITY
CAPABILITY_MISMATCH
PROVIDER_MISMATCH
BUDGET_EXCEEDED
CANCELLED
TIMEOUT
PROVIDER_FAILURE
INVALID_RESPONSE
REPLAY_CONFLICT
INTERNAL_FAILURE
```

## Resource, cancellation, and response gates

- input token estimation is deterministic and checked before provider invocation;
- declared maximum output plus input ceilings must fit both the total-token and model-context ceilings;
- output tokens, total tokens, logical duration, and cost are checked before a result can pass;
- a cancellation signal checked before and during the provider boundary yields `CANCELLED` without output;
- provider exceptions are converted to a sanitized `PROVIDER_FAILURE` containing only the exception type;
- outputs must be finite canonical JSON mappings containing every required key;
- failed validation never returns a passing output.

P14B logical fixture duration proves contract behavior only. Actual wall-clock timeout, cancellation, network, credential, and provider retry controls belong to P14C.

## Replay-safe idempotency

The in-memory replay store serializes fixture execution per runtime instance. An identical canonical request with the same idempotency key returns the stored terminal result with `replayed=true` and does not reinvoke the provider. Reusing the key with any different canonical request returns `REPLAY_CONFLICT` and does not replace the accepted entry.

The runtime re-hashes the request after provider return and blocks provider-side request mutation. Stored and replayed structured outputs are separate canonical copies, so caller mutation of a returned result cannot corrupt the replay entry or its output hash.

This is deterministic single-process evidence, not durable or distributed exactly-once execution. P14G must integrate later P14 actions with the accepted durable orchestrator.

## Deterministic fixture provider

The fixture provider is constructed from explicit operation-to-response scenarios. It performs only in-memory canonicalization and counting, has zero implicit network or filesystem behavior, requires exact provider/model identity, and exposes a call count for no-duplicate-replay evidence. Scenarios can deterministically produce structured success, stable provider failure, logical timeout, budget excess, invalid output, or cancellation.

The P14B runtime also requires provider metadata to declare `provider_kind=deterministic_fixture`, `execution_mode=fixture`, and false external-provider, credential, and network flags before invocation. This is a fail-closed contract guard against accidental live-adapter use, not containment against a malicious provider that lies about its implementation; P14C must supply the separately authorized live boundary.

## Exact file scope

```text
src/tool_system/ai_worker/__init__.py
src/tool_system/ai_worker/contract.py
src/tool_system/ai_worker/runtime.py
src/tool_system/ai_worker/fixture_provider.py
tests/test_ai_worker_contract.py
tests/test_ai_worker_fixture_provider.py
tests/test_phase_alignment.py
tests/test_p14_phase_entry_contract.py
docs/reports/p14b_provider_neutral_ai_worker_contract.md
examples/task_manifests/tool_system_p14b_provider_neutral_ai_worker_contract.yaml
examples/change_plans/tool_system_p14b_provider_neutral_ai_worker_contract.yaml
examples/active_gates.yaml
blueprint/tool_system_v0.yaml
README.md
AGENTS.md
```

## Acceptance evidence target

```text
request_and_result_contract_tests: PASS
content_hash_and_structured_output_validation: PASS
capability_prompt_and_provider_binding: PASS
input_output_total_context_time_and_cost_budgets: PASS
cancellation_and_stable_error_taxonomy: PASS
secret_free_request_and_result_audit: PASS
same_request_replay_without_provider_reinvoke: PASS
same_key_different_request_conflict: PASS
fixture_provider_external_io: none
full_repository_tests: PASS
active_gates: PASS
live_provider_calls: 0
target_repo_mutation: false
production_deployment: false
```

## Claim boundary

P14B does not prove a real model provider, model quality, actual token metering, wall-clock provider timeout, provider credential handling, provider-network isolation, durable replay, repository context selection, blueprint compilation, patch generation, test repair, local Git orchestration, remote target safety, production readiness, or Codex replacement.

## Local execution evidence

```text
content_addressed_request_and_structured_result_contract: PASS
model_capability_provider_and_prompt_version_binding: PASS
input_output_total_context_time_and_cost_budget_gates: PASS
cancellation_and_stable_error_taxonomy: PASS
secret_sensitivity_and_secret_like_metadata_preflight: PASS
request_audit_payload_and_metadata_value_redaction: PASS
result_audit_output_and_idempotency_value_redaction: PASS
provider_exception_text_redaction: PASS
provider_response_shape_usage_error_and_output_validation: PASS
request_post_invoke_hash_binding: PASS
stored_replay_output_copy_isolation: PASS
same_request_concurrent_replay_provider_invocations: exactly_one
same_key_different_request: REPLAY_CONFLICT
live_provider_metadata: blocked_before_invoke
fixture_filesystem_and_network_probe: no_IO
focused_contract_alignment_tests: PASS_33
full_repository_tests: PASS_295
python_compileall: PASS
change_plan: PASS
active_gates: PASS
git_diff_check: PASS
creator_owned_test_and_bytecode_roots: removed
live_provider_calls: 0
credential_access: 0
target_repo_mutation: false
production_deployment: false
```

## CI acceptance and closure evidence

```text
candidate_remote_head: 8eb2689387dd1b3691987aeb31789f44ca87a5e9
candidate_base: 9acac526c4579f69f792bd0770d962f6540ab5b1
candidate_compare: ahead_1_behind_0
candidate_diff: 15_files_2180_additions_28_deletions
github_actions_workflow: tool-system-ci
github_actions_run: 29182069373
github_actions_run_number: 935
github_actions_conclusion: success
closure_record_scope_delta: this_report_only
final_closure_gate: closure_head_CI_success_and_squash_merge_required
```

P14B acceptance and closure are effective only when the closure-record head itself passes GitHub CI, the same PR squash-merges to `main`, and fresh-state verification confirms the merged state. The accepted module is limited to the provider-neutral contract and deterministic fixture boundary described here. No P14C authority follows from this closure.

## Rollback and stop condition

Before merge, rollback is closing the unmerged P14B PR while retaining its head as evidence. After merge, rollback requires a named revert packet and PR; no reset or force-push. Creator-owned temporary test roots and bytecode are removed after validation. Branch cleanup, including `dummy-unused`, remains separately gated.

After focused tests, full tests, active gates, CI, squash merge, and fresh-main verification pass, P14B is accepted and closed at this bounded scope. Stop at P14C: no real provider/model/credential/network/cost execution may occur without a separately named and explicitly authorized packet.
