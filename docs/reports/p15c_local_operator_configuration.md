# P15C Local Operator Configuration

## Status

`P15C_LOCAL_OPERATOR_CONFIGURATION_SOURCE_IMPLEMENTED_FAKE_IO_ONLY`

This correction supersedes the unmerged Hosted live bridge in Draft PR `#175`.
That PR was closed without Ready, merge, provider invocation, credential-value
access, target transfer, benchmark execution, or spend. Its branch remains
retained as evidence.

## Per-installation boundary

The public repository contains only disabled, empty examples. Every installation
owns its private files outside the checkout:

- `~/.config/tool-system/settings.toml` contains manually adjustable execution
  switches, total and provider budgets, expiry, source bindings, target binding,
  and provider-transfer switches;
- `~/.config/tool-system/credentials.toml` contains only that installation's
  provider keys;
- `~/.config/tool-system/p15c-target-packet.json` contains the operator-private
  exact target packet and snapshot reference; and
- `~/.local/state/tool-system/p15c-usage.sqlite3` contains cumulative sanitized
  attempt and cost state.

The settings and credential files are distinct so changing a model switch or
budget never requires opening, copying, rewriting, or publishing a key. All
private inputs remain owner-only, non-symlink files under owner-only directories.
The runtime reads a credential only after source, target, transfer, policy,
cancellation, request, replay, and budget gates pass; it never prints, hashes,
returns, or persists the value.

The local settings file owns the active spend limit. The implementation contains
no literal 20 USD execution ceiling. The disabled public example records the
currently authorized 20,000,000 microUSD value for operator copying, but execution
uses the private copied value and the existing atomic ledger.

## Hosted boundary

No new workflow is added. Existing Hosted CI runs the full source and consistency
suite with synthetic credentials, private controls, target identities, snapshots,
and fake transports only. Repository workflows contain no reference to OpenAI,
DeepSeek, or Qwen API-key Secrets, no private bundle Secret, and no live
`p15c_entry --execute` command.

Copying or forking the public repository therefore copies only code, empty
examples, and credential reference names. It does not copy an installation's
local files or any GitHub repository Secret value.

## Compatibility and stop boundary

`--settings` is the preferred operator option and defaults to the repository-
external path above. The former `--policy` spelling remains an alias. Explicit
path overrides remain available for isolated operators and tests. Packet-only
mode does not inspect any private default path.

Only `ai_worker_runtime` advances from `1.7.0` to interface-compatible `1.8.0`;
`ai-worker-runtime-api@1.0.0` remains unchanged. The blueprint, frozen provider
packets, routes, models, corpus, target repository, and P15D boundary do not
change. Publication performs zero credential resolution, target access, provider
network operation, benchmark execution, target mutation, production, cleanup,
or rollback.
