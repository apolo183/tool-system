# TS-M03 Task-Manifest Schema/CLI Authority-Equivalence Realignment Specification v1

## 1. Decision and frozen base

This report is the non-authority specification for
`TOOL-SYSTEM-TS-M03-TASK-MANIFEST-SCHEMA-CLI-AUTHORITY-EQUIVALENCE-REALIGNMENT-SPEC-v1`.
It corrects no code and grants no execution, repository, lifecycle, cleanup, or
public-acceptance authority.

The specification was prepared only after the GitHub App read
`refs/heads/main` and then the corresponding Git commit object in that order:

- repository: `apolo183/tool-system`
- canonical branch: `main`
- commit: `1373c98296bfc2999d0142de41926a3111b3f55f`
- tree: `b854500a7e74ae79de1fda27c119c99d4403de49`
- branch for this specification:
  `agent/ts-m03-task-manifest-schema-cli-authority-equivalence-realignment-spec-v1`
- commit message:
  `Specify TS-M03 task-manifest schema and CLI authority equivalence`

Any base commit or tree drift before publication or merge is a stop condition.

## 2. Confirmed defect

`harness/task_manifest.schema.json` declares JSON Schema Draft 2020-12, closes
the root and nested objects with `additionalProperties: false`, and constrains
`task_type` to nine values. The current
`validate_manifest_structure()` does not execute that Schema. It checks only
missing root keys, three non-empty values, two mapping values, and
`approval.required`. Consequently, the CLI can return structural PASS for a
mapping which the formal Schema rejects.

This is the confirmed TS-M03 governance defect. It is not evidence that a
Schema PASS grants authority. Repository policy, autonomy policy, the explicit
task-manifest/change-plan pair, lifecycle approval, and all execution gates
remain separate and fail closed.

## 3. Deterministic retained-corpus inventory

The inventory at the frozen base covers every tracked regular YAML file under
`examples/task_manifests/`. The cohort is fixed to commit
`1373c98296bfc2999d0142de41926a3111b3f55f`; later TS-M03 manifests are not
members of it. With paths sorted by UTF-8 bytes, joined with one trailing LF,
the 14,352 canonical bytes have SHA-256
`8389154c4a0782041ecc29bd636af71b52b62e632062f086e4cb06dd21d0b8c9`.
With each line encoded as `<path><TAB><git-blob-sha><LF>`, the 22,101 canonical
bytes have SHA-256
`18a964d4b75fc07cffa99350adb3bb84c5277d3244182a1d6c64fd3ceaf7141b`.

| Measure | Result |
| --- | ---: |
| Retained task manifests | 189 |
| PyYAML parse PASS / FAIL | 189 / 0 |
| Current CLI structural PASS / BLOCK | 178 / 11 |
| Current formal Schema PASS / BLOCK | 1 / 188 |

The sole formal-Schema PASS is
`examples/task_manifests/tool_system_p15c_local_operator_config_v1.yaml`.
The eleven CLI structural failures all omit `evidence`; nine also omit
`forbidden_files`.

The principal formal-Schema conflicts are:

| Conflict | Count |
| --- | ---: |
| root `alignment` not registered | 130 |
| root `publication` not registered | 72 |
| root `bounded_closure` not registered | 70 |
| root `authority_effect` not registered | 33 |
| `task_type` outside the nine-value formal enum | 76 |
| `rollback.execution_authorized` not registered | 65 |
| `evidence.ref` not registered | 39 |

There are twelve distinct root-key sets. Approval objects also vary: 80 use the
four formal fields, 103 use only `required` and `approved_by`, five use
`required`, `approved_by`, and `approval_source` and therefore omit only
`approved_at`, and one uses `required` plus `basis`. In total, 109 omit
`approved_at` and 104 omit `approval_source`. One visually complete timestamp
is decoded by PyYAML as a Python `datetime`, not the Schema-required string.

