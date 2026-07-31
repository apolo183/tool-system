# Process Authority Contract v1

Role: durable tool-system current-task authority and replay-boundary contract.

Owner: canonical `process-authority` module.

Upstream: `blueprint/tool_system_v0.yaml:product_objective`, `blueprint/tool_system_v0.yaml:milestone_module_invariant`, and `docs/tool_system_global_development_principles_v1.md`.

Downstream: task planner, task runner, role runtime, CLI adapters, tests, and audit records.

## Current-task authority

`config/process_authority_v1.yaml` is the single local machine contract for task-pair authority. Current execution requires one task manifest and one change plan supplied explicitly for that invocation. The change plan must name the same manifest. A repository-wide implicit task index is not current execution authority.

Its machine module identity is exactly `process-authority@2.1.0`, exposing
`process-authority-api@2.0.0`. The historical compatibility ID
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

`process-authority@2.1.0` also implements the separately authorized source for
one P14C live-provider approval trust root. Given a positive comment ID and an
exact typed action binding, the issuer performs one TLS-verified public `GET`
to
`https://api.github.com/repos/apolo183/tool-system/issues/comments/{comment_id}`.
The host, repository, owner login, endpoint, API version, timeout, response-size
limit, and request headers are fixed internally. The caller cannot substitute a
reader, identity mapping, approval boolean, or prevalidated record.

The response must identify the same comment in `apolo183/tool-system`, with
author login `apolo183`, `author_association: OWNER`, and identical
`created_at` and `updated_at` timestamps. The comment body must be strict JSON
with no duplicate or extra keys and must bind exactly:

- authorization ID, repository, action, source base, packet and request hashes;
- public fixture, provider, exact model, method, host, path, credential
  reference, and `live_network` transport;
- one provider invocation, attempt/token/time/cost ceilings, a 64-character
  lowercase hexadecimal nonce, and an expiry no more than fifteen minutes
  after comment creation;
- `false` for target-repository mutation, production deployment, cleanup, and
  P14D.

Authentication failures, API failures, edits, expiry, malformed data, binding
drift, or reuse of the same comment in the same process block issuance. A valid
record yields one opaque in-memory grant; that grant can mint one immutable
capability bound to the exact packet, request, and live transport object, and
the capability can be consumed once and only before the approval expiry.

This is source capability, not live-execution evidence. This implementation
creates or edits no GitHub comment, reads no credential value, calls no model
provider, and leaves `live_model_provider_execution_authorized: false`. It does
not claim durable replay prevention across independent processes or protection
against hostile code already executing inside the trusted Python process.
Those require a separately authorized durable authority owner and threat-model
expansion.

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

This contract grants no finance-us or other target-repository mutation, live provider execution, branch cleanup, production deployment, or governance activation. Rollback uses a named revert PR preserving Git and audit history.
