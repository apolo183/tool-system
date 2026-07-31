# P14C Live Issuer Implementation Evidence

Status: `DRAFT_PR_PENDING_NO_LIVE_EXECUTION`

This report records source work authorized by
`P14C-LIVE-ISSUER-IMPL-v1`. It is not a GitHub approval record, live execution
authority, P14C acceptance, or permission for any later stage.

## Exact authority

- repository: `apolo183/tool-system`
- source base: `b6ea3c62aa668031e87abb6341f82cb1bd32a3eb`
- branch: `agent/p14c-live-issuer-v1`
- publication ceiling: one commit and one Draft PR
- trust root: one public GitHub issue comment in `apolo183/tool-system`
  authored by login `apolo183` with `author_association: OWNER`
- future live-execution authorization ID: `P14C-LIVE-EXEC-v1`
- real approval records created or edited by this change: `0`
- credential values accessed: `0`
- real provider calls: `0`
- downstream repository reads or writes: `0`

Ready transition, main merge, a real approval record, credential-value access,
live execution, P14C acceptance, P14D, downstream access, cleanup, rollback,
branch deletion, and production remain unauthorized.

## Trust-root and one-shot design

The process-authority issuer accepts only a positive comment ID and an exact
typed P14C binding. It constructs the GitHub API path internally and performs
one TLS-verified `GET` to
`/repos/apolo183/tool-system/issues/comments/{comment_id}`. It sends no
credential or authorization header and accepts no injected reader, actor
mapping, approval boolean, or prevalidated response.

The response must bind the exact comment and repository, owner login,
`OWNER` association, and unedited timestamps. The strict JSON body permits no
duplicate or extra fields and binds the authorization ID, source base, packet
and request hashes, public fixture, provider, exact model, endpoint, credential
reference, exact network transport, one-invocation ceiling, attempt/token/time/
cost bounds, expiry, nonce, and explicit false values for target mutation,
production, cleanup, and P14D.

A valid record creates one opaque in-memory grant. That grant can mint one
immutable capability bound to the same packet, request, approval digest,
issue/comment IDs, and exact `OpenAIResponsesTransport` object. The grant and
capability each reject a second consumption, and both reject use after the
approval expiry.

GitHub documents the exact issue-comment read endpoint and response fields,
including `user`, `body`, `created_at`, `updated_at`, `issue_url`, and
`author_association`, and defines `OWNER` as the repository owner:
<https://docs.github.com/en/enterprise-cloud@latest/rest/issues/comments>.
Public unauthenticated reads remain subject to GitHub's documented primary rate
limit; one unavailable or rate-limited read fails closed:
<https://docs.github.com/en/enterprise-cloud@latest/rest/using-the-rest-api/rate-limits-for-the-rest-api>.

## Evidence boundary

Every test replaces `http.client.HTTPSConnection` and the provider transport
with local fakes. Tests cover exact success plus wrong owner, wrong association,
edited timestamps, wrong repository, expiry, excessive lifetime, malformed or
duplicate JSON, binding drift, HTTP failure, transport substitution, grant
construction, capability replay, and comment replay.

The code does not provide durable cross-process replay storage. It also does not
claim to defend against hostile monkeypatching or arbitrary code already
executing inside the trusted process. Those are explicit future authority and
threat-model boundaries, not evidence gaps filled by this Draft PR.

## Verification

Local verification recorded on 2026-07-31:

- exact task manifest/change-plan binding and change-plan validation: `PASS`;
- issuer, AI-worker live adapter, process authority, P14C contract, and phase
  alignment suite: `69 passed`;
- full repository suite: `536 passed`;
- process-authority validator: `PASS`, with `process-authority@2.1.0`,
  `process-authority-api@2.0.0`, and `108` replay-only legacy pairs;
- current module-registry authority validator: `PASS`, with `101` owned paths,
  `152` ContractReferences, and the observed and declared
  `process-authority -> ai-worker-runtime` edge equal;
- repository-manifest validator: `PASS`, with `206` formal files, `300`
  retained non-authority paths, and zero unclassified paths;
- source compilation and `git diff --check`: `PASS`;
- real GitHub reads, approval-record writes, credential-value reads, provider
  calls, and downstream operations: `0`.

Hosted CI remains pending until the Draft PR exists. Hosted success would prove
the committed source and tests on GitHub, not a live provider execution.

## Stop condition

Publication must stop on base drift, an unapproved file, any real GitHub
approval-record write, real credential or provider access, downstream access,
test failure, registry/manifest mismatch, or scope expansion. Passing source and
fake-I/O tests permits only a Draft PR.
