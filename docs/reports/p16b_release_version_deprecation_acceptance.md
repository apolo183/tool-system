# P16B Release, Version, and Deprecation Acceptance

P16B closes the core policy/interface gap identified by P16A. The
`release-governance` module is deterministic, provider-neutral, default-mainline
compatible, and performs no I/O.

## Accepted core evidence

- Canonical semantic versions are strictly parsed and ordered.
- Compatibility windows are inclusive and fail closed for too-old and future-major inputs.
- Deprecation transitions use only caller-supplied integer UTC epoch seconds and require monotonic dates plus an explicit replacement.
- Release-candidate decisions use stable ordered reason codes.
- A successful decision is only `ELIGIBLE_FOR_SEPARATE_AUTHORIZATION`; it is not release, deployment, production, provider, cleanup, or rollback authority.
- The module owns no provider/API dependency and does not make OPTIONAL-API-PROVIDER-PLUGIN-v2 a P16 Core gate.

## Remaining boundary

Artifact publication, package signing, deployment, production verification, real
migration, rollback, backup/restore, and disaster-recovery exercises remain
separately authorized work. P16 remains unaccepted. The next dependency is
P16C state migration and compatibility.
