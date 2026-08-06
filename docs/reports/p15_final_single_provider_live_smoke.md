# P15 Final Single-Provider Live Smoke Lifecycle

## Authorization

The user authorized one controlled API-backup smoke from canonical `main@71bc347942e921675cea340ff07274834a1b8f9f` using one explicitly enabled and usable provider/model selected by repository-external private operator configuration.

## Preflight boundary

Hosted CI may run only the existing full fake-I/O and governance suite. It must not receive provider Secrets or execute `tool-system-p15c-benchmark --execute`.

The real smoke requires the installation-owned files already defined by the runtime:

- `~/.config/tool-system/settings.toml`;
- `~/.config/tool-system/credentials.toml`;
- `~/.local/state/tool-system/p15c-usage.sqlite3`.

The runtime may resolve the selected credential after all gates pass but must not print, hash, persist, or return its value.

## Exact live limits

- one repository-external provider/model route;
- API and provider explicitly enabled;
- total and provider budget no more than the private operator ceiling, with a lifecycle default recommendation of 1,000,000 microUSD;
- one allowed deterministic-corpus case;
- `max_provider_invocations = 1`;
- no automatic retry;
- one success stops the chain;
- unavailable, unconfigured, unfunded, invalid, expired, or unusable routes may be skipped;
- no target repository or private target bundle is loaded;
- no production, cleanup, rollback, P16 entry, or P15 acceptance.

## Current execution disposition

`BLOCKED_CURRENT_WEB_EXECUTION_ENVIRONMENT_HAS_NO_REPOSITORY_EXTERNAL_PRIVATE_CONFIG_ACCESS`

GitHub App connector access is sufficient for repository publication and Hosted fake-I/O validation, but it cannot read or invoke the installation-owned private configuration and ledger. No credential value was requested or accessed, no provider was called, and no spend occurred.

The Draft PR must remain Draft after Hosted CI until an authorized private operator execution surface can run preflight and the single call without transferring credential material into ChatGPT, GitHub, or Hosted CI.
