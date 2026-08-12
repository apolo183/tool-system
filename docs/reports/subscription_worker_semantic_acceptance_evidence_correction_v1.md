# Subscription worker semantic acceptance evidence correction v1

## Decision

At canonical `tool-system`
`main@f9dd68909ed0ffba9dc1a40197482d908c9cc2db` (tree
`aa12da08d6707beca83fe164339dbda9a3260d0a`), TS-B01 is confirmed: the
public validator copied the entire frozen acceptance set after every configured
command returned PASS, the code reviewer checked only candidate shape and
scope, and the contract reviewer checked only validation status and the copied
acceptance list.

This package replaces that public execution contract with
`subscription_public_entry_execution_binding_v2`. TS-B01 becomes
`corrected_pending_reacceptance`, not accepted. The historical
`accepted_subscription_worker_public_entry_core` decision remains reopened,
and real-repository execution remains blocked by TS-B02. The present
authorization covers this correction only; it grants neither public-entry
reacceptance nor correction of any other audit finding.

The authorized correction scope contains thirteen paths. The thirteenth path,
`tests/test_module_registry.py`, changes only the registry's raw byte-length,
raw SHA-256, and normalized semantic SHA-256 seals so the intentional
`config/module_registry_v1.yaml` update remains independently fail closed.

## Corrected evidence boundary

Every frozen acceptance item now requires exactly one ordered
`subscription_acceptance_evidence_obligation_v1`. The canonical obligation
binds:

1. the acceptance item and its canonical SHA-256;
2. one supported `behavior` or `contract` evidence type;
3. one unique exact validation command and its canonical SHA-256;
4. the expected stdout and stderr SHA-256 values;
5. the complete expected baseline-to-candidate diff path list; and
6. a present-content SHA-256 or absent-state assertion for every changed path.

The obligation itself has a canonical SHA-256. Coverage must be exact: the
ordered obligation items equal the frozen acceptance set, the unique commands
equal the frozen validation set in the same order, every asserted path is
inside the frozen scope, and no obligation, command, assertion, or changed
path is missing, duplicated, swapped, or extra. A v1 execution binding and any natural-language
acceptance item lacking this complete supported machine evidence fail closed.

After an exact command runs, command exit zero is only one prerequisite. The
validator also compares captured output digests, actual diff paths, and actual
candidate file state with the frozen obligation. It then issues one
`subscription_acceptance_evidence_receipt_v1` binding the obligation digest,
evidence type, frozen contract digest, actual candidate tree, actual diff,
command digest, exit code, output digests, and candidate-assertion digest. A
canonical receipt digest makes later tampering detectable.

The code reviewer independently recomputes the baseline-to-candidate diff,
candidate tree, candidate assertions, and expected receipt for each item. The
contract reviewer independently verifies exact complete item/command coverage,
obligation identity, validation receipt, candidate tree, frozen contract
digest, and receipt digest. Either reviewer returns the affected acceptance
item as violated on any mismatch. An empty diff cannot satisfy an obligation.

## Deterministic evidence

The task-runner suite covers:

- wrong candidate content with an unrelated command that exits successfully;
- two passing acceptance commands swapped between their frozen items;
- a receipt bound to the wrong acceptance item;
- a stale candidate-tree receipt;
- missing or duplicate obligation coverage;
- an empty candidate diff;
- a content-tampered receipt whose digest is recomputed; and
- correct remote-free Python and TypeScript fake-process fixtures.

The correct fixtures retain exactly one bounded local commit and zero remote,
provider, credential, target, production, cleanup, or rollback effects. The
negative fixtures stop before a local branch or commit. No test invokes a real
Codex executable, ChatGPT web automation, API provider, credential, or real
downstream repository.

## Compatibility and module disposition

Execution-binding v2 is a fail-closed input-contract replacement, so the
`task_runner` module becomes `2.0.0` and `task-runner-api` becomes `2.0.0`.
The root CLI remains its direct consumer and must supply a v2-bound manifest;
the public result envelope and all existing durable lease, call accounting,
terminal-code, remote-free local-Git, and hard-zero external-authority fields
remain unchanged.

Rollback identity is canonical base
`tool-system@f9dd68909ed0ffba9dc1a40197482d908c9cc2db:task_runner@1.2.0`.
Rollback execution is not authorized by this package.

## Residual boundary and stop

This correction does not provide OS-level validation isolation, bind the
resolved worker binary, or turn side-effect boundary fields into OS audit
observations. TS-B02 therefore remains a confirmed real-repository blocker.
TS-H01, TS-H02, TS-H03, TS-M01, and TS-M02 remain unchanged and unresolved.

The public entry is not reaccepted here. Real Codex Worker execution, real
downstream access, v3 isolated acceptance, API/provider execution, production,
cleanup, and rollback remain unauthorized. After the guarded squash merge,
work stops before any reacceptance or other finding correction.