These files are retained evidence, not an active authority corpus.
`REPO_MANIFEST.md` classifies `examples/task_manifests/**/*` and
`examples/change_plans/**/*` with `authority=false` and
`runtime_default=false`. The implementation correction therefore MUST NOT
bulk-edit, grant authority to, or migrate that frozen historical cohort. Some
retained files can become structurally admissible after the compatible Schema
addition below; structural admissibility never changes their non-authority
classification. A formerly permissive CLI result does not promote a retained
file into a supported authority input.

A read-only shadow run in a creator-owned temporary copy replaced only the
Schema oracle described below, quoted the synthetic target fixture timestamp,
and ran the frozen 876-test suite. It exposed 127 Schema-induced failures in
42 test files. One additional failure was excluded because launching pytest
from standard input prevented a multiprocessing child from reopening the
launcher; it was not caused by Schema validation. This impact result is a
planning probe, not implementation or acceptance evidence. It proves that the
previous twelve-path estimate was incomplete and that preserving strict
authority requires an explicit affected-test migration.

## 4. One formal structural authority

The following ownership and equivalence contract is frozen:

1. `harness/task_manifest.schema.json` remains the single machine-readable
   task-manifest structural authority.
2. The natural code owner is the `manifest-validation` module.
3. `validate_manifest_structure(manifest) -> tuple[bool, list[str]]` remains the
   shared public Python boundary and keeps its input and result shapes.
4. `jsonschema` MUST be imported lazily inside the structure-validation path.
   `load_yaml_file()` remains usable without that dependency. `ImportError` is
   caught and returns a deterministic structural BLOCK.
5. The function reads the exact Schema once from
   `Path(__file__).resolve().parents[3] / "harness" /
   "task_manifest.schema.json"`, parses that captured byte string once,
   validates it with `Draft202012Validator.check_schema()`, and enumerates all
   instance errors with `Draft202012Validator.iter_errors()`.
6. Before validator construction, a recursive guard rejects every `$ref` which
   is not a string beginning `#/$defs/`, every `$dynamicRef` or `$recursiveRef`,
   and every nested `$id` that could change the resolution base. The root HTTPS
   `$id` is identity only and grants no network access.
7. There MUST be no second hand-written acceptance path, copied property list,
   permissive fallback, mock validator, caller-selected Schema, or
   network-fetched Schema.
8. Schema absence, unreadability, invalid JSON, meta-Schema failure, prohibited
   reference, resolution exception, or dependency failure MUST deterministically
   BLOCK before any fallback could run.

Let `J(M)` mean that `M` is an acyclic string-key mapping containing only JSON
values: null, bool, int, finite float, string, list, and string-key mapping. Let
`B` be the exact captured Schema bytes and `S = json.loads(B)` after
local-reference guarding and `Draft202012Validator.check_schema(S)` have both
succeeded. For every `M` where `J(M)` is true:

```text
validate_manifest_structure(M)[0]
  == (len(tuple(Draft202012Validator(S).iter_errors(M))) == 0)
```

If `J(M)` is false or Schema/dependency preparation fails, the left side is
false and the Schema equivalence expression is not evaluated.

The task-manifest CLI has a stronger overall decision:

```text
CLI_PASS(M) == SCHEMA_PASS(M) and REPO_POLICY_PASS(M) and AUTONOMY_POLICY_PASS
```

Therefore CLI PASS implies formal-Schema PASS. Formal-Schema PASS alone never
implies authorization. The change-plan CLI and repository controller already
delegate task-manifest structure checking to the same function and MUST retain
that single path.

## 5. Formal Schema realignment boundary

The implementation correction MUST preserve the current fourteen required
root fields and the current nine-value `task_type` enum. It MUST NOT add an
unversioned catch-all object, set root `additionalProperties` to true, or admit
every historical spelling merely to increase the corpus PASS count.

The Schema change is limited to fields with a current application-code
consumer:

### 5.1 `alignment`

