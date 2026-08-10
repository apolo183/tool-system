# Subscription Worker Codex Structured Output and Sandbox Correction v1

## Decision

The accepted guarded Codex CLI adapter required a compatibility correction before public-entry dispatch. Its prior `--json` handling treated the final JSONL event as the structured patch, passed the prompt in the argument vector, did not explicitly select a read-only sandbox or ephemeral execution, and did not prove process-group cancellation. Those behaviors did not support the module contract's structured-result-only and finite-cancellation claims.

This package corrects that adapter in place without changing `worker-adapter-api@1.0.0`. Public CLI, task-runner dispatch, isolated-workspace creation, local Git, remote publication, API providers, production, cleanup, and rollback remain outside this package.

## Corrected process boundary

The guarded path remains default disabled and requires explicit enablement plus request authority. When selected, it uses an exact shell-free vector with:

- global `--ask-for-approval never` so the non-interactive run cannot pause for an unbounded approval;
- `codex exec --json` for a bounded event stream;
- `--ephemeral --ignore-user-config` so no session rollout is persisted and user config cannot re-enable MCP, hooks, a non-subscription provider, or broader tool defaults; authentication still follows `CODEX_HOME`;
- `--sandbox read-only` so the worker returns a patch instead of editing the workspace;
- `--output-schema <creator-owned-schema>` and `--output-last-message <creator-owned-result>`;
- `--skip-git-repo-check -`, with the structured prompt supplied through stdin rather than process arguments.

The official Codex developer command reference distinguishes `--json` event output from `--output-schema` final-response validation, documents `--output-last-message`, `--sandbox`, and `--ephemeral`, and is the behavioral basis for this correction: https://developers.openai.com/codex/cli/reference/

The schema and result paths exist only inside one owner-mode creator-owned temporary directory. The schema is mode 0600. The result, stdout, and stderr are byte bounded; the result must be a JSON object and pass the development loop's compatible structured-patch shape. Raw process output and temporary paths are never returned or audited.

## Timeout and cancellation

The production process runner creates a new process session. On timeout it sends TERM to the process group, waits for a finite grace interval, escalates to KILL if needed, reaps the process, and returns the existing fail-closed timeout result. Non-POSIX fallback terminates then kills the direct child within the same finite boundary. Injected fake-process tests exercise both TERM completion and KILL escalation without spawning Codex or performing network activity.

## Authority and effects

The minimal environment continues to reject provider-credential variable names. Ignoring user configuration does not extract or expose authentication state; it prevents repository-external behavioral configuration from expanding the fixed worker surface. Neither executable presence, subscription authentication state, environment variables, nor temporary file creation grants execution authority. Target-repository writes, target mutation, provider execution, credential-value access, production, remote operations, project cleanup, and rollback remain false.

Creator-owned temporary schema/result creation and automatic removal are implementation-lifetime artifacts, not target-repository or project-cleanup authority. The worker adapter contract and module registry declare this conditional boundary without changing the public interface or module version.

## Validation boundary

Hosted CI uses injected fake process controllers only. Tests prove exact argv shape, stdin prompt transfer, minimal environment, private schema file, schema-bound final-message parsing, strict patch rejection, independent byte limits, nonzero status, timeout, process-group TERM/KILL cancellation, redaction, and default-disabled behavior. The existing task-runner subscription-pipeline integration test is updated to feed the prompt through stdin and the patch through the private final-message path; production task-runner code is unchanged. No real Codex, ChatGPT Web, browser, API provider, credential, downstream repository, production, cleanup, or rollback operation is performed.

After merge, the next independent package may compose this adapter with the existing public entry only after isolated-workspace and exact authority bindings are proven.
