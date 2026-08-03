# P15C Runtime Control Plane Implementation

## Status

`P15C_RUNTIME_CONTROL_PLANE_SOURCE_IMPLEMENTED_FAKE_TRANSPORT_ONLY_PENDING_PUBLICATION`

This record closes only the public source-publication substage authorized by
`P15C-CROSS-PROVIDER-READ-ONLY-BENCHMARK-LIFECYCLE-v1`. It does not record a
private preflight, a live benchmark result, P15C acceptance, or P15D entry.

## Canonical basis and bounded closure

- Requested lifecycle base: `tool-system@f30f43512acfa497afd9f27dcce7cf4a0ebeb101`.
- Corrected canonical source base consumed after the prerequisite packet repair:
  `tool-system@1019b719547fe0b38341821e968dcae57a1f3697`, tree
  `8f74c31d2033feff357c4a306e23f6f7f8d44c13`.
- Task manifest:
  `examples/task_manifests/tool_system_p15c_runtime_control_plane_v1.yaml`.
- Change plan:
  `examples/change_plans/tool_system_p15c_runtime_control_plane_v1.yaml`.
- Frozen publication closure: exactly 26 paths.
- Only durable module changed: `ai_worker_runtime`, module version `1.7.0`;
  aggregate interface `ai-worker-runtime-api@1.0.0` remains compatible.
- The P15B adaptive portfolio module, blueprint, provider-economics roadmap,
  packet catalog, target repositories, process-authority implementation, and
  all P15D, production, cleanup, and rollback surfaces remain unchanged.

## Generic execution boundary

The P15C control plane is target-neutral. Target repository identity, branch,
exact commit, path allowlist, content inventory, durable-module contract, and
snapshot root are caller-supplied operator-private inputs. No downstream project
identity is embedded in public runtime source, configuration, documentation, or
test fixtures.

The source enforces all of the following before a provider transport can start:

1. An owner-only expiring execution-policy file names the exact lifecycle,
   canonical tool-system tree, exact target-packet SHA-256, exact
   two-provider/two-case matrix, a total budget
   no greater than 20,000,000 microUSD, per-provider sub-budgets, OpenAI and
   DeepSeek enablement, provider-transfer switches, and Qwen disabled with zero
   budget.
2. The local tool-system checkout has a canonical origin, exact canonical tree,
   clean worktree, and content seal covering the packet catalog and all three
   P15C execution modules. These checks repeat immediately before each transport.
3. The target packet grants inventory read, benchmark read, and OpenAI and
   DeepSeek transfer while denying mutation and Qwen transfer. Its allowlist is
   sorted, finite, repository-relative, and content addressed by SHA-256 and Git
   blob identity.
4. Snapshot files must be owner-controlled, UTF-8, regular single-link files
   under the exact snapshot root. Symlinks, Git metadata, environment or
   credential paths, blocked key formats, secret-like content, and byte or hash
   drift fail closed.
5. Provider keys resolve only through the exact opaque references in a separate
   owner-only TOML credential store. Values are held only for request headers and
   are never logged, returned, hashed into evidence, or stored in the usage
   ledger.
6. A versioned owner-only SQLite ledger atomically reserves the per-attempt cap
   under total and provider budgets. It settles sanitized usage and aggregate
   metrics, releases a pre-transport cancellation, and charges the full reserved
   cap when post-transport cost is uncertain. Attempt identity prevents replay.

## Frozen provider requests

- DeepSeek: exact `deepseek-v4-flash` Chat Completions request to
  `api.deepseek.com/chat/completions`, JSON object mode, thinking disabled.
- OpenAI: exact `gpt-5.6-luna` Responses request to
  `api.openai.com/v1/responses`, strict JSON-schema output and `store=false`.
- Both: 2,048 requested output tokens, one attempt, zero retries, direct verified
  TLS, fixed host and path, no proxy, redirect, fallback, stream, tools, provider
  web search, or response persistence.
- Qwen: omitted from the executable packet set, disabled by both public packet
  evidence and private policy validation, and assigned zero budget.

Public benchmark receipts contain provider/model/case identifiers, request and
validated-output hashes, token counts, integer microUSD charges, duration,
schema validity, grounded aggregate finding counts, deterministic expected-path
recall, and confidence. They exclude credential values, raw provider output,
private target identity, private commit, allowlist paths, and target content.

## Source-stage verification

All provider-facing tests inject fake transports. Private-control tests use only
owner-only temporary files and synthetic identities. Verification covers exact
packet loading, deterministic corpus content identity, request shape, response
schema, cost arithmetic, private target transfer gates, policy expiry and budget,
credential-reference isolation, source drift, target drift and secret rejection,
atomic ledger replay and failure charging, cancellation, exact fake four-call
matrix, CLI packet-only zero-I/O behavior, module governance, phase consistency,
and full repository regression.

The source-publication stage records these exact operation counts:

- credential resolver invocations: 0
- credential value accesses: 0
- private target snapshot reads: 0
- target repository accesses: 0
- provider invocations: 0
- live network operations: 0
- benchmark executions: 0
- private repository provider transfers: 0
- target mutations: 0
- production operations: 0
- cleanup operations: 0
- rollback operations: 0
- blueprint changes: 0

## Authority and next gate

The user lifecycle authorizes a later operator-private preflight and the exact
four-call benchmark after this source is merged and the canonical main source
seal is frozen into the private policy. This descriptive record grants no
authority by itself. Any source drift, missing private control, target-packet
drift, credential-reference failure, transfer mismatch, budget failure, or
Hosted CI failure blocks execution. P15C remains unaccepted and P15D remains
unauthorized.