An optional, strictly typed root `alignment` property is added because
`alignment_gate.py` reads it. When present it has exactly `parent` and `global`.
Each block has exactly the non-empty string fields `document`,
`section_or_key`, and `scope`. The alignment gate retains responsibility for
cross-document matching. Structural validity alone does not establish
alignment or authority.

### 5.2 `historical_fixture`

An optional, strictly typed root `historical_fixture` property is added because
`repo_write_policy.py` reads it for retired repositories. When present it has
exactly:

```yaml
closed: true
new_work_authorized: false
```

It can preserve a specifically policy-allowed closed fixture; it cannot permit
new work.

Applied to the frozen-base cohort, the strict `alignment` addition is expected
to move five retained files from structural BLOCK to structural PASS:
`examples/task_manifests/tool_system_blueprint_process_state_separation_v1.yaml`,
`examples/task_manifests/tool_system_p14c_check_provenance_v1.yaml`,
`examples/task_manifests/tool_system_p14c_live_issuer_v1.yaml`,
`examples/task_manifests/tool_system_p14c_pr_authorization_gate.yaml`, and
`examples/task_manifests/tool_system_project_state_single_owner_v1.yaml`.
Together with the original sole PASS, the
predicted post-correction structural result is 6 PASS / 183 BLOCK. All 189
remain `authority=false` and `runtime_default=false`. The historical finance
fixture remains structurally blocked because its `historical_fixture` object
also contains an unregistered `purpose` field.

### 5.3 Fields intentionally not admitted

The following retained narrative fields remain invalid in a formal active task
manifest: `authority_effect`, `bounded_closure`, `publication`, and
`rollback.execution_authorized`. Their contents belong in the paired change
plan or report and cannot manufacture authority.

Historical task types outside the current formal enum also remain invalid.
Future authors use the formal type matching the dominant change, for example
`docs_add`, `docs_modify`, `code_add`, or `code_modify`; historical labels are
not silently aliased.

Consumer-specific subscription bindings read by `task_runner.py` are not
silently admitted by this general Schema correction. Real repository execution
is already blocked by TS-B02. Before such a binding can become an active task
manifest input, its exact shape must be separately typed and adversarially
closed without weakening the general root. This specification grants no such
execution authority.

## 6. Parsed-value boundary and stable diagnostics

Schema/CLI equivalence begins with the parsed root mapping returned by the
existing YAML loader. Before invoking `jsonschema`, the implementation MUST
walk that mapping deterministically and accept only null, bool, int, finite
float, string, list, and string-key mapping. It rejects tuples, dates or
datetimes, bytes, sets, custom Python objects, non-finite numbers, non-string
keys, and cyclic containers. Cycle detection uses the current ancestor stack,
not a global seen set, so a shared but acyclic YAML alias DAG is not mistaken
for a cycle. The target fixture's `approval.approved_at` value MUST be quoted so
that it remains a string.

This correction does not claim lexical duplicate-key detection in raw YAML;
JSON Schema receives a parsed instance, not YAML tokens. No duplicate-key
hardening claim may be made without a separately reviewed loader change.

The public function receives no Schema-path parameter. Tests for missing,
malformed, meta-invalid, or prohibited-reference Schema cases may monkeypatch a
private module constant or private loader helper to a creator-owned temporary
file. That test seam still reaches the sole production validator and is not a
second acceptance path. Missing-dependency tests intercept the lazy import;
they do not uninstall packages or mutate the environment.

Third-party free-form error prose MUST NOT become the project contract. The
project emits stable reasons using these codes:

- `TASK_MANIFEST_NON_JSON_VALUE`
- `TASK_MANIFEST_SCHEMA_UNAVAILABLE`
- `TASK_MANIFEST_SCHEMA_INVALID`
- `TASK_MANIFEST_SCHEMA_VIOLATION`

