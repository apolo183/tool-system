# Durable Module and Interface Registry v1

Repository: `tool-system`

Parent authority: user-authorized tool-system local cutover and durable module/interface registry work.

Global alignment: `blueprint/tool_system_v0.yaml:product_objective` requires a bounded blueprint-to-code system whose components can be changed and revalidated without an undocumented whole-system rewrite. This change turns the accepted durable-module rule into a local machine-readable inventory and declared dependency graph.

## Scope and reason

The v1 registry records the current tool-system implementation as 14 persistent functional modules. Each entry declares one natural owner, one responsibility, a module and public-interface version, input/output/error and side-effect contracts, code/data/test/runtime/cleanup boundaries, upstream and downstream dependencies, preconditions, authority, and acceptance/rollback/replacement evidence.

The validator fails closed on:

- unknown, missing, or extra contract fields;
- invalid module, semantic-version, interface-version, lifecycle, or status values;
- unsafe or unmatched active natural-owner paths;
- two modules claiming the same natural-owner file;
- unclaimed required source/config paths, unknown dependencies, self-dependencies, stale dependency versions, or stale interface versions;
- non-reciprocal upstream/downstream declarations;
- a cycle in the declared dependency graph.

## Changed boundaries

- `config/module_registry_v1.yaml` owns the declared module inventory.
- `config/module_registry_schema_v1.json` owns the serialized v1 field contract.
- `src/tool_system/architecture/module_registry.py` owns structural and semantic validation.
- `src/tool_system/cli/validate_module_registry.py` exposes the validator without granting execution authority.
- the blueprint, local principles, README, AGENTS, and alignment tests record the exact implemented claim.

No existing implementation package is moved or rewritten. Existing reports, task manifests, change plans, and active-gate inputs remain in place pending the separate process-authority migration.

## Claim boundary

This change proves only local structural validation of the registered inventory, natural owners, version references, reciprocal declared edges, and declared DAG. It does not derive or enforce Python import edges, isolate runtime memory or state by module, prove behavioral interface compatibility, automatically replace a module, execute cleanup, call a live provider, mutate finance-us or any other target repository, or deploy to production.

## Verification

```text
python -m tool_system.cli.validate_module_registry config/module_registry_v1.yaml
pytest -q tests/test_module_registry.py tests/test_milestone_module_invariant.py
pytest -q
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
git diff --check
```

Acceptance requires focused and full local tests, the active-gate validator, hosted required CI, squash merge, and a clean post-merge main verification.

## Rollback and replacement

Before merge, close the unmerged PR and retain its evidence. After merge, rollback or replacement uses a named PR that preserves Git and audit history, validates the affected public dependency closure, and leaves exactly one accepted active registry route. This change authorizes no destructive cleanup or branch deletion.
