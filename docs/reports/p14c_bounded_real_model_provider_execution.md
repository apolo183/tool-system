# P14C Bounded Real Model Provider Execution

status: VALIDATING
phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT
stage: P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION
parent: docs/reports/p14mr_milestone_module_invariant.md
provider_contract_parent: docs/reports/p14b_provider_neutral_ai_worker_contract.md
validated_main: c30df8c6955260d07fbf271f62d54a921ea26e86
authorized_by: user_approved_p14c_named_execution_packet_and_full_lifecycle

## Single objective

Implement and accept exactly one bounded real model-provider path that reuses the accepted P14B request/result interface and proves credential isolation, exact network restriction, actual timeout and cancellation control, bounded retry, cumulative cost control, strict response validation, redacted audit evidence, replay safety, and zero repository mutation.

P14C may send only the content-addressed non-sensitive synthetic fixture defined by this record. It may not read or transmit tool-system repository content, finance-us content, another target repository, user data, secrets, or production data.

## Parent and global alignment

Parent alignment: accepted P14MR requires P14C to be a versioned replaceable module with a public interface and bounded blast radius. Accepted P14B supplies the provider-neutral request/result contract and retains its fixture-only default boundary. P14C adds one separately authorized live adapter without replacing or weakening that default.

Global alignment: `blueprint/tool_system_v0.yaml:product_objective` requires a bounded real AI worker before repository context, blueprint compilation, implementation, repair, review, and local Git orchestration can be built. P14C closes only the real-provider transport link. It does not implement any downstream product link or grant repository authority.

## Versioned module contract

```text
module_id: P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION
module_version: 1.0.0
blueprint_objective_ref: blueprint/tool_system_v0.yaml:product_objective.invoke_bounded_real_ai_worker
direct_parent_refs:
  - P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT@1.0.0
  - P14MR_MILESTONE_MODULE_INVARIANT@1.0.0
natural_owner_paths:
  - src/tool_system/ai_worker/live_provider.py
  - src/tool_system/cli/run_p14c_live_evidence.py
  - tests/test_ai_worker_live_provider.py
input_contract: accepted P14B AIWorkerRequest plus the exact authorized P14C packet and synthetic fixture
output_contract: accepted P14B AIWorkerResult plus redacted per-attempt live audit evidence
public_interface: BoundedLiveAIWorkerRuntime.run(AIWorkerRequest, cancellation) -> AIWorkerResult
dependency_module_ids_and_versions:
  - P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT@1.0.0
  - P14MR_MILESTONE_MODULE_INVARIANT@1.0.0
content_hashes_and_expected_preconditions:
  main_sha: c30df8c6955260d07fbf271f62d54a921ea26e86
  packet_sha256: ec19a1039b1dbdf162be0b3acfe28897fec304221bc809aba9263bb86bbe9ee4
  live_provider_sha256: 3eef8a7beb416ec0fab1890d1111986256932946874758535ee65a64be46bf55
  live_cli_sha256: 8b0bb97b757e9c34656563568c41898ea79f9db169b870d6461f8e393634b61b
authorization_envelope: p14c-openai-gpt56-luna-v1
acceptance_tests_and_evidence: focused contract/transport tests, full tests, one bounded live PASS, CI, merge, fresh-main verification
invalidation_conditions: packet drift, provider/model/host/path/credential/budget drift, secret leakage, unbounded retry, invalid output acceptance, repository input, target mutation, or production action
rollback_and_cleanup_disposition: close unmerged PR or named git-revert PR; remove creator-owned temporary evidence only; no branch cleanup
replacement_or_supersession_ref: none
```

An interface-compatible P14C replacement must keep the P14B request/result public interface and revalidate direct dependents. It must not change P11–P13, P14MR, repository-control, policy, or unrelated modules. An incompatible replacement requires a new module version and explicit impact record.

## Named execution packet

```text
packet_id: p14c-openai-gpt56-luna-v1
provider_id: openai
model_id: gpt-5.6-luna
api_method: POST
api_host: api.openai.com
api_port: 443
api_path: /v1/responses
tls_verification_required: true
redirects_allowed: false
proxy_environment_used: false
credential_reference: env:OPENAI_API_KEY
reasoning_effort: none
store: false
tools: none
structured_output: strict_json_schema
operation: p14c-synthetic-normalize
prompt_id: p14c-synthetic-normalizer
prompt_version: v1
max_input_tokens_per_attempt: 4096
max_output_tokens_per_attempt: 512
max_total_tokens_per_attempt: 4608
max_attempts: 2
max_cumulative_tokens: 9216
request_timeout_ms: 20000
live_evidence_wall_clock_ms: 45000
max_cumulative_cost_microusd: 20000
input_price_microusd_per_token: 1
output_price_microusd_per_token: 6
retryable_http_statuses: [408, 429, 500, 502, 503, 504]
retryable_transport_events: [connection_failure, timeout]
max_retry_after_ms: 2000
default_backoff_ms: 250
remote_target_mutation_authorized: false
production_deployment_authorized: false
```

The price mapping is the approved 2026-07-12 standard short-context schedule for `gpt-5.6-luna`. A retryable attempt with unknown usage reserves the full per-attempt ceiling before another attempt. Provider, model, price, host, path, budget, credential reference, or payload drift fails closed and requires a new packet; no model or provider fallback is permitted.

## Exact synthetic live fixture

The sole live input is a public JSON fixture with the stable identifier `P14C-001`. It asks the model to normalize a synthetic task and return exactly:

```text
fixture_id
status
summary
```

