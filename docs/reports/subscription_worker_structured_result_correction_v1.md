# Subscription Worker Structured Result Correction v1

PR #207 correctly added a guarded fake-process Codex adapter but returned only redacted process metadata. The public development loop requires a structured worker result, so this correction parses newline-delimited JSON only after a zero exit code and returns the terminal JSON object as `structured_result`. Invalid JSON, a non-object terminal record, excess output, timeout, process error, or nonzero exit remains fail closed. Raw stdout and stderr are never retained in the adapter result.

Scope is limited to the worker-adapter implementation, its direct test, and this package's report/manifest/change-plan. No real Codex, API, credential, downstream, Git target, production, cleanup, or rollback action occurs.
