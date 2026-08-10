# Subscription Worker Adapter v1 Implementation

The worker-adapter module now exposes an opt-in Codex CLI subscription adapter while preserving `DryRunWorkerAdapter` as the default.

The adapter requires explicit enablement and per-request subscription-worker authorization. It rejects target-repository mutation and production authority, constructs a fixed argument vector with `shell=False`, forwards only an explicit minimal environment-name allowlist, forbids provider credential environment names, applies timeout and output limits, and records only redacted process metadata. OSError, timeout, nonzero exit, excessive output, missing authority, or invalid configuration fail closed.

Hosted CI injects fake process runners. This package does not execute Codex, call an API, read credentials, access a downstream repository, create a local target commit, or grant public-entry authority. Public CLI integration belongs to the next dependent package.