The live guard binds the exact payload SHA-256, operation, prompt id/version, required capabilities, output keys, model, budgets, and all authority flags before credential or network access. The response schema requires `fixture_id=P14C-001`, `status=PASS`, a bounded summary, and no additional properties.

No repository file, repository diff, blueprint content, target state, business data, personal data, credential, external tool, web search, file search, or production input is allowed in the live request.

## Credential, network, retry, cancellation, and redaction controls

- the credential value is resolved from `OPENAI_API_KEY` only inside the provider invocation and is never accepted in the AI request, packet serialization, CLI argument, audit, exception, replay record, document, or Git object;
- the standard transport connects directly to `api.openai.com:443`, verifies TLS and hostname, posts only `/v1/responses`, follows no redirect, and ignores proxy environment variables;
- one logical request permits at most two HTTP attempts and only the named status or transport failures are retryable;
- `Retry-After` is honored only up to 2000 ms and only within the remaining 45000 ms live-evidence deadline;
- cancellation is checked before credential access, before dispatch, during backoff, during an in-flight transport, and after transport return; an in-flight cancellation closes the connection and performs no retry;
- raw authorization headers, request input, response body, structured output, provider error body, and raw exception text are excluded from persistent audit;
- audit retains only packet/request hashes, provider/model, attempt number, HTTP status class or stable transport code, usage, duration, conservative cost, output hash, terminal status, and stable error code;
- unit and integration tests use injected transports and never call the real provider; only the formal live-evidence CLI may open the approved network path.

## Natural-owner and compatibility disposition

P14C adds the live adapter under `src/tool_system/ai_worker/live_provider.py` and a formal evidence entry point under `src/tool_system/cli/run_p14c_live_evidence.py`. The P14B `AIWorkerRuntime` remains fixture-only by default. Its internal execution guard becomes injectable so the P14C wrapper can reuse the same request integrity, replay, usage, response, and audit validation without creating a second result-validation mainline.

The P14B public dataclasses, default fixture provider behavior, error taxonomy, result shape, and live-provider fail-closed test remain compatible and are revalidated. P11–P13 and repository-control owners are not changed.

## Exact file scope

```text
AGENTS.md
README.md
blueprint/tool_system_v0.yaml
docs/reports/p14c_bounded_real_model_provider_execution.md
examples/task_manifests/tool_system_p14c_bounded_real_model_provider_execution.yaml
examples/change_plans/tool_system_p14c_bounded_real_model_provider_execution.yaml
examples/active_gates.yaml
pyproject.toml
src/tool_system/ai_worker/__init__.py
src/tool_system/ai_worker/contract.py
src/tool_system/ai_worker/runtime.py
src/tool_system/ai_worker/live_provider.py
src/tool_system/cli/run_p14c_live_evidence.py
tests/test_ai_worker_live_provider.py
tests/test_p14c_execution_contract.py
tests/test_phase_alignment.py
tests/test_p14_phase_entry_contract.py
```

## Acceptance target

```text
named_packet_exact_match: PASS
default_fixture_runtime_live_provider_block: PASS
synthetic_payload_hash_binding: PASS
credential_reference_and_value_isolation: PASS
exact_TLS_network_path_and_no_redirect: PASS
strict_responses_request_and_output_validation: PASS
timeout_and_inflight_cancellation: PASS
bounded_retry_and_retry_after: PASS
cumulative_attempt_token_time_cost_gates: PASS
request_response_exception_audit_redaction: PASS
replay_without_second_provider_call: PASS
focused_tests: PASS
full_repository_tests: PASS
active_gates: PASS
bounded_live_provider_result: PASS
live_provider_calls: 1 logical, at most 2 HTTP attempts
target_repo_reads: 0
target_repo_mutation: false
production_deployment: false
```

## Local and CI evidence

```text
expected_main_precondition: c30df8c6955260d07fbf271f62d54a921ea26e86
working_branch: p14c-bounded-real-provider
manifest_structure_and_repo_policy: PASS
change_plan: PASS
active_gates: PASS
packet_exact_match: PASS
packet_sha256: ec19a1039b1dbdf162be0b3acfe28897fec304221bc809aba9263bb86bbe9ee4
fixture_default_compatibility: PASS
packet_request_credential_network_retry_timeout_cancellation_cost_output_replay_redaction_tests: PASS
focused_tests: PASS_76
full_repository_tests: PASS_338
ruff_check: PASS
ruff_format_check: PASS
python_compileall: PASS
git_diff_check: PASS
planned_changed_files: 17
actual_changed_files: 17
changed_files_match_plan: PASS
formal_live_preflight: PASS
credential_reference: env:OPENAI_API_KEY
credential_available: false
network_attempts: 0
live_provider_calls: 0
target_repo_reads: 0
target_repo_mutation: false
production_deployment: false
```

The implementation is locally validated and the exact packet is ready, but the current execution environment does not expose `OPENAI_API_KEY`. P14C therefore remains `VALIDATING`: formal live evidence, candidate CI, closure-head CI, squash merge, and fresh-main verification are still required. Missing credential material is not bypassed and is not replaced by a different credential, provider, model, or fixture.

## Rollback and stop condition

Before merge, rollback is closing the unmerged P14C PR while retaining its head and audit evidence. After merge, rollback requires a separately named git-revert packet and PR; reset, force-push, branch deletion, and destructive cleanup are not authorized.

Creator-owned temporary pytest, bytecode, and live-evidence process roots are removed after verification. No existing branch, including `dummy-unused`, is deleted.

After P14C acceptance and closure, stop at P14D. Repository-context implementation, any target-repository read benchmark or mutation, finance-us P1B, P14D or later source work, P15-P16, and production deployment remain separately unauthorized.