Each violation reason includes the RFC 6901 instance pointer, local Schema
pointer, validation keyword, and a project-generated `normalized_detail`.
Pointer escaping is deterministic. Keyword-specific handlers construct
`normalized_detail` from canonical JSON constraints, missing keys, or unknown
keys and never from `error.message`. Complete duplicate records are removed;
the rest are sorted by `(instance_pointer, schema_pointer, keyword,
normalized_detail)`. Non-JSON reasons sort by `(instance_pointer, type_code)`.
No ordering depends on dictionary insertion order, locale, current working
directory, or third-party prose.

## 7. Dependency, license, and package boundary

The implementation dependency is frozen as `jsonschema==4.26.0`, invoked via
`Draft202012Validator`. Upstream PyPI metadata declares Draft 2020-12 support,
error-path querying, an MIT license, and Python `>=3.10` compatibility.

The future implementation may add only that direct runtime dependency to
`pyproject.toml` and records the exact version and MIT license in prose adjacent
to the manifest-validation compound contract. The current module registry's
`external_dependencies` field is a local module/provider-contract boundary,
not a Python-distribution inventory: it is empty today even though
`pyproject.toml` already declares PyYAML and a conditional tomli dependency,
and the current adapter rejects every non-empty value. It therefore MUST remain
`[]`; the correction MUST NOT mislabel a Python package as a registered local
module provider or change architecture-registry semantics incidentally.

This narrow recording does not provide a lock, transitive dependency seal,
package hash, provenance attestation, or vulnerability review. The only
workflow change permitted by the future closure is replacing the active-gate
validator's input path with the separately registered strict smoke index. The
implementation MUST NOT otherwise modify a workflow, runner, permissions,
Action pin, Python support matrix, lock the full dependency graph, or claim
TS-M02 supply-chain closure.

The dependency is lazily imported only when structure validation runs. The
source-checkout Schema path is exactly
`Path(__file__).resolve().parents[3] / "harness" /
"task_manifest.schema.json"`. The bytes are read once for one validation
construction. There is no environment-variable, current-working-directory, or
caller override. A wheel without that repository-local `harness` file returns
`TASK_MANIFEST_SCHEMA_UNAVAILABLE`; it does not embed or discover a second
Schema.

## 8. Module and interface versioning

The correction preserves the required-field set, every instance already valid
under the current formal Schema, the Python call signature, the
`(bool, list[str])` result, CLI `status/reasons` shape, fail-closed behavior, and
absence of command execution. It is a backward-compatible additive structural
contract change for two optional fields already consumed by application code,
plus a defect repair which removes the CLI's independent permissive path.

Accordingly:

- `manifest-validation` module version: `1.0.0 -> 1.0.1`
- aggregate interface: remain `manifest-validation-api@1.0.0`
- natural owner: `manifest-validation`
- package dependency co-owner: package maintainer
- registry and mapping-contract co-owner: `architecture-registry`

If implementation changes a required field, result shape, caller-supplied
Schema path, or public interface version, it is outside this specification and
must stop for a replacement authorization package.

## 9. Exact next implementation closure

The next task, which this specification does not start or authorize, is:

`TOOL-SYSTEM-TS-M03-TASK-MANIFEST-SCHEMA-CLI-AUTHORITY-EQUIVALENCE-CORRECTION-v1`

Its exact path closure is 58 paths: six ADD and 52 MODIFY. This larger closure
is mandatory because a strict Schema deliberately invalidates retained inputs
which the old validator treated as current positive fixtures.

ADD:

1. `docs/reports/tool_system_ts_m03_task_manifest_schema_cli_authority_equivalence_correction_v1.md`
2. `examples/task_manifests/tool_system_ts_m03_task_manifest_schema_cli_authority_equivalence_correction_v1.yaml`
3. `examples/change_plans/tool_system_ts_m03_task_manifest_schema_cli_authority_equivalence_correction_v1.yaml`
4. `tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml`
5. `tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml`
6. `tests/fixtures/manifest_validation/strict_active_gates_v1.yaml`

MODIFY:

