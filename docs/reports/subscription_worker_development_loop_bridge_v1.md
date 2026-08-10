# Subscription Worker Development-Loop Bridge v1

This package adds the worker-adapter-owned bridge required by the next public-entry integration package. It canonicalizes each bounded development-loop request into the adapter prompt, forces the per-cycle adapter request to external-worker execution while keeping target-write, target-mutation, and production flags false, and returns only a passing structured result. A blocked adapter or missing structured result returns a deliberately invalid authority field so the existing development loop fails closed before applying a patch.

The default dry-run adapter and all API defaults remain unchanged. Tests inject a fixture adapter; no real Codex, API, credential, repository, Git, production, cleanup, or rollback action occurs.
