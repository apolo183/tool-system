# P15 Single-Provider Transport Proxy Correction

## Evidence and root cause

The final single-provider attempt on canonical `main@71bc347942e921675cea340ff07274834a1b8f9f` exhausted its one-call allowance with `TRANSPORT_CONNECTION`, zero input/output tokens, no raw provider output, and no winning provider. The then-active P15 transport used direct verified TLS only and explicitly had no proxy support. The outcome was published through PR #191 and did not accept P15 or enter P16.

## Corrected boundary

The ai-worker-runtime module now keeps `direct_tls` as its public disabled-example default and adds schema 4 for an explicit repository-external transport selection:

- `direct_tls` requires an empty proxy host and zero proxy port;
- `http_connect` requires an owner-only configured loopback host and bounded port;
- only the existing fixed provider host/path allowlist may be tunneled;
- TLS verification remains the standard-library verified target TLS context;
- redirects, proxy credentials, environment proxy activation, dynamic endpoints, and same-route retries remain unsupported;
- the private endpoint is used only inside the runtime transport object and is replaced by a private marker plus zero port before the public policy digest is calculated;
- schema 3 remains readable as direct-TLS single-provider compatibility, while schemas 1 and 2 retain their legacy matrix behavior.

The proxy setting grants transport configuration only. It does not enable API mode, a provider, a model, transfer, a credential, a budget, a retry, or an execution.

## Fake-I/O evidence contract

Hosted and local tests inject the HTTPSConnection boundary. They verify the direct default, exact loopback proxy selection, CONNECT tunnel target, fixed provider route, verified TLS context construction, endpoint non-disclosure, invalid mode/host/port rejection, disabled public template, schema compatibility, and absence of environment-proxy or proxy-credential behavior. No test or workflow carries a real provider secret or invokes a provider.

## Read-only network and proxy preflight mapping

After merge, an operator may prepare a future, separately authorized preflight by copying the disabled example outside the repository and explicitly choosing either direct TLS or loopback CONNECT. The future preflight must prove:

- then-canonical commit and tree plus a clean worktree;
- API mode and exactly one provider/model explicitly enabled;
- active expiry, budget, transfer, cancellation, one-call and zero-retry limits;
- `transport_mode = "http_connect"` only when the owner-only proxy host and port are explicitly configured;
- proxy endpoint reachability may be checked without a provider request only under separate local diagnostic authority;
- no credential value, proxy endpoint, raw output, or target identity enters public evidence.

## Stop boundary

This correction performs no real provider invocation, benchmark, target access, production, cleanup, rollback, P15 acceptance, or P16 entry. The exhausted PR #191 live authorization remains exhausted. Any future provider request requires a new explicit single-call lifecycle after this correction is merged and its private preflight passes.