7. `REPO_MANIFEST.md`
8. `.github/workflows/tool-system-ci.yml`
9. `harness/task_manifest.schema.json`
10. `src/tool_system/manifest/task_manifest.py`
11. `pyproject.toml`
12. `docs/modules/manifest-validation-contract-v1.md`
13. `docs/tool_system_module_registry_contract_v1.md`
14. `config/module_registry_v1.yaml`
15. `tests/fixtures/target_repo/task_manifest.yaml`
16. `tests/test_repo_manifest.py`
17. `tests/test_active_gate_resolver.py`
18. `tests/test_active_gates.py`
19. `tests/test_audit_bundle.py`
20. `tests/test_blueprint_compiler.py`
21. `tests/test_change_plan_gate.py`
22. `tests/test_cleanup_plan.py`
23. `tests/test_command_runner.py`
24. `tests/test_controller_actions.py`
25. `tests/test_controller_run.py`
26. `tests/test_controller_self_check.py`
27. `tests/test_execution_approval.py`
28. `tests/test_execution_state_snapshot.py`
29. `tests/test_final_record.py`
30. `tests/test_github_state_adapter.py`
31. `tests/test_global_principles.py`
32. `tests/test_live_github_collector.py`
33. `tests/test_main_ci.py`
34. `tests/test_module_registry.py`
35. `tests/test_multi_task.py`
36. `tests/test_mutation_command_packet.py`
37. `tests/test_p10r_a_machine_policy_enforcement.py`
38. `tests/test_p15c_execution_packet_freeze.py`
39. `tests/test_p15d_failure_economics_corpus_prerequisite.py`
40. `tests/test_p4d_precheck.py`
41. `tests/test_phase_alignment.py`
42. `tests/test_process_authority.py`
43. `tests/test_provider_portfolio_failure_control.py`
44. `tests/test_repo_controller.py`
45. `tests/test_repository_context_builder.py`
46. `tests/test_requirement_graph.py`
47. `tests/test_role_runtime.py`
48. `tests/test_root_cli.py`
49. `tests/test_stage_runner.py`
50. `tests/test_state_collector.py`
51. `tests/test_target_repo_dry_run.py`
52. `tests/test_target_repo_pr_plan_preview.py`
53. `tests/test_task_graph.py`
54. `tests/test_task_graph_runner.py`
55. `tests/test_task_manifest_policy.py`
56. `tests/test_task_runner.py`
57. `tests/test_write_intent.py`
58. `tests/test_write_packet.py`

No CLI source path is in the closure because both manifest CLIs already call
`validate_manifest_structure()`. No retained manifest is migrated. The two new
fixtures form one tool-system-targeted, read-only, no-command, fully strict
synthetic pair. `REPO_MANIFEST.md` and `tests/test_repo_manifest.py` register
the pair and its strict smoke index as three exact test-data paths and update
the formal-file count from 292 to 295.
The task fixture uses `task_type: read_only_audit`,
`target_repo: apolo183/tool-system`, `write_mode: read_only`, empty verification
commands, complete structurally synthetic approval metadata, and no runtime
binding. Neither a fixture label nor structural PASS is an authorization
decision; an explicitly supplied pair remains subject to every normal policy
and process-authority gate.
The change plan binds that exact task path, has the same empty command list,
and cannot authorize a repository change merely by naming a `changed_files`
scope required by the current plan contract.

The new strict smoke index is alignment-disabled and points only to the new
synthetic pair. The existing Hosted workflow changes exactly one command
argument from `examples/active_gates.yaml` to that new path. No step, job,
trigger, runner, permission, or Action reference changes.

`examples/active_gates.yaml` remains byte-identical. It is the content-addressed
108-pair legacy replay input bound by `config/replay_snapshot_v1.yaml`,
`config/process_authority_v1.yaml`, the process-authority implementation, and
its contract. It MUST NOT be rewritten, rehashed, relocated, or treated as the
strict active Schema smoke corpus. The process-authority validator, legacy
snapshot, source-level default resolver path, and all historical manifests and
plans remain unchanged. Under the corrected public validator, any attempt to
admit a structurally invalid historical manifest still fails closed.

