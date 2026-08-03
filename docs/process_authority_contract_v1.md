# Process Authority Contract v1

Role: durable tool-system current-task authority and replay-boundary contract.

Owner: canonical `process-authority` module.

Upstream: `blueprint/tool_system_v0.yaml:product_objective`, `blueprint/tool_system_v0.yaml:milestone_module_invariant`, and `docs/tool_system_global_development_principles_v1.md`.

Downstream: task planner, task runner, role runtime, CLI adapters, tests, and audit records.

## Current-task authority

`config/process_authority_v1.yaml` is the single local machine contract for task-pair authority. Current execution requires one task manifest and one change plan supplied explicitly for that invocation. The change plan must name the same manifest. A repository-wide implicit task index is not current execution authority.

Its machine module identity is exactly `process-authority@2.3.0`, exposing
`process-authority-api@2.1.0`. The historical compatibility ID
`process_authority` is not accepted in the current authority file. The Python
package remains `tool_system.process_authority`; that language-level underscore
does not create a second module authority or an identity alias.

Before any configured command runs, the task runner must pass the process-authority contract, manifest policy validation, explicit pair binding, and change-plan validation. A failed preflight runs no configured command.

The public command-dispatch API receives the real authority, manifest, plan,
repo-write policy, autonomy-policy, working-directory, and timeout inputs. It
revalidates those inputs internally and accepts no caller-created PASS value,
receipt, token, or unchecked command list. It captures the validated file bytes,
compares them again immediately before dispatch, and extracts commands from the
same captured plan bytes. Any validation failure or byte drift blocks before
`subprocess.run`.

## P14C GitHub approval boundary

`process-authority@2.3.0` also implements the separately authorized source for
one P14C live-provider approval trust root. Given a positive comment ID and an
exact typed action binding, the issuer performs one TLS-verified public `GET`
to
`https://api.github.com/repos/apolo183/tool-system/issues/comments/{comment_id}`.
The host, repository, owner login, endpoint, API version, timeout, response-size
limit, and request headers are fixed internally. The caller cannot substitute a
reader, identity mapping, approval boolean, or prevalidated record.

Before the GitHub read, the issuer measures the caller-selected canonical
tool-system checkout and requires its canonical origin, exact Git top level,
current commit and tree, clean status, loaded canonical committed operator
entry, and fixed critical runtime source files. It hashes a canonical manifest
of those bytes and binds the result to the actual host name and the immutable
identity of one caller-selected hardened `DurableOrchestratorStore`. No
caller-created source PASS value is accepted.

The response must identify the same comment in `apolo183/tool-system`, with
author login `apolo183`, `author_association: OWNER`, and identical
`created_at` and `updated_at` timestamps. The comment body must be strict JSON
with no duplicate or extra keys and must bind exactly:

- authorization ID, repository, action, historical implementation-authorization
  base, packet and request hashes;
- exact execution commit, execution tree, critical-source manifest SHA-256,
  `clean_worktree: true`, actual execution host, and durable ledger identity;
- public fixture, provider, exact model, method, host, path, credential
  reference, and `live_network` transport;
- one provider invocation, attempt/token/time/cost ceilings, a 64-character
  lowercase hexadecimal nonce, and an expiry no more than fifteen minutes
  after comment creation;
- `false` for target-repository mutation, production deployment, cleanup, and
  P14D.

Authentication failures, API failures, edits, expiry, malformed data, source or
binding drift, wrong host or ledger, or reuse of the same comment block
issuance. After full validation and before grant construction, the issuer calls
`durable-orchestrator-api@1.1.0` to insert the exact approval identity and
digests with `BEGIN IMMEDIATE`. The record is burn-on-claim: if the process
crashes after commit, it remains consumed and a fresh approval comment is
required. Two processes using the same single-host database therefore have at
most one winner. This is not a multi-host or distributed exactly-once claim.

A valid durably consumed record yields one opaque in-memory grant; that grant
can mint one immutable capability bound to the exact packet, request, live
transport object, source seal, host, and ledger identity. The capability can be
consumed once and revalidates the same source seal immediately before each
credential access and before approval expiry.

## P14C committed operator entry

The packaged command `tool-system-p14c-live` is the only committed operator
entry for this path. `prepare-approval` requires an exact repository root and a
ledger path outside that checkout. It initializes or reopens the hardened
single-host ledger, measures the clean current source including its own
canonical module bytes, generates a cryptographic nonce and expiry of at most
fifteen minutes, and prints the exact public JSON body the repository owner may
publish. Preparation performs no GitHub read or write, credential access, or
provider call.

`execute` requires the same repository and ledger plus one positive GitHub
comment ID. It recomputes the seal, uses the internally fixed public GitHub
reader, burns a matching approval before capability construction, invokes only
the current exact packet-bound P14C public synthetic provider transport, and
prints a redacted receipt. The receipt contains approval and source digests,
bounded usage, an output hash, and audit-safe error fields; it contains neither
the credential value nor raw provider output. The command creates or edits no
GitHub comment. Calling the module through an unsealed one-off script cannot
satisfy the canonical loaded-module source check.

This is source capability, not live-execution evidence. The implementation and
its tests create or edit no real GitHub comment, read no credential value, call
no model provider, and leave `live_model_provider_execution_authorized: false`.
It does not claim multi-host replay prevention, guaranteed provider completion,
or protection against hostile code already executing inside the trusted Python
process. A first real approval, credential read, or provider call remains
separately prohibited until explicitly authorized.

## Canonical replay boundary

`config/replay_snapshot_v1.yaml` is content-addressed compatibility evidence for the legacy `examples/active_gates.yaml` pair set at source head `4445cb5ec3ddab0738560e0d5f4a64b9dd582bd7`. It records the source index SHA256 and a deterministic digest over the sorted manifest path/hash and change-plan path/hash tuples.

Replay validation reconstructs both digests from the current legacy inputs and blocks on any drift. The snapshot has `authority: false`, `replay_only: true`, and every execution, target-mutation, production, and cleanup flag set to false. It cannot authorize commands or become a fallback current-task route.

## Caller migration

Task, batch, graph, stage, and role-runtime defaults use explicit task pairs and `config/process_authority_v1.yaml`. The legacy `--active-gates` option remains only as an explicit replay-only compatibility input. It is never selected by default and is rejected when command execution is requested.

The legacy active-gate validator remains a consistency check for retained replay inputs, not an authority grant. CI validates the process-authority contract, the replay snapshot, the durable module registry, and legacy replay consistency independently.

The retained replay boundary contains no compatibility module-ID input and
cannot authorize the protected command-dispatch API.

## Cleanup and claim boundary

Existing reports, manifests, change plans, and `examples/active_gates.yaml` remain present as retained non-authority inputs. This contract does not delete, reclassify, or move them. Cleanup requires a separate authorization and accepted disposition.

This contract grants no target-repository mutation, live provider execution, branch cleanup, production deployment, or governance activation. Rollback uses a named revert PR preserving Git and audit history.
