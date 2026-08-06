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

## Private operator execution result

`COMPLETED_ONE_ATTEMPT_NO_AVAILABLE_PROVIDER_TRANSPORT_CONNECTION`

The DGX private operator execution surface ran the canonical runtime from source-sealed `main@71bc347942e921675cea340ff07274834a1b8f9f` with tree `a2060295f9602c8e2b9ffa7bf7bcf35e6f563090`.

Sanitized retained evidence:

- provider/model: `openai` / `gpt-5.6-luna`;
- route mode: `single-success`;
- deterministic case count: one;
- route attempts: one;
- provider invocations: one;
- automatic retries: zero;
- result: `NO_AVAILABLE_PROVIDER`;
- failure code: `TRANSPORT_CONNECTION`;
- winning provider/model: none;
- charged amount: 25,000 microUSD, recorded by the ledger as `UNCERTAIN`;
- configured private total ceiling: 1,000,000 microUSD;
- credential values recorded: zero;
- raw provider outputs recorded: zero;
- private target loaded or identified: false;
- target mutations, production, cleanup, and rollback operations: zero.

The single invocation allowance is exhausted. This lifecycle does not authorize a retry, a second provider, or diagnosis by another live call. The failed transport result therefore does not satisfy the remaining successful-live-smoke acceptance item.

## Read-only final P15 mapping

All non-live P15 evidence remains complete. The only remaining acceptance item is one successful controlled single-provider live smoke. This attempt produced no successful provider response, so:

- P15 remains unaccepted;
- P16 remains unentered;
- no additional live execution is authorized;
- a future retry requires a new explicit lifecycle and a fresh canonical-source, network, budget, expiry, transfer, cancellation, retry, and audit preflight.

Publication of this sanitized result may proceed through the existing Draft PR, Hosted fake-I/O CI, no-drift Ready transition, and squash merge while retaining the feature branch. Publication records the outcome; it does not convert failure into acceptance.