`tests/test_change_plan_scope_extra.py` remains outside the closure. It calls
only the pure mapping-level wildcard scope primitive against a retained pair;
it does not call task-manifest structure validation, a CLI, a controller, or an
execution admission path and makes no current-authority claim.

The registry modifications are limited to
`manifest-validation.module_version=1.0.1`, adding exactly
`harness/task_manifest.schema.json`, the formal synthetic task/change-plan
pair, and its strict smoke index to `manifest-validation.boundaries.data`, and
updating the manifest-validation compound-contract references/hashes. Those
four paths
MUST NOT also appear in `boundaries.tests`; Python test files remain in that
group, preserving the registry's no-overlap invariant. `external_dependencies`
remains empty under its existing local provider-contract semantics. The
mapping contract changes only the module version and rollback identity.
`tests/test_module_registry.py` updates the registry byte-length, raw-SHA, and
semantic-SHA seals and tests the new boundaries; it does not weaken registry
validation.

The implementation branch and commit are frozen as:

- branch:
  `agent/ts-m03-task-manifest-schema-cli-authority-equivalence-correction-v1`
- commit message:
  `Correct TS-M03 task-manifest schema and CLI equivalence`

Any need for a 59th path, dependency other than `jsonschema==4.26.0`, raw YAML
loader change, any workflow change beyond the exact active-gate input argument,
or consumer production-code modification is a stop condition requiring a new
exact authorization package.

## 10. Adversarial and compatibility matrix

The primary implementation test owner is `tests/test_task_manifest_policy.py`;
the 42 affected test owners retain responsibility for their own entry points.
The correction MUST prove all of the following without mock Schema validation:

1. the quoted synthetic target fixture passes both the formal Schema and the
   shared structural function;
2. every formal required-field deletion blocks identically;
3. unknown root and nested fields block identically;
4. every out-of-enum `task_type` and rollback method blocks identically;
5. malformed `alignment` and any extra alignment key block identically;
6. `historical_fixture.closed != true` or
   `new_work_authorized != false` blocks identically;
7. `authority_effect`, `bounded_closure`, `publication`,
   `rollback.execution_authorized`, and `evidence.ref` remain blocked;
8. an unquoted timestamp, tuple, non-string key, non-finite number, custom
   value, or cyclic structure blocks with a stable project-owned reason, while
   a shared acyclic alias DAG does not false-block;
9. missing, malformed, meta-invalid, or remotely resolving Schema blocks with
   no old-validator fallback;
10. all simultaneous Schema errors are returned in deterministic pointer order;
11. direct function, task-manifest CLI, change-plan CLI, repository controller,
    and target-repository adapter expose an identical manifest-reason segment
    when their other context inputs are valid;
12. a Schema PASS plus policy BLOCK yields overall CLI BLOCK;
13. a Schema PASS never changes process authority or permits command execution;
14. the two frozen-base cohort seals reproduce; whether an individual retained
    file structurally passes or blocks, `REPO_MANIFEST.md` still classifies it
    as `authority=false` and `runtime_default=false`;
15. module-contract hashes, module registry, static import DAG, repository
    manifest, active gates, process authority, and updated registry raw/semantic
    seals remain valid;
16. full `pytest` passes on Hosted CI with zero Schema-induced failure.

The existing `tool_system_p3_repo_controller.yaml` retained file MUST NOT remain
an implicit active test fixture merely because the old CLI accepted it. Tests
must copy the formal synthetic target pair into a creator-owned temporary
directory and adapt only formally registered fields, or use the exact synthetic
pair with its injected policy. No test may monkeypatch, bypass, or replace the
production Schema validator.

The affected-test migration has three frozen dispositions. A file marked mixed
must preserve every listed disposition; it cannot convert its entire test
surface to only PASS or only BLOCK.

