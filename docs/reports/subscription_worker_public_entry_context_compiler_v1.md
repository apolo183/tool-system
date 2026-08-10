# Subscription Worker Public Entry Context Compiler v1

## Objective

This package composes the accepted `repository-context-api` and `blueprint-compiler-api` behind the existing root `tool-system develop` command. It consumes the passing authority preflight, opens one caller-selected exact clean local Git snapshot through the hardened read-only repository-context boundary, parses only the selected committed blueprint and module-registry blobs, and produces one deterministic bounded compilation.

## Order and fail-closed boundary

The production order is fixed:

1. validate bounded CLI input and the exact current manifest/change-plan pair;
2. freeze the redacted authority packet;
3. build and revalidate one exact clean repository context using local Git read operations only;
4. require the selected blueprint and module-registry blobs to be UTF-8 YAML mappings;
5. compile the caller-selected milestone set under the non-authorizing isolated-fixture envelope;
6. emit only redacted snapshot/context evidence, the compiled DAG, hashes, and explicit zero-effect counters.

Invalid authority, stale or dirty repositories, unsafe paths, missing evidence, invalid YAML, rejected owner evidence, invalid module bindings, overlaps, cycles, or finite-limit violations stop before a compilation packet is emitted.

## Privacy and effects

The public result does not expose the repository-root path or selected file contents. It may expose caller-selected repo-relative paths and content hashes needed for deterministic evidence. This package authorizes only the repository-context module's existing hardened local Git reads. It performs zero repository writes, local Git writes, worker invocations, API/provider calls, credential-value accesses, remote operations, production operations, cleanup, or rollback.

## Remaining closure

A passing context/compiler packet is still non-executing. Subscription-worker dispatch, isolated candidate mutation, validation/review, bounded local branch/commit, multi-stack acceptance, and final closure acceptance remain later packages under the already approved lifecycle. Optional API providers remain default off and non-gating.