### 10.1 A: current positive consumers

Generic CLI, gate, controller, runner, and adapter positive cases use the
forward-valid synthetic pair and continue proving their original behavior:

- `tests/test_active_gate_resolver.py`
- `tests/test_active_gates.py`
- `tests/test_change_plan_gate.py`
- `tests/test_command_runner.py`
- `tests/test_controller_run.py`
- `tests/test_controller_self_check.py`
- `tests/test_github_state_adapter.py`
- `tests/test_live_github_collector.py`
- `tests/test_multi_task.py`
- `tests/test_p10r_a_machine_policy_enforcement.py`
- `tests/test_process_authority.py`
- `tests/test_repo_controller.py`
- `tests/test_stage_runner.py`
- `tests/test_task_graph_runner.py`

The committed positive active-gate case specifically validates
`tests/fixtures/manifest_validation/strict_active_gates_v1.yaml`; negative
pairing, order, policy, and alignment cases continue to use creator-owned
temporary inputs. The legacy `examples/active_gates.yaml` is tested only for
its process-authority snapshot identity and fail-closed admission behavior.
Tests also prove that resolving the synthetic pair is path selection only,
that its empty command list dispatches no subprocess, and that no repository
write occurs regardless of the returned validation status.

### 10.2 B: retained historical evidence

The following tests keep their byte, field, scope, state, report, seal, and
`authority=false` / `runtime_default=false` assertions:

- `tests/test_audit_bundle.py`
- `tests/test_blueprint_compiler.py`
- `tests/test_cleanup_plan.py`
- `tests/test_controller_actions.py`
- `tests/test_execution_approval.py`
- `tests/test_execution_state_snapshot.py`
- `tests/test_final_record.py`
- `tests/test_global_principles.py`
- `tests/test_main_ci.py`
- `tests/test_module_registry.py`
- `tests/test_mutation_command_packet.py`
- `tests/test_p15c_execution_packet_freeze.py`
- `tests/test_p15d_failure_economics_corpus_prerequisite.py`
- `tests/test_p4d_precheck.py`
- `tests/test_phase_alignment.py`
- `tests/test_provider_portfolio_failure_control.py`
- `tests/test_repository_context_builder.py`
- `tests/test_requirement_graph.py`
- `tests/test_role_runtime.py`
- `tests/test_state_collector.py`
- `tests/test_target_repo_dry_run.py`
- `tests/test_target_repo_pr_plan_preview.py`
- `tests/test_write_intent.py`
- `tests/test_write_packet.py`

Only when the exact retained instance is rejected by the new strict Schema does
its old task/change-plan CLI PASS expectation become deterministic Schema
BLOCK. The predicted six strict-Schema PASS instances remain PASS when directly
tested; they still gain no authority. A BLOCK is not reported as historical
artifact corruption.

### 10.3 Mixed A+B and A+B+C files

- `tests/test_root_cli.py`: run/batch routing families use the synthetic pair;
  the `tool_system_root_cli.yaml` retained-package family uses B.
- `tests/test_task_graph.py`: runnable graph/batch families use synthetic
  pairs; P7A/P7B/P7C retained-plan families use B.
- `tests/test_task_manifest_policy.py`: the Schema/CLI-equivalence and
  synthetic-target families use A; the
  `tool_system_p3_repo_controller.yaml` family proves retained classification
  and strict BLOCK under B.
- `tests/test_task_runner.py`: generic `run_task_pipeline` and explicit core
  pair families use A; context-compiler, snapshot, and semantic-correction
  package-freeze families use B. Subscription preflight, context, execution,
  and multi-stack public-entry families additionally prove that unregistered
  root/binding fields block before worker, subprocess, Git write, lease, call,
  or receipt effects. Deeper timeout, replay, candidate, receipt, and repair
  families feed the already constructed internal typed boundary directly;
  they do not monkeypatch the validator or make an unregistered manifest pass.

## 11. Affected-consumer closure

The public interface version remains unchanged, so consumer code is not
modified. Nevertheless, the correction MUST revalidate the nine direct
consumers registered for `manifest-validation`:

- `architecture-registry`
- `cleanup-planner`
- `cli-frontend`
- `process-authority`
- `repository-controller`
- `role-runtime`
- `target-repo-adapter`
- `task-planner`
- `task-runner`

Focused validation includes task-manifest policy, change-plan, alignment,
repository-controller, target-repository adapters, task planner/runner, module
contract, module registry, import graph, repository manifest, active-gate, and
process-authority tests, followed by full `pytest`.

The lazy import is part of the affected-consumer boundary: consumers that only
use `load_yaml_file()` do not become import-time dependants on `jsonschema`.
Missing dependency blocks only the structure-validation path and cannot revive
the old hand-written validator.

## 12. Preserved findings, state, and sequence

This specification and its later correction do not alter project state or
public acceptance. In particular:

- TS-B02 remains `confirmed_blocker` and real repository execution remains
  closed;
- TS-B01 remains `corrected_pending_reacceptance`;
- the public entry remains unaccepted;
- TS-H01, TS-H02, TS-H03, TS-M01, and TS-M02 are not corrected;
- TS-M03 is not corrected by this specification document; only a separately
  authorized implementation plus affected-closure evidence can move it to
  corrected-pending-reacceptance;
- TS-B02A, TS-B02B, TS-B02C, TS-B02D, and public-entry reacceptance are not
  started.

After a separately authorized TS-M03 implementation and its revalidation
close, the frozen order resumes at TS-B02A, then TS-B02B, TS-B02C, TS-B02D,
and finally public-entry reacceptance. No step may infer authority from this
report.

## 13. This specification package and publication stop

This task adds exactly these three non-authority paths:

1. this report;
2. `examples/task_manifests/tool_system_ts_m03_task_manifest_schema_cli_authority_equivalence_realignment_spec_v1.yaml`;
3. `examples/change_plans/tool_system_ts_m03_task_manifest_schema_cli_authority_equivalence_realignment_spec_v1.yaml`.

The task manifest is intentionally authored only with fields and nested keys
registered by the current formal Schema. A GitHub-App-bound prepublication
review checked that vocabulary and all current Schema keywords used by this
instance. Because the frozen base does not declare `jsonschema` as a project
dependency, neither the old CLI nor existing Hosted CI is represented as
formal-Schema execution evidence;
that missing equivalence oracle is precisely what the successor correction
must add.

Publication is one commit containing exactly three added mode-100644 paths and
one Draft pull request. Existing Hosted CI must pass without workflow or runner
changes. Only after base, head, exact paths,
commit count, checks, comments, reviews, and threads are re-read with no drift
may the PR be marked Ready and squash-merged with the expected head SHA. The
source branch is retained; if repository settings automatically delete it, the
exact original head ref is restored and re-read. The task then stops without
starting the implementation correction or any TS-B02A/runtime work.

## References

- Frozen commit:
  https://github.com/apolo183/tool-system/commit/1373c98296bfc2999d0142de41926a3111b3f55f
- Formal task-manifest Schema:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/harness/task_manifest.schema.json
- Current structural validator:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/src/tool_system/manifest/task_manifest.py
- Task-manifest CLI:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/src/tool_system/cli/validate_task_manifest.py
- Alignment consumer:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/src/tool_system/gate/alignment_gate.py
- Repository-policy consumer:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/src/tool_system/policy/repo_write_policy.py
- Retained-set authority classification:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/REPO_MANIFEST.md
- Manifest-validation module contract:
  https://github.com/apolo183/tool-system/blob/1373c98296bfc2999d0142de41926a3111b3f55f/docs/modules/manifest-validation-contract-v1.md
- `jsonschema` project and license:
  https://github.com/python-jsonschema/jsonschema
- `jsonschema` 4.26.0 package metadata:
  https://pypi.org/project/jsonschema/4.26.0/
