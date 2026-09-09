# CubeSandbox backend acceptance contract v1 — local source evidence

Task: `TOOL-SYSTEM-TS-B02A-CUBESANDBOX-V070-ARM64-BACKEND-ACCEPTANCE-CONTRACT-v1`.
`authority_effect: none`. The initial-delivery record below is retained as
historical evidence, including its initial specification-completion claims.
The same-task review-correction appendix records the current tested candidate;
independent re-review remains pending.

## Frozen scope and alignment

The exact ten paths, budgets, verification commands and rollback are in
`examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml`,
bound to the same-named task manifest. The direct parent is the ARM64/KVM path
specification sections 9–11; the global anchor is
`blueprint/tool_system_v0.yaml:product_objective`. This task designs four
evidence predicates and synthetic tests; it implements no live backend and
changes no module, runtime interface, policy, blueprint or acceptance state.

The local starting main was clean at
`027dbb3fb83c38def70e81d58712f80dbe613483`, tree
`0480170128bb0c88a57eb91ff752a0ad954c6e08`. Authenticated GitHub current main
was read, followed by one local `git fetch --no-tags origin refs/heads/main`.
The candidate branch is
`agent/ts-b02a-cubesandbox-v070-acceptance-contract-v1`, based on
`306a01fa6bf3bc8ed4204b88abdcb4f16f75360e`, tree
`ec74af108b6f1d7d4c9c7e440aec128261f3f251`. Fetch updated `origin/main`, not
the local main branch. No commit, push, PR or merge is part of this task.

## Current source reads

The two fixed central paths were re-read from canonical GitHub main in this
task, not from a local governance checkout or a pinned central revision:

| Path | Returned blob identity |
| --- | --- |
| finance-governance `docs/global_development_principles_v1.md` | `17741fb79252b43d6ff820dcffc7c92ab349acfc` |
| finance-governance `config/repo_registry_v1.yaml` | `20c9ec3cd74337bbf4cf5c5ab19de3b7ccd7eaf3` |

Local current contracts, repository manifest, blueprint objective, project-state
boundary, process-authority API, command gate, strict task-manifest validator,
development-loop public API, task-runner evidence obligations and P16 readiness
mechanism were read before implementation. Existing file modification is limited
to four formal rows in `REPO_MANIFEST.md` and the two exact-count assertions in
`tests/test_repo_manifest.py` (295 to 299). The first full-suite failure exposed
this immediate test dependency. The task pair was corrected from nine to ten
paths and validated before editing that test; its remaining coverage and
rejection assertions were preserved. Existing retained non-authority globs cover
the reports and explicit task pair unchanged.

Upstream reads are pinned to `d0081641c59822e4e5653b7462e914410b81910a`:

| Path | Returned blob identity |
| --- | --- |
| `.github/workflows/release-docker-images.yml` | `e3cb7dda7523db6195a789271e2f7af047cc5d06` |
| `deploy/release-assets.yaml` | `67d8d4b79749c275f822a8c629b73b6aa3723cdb` |
| `Cubelet/services/cubebox/destroy_shim_wait.go` | `8f3cbe67f32b0ebbac678405758457eac553fbb5` |
| `Cubelet/services/cubebox/snapshot_runtime_binding.go` | `1f12bb8a2715635562f74760055bb3a06b2e5a11` |
| `Cubelet/network/runtime/network_runtime.go` | `d0eb29efb395b2ed84f3aab870505754804515c4` |
| `Cubelet/network/runtime/tap_lifecycle.go` | `9da7ef047f96858debe656f0c97d2dd6b9d30148` |
| `docs/guide/snapshot-rollback-clone.md` | `d8cbd36ce6704e950a3deb871bf097569b0b6789` |

Release-run metadata for `33152639150` reported matching source/tag, attempt 2,
completed/success, and the pinned reusable image workflow. Workflow source lines
725–729 state the no-published-attestation policy and `provenance: false`.
This is source/workflow evidence, not a provenance attestation, registry pull,
installation, host operation or runtime acceptance.

## Local validation environment and retained failures

Default `python` was Python 3.14.3 and lacked the project's already-pinned
`jsonschema==4.26.0`. System Python had jsonschema 4.10.3 but lacked pytest and
was not substituted. The old Python 3.12 directory lacked the requested `python`
entry and was not repaired.

The first task-local pip dependency preparation attempted the inherited index
through `127.0.0.1:17898`; sandbox networking returned `Operation not permitted`.
It was interrupted with exit 130. No escalation or network bypass was used.
The finite local-wheel fallback was:

```text
python -B -m pip install --no-index --disable-pip-version-check --no-cache-dir --target /tmp/ts-b02a-cubesandbox-contract-v1-deps --find-links /home/rich/wheelhouse/finance-app/py314-aarch64/pool jsonschema==4.26.0
```

Pip reported successful task-directory installation of attrs 26.1.0,
jsonschema 4.26.0, jsonschema-specifications 2025.9.1, referencing 0.37.0 and
rpds-py 2026.6.3. The enclosing pyenv shim nevertheless exited 1 with
`pyenv: cannot rehash: /home/rich/.pyenv/shims isn't writable`. No rehash or
permission repair followed. Actual imports and protected validation subsequently
succeeded using the explicit existing Python binary. The task dependency
directory is retained, not deleted, and the system Python/global package
environment was not changed. This is source-test dependency preparation, not
CubeSandbox host installation.

Validation uses the default sandbox, cwd `/home/rich/projects/tool-system`,
`PATH=/home/rich/.pyenv/versions/3.14.3/bin:/snap/ruff/current/bin:/usr/bin:/bin`,
`PYTHONPATH=src:/tmp/ts-b02a-cubesandbox-contract-v1-deps`, and
`PYTHONDONTWRITEBYTECODE=1`. No provider/credential environment is forwarded.
The existing protected `tool_system.gate.command_runner.run_commands` receives
the actual task pair, authority and policy paths, cwd and finite timeout; it
revalidates and compares bytes before dispatch. Its dispatch `status=PASS` is
not taken as test success: every actual command exit and output is checked.

## Validation receipts

Initial task-manifest and bound change-plan validators returned PASS, exit 0,
with empty reasons. Focused batch 1 passed:

```text
python -B -m pytest -q -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py
........................................................                 [100%]
56 passed in 2.57s
exit=0; stderr empty
```

Protected preflight: process authority PASS; manifest PASS; exact pair binding
PASS; change plan PASS; `validation_to_dispatch_inputs_equal=true`; one command.
Captured manifest SHA-256:
`6befe3892d5464449b87a40c0895d95082e4a5a85f702a7654b4957474084ce6`.
Captured focused-plan SHA-256:
`d4b36f947820d61680e5dd74a40fbecd1ca04c2513a47d66efe1f18b206a3496`.
The completed focused stage permits moving the same plan to its already listed
remaining validation batch; this changes no acceptance predicate or file scope.

Both full-suite attempts used this command in the environment above:

```text
python -B -m pytest -q -p no:cacheprovider
full-suite 1: 4 failed, 964 passed in 72.36s (0:01:12); exit=1
full-suite 2: 3 failed, 965 passed in 71.52s (0:01:11); exit=1
stderr empty; neither attempt timed out
```

The first candidate-caused failure was the existing manifest count assertion,
`assert 299 == 295`. Synchronizing its two assertions fixed that failure. The
three failures retained in the second run are:

| Test | Observed failure |
| --- | --- |
| `tests/test_durable_orchestrator_reliability.py::test_text_and_json_resource_bounds_fail_before_mutation` | `ValueError: database parent must not be group/world-writable` at unchanged `src/tool_system/orchestrator/durable.py:128` |
| `tests/test_durable_orchestrator_reliability.py::test_database_parent_identity_substitution_is_detected` | Same directory-mode rejection at `durable.py:128` |
| `tests/test_p14h_multi_stack_e2e.py::test_typescript_language_neutral_flow_records_add_modify_delete` | `FileNotFoundError: [Errno 2] No such file or directory: 'node'` in the fixture syntax validator |

The inherited umask was read as `0002`; neither that setting nor existing file
permissions were changed. Node was unavailable in the validation PATH. These
observations identify environment prerequisites in unchanged test/runtime files;
no separate pristine-baseline run was performed, so they are not a verified
canonical-main baseline classification. No test was skipped, weakened, repaired
outside scope, or converted to PASS. Overall full-suite status is **NOT_PASSED**.

First-run lint reported two I001 import-layout diagnostics and one RUF007
successive-pair diagnostic. Explicit import layout and `itertools.pairwise`
resolved them. An intermediate format check requested a one-line expression;
the final format check passed. No production source changed.

After the second full suite, source comparison with the written G4 contract
identified one final boundary error: one clean sample first observed exactly at
the deadline was BLOCKED even though two clean samples were required. Repair
cycle 2 added exact-deadline and after-deadline regressions. Focused run 2 first
demonstrated the defect (`1 failed, 57 passed in 2.70s`, exit 1;
`assert 'BLOCKED' == 'FAIL'`). The bounded correction now returns
`NETWORK_RELEASE_DEADLINE_UNPROVED / FAIL`. Focused run 3 on final oracle/test
bytes passed:

```text
python -B -m pytest -q -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py
..........................................................               [100%]
58 passed in 2.69s
exit=0; stderr empty; timeout=false
```

The 58 cases cover all requested positive/negative outcomes and the existing
pure development-loop consumer. The final two additional regressions were run
in the focused suite; full-suite run 2 preceded that last small predicate
correction. The two-run full-suite budget is spent; no later full-suite or
Hosted CI pass is claimed. Repair cycles used: 2/2; focused runs: 3/3; full
suites: 2/2; branches: 1/1; changed paths: 10/10 after documented correction.

The remaining required checks produced:

| Exact command | Result |
| --- | --- |
| `ruff check tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py` | Final exit 0, `All checks passed!` |
| `ruff format --check tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py` | Final exit 0, `2 files already formatted` |
| `python -B -m tool_system.cli.validate_active_gates tests/fixtures/manifest_validation/strict_active_gates_v1.yaml` | PASS, exit 0, empty reasons |
| `python -B -m tool_system.cli.validate_process_authority config/process_authority_v1.yaml` | PASS, exit 0, 108 retained replay pairs, no execution authority from replay |
| `python -B -m tool_system.cli.validate_module_registry config/module_registry_v1.yaml --require-current-authority` | PASS, exit 0, empty reasons |
| `python -B -m tool_system.cli.validate_repo_manifest REPO_MANIFEST.md` | PASS, exit 0, 299 formal files, 842 tracked paths, zero unclassified paths |
| `git diff --check` | Exit 0 |

Both full batches and both boundary-regression batches passed the existing
protected authority/manifest/pair/plan preflight and captured equal inputs
before dispatch. Every actual child exit was checked independently from the
dispatch PASS. The first full-plan hash was
`422264abf74f1669fb68ff307680ca08f589910e296b681a866c55cea465379a`;
the second was
`776d5b01bde8bf9d56fd53fd40bb70fa5b78920d453c71173a7566f558e5601a`.
Final task-pair identities and all other candidate source bytes are below. The
evidence record itself is deliberately excluded from self-referential hashing.

```text
0694d1ebc6ba31e5dd1cc6bc3cec2d3105c631d1f657e0dc81645b8b84956ac9 docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md
11c0b259c9304fcb5edd1ddafa1c7c60516d0563b46ab91161213df40c52b49f harness/cubesandbox_backend_acceptance_v1.schema.json
835b7dd516ae0df69ad1b42a23505bd3f1b89826d97be9e584893fc7eab9fe58 tests/fixtures/cubesandbox_backend_acceptance_v1.json
dfc43f6215567af0e367e9d3ae4952cbffdf8065fd506db24df8ff389d91ce86 tests/cubesandbox_contract_oracle.py
e7125772e597fac63a2b4b9295cd473a75268cd98417f1c8388c5e71434c6b21 tests/test_cubesandbox_backend_acceptance_contract.py
6b9b644c02c9e565ba360ed8a929288bf311d30e07a2ea738da7baa083b61b00 examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml
bdddabc439b7f1bf884ec37e828f4b2ec5e1598498fc9e901f110ea3212b37f0 examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml
73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59 REPO_MANIFEST.md
98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362 tests/test_repo_manifest.py
```

## Real-host blockers and claims

Lifecycle-manager ARM64 OCI digest remains null. The executable closure, asset
hash/source chain, selected topology, registry resolution, current host
permissions, PID1 FD/async-close observer, complete network attribution,
snapshot identities, core containment and exact future probe package remain
unproved. The test-only oracle rejects real-host imports. Independent review and
separate real-host authorization are required; no automatic continuation.

```text
SOURCE_AND_CONTRACT_ONLY=true
DGX_EXECUTION=false
HOST_INSTALLATION=false
NETWORK_MUTATION=false
SYSTEMD_MUTATION=false
CANONICAL_MAIN_WRITE=false
REAL_BACKEND_ACCEPTANCE_EXECUTED=false
G1_SPEC_COMPLETE=true
G2_SPEC_COMPLETE=true
G3_SPEC_COMPLETE=true
G4_SPEC_COMPLETE=true
REAL_BACKEND_ACCEPTANCE_AUTHORIZED=false
```

Here `DGX_EXECUTION` and `HOST_INSTALLATION` describe the prohibited backend/host
operations, not the explicitly authorized local source/fixture tests or their
task-local dependency files. No CubeSandbox binary/service/VM/workload ran.


## Same-task review correction — retained entry evidence

This appendix records the explicitly authorized continuation of the same task
and branch. All initial-delivery failures and consumed budgets above remain
retained. The supplied review was a finding source; the actual disk candidate,
index, hashes and original tool receipts were checked before new assertions.
Current central main returned the same two formal blob identities listed above.
No branch, task variant, eleventh candidate file, dependency installation or
host probe was created. The following read-only entry audit is original output:

```text
{
  "files": [
    {
      "path": "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md",
      "sha256": "0694d1ebc6ba31e5dd1cc6bc3cec2d3105c631d1f657e0dc81645b8b84956ac9",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "harness/cubesandbox_backend_acceptance_v1.schema.json",
      "sha256": "11c0b259c9304fcb5edd1ddafa1c7c60516d0563b46ab91161213df40c52b49f",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "tests/fixtures/cubesandbox_backend_acceptance_v1.json",
      "sha256": "835b7dd516ae0df69ad1b42a23505bd3f1b89826d97be9e584893fc7eab9fe58",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "tests/cubesandbox_contract_oracle.py",
      "sha256": "dfc43f6215567af0e367e9d3ae4952cbffdf8065fd506db24df8ff389d91ce86",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "tests/test_cubesandbox_backend_acceptance_contract.py",
      "sha256": "e7125772e597fac63a2b4b9295cd473a75268cd98417f1c8388c5e71434c6b21",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "sha256": "6b9b644c02c9e565ba360ed8a929288bf311d30e07a2ea738da7baa083b61b00",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "sha256": "bdddabc439b7f1bf884ec37e828f4b2ec5e1598498fc9e901f110ea3212b37f0",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "REPO_MANIFEST.md",
      "sha256": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "retained_digest_match": true,
      "index_equal": true
    },
    {
      "path": "tests/test_repo_manifest.py",
      "sha256": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362",
      "retained_digest_match": true,
      "index_equal": true
    }
  ],
  "evidence_sha256": "646f7f0f388d9256a24db1f2f10cfa6d4bc2fa32e5e9793371030da6ceee0d4c",
  "staged_patch_sha256": "933d44614e6cb2a5604fb30ecf95555de28cfc7fca045ddc818c012ba0732c50",
  "test_environment": {
    "pytest": "9.1.1",
    "jsonschema": "4.26.0"
  },
  "node": null
}
images, or choose a weaker backend.

## 6. Frozen ephemeral guest topology

Each future execution must use a fresh task/execution-scoped guest lifecycle.
Reusing an unreset mutable guest across requests is prohibited. The selected
topology must bind and prove all of the following before workload release:

| Layer | Frozen candidate boundary |
| --- | --- |
| Host provider | One exact DGX boot identity, kernel identity, KVM capability set, VMM executable and full interpreter/loader chain, firmware, machine type, device graph, launch configuration, and provider policy digest. |
| Host process containment | The execution-specific VMM, every execution-specific helper, thread and provider-owned descendant are placed in an owned host cgroup and tracked with stable process identities such as pidfds. Provider failure, timeout, or evidence loss terminates that complete host-side boundary. A stack that requires an unowned shared system daemon is a blocker for this profile unless a separate re-freeze names it as a trusted long-lived control plane and distinguishes it from execution-owned cleanup. |
| Guest boot | A sealed ARM64 guest kernel, initrd where used, command line, minimal root image, boot configuration, and guest policy are identified by exact immutable digests. Secure or measured boot is not claimed unless separately implemented and proved. |
| Storage | A read-only sealed base plus a disposable per-run overlay. Content-addressed input is attached read-only; scratch and declared-output devices are disposable and quota-bound. No host home, repository tree, raw host block device, or provider-control path is exposed. |
| Host sharing | No 9p, virtiofs, shared folder, host bind mount, arbitrary host file descriptor, or equivalent host-filesystem sharing. Declared output is detached and processed only through the bounded post-workload procedure below. |
| Network | No guest NIC, TAP, bridge, macvtap, SLIRP, `passt`, inherited socket, or equivalent network path for `deny_all`. Before the first workload instruction, an ARM64-derived and identity-sealed seccomp filter or equivalent guest-OS control must also fail closed on the frozen network-socket ABI. Device absence alone is insufficient. If QEMU is later selected, flags such as `-nic none` and `-nodefaults` are inputs to inspect, not sufficient evidence by themselves. [Q2] |
| Control channels | No workload-accessible vsock, QMP, monitor, qemu-guest-agent, serial control protocol, provider socket, or host management endpoint. A deliberately minimal provider-owned ordinary stdout/stderr path may exist only under bounded streaming semantics and may not become a bidirectional escape surface. |
| Evidence channel | Guest OS observations travel over a separate, provider-owned, one-way guest-supervisor-to-host channel that the workload cannot read or write. It is finite in bytes and events and binds execution nonce, request digest, guest boot identity, provider identity, event type and sequence. Loss, truncation, reordering, duplication, identity mismatch, or workload writability blocks. It is local provider evidence, not independent attestation. |
| Devices | No GPU, host USB, host PCI, VFIO, arbitrary device, host credential store, or provider-control device passthrough. Required synthetic guest devices are exact, minimal, and frozen. |
| Guest containment | The workload starts only after guest cgroup, namespace, mount, filesystem, network, identity, quota, stream, timeout, and evidence collectors are established. The workload remains unprivileged relative to guest init/provider controls. |
| Disposal | Completion destroys the guest execution state and proves host VMM/helper exit, guest descendant termination, detached storage, removed overlay and temporary channels, released mounts/device mappings, and empty owned cgroups. This proves resource/reference removal, not forensic secure erase of the underlying NVMe media. |

The future implementation may choose a different concrete VMM or guest device
model only through a separately authorized re-freeze. It may not weaken the
semantic boundary by arguing that VM separation makes one of the conjunctive
TS-B02 guarantees unnecessary.

Ordinary stdout/stderr, the evidence channel, and any future
`subscription_transport_only` channel are disjoint. The first carries bounded
workload bytes, the second carries bounded provider observations, and neither
authorizes network access or live Codex transport. The evidence channel has no
workload-controlled inbound side and cannot be reused as a command or data-
transfer backchannel.

Declared-output finalization is ordered, not circular:

37:The pre-execution closure is:
79:requirement was an execution boundary that does not rely on the observed
102:real-execution authorization.
133:- that the intended execution identity can open `/dev/kvm` or successfully
180:- native execution on the DGX host;
182:- software-emulated TCG execution;
194:Each future execution must use a fresh task/execution-scoped guest lifecycle.
201:| Host process containment | The execution-specific VMM, every execution-specific helper, thread and provider-owned descendant are placed in an owned host cgroup and tracked with stable process identities such as pidfds. Provider failure, timeout, or evidence loss terminates that complete host-side boundary. A stack that requires an unowned shared system daemon is a blocker for this profile unless a separate re-freeze names it as a trusted long-lived control plane and distinguishes it from execution-owned cleanup. |
207:| Evidence channel | Guest OS observations travel over a separate, provider-owned, one-way guest-supervisor-to-host channel that the workload cannot read or write. It is finite in bytes and events and binds execution nonce, request digest, guest boot identity, provider identity, event type and sequence. Loss, truncation, reordering, duplication, identity mismatch, or workload writability blocks. It is local provider evidence, not independent attestation. |
210:| Disposal | Completion destroys the guest execution state and proves host VMM/helper exit, guest descendant termination, detached storage, removed overlay and temporary channels, released mounts/device mappings, and empty owned cgroups. This proves resource/reference removal, not forensic secure erase of the underlying NVMe media. |
288:   attempts to restore it through `setrlimit` or `prlimit64` are denied and
307:attempts to restore dumpability or core limits. Guest self-report, no core file,
313:cleanup interval must be bound to the same execution. If the host's pipe helper
380:  evidence-channel identity, execution nonce, request digest, guest boot
413:| provider-effective plan, enforcement and `ExecutionEvidenceV1` | future TS-B02A isolated-execution backend/provider | Resolve and seal actual provider configuration, gate, boot, execute, enforce, observe, terminate, parse declared output, clean, and return the immutable composite record; do not choose business policy or publish acceptance. |
414:| independent matching and TS-B01/TS-B02 join | future TS-B02C task-runner | Revalidate every worker/validation execution record and join it with matching TS-B01 semantic evidence before any execution/effect projection. |
415:| affected-closure acceptance | future TS-B02D evidence owner | Revalidate adversarial and consumer closure; do not implement runtime or enable real execution. |
438:  and its survival may never be reported as execution-owned cleanup; [K2]
498:It must be separately authorized for execution by the DGX-local Codex CLI; the
563:authorization. Neither prerequisite may fall back to native DGX execution,
564:ordinary subprocess execution, a container, TCG, Hosted x86_64, or PR #231.
573:  `agent/subscription-worker-ts-b02a-core-local-os-isolated-execution-v1`;
598:- real repository execution: blocked;
623:or real execution.
```

### Counterexample round (additional targeted 1/2)

Protected dispatch receipt, including complete original stdout and stderr:

```json
{
  "status": "PASS",
  "preflight": {
    "process_authority_result": {
      "status": "PASS",
      "authority_path": "config/process_authority_v1.yaml",
      "module_id": "process-authority",
      "module_version": "2.3.0",
      "public_interface_id": "process-authority-api",
      "public_interface_version": "2.1.0",
      "current_task_input_mode": "explicit_manifest_change_plan_pair",
      "implicit_repository_index_allowed": false,
      "legacy_authority": false,
      "replay_result": {
        "status": "PASS",
        "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
        "pair_count": 108,
        "authority": false,
        "replay_only": true,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "production_deployment": false,
      "cleanup_execution": false,
      "reasons": []
    },
    "manifest_result": {
      "status": "PASS",
      "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "policy_path": "policy/repo_write_policy.yaml",
      "reasons": [],
      "autonomy_policy_path": "policy/autonomy_policy.yaml"
    },
    "pair_binding_result": {
      "status": "PASS",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "binding_mode": "explicit_manifest_change_plan_pair",
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "reasons": []
    },
    "change_plan_result": {
      "status": "PASS",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "reasons": []
    },
    "replay_execution_requested": false,
    "validation_to_dispatch_inputs_equal": true
  },
  "input_sha256_before": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "6ac85b690869549fffe6e5a47a7a182c0fd09ed7d1f60609614420e767a1226d",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "input_sha256_after": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "6ac85b690869549fffe6e5a47a7a182c0fd09ed7d1f60609614420e767a1226d",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "command_results": [
    {
      "name": "python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 1,
      "stdout": "..........................................................FFFFFFFFFF     [100%]\n=================================== FAILURES ===================================\n___________ test_review_jointly_empty_embedded_artifacts_cannot_pass ___________\ntests/test_cubesandbox_backend_acceptance_contract.py:485: in test_review_jointly_empty_embedded_artifacts_cannot_pass\n    assert gate(evaluate(evidence, catalog), 0)[\"status\"] == \"BLOCKED\"\nE   AssertionError: assert 'PASS' == 'BLOCKED'\nE     \nE     - BLOCKED\nE     + PASS\n_________ test_review_previous_owned_identity_cannot_become_background _________\ntests/test_cubesandbox_backend_acceptance_contract.py:496: in test_review_previous_owned_identity_cannot_become_background\n    assert gate(evaluate(evidence, catalog), 3)[\"status\"] == \"FAIL\"\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n______________ test_review_penultimate_fd_gap_at_deadline_is_fail ______________\ntests/test_cubesandbox_backend_acceptance_contract.py:504: in test_review_penultimate_fd_gap_at_deadline_is_fail\n    assert gate(evaluate(evidence, catalog), 1)[\"status\"] == \"FAIL\"\nE   AssertionError: assert 'BLOCKED' == 'FAIL'\nE     \nE     - FAIL\nE     + BLOCKED\n__________ test_review_no_pid1_retention_with_complete_scan_can_pass ___________\ntests/test_cubesandbox_backend_acceptance_contract.py:511: in test_review_no_pid1_retention_with_complete_scan_can_pass\n    assert gate(evaluate(evidence, catalog), 1)[\"status\"] == \"PASS\"\nE   AssertionError: assert 'BLOCKED' == 'PASS'\nE     \nE     - PASS\nE     + BLOCKED\n___________ test_review_runtime_deny_all_evidence_cannot_be_omitted ____________\ntests/test_cubesandbox_backend_acceptance_contract.py:517: in test_review_runtime_deny_all_evidence_cannot_be_omitted\n    assert gate(evaluate(evidence, catalog), 3)[\"status\"] == \"FAIL\"\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n___________ test_review_restored_actual_components_cannot_be_omitted ___________\ntests/test_cubesandbox_backend_acceptance_contract.py:523: in test_review_restored_actual_components_cannot_be_omitted\n    assert gate(evaluate(evidence, catalog), 2)[\"status\"] == \"FAIL\"\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n______ test_review_binding_fields_are_machine_required[component-fields0] ______\ntests/test_cubesandbox_backend_acceptance_contract.py:536: in test_review_binding_fields_are_machine_required\n    assert fields <= set(SCHEMA[\"$defs\"][definition][\"required\"])\nE   AssertionError: assert {'artifact_type'} <= {'architectur...ase_tag', ...}\nE     \nE     Extra items in the left set:\nE     'artifact_type'\n_______ test_review_binding_fields_are_machine_required[catalog-fields1] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:536: in test_review_binding_fields_are_machine_required\n    assert fields <= set(SCHEMA[\"$defs\"][definition][\"required\"])\nE   AssertionError: assert {'approved_cl...ed_artifacts'} <= {'catalog_id'...d_components'}\nE     \nE     Extra items in the left set:\nE     'network_policy'\nE     'approved_clean_templates'\nE     'required_artifacts'\n______ test_review_binding_fields_are_machine_required[snapshot-fields2] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:536: in test_review_binding_fields_are_machine_required\n    assert fields <= set(SCHEMA[\"$defs\"][definition][\"required\"])\nE   AssertionError: assert {'source_exec...tate_domains'} <= {'checkpoint_...ot_path', ...}\nE     \nE     Extra items in the left set:\nE     'source_kind'\nE     'source_execution_id'\nE     'source_request_sha256'\nE     'state_domains'\n_______ test_review_binding_fields_are_machine_required[restore-fields3] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:536: in test_review_binding_fields_are_machine_required\n    assert fields <= set(SCHEMA[\"$defs\"][definition][\"required\"])\nE   AssertionError: assert {'components'...restore_mode'} <= {'checkpoint_...ce_keys', ...}\nE     \nE     Extra items in the left set:\nE     'components'\nE     'restore_mode'\nE     'request_sha256'\nE     'execution_id'\n=========================== short test summary info ============================\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_jointly_empty_embedded_artifacts_cannot_pass\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_previous_owned_identity_cannot_become_background\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_penultimate_fd_gap_at_deadline_is_fail\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_no_pid1_retention_with_complete_scan_can_pass\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_runtime_deny_all_evidence_cannot_be_omitted\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_restored_actual_components_cannot_be_omitted\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_binding_fields_are_machine_required[component-fields0]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_binding_fields_are_machine_required[catalog-fields1]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_binding_fields_are_machine_required[snapshot-fields2]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_review_binding_fields_are_machine_required[restore-fields3]\n10 failed, 58 passed in 3.00s\n",
      "stderr": ""
    }
  ],
  "subprocess_call_count": 1,
  "reasons": []
}
```

### Exact baseline dependency comparison (1/1)

The three selected tests execute byte-identical baseline source and fixtures in
the same retained environment. This is not a pristine full-tree run: the
candidate contract files remain present and are not loaded by these tests.
No baseline checkout, branch, source rewrite, mode or PATH repair occurred.
The complete related dependency set (144 files) was read from Git archive bytes
at the exact baseline and compared before dispatch. No archive was extracted.

```text
{
  "baseline": "306a01fa6bf3bc8ed4204b88abdcb4f16f75360e",
  "tree": "ec74af108b6f1d7d4c9c7e440aec128261f3f251",
  "matched_files": 144,
  "dependency_closure_sha256": "60f5f7eb0b9791c14909e944a99da069770ef7f1a436a4485d651e9263d6f4d8",
  "all_bytes_equal": true,
  "mode": "exact baseline dependency bytes in unchanged source-test environment; no checkout or branch"
}
```

```json
{
  "status": "PASS",
  "preflight": {
    "process_authority_result": {
      "status": "PASS",
      "authority_path": "config/process_authority_v1.yaml",
      "module_id": "process-authority",
      "module_version": "2.3.0",
      "public_interface_id": "process-authority-api",
      "public_interface_version": "2.1.0",
      "current_task_input_mode": "explicit_manifest_change_plan_pair",
      "implicit_repository_index_allowed": false,
      "legacy_authority": false,
      "replay_result": {
        "status": "PASS",
        "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
        "pair_count": 108,
        "authority": false,
        "replay_only": true,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "production_deployment": false,
      "cleanup_execution": false,
      "reasons": []
    },
    "manifest_result": {
      "status": "PASS",
      "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "policy_path": "policy/repo_write_policy.yaml",
      "reasons": [],
      "autonomy_policy_path": "policy/autonomy_policy.yaml"
    },
    "pair_binding_result": {
      "status": "PASS",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "binding_mode": "explicit_manifest_change_plan_pair",
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "reasons": []
    },
    "change_plan_result": {
      "status": "PASS",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "reasons": []
    },
    "replay_execution_requested": false,
    "validation_to_dispatch_inputs_equal": true
  },
  "input_sha256_before": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "1154d24e1e7a7beec496c4f2861896e6b55d7641da74a4a28753820a3644aca4",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "input_sha256_after": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "1154d24e1e7a7beec496c4f2861896e6b55d7641da74a4a28753820a3644aca4",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "command_results": [
    {
      "name": "python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_durable_orchestrator_reliability.py::test_text_and_json_resource_bounds_fail_before_mutation tests/test_durable_orchestrator_reliability.py::test_database_parent_identity_substitution_is_detected tests/test_p14h_multi_stack_e2e.py::test_typescript_language_neutral_flow_records_add_modify_delete",
      "exit_code": 1,
      "stdout": "FFF                                                                      [100%]\n=================================== FAILURES ===================================\n___________ test_text_and_json_resource_bounds_fail_before_mutation ____________\ntests/test_durable_orchestrator_reliability.py:154: in test_text_and_json_resource_bounds_fail_before_mutation\n    record_store = _store(record_path, max_record_bytes=16)\n                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\nsrc/tool_system/orchestrator/durable.py:128: in __init__\n    raise ValueError(\"database parent must not be group/world-writable\")\nE   ValueError: database parent must not be group/world-writable\n____________ test_database_parent_identity_substitution_is_detected ____________\ntests/test_durable_orchestrator_reliability.py:305: in test_database_parent_identity_substitution_is_detected\n    store = _store(parent)\n            ^^^^^^^^^^^^^^\ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\nsrc/tool_system/orchestrator/durable.py:128: in __init__\n    raise ValueError(\"database parent must not be group/world-writable\")\nE   ValueError: database parent must not be group/world-writable\n_______ test_typescript_language_neutral_flow_records_add_modify_delete ________\ntests/test_p14h_multi_stack_e2e.py:362: in test_typescript_language_neutral_flow_records_add_modify_delete\n    root, head, result, _ = _run_compiled_stack(\ntests/test_p14h_multi_stack_e2e.py:166: in _run_compiled_stack\n    result = run_durable_local_git(\nsrc/tool_system/local_git/orchestrator.py:636: in run_durable_local_git\n    loop_result = run_development_loop(\nsrc/tool_system/development_loop/loop.py:433: in run_development_loop\n    validation_results, satisfied, blockers = _validation(validator(candidate), contract)\n                                                          ^^^^^^^^^^^^^^^^^^^^\nsrc/tool_system/local_git/orchestrator.py:621: in durable_validator\n    result = validator(candidate)\n             ^^^^^^^^^^^^^^^^^^^^\ntests/test_p14h_multi_stack_e2e.py:331: in validator\n    syntax = all(\n             ^^^\ntests/test_p14h_multi_stack_e2e.py:332: in <genexpr>\n    subprocess.run(\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:554: in run\n    with Popen(*popenargs, **kwargs) as process:\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1038: in __init__\n    self._execute_child(args, executable, preexec_fn, close_fds,\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1989: in _execute_child\n    raise child_exception_type(errno_num, err_msg, err_filename)\nE   FileNotFoundError: [Errno 2] No such file or directory: 'node'\n=========================== short test summary info ============================\nFAILED tests/test_durable_orchestrator_reliability.py::test_text_and_json_resource_bounds_fail_before_mutation\nFAILED tests/test_durable_orchestrator_reliability.py::test_database_parent_identity_substitution_is_detected\nFAILED tests/test_p14h_multi_stack_e2e.py::test_typescript_language_neutral_flow_records_add_modify_delete\n3 failed in 0.34s\n",
      "stderr": ""
    }
  ],
  "subprocess_call_count": 1,
  "reasons": []
}
```


### Final correction results and preserved budget

The single authorized correction batch changed only the original ten-path
candidate scope. Final targeted round (additional 2/2) passed all 107 tests,
including all original 58 regressions. No source/schema/fixture/test change
followed this run. Only final plan bookkeeping and this evidence appendix were
updated afterward; dispatch plan hash and final plan hash are separately
retained. Ruff, format and all four repository validators passed. No production
runtime, systemd termination implementation, formal project state, governance
policy or existing safety rejection was changed.

| Verified counterexample on entry bytes | Before | Final expected behavior actually tested |
| --- | --- | --- |
| Approved and observed embedded assets both empty | G1 PASS | G1 BLOCKED; fixed artifact minimum also survives clearing the declared obligation set |
| Earlier owned object relabelled background in a later deadline sample | G4 PASS | G4 FAIL; immutable ownership history remains active across rounds |
| Penultimate FD coverage missing, only terminal sample complete/empty at deadline | G2 BLOCKED | G2 FAIL |
| No PID1-retained stdio object, with complete scans | G2 BLOCKED | G2 PASS; helper and async-close residue still independently FAIL |
| Runtime deny_all evidence omitted | G4 PASS | Schema FAIL; permissive, late, inactive, exposed-path and successful-socket evidence also FAIL despite clean post-state |
| Restored actual components omitted | G3 PASS | Schema FAIL; changed restore OCI/file/embedded/version/commit/arch identity FAIL through reused G1 |
| Component artifact-type field absent from required schema | Assertion failed | Typed OCI/file branches required; fictitious OCI on ordinary file FAIL |
| Required artifact set, network policy and clean-template catalog absent | Assertion failed | Required and evaluated, with immutable minimum obligations |
| Snapshot source execution/kind/request/state domains absent | Assertion failed | Required and compared; same-execution restore and approved base-only template are distinct |
| Restore mode/execution/request/actual components absent | Assertion failed | Required and compared; mutable cross-execution state reuse FAIL |

New positive and negative cases also prove plain-file missing-hash BLOCKED,
post-restore deny_all checks, complete socket-ABI coverage, clean-template
approval/content binding, fresh execution/request/sandbox identities, rejection
of dirty templates, and preserved unrelated background change handling.
All values and observations are synthetic; no new execution interface exists.

Cumulative used budgets: original repair 2 plus authorized correction 1 = 3;
original targeted 3 plus additional 2 = 5; original full suites 2 plus additional
0 = 2; exact baseline comparison 1/1; branches 1; candidate paths 10. None of
the original failures or used budgets were reset. No dependencies were installed,
no global PATH, umask, directory permissions or system environment was repaired,
and no test was skipped or weakened. The additional full-suite allowance remains
unused because its environment precondition is blocked, not because of a pass.

### Final targeted raw output and exit

```text
........................................................................ [ 67%]
...................................                                      [100%]
107 passed in 6.40s
```

`exit_code=0`; stderr is the empty string; `timeout=false`.
Full protected receipt with exact commands, original stdout/stderr and exits:

```json
{
  "status": "PASS",
  "preflight": {
    "process_authority_result": {
      "status": "PASS",
      "authority_path": "config/process_authority_v1.yaml",
      "module_id": "process-authority",
      "module_version": "2.3.0",
      "public_interface_id": "process-authority-api",
      "public_interface_version": "2.1.0",
      "current_task_input_mode": "explicit_manifest_change_plan_pair",
      "implicit_repository_index_allowed": false,
      "legacy_authority": false,
      "replay_result": {
        "status": "PASS",
        "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
        "pair_count": 108,
        "authority": false,
        "replay_only": true,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "production_deployment": false,
      "cleanup_execution": false,
      "reasons": []
    },
    "manifest_result": {
      "status": "PASS",
      "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "policy_path": "policy/repo_write_policy.yaml",
      "reasons": [],
      "autonomy_policy_path": "policy/autonomy_policy.yaml"
    },
    "pair_binding_result": {
      "status": "PASS",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "binding_mode": "explicit_manifest_change_plan_pair",
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "reasons": []
    },
    "change_plan_result": {
      "status": "PASS",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "reasons": []
    },
    "replay_execution_requested": false,
    "validation_to_dispatch_inputs_equal": true
  },
  "input_sha256_before": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "a3aca219d95de9d9fa53840a4d6e9d102a41a9d6d5d7a613c4606f8a2ac51ca7",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "input_sha256_after": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "a3aca219d95de9d9fa53840a4d6e9d102a41a9d6d5d7a613c4606f8a2ac51ca7",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0"
  },
  "command_results": [
    {
      "name": "python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 0,
      "stdout": "........................................................................ [ 67%]\n...................................                                      [100%]\n107 passed in 6.40s\n",
      "stderr": ""
    },
    {
      "name": "ruff check tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 0,
      "stdout": "All checks passed!\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_active_gates tests/fixtures/manifest_validation/strict_active_gates_v1.yaml",
      "exit_code": 0,
      "stdout": "{\n  \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n  \"reasons\": [],\n  \"results\": [\n    {\n      \"autonomy_policy_path\": \"policy/autonomy_policy.yaml\",\n      \"kind\": \"task_manifest\",\n      \"manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n      \"policy_path\": \"policy/repo_write_policy.yaml\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"change_plan_path\": \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n      \"kind\": \"change_plan\",\n      \"reasons\": [],\n      \"status\": \"PASS\",\n      \"task_manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\"\n    },\n    {\n      \"alignment_gate_enabled\": false,\n      \"checked\": [],\n      \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n      \"kind\": \"alignment_gate\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    }\n  ],\n  \"status\": \"PASS\"\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_process_authority config/process_authority_v1.yaml",
      "exit_code": 0,
      "stdout": "{\n  \"authority_path\": \"config/process_authority_v1.yaml\",\n  \"cleanup_execution\": false,\n  \"current_task_input_mode\": \"explicit_manifest_change_plan_pair\",\n  \"executes_target_repo_mutation\": false,\n  \"implicit_repository_index_allowed\": false,\n  \"legacy_authority\": false,\n  \"module_id\": \"process-authority\",\n  \"module_version\": \"2.3.0\",\n  \"production_deployment\": false,\n  \"public_interface_id\": \"process-authority-api\",\n  \"public_interface_version\": \"2.1.0\",\n  \"reasons\": [],\n  \"replay_result\": {\n    \"authority\": false,\n    \"executes_target_repo_mutation\": false,\n    \"pair_count\": 108,\n    \"reasons\": [],\n    \"replay_only\": true,\n    \"snapshot_path\": \"/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml\",\n    \"status\": \"PASS\"\n  },\n  \"status\": \"PASS\",\n  \"writes_target_repo\": false\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_module_registry config/module_registry_v1.yaml --require-current-authority",
      "exit_code": 0,
      "stdout": "{\n  \"compatibility_adapter\": {\n    \"applied\": false,\n    \"authority\": false,\n    \"cache_registry\": false,\n    \"caller_boundary\": \"registry_loader_and_validator_entrypoints_only\",\n    \"current_formal_registry_owner\": \"config/module_registry_v1.yaml\",\n    \"generated_projection\": false,\n    \"mapping_owner_path\": \"docs/tool_system_module_registry_contract_v1.md\",\n    \"persistence\": \"none\",\n    \"persistent_projection\": false,\n    \"registry_files_read\": [\n      \"config/module_registry_v1.yaml\"\n    ],\n    \"second_registry_authority\": false,\n    \"second_schema_authority\": false,\n    \"serializes_projection\": false,\n    \"translation_boundary\": \"memory_only\"\n  },\n  \"contract_reference_count\": 253,\n  \"current_registry_authority\": true,\n  \"declared_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"execution_order\": [\n    \"agent-worker-runtime\",\n    \"blueprint-compiler\",\n    \"development-loop\",\n    \"durable-orchestrator\",\n    \"local-git\",\n    \"manifest-validation\",\n    \"architecture-registry\",\n    \"process-authority\",\n    \"ai-worker-runtime\",\n    \"adaptive-model-portfolio-and-economics\",\n    \"release-governance\",\n    \"operational-observability\",\n    \"record-retention\",\n    \"repository-context\",\n    \"repository-controller\",\n    \"cleanup-planner\",\n    \"state-migration\",\n    \"recovery-planning\",\n    \"subscription-capacity\",\n    \"production-readiness\",\n    \"target-repo-adapter\",\n    \"task-planner\",\n    \"role-runtime\",\n    \"worker-adapter\",\n    \"task-runner\",\n    \"cli-frontend\"\n  ],\n  \"external_provider_count\": 0,\n  \"module_count\": 26,\n  \"observed_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"owned_path_count\": 130,\n  \"reasons\": [],\n  \"registry_input_mode\": \"current_module_registry\",\n  \"registry_path\": \"config/module_registry_v1.yaml\",\n  \"required_owned_path_count\": 124,\n  \"status\": \"PASS\",\n  \"validation_scope\": \"tool_system_current_module_registry\"\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_repo_manifest REPO_MANIFEST.md",
      "exit_code": 0,
      "stdout": "{\n  \"cleanup_authorized\": false,\n  \"executes_target_repo_mutation\": false,\n  \"formal_execution_order\": [\n    \"docs/tool_system_global_development_principles_v1.md\",\n    \".gitignore\",\n    \"blueprint/schema/tool_system_blueprint.schema.json\",\n    \"pyproject.toml\",\n    \"blueprint/tool_system_v0.yaml\",\n    \"config/module_registry_schema_v1.json\",\n    \"config/module_registry_v1.yaml\",\n    \"docs/agent_role_taxonomy_v1.md\",\n    \"docs/model_provider_portfolio_and_economics_contract_v1.md\",\n    \"docs/operator_runbook_and_deprecation_policy_v1.md\",\n    \"docs/tool_system_module_registry_contract_v1.md\",\n    \"docs/tool_system_project_state_v1.yaml\",\n    \"harness/task_manifest.schema.json\",\n    \"policy/autonomy_policy.yaml\",\n    \"tests/fixtures/p14h/python_cli/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/python_cli/STATUS.md\",\n    \"tests/fixtures/p14h/python_cli/blueprint.yaml\",\n    \"tests/fixtures/p14h/typescript_package/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/typescript_package/STATUS.md\",\n    \"tests/fixtures/p14h/typescript_package/blueprint.yaml\",\n    \"tests/test_product_objective_alignment.py\",\n    \"tests/test_ts_b02a_core_local_os_isolation_backend_feasibility.py\",\n    \"config/process_authority_schema_v1.json\",\n    \"config/process_authority_v1.yaml\",\n    \"docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md\",\n    \"docs/modules/agent-worker-runtime-contract-v1.md\",\n    \"docs/modules/ai-worker-runtime-contract-v1.md\",\n    \"docs/modules/architecture-registry-contract-v1.md\",\n    \"docs/modules/blueprint-compiler-contract-v1.md\",\n    \"docs/modules/cleanup-planner-contract-v1.md\",\n    \"docs/modules/cli-frontend-contract-v1.md\",\n    \"docs/modules/development-loop-contract-v1.md\",\n    \"docs/modules/durable-orchestrator-contract-v1.md\",\n    \"docs/modules/local-git-contract-v1.md\",\n    \"docs/modules/manifest-validation-contract-v1.md\",\n    \"docs/modules/operational-observability-contract-v1.md\",\n    \"docs/modules/process-authority-contract-v1.md\",\n    \"docs/modules/production-readiness-contract-v1.md\",\n    \"docs/modules/record-retention-contract-v1.md\",\n    \"docs/modules/recovery-planning-contract-v1.md\",\n    \"docs/modules/release-governance-contract-v1.md\",\n    \"docs/modules/repository-context-contract-v1.md\",\n    \"docs/modules/repository-controller-contract-v1.md\",\n    \"docs/modules/role-runtime-contract-v1.md\",\n    \"docs/modules/state-migration-contract-v1.md\",\n    \"docs/modules/subscription-capacity-contract-v1.md\",\n    \"docs/modules/target-repo-adapter-contract-v1.md\",\n    \"docs/modules/task-planner-contract-v1.md\",\n    \"docs/modules/task-runner-contract-v1.md\",\n    \"docs/modules/worker-adapter-contract-v1.md\",\n    \"config/p15c_execution_packet_freeze_v1.yaml\",\n    \"config/p15d_failure_economics_corpus_prerequisite_v1.yaml\",\n    \"tests/test_p16a_sustainable_operations_specification.py\",\n    \"tests/test_phase_alignment.py\",\n    \"policy/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/src/calculator.py\",\n    \"tests/fixtures/p14h/typescript_package/package.json\",\n    \"tests/fixtures/p14h/typescript_package/src/index.ts\",\n    \"tests/fixtures/p14h/typescript_package/src/legacy.ts\",\n    \"tests/test_p14h_multi_stack_e2e.py\",\n    \"REPO_MANIFEST.md\",\n    \"config/replay_snapshot_v1.yaml\",\n    \"examples/requirements/tool_system_p7d.yaml\",\n    \"examples/task_graphs/tool_system_p7a_task_graph.yaml\",\n    \"src/tool_system/__init__.py\",\n    \"src/tool_system/agent_worker/__init__.py\",\n    \"src/tool_system/agent_worker/interface.py\",\n    \"src/tool_system/agent_worker/process_runtime.py\",\n    \"src/tool_system/ai_worker/__init__.py\",\n    \"src/tool_system/ai_worker/contract.py\",\n    \"src/tool_system/ai_worker/fixture_provider.py\",\n    \"src/tool_system/ai_worker/live_evidence.py\",\n    \"src/tool_system/ai_worker/live_provider.py\",\n    \"src/tool_system/architecture/__init__.py\",\n    \"src/tool_system/architecture/module_registry.py\",\n    \"src/tool_system/architecture/repo_manifest.py\",\n    \"src/tool_system/blueprint_compiler/__init__.py\",\n    \"src/tool_system/blueprint_compiler/compiler.py\",\n    \"src/tool_system/cleanup/__init__.py\",\n    \"src/tool_system/cleanup/residue_plan.py\",\n    \"src/tool_system/cli/__init__.py\",\n    \"src/tool_system/cli/cleanup_plan.py\",\n    \"src/tool_system/cli/controller_run.py\",\n    \"src/tool_system/cli/controller_self_check.py\",\n    \"src/tool_system/cli/evaluate_github_state.py\",\n    \"src/tool_system/cli/evaluate_repo_write.py\",\n    \"src/tool_system/cli/execute_change_plan.py\",\n    \"src/tool_system/cli/main.py\",\n    \"src/tool_system/cli/observe_main_ci.py\",\n    \"src/tool_system/cli/plan_requirement.py\",\n    \"src/tool_system/cli/plan_task_graph.py\",\n    \"src/tool_system/cli/run_batch.py\",\n    \"src/tool_system/cli/run_role_graph.py\",\n    \"src/tool_system/cli/run_stage.py\",\n    \"src/tool_system/cli/run_task.py\",\n    \"src/tool_system/cli/run_task_graph.py\",\n    \"src/tool_system/cli/target_repo_dry_run.py\",\n    \"src/tool_system/cli/target_repo_pr_plan_preview.py\",\n    \"src/tool_system/cli/validate_active_gates.py\",\n    \"src/tool_system/cli/validate_alignment_gate.py\",\n    \"src/tool_system/cli/validate_change_plan.py\",\n    \"src/tool_system/cli/validate_module_registry.py\",\n    \"src/tool_system/cli/validate_process_authority.py\",\n    \"src/tool_system/cli/validate_repo_manifest.py\",\n    \"src/tool_system/cli/validate_task_manifest.py\",\n    \"src/tool_system/development_loop/__init__.py\",\n    \"src/tool_system/gate/README.md\",\n    \"src/tool_system/gate/__init__.py\",\n    \"src/tool_system/gate/alignment_gate.py\",\n    \"src/tool_system/gate/change_plan.py\",\n    \"src/tool_system/gate/command_runner.py\",\n    \"src/tool_system/gate/test_gate.py\",\n    \"src/tool_system/local_git/__init__.py\",\n    \"src/tool_system/manifest/__init__.py\",\n    \"src/tool_system/manifest/task_manifest.py\",\n    \"src/tool_system/orchestrator/__init__.py\",\n    \"src/tool_system/planner/__init__.py\",\n    \"src/tool_system/planner/requirement_graph.py\",\n    \"src/tool_system/planner/task_graph.py\",\n    \"src/tool_system/policy/__init__.py\",\n    \"src/tool_system/policy/autonomy_policy.py\",\n    \"src/tool_system/policy/repo_write_policy.py\",\n    \"src/tool_system/process_authority/__init__.py\",\n    \"src/tool_system/process_authority/contract.py\",\n    \"src/tool_system/provider_portfolio/__init__.py\",\n    \"src/tool_system/provider_portfolio/fixtures.py\",\n    \"src/tool_system/repo_controller/__init__.py\",\n    \"src/tool_system/repo_controller/actions.py\",\n    \"src/tool_system/repo_controller/artifact.py\",\n    \"src/tool_system/repo_controller/audit_log.py\",\n    \"src/tool_system/repo_controller/controller.py\",\n    \"src/tool_system/repo_controller/controller_run.py\",\n    \"src/tool_system/repo_controller/github_state.py\",\n    \"src/tool_system/repo_controller/live_github_collector.py\",\n    \"src/tool_system/repo_controller/main_ci.py\",\n    \"src/tool_system/repo_controller/self_check.py\",\n    \"src/tool_system/repository_context/__init__.py\",\n    \"src/tool_system/repository_context/builder.py\",\n    \"src/tool_system/runner/active_gate_resolver.py\",\n    \"src/tool_system/runner/stage_runner.py\",\n    \"src/tool_system/runner/task_graph_runner.py\",\n    \"src/tool_system/runtime/__init__.py\",\n    \"src/tool_system/runtime/audit_bundle.py\",\n    \"src/tool_system/runtime/role_runtime.py\",\n    \"src/tool_system/runtime/transition_gate.py\",\n    \"src/tool_system/target_repo/__init__.py\",\n    \"src/tool_system/target_repo/dry_run_adapter.py\",\n    \"src/tool_system/target_repo/execution_approval.py\",\n    \"src/tool_system/target_repo/execution_state_snapshot.py\",\n    \"src/tool_system/target_repo/mutation_command_packet.py\",\n    \"src/tool_system/target_repo/p4c_preview_module.py\",\n    \"src/tool_system/target_repo/p4d_precheck.py\",\n    \"src/tool_system/target_repo/p5h_record.py\",\n    \"src/tool_system/target_repo/p5i_bundle.py\",\n    \"src/tool_system/target_repo/pr_plan_preview.py\",\n    \"src/tool_system/target_repo/state_collector.py\",\n    \"src/tool_system/target_repo/write_intent_record.py\",\n    \"src/tool_system/target_repo/write_packet.py\",\n    \"src/tool_system/worker_adapter/__init__.py\",\n    \"src/tool_system/worker_adapter/policy_gate.py\",\n    \"src/tool_system/development_loop/loop.py\",\n    \"src/tool_system/orchestrator/durable.py\",\n    \"src/tool_system/local_git/orchestrator.py\",\n    \"src/tool_system/production_readiness/__init__.py\",\n    \"src/tool_system/production_readiness/policy.py\",\n    \"src/tool_system/release_governance/__init__.py\",\n    \"src/tool_system/release_governance/policy.py\",\n    \"harness/cubesandbox_backend_acceptance_v1.schema.json\",\n    \"src/tool_system/runner/task_runner.py\",\n    \"src/tool_system/worker_adapter/contract.py\",\n    \"src/tool_system/worker_adapter/orchestration.py\",\n    \"examples/operator_config/tool_system_settings.example.toml\",\n    \"src/tool_system/ai_worker/p15c_controls.py\",\n    \"tests/test_p15c_execution_packet_freeze.py\",\n    \"tests/test_p15d_failure_economics_corpus_prerequisite.py\",\n    \"tests/fixtures/target_repo/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/tests/calculator_spec.py\",\n    \"tests/fixtures/p14h/typescript_package/tests/index.test.ts\",\n    \".github/workflows/tool-system-ci.yml\",\n    \"AGENTS.md\",\n    \"README.md\",\n    \"docs/process_authority_contract_v1.md\",\n    \"examples/batches/tool_system_batch_runner.yaml\",\n    \"examples/batches/tool_system_resolved_batch.yaml\",\n    \"examples/cleanup/tool_system_residue_state.yaml\",\n    \"examples/gate_decisions/pass.yaml\",\n    \"examples/github_states/tool_system_p3b_pass.yaml\",\n    \"examples/repo_write_decisions/tool_system_p3_pass.yaml\",\n    \"tests/fixtures/p11_worker_fixture.py\",\n    \"tests/test_active_gate_resolver.py\",\n    \"tests/test_active_gates.py\",\n    \"tests/test_agent_role_taxonomy.py\",\n    \"tests/test_agent_worker_interface.py\",\n    \"tests/test_ai_worker_contract.py\",\n    \"tests/test_ai_worker_fixture_provider.py\",\n    \"tests/test_ai_worker_live_provider.py\",\n    \"tests/test_alignment_gate.py\",\n    \"tests/test_audit_bundle.py\",\n    \"tests/test_blueprint_compiler.py\",\n    \"tests/test_change_plan_gate.py\",\n    \"tests/test_change_plan_scope_extra.py\",\n    \"tests/test_cleanup_plan.py\",\n    \"tests/test_command_runner.py\",\n    \"tests/test_controller_actions.py\",\n    \"tests/test_controller_run.py\",\n    \"tests/test_controller_self_check.py\",\n    \"tests/test_development_loop.py\",\n    \"tests/test_durable_orchestrator_recovery.py\",\n    \"tests/test_durable_orchestrator_side_effects.py\",\n    \"tests/test_durable_orchestrator_state.py\",\n    \"tests/test_execution_approval.py\",\n    \"tests/test_execution_state_snapshot.py\",\n    \"tests/test_final_record.py\",\n    \"tests/test_github_state_adapter.py\",\n    \"tests/test_global_principles.py\",\n    \"tests/test_live_github_collector.py\",\n    \"tests/test_local_git_orchestrator.py\",\n    \"tests/test_main_ci.py\",\n    \"tests/test_milestone_module_invariant.py\",\n    \"tests/test_module_contracts.py\",\n    \"tests/test_module_import_graph.py\",\n    \"tests/test_module_registry.py\",\n    \"tests/test_multi_task.py\",\n    \"tests/test_mutation_command_packet.py\",\n    \"tests/test_p10r_a_machine_policy_enforcement.py\",\n    \"tests/test_p13_integrated_security_reliability.py\",\n    \"tests/test_p14_phase_entry_contract.py\",\n    \"tests/test_p14c_execution_contract.py\",\n    \"tests/test_p4d_precheck.py\",\n    \"tests/test_process_authority.py\",\n    \"tests/test_process_worker_runtime_adversarial.py\",\n    \"tests/test_process_worker_runtime_execution.py\",\n    \"tests/test_process_worker_runtime_preflight.py\",\n    \"tests/test_provider_portfolio_fixtures.py\",\n    \"tests/test_repo_controller.py\",\n    \"tests/test_repo_manifest.py\",\n    \"tests/test_repository_context_builder.py\",\n    \"tests/test_requirement_graph.py\",\n    \"tests/test_role_runtime.py\",\n    \"tests/test_role_transition_gate.py\",\n    \"tests/test_root_cli.py\",\n    \"tests/test_runtime_audit_bundle.py\",\n    \"tests/test_stage_runner.py\",\n    \"tests/test_state_collector.py\",\n    \"tests/test_target_repo_dry_run.py\",\n    \"tests/test_target_repo_pr_plan_preview.py\",\n    \"tests/test_task_graph.py\",\n    \"tests/test_task_graph_runner.py\",\n    \"tests/test_task_manifest_policy.py\",\n    \"tests/test_worker_adapter_contract.py\",\n    \"tests/test_worker_adapter_orchestration.py\",\n    \"tests/test_worker_adapter_policy_gate.py\",\n    \"tests/test_write_intent.py\",\n    \"tests/test_write_packet.py\",\n    \"src/tool_system/ai_worker/runtime.py\",\n    \"src/tool_system/provider_portfolio/failure_control.py\",\n    \"tests/test_target_identity_decoupling.py\",\n    \"tests/test_durable_orchestrator_reliability.py\",\n    \"tests/test_production_readiness.py\",\n    \"src/tool_system/operational_observability/__init__.py\",\n    \"src/tool_system/state_migration/__init__.py\",\n    \"src/tool_system/subscription_capacity/__init__.py\",\n    \"src/tool_system/operational_observability/policy.py\",\n    \"src/tool_system/state_migration/planner.py\",\n    \"src/tool_system/subscription_capacity/policy.py\",\n    \"tests/test_release_governance.py\",\n    \"tests/cubesandbox_contract_oracle.py\",\n    \"tests/fixtures/cubesandbox_backend_acceptance_v1.json\",\n    \"tests/test_task_runner.py\",\n    \"examples/operator_config/tool_system_credentials.example.toml\",\n    \"src/tool_system/ai_worker/p15c_benchmark.py\",\n    \"tests/test_ai_worker_p15c_controls.py\",\n    \"tests/fixtures/target_repo/task_manifest.yaml\",\n    \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n    \"tests/test_central_governance_consumption.py\",\n    \"tests/test_model_provider_portfolio_contract.py\",\n    \"src/tool_system/process_authority/live_provider_approval.py\",\n    \"src/tool_system/provider_portfolio/provider_mode.py\",\n    \"tests/test_ai_worker_provider_mode.py\",\n    \"tests/test_provider_portfolio_failure_control.py\",\n    \"src/tool_system/record_retention/__init__.py\",\n    \"src/tool_system/recovery_planning/__init__.py\",\n    \"src/tool_system/record_retention/policy.py\",\n    \"tests/test_operational_observability.py\",\n    \"src/tool_system/recovery_planning/planner.py\",\n    \"tests/test_state_migration.py\",\n    \"tests/test_subscription_capacity.py\",\n    \"tests/test_cubesandbox_backend_acceptance_contract.py\",\n    \"src/tool_system/ai_worker/p15c_entry.py\",\n    \"tests/test_ai_worker_p15c_benchmark.py\",\n    \"tests/test_target_repo_dry_run_probe.py\",\n    \"tests/test_p14c_live_issuer.py\",\n    \"tests/test_provider_portfolio_provider_mode.py\",\n    \"tests/test_record_retention.py\",\n    \"tests/test_recovery_planning.py\",\n    \"tests/test_ai_worker_p15c_entry.py\",\n    \"tests/test_p15c_local_operator_config.py\"\n  ],\n  \"formal_file_count\": 299,\n  \"formal_path_count\": 299,\n  \"formal_set_count\": 0,\n  \"legacy_path_count\": 543,\n  \"legacy_set_count\": 6,\n  \"manifest_path\": \"REPO_MANIFEST.md\",\n  \"parser_mode\": \"exact_formal_files\",\n  \"reasons\": [],\n  \"retained_inputs_are_current_authority\": false,\n  \"status\": \"PASS\",\n  \"tracked_path_count\": 842,\n  \"unclassified_path_count\": 0,\n  \"writes_target_repo\": false\n}\n",
      "stderr": ""
    },
    {
      "name": "git diff --check",
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    }
  ],
  "subprocess_call_count": 7,
  "reasons": []
}
```

### Current full-suite disposition (no command launched)

```json
{
  "command": "python -B -m pytest -q -p no:cacheprovider",
  "status": "NOT_EXECUTED_ENVIRONMENT_BLOCKED",
  "executed": false,
  "stdout": "",
  "stderr": "",
  "exit_code": null,
  "timeout": null,
  "reasons": [
    "node unavailable in the unchanged validation PATH",
    "the exact-baseline targeted comparison still rejects group-writable fixture directories"
  ],
  "additional_full_suite_runs_used": 0,
  "cumulative_full_suite_runs_used": 2
}
```

A nonexistent run has no exit code or timeout result. Overall full-suite
acceptance remains NOT_PASSED. The latest actual full run is the retained
historical 965 passed / 3 failed result below, before this review correction;
it is not a full-suite validation of the final corrected candidate.

### Final source SHA-256 inventory

The final evidence file itself is excluded to avoid self-referential hashes.
Its final digest and complete staged-patch digest are returned separately.

```json
{
  "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "81bfa895e1b45b9c10dee644753df0b2d6470b95e96ef1800ba82e43ced9bb03",
  "harness/cubesandbox_backend_acceptance_v1.schema.json": "84960537f2172d6246635c732fad0b03d95b47dec1a44cc529908ff88f6e2170",
  "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "3ad67cb076e872db80086669acb85c5c4e1ef1da201a660b3bf204658877790a",
  "tests/cubesandbox_contract_oracle.py": "11fa82b23a7a7d814a6a15834ab13b80327b095b2db13a74be9033021a7db0e5",
  "tests/test_cubesandbox_backend_acceptance_contract.py": "91e810c53f30b7c03c49962f99c596aaf8cebebdf44e9456390f0ec5130e6df3",
  "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "0f7d0cd223e0245cc3b372a9ce388e71a0b78a6095b49232c75c305fa87d95d0",
  "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "a8f311d1a03a8ec36629457ee65096e403745d1573c8e6d48f66a5bd6c9259ce",
  "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
  "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
}
```

### Remaining prerequisites and source-only stop

The four requested specification corrections are implemented and covered by
synthetic regressions. Independent re-review and a passing full-suite run in an
already approved environment remain outstanding. Node and the unchanged
directory-mode prerequisites remain unsatisfied in this environment.
Lifecycle-manager ARM64 OCI digest, the complete approved executable/file
closure, real deny_all topology/ARM64 ABI and enforcement hashes, real observer
implementation and visibility, source-to-artifact chain, clean-template
approval if used, and exact separately approved host execution package remain
unproved. Candidate digests and enforcement hashes remain null where unfrozen.
No published provenance/SBOM attestation is invented or credited.

```text
SOURCE_AND_CONTRACT_ONLY=true
DGX_EXECUTION=false
HOST_INSTALLATION=false
NETWORK_MUTATION=false
SYSTEMD_MUTATION=false
CANONICAL_MAIN_WRITE=false
REAL_BACKEND_ACCEPTANCE_EXECUTED=false
REAL_BACKEND_ACCEPTANCE_AUTHORIZED=false
G1_SPEC_COMPLETE=true
G2_SPEC_COMPLETE=true
G3_SPEC_COMPLETE=true
G4_SPEC_COMPLETE=true
DEPENDENCY_INSTALLATION=false
```

Stop at the local source-review boundary. No commit, push, PR, merge,
CubeSandbox operation or host probe is authorized by these results.

### Retained historical full-suite raw receipts

These original command receipts were read from the retained tool results, not
reconstructed from the summary. Their failures remain preserved unchanged.

Original full suite 1:

```json
{
  "input_sha256": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "422264abf74f1669fb68ff307680ca08f589910e296b681a866c55cea465379a",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "6befe3892d5464449b87a40c0895d95082e4a5a85f702a7654b4957474084ce6"
  },
  "command_result": {
    "name": "python -B -m pytest -q -p no:cacheprovider",
    "exit_code": 1,
    "stdout": "........................................................................ [  7%]\n........................................................................ [ 14%]\n........................................................................ [ 22%]\n........................................................................ [ 29%]\n............F.....F..................................................... [ 37%]\n........................................................................ [ 44%]\n........................................................................ [ 52%]\n........................F............................................... [ 59%]\n........................................................................ [ 66%]\n........................................................................ [ 74%]\n.......F................................................................ [ 81%]\n........................................................................ [ 89%]\n........................................................................ [ 96%]\n................................                                         [100%]\n=================================== FAILURES ===================================\n___________ test_text_and_json_resource_bounds_fail_before_mutation ____________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-30/test_text_and_json_resource_bo0')\n\n    def test_text_and_json_resource_bounds_fail_before_mutation(tmp_path: Path) -> None:\n        text_store = _store(tmp_path, max_text_bytes=8)\n        with pytest.raises(ValueError, match=\"max_text_bytes\"):\n            text_store.create_run(\n                \"run-too-long\", blueprint_ref=\"bp\", manifest_ref=\"manifest\"\n            )\n        assert text_store.get_run(\"missing\") is None\n    \n        record_path = tmp_path / \"record\"\n        record_path.mkdir()\n>       record_store = _store(record_path, max_record_bytes=16)\n                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\ntests/test_durable_orchestrator_reliability.py:154: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <tool_system.orchestrator.durable.DurableOrchestratorStore object at 0xefdc34ad1950>\ndatabase_path = PosixPath('/tmp/pytest-of-rich/pytest-30/test_text_and_json_resource_bo0/record/state.sqlite3')\nforbidden_roots = (PosixPath('/home/rich/projects/tool-system'),)\nclock = <built-in function time>, busy_timeout_ms = 5000, max_text_bytes = 4096\nmax_record_bytes = 16\n\n    def __init__(\n        self,\n        database_path: str | Path,\n        *,\n        forbidden_roots: tuple[str | Path, ...],\n        clock: Callable[[], float] = time.time,\n        busy_timeout_ms: int = 5_000,\n        max_text_bytes: int = 4_096,\n        max_record_bytes: int = 1024 * 1024,\n    ) -> None:\n        if not forbidden_roots:\n            raise ValueError(\"forbidden_roots must be non-empty\")\n        raw_path = Path(database_path)\n        if raw_path.exists() and raw_path.is_symlink():\n            raise ValueError(\"database_path must not be a symlink\")\n        parent = raw_path.parent.resolve(strict=True)\n        if raw_path.parent.is_symlink():\n            raise ValueError(\"database parent must not be a symlink\")\n        parent_stat = parent.lstat()\n        if not stat.S_ISDIR(parent_stat.st_mode):\n            raise ValueError(\"database parent must be a directory\")\n        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):\n>           raise ValueError(\"database parent must not be group/world-writable\")\nE           ValueError: database parent must not be group/world-writable\n\nsrc/tool_system/orchestrator/durable.py:128: ValueError\n____________ test_database_parent_identity_substitution_is_detected ____________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-30/test_database_parent_identity_0')\n\n    def test_database_parent_identity_substitution_is_detected(tmp_path: Path) -> None:\n        parent = tmp_path / \"state\"\n        parent.mkdir()\n>       store = _store(parent)\n                ^^^^^^^^^^^^^^\n\ntests/test_durable_orchestrator_reliability.py:305: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <tool_system.orchestrator.durable.DurableOrchestratorStore object at 0xefdc34ad25d0>\ndatabase_path = PosixPath('/tmp/pytest-of-rich/pytest-30/test_database_parent_identity_0/state/state.sqlite3')\nforbidden_roots = (PosixPath('/home/rich/projects/tool-system'),)\nclock = <built-in function time>, busy_timeout_ms = 5000, max_text_bytes = 4096\nmax_record_bytes = 1048576\n\n    def __init__(\n        self,\n        database_path: str | Path,\n        *,\n        forbidden_roots: tuple[str | Path, ...],\n        clock: Callable[[], float] = time.time,\n        busy_timeout_ms: int = 5_000,\n        max_text_bytes: int = 4_096,\n        max_record_bytes: int = 1024 * 1024,\n    ) -> None:\n        if not forbidden_roots:\n            raise ValueError(\"forbidden_roots must be non-empty\")\n        raw_path = Path(database_path)\n        if raw_path.exists() and raw_path.is_symlink():\n            raise ValueError(\"database_path must not be a symlink\")\n        parent = raw_path.parent.resolve(strict=True)\n        if raw_path.parent.is_symlink():\n            raise ValueError(\"database parent must not be a symlink\")\n        parent_stat = parent.lstat()\n        if not stat.S_ISDIR(parent_stat.st_mode):\n            raise ValueError(\"database parent must be a directory\")\n        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):\n>           raise ValueError(\"database parent must not be group/world-writable\")\nE           ValueError: database parent must not be group/world-writable\n\nsrc/tool_system/orchestrator/durable.py:128: ValueError\n_______ test_typescript_language_neutral_flow_records_add_modify_delete ________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-30/test_typescript_language_neutr0')\n\n    def test_typescript_language_neutral_flow_records_add_modify_delete(\n        tmp_path: Path,\n    ) -> None:\n        def worker(_: Mapping[str, object]) -> dict[str, object]:\n            return {\n                \"operations\": [\n                    {\n                        \"op\": \"add\",\n                        \"path\": \"src/format.ts\",\n                        \"expected_sha256\": None,\n                        \"content\": \"export const format = (value) => `value:${value}`;\\n\",\n                    },\n                    {\n                        \"op\": \"replace\",\n                        \"path\": \"src/index.ts\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"src/index.ts\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                        \"content\": 'import { format } from \"./format.js\";\\n\\nexport const display = (value) => format(value);\\n',\n                    },\n                    {\n                        \"op\": \"delete\",\n                        \"path\": \"src/legacy.ts\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"src/legacy.ts\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                    },\n                    {\n                        \"op\": \"replace\",\n                        \"path\": \"STATUS.md\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"STATUS.md\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                        \"content\": \"implementation: accepted\\n\",\n                    },\n                ]\n            }\n    \n        acceptance = (\n            \"formatter is exported\",\n            \"legacy source is removed\",\n            \"status converges\",\n        )\n    \n        def validator(files: Mapping[str, str]) -> dict[str, object]:\n            syntax = all(\n                subprocess.run(\n                    [\"node\", \"--input-type=module\", \"--check\", \"-\"],\n                    input=files[path],\n                    text=True,\n                    capture_output=True,\n                    check=False,\n                ).returncode\n                == 0\n                for path in (\"src/format.ts\", \"src/index.ts\", \"tests/index.test.ts\")\n            )\n            passed = (\n                syntax and \"format(value)\" in files[\"src/index.ts\"],\n                \"src/legacy.ts\" not in files,\n                files[\"STATUS.md\"] == \"implementation: accepted\\n\",\n            )\n            satisfied = [\n                item\n                for item, ok in zip(acceptance, passed, strict=True)\n                if ok\n            ]\n            return {\n                \"validation_results\": {\n                    \"fixture-stack\": {\n                        \"status\": \"PASS\" if len(satisfied) == 3 else \"BLOCK\",\n                        \"diagnostic\": None,\n                    }\n                },\n                \"satisfied_acceptance_items\": satisfied,\n            }\n    \n>       root, head, result, _ = _run_compiled_stack(\n            tmp_path=tmp_path,\n            name=\"typescript_package\",\n            milestone_id=\"TYPESCRIPT_PACKAGE\",\n            terms=(\"display\", \"legacy\", \"formatter\"),\n            worker=worker,\n            validator=validator,\n            run_id=\"p14h-typescript\",\n        )\n\ntests/test_p14h_multi_stack_e2e.py:362: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_p14h_multi_stack_e2e.py:166: in _run_compiled_stack\n    result = run_durable_local_git(\nsrc/tool_system/local_git/orchestrator.py:636: in run_durable_local_git\n    loop_result = run_development_loop(\nsrc/tool_system/development_loop/loop.py:433: in run_development_loop\n    validation_results, satisfied, blockers = _validation(validator(candidate), contract)\n                                                          ^^^^^^^^^^^^^^^^^^^^\nsrc/tool_system/local_git/orchestrator.py:621: in durable_validator\n    result = validator(candidate)\n             ^^^^^^^^^^^^^^^^^^^^\ntests/test_p14h_multi_stack_e2e.py:331: in validator\n    syntax = all(\n             ^^^\ntests/test_p14h_multi_stack_e2e.py:332: in <genexpr>\n    subprocess.run(\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:554: in run\n    with Popen(*popenargs, **kwargs) as process:\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1038: in __init__\n    self._execute_child(args, executable, preexec_fn, close_fds,\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <Popen: returncode: 255 args: ['node', '--input-type=module', '--check', '-']>\nargs = ['node', '--input-type=module', '--check', '-'], executable = b'node'\npreexec_fn = None, close_fds = True, pass_fds = (), cwd = None, env = None\nstartupinfo = None, creationflags = 0, shell = False, p2cread = 11\np2cwrite = 13, c2pread = 14, c2pwrite = 15, errread = 16, errwrite = 17\nrestore_signals = True, gid = None, gids = None, uid = None, umask = -1\nstart_new_session = False, process_group = -1\n\n    def _execute_child(self, args, executable, preexec_fn, close_fds,\n                       pass_fds, cwd, env,\n                       startupinfo, creationflags, shell,\n                       p2cread, p2cwrite,\n                       c2pread, c2pwrite,\n                       errread, errwrite,\n                       restore_signals,\n                       gid, gids, uid, umask,\n                       start_new_session, process_group):\n        \"\"\"Execute program (POSIX version)\"\"\"\n    \n        if isinstance(args, (str, bytes)):\n            args = [args]\n        elif isinstance(args, os.PathLike):\n            if shell:\n                raise TypeError('path-like args is not allowed when '\n                                'shell is true')\n            args = [args]\n        else:\n            args = list(args)\n    \n        if shell:\n            # On Android the default shell is at '/system/bin/sh'.\n            unix_shell = ('/system/bin/sh' if\n                      hasattr(sys, 'getandroidapilevel') else '/bin/sh')\n            args = [unix_shell, \"-c\"] + args\n            if executable:\n                args[0] = executable\n    \n        if executable is None:\n            executable = args[0]\n    \n        sys.audit(\"subprocess.Popen\", executable, args, cwd, env)\n    \n        if (_USE_POSIX_SPAWN\n                and os.path.dirname(executable)\n                and preexec_fn is None\n                and (not close_fds or _HAVE_POSIX_SPAWN_CLOSEFROM)\n                and not pass_fds\n                and cwd is None\n                and (p2cread == -1 or p2cread > 2)\n                and (c2pwrite == -1 or c2pwrite > 2)\n                and (errwrite == -1 or errwrite > 2)\n                and not start_new_session\n                and process_group == -1\n                and gid is None\n                and gids is None\n                and uid is None\n                and umask < 0):\n            self._posix_spawn(args, executable, env, restore_signals, close_fds,\n                              p2cread, p2cwrite,\n                              c2pread, c2pwrite,\n                              errread, errwrite)\n            return\n    \n        orig_executable = executable\n    \n        # For transferring possible exec failure from child to parent.\n        # Data format: \"exception name:hex errno:description\"\n        # Pickle is not used; it is complex and involves memory allocation.\n        errpipe_read, errpipe_write = os.pipe()\n        # errpipe_write must not be in the standard io 0, 1, or 2 fd range.\n        low_fds_to_close = []\n        while errpipe_write < 3:\n            low_fds_to_close.append(errpipe_write)\n            errpipe_write = os.dup(errpipe_write)\n        for low_fd in low_fds_to_close:\n            os.close(low_fd)\n        try:\n            try:\n                # We must avoid complex work that could involve\n                # malloc or free in the child process to avoid\n                # potential deadlocks, thus we do all this here.\n                # and pass it to fork_exec()\n    \n                if env is not None:\n                    env_list = []\n                    for k, v in env.items():\n                        k = os.fsencode(k)\n                        if b'=' in k:\n                            raise ValueError(\"illegal environment variable name\")\n                        env_list.append(k + b'=' + os.fsencode(v))\n                else:\n                    env_list = None  # Use execv instead of execve.\n                executable = os.fsencode(executable)\n                if os.path.dirname(executable):\n                    executable_list = (executable,)\n                else:\n                    # This matches the behavior of os._execvpe().\n                    executable_list = tuple(\n                        os.path.join(os.fsencode(dir), executable)\n                        for dir in os.get_exec_path(env))\n                fds_to_keep = set(pass_fds)\n                fds_to_keep.add(errpipe_write)\n                self.pid = _fork_exec(\n                        args, executable_list,\n                        close_fds, tuple(sorted(map(int, fds_to_keep))),\n                        cwd, env_list,\n                        p2cread, p2cwrite, c2pread, c2pwrite,\n                        errread, errwrite,\n                        errpipe_read, errpipe_write,\n                        restore_signals, start_new_session,\n                        process_group, gid, gids, uid, umask,\n                        preexec_fn)\n                self._child_created = True\n            finally:\n                # be sure the FD is closed no matter what\n                os.close(errpipe_write)\n    \n            self._close_pipe_fds(p2cread, p2cwrite,\n                                 c2pread, c2pwrite,\n                                 errread, errwrite)\n    \n            # Wait for exec to fail or succeed; possibly raising an\n            # exception (limited in size)\n            errpipe_data = bytearray()\n            while True:\n                part = os.read(errpipe_read, 50000)\n                errpipe_data += part\n                if not part or len(errpipe_data) > 50000:\n                    break\n        finally:\n            # be sure the FD is closed no matter what\n            os.close(errpipe_read)\n    \n        if errpipe_data:\n            try:\n                pid, sts = os.waitpid(self.pid, 0)\n                if pid == self.pid:\n                    self._handle_exitstatus(sts)\n                else:\n                    self.returncode = sys.maxsize\n            except ChildProcessError:\n                pass\n    \n            try:\n                exception_name, hex_errno, err_msg = (\n                        errpipe_data.split(b':', 2))\n                # The encoding here should match the encoding\n                # written in by the subprocess implementations\n                # like _posixsubprocess\n                err_msg = err_msg.decode()\n            except ValueError:\n                exception_name = b'SubprocessError'\n                hex_errno = b'0'\n                err_msg = 'Bad exception data from child: {!r}'.format(\n                              bytes(errpipe_data))\n            child_exception_type = getattr(\n                    builtins, exception_name.decode('ascii'),\n                    SubprocessError)\n            if issubclass(child_exception_type, OSError) and hex_errno:\n                errno_num = int(hex_errno, 16)\n                if err_msg == \"noexec:chdir\":\n                    err_msg = \"\"\n                    # The error must be from chdir(cwd).\n                    err_filename = cwd\n                elif err_msg == \"noexec\":\n                    err_msg = \"\"\n                    err_filename = None\n                else:\n                    err_filename = orig_executable\n                if errno_num != 0:\n                    err_msg = os.strerror(errno_num)\n                if err_filename is not None:\n>                   raise child_exception_type(errno_num, err_msg, err_filename)\nE                   FileNotFoundError: [Errno 2] No such file or directory: 'node'\n\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1989: FileNotFoundError\n_______ test_current_repository_manifest_covers_every_tracked_path_once ________\n\n    def test_current_repository_manifest_covers_every_tracked_path_once() -> None:\n        result = validate_repo_manifest(MANIFEST, ROOT)\n        parser_mode, rows, reasons = parse_manifest_formal_rows(_manifest_text())\n        legacy_rows, legacy_reasons = _table_rows(\n            _manifest_text(),\n            LEGACY_SECTION,\n            LEGACY_COLUMNS,\n        )\n        tracked = _tracked_paths(ROOT)\n        retained_paths = set().union(\n            *(\n                _expand_tracked_pattern(ROOT, row[\"path\"], tracked)\n                for row in legacy_rows\n            )\n        )\n    \n        assert result[\"status\"] == \"PASS\"\n        assert result[\"reasons\"] == []\n        assert result[\"parser_mode\"] == EXACT_FORMAL_PARSER_MODE\n        assert parser_mode == EXACT_FORMAL_PARSER_MODE\n        assert reasons == []\n        assert legacy_reasons == []\n>       assert len(rows) == 295\nE       AssertionError: assert 299 == 295\nE        +  where 299 = len([{'path': 'docs/tool_system_global_development_principles_v1.md', 'role': 'local engineering constitution', 'purpose':..., static import DAG, side-effect taxonomy, and rollback boundary.', 'owner': 'architecture_registry module', ...}, ...])\n\ntests/test_repo_manifest.py:130: AssertionError\n=========================== short test summary info ============================\nFAILED tests/test_durable_orchestrator_reliability.py::test_text_and_json_resource_bounds_fail_before_mutation\nFAILED tests/test_durable_orchestrator_reliability.py::test_database_parent_identity_substitution_is_detected\nFAILED tests/test_p14h_multi_stack_e2e.py::test_typescript_language_neutral_flow_records_add_modify_delete\nFAILED tests/test_repo_manifest.py::test_current_repository_manifest_covers_every_tracked_path_once\n4 failed, 964 passed in 72.36s (0:01:12)\n",
    "stderr": ""
  }
}
```

Original full suite 2:

```json
{
  "input_sha256": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "776d5b01bde8bf9d56fd53fd40bb70fa5b78920d453c71173a7566f558e5601a",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "6b9b644c02c9e565ba360ed8a929288bf311d30e07a2ea738da7baa083b61b00"
  },
  "command_result": {
    "name": "python -B -m pytest -q -p no:cacheprovider",
    "exit_code": 1,
    "stdout": "........................................................................ [  7%]\n........................................................................ [ 14%]\n........................................................................ [ 22%]\n........................................................................ [ 29%]\n............F.....F..................................................... [ 37%]\n........................................................................ [ 44%]\n........................................................................ [ 52%]\n........................F............................................... [ 59%]\n........................................................................ [ 66%]\n........................................................................ [ 74%]\n........................................................................ [ 81%]\n........................................................................ [ 89%]\n........................................................................ [ 96%]\n................................                                         [100%]\n=================================== FAILURES ===================================\n___________ test_text_and_json_resource_bounds_fail_before_mutation ____________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-31/test_text_and_json_resource_bo0')\n\n    def test_text_and_json_resource_bounds_fail_before_mutation(tmp_path: Path) -> None:\n        text_store = _store(tmp_path, max_text_bytes=8)\n        with pytest.raises(ValueError, match=\"max_text_bytes\"):\n            text_store.create_run(\n                \"run-too-long\", blueprint_ref=\"bp\", manifest_ref=\"manifest\"\n            )\n        assert text_store.get_run(\"missing\") is None\n    \n        record_path = tmp_path / \"record\"\n        record_path.mkdir()\n>       record_store = _store(record_path, max_record_bytes=16)\n                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\ntests/test_durable_orchestrator_reliability.py:154: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <tool_system.orchestrator.durable.DurableOrchestratorStore object at 0xf69bb7225950>\ndatabase_path = PosixPath('/tmp/pytest-of-rich/pytest-31/test_text_and_json_resource_bo0/record/state.sqlite3')\nforbidden_roots = (PosixPath('/home/rich/projects/tool-system'),)\nclock = <built-in function time>, busy_timeout_ms = 5000, max_text_bytes = 4096\nmax_record_bytes = 16\n\n    def __init__(\n        self,\n        database_path: str | Path,\n        *,\n        forbidden_roots: tuple[str | Path, ...],\n        clock: Callable[[], float] = time.time,\n        busy_timeout_ms: int = 5_000,\n        max_text_bytes: int = 4_096,\n        max_record_bytes: int = 1024 * 1024,\n    ) -> None:\n        if not forbidden_roots:\n            raise ValueError(\"forbidden_roots must be non-empty\")\n        raw_path = Path(database_path)\n        if raw_path.exists() and raw_path.is_symlink():\n            raise ValueError(\"database_path must not be a symlink\")\n        parent = raw_path.parent.resolve(strict=True)\n        if raw_path.parent.is_symlink():\n            raise ValueError(\"database parent must not be a symlink\")\n        parent_stat = parent.lstat()\n        if not stat.S_ISDIR(parent_stat.st_mode):\n            raise ValueError(\"database parent must be a directory\")\n        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):\n>           raise ValueError(\"database parent must not be group/world-writable\")\nE           ValueError: database parent must not be group/world-writable\n\nsrc/tool_system/orchestrator/durable.py:128: ValueError\n____________ test_database_parent_identity_substitution_is_detected ____________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-31/test_database_parent_identity_0')\n\n    def test_database_parent_identity_substitution_is_detected(tmp_path: Path) -> None:\n        parent = tmp_path / \"state\"\n        parent.mkdir()\n>       store = _store(parent)\n                ^^^^^^^^^^^^^^\n\ntests/test_durable_orchestrator_reliability.py:305: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_durable_orchestrator_reliability.py:80: in _store\n    return DurableOrchestratorStore(\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <tool_system.orchestrator.durable.DurableOrchestratorStore object at 0xf69bb72265d0>\ndatabase_path = PosixPath('/tmp/pytest-of-rich/pytest-31/test_database_parent_identity_0/state/state.sqlite3')\nforbidden_roots = (PosixPath('/home/rich/projects/tool-system'),)\nclock = <built-in function time>, busy_timeout_ms = 5000, max_text_bytes = 4096\nmax_record_bytes = 1048576\n\n    def __init__(\n        self,\n        database_path: str | Path,\n        *,\n        forbidden_roots: tuple[str | Path, ...],\n        clock: Callable[[], float] = time.time,\n        busy_timeout_ms: int = 5_000,\n        max_text_bytes: int = 4_096,\n        max_record_bytes: int = 1024 * 1024,\n    ) -> None:\n        if not forbidden_roots:\n            raise ValueError(\"forbidden_roots must be non-empty\")\n        raw_path = Path(database_path)\n        if raw_path.exists() and raw_path.is_symlink():\n            raise ValueError(\"database_path must not be a symlink\")\n        parent = raw_path.parent.resolve(strict=True)\n        if raw_path.parent.is_symlink():\n            raise ValueError(\"database parent must not be a symlink\")\n        parent_stat = parent.lstat()\n        if not stat.S_ISDIR(parent_stat.st_mode):\n            raise ValueError(\"database parent must be a directory\")\n        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):\n>           raise ValueError(\"database parent must not be group/world-writable\")\nE           ValueError: database parent must not be group/world-writable\n\nsrc/tool_system/orchestrator/durable.py:128: ValueError\n_______ test_typescript_language_neutral_flow_records_add_modify_delete ________\n\ntmp_path = PosixPath('/tmp/pytest-of-rich/pytest-31/test_typescript_language_neutr0')\n\n    def test_typescript_language_neutral_flow_records_add_modify_delete(\n        tmp_path: Path,\n    ) -> None:\n        def worker(_: Mapping[str, object]) -> dict[str, object]:\n            return {\n                \"operations\": [\n                    {\n                        \"op\": \"add\",\n                        \"path\": \"src/format.ts\",\n                        \"expected_sha256\": None,\n                        \"content\": \"export const format = (value) => `value:${value}`;\\n\",\n                    },\n                    {\n                        \"op\": \"replace\",\n                        \"path\": \"src/index.ts\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"src/index.ts\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                        \"content\": 'import { format } from \"./format.js\";\\n\\nexport const display = (value) => format(value);\\n',\n                    },\n                    {\n                        \"op\": \"delete\",\n                        \"path\": \"src/legacy.ts\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"src/legacy.ts\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                    },\n                    {\n                        \"op\": \"replace\",\n                        \"path\": \"STATUS.md\",\n                        \"expected_sha256\": _sha(\n                            (FIXTURES / \"typescript_package\" / \"STATUS.md\").read_text(\n                                encoding=\"utf-8\"\n                            )\n                        ),\n                        \"content\": \"implementation: accepted\\n\",\n                    },\n                ]\n            }\n    \n        acceptance = (\n            \"formatter is exported\",\n            \"legacy source is removed\",\n            \"status converges\",\n        )\n    \n        def validator(files: Mapping[str, str]) -> dict[str, object]:\n            syntax = all(\n                subprocess.run(\n                    [\"node\", \"--input-type=module\", \"--check\", \"-\"],\n                    input=files[path],\n                    text=True,\n                    capture_output=True,\n                    check=False,\n                ).returncode\n                == 0\n                for path in (\"src/format.ts\", \"src/index.ts\", \"tests/index.test.ts\")\n            )\n            passed = (\n                syntax and \"format(value)\" in files[\"src/index.ts\"],\n                \"src/legacy.ts\" not in files,\n                files[\"STATUS.md\"] == \"implementation: accepted\\n\",\n            )\n            satisfied = [\n                item\n                for item, ok in zip(acceptance, passed, strict=True)\n                if ok\n            ]\n            return {\n                \"validation_results\": {\n                    \"fixture-stack\": {\n                        \"status\": \"PASS\" if len(satisfied) == 3 else \"BLOCK\",\n                        \"diagnostic\": None,\n                    }\n                },\n                \"satisfied_acceptance_items\": satisfied,\n            }\n    \n>       root, head, result, _ = _run_compiled_stack(\n            tmp_path=tmp_path,\n            name=\"typescript_package\",\n            milestone_id=\"TYPESCRIPT_PACKAGE\",\n            terms=(\"display\", \"legacy\", \"formatter\"),\n            worker=worker,\n            validator=validator,\n            run_id=\"p14h-typescript\",\n        )\n\ntests/test_p14h_multi_stack_e2e.py:362: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \ntests/test_p14h_multi_stack_e2e.py:166: in _run_compiled_stack\n    result = run_durable_local_git(\nsrc/tool_system/local_git/orchestrator.py:636: in run_durable_local_git\n    loop_result = run_development_loop(\nsrc/tool_system/development_loop/loop.py:433: in run_development_loop\n    validation_results, satisfied, blockers = _validation(validator(candidate), contract)\n                                                          ^^^^^^^^^^^^^^^^^^^^\nsrc/tool_system/local_git/orchestrator.py:621: in durable_validator\n    result = validator(candidate)\n             ^^^^^^^^^^^^^^^^^^^^\ntests/test_p14h_multi_stack_e2e.py:331: in validator\n    syntax = all(\n             ^^^\ntests/test_p14h_multi_stack_e2e.py:332: in <genexpr>\n    subprocess.run(\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:554: in run\n    with Popen(*popenargs, **kwargs) as process:\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1038: in __init__\n    self._execute_child(args, executable, preexec_fn, close_fds,\n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = <Popen: returncode: 255 args: ['node', '--input-type=module', '--check', '-']>\nargs = ['node', '--input-type=module', '--check', '-'], executable = b'node'\npreexec_fn = None, close_fds = True, pass_fds = (), cwd = None, env = None\nstartupinfo = None, creationflags = 0, shell = False, p2cread = 11\np2cwrite = 13, c2pread = 14, c2pwrite = 15, errread = 16, errwrite = 17\nrestore_signals = True, gid = None, gids = None, uid = None, umask = -1\nstart_new_session = False, process_group = -1\n\n    def _execute_child(self, args, executable, preexec_fn, close_fds,\n                       pass_fds, cwd, env,\n                       startupinfo, creationflags, shell,\n                       p2cread, p2cwrite,\n                       c2pread, c2pwrite,\n                       errread, errwrite,\n                       restore_signals,\n                       gid, gids, uid, umask,\n                       start_new_session, process_group):\n        \"\"\"Execute program (POSIX version)\"\"\"\n    \n        if isinstance(args, (str, bytes)):\n            args = [args]\n        elif isinstance(args, os.PathLike):\n            if shell:\n                raise TypeError('path-like args is not allowed when '\n                                'shell is true')\n            args = [args]\n        else:\n            args = list(args)\n    \n        if shell:\n            # On Android the default shell is at '/system/bin/sh'.\n            unix_shell = ('/system/bin/sh' if\n                      hasattr(sys, 'getandroidapilevel') else '/bin/sh')\n            args = [unix_shell, \"-c\"] + args\n            if executable:\n                args[0] = executable\n    \n        if executable is None:\n            executable = args[0]\n    \n        sys.audit(\"subprocess.Popen\", executable, args, cwd, env)\n    \n        if (_USE_POSIX_SPAWN\n                and os.path.dirname(executable)\n                and preexec_fn is None\n                and (not close_fds or _HAVE_POSIX_SPAWN_CLOSEFROM)\n                and not pass_fds\n                and cwd is None\n                and (p2cread == -1 or p2cread > 2)\n                and (c2pwrite == -1 or c2pwrite > 2)\n                and (errwrite == -1 or errwrite > 2)\n                and not start_new_session\n                and process_group == -1\n                and gid is None\n                and gids is None\n                and uid is None\n                and umask < 0):\n            self._posix_spawn(args, executable, env, restore_signals, close_fds,\n                              p2cread, p2cwrite,\n                              c2pread, c2pwrite,\n                              errread, errwrite)\n            return\n    \n        orig_executable = executable\n    \n        # For transferring possible exec failure from child to parent.\n        # Data format: \"exception name:hex errno:description\"\n        # Pickle is not used; it is complex and involves memory allocation.\n        errpipe_read, errpipe_write = os.pipe()\n        # errpipe_write must not be in the standard io 0, 1, or 2 fd range.\n        low_fds_to_close = []\n        while errpipe_write < 3:\n            low_fds_to_close.append(errpipe_write)\n            errpipe_write = os.dup(errpipe_write)\n        for low_fd in low_fds_to_close:\n            os.close(low_fd)\n        try:\n            try:\n                # We must avoid complex work that could involve\n                # malloc or free in the child process to avoid\n                # potential deadlocks, thus we do all this here.\n                # and pass it to fork_exec()\n    \n                if env is not None:\n                    env_list = []\n                    for k, v in env.items():\n                        k = os.fsencode(k)\n                        if b'=' in k:\n                            raise ValueError(\"illegal environment variable name\")\n                        env_list.append(k + b'=' + os.fsencode(v))\n                else:\n                    env_list = None  # Use execv instead of execve.\n                executable = os.fsencode(executable)\n                if os.path.dirname(executable):\n                    executable_list = (executable,)\n                else:\n                    # This matches the behavior of os._execvpe().\n                    executable_list = tuple(\n                        os.path.join(os.fsencode(dir), executable)\n                        for dir in os.get_exec_path(env))\n                fds_to_keep = set(pass_fds)\n                fds_to_keep.add(errpipe_write)\n                self.pid = _fork_exec(\n                        args, executable_list,\n                        close_fds, tuple(sorted(map(int, fds_to_keep))),\n                        cwd, env_list,\n                        p2cread, p2cwrite, c2pread, c2pwrite,\n                        errread, errwrite,\n                        errpipe_read, errpipe_write,\n                        restore_signals, start_new_session,\n                        process_group, gid, gids, uid, umask,\n                        preexec_fn)\n                self._child_created = True\n            finally:\n                # be sure the FD is closed no matter what\n                os.close(errpipe_write)\n    \n            self._close_pipe_fds(p2cread, p2cwrite,\n                                 c2pread, c2pwrite,\n                                 errread, errwrite)\n    \n            # Wait for exec to fail or succeed; possibly raising an\n            # exception (limited in size)\n            errpipe_data = bytearray()\n            while True:\n                part = os.read(errpipe_read, 50000)\n                errpipe_data += part\n                if not part or len(errpipe_data) > 50000:\n                    break\n        finally:\n            # be sure the FD is closed no matter what\n            os.close(errpipe_read)\n    \n        if errpipe_data:\n            try:\n                pid, sts = os.waitpid(self.pid, 0)\n                if pid == self.pid:\n                    self._handle_exitstatus(sts)\n                else:\n                    self.returncode = sys.maxsize\n            except ChildProcessError:\n                pass\n    \n            try:\n                exception_name, hex_errno, err_msg = (\n                        errpipe_data.split(b':', 2))\n                # The encoding here should match the encoding\n                # written in by the subprocess implementations\n                # like _posixsubprocess\n                err_msg = err_msg.decode()\n            except ValueError:\n                exception_name = b'SubprocessError'\n                hex_errno = b'0'\n                err_msg = 'Bad exception data from child: {!r}'.format(\n                              bytes(errpipe_data))\n            child_exception_type = getattr(\n                    builtins, exception_name.decode('ascii'),\n                    SubprocessError)\n            if issubclass(child_exception_type, OSError) and hex_errno:\n                errno_num = int(hex_errno, 16)\n                if err_msg == \"noexec:chdir\":\n                    err_msg = \"\"\n                    # The error must be from chdir(cwd).\n                    err_filename = cwd\n                elif err_msg == \"noexec\":\n                    err_msg = \"\"\n                    err_filename = None\n                else:\n                    err_filename = orig_executable\n                if errno_num != 0:\n                    err_msg = os.strerror(errno_num)\n                if err_filename is not None:\n>                   raise child_exception_type(errno_num, err_msg, err_filename)\nE                   FileNotFoundError: [Errno 2] No such file or directory: 'node'\n\n../../.pyenv/versions/3.14.3/lib/python3.14/subprocess.py:1989: FileNotFoundError\n=========================== short test summary info ============================\nFAILED tests/test_durable_orchestrator_reliability.py::test_text_and_json_resource_bounds_fail_before_mutation\nFAILED tests/test_durable_orchestrator_reliability.py::test_database_parent_identity_substitution_is_detected\nFAILED tests/test_p14h_multi_stack_e2e.py::test_typescript_language_neutral_flow_records_add_modify_delete\n3 failed, 965 passed in 71.52s (0:01:11)\n",
    "stderr": ""
  }
}
```


## R1–R4 exact-review correction continuation (2026-09-09)

This resumes the same task, branch, baseline and ten-path closure. The missing-input stop used no correction, test, static batch or export. Approximately five active minutes of prior inspection are retained; the overnight interval awaiting the transferred package was stopped work. The transfer message adds no budget. Entry cumulative usage: correction batches 3, directed rounds 5, full suites 2, baseline comparison 1, branches 1, paths 10. Additional limits: one correction, two directed rounds, one final static/governance batch, one final export, 90 active work minutes including prior inspection; no installs, paid API, whole-repository tests, baseline rerun or host operations.

### Exact preflight and fixed scope

The supplied ZIP `/tmp/ts-b02a-r1r4-review.P2FKKHYl/tool_system_cubesandbox_exact_candidate_review.zip` is 325281 bytes, SHA-256 `da8843d21e5c027a356698fadf5ab0f5f8d5d7f7b6ffb0e20648513cb6c4e1b1`. Every SHA256SUMS entry matched. All ten archived candidate files equal actual worktree and index bytes; no candidate archive was copied into the repository. Branch is `agent/ts-b02a-cubesandbox-v070-acceptance-contract-v1`, HEAD `306a01fa6bf3bc8ed4204b88abdcb4f16f75360e`, baseline tree `ec74af108b6f1d7d4c9c7e440aec128261f3f251`. The exact export diff command `git --no-optional-locks --no-pager diff --cached --binary --no-ext-diff --no-textconv --no-color HEAD --` produced 480349 bytes with entry SHA-256 `6ace6f90f5c0114e1d24b705fcfb1dd37e8c68507798c20e269689a375dc9a6e`.

Current central main fixed paths were read directly again: principles blob `17741fb79252b43d6ff820dcffc7c92ab349acfc`, identity registry blob `20c9ec3cd74337bbf4cf5c5ab19de3b7ccd7eaf3`. These are observed read identities, not policy pins. Local principles, blueprint product_objective, parent sections 6–7, current pair, contract sections 5–7, existing oracle/schema/fixture/tests and review inputs were read before editing. R1–R4 retain parent complete disposal, fresh execution and deny_all semantics and bounded blueprint-driven source development. No runtime/public interface or authority framework changed. REPO_MANIFEST.md and tests/test_repo_manifest.py remain unchanged from entry.

### First directed round: exact original candidate, raw receipt

The seven test constructors matched canonical JSON SHA-256 of the seven archived input objects before evaluation. Oracle, schema and fixture were unchanged, and their hashes remained stable through execution. The complete original 107 assertions passed; all seven new assertions failed on actual erroneous PASS results. No archived oracle or replay_review.py was executed. Result: `7 failed, 107 passed in 7.18s`, exit 1, stderr empty. This uses additional directed round 1/2 (cumulative 6); original failures are retained below.

```json
{
  "status": "PASS",
  "preflight": {
    "process_authority_result": {
      "status": "PASS",
      "authority_path": "config/process_authority_v1.yaml",
      "module_id": "process-authority",
      "module_version": "2.3.0",
      "public_interface_id": "process-authority-api",
      "public_interface_version": "2.1.0",
      "current_task_input_mode": "explicit_manifest_change_plan_pair",
      "implicit_repository_index_allowed": false,
      "legacy_authority": false,
      "replay_result": {
        "status": "PASS",
        "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
        "pair_count": 108,
        "authority": false,
        "replay_only": true,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "production_deployment": false,
      "cleanup_execution": false,
      "reasons": []
    },
    "manifest_result": {
      "status": "PASS",
      "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "policy_path": "policy/repo_write_policy.yaml",
      "reasons": [],
      "autonomy_policy_path": "policy/autonomy_policy.yaml"
    },
    "pair_binding_result": {
      "status": "PASS",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "binding_mode": "explicit_manifest_change_plan_pair",
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "reasons": []
    },
    "change_plan_result": {
      "status": "PASS",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "reasons": []
    },
    "replay_execution_requested": false,
    "validation_to_dispatch_inputs_equal": true
  },
  "input_sha256_before": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "57b1d07264ea9fa95f26988b551cef3cee525ab5840c60bafa26457589a81086",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "cba28c9f8ef14f070148b04d1ac33cd5d9981135e2f32962c9f5201d7d996705"
  },
  "input_sha256_after": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "57b1d07264ea9fa95f26988b551cef3cee525ab5840c60bafa26457589a81086",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "cba28c9f8ef14f070148b04d1ac33cd5d9981135e2f32962c9f5201d7d996705"
  },
  "command_results": [
    {
      "name": "python -B -m pytest -q -s --tb=short -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 1,
      "stdout": "...........................................................................................................R1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R1_POST_ONLY_RELABELLING\", \"expected\": \"FAIL\", \"expected_reason\": \"0:SANDBOX_NETWORK_RESOURCE_LEAK\", \"input_schema_valid\": true, \"original_input_sha256\": \"1048073208a4b26913e5516f5c3b284863bc9e2b5bd23db9ac1f2d7f59181fad\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R1_POST_ONLY_CROSS_ROUND\", \"expected\": \"FAIL\", \"expected_reason\": \"1:SANDBOX_NETWORK_RESOURCE_LEAK\", \"input_schema_valid\": true, \"original_input_sha256\": \"5dcb5a2f405bb39e02c86de2f863b0506bdc84d6c92400026f7b2f4307d15066\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R2_FOREIGN_POOL_REFERENCE_DELETED\", \"expected\": \"FAIL\", \"expected_reason\": \"0:CROSS_SANDBOX_CONTAMINATION\", \"input_schema_valid\": true, \"original_input_sha256\": \"efac03e97399e11168142c808423b92db3b7c874f4b1222a06cd6f7c1ce2379d\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R3_RUNTIME_EXECUTION_JOIN\", \"expected\": \"FAIL\", \"expected_reason\": \"1:EXECUTION_JOIN_MISMATCH\", \"input_schema_valid\": true, \"original_input_sha256\": \"1bd0433810452910837831ec1d9091d1697b25edddf1ea6213d7e3d3c94c850f\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R3_TERMINATION_EXECUTION_JOIN\", \"expected\": \"FAIL\", \"expected_reason\": \"payload_sigkill:EXECUTION_JOIN_MISMATCH\", \"input_schema_valid\": true, \"original_input_sha256\": \"b892ce093b8bf5cd21b2424b3a64f0eaae2fc3d59afb598484951d328a83d779\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R4_RESTORE_FOREIGN_PROCESS\", \"expected\": \"FAIL\", \"expected_reason\": \"RESTORE_PROCESS_FOREIGN_BINDING\", \"input_schema_valid\": true, \"original_input_sha256\": \"a9cc6e5cf6e37352ed4eace5123a77150ad9abe0c4004850eb8f279f2c14cdf2\", \"reasons\": []}\nFR1_R4_RESULT {\"actual\": \"PASS\", \"aggregate\": \"PASS\", \"case\": \"R4_RESTORE_UNOBSERVED_PROCESS\", \"expected\": \"BLOCKED\", \"expected_reason\": \"RESTORE_PROCESS_OBSERVATION_MISSING\", \"input_schema_valid\": true, \"original_input_sha256\": \"38fcd30c2424702e667402dbd90f7804e505caa31941b42999cf9ef96cf61ed4\", \"reasons\": []}\nF\n=================================== FAILURES ===================================\n_______ test_r1_r4_exact_review_counterexample[R1_POST_ONLY_RELABELLING] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n_______ test_r1_r4_exact_review_counterexample[R1_POST_ONLY_CROSS_ROUND] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n__ test_r1_r4_exact_review_counterexample[R2_FOREIGN_POOL_REFERENCE_DELETED] ___\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n______ test_r1_r4_exact_review_counterexample[R3_RUNTIME_EXECUTION_JOIN] _______\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n____ test_r1_r4_exact_review_counterexample[R3_TERMINATION_EXECUTION_JOIN] _____\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n______ test_r1_r4_exact_review_counterexample[R4_RESTORE_FOREIGN_PROCESS] ______\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'FAIL'\nE     \nE     - FAIL\nE     + PASS\n____ test_r1_r4_exact_review_counterexample[R4_RESTORE_UNOBSERVED_PROCESS] _____\ntests/test_cubesandbox_backend_acceptance_contract.py:910: in test_r1_r4_exact_review_counterexample\n    assert selected[\"status\"] == expected\nE   AssertionError: assert 'PASS' == 'BLOCKED'\nE     \nE     - BLOCKED\nE     + PASS\n=========================== short test summary info ============================\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R1_POST_ONLY_RELABELLING]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R1_POST_ONLY_CROSS_ROUND]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R2_FOREIGN_POOL_REFERENCE_DELETED]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R3_RUNTIME_EXECUTION_JOIN]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R3_TERMINATION_EXECUTION_JOIN]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R4_RESTORE_FOREIGN_PROCESS]\nFAILED tests/test_cubesandbox_backend_acceptance_contract.py::test_r1_r4_exact_review_counterexample[R4_RESTORE_UNOBSERVED_PROCESS]\n7 failed, 107 passed in 7.18s\n",
      "stderr": ""
    }
  ],
  "subprocess_call_count": 1,
  "reasons": [],
  "source_sha256_before": {
    "tests/cubesandbox_contract_oracle.py": "11fa82b23a7a7d814a6a15834ab13b80327b095b2db13a74be9033021a7db0e5",
    "harness/cubesandbox_backend_acceptance_v1.schema.json": "84960537f2172d6246635c732fad0b03d95b47dec1a44cc529908ff88f6e2170",
    "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "3ad67cb076e872db80086669acb85c5c4e1ef1da201a660b3bf204658877790a",
    "tests/test_cubesandbox_backend_acceptance_contract.py": "2e3c3c61c2310cb788323bfb0056941221365731823dbf6712519db9d30b97a6",
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "cba28c9f8ef14f070148b04d1ac33cd5d9981135e2f32962c9f5201d7d996705",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "57b1d07264ea9fa95f26988b551cef3cee525ab5840c60bafa26457589a81086"
  },
  "source_sha256_after": {
    "tests/cubesandbox_contract_oracle.py": "11fa82b23a7a7d814a6a15834ab13b80327b095b2db13a74be9033021a7db0e5",
    "harness/cubesandbox_backend_acceptance_v1.schema.json": "84960537f2172d6246635c732fad0b03d95b47dec1a44cc529908ff88f6e2170",
    "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "3ad67cb076e872db80086669acb85c5c4e1ef1da201a660b3bf204658877790a",
    "tests/test_cubesandbox_backend_acceptance_contract.py": "2e3c3c61c2310cb788323bfb0056941221365731823dbf6712519db9d30b97a6",
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "cba28c9f8ef14f070148b04d1ac33cd5d9981135e2f32962c9f5201d7d996705",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "57b1d07264ea9fa95f26988b551cef3cee525ab5840c60bafa26457589a81086"
  },
  "exact_test_time_pair_base64": {
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "dGFza19pZDogdG9vbC1zeXN0ZW0tdHMtYjAyYS1jdWJlc2FuZGJveC12MDcwLWFybTY0LWJhY2tlbmQtYWNjZXB0YW5jZS1jb250cmFjdC12MQp0YXNrX3R5cGU6IHRlc3RfYWRkCnRhcmdldF9yZXBvOiBhcG9sbzE4My90b29sLXN5c3RlbQp0YXJnZXRfYnJhbmNoOiBhZ2VudC90cy1iMDJhLWN1YmVzYW5kYm94LXYwNzAtYWNjZXB0YW5jZS1jb250cmFjdC12MQpwaGFzZTogVFNfQjAyQV9DT05UUkFDVF9PTkxZCmFwcHJvdmVkX2JsdWVwcmludF9yZWZzOgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sCiAgICBzZWN0aW9uX29yX2tleTogcHJvZHVjdF9vYmplY3RpdmUKc2NvcGU6CiAgc3VtbWFyeTogRGVzaWduIGZvdXIgQ3ViZVNhbmRib3ggdjAuNy4wIEFSTTY0IGFjY2VwdGFuY2UgZ2F0ZXMgYW5kIHRlc3Qgb25seSBzeW50aGV0aWMgZXZpZGVuY2UsIHdpdGggbm8gYmFja2VuZCBleGVjdXRpb24gb3IgcHVibGljYXRpb24uCiAgaW5fc2NvcGU6CiAgICAtIEFwcGx5IG9ubHkgdGhlIGF1dGhvcml6ZWQgUjEtUjQgc2V2ZW4gZXhhY3QtaW5wdXQgY29ycmVjdGlvbnMgaW4gdGhlIHNhbWUgdGVuIHBhdGhzOyBwcmVzZXJ2ZSBvcmlnaW5hbCAxMDcgdGVzdCBzZW1hbnRpY3MgYW5kIGFsbCBoaXN0b3JpY2FsIGNvdW50cy4gTm8gUjUgY29ycmVjdGlvbiwgZnVsbCBzdWl0ZSwgYmFzZWxpbmUgcmVydW4gb3IgbmV3IGRlcGVuZGVuY3kuCiAgICAtIFJlYWQgZnJvemVuIHVwc3RyZWFtIHNvdXJjZSBhbmQgY3VycmVudCBjZW50cmFsIG1haW4gZm9ybWFsIHJ1bGVzLgogICAgLSBTcGVjaWZ5IGNvbXBvbmVudCBiaW5kaW5nLCBjb21wbGV0ZSByZWFwLCBzbmFwc2hvdCBpbnRlZ3JpdHksIGFuZCBhdHRyaWJ1dGVkIG5ldHdvcmsgY2xlYW51cC4KICAgIC0gQWRkIGEgbG9jYWwgSlNPTiBTY2hlbWEgYW5kIHRlc3Qtb25seSBwdXJlIG9yYWNsZSB1c2luZyBleGlzdGluZyBqc29uc2NoZW1hIGFuZCBweXRlc3QgbWVjaGFuaXNtcy4KICAgIC0gUmVnaXN0ZXIgZm9ybWFsIHRlc3QgYW5kIHNjaGVtYSBwYXRocyBpbiB0aGUgZXhpc3RpbmcgcmVwb3NpdG9yeSBtYW5pZmVzdC4KICAgIC0gU3luY2hyb25pemUgdGhlIGV4aXN0aW5nIGV4YWN0LWNvdW50IHJlcG9zaXRvcnktbWFuaWZlc3QgdGVzdCB3aXRoIHRoZSBmb3VyIGFkZGVkIGZvcm1hbCByb3dzLCBwcmVzZXJ2aW5nIGl0cyBjb3ZlcmFnZSBhbmQgcmVqZWN0aW9uIGNoZWNrcy4KICAgIC0gS2VlcCBvbmUgbG9jYWwgY2FuZGlkYXRlIGJyYW5jaCBhbmQgcmV0dXJuIGFuIHVuY29tbWl0dGVkIHJldmlld2FibGUgZGlmZi4KICAgIC0gQXBwbHkgdGhlIGV4cGxpY2l0bHkgYXV0aG9yaXplZCBzYW1lLXRhc2sgcmV2aWV3IGNvcnJlY3Rpb24gZm9yIG1hbmRhdG9yeSB0eXBlZCBhcnRpZmFjdHMsIGN1bXVsYXRpdmUgbmV0d29yayBvd25lcnNoaXAsIGNvbXBsZXRlIHJlYXAgc2FtcGxlcywgcnVudGltZSBkZW55X2FsbCBhbmQgZXhlY3V0aW9uLXNjb3BlZCByZXN0b3JlczsgcHJlc2VydmUgYWxsIHByaW9yIGJ1ZGdldHMgYW5kIGZhaWx1cmVzLgogIG91dF9vZl9zY29wZToKICAgIC0gQ3ViZVNhbmRib3ggaW5zdGFsbGF0aW9uLCBzZXJ2aWNlIG9yIHN5c3RlbWQgbXV0YXRpb24sIFZNIG9yIFZNTSBleGVjdXRpb24sIHJlYWwgc2FuZGJveCB3b3JrbG9hZCwgbmV0d29ya2luZyBvciBlQlBGIG11dGF0aW9uLgogICAgLSBDYW5vbmljYWwgbWFpbiB3cml0ZXMsIGNvbW1pdHMsIFBSIGNyZWF0aW9uLCBtZXJnZSwgcHVibGljYXRpb24sIGJhY2tlbmQgYWNjZXB0YW5jZSBvciBwcm9iZSBhdXRob3JpemF0aW9uLgogICAgLSBSdW50aW1lIGFkYXB0ZXIgaW1wbGVtZW50YXRpb24sIG5ldyBnb3Zlcm5hbmNlIGZyYW1ld29yaywgbW9kdWxlIG9yIHB1YmxpYyBpbnRlcmZhY2UsIHBlcm1pc3Npb24gY2hhbmdlcywgY2xlYW51cCBleGVjdXRpb24uCmV2aWRlbmNlOgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sCiAgICB3aHlfcmVsZXZhbnQ6IEJvdW5kZWQgaXNvbGF0ZWQgZGV2ZWxvcG1lbnQgYW5kIGluZGVwZW5kZW50bHkgb2JzZXJ2ZWQgZXZpZGVuY2UgcmVtYWluIHRoZSBnbG9iYWwgb2JqZWN0aXZlLgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGRvY3MvcmVwb3J0cy9zdWJzY3JpcHRpb25fd29ya2VyX3RzX2IwMmFfZGd4X3NwYXJrX2xpbnV4X2FybTY0X3ByaW1hcnlfdGFyZ2V0X2FuZF9lcGhlbWVyYWxfa3ZtX2lzb2xhdGlvbl9wYXRoX3JlYWxpZ25tZW50X3NwZWNpZmljYXRpb25fdjEubWQKICAgIGNvbW1pdF9zaGE6IDMwNmEwMWZhNmJmM2JjOGVkNDIwNGI4OGFiZGNiNGYxNmY3NTM2MGUKICAgIGxpbmVfcmFuZ2U6IDQ5MC01NzAKICAgIHdoeV9yZWxldmFudDogRGlyZWN0IHBhcmVudCBzZXBhcmF0ZXMgc291cmNlIGRlc2lnbiwgcmVhZC1vbmx5IGludmVudG9yeSwgY29uZGl0aW9uYWwgZW5hYmxlbWVudCwgYW5kIGV4cGxpY2l0bHkgYXV0aG9yaXplZCBndWVzdCBwcm9iZS4KICAtIHJlcG86IFRlbmNlbnRDbG91ZC9DdWJlU2FuZGJveAogICAgcGF0aDogLmdpdGh1Yi93b3JrZmxvd3MvcmVsZWFzZS1kb2NrZXItaW1hZ2VzLnltbAogICAgY29tbWl0X3NoYTogZDAwODE2NDFjNTk4MjJlNGU1NjUzYjc0NjJlOTE0NDEwYjgxOTEwYQogICAgbGluZV9yYW5nZTogNzI1LTc0MAogICAgd2h5X3JlbGV2YW50OiBGcm96ZW4gQVJNNjQgc291cmNlIHdvcmtmbG93IGRpc2FibGVzIHB1Ymxpc2hlZCBwcm92ZW5hbmNlIGFuZCBTQk9NIGF0dGVzdGF0aW9ucy4KYWxsb3dlZF9maWxlczoKICAtIGRvY3MvcmVwb3J0cy90c19iMDJhX2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdF92MS5tZAogIC0gZG9jcy9yZXBvcnRzL3RzX2IwMmFfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxX2V2aWRlbmNlLm1kCiAgLSBoYXJuZXNzL2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV92MS5zY2hlbWEuanNvbgogIC0gdGVzdHMvZml4dHVyZXMvY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX3YxLmpzb24KICAtIHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weQogIC0gdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAtIGV4YW1wbGVzL3Rhc2tfbWFuaWZlc3RzL3Rvb2xfc3lzdGVtX3RzX2IwMmFfY3ViZXNhbmRib3hfYWNjZXB0YW5jZV9jb250cmFjdF92MS55YW1sCiAgLSBleGFtcGxlcy9jaGFuZ2VfcGxhbnMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKICAtIFJFUE9fTUFOSUZFU1QubWQKICAtIHRlc3RzL3Rlc3RfcmVwb19tYW5pZmVzdC5weQpmb3JiaWRkZW5fZmlsZXM6CiAgLSBzcmMvKioKICAtIGNvbmZpZy8qKgogIC0gcG9saWN5LyoqCiAgLSBibHVlcHJpbnQvKioKICAtIC5naXRodWIvKioKICAtIEFHRU5UUy5tZAogIC0gcHlwcm9qZWN0LnRvbWwKICAtIGRvY3MvdG9vbF9zeXN0ZW1fcHJvamVjdF9zdGF0ZV92MS55YW1sCndyaXRlX21vZGU6IHB1bGxfcmVxdWVzdAp2ZXJpZmljYXRpb246CiAgY29tbWFuZHM6CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLXMgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHJ1ZmYgZm9ybWF0IC0tY2hlY2sgdGVzdHMvY3ViZXNhbmRib3hfY29udHJhY3Rfb3JhY2xlLnB5IHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLXAgbm86Y2FjaGVwcm92aWRlciB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogICAgLSBweXRob24gLUIgLW0gcHl0ZXN0IC1xIC1wIG5vOmNhY2hlcHJvdmlkZXIKICAgIC0gcnVmZiBjaGVjayB0ZXN0cy9jdWJlc2FuZGJveF9jb250cmFjdF9vcmFjbGUucHkgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAgIC0gcHl0aG9uIC1CIC1tIHRvb2xfc3lzdGVtLmNsaS52YWxpZGF0ZV9hY3RpdmVfZ2F0ZXMgdGVzdHMvZml4dHVyZXMvbWFuaWZlc3RfdmFsaWRhdGlvbi9zdHJpY3RfYWN0aXZlX2dhdGVzX3YxLnlhbWwKICAgIC0gcHl0aG9uIC1CIC1tIHRvb2xfc3lzdGVtLmNsaS52YWxpZGF0ZV9wcm9jZXNzX2F1dGhvcml0eSBjb25maWcvcHJvY2Vzc19hdXRob3JpdHlfdjEueWFtbAogICAgLSBweXRob24gLUIgLW0gdG9vbF9zeXN0ZW0uY2xpLnZhbGlkYXRlX21vZHVsZV9yZWdpc3RyeSBjb25maWcvbW9kdWxlX3JlZ2lzdHJ5X3YxLnlhbWwgLS1yZXF1aXJlLWN1cnJlbnQtYXV0aG9yaXR5CiAgICAtIHB5dGhvbiAtQiAtbSB0b29sX3N5c3RlbS5jbGkudmFsaWRhdGVfcmVwb19tYW5pZmVzdCBSRVBPX01BTklGRVNULm1kCiAgICAtIGdpdCBkaWZmIC0tY2hlY2sKICAgIC0gcHl0aG9uIC1CIC1tIHB5dGVzdCAtcSAtLXRiPXNob3J0IC1wIG5vOmNhY2hlcHJvdmlkZXIgdGVzdHMvdGVzdF9kdXJhYmxlX29yY2hlc3RyYXRvcl9yZWxpYWJpbGl0eS5weTo6dGVzdF90ZXh0X2FuZF9qc29uX3Jlc291cmNlX2JvdW5kc19mYWlsX2JlZm9yZV9tdXRhdGlvbiB0ZXN0cy90ZXN0X2R1cmFibGVfb3JjaGVzdHJhdG9yX3JlbGlhYmlsaXR5LnB5Ojp0ZXN0X2RhdGFiYXNlX3BhcmVudF9pZGVudGl0eV9zdWJzdGl0dXRpb25faXNfZGV0ZWN0ZWQgdGVzdHMvdGVzdF9wMTRoX211bHRpX3N0YWNrX2UyZS5weTo6dGVzdF90eXBlc2NyaXB0X2xhbmd1YWdlX25ldXRyYWxfZmxvd19yZWNvcmRzX2FkZF9tb2RpZnlfZGVsZXRlCiAgcGFzc19jb25kaXRpb25zOgogICAgLSBBbGwgZm91ciBnYXRlIHNwZWNpZmljYXRpb25zIGFuZCBleGFjdCByZXF1ZXN0ZWQgcG9zaXRpdmUgYW5kIG5lZ2F0aXZlIGZpeHR1cmUgYXNzZXJ0aW9ucyBwYXNzLgogICAgLSBTeW50aGV0aWMgUEFTUyBuZXZlciBhdXRob3JpemVzIHJlYWwgYmFja2VuZCBhY2NlcHRhbmNlOyB0aGUgY2FuZGlkYXRlIGxpZmVjeWNsZS1tYW5hZ2VyIGRpZ2VzdCByZW1haW5zIG51bGwgYW5kIEcxIEJMT0NLRUQuCiAgICAtIE9ubHkgdGhlIHRlbiBsaXN0ZWQgcGF0aHMgZGlmZmVyOyBjYW5vbmljYWwgbWFpbiwgcnVudGltZSwgYXV0aG9yaXR5IGNvbnRyYWN0cyBhbmQgcHVibGljIGludGVyZmFjZXMgYXJlIHVuY2hhbmdlZC4Kcm9sbGJhY2s6CiAgbWV0aG9kOiBwYXRjaF9yZXZlcnNlCiAgcmVmZXJlbmNlOiBSZXZlcnNlIG9ubHkgdGhpcyB0ZW4tcGF0aCBjYW5kaWRhdGUgZGlmZiBhZ2FpbnN0IDMwNmEwMWZhNmJmM2JjOGVkNDIwNGI4OGFiZGNiNGYxNmY3NTM2MGUgYWZ0ZXIgcmV2aWV3OyBubyBhdXRvbWF0aWMgY2xlYW51cCBvciBtYWluIHJlc2V0LgphcHByb3ZhbDoKICByZXF1aXJlZDogdHJ1ZQogIGFwcHJvdmVkX2J5OiBhcG9sbzE4MwogIGFwcHJvdmFsX3NvdXJjZTogQ3VycmVudCB1c2VyIHRhc2sgVE9PTC1TWVNURU0tVFMtQjAyQS1DVUJFU0FOREJPWC1WMDcwLUFSTTY0LUJBQ0tFTkQtQUNDRVBUQU5DRS1DT05UUkFDVC12MTsgbG9jYWwgc291cmNlL2RvYy9maXh0dXJlIHdvcmsgb25seSwgcHVibGljYXRpb24gZXhwbGljaXRseSBwcm9oaWJpdGVkLgogIGFwcHJvdmVkX2F0OiAyMDI2LTA5LTA4IEF1c3RyYWxpYS9BZGVsYWlkZTsgZGF0ZS1sZXZlbCB0YXNrIGF1dGhvcml6YXRpb24K",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "cGxhbl9pZDogdG9vbC1zeXN0ZW0tdHMtYjAyYS1jdWJlc2FuZGJveC12MDcwLWFybTY0LWJhY2tlbmQtYWNjZXB0YW5jZS1jb250cmFjdC12MQp0YXJnZXRfcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KdGFza19tYW5pZmVzdDogZXhhbXBsZXMvdGFza19tYW5pZmVzdHMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKYmFzZWxpbmU6CiAgY29tbWl0OiAzMDZhMDFmYTZiZjNiYzhlZDQyMDRiODhhYmRjYjRmMTZmNzUzNjBlCiAgdHJlZTogZWM3NGFmMTA4YjZmMWQ3ZDRjOWM3ZTQ0MGFlYzEyODI2MWYzZjI1MQogIG9yaWdpbmFsX2xvY2FsX21haW46IDAyN2RiYjNmYjgzYzM4ZGVmNzBlODFkNTg3MTJmODBkYmU2MTM0ODMKYnJhbmNoOiBhZ2VudC90cy1iMDJhLWN1YmVzYW5kYm94LXYwNzAtYWNjZXB0YW5jZS1jb250cmFjdC12MQphbGlnbm1lbnQ6CiAgcGFyZW50OiBkb2NzL3JlcG9ydHMvc3Vic2NyaXB0aW9uX3dvcmtlcl90c19iMDJhX2RneF9zcGFya19saW51eF9hcm02NF9wcmltYXJ5X3RhcmdldF9hbmRfZXBoZW1lcmFsX2t2bV9pc29sYXRpb25fcGF0aF9yZWFsaWdubWVudF9zcGVjaWZpY2F0aW9uX3YxLm1kIHNlY3Rpb25zIDktMTE7IGRlZmluZSBldmlkZW5jZSBvbmx5IGFuZCBwcmVzZXJ2ZSBmdXR1cmUgcHJvYmUgYXV0aG9yaXphdGlvbi4KICBnbG9iYWw6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sOnByb2R1Y3Rfb2JqZWN0aXZlOyBib3VuZGVkIGlzb2xhdGVkIGRldmVsb3BtZW50LCBubyBzaWxlbnQgYXV0aG9yaXR5IG9yIHJ1bnRpbWUgZXhwYW5zaW9uLgpjaGFuZ2VkX2ZpbGVzOgogIC0gZG9jcy9yZXBvcnRzL3RzX2IwMmFfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLm1kCiAgLSBkb2NzL3JlcG9ydHMvdHNfYjAyYV9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3RfdjFfZXZpZGVuY2UubWQKICAtIGhhcm5lc3MvY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX3YxLnNjaGVtYS5qc29uCiAgLSB0ZXN0cy9maXh0dXJlcy9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfdjEuanNvbgogIC0gdGVzdHMvY3ViZXNhbmRib3hfY29udHJhY3Rfb3JhY2xlLnB5CiAgLSB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogIC0gZXhhbXBsZXMvdGFza19tYW5pZmVzdHMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKICAtIGV4YW1wbGVzL2NoYW5nZV9wbGFucy90b29sX3N5c3RlbV90c19iMDJhX2N1YmVzYW5kYm94X2FjY2VwdGFuY2VfY29udHJhY3RfdjEueWFtbAogIC0gUkVQT19NQU5JRkVTVC5tZAogIC0gdGVzdHMvdGVzdF9yZXBvX21hbmlmZXN0LnB5CmZpbGVfZGlzcG9zaXRpb246CiAgZXhpc3RpbmdfZmlsZTogUkVQT19NQU5JRkVTVC5tZAogIHJlZ2lvbjogRm9ybWFsIEZpbGVzIGFuZCBSZXRhaW5lZCBOb24tQXV0aG9yaXR5IFNldHMgdGFibGVzCiAgYWN0aW9uOiBBZGQgb25seSBmb3VyIGZvcm1hbCBzY2hlbWEvdGVzdC9maXh0dXJlIHJvd3M7IGV4aXN0aW5nIHJldGFpbmVkIGdsb2JzIGNvdmVyIHRoZSB0d28gcmVwb3J0cyBhbmQgZXhwbGljaXQgcGFpci4gTm8gcmVjbGFzc2lmaWNhdGlvbiBvciBjbGVhbnVwLgogIGRlcGVuZGVudF90ZXN0OiB0ZXN0cy90ZXN0X3JlcG9fbWFuaWZlc3QucHkgbGluZXMgMTA5LTE0MzsgY2hhbmdlIG9ubHkgdGhlIHR3byBleGFjdCBmb3JtYWwtcm93IGNvdW50IGFzc2VydGlvbnMgZnJvbSAyOTUgdG8gMjk5IGFmdGVyIHJlYWRpbmcgdGhlIGZpcnN0IGZ1bGwtc3VpdGUgZmFpbHVyZS4Kc2NvcGVfY29ycmVjdGlvbjoKICByZWFzb246IFRoZSBmb3VyIG5ldyBmb3JtYWwgcm93cyByZXF1aXJlIHRoZSBleGlzdGluZyByZXBvc2l0b3J5LW1hbmlmZXN0IHRlc3QgdG8gYXNzZXJ0IHRoZSBuZXcgZXhhY3QgY291bnQuIERvY3VtZW50IHRoaXMgaW1tZWRpYXRlIGRlcGVuZGVuY3kgYmVmb3JlIGVkaXRpbmcgaXQ7IG5vIGFjY2VwdGFuY2Ugc2NvcGUgb3IgcnVudGltZSBhdXRob3JpdHkgY2hhbmdlcy4KICBjaGFuZ2VkX3BhdGhfY291bnRfYmVmb3JlOiA5CiAgY2hhbmdlZF9wYXRoX2NvdW50X2FmdGVyOiAxMAogIGZpcnN0X2Z1bGxfc3VpdGU6IDQgZmFpbGVkLCA5NjQgcGFzc2VkIGluIDcyLjM2czsgbWFuaWZlc3QgY291bnQgZmFpbHVyZSBpcyBjYW5kaWRhdGUtY2F1c2VkLCB0d28gZHVyYWJpbGl0eSBmYWlsdXJlcyByZWplY3QgZ3JvdXAtd3JpdGFibGUgZml4dHVyZSBkaXJlY3RvcmllcywgYW5kIHRoZSBUeXBlU2NyaXB0IGZpeHR1cmUgY2Fubm90IGZpbmQgbm9kZS4KICByZXBhaXJfY3ljbGU6IDEgb2YgMjsgc3luY2hyb25pemUgZXhhY3QgY291bnRzIGFuZCBmaXggdGhyZWUgbmV3LWZpbGUgbGludCBkaWFnbm9zdGljcyBvbmx5LiBEbyBub3QgcmVwYWlyIHRoZSBob3N0IG9yIGV4aXN0aW5nIGR1cmFiaWxpdHkvVHlwZVNjcmlwdCBpbXBsZW1lbnRhdGlvbi4KZmluYWxfYm91bmRhcnlfY29ycmVjdGlvbjoKICByZXBhaXJfY3ljbGU6IDIgb2YgMgogIHJlYXNvbjogRzQgcmVxdWlyZXMgdHdvIGNsZWFuIHNhbXBsZXMgYnkgdGhlIGRlYWRsaW5lLiBBIGZpcnN0IGNsZWFuIHNhbXBsZSBleGFjdGx5IGF0IHRoZSBkZWFkbGluZSBtdXN0IGJlIEZBSUwsIG5vdCBCTE9DS0VELiBBZGQgYSBzeW50aGV0aWMgcmVncmVzc2lvbiBiZWZvcmUgY29ycmVjdGluZyB0aGlzIGJyYW5jaDsgcHJlc2VydmUgdGhlIGV4aXN0aW5nIGFmdGVyLWRlYWRsaW5lIEZBSUwuCiAgZmlsZXM6IHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weSBmaW5hbCBjbGVhbi1zYW1wbGUgdmVyZGljdDsgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkgbmV0d29yayBkZWFkbGluZSBjYXNlcy4KICB2YWxpZGF0aW9uX2J1ZGdldDogVXNlIGZvY3VzZWQgcnVucyAyIGFuZCAzIGZvciByZWdyZXNzaW9uIHRoZW4gcmVwYWlyLiBCb3RoIGZ1bGwtc3VpdGUgcnVucyBhcmUgc3BlbnQ7IGRvIG5vdCByZXJ1biB0aGVtIG9yIHJlcGFpciB1bnJlbGF0ZWQgaG9zdCBwcmVyZXF1aXNpdGVzLgpyZXVzZToKICAtIFVzZSBleGlzdGluZyBqc29uc2NoZW1hIERyYWZ0MjAyMDEyVmFsaWRhdG9yLCBweXRlc3QgYW5kIGV4cGxpY2l0IHRhc2stcGFpci9wcm9jZXNzLWF1dGhvcml0eSB2YWxpZGF0aW9uLgogIC0gVGhlIGNvbW1hbmQgdGVzdCBnYXRlIG9ubHkgZXZhbHVhdGVzIGNvbW1hbmQgZXhpdHMgYW5kIGNhbm5vdCBkZWNpZGUgaG9zdCBhY2NlcHRhbmNlLiBEbyBub3QgZmVlZCBob3N0IGNsYWltcyBpbnRvIGl0LgogIC0gVGhlIHByb2R1Y3Rpb24tcmVhZGluZXNzIGRlY2lzaW9uIGlzIFAxNi1zcGVjaWZpYyBhbmQgZ3JhbnRzIG5vIGJhY2tlbmQgZXZpZGVuY2Ugc2VtYW50aWNzOyBwcmVzZXJ2ZSBpdC4KICAtIEV4aXN0aW5nIElzb2xhdGlvblJlcXVlc3RWMSBhbmQgRXhlY3V0aW9uRXZpZGVuY2VWMSBvd25lcnNoaXAgcmVtYWlucyB3aXRoIGZ1dHVyZSBUUy1CMDJBL0IvQzsgdGhpcyBpcyBhIHRlc3Qtb25seSBjb250cmFjdCBzcGVjaWFsaXphdGlvbiwgbm90IGEgcnVudGltZSBvciBuZXcgcHVibGljIGludGVyZmFjZS4KICAtIFJldXNlIHRoZSBwdWJsaWMgRnJvemVuRGV2ZWxvcG1lbnRDb250cmFjdCBhbmQgZGV2ZWxvcG1lbnQtbG9vcCBWYWxpZGF0b3IgY2FsbGJhY2s7IGV4aXN0aW5nIHRhc2stcnVubmVyIGV4ZWN1dGlvbi1iaW5kaW5nLXYyIGV2aWRlbmNlIG9ibGlnYXRpb25zIGFuZCBydW5uZXItaXNzdWVkIHJlY2VpcHRzIHJlbWFpbiB0aGUgc29sZSBjb2RlLWRldmVsb3BtZW50IHJlY2VpcHQgZnJhbWV3b3JrLCB1bmNoYW5nZWQuCmJ1ZGdldHM6CiAgYnJhbmNoX2NvdW50OiAxCiAgY2hhbmdlZF9wYXRoX2NvdW50OiAxMAogIHJlcGFpcl9jeWNsZXM6IDIKICBmb2N1c2VkX3Rlc3RfcnVuczogMwogIGZ1bGxfc3VpdGVfcnVuczogMgogIHdhbGxfbWludXRlc19mcm9tX3Njb3BlX2ZyZWV6ZTogOTAKICBleHRlcm5hbF9yZXZpZXdfY3ljbGVzOiAwCiAgcGFpZF9hcGlfY2FsbHM6IDAKICByZWFsX2JhY2tlbmRfb3BlcmF0aW9uczogMAogIHB1YmxpY2F0aW9uX29wZXJhdGlvbnM6IDAKdmFsaWRhdGlvbl9lbnZpcm9ubWVudDoKICBjd2Q6IC9ob21lL3JpY2gvcHJvamVjdHMvdG9vbC1zeXN0ZW0KICBweXRob246IC9ob21lL3JpY2gvLnB5ZW52L3ZlcnNpb25zLzMuMTQuMy9iaW4vcHl0aG9uCiAgUFlUSE9ORE9OVFdSSVRFQllURUNPREU6ICcxJwogIFBZVEhPTlBBVEg6IHNyYzovdG1wL3RzLWIwMmEtY3ViZXNhbmRib3gtY29udHJhY3QtdjEtZGVwcwogIHRlbXBvcmFyeV9kZXBlbmRlbmN5X2V4Y2VwdGlvbjogRXhpc3RpbmcgcGlubmVkIGpzb25zY2hlbWEgYW5kIGl0cyBkZXBlbmRlbmNpZXMgY29waWVkIGZyb20gbG9jYWwgd2hlZWxob3VzZSBpbnRvIHRoaXMgdGFzay1vbmx5IC90bXAgZGlyZWN0b3J5OyByZXRhaW5lZCBmb3IgcmV2aWV3LCBubyBzeXN0ZW0gZW52aXJvbm1lbnQgb3IgQ3ViZVNhbmRib3ggaW5zdGFsbGF0aW9uLiBJbml0aWFsIG5ldHdvcmsgYXR0ZW1wdCBpbnRlcnJ1cHRlZCBhZnRlciBzYW5kYm94IGRlbmlhbDsgcmV0YWluIGl0cyBmYWlsdXJlIGluIGV2aWRlbmNlLgp2ZXJpZmljYXRpb246CiAgY29tbWFuZHM6CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLXMgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CmNvbXBsZXRlZF92YWxpZGF0aW9uX2JhdGNoOgogIGZvY3VzZWRfY29tbWFuZDogcHl0aG9uIC1CIC1tIHB5dGVzdCAtcSAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgcmVzdWx0OiA1NiBwYXNzZWQgaW4gMi41N3M7IGV4aXQgMDsgcHJvdGVjdGVkIGlucHV0IGJ5dGVzIGVxdWFsIGJlZm9yZSBkaXNwYXRjaC4KICBmdWxsX3N1aXRlXzE6IDQgZmFpbGVkLCA5NjQgcGFzc2VkIGluIDcyLjM2czsgZXhpdCAxOyBvcmlnaW5hbCBsaW50IGZhaWxlZCB3aXRoIDMgZGlhZ25vc3RpY3M7IGFsbCBmb3VyIHJlcG9zaXRvcnkgdmFsaWRhdG9ycyBwYXNzZWQuCiAgZnVsbF9zdWl0ZV8yOiAzIGZhaWxlZCwgOTY1IHBhc3NlZCBpbiA3MS41MnM7IGV4aXQgMTsgbGludCBhbmQgYWxsIGZvdXIgcmVwb3NpdG9yeSB2YWxpZGF0b3JzIHBhc3NlZC4gUmVtYWluaW5nIGZhaWx1cmVzIGFyZSB0d28gZ3JvdXAtd3JpdGFibGUgZml4dHVyZS1kaXJlY3RvcnkgY2hlY2tzIGFuZCBtaXNzaW5nIG5vZGUgaW4gdGhlIHZhbGlkYXRpb24gUEFUSC4Kcm9sbGJhY2s6CiAgbWV0aG9kOiBwYXRjaF9yZXZlcnNlCiAgcmVmZXJlbmNlOiBSZXZlcnNlIG9ubHkgdGhlIHRlbi1wYXRoIGNhbmRpZGF0ZSBwYXRjaCBhZnRlciByZXZpZXc7IHByZXNlcnZlIG9yaWdpbmFsIGxvY2FsIG1haW4gYW5kIGFsbCBleGlzdGluZyBldmlkZW5jZS4Kc3RvcDoKICB0ZXJtaW5hbDogUmV2aWV3YWJsZSBsb2NhbCBjb250cmFjdCB3aXRoIGZpeHR1cmUgcmVzdWx0cyBhbmQgZXhwbGljaXQgcmVhbC1ob3N0IGJsb2NrZXJzOyBzdG9wIGZvciBpbmRlcGVuZGVudCByZXZpZXcuCiAgb25fc2NvcGVfZHJpZnQ6IHRydWUKICBvbl9idWRnZXRfZXhoYXVzdGlvbjogdHJ1ZQogIG9uX3JlcGVhdGVkX25vX3Byb2dyZXNzOiB0cnVlCiAgY29tbWl0OiBmYWxzZQogIHB1bGxfcmVxdWVzdDogZmFsc2UKICBtZXJnZTogZmFsc2UKICByZWFsX2JhY2tlbmRfYWNjZXB0YW5jZV9hdXRob3JpemVkOiBmYWxzZQpyZXZpZXdfY29ycmVjdGlvbl9hdXRob3JpemF0aW9uOgogIHNvdXJjZTogRXhwbGljaXQgc2FtZS10YXNrIHVzZXIgY29udGludWF0aW9uIGFmdGVyIGluZGVwZW5kZW50IHNvdXJjZSByZXZpZXc7IG5vIG5ldyBicmFuY2gsIHRhc2sgaWRlbnRpdHksIGZyYW1ld29yayBvciBwYXRoLgogIHByZXNlcnZlZF91c2VkX2J1ZGdldDogJ3JlcGFpciAyLzI7IGZvY3VzZWQgMy8zOyBmdWxsIHN1aXRlIDIvMjsgYnJhbmNoIDEvMTsgZXhhY3QgcGF0aHMgMTAvMTAnCiAgYWRkaXRpb25hbF9idWRnZXQ6ICdvbmUgY29ycmVjdGlvbiBiYXRjaDsgdHdvIHRhcmdldGVkIHJvdW5kcyAoY291bnRlcmV4YW1wbGVzIHRoZW4gZmluYWwgcmVncmVzc2lvbik7IGF0IG1vc3Qgb25lIGV4YWN0LWJhc2UgY29tcGFyaXNvbiBvZiB0aGUgdGhyZWUgaGlzdG9yaWNhbCBmYWlsdXJlczsgYXQgbW9zdCBvbmUgZnVsbCBzdWl0ZSBvbmx5IGlmIGV4aXN0aW5nIGVudmlyb25tZW50IHByZXJlcXVpc2l0ZXMgcGFzcycKICByZWFkc19iZWZvcmVfd3JpdGU6ICdWZXJpZmllZCBpbmRleCBlcXVhbHMgd29ya3RyZWUgYW5kIGFsbCBuaW5lIHJldGFpbmVkIHNvdXJjZSBTSEEyNTYgdmFsdWVzOyByZWFkIG9yaWdpbmFsIHRvb2wgcmVjZWlwdHMgYW5kIGxvY2FsIGV2aWRlbmNlOyByZS1yZWFkIGJvdGggY3VycmVudCBjZW50cmFsIG1haW4gZm9ybWFsIHBhdGhzLiBQYXJlbnQgc2VjdGlvbiA2IGJpbmRzIGRlbnlfYWxsIGFuZCBmcmVzaCBleGVjdXRpb24gc3RhdGUuJwogIGNvcnJlY3Rpb25fcmVnaW9uczoKICAgIC0gJ0cxIG9yYWNsZSBfY29tcG9uZW50cyBhbmQgc2NoZW1hIGFydGlmYWN0L2NvbXBvbmVudC9jYXRhbG9nOiBmaXhlZCBtaW5pbXVtIHR5cGVkIGFydGlmYWN0IG9ibGlnYXRpb25zOyBPQ0kgYW5kIGZpbGUgaWRlbnRpdGllcyB1c2UgZGlzdGluY3Qgc2hhcGVzOyBubyBqb2ludGx5IGVtcHR5IGVtYmVkZGVkIGNsb3N1cmUgUEFTUy4nCiAgICAtICdHMiBvcmFjbGUgX3JlYXAgYW5kIHJlYXAgZXZpZGVuY2U6IGZpbmFsIHR3byBzYW1wbGVzIG11c3QgZWFjaCBiZSBjb21wbGV0ZSBhbmQgZW1wdHkgYnkgZGVhZGxpbmU7IFBJRDEgcmV0YWluZWQtRkQgcG9zaXRpdmUgY29udHJvbCBpcyBvcHRpb25hbCwgc2NhbiBjb21wbGV0ZW5lc3MgYW5kIGFsbCBleGVjdXRpb24gaGVscGVycyByZW1haW4gbWFuZGF0b3J5LicKICAgIC0gJ0c0IG9yYWNsZSBfbmV0d29yayBhbmQgcmVzb3VyY2Uvcm91bmQgc2NoZW1hOiByZXRhaW4gaW1tdXRhYmxlIG93bmVkIGlkZW50aXRpZXMgYWNyb3NzIGV2ZXJ5IGxhdGVyIHBvc3Qgc2FtcGxlOyByZXF1aXJlIHJ1bnRpbWUgZGVueV9hbGwgZXZpZGVuY2UsIGd1ZXN0IGRldmljZS9jb250cm9sIHBhdGggYWJzZW5jZSBhbmQgc2VhbGVkIEFSTTY0IHNvY2tldC1BQkkgZW5mb3JjZW1lbnQgYmVmb3JlIHdvcmtsb2FkIGFuZCB0aHJvdWdoIHJ1bnRpbWUvcmVzdG9yZXMuJwogICAgLSAnRzMgb3JhY2xlIF9zbmFwc2hvdCBhbmQgc25hcHNob3QvcmVzdG9yZSBzY2hlbWE6IHJlLWV2YWx1YXRlIHJlc3RvcmVkIGNvbXBvbmVudCBvYnNlcnZhdGlvbnMgd2l0aCBHMTsgYmluZCBzYW1lIGV4ZWN1dGlvbi9yZXF1ZXN0LCBzZXBhcmF0ZWx5IGFwcHJvdmVkIGNsZWFuIHRlbXBsYXRlIGFuZCBuZXcgZXhlY3V0aW9uLCBvciByZWplY3QgY3Jvc3MtZXhlY3V0aW9uIG11dGFibGUgc3RhdGUuJwogICAgLSAnS2VlcCB0ZXN0cy90ZXN0X3JlcG9fbWFuaWZlc3QucHkgYW5kIFJFUE9fTUFOSUZFU1QubWQgdW5jaGFuZ2VkIGZyb20gdGhlIGluaXRpYWwgdGVuLWZpbGUgY2FuZGlkYXRlLiBTYXZlIHJhdyByZWNlaXB0cyBhbmQgZmluYWwgZGlnZXN0IGludmVudG9yeSBpbnNpZGUgdGhlIGV4aXN0aW5nIGV2aWRlbmNlIHJlcG9ydCwgbm90IGFuIGVsZXZlbnRoIGZpbGUuJwogIGJhc2VsaW5lX2NvbXBhcmlzb246ICdTYW1lIGVudmlyb25tZW50LCBleGFjdCAzMDZhMDFmYTZiZjNiYzhlZDQyMDRiODhhYmRjYjRmMTZmNzUzNjBlIHNvdXJjZS90ZXN0L2ZpeHR1cmUgZGVwZW5kZW5jeSBieXRlcyB2ZXJpZmllZCBiZWZvcmUgb25lIHRocmVlLW5vZGUgcnVuOyBubyBjaGVja291dCwgbmV3IGJyYW5jaCwgcGVybWlzc2lvbiBvciBQQVRIIHJlcGFpci4nCiAgZW52aXJvbm1lbnRfc3RvcDogJ0V4aXN0aW5nIFB5dGhvbiAzLjE0LjMsIHB5dGVzdCA5LjEuMSBhbmQgcmV0YWluZWQganNvbnNjaGVtYSA0LjI2LjAgaW1wb3J0IHN1Y2Nlc3NmdWxseS4gTm9kZSBpcyBhYnNlbnQuIE5vIGRlcGVuZGVuY3kgaW5zdGFsbGF0aW9uIG9yIGZ1bGwgc3VpdGUgd2hpbGUgdGhpcyBwcmVyZXF1aXNpdGUgaXMgbWlzc2luZy4nCiAgY291bnRlcmV4YW1wbGVfcm91bmQ6ICdhZGRpdGlvbmFsIHRhcmdldGVkIDEvMjsgMTAgZmFpbGVkLCA1OCBwYXNzZWQgaW4gMy4wMHM7IGV4aXQgMTsgYWxsIHRlbiBuZXcgcmV2aWV3IGFzc2VydGlvbnMgZmFpbGVkIG9uIHRoZSB2ZXJpZmllZCBvcmlnaW5hbCBvcmFjbGUvc2NoZW1hIHdoaWxlIGFsbCBvcmlnaW5hbCByZWdyZXNzaW9ucyBwYXNzZWQnCiAgYmFzZWxpbmVfY29tcGFyaXNvbl9yZXN1bHQ6ICcxLzEgdXNlZDsgMTQ0IHNvdXJjZS90ZXN0L2ZpeHR1cmUgZGVwZW5kZW5jeSBmaWxlcyBlcXVhbCBleGFjdCBiYXNlbGluZTsgMyBmYWlsZWQgaW4gMC4zNHMsIGV4aXQgMSwgc2FtZSBkaXJlY3RvcnktbW9kZSByZWplY3Rpb25zIGFuZCBtaXNzaW5nIG5vZGUnCiAgZnVsbF9zdWl0ZV9kaXNwb3NpdGlvbjogJ2FkZGl0aW9uYWwgMC8xIHVzZWQ7IE5PVF9FWEVDVVRFRF9FTlZJUk9OTUVOVF9CTE9DS0VEOyBub2RlIHVuYXZhaWxhYmxlIGFuZCBleGlzdGluZyBkaXJlY3RvcnktbW9kZSBwcmVyZXF1aXNpdGVzIGZhaWw7IGRvIG5vdCBydW4gYSBrbm93biBmYWlsaW5nIGZ1bGwgc3VpdGUnCiAgZmluYWxfdGFyZ2V0ZWRfcm91bmQ6ICdhZGRpdGlvbmFsIDIvMjsgMTA3IHBhc3NlZCBpbiA2LjQwczsgZXhpdCAwOyBhbGwgb3JpZ2luYWwgNTggcmVncmVzc2lvbnMgcmV0YWluZWQ7IFJ1ZmYgYW5kIGZvdXIgcmVwb3NpdG9yeSB2YWxpZGF0b3JzIFBBU1MnCiAgY3VtdWxhdGl2ZV91c2VkX2J1ZGdldDogJ3JlcGFpciBiYXRjaGVzIDMgKG9yaWdpbmFsIDIgcGx1cyBhdXRob3JpemVkIDEpOyB0YXJnZXRlZCByb3VuZHMgNSAob3JpZ2luYWwgMyBwbHVzIGF1dGhvcml6ZWQgMik7IGZ1bGwgc3VpdGUgcnVucyAyIChvcmlnaW5hbCAyIHBsdXMgYWRkaXRpb25hbCAwKTsgZXhhY3QgYmFzZWxpbmUgY29tcGFyaXNvbnMgMTsgYnJhbmNoZXMgMTsgY2FuZGlkYXRlIHBhdGhzIDEwJwogIHN0YXRlOiBzb3VyY2VfY29ycmVjdGlvbl9jb21wbGV0ZV93YWl0aW5nX2Zvcl9pbmRlcGVuZGVudF9yZXZpZXcKcjFfcjRfY29ycmVjdGlvbl9hdXRob3JpemF0aW9uOgogIHNvdXJjZTogRXhwbGljaXQgc2FtZS10YXNrIFIxLVI0IHVzZXIgYXV0aG9yaXphdGlvbjsgcmVzdW1lZCBhZnRlciBleGFjdCByZXZpZXcgcGFja2FnZSB0cmFuc2Zlci4gTm8gYWRkaXRpb25hbCBidWRnZXQgZnJvbSB0aGUgdHJhbnNmZXIgbWVzc2FnZS4KICByZXZpZXdfemlwOiAvdG1wL3RzLWIwMmEtcjFyNC1yZXZpZXcuUDJGS0tIWWwvdG9vbF9zeXN0ZW1fY3ViZXNhbmRib3hfZXhhY3RfY2FuZGlkYXRlX3Jldmlldy56aXAKICByZXZpZXdfemlwX3NoYTI1NjogZGE4ODQzZDIxZTVjMDI3YTM1NjY5OGZhZGY1YWIwZjVmOGQ1ZDdmN2I2ZmZiMGUyMDY0ODUxM2NiNmM0ZTFiMQogIGVudHJ5X3VzZWRfYnVkZ2V0OiAnY29ycmVjdGlvbiAzOyBkaXJlY3RlZCA1OyBmdWxsIHN1aXRlIDI7IGJhc2VsaW5lIGNvbXBhcmlzb24gMTsgYnJhbmNoZXMgMTsgY2FuZGlkYXRlIHBhdGhzIDEwJwogIGFkZGl0aW9uYWxfbGltaXRzOiAnY29ycmVjdGlvbiAxOyBkaXJlY3RlZCByb3VuZHMgMjsgZmluYWwgc3RhdGljL2dvdmVybmFuY2UgYmF0Y2ggMTsgZmluYWwgZXhwb3J0IDE7IGFjdGl2ZSB3b3JrIG1pbnV0ZXMgOTAgaW5jbHVkaW5nIHByZS10cmFuc2ZlciByZWFkLW9ubHkgd29yazsgZGVwZW5kZW5jeS9mdWxsLXN1aXRlL2Jhc2VsaW5lL2hvc3QvcHVibGljYXRpb24gb3BlcmF0aW9ucyAwJwogIHRpbWVfYWNjb3VudGluZzogJ1ByZS10cmFuc2ZlciBpbnNwZWN0aW9uIHVzZWQgYXBwcm94aW1hdGVseSA1IG1pbnV0ZXM7IGlucHV0LXdhaXQgaW50ZXJ2YWwgd2FzIHN0b3BwZWQsIHdpdGggbm8gd29yayBvciBidWRnZXQgY29uc3VtcHRpb24uIFJlc3VtZSAyMDI2LTA5LTA5IDA3OjM3OjI2IFVUQzsgcmV0YWluIHByaW9yIHVzYWdlLicKICByZWFkX2JlZm9yZV93cml0ZTogJ0FsbCB0ZW4gZGlzay9pbmRleC9leHBvcnQvcmV2aWV3IGNhbmRpZGF0ZSBieXRlcyBlcXVhbDsgSEVBRC90cmVlL2JyYW5jaCBhbmQgc2FmZSBwYXRjaCBpZGVudGl0eSBtYXRjaC4gQ3VycmVudCBjZW50cmFsIG1haW4gZml4ZWQgcGF0aHMsIGxvY2FsIHByaW5jaXBsZXMsIHBhcmVudCBzZWN0aW9ucyA2LTcsIGV4aXN0aW5nIGNvbnRyYWN0IHNlY3Rpb25zIDYtNywgb3JhY2xlIF9yZWFwL19zbmFwc2hvdC9fbmV0d29yaywgc2NoZW1hIHByb2Nlc3MvcmVzdG9yZS9ldmlkZW5jZSBhbmQgZXhhY3Qgc2V2ZW4gcmV2aWV3IGlucHV0cyByZWFkLicKICBmaXhlZF9jb3JyZWN0aW9uczoKICAgIC0gJ1IxX1BPU1RfT05MWV9SRUxBQkVMTElORyBhbmQgUjFfUE9TVF9PTkxZX0NST1NTX1JPVU5EOiBhYnNvcmIgZXhwbGljaXQgcHJlL2FjdGl2ZS9wb3N0IG93bmVyIG9yIHJlZmVyZW5jZSBvYnNlcnZhdGlvbnMgaW4gcGVyc2lzdGVudCBpbW11dGFibGUta2V5IGhpc3Rvcnk7IHByZXNlcnZlIGxhd2Z1bCBwcmUtZXhpc3Rpbmcgc2hhcmVkLXBvb2wgcmVsZWFzZS4nCiAgICAtICdSMl9GT1JFSUdOX1BPT0xfUkVGRVJFTkNFX0RFTEVURUQ6IHByb3RlY3QgZm9yZWlnbiBleGNsdXNpdmUgb3duZXJzIGFuZCBmb3JlaWduIHNoYXJlZCByZWZlcmVuY2VzIGluIGFjdGl2ZSBhbmQgcG9zdCwgYWxsb3dpbmcgdW5yZWxhdGVkIGJhY2tncm91bmQgY2hhbmdlcy4nCiAgICAtICdSM19SVU5USU1FX0VYRUNVVElPTl9KT0lOIGFuZCBSM19URVJNSU5BVElPTl9FWEVDVVRJT05fSk9JTjogam9pbiBzYW1lLW93bmVyIHRlcm1pbmF0aW9uIGFuZCBydW50aW1lIGV4ZWN1dGlvbnMgZm9yIGV2ZXJ5IGFwcGxpY2FibGUgY2FzZTsgZGlzdGluY3QgaW5kZXBlbmRlbnQgc2NlbmFyaW9zIHJlbWFpbiBkaXN0aW5jdC4nCiAgICAtICdSNF9SRVNUT1JFX0ZPUkVJR05fUFJPQ0VTUyBhbmQgUjRfUkVTVE9SRV9VTk9CU0VSVkVEX1BST0NFU1M6IGJpbmQgZWFjaCByZXN0b3JlIHRvIHR5cGVkIGhvc3QgcHJvY2VzcyBvYnNlcnZhdGlvbnMgYW5kIG93bmVyL2V4ZWN1dGlvbiwgcmVqZWN0IGZvcmVpZ24ga2V5cyBhbmQgYmxvY2sgbWlzc2luZyBvYnNlcnZhdGlvbnM7IG5vIHNlY29uZCB0ZXJtaW5hbCBkZXN0cm95IHJlcXVpcmVtZW50LicKICBwbGFubmVkX3JvdW5kczogJ0ZpcnN0OiBvcmlnaW5hbCAxMDcgcGx1cyBzZXZlbiBleGFjdCByZXZpZXctaW5wdXQgcmVncmVzc2lvbnMgYWdhaW5zdCB1bmNoYW5nZWQgb3JhY2xlL3NjaGVtYS9maXh0dXJlLiBUaGVuIG9uZSBjb3JyZWN0aW9uIGJhdGNoIGFuZCBmaW5hbCBjb21wbGV0ZSBkaXJlY3RlZCBzdWl0ZSwgaW5jbHVkaW5nIHN0cnVjdHVyYWwgbWlncmF0aW9uIGVxdWl2YWxlbmNlIGFuZCBkaXJlY3RseSByZWxhdGVkIHBvc2l0aXZlcy4nCiAgZmluYWxfc3RhdGljX2JhdGNoOiAnUnVmZiBjaGVjayBhbmQgZm9ybWF0IC0tY2hlY2sgb24gdGhlIHR3byBjb250cmFjdCBQeXRob24gZmlsZXM7IGV4aXN0aW5nIGFjdGl2ZS1nYXRlcywgcHJvY2Vzcy1hdXRob3JpdHksIG1vZHVsZS1yZWdpc3RyeSBhbmQgcmVwby1tYW5pZmVzdCB2YWxpZGF0b3JzOyBnaXQgZGlmZiAtLWNoZWNrLiBObyBmdWxsIHB5dGVzdCBvciBiYXNlbGluZSBjaGVja3MuJwogIHNjb3BlOiAnTW9kaWZ5IG9ubHkgZXhpc3RpbmcgY29udHJhY3QvZXZpZGVuY2Uvc2NoZW1hL29yYWNsZS9maXh0dXJlL2NvbnRyYWN0LXRlc3RzL29yaWdpbmFsIG1hbmlmZXN0L3BsYW4uIEtlZXAgUkVQT19NQU5JRkVTVC5tZCBhbmQgdGVzdHMvdGVzdF9yZXBvX21hbmlmZXN0LnB5IGJ5dGUtaWRlbnRpY2FsIHRvIGVudHJ5LicKICByZWNvcmRfcmV0ZW50aW9uOiAnQXBwZW5kIG9yaWdpbmFsIHN0ZG91dC9zdGRlcnIvZXhpdCwgc291cmNlIGhhc2hlcyBhbmQgZXhhY3QgdGVzdC10aW1lIHBhaXIgYnl0ZXMgdG8gZXhpc3RpbmcgZXZpZGVuY2UvZmluYWwgWklQOyByZXRhaW4gYWxsIG9yaWdpbmFsIGZhaWx1cmVzIGFuZCB1bmtub3duIGhpc3RvcmljYWwgMTQ0LWZpbGUvdGVzdC10aW1lLXBsYW4gYnl0ZXMuJwogIHRlcm1pbmFsOiAnT25lIGZpbmFsIHRlbi1maWxlIFpJUCBmb3IgaW5kZXBlbmRlbnQgcmV2aWV3OyBubyBmaW5hbCBzb3VyY2UgYWNjZXB0YW5jZSwgcmVhbCBiYWNrZW5kIGFjY2VwdGFuY2UsIGhvc3QgYXV0aG9yaXphdGlvbiBvciBuZXh0IHN0YWdlLicKICBzdGF0ZTogZXhhY3RfY291bnRlcmV4YW1wbGVzX3JlYWR5X2Zvcl9maXJzdF9kaXJlY3RlZF9yb3VuZAo="
  }
}
```

### Single correction batch and explicit fixture migration

R1 extends the existing immutable network-key history to explicit ownership/references from pre, active and every cleanup sample. Relabelling cannot erase history across samples or rounds. The existing pre-existing clean shared-pool baseline exception remains: a lease first seen in cleanup may return to that unchanged baseline and remain in later inventories. R2 protects both foreign exclusive owner and foreign sandbox_references in active and post. G4 still permits evidenced background changes; R5 unknown attribution remains outside this correction.

R3 uses one shared same-owner execution join in both G2 and G4 for every termination scenario, retaining distinct IDs for independent executions. Contradictions are EXECUTION_JOIN_MISMATCH/FAIL. G2 completeness, finite deadline, helper/FD conditions and optional PID1 positive control are unchanged.

R4 adds closed restore_process_observation records in the existing evidence schema, reusing the existing typed process definition. Each restore independently matches owner, execution, snapshot and canonical process birth keys. Known foreign identities cannot be overwritten by a later relabelled observation. Missing observed keys/coverage block; actual owner/execution/scope/identity contradictions fail. The first restore still joins its destroy evidence; the second is not required to add a termination case.

The fixture migration adds two synthetic restore_process_observations and replaces only the second restore's three previously unobserved display strings with canonical hashes of explicit new synthetic rows (host_boot_id synthetic-host-boot, PIDs 420/421/422, start_ticks 202, namespace synthetic-pidns, host scope, owner/execution of that restore). The first rows reuse the original first-restore VMM/controller/helper observation identities. Catalogs and all other base evidence stay unchanged. The clean-template test helper rebinds the new observation records alongside its existing owner/execution rebinding; original test assertions are retained.

Each of the seven final regressions projects out only these two documented structural changes and verifies equality to its original archived canonical input hash. R4's foreign and unobserved claim lists are never normalized away. Every migrated input must validate structurally and assert its specific semantic reason, excluding SCHEMA_VIOLATION. Additional controls exercise phase/reference history, legitimate pool return, foreign shared lease protection in both phases, all six execution joins, observation owner/execution/role/scope/completeness and both restore indices. All are pure fixture inputs. Formatting was a source edit within this single correction batch: `/snap/ruff/current/bin/ruff format --no-cache tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py`, stdout `2 files reformatted`, stderr empty, exit 0.

### Final verification plan frozen before execution

One final directed suite followed by one static/governance batch uses the existing protected dispatcher and original task pair. The batch contains Ruff check/format-check, the four existing repository validators and diff whitespace checking; no full suite, baseline or host checks. The retained source identity and exact test-time manifest/plan bytes accompany each raw receipt. After this run only evidence and result bookkeeping may change; no oracle, schema, fixture or test changes without a newly authorized test budget. Results are pending at this point and are not prefilled as PASS.


### Final R1–R4 directed and static/governance raw output

Protected dispatch and outer shell exit 0. Directed round 2/2: `160 passed in 10.05s`, exit 0, stderr empty. This comprises the original 107, seven exact review regressions and 46 directly related controls. All seven review inputs remain schema-valid and their old-form canonical input hashes remain equal to the package. Six return FAIL and the unobserved-process case returns BLOCKED, with exact semantic reasons; none is rejected for SCHEMA_VIOLATION. Ruff check/format-check, four existing repository validators, whitespace checking and original test-definition/scope comparison all exit 0. Forty original test function ASTs, including parametrization, are unchanged. Both manifest registration files are unchanged. The full raw receipt follows, including source hashes before/after and exact test-time pair bytes; no archived replay script selected the final oracle.

```json
{
  "status": "PASS",
  "preflight": {
    "process_authority_result": {
      "status": "PASS",
      "authority_path": "config/process_authority_v1.yaml",
      "module_id": "process-authority",
      "module_version": "2.3.0",
      "public_interface_id": "process-authority-api",
      "public_interface_version": "2.1.0",
      "current_task_input_mode": "explicit_manifest_change_plan_pair",
      "implicit_repository_index_allowed": false,
      "legacy_authority": false,
      "replay_result": {
        "status": "PASS",
        "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
        "pair_count": 108,
        "authority": false,
        "replay_only": true,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "production_deployment": false,
      "cleanup_execution": false,
      "reasons": []
    },
    "manifest_result": {
      "status": "PASS",
      "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "policy_path": "policy/repo_write_policy.yaml",
      "reasons": [],
      "autonomy_policy_path": "policy/autonomy_policy.yaml"
    },
    "pair_binding_result": {
      "status": "PASS",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "binding_mode": "explicit_manifest_change_plan_pair",
      "writes_target_repo": false,
      "executes_target_repo_mutation": false,
      "reasons": []
    },
    "change_plan_result": {
      "status": "PASS",
      "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
      "reasons": []
    },
    "replay_execution_requested": false,
    "validation_to_dispatch_inputs_equal": true
  },
  "input_sha256_before": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "ae0e6707f257e95f120a5bb253ab6b30cbc15e8caefd1fb207340883cc3d8274",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "ec72bf9fb18bad9e06138098eeae5a894c9212bc43c01ca9ccd546378a8e7969"
  },
  "input_sha256_after": {
    "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
    "change_plan": "ae0e6707f257e95f120a5bb253ab6b30cbc15e8caefd1fb207340883cc3d8274",
    "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
    "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
    "task_manifest": "ec72bf9fb18bad9e06138098eeae5a894c9212bc43c01ca9ccd546378a8e7969"
  },
  "command_results": [
    {
      "name": "python -B -m pytest -q -s --tb=short -p no:cacheprovider tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 0,
      "stdout": "...........................................................................................................R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R1_POST_ONLY_RELABELLING\", \"expected\": \"FAIL\", \"expected_reason\": \"0:SANDBOX_NETWORK_RESOURCE_LEAK\", \"input_schema_valid\": true, \"original_input_sha256\": \"1048073208a4b26913e5516f5c3b284863bc9e2b5bd23db9ac1f2d7f59181fad\", \"reasons\": [\"0:NETWORK_RELEASE_DEADLINE_UNPROVED\", \"0:SANDBOX_NETWORK_RESOURCE_LEAK\"]}\n.R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R1_POST_ONLY_CROSS_ROUND\", \"expected\": \"FAIL\", \"expected_reason\": \"1:SANDBOX_NETWORK_RESOURCE_LEAK\", \"input_schema_valid\": true, \"original_input_sha256\": \"5dcb5a2f405bb39e02c86de2f863b0506bdc84d6c92400026f7b2f4307d15066\", \"reasons\": [\"1:NETWORK_RELEASE_DEADLINE_UNPROVED\", \"1:SANDBOX_NETWORK_RESOURCE_LEAK\"]}\n.R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R2_FOREIGN_POOL_REFERENCE_DELETED\", \"expected\": \"FAIL\", \"expected_reason\": \"0:CROSS_SANDBOX_CONTAMINATION\", \"input_schema_valid\": true, \"original_input_sha256\": \"efac03e97399e11168142c808423b92db3b7c874f4b1222a06cd6f7c1ce2379d\", \"reasons\": [\"0:CROSS_SANDBOX_CONTAMINATION\"]}\n.R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R3_RUNTIME_EXECUTION_JOIN\", \"expected\": \"FAIL\", \"expected_reason\": \"1:EXECUTION_JOIN_MISMATCH\", \"input_schema_valid\": true, \"original_input_sha256\": \"1bd0433810452910837831ec1d9091d1697b25edddf1ea6213d7e3d3c94c850f\", \"reasons\": [\"1:EXECUTION_JOIN_MISMATCH\"]}\n.R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R3_TERMINATION_EXECUTION_JOIN\", \"expected\": \"FAIL\", \"expected_reason\": \"payload_sigkill:EXECUTION_JOIN_MISMATCH\", \"input_schema_valid\": true, \"original_input_sha256\": \"b892ce093b8bf5cd21b2424b3a64f0eaae2fc3d59afb598484951d328a83d779\", \"reasons\": [\"payload_sigkill:EXECUTION_JOIN_MISMATCH\"]}\n.R1_R4_RESULT {\"actual\": \"FAIL\", \"aggregate\": \"FAIL\", \"case\": \"R4_RESTORE_FOREIGN_PROCESS\", \"expected\": \"FAIL\", \"expected_reason\": \"RESTORE_PROCESS_FOREIGN_BINDING\", \"input_schema_valid\": true, \"original_input_sha256\": \"a9cc6e5cf6e37352ed4eace5123a77150ad9abe0c4004850eb8f279f2c14cdf2\", \"reasons\": [\"RESTORE_PROCESS_FOREIGN_BINDING\", \"RESTORE_PROCESS_OBSERVATION_MISSING\"]}\n.R1_R4_RESULT {\"actual\": \"BLOCKED\", \"aggregate\": \"BLOCKED\", \"case\": \"R4_RESTORE_UNOBSERVED_PROCESS\", \"expected\": \"BLOCKED\", \"expected_reason\": \"RESTORE_PROCESS_OBSERVATION_MISSING\", \"input_schema_valid\": true, \"original_input_sha256\": \"38fcd30c2424702e667402dbd90f7804e505caa31941b42999cf9ef96cf61ed4\", \"reasons\": [\"RESTORE_PROCESS_OBSERVATION_MISSING\"]}\n...............................................\n160 passed in 10.05s\n",
      "stderr": ""
    },
    {
      "name": "ruff check --no-cache tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 0,
      "stdout": "All checks passed!\n",
      "stderr": ""
    },
    {
      "name": "ruff format --check --no-cache tests/cubesandbox_contract_oracle.py tests/test_cubesandbox_backend_acceptance_contract.py",
      "exit_code": 0,
      "stdout": "2 files already formatted\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_active_gates tests/fixtures/manifest_validation/strict_active_gates_v1.yaml",
      "exit_code": 0,
      "stdout": "{\n  \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n  \"reasons\": [],\n  \"results\": [\n    {\n      \"autonomy_policy_path\": \"policy/autonomy_policy.yaml\",\n      \"kind\": \"task_manifest\",\n      \"manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n      \"policy_path\": \"policy/repo_write_policy.yaml\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"change_plan_path\": \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n      \"kind\": \"change_plan\",\n      \"reasons\": [],\n      \"status\": \"PASS\",\n      \"task_manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\"\n    },\n    {\n      \"alignment_gate_enabled\": false,\n      \"checked\": [],\n      \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n      \"kind\": \"alignment_gate\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    }\n  ],\n  \"status\": \"PASS\"\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_process_authority config/process_authority_v1.yaml",
      "exit_code": 0,
      "stdout": "{\n  \"authority_path\": \"config/process_authority_v1.yaml\",\n  \"cleanup_execution\": false,\n  \"current_task_input_mode\": \"explicit_manifest_change_plan_pair\",\n  \"executes_target_repo_mutation\": false,\n  \"implicit_repository_index_allowed\": false,\n  \"legacy_authority\": false,\n  \"module_id\": \"process-authority\",\n  \"module_version\": \"2.3.0\",\n  \"production_deployment\": false,\n  \"public_interface_id\": \"process-authority-api\",\n  \"public_interface_version\": \"2.1.0\",\n  \"reasons\": [],\n  \"replay_result\": {\n    \"authority\": false,\n    \"executes_target_repo_mutation\": false,\n    \"pair_count\": 108,\n    \"reasons\": [],\n    \"replay_only\": true,\n    \"snapshot_path\": \"/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml\",\n    \"status\": \"PASS\"\n  },\n  \"status\": \"PASS\",\n  \"writes_target_repo\": false\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_module_registry config/module_registry_v1.yaml --require-current-authority",
      "exit_code": 0,
      "stdout": "{\n  \"compatibility_adapter\": {\n    \"applied\": false,\n    \"authority\": false,\n    \"cache_registry\": false,\n    \"caller_boundary\": \"registry_loader_and_validator_entrypoints_only\",\n    \"current_formal_registry_owner\": \"config/module_registry_v1.yaml\",\n    \"generated_projection\": false,\n    \"mapping_owner_path\": \"docs/tool_system_module_registry_contract_v1.md\",\n    \"persistence\": \"none\",\n    \"persistent_projection\": false,\n    \"registry_files_read\": [\n      \"config/module_registry_v1.yaml\"\n    ],\n    \"second_registry_authority\": false,\n    \"second_schema_authority\": false,\n    \"serializes_projection\": false,\n    \"translation_boundary\": \"memory_only\"\n  },\n  \"contract_reference_count\": 253,\n  \"current_registry_authority\": true,\n  \"declared_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"execution_order\": [\n    \"agent-worker-runtime\",\n    \"blueprint-compiler\",\n    \"development-loop\",\n    \"durable-orchestrator\",\n    \"local-git\",\n    \"manifest-validation\",\n    \"architecture-registry\",\n    \"process-authority\",\n    \"ai-worker-runtime\",\n    \"adaptive-model-portfolio-and-economics\",\n    \"release-governance\",\n    \"operational-observability\",\n    \"record-retention\",\n    \"repository-context\",\n    \"repository-controller\",\n    \"cleanup-planner\",\n    \"state-migration\",\n    \"recovery-planning\",\n    \"subscription-capacity\",\n    \"production-readiness\",\n    \"target-repo-adapter\",\n    \"task-planner\",\n    \"role-runtime\",\n    \"worker-adapter\",\n    \"task-runner\",\n    \"cli-frontend\"\n  ],\n  \"external_provider_count\": 0,\n  \"module_count\": 26,\n  \"observed_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"owned_path_count\": 130,\n  \"reasons\": [],\n  \"registry_input_mode\": \"current_module_registry\",\n  \"registry_path\": \"config/module_registry_v1.yaml\",\n  \"required_owned_path_count\": 124,\n  \"status\": \"PASS\",\n  \"validation_scope\": \"tool_system_current_module_registry\"\n}\n",
      "stderr": ""
    },
    {
      "name": "python -B -m tool_system.cli.validate_repo_manifest REPO_MANIFEST.md",
      "exit_code": 0,
      "stdout": "{\n  \"cleanup_authorized\": false,\n  \"executes_target_repo_mutation\": false,\n  \"formal_execution_order\": [\n    \"docs/tool_system_global_development_principles_v1.md\",\n    \".gitignore\",\n    \"blueprint/schema/tool_system_blueprint.schema.json\",\n    \"pyproject.toml\",\n    \"blueprint/tool_system_v0.yaml\",\n    \"config/module_registry_schema_v1.json\",\n    \"config/module_registry_v1.yaml\",\n    \"docs/agent_role_taxonomy_v1.md\",\n    \"docs/model_provider_portfolio_and_economics_contract_v1.md\",\n    \"docs/operator_runbook_and_deprecation_policy_v1.md\",\n    \"docs/tool_system_module_registry_contract_v1.md\",\n    \"docs/tool_system_project_state_v1.yaml\",\n    \"harness/task_manifest.schema.json\",\n    \"policy/autonomy_policy.yaml\",\n    \"tests/fixtures/p14h/python_cli/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/python_cli/STATUS.md\",\n    \"tests/fixtures/p14h/python_cli/blueprint.yaml\",\n    \"tests/fixtures/p14h/typescript_package/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/typescript_package/STATUS.md\",\n    \"tests/fixtures/p14h/typescript_package/blueprint.yaml\",\n    \"tests/test_product_objective_alignment.py\",\n    \"tests/test_ts_b02a_core_local_os_isolation_backend_feasibility.py\",\n    \"config/process_authority_schema_v1.json\",\n    \"config/process_authority_v1.yaml\",\n    \"docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md\",\n    \"docs/modules/agent-worker-runtime-contract-v1.md\",\n    \"docs/modules/ai-worker-runtime-contract-v1.md\",\n    \"docs/modules/architecture-registry-contract-v1.md\",\n    \"docs/modules/blueprint-compiler-contract-v1.md\",\n    \"docs/modules/cleanup-planner-contract-v1.md\",\n    \"docs/modules/cli-frontend-contract-v1.md\",\n    \"docs/modules/development-loop-contract-v1.md\",\n    \"docs/modules/durable-orchestrator-contract-v1.md\",\n    \"docs/modules/local-git-contract-v1.md\",\n    \"docs/modules/manifest-validation-contract-v1.md\",\n    \"docs/modules/operational-observability-contract-v1.md\",\n    \"docs/modules/process-authority-contract-v1.md\",\n    \"docs/modules/production-readiness-contract-v1.md\",\n    \"docs/modules/record-retention-contract-v1.md\",\n    \"docs/modules/recovery-planning-contract-v1.md\",\n    \"docs/modules/release-governance-contract-v1.md\",\n    \"docs/modules/repository-context-contract-v1.md\",\n    \"docs/modules/repository-controller-contract-v1.md\",\n    \"docs/modules/role-runtime-contract-v1.md\",\n    \"docs/modules/state-migration-contract-v1.md\",\n    \"docs/modules/subscription-capacity-contract-v1.md\",\n    \"docs/modules/target-repo-adapter-contract-v1.md\",\n    \"docs/modules/task-planner-contract-v1.md\",\n    \"docs/modules/task-runner-contract-v1.md\",\n    \"docs/modules/worker-adapter-contract-v1.md\",\n    \"config/p15c_execution_packet_freeze_v1.yaml\",\n    \"config/p15d_failure_economics_corpus_prerequisite_v1.yaml\",\n    \"tests/test_p16a_sustainable_operations_specification.py\",\n    \"tests/test_phase_alignment.py\",\n    \"policy/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/src/calculator.py\",\n    \"tests/fixtures/p14h/typescript_package/package.json\",\n    \"tests/fixtures/p14h/typescript_package/src/index.ts\",\n    \"tests/fixtures/p14h/typescript_package/src/legacy.ts\",\n    \"tests/test_p14h_multi_stack_e2e.py\",\n    \"REPO_MANIFEST.md\",\n    \"config/replay_snapshot_v1.yaml\",\n    \"examples/requirements/tool_system_p7d.yaml\",\n    \"examples/task_graphs/tool_system_p7a_task_graph.yaml\",\n    \"src/tool_system/__init__.py\",\n    \"src/tool_system/agent_worker/__init__.py\",\n    \"src/tool_system/agent_worker/interface.py\",\n    \"src/tool_system/agent_worker/process_runtime.py\",\n    \"src/tool_system/ai_worker/__init__.py\",\n    \"src/tool_system/ai_worker/contract.py\",\n    \"src/tool_system/ai_worker/fixture_provider.py\",\n    \"src/tool_system/ai_worker/live_evidence.py\",\n    \"src/tool_system/ai_worker/live_provider.py\",\n    \"src/tool_system/architecture/__init__.py\",\n    \"src/tool_system/architecture/module_registry.py\",\n    \"src/tool_system/architecture/repo_manifest.py\",\n    \"src/tool_system/blueprint_compiler/__init__.py\",\n    \"src/tool_system/blueprint_compiler/compiler.py\",\n    \"src/tool_system/cleanup/__init__.py\",\n    \"src/tool_system/cleanup/residue_plan.py\",\n    \"src/tool_system/cli/__init__.py\",\n    \"src/tool_system/cli/cleanup_plan.py\",\n    \"src/tool_system/cli/controller_run.py\",\n    \"src/tool_system/cli/controller_self_check.py\",\n    \"src/tool_system/cli/evaluate_github_state.py\",\n    \"src/tool_system/cli/evaluate_repo_write.py\",\n    \"src/tool_system/cli/execute_change_plan.py\",\n    \"src/tool_system/cli/main.py\",\n    \"src/tool_system/cli/observe_main_ci.py\",\n    \"src/tool_system/cli/plan_requirement.py\",\n    \"src/tool_system/cli/plan_task_graph.py\",\n    \"src/tool_system/cli/run_batch.py\",\n    \"src/tool_system/cli/run_role_graph.py\",\n    \"src/tool_system/cli/run_stage.py\",\n    \"src/tool_system/cli/run_task.py\",\n    \"src/tool_system/cli/run_task_graph.py\",\n    \"src/tool_system/cli/target_repo_dry_run.py\",\n    \"src/tool_system/cli/target_repo_pr_plan_preview.py\",\n    \"src/tool_system/cli/validate_active_gates.py\",\n    \"src/tool_system/cli/validate_alignment_gate.py\",\n    \"src/tool_system/cli/validate_change_plan.py\",\n    \"src/tool_system/cli/validate_module_registry.py\",\n    \"src/tool_system/cli/validate_process_authority.py\",\n    \"src/tool_system/cli/validate_repo_manifest.py\",\n    \"src/tool_system/cli/validate_task_manifest.py\",\n    \"src/tool_system/development_loop/__init__.py\",\n    \"src/tool_system/gate/README.md\",\n    \"src/tool_system/gate/__init__.py\",\n    \"src/tool_system/gate/alignment_gate.py\",\n    \"src/tool_system/gate/change_plan.py\",\n    \"src/tool_system/gate/command_runner.py\",\n    \"src/tool_system/gate/test_gate.py\",\n    \"src/tool_system/local_git/__init__.py\",\n    \"src/tool_system/manifest/__init__.py\",\n    \"src/tool_system/manifest/task_manifest.py\",\n    \"src/tool_system/orchestrator/__init__.py\",\n    \"src/tool_system/planner/__init__.py\",\n    \"src/tool_system/planner/requirement_graph.py\",\n    \"src/tool_system/planner/task_graph.py\",\n    \"src/tool_system/policy/__init__.py\",\n    \"src/tool_system/policy/autonomy_policy.py\",\n    \"src/tool_system/policy/repo_write_policy.py\",\n    \"src/tool_system/process_authority/__init__.py\",\n    \"src/tool_system/process_authority/contract.py\",\n    \"src/tool_system/provider_portfolio/__init__.py\",\n    \"src/tool_system/provider_portfolio/fixtures.py\",\n    \"src/tool_system/repo_controller/__init__.py\",\n    \"src/tool_system/repo_controller/actions.py\",\n    \"src/tool_system/repo_controller/artifact.py\",\n    \"src/tool_system/repo_controller/audit_log.py\",\n    \"src/tool_system/repo_controller/controller.py\",\n    \"src/tool_system/repo_controller/controller_run.py\",\n    \"src/tool_system/repo_controller/github_state.py\",\n    \"src/tool_system/repo_controller/live_github_collector.py\",\n    \"src/tool_system/repo_controller/main_ci.py\",\n    \"src/tool_system/repo_controller/self_check.py\",\n    \"src/tool_system/repository_context/__init__.py\",\n    \"src/tool_system/repository_context/builder.py\",\n    \"src/tool_system/runner/active_gate_resolver.py\",\n    \"src/tool_system/runner/stage_runner.py\",\n    \"src/tool_system/runner/task_graph_runner.py\",\n    \"src/tool_system/runtime/__init__.py\",\n    \"src/tool_system/runtime/audit_bundle.py\",\n    \"src/tool_system/runtime/role_runtime.py\",\n    \"src/tool_system/runtime/transition_gate.py\",\n    \"src/tool_system/target_repo/__init__.py\",\n    \"src/tool_system/target_repo/dry_run_adapter.py\",\n    \"src/tool_system/target_repo/execution_approval.py\",\n    \"src/tool_system/target_repo/execution_state_snapshot.py\",\n    \"src/tool_system/target_repo/mutation_command_packet.py\",\n    \"src/tool_system/target_repo/p4c_preview_module.py\",\n    \"src/tool_system/target_repo/p4d_precheck.py\",\n    \"src/tool_system/target_repo/p5h_record.py\",\n    \"src/tool_system/target_repo/p5i_bundle.py\",\n    \"src/tool_system/target_repo/pr_plan_preview.py\",\n    \"src/tool_system/target_repo/state_collector.py\",\n    \"src/tool_system/target_repo/write_intent_record.py\",\n    \"src/tool_system/target_repo/write_packet.py\",\n    \"src/tool_system/worker_adapter/__init__.py\",\n    \"src/tool_system/worker_adapter/policy_gate.py\",\n    \"src/tool_system/development_loop/loop.py\",\n    \"src/tool_system/orchestrator/durable.py\",\n    \"src/tool_system/local_git/orchestrator.py\",\n    \"src/tool_system/production_readiness/__init__.py\",\n    \"src/tool_system/production_readiness/policy.py\",\n    \"src/tool_system/release_governance/__init__.py\",\n    \"src/tool_system/release_governance/policy.py\",\n    \"harness/cubesandbox_backend_acceptance_v1.schema.json\",\n    \"src/tool_system/runner/task_runner.py\",\n    \"src/tool_system/worker_adapter/contract.py\",\n    \"src/tool_system/worker_adapter/orchestration.py\",\n    \"examples/operator_config/tool_system_settings.example.toml\",\n    \"src/tool_system/ai_worker/p15c_controls.py\",\n    \"tests/test_p15c_execution_packet_freeze.py\",\n    \"tests/test_p15d_failure_economics_corpus_prerequisite.py\",\n    \"tests/fixtures/target_repo/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/tests/calculator_spec.py\",\n    \"tests/fixtures/p14h/typescript_package/tests/index.test.ts\",\n    \".github/workflows/tool-system-ci.yml\",\n    \"AGENTS.md\",\n    \"README.md\",\n    \"docs/process_authority_contract_v1.md\",\n    \"examples/batches/tool_system_batch_runner.yaml\",\n    \"examples/batches/tool_system_resolved_batch.yaml\",\n    \"examples/cleanup/tool_system_residue_state.yaml\",\n    \"examples/gate_decisions/pass.yaml\",\n    \"examples/github_states/tool_system_p3b_pass.yaml\",\n    \"examples/repo_write_decisions/tool_system_p3_pass.yaml\",\n    \"tests/fixtures/p11_worker_fixture.py\",\n    \"tests/test_active_gate_resolver.py\",\n    \"tests/test_active_gates.py\",\n    \"tests/test_agent_role_taxonomy.py\",\n    \"tests/test_agent_worker_interface.py\",\n    \"tests/test_ai_worker_contract.py\",\n    \"tests/test_ai_worker_fixture_provider.py\",\n    \"tests/test_ai_worker_live_provider.py\",\n    \"tests/test_alignment_gate.py\",\n    \"tests/test_audit_bundle.py\",\n    \"tests/test_blueprint_compiler.py\",\n    \"tests/test_change_plan_gate.py\",\n    \"tests/test_change_plan_scope_extra.py\",\n    \"tests/test_cleanup_plan.py\",\n    \"tests/test_command_runner.py\",\n    \"tests/test_controller_actions.py\",\n    \"tests/test_controller_run.py\",\n    \"tests/test_controller_self_check.py\",\n    \"tests/test_development_loop.py\",\n    \"tests/test_durable_orchestrator_recovery.py\",\n    \"tests/test_durable_orchestrator_side_effects.py\",\n    \"tests/test_durable_orchestrator_state.py\",\n    \"tests/test_execution_approval.py\",\n    \"tests/test_execution_state_snapshot.py\",\n    \"tests/test_final_record.py\",\n    \"tests/test_github_state_adapter.py\",\n    \"tests/test_global_principles.py\",\n    \"tests/test_live_github_collector.py\",\n    \"tests/test_local_git_orchestrator.py\",\n    \"tests/test_main_ci.py\",\n    \"tests/test_milestone_module_invariant.py\",\n    \"tests/test_module_contracts.py\",\n    \"tests/test_module_import_graph.py\",\n    \"tests/test_module_registry.py\",\n    \"tests/test_multi_task.py\",\n    \"tests/test_mutation_command_packet.py\",\n    \"tests/test_p10r_a_machine_policy_enforcement.py\",\n    \"tests/test_p13_integrated_security_reliability.py\",\n    \"tests/test_p14_phase_entry_contract.py\",\n    \"tests/test_p14c_execution_contract.py\",\n    \"tests/test_p4d_precheck.py\",\n    \"tests/test_process_authority.py\",\n    \"tests/test_process_worker_runtime_adversarial.py\",\n    \"tests/test_process_worker_runtime_execution.py\",\n    \"tests/test_process_worker_runtime_preflight.py\",\n    \"tests/test_provider_portfolio_fixtures.py\",\n    \"tests/test_repo_controller.py\",\n    \"tests/test_repo_manifest.py\",\n    \"tests/test_repository_context_builder.py\",\n    \"tests/test_requirement_graph.py\",\n    \"tests/test_role_runtime.py\",\n    \"tests/test_role_transition_gate.py\",\n    \"tests/test_root_cli.py\",\n    \"tests/test_runtime_audit_bundle.py\",\n    \"tests/test_stage_runner.py\",\n    \"tests/test_state_collector.py\",\n    \"tests/test_target_repo_dry_run.py\",\n    \"tests/test_target_repo_pr_plan_preview.py\",\n    \"tests/test_task_graph.py\",\n    \"tests/test_task_graph_runner.py\",\n    \"tests/test_task_manifest_policy.py\",\n    \"tests/test_worker_adapter_contract.py\",\n    \"tests/test_worker_adapter_orchestration.py\",\n    \"tests/test_worker_adapter_policy_gate.py\",\n    \"tests/test_write_intent.py\",\n    \"tests/test_write_packet.py\",\n    \"src/tool_system/ai_worker/runtime.py\",\n    \"src/tool_system/provider_portfolio/failure_control.py\",\n    \"tests/test_target_identity_decoupling.py\",\n    \"tests/test_durable_orchestrator_reliability.py\",\n    \"tests/test_production_readiness.py\",\n    \"src/tool_system/operational_observability/__init__.py\",\n    \"src/tool_system/state_migration/__init__.py\",\n    \"src/tool_system/subscription_capacity/__init__.py\",\n    \"src/tool_system/operational_observability/policy.py\",\n    \"src/tool_system/state_migration/planner.py\",\n    \"src/tool_system/subscription_capacity/policy.py\",\n    \"tests/test_release_governance.py\",\n    \"tests/cubesandbox_contract_oracle.py\",\n    \"tests/fixtures/cubesandbox_backend_acceptance_v1.json\",\n    \"tests/test_task_runner.py\",\n    \"examples/operator_config/tool_system_credentials.example.toml\",\n    \"src/tool_system/ai_worker/p15c_benchmark.py\",\n    \"tests/test_ai_worker_p15c_controls.py\",\n    \"tests/fixtures/target_repo/task_manifest.yaml\",\n    \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n    \"tests/test_central_governance_consumption.py\",\n    \"tests/test_model_provider_portfolio_contract.py\",\n    \"src/tool_system/process_authority/live_provider_approval.py\",\n    \"src/tool_system/provider_portfolio/provider_mode.py\",\n    \"tests/test_ai_worker_provider_mode.py\",\n    \"tests/test_provider_portfolio_failure_control.py\",\n    \"src/tool_system/record_retention/__init__.py\",\n    \"src/tool_system/recovery_planning/__init__.py\",\n    \"src/tool_system/record_retention/policy.py\",\n    \"tests/test_operational_observability.py\",\n    \"src/tool_system/recovery_planning/planner.py\",\n    \"tests/test_state_migration.py\",\n    \"tests/test_subscription_capacity.py\",\n    \"tests/test_cubesandbox_backend_acceptance_contract.py\",\n    \"src/tool_system/ai_worker/p15c_entry.py\",\n    \"tests/test_ai_worker_p15c_benchmark.py\",\n    \"tests/test_target_repo_dry_run_probe.py\",\n    \"tests/test_p14c_live_issuer.py\",\n    \"tests/test_provider_portfolio_provider_mode.py\",\n    \"tests/test_record_retention.py\",\n    \"tests/test_recovery_planning.py\",\n    \"tests/test_ai_worker_p15c_entry.py\",\n    \"tests/test_p15c_local_operator_config.py\"\n  ],\n  \"formal_file_count\": 299,\n  \"formal_path_count\": 299,\n  \"formal_set_count\": 0,\n  \"legacy_path_count\": 543,\n  \"legacy_set_count\": 6,\n  \"manifest_path\": \"REPO_MANIFEST.md\",\n  \"parser_mode\": \"exact_formal_files\",\n  \"reasons\": [],\n  \"retained_inputs_are_current_authority\": false,\n  \"status\": \"PASS\",\n  \"tracked_path_count\": 842,\n  \"unclassified_path_count\": 0,\n  \"writes_target_repo\": false\n}\n",
      "stderr": ""
    },
    {
      "name": "git --no-optional-locks --no-pager diff --check --no-ext-diff --no-textconv HEAD --",
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    }
  ],
  "subprocess_call_count": 8,
  "reasons": [],
  "source_sha256_before": {
    "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
    "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
    "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
    "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ec72bf9fb18bad9e06138098eeae5a894c9212bc43c01ca9ccd546378a8e7969",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ae0e6707f257e95f120a5bb253ab6b30cbc15e8caefd1fb207340883cc3d8274"
  },
  "source_sha256_after": {
    "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
    "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
    "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
    "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ec72bf9fb18bad9e06138098eeae5a894c9212bc43c01ca9ccd546378a8e7969",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ae0e6707f257e95f120a5bb253ab6b30cbc15e8caefd1fb207340883cc3d8274"
  },
  "exact_test_time_pair_base64": {
    "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "dGFza19pZDogdG9vbC1zeXN0ZW0tdHMtYjAyYS1jdWJlc2FuZGJveC12MDcwLWFybTY0LWJhY2tlbmQtYWNjZXB0YW5jZS1jb250cmFjdC12MQp0YXNrX3R5cGU6IHRlc3RfYWRkCnRhcmdldF9yZXBvOiBhcG9sbzE4My90b29sLXN5c3RlbQp0YXJnZXRfYnJhbmNoOiBhZ2VudC90cy1iMDJhLWN1YmVzYW5kYm94LXYwNzAtYWNjZXB0YW5jZS1jb250cmFjdC12MQpwaGFzZTogVFNfQjAyQV9DT05UUkFDVF9PTkxZCmFwcHJvdmVkX2JsdWVwcmludF9yZWZzOgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sCiAgICBzZWN0aW9uX29yX2tleTogcHJvZHVjdF9vYmplY3RpdmUKc2NvcGU6CiAgc3VtbWFyeTogRGVzaWduIGZvdXIgQ3ViZVNhbmRib3ggdjAuNy4wIEFSTTY0IGFjY2VwdGFuY2UgZ2F0ZXMgYW5kIHRlc3Qgb25seSBzeW50aGV0aWMgZXZpZGVuY2UsIHdpdGggbm8gYmFja2VuZCBleGVjdXRpb24gb3IgcHVibGljYXRpb24uCiAgaW5fc2NvcGU6CiAgICAtIEFwcGx5IG9ubHkgdGhlIGF1dGhvcml6ZWQgUjEtUjQgc2V2ZW4gZXhhY3QtaW5wdXQgY29ycmVjdGlvbnMgaW4gdGhlIHNhbWUgdGVuIHBhdGhzOyBwcmVzZXJ2ZSBvcmlnaW5hbCAxMDcgdGVzdCBzZW1hbnRpY3MgYW5kIGFsbCBoaXN0b3JpY2FsIGNvdW50cy4gTm8gUjUgY29ycmVjdGlvbiwgZnVsbCBzdWl0ZSwgYmFzZWxpbmUgcmVydW4gb3IgbmV3IGRlcGVuZGVuY3kuCiAgICAtIFJlYWQgZnJvemVuIHVwc3RyZWFtIHNvdXJjZSBhbmQgY3VycmVudCBjZW50cmFsIG1haW4gZm9ybWFsIHJ1bGVzLgogICAgLSBTcGVjaWZ5IGNvbXBvbmVudCBiaW5kaW5nLCBjb21wbGV0ZSByZWFwLCBzbmFwc2hvdCBpbnRlZ3JpdHksIGFuZCBhdHRyaWJ1dGVkIG5ldHdvcmsgY2xlYW51cC4KICAgIC0gQWRkIGEgbG9jYWwgSlNPTiBTY2hlbWEgYW5kIHRlc3Qtb25seSBwdXJlIG9yYWNsZSB1c2luZyBleGlzdGluZyBqc29uc2NoZW1hIGFuZCBweXRlc3QgbWVjaGFuaXNtcy4KICAgIC0gUmVnaXN0ZXIgZm9ybWFsIHRlc3QgYW5kIHNjaGVtYSBwYXRocyBpbiB0aGUgZXhpc3RpbmcgcmVwb3NpdG9yeSBtYW5pZmVzdC4KICAgIC0gU3luY2hyb25pemUgdGhlIGV4aXN0aW5nIGV4YWN0LWNvdW50IHJlcG9zaXRvcnktbWFuaWZlc3QgdGVzdCB3aXRoIHRoZSBmb3VyIGFkZGVkIGZvcm1hbCByb3dzLCBwcmVzZXJ2aW5nIGl0cyBjb3ZlcmFnZSBhbmQgcmVqZWN0aW9uIGNoZWNrcy4KICAgIC0gS2VlcCBvbmUgbG9jYWwgY2FuZGlkYXRlIGJyYW5jaCBhbmQgcmV0dXJuIGFuIHVuY29tbWl0dGVkIHJldmlld2FibGUgZGlmZi4KICAgIC0gQXBwbHkgdGhlIGV4cGxpY2l0bHkgYXV0aG9yaXplZCBzYW1lLXRhc2sgcmV2aWV3IGNvcnJlY3Rpb24gZm9yIG1hbmRhdG9yeSB0eXBlZCBhcnRpZmFjdHMsIGN1bXVsYXRpdmUgbmV0d29yayBvd25lcnNoaXAsIGNvbXBsZXRlIHJlYXAgc2FtcGxlcywgcnVudGltZSBkZW55X2FsbCBhbmQgZXhlY3V0aW9uLXNjb3BlZCByZXN0b3JlczsgcHJlc2VydmUgYWxsIHByaW9yIGJ1ZGdldHMgYW5kIGZhaWx1cmVzLgogIG91dF9vZl9zY29wZToKICAgIC0gQ3ViZVNhbmRib3ggaW5zdGFsbGF0aW9uLCBzZXJ2aWNlIG9yIHN5c3RlbWQgbXV0YXRpb24sIFZNIG9yIFZNTSBleGVjdXRpb24sIHJlYWwgc2FuZGJveCB3b3JrbG9hZCwgbmV0d29ya2luZyBvciBlQlBGIG11dGF0aW9uLgogICAgLSBDYW5vbmljYWwgbWFpbiB3cml0ZXMsIGNvbW1pdHMsIFBSIGNyZWF0aW9uLCBtZXJnZSwgcHVibGljYXRpb24sIGJhY2tlbmQgYWNjZXB0YW5jZSBvciBwcm9iZSBhdXRob3JpemF0aW9uLgogICAgLSBSdW50aW1lIGFkYXB0ZXIgaW1wbGVtZW50YXRpb24sIG5ldyBnb3Zlcm5hbmNlIGZyYW1ld29yaywgbW9kdWxlIG9yIHB1YmxpYyBpbnRlcmZhY2UsIHBlcm1pc3Npb24gY2hhbmdlcywgY2xlYW51cCBleGVjdXRpb24uCmV2aWRlbmNlOgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sCiAgICB3aHlfcmVsZXZhbnQ6IEJvdW5kZWQgaXNvbGF0ZWQgZGV2ZWxvcG1lbnQgYW5kIGluZGVwZW5kZW50bHkgb2JzZXJ2ZWQgZXZpZGVuY2UgcmVtYWluIHRoZSBnbG9iYWwgb2JqZWN0aXZlLgogIC0gcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KICAgIHBhdGg6IGRvY3MvcmVwb3J0cy9zdWJzY3JpcHRpb25fd29ya2VyX3RzX2IwMmFfZGd4X3NwYXJrX2xpbnV4X2FybTY0X3ByaW1hcnlfdGFyZ2V0X2FuZF9lcGhlbWVyYWxfa3ZtX2lzb2xhdGlvbl9wYXRoX3JlYWxpZ25tZW50X3NwZWNpZmljYXRpb25fdjEubWQKICAgIGNvbW1pdF9zaGE6IDMwNmEwMWZhNmJmM2JjOGVkNDIwNGI4OGFiZGNiNGYxNmY3NTM2MGUKICAgIGxpbmVfcmFuZ2U6IDQ5MC01NzAKICAgIHdoeV9yZWxldmFudDogRGlyZWN0IHBhcmVudCBzZXBhcmF0ZXMgc291cmNlIGRlc2lnbiwgcmVhZC1vbmx5IGludmVudG9yeSwgY29uZGl0aW9uYWwgZW5hYmxlbWVudCwgYW5kIGV4cGxpY2l0bHkgYXV0aG9yaXplZCBndWVzdCBwcm9iZS4KICAtIHJlcG86IFRlbmNlbnRDbG91ZC9DdWJlU2FuZGJveAogICAgcGF0aDogLmdpdGh1Yi93b3JrZmxvd3MvcmVsZWFzZS1kb2NrZXItaW1hZ2VzLnltbAogICAgY29tbWl0X3NoYTogZDAwODE2NDFjNTk4MjJlNGU1NjUzYjc0NjJlOTE0NDEwYjgxOTEwYQogICAgbGluZV9yYW5nZTogNzI1LTc0MAogICAgd2h5X3JlbGV2YW50OiBGcm96ZW4gQVJNNjQgc291cmNlIHdvcmtmbG93IGRpc2FibGVzIHB1Ymxpc2hlZCBwcm92ZW5hbmNlIGFuZCBTQk9NIGF0dGVzdGF0aW9ucy4KYWxsb3dlZF9maWxlczoKICAtIGRvY3MvcmVwb3J0cy90c19iMDJhX2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdF92MS5tZAogIC0gZG9jcy9yZXBvcnRzL3RzX2IwMmFfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxX2V2aWRlbmNlLm1kCiAgLSBoYXJuZXNzL2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV92MS5zY2hlbWEuanNvbgogIC0gdGVzdHMvZml4dHVyZXMvY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX3YxLmpzb24KICAtIHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weQogIC0gdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAtIGV4YW1wbGVzL3Rhc2tfbWFuaWZlc3RzL3Rvb2xfc3lzdGVtX3RzX2IwMmFfY3ViZXNhbmRib3hfYWNjZXB0YW5jZV9jb250cmFjdF92MS55YW1sCiAgLSBleGFtcGxlcy9jaGFuZ2VfcGxhbnMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKICAtIFJFUE9fTUFOSUZFU1QubWQKICAtIHRlc3RzL3Rlc3RfcmVwb19tYW5pZmVzdC5weQpmb3JiaWRkZW5fZmlsZXM6CiAgLSBzcmMvKioKICAtIGNvbmZpZy8qKgogIC0gcG9saWN5LyoqCiAgLSBibHVlcHJpbnQvKioKICAtIC5naXRodWIvKioKICAtIEFHRU5UUy5tZAogIC0gcHlwcm9qZWN0LnRvbWwKICAtIGRvY3MvdG9vbF9zeXN0ZW1fcHJvamVjdF9zdGF0ZV92MS55YW1sCndyaXRlX21vZGU6IHB1bGxfcmVxdWVzdAp2ZXJpZmljYXRpb246CiAgY29tbWFuZHM6CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLXMgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHJ1ZmYgZm9ybWF0IC0tY2hlY2sgdGVzdHMvY3ViZXNhbmRib3hfY29udHJhY3Rfb3JhY2xlLnB5IHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHJ1ZmYgY2hlY2sgLS1uby1jYWNoZSB0ZXN0cy9jdWJlc2FuZGJveF9jb250cmFjdF9vcmFjbGUucHkgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAgIC0gcnVmZiBmb3JtYXQgLS1jaGVjayAtLW5vLWNhY2hlIHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weSB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogICAgLSBnaXQgLS1uby1vcHRpb25hbC1sb2NrcyAtLW5vLXBhZ2VyIGRpZmYgLS1jaGVjayAtLW5vLWV4dC1kaWZmIC0tbm8tdGV4dGNvbnYgSEVBRCAtLQogICAgLSBweXRob24gLUIgLW0gcHl0ZXN0IC1xIC0tdGI9c2hvcnQgLXAgbm86Y2FjaGVwcm92aWRlciB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogICAgLSBweXRob24gLUIgLW0gcHl0ZXN0IC1xIC1wIG5vOmNhY2hlcHJvdmlkZXIgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAgIC0gcHl0aG9uIC1CIC1tIHB5dGVzdCAtcSAtcCBubzpjYWNoZXByb3ZpZGVyCiAgICAtIHJ1ZmYgY2hlY2sgdGVzdHMvY3ViZXNhbmRib3hfY29udHJhY3Rfb3JhY2xlLnB5IHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHB5dGhvbiAtQiAtbSB0b29sX3N5c3RlbS5jbGkudmFsaWRhdGVfYWN0aXZlX2dhdGVzIHRlc3RzL2ZpeHR1cmVzL21hbmlmZXN0X3ZhbGlkYXRpb24vc3RyaWN0X2FjdGl2ZV9nYXRlc192MS55YW1sCiAgICAtIHB5dGhvbiAtQiAtbSB0b29sX3N5c3RlbS5jbGkudmFsaWRhdGVfcHJvY2Vzc19hdXRob3JpdHkgY29uZmlnL3Byb2Nlc3NfYXV0aG9yaXR5X3YxLnlhbWwKICAgIC0gcHl0aG9uIC1CIC1tIHRvb2xfc3lzdGVtLmNsaS52YWxpZGF0ZV9tb2R1bGVfcmVnaXN0cnkgY29uZmlnL21vZHVsZV9yZWdpc3RyeV92MS55YW1sIC0tcmVxdWlyZS1jdXJyZW50LWF1dGhvcml0eQogICAgLSBweXRob24gLUIgLW0gdG9vbF9zeXN0ZW0uY2xpLnZhbGlkYXRlX3JlcG9fbWFuaWZlc3QgUkVQT19NQU5JRkVTVC5tZAogICAgLSBnaXQgZGlmZiAtLWNoZWNrCiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfZHVyYWJsZV9vcmNoZXN0cmF0b3JfcmVsaWFiaWxpdHkucHk6OnRlc3RfdGV4dF9hbmRfanNvbl9yZXNvdXJjZV9ib3VuZHNfZmFpbF9iZWZvcmVfbXV0YXRpb24gdGVzdHMvdGVzdF9kdXJhYmxlX29yY2hlc3RyYXRvcl9yZWxpYWJpbGl0eS5weTo6dGVzdF9kYXRhYmFzZV9wYXJlbnRfaWRlbnRpdHlfc3Vic3RpdHV0aW9uX2lzX2RldGVjdGVkIHRlc3RzL3Rlc3RfcDE0aF9tdWx0aV9zdGFja19lMmUucHk6OnRlc3RfdHlwZXNjcmlwdF9sYW5ndWFnZV9uZXV0cmFsX2Zsb3dfcmVjb3Jkc19hZGRfbW9kaWZ5X2RlbGV0ZQogIHBhc3NfY29uZGl0aW9uczoKICAgIC0gQWxsIGZvdXIgZ2F0ZSBzcGVjaWZpY2F0aW9ucyBhbmQgZXhhY3QgcmVxdWVzdGVkIHBvc2l0aXZlIGFuZCBuZWdhdGl2ZSBmaXh0dXJlIGFzc2VydGlvbnMgcGFzcy4KICAgIC0gU3ludGhldGljIFBBU1MgbmV2ZXIgYXV0aG9yaXplcyByZWFsIGJhY2tlbmQgYWNjZXB0YW5jZTsgdGhlIGNhbmRpZGF0ZSBsaWZlY3ljbGUtbWFuYWdlciBkaWdlc3QgcmVtYWlucyBudWxsIGFuZCBHMSBCTE9DS0VELgogICAgLSBPbmx5IHRoZSB0ZW4gbGlzdGVkIHBhdGhzIGRpZmZlcjsgY2Fub25pY2FsIG1haW4sIHJ1bnRpbWUsIGF1dGhvcml0eSBjb250cmFjdHMgYW5kIHB1YmxpYyBpbnRlcmZhY2VzIGFyZSB1bmNoYW5nZWQuCnJvbGxiYWNrOgogIG1ldGhvZDogcGF0Y2hfcmV2ZXJzZQogIHJlZmVyZW5jZTogUmV2ZXJzZSBvbmx5IHRoaXMgdGVuLXBhdGggY2FuZGlkYXRlIGRpZmYgYWdhaW5zdCAzMDZhMDFmYTZiZjNiYzhlZDQyMDRiODhhYmRjYjRmMTZmNzUzNjBlIGFmdGVyIHJldmlldzsgbm8gYXV0b21hdGljIGNsZWFudXAgb3IgbWFpbiByZXNldC4KYXBwcm92YWw6CiAgcmVxdWlyZWQ6IHRydWUKICBhcHByb3ZlZF9ieTogYXBvbG8xODMKICBhcHByb3ZhbF9zb3VyY2U6IEN1cnJlbnQgdXNlciB0YXNrIFRPT0wtU1lTVEVNLVRTLUIwMkEtQ1VCRVNBTkRCT1gtVjA3MC1BUk02NC1CQUNLRU5ELUFDQ0VQVEFOQ0UtQ09OVFJBQ1QtdjE7IGxvY2FsIHNvdXJjZS9kb2MvZml4dHVyZSB3b3JrIG9ubHksIHB1YmxpY2F0aW9uIGV4cGxpY2l0bHkgcHJvaGliaXRlZC4KICBhcHByb3ZlZF9hdDogMjAyNi0wOS0wOCBBdXN0cmFsaWEvQWRlbGFpZGU7IGRhdGUtbGV2ZWwgdGFzayBhdXRob3JpemF0aW9uCg==",
    "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "cGxhbl9pZDogdG9vbC1zeXN0ZW0tdHMtYjAyYS1jdWJlc2FuZGJveC12MDcwLWFybTY0LWJhY2tlbmQtYWNjZXB0YW5jZS1jb250cmFjdC12MQp0YXJnZXRfcmVwbzogYXBvbG8xODMvdG9vbC1zeXN0ZW0KdGFza19tYW5pZmVzdDogZXhhbXBsZXMvdGFza19tYW5pZmVzdHMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKYmFzZWxpbmU6CiAgY29tbWl0OiAzMDZhMDFmYTZiZjNiYzhlZDQyMDRiODhhYmRjYjRmMTZmNzUzNjBlCiAgdHJlZTogZWM3NGFmMTA4YjZmMWQ3ZDRjOWM3ZTQ0MGFlYzEyODI2MWYzZjI1MQogIG9yaWdpbmFsX2xvY2FsX21haW46IDAyN2RiYjNmYjgzYzM4ZGVmNzBlODFkNTg3MTJmODBkYmU2MTM0ODMKYnJhbmNoOiBhZ2VudC90cy1iMDJhLWN1YmVzYW5kYm94LXYwNzAtYWNjZXB0YW5jZS1jb250cmFjdC12MQphbGlnbm1lbnQ6CiAgcGFyZW50OiBkb2NzL3JlcG9ydHMvc3Vic2NyaXB0aW9uX3dvcmtlcl90c19iMDJhX2RneF9zcGFya19saW51eF9hcm02NF9wcmltYXJ5X3RhcmdldF9hbmRfZXBoZW1lcmFsX2t2bV9pc29sYXRpb25fcGF0aF9yZWFsaWdubWVudF9zcGVjaWZpY2F0aW9uX3YxLm1kIHNlY3Rpb25zIDktMTE7IGRlZmluZSBldmlkZW5jZSBvbmx5IGFuZCBwcmVzZXJ2ZSBmdXR1cmUgcHJvYmUgYXV0aG9yaXphdGlvbi4KICBnbG9iYWw6IGJsdWVwcmludC90b29sX3N5c3RlbV92MC55YW1sOnByb2R1Y3Rfb2JqZWN0aXZlOyBib3VuZGVkIGlzb2xhdGVkIGRldmVsb3BtZW50LCBubyBzaWxlbnQgYXV0aG9yaXR5IG9yIHJ1bnRpbWUgZXhwYW5zaW9uLgpjaGFuZ2VkX2ZpbGVzOgogIC0gZG9jcy9yZXBvcnRzL3RzX2IwMmFfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLm1kCiAgLSBkb2NzL3JlcG9ydHMvdHNfYjAyYV9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3RfdjFfZXZpZGVuY2UubWQKICAtIGhhcm5lc3MvY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX3YxLnNjaGVtYS5qc29uCiAgLSB0ZXN0cy9maXh0dXJlcy9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfdjEuanNvbgogIC0gdGVzdHMvY3ViZXNhbmRib3hfY29udHJhY3Rfb3JhY2xlLnB5CiAgLSB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogIC0gZXhhbXBsZXMvdGFza19tYW5pZmVzdHMvdG9vbF9zeXN0ZW1fdHNfYjAyYV9jdWJlc2FuZGJveF9hY2NlcHRhbmNlX2NvbnRyYWN0X3YxLnlhbWwKICAtIGV4YW1wbGVzL2NoYW5nZV9wbGFucy90b29sX3N5c3RlbV90c19iMDJhX2N1YmVzYW5kYm94X2FjY2VwdGFuY2VfY29udHJhY3RfdjEueWFtbAogIC0gUkVQT19NQU5JRkVTVC5tZAogIC0gdGVzdHMvdGVzdF9yZXBvX21hbmlmZXN0LnB5CmZpbGVfZGlzcG9zaXRpb246CiAgZXhpc3RpbmdfZmlsZTogUkVQT19NQU5JRkVTVC5tZAogIHJlZ2lvbjogRm9ybWFsIEZpbGVzIGFuZCBSZXRhaW5lZCBOb24tQXV0aG9yaXR5IFNldHMgdGFibGVzCiAgYWN0aW9uOiBBZGQgb25seSBmb3VyIGZvcm1hbCBzY2hlbWEvdGVzdC9maXh0dXJlIHJvd3M7IGV4aXN0aW5nIHJldGFpbmVkIGdsb2JzIGNvdmVyIHRoZSB0d28gcmVwb3J0cyBhbmQgZXhwbGljaXQgcGFpci4gTm8gcmVjbGFzc2lmaWNhdGlvbiBvciBjbGVhbnVwLgogIGRlcGVuZGVudF90ZXN0OiB0ZXN0cy90ZXN0X3JlcG9fbWFuaWZlc3QucHkgbGluZXMgMTA5LTE0MzsgY2hhbmdlIG9ubHkgdGhlIHR3byBleGFjdCBmb3JtYWwtcm93IGNvdW50IGFzc2VydGlvbnMgZnJvbSAyOTUgdG8gMjk5IGFmdGVyIHJlYWRpbmcgdGhlIGZpcnN0IGZ1bGwtc3VpdGUgZmFpbHVyZS4Kc2NvcGVfY29ycmVjdGlvbjoKICByZWFzb246IFRoZSBmb3VyIG5ldyBmb3JtYWwgcm93cyByZXF1aXJlIHRoZSBleGlzdGluZyByZXBvc2l0b3J5LW1hbmlmZXN0IHRlc3QgdG8gYXNzZXJ0IHRoZSBuZXcgZXhhY3QgY291bnQuIERvY3VtZW50IHRoaXMgaW1tZWRpYXRlIGRlcGVuZGVuY3kgYmVmb3JlIGVkaXRpbmcgaXQ7IG5vIGFjY2VwdGFuY2Ugc2NvcGUgb3IgcnVudGltZSBhdXRob3JpdHkgY2hhbmdlcy4KICBjaGFuZ2VkX3BhdGhfY291bnRfYmVmb3JlOiA5CiAgY2hhbmdlZF9wYXRoX2NvdW50X2FmdGVyOiAxMAogIGZpcnN0X2Z1bGxfc3VpdGU6IDQgZmFpbGVkLCA5NjQgcGFzc2VkIGluIDcyLjM2czsgbWFuaWZlc3QgY291bnQgZmFpbHVyZSBpcyBjYW5kaWRhdGUtY2F1c2VkLCB0d28gZHVyYWJpbGl0eSBmYWlsdXJlcyByZWplY3QgZ3JvdXAtd3JpdGFibGUgZml4dHVyZSBkaXJlY3RvcmllcywgYW5kIHRoZSBUeXBlU2NyaXB0IGZpeHR1cmUgY2Fubm90IGZpbmQgbm9kZS4KICByZXBhaXJfY3ljbGU6IDEgb2YgMjsgc3luY2hyb25pemUgZXhhY3QgY291bnRzIGFuZCBmaXggdGhyZWUgbmV3LWZpbGUgbGludCBkaWFnbm9zdGljcyBvbmx5LiBEbyBub3QgcmVwYWlyIHRoZSBob3N0IG9yIGV4aXN0aW5nIGR1cmFiaWxpdHkvVHlwZVNjcmlwdCBpbXBsZW1lbnRhdGlvbi4KZmluYWxfYm91bmRhcnlfY29ycmVjdGlvbjoKICByZXBhaXJfY3ljbGU6IDIgb2YgMgogIHJlYXNvbjogRzQgcmVxdWlyZXMgdHdvIGNsZWFuIHNhbXBsZXMgYnkgdGhlIGRlYWRsaW5lLiBBIGZpcnN0IGNsZWFuIHNhbXBsZSBleGFjdGx5IGF0IHRoZSBkZWFkbGluZSBtdXN0IGJlIEZBSUwsIG5vdCBCTE9DS0VELiBBZGQgYSBzeW50aGV0aWMgcmVncmVzc2lvbiBiZWZvcmUgY29ycmVjdGluZyB0aGlzIGJyYW5jaDsgcHJlc2VydmUgdGhlIGV4aXN0aW5nIGFmdGVyLWRlYWRsaW5lIEZBSUwuCiAgZmlsZXM6IHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weSBmaW5hbCBjbGVhbi1zYW1wbGUgdmVyZGljdDsgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkgbmV0d29yayBkZWFkbGluZSBjYXNlcy4KICB2YWxpZGF0aW9uX2J1ZGdldDogVXNlIGZvY3VzZWQgcnVucyAyIGFuZCAzIGZvciByZWdyZXNzaW9uIHRoZW4gcmVwYWlyLiBCb3RoIGZ1bGwtc3VpdGUgcnVucyBhcmUgc3BlbnQ7IGRvIG5vdCByZXJ1biB0aGVtIG9yIHJlcGFpciB1bnJlbGF0ZWQgaG9zdCBwcmVyZXF1aXNpdGVzLgpyZXVzZToKICAtIFVzZSBleGlzdGluZyBqc29uc2NoZW1hIERyYWZ0MjAyMDEyVmFsaWRhdG9yLCBweXRlc3QgYW5kIGV4cGxpY2l0IHRhc2stcGFpci9wcm9jZXNzLWF1dGhvcml0eSB2YWxpZGF0aW9uLgogIC0gVGhlIGNvbW1hbmQgdGVzdCBnYXRlIG9ubHkgZXZhbHVhdGVzIGNvbW1hbmQgZXhpdHMgYW5kIGNhbm5vdCBkZWNpZGUgaG9zdCBhY2NlcHRhbmNlLiBEbyBub3QgZmVlZCBob3N0IGNsYWltcyBpbnRvIGl0LgogIC0gVGhlIHByb2R1Y3Rpb24tcmVhZGluZXNzIGRlY2lzaW9uIGlzIFAxNi1zcGVjaWZpYyBhbmQgZ3JhbnRzIG5vIGJhY2tlbmQgZXZpZGVuY2Ugc2VtYW50aWNzOyBwcmVzZXJ2ZSBpdC4KICAtIEV4aXN0aW5nIElzb2xhdGlvblJlcXVlc3RWMSBhbmQgRXhlY3V0aW9uRXZpZGVuY2VWMSBvd25lcnNoaXAgcmVtYWlucyB3aXRoIGZ1dHVyZSBUUy1CMDJBL0IvQzsgdGhpcyBpcyBhIHRlc3Qtb25seSBjb250cmFjdCBzcGVjaWFsaXphdGlvbiwgbm90IGEgcnVudGltZSBvciBuZXcgcHVibGljIGludGVyZmFjZS4KICAtIFJldXNlIHRoZSBwdWJsaWMgRnJvemVuRGV2ZWxvcG1lbnRDb250cmFjdCBhbmQgZGV2ZWxvcG1lbnQtbG9vcCBWYWxpZGF0b3IgY2FsbGJhY2s7IGV4aXN0aW5nIHRhc2stcnVubmVyIGV4ZWN1dGlvbi1iaW5kaW5nLXYyIGV2aWRlbmNlIG9ibGlnYXRpb25zIGFuZCBydW5uZXItaXNzdWVkIHJlY2VpcHRzIHJlbWFpbiB0aGUgc29sZSBjb2RlLWRldmVsb3BtZW50IHJlY2VpcHQgZnJhbWV3b3JrLCB1bmNoYW5nZWQuCmJ1ZGdldHM6CiAgYnJhbmNoX2NvdW50OiAxCiAgY2hhbmdlZF9wYXRoX2NvdW50OiAxMAogIHJlcGFpcl9jeWNsZXM6IDIKICBmb2N1c2VkX3Rlc3RfcnVuczogMwogIGZ1bGxfc3VpdGVfcnVuczogMgogIHdhbGxfbWludXRlc19mcm9tX3Njb3BlX2ZyZWV6ZTogOTAKICBleHRlcm5hbF9yZXZpZXdfY3ljbGVzOiAwCiAgcGFpZF9hcGlfY2FsbHM6IDAKICByZWFsX2JhY2tlbmRfb3BlcmF0aW9uczogMAogIHB1YmxpY2F0aW9uX29wZXJhdGlvbnM6IDAKdmFsaWRhdGlvbl9lbnZpcm9ubWVudDoKICBjd2Q6IC9ob21lL3JpY2gvcHJvamVjdHMvdG9vbC1zeXN0ZW0KICBweXRob246IC9ob21lL3JpY2gvLnB5ZW52L3ZlcnNpb25zLzMuMTQuMy9iaW4vcHl0aG9uCiAgUFlUSE9ORE9OVFdSSVRFQllURUNPREU6ICcxJwogIFBZVEhPTlBBVEg6IHNyYzovdG1wL3RzLWIwMmEtY3ViZXNhbmRib3gtY29udHJhY3QtdjEtZGVwcwogIHRlbXBvcmFyeV9kZXBlbmRlbmN5X2V4Y2VwdGlvbjogRXhpc3RpbmcgcGlubmVkIGpzb25zY2hlbWEgYW5kIGl0cyBkZXBlbmRlbmNpZXMgY29waWVkIGZyb20gbG9jYWwgd2hlZWxob3VzZSBpbnRvIHRoaXMgdGFzay1vbmx5IC90bXAgZGlyZWN0b3J5OyByZXRhaW5lZCBmb3IgcmV2aWV3LCBubyBzeXN0ZW0gZW52aXJvbm1lbnQgb3IgQ3ViZVNhbmRib3ggaW5zdGFsbGF0aW9uLiBJbml0aWFsIG5ldHdvcmsgYXR0ZW1wdCBpbnRlcnJ1cHRlZCBhZnRlciBzYW5kYm94IGRlbmlhbDsgcmV0YWluIGl0cyBmYWlsdXJlIGluIGV2aWRlbmNlLgp2ZXJpZmljYXRpb246CiAgY29tbWFuZHM6CiAgICAtIHB5dGhvbiAtQiAtbSBweXRlc3QgLXEgLXMgLS10Yj1zaG9ydCAtcCBubzpjYWNoZXByb3ZpZGVyIHRlc3RzL3Rlc3RfY3ViZXNhbmRib3hfYmFja2VuZF9hY2NlcHRhbmNlX2NvbnRyYWN0LnB5CiAgICAtIHJ1ZmYgY2hlY2sgLS1uby1jYWNoZSB0ZXN0cy9jdWJlc2FuZGJveF9jb250cmFjdF9vcmFjbGUucHkgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICAgIC0gcnVmZiBmb3JtYXQgLS1jaGVjayAtLW5vLWNhY2hlIHRlc3RzL2N1YmVzYW5kYm94X2NvbnRyYWN0X29yYWNsZS5weSB0ZXN0cy90ZXN0X2N1YmVzYW5kYm94X2JhY2tlbmRfYWNjZXB0YW5jZV9jb250cmFjdC5weQogICAgLSBweXRob24gLUIgLW0gdG9vbF9zeXN0ZW0uY2xpLnZhbGlkYXRlX2FjdGl2ZV9nYXRlcyB0ZXN0cy9maXh0dXJlcy9tYW5pZmVzdF92YWxpZGF0aW9uL3N0cmljdF9hY3RpdmVfZ2F0ZXNfdjEueWFtbAogICAgLSBweXRob24gLUIgLW0gdG9vbF9zeXN0ZW0uY2xpLnZhbGlkYXRlX3Byb2Nlc3NfYXV0aG9yaXR5IGNvbmZpZy9wcm9jZXNzX2F1dGhvcml0eV92MS55YW1sCiAgICAtIHB5dGhvbiAtQiAtbSB0b29sX3N5c3RlbS5jbGkudmFsaWRhdGVfbW9kdWxlX3JlZ2lzdHJ5IGNvbmZpZy9tb2R1bGVfcmVnaXN0cnlfdjEueWFtbCAtLXJlcXVpcmUtY3VycmVudC1hdXRob3JpdHkKICAgIC0gcHl0aG9uIC1CIC1tIHRvb2xfc3lzdGVtLmNsaS52YWxpZGF0ZV9yZXBvX21hbmlmZXN0IFJFUE9fTUFOSUZFU1QubWQKICAgIC0gZ2l0IC0tbm8tb3B0aW9uYWwtbG9ja3MgLS1uby1wYWdlciBkaWZmIC0tY2hlY2sgLS1uby1leHQtZGlmZiAtLW5vLXRleHRjb252IEhFQUQgLS0KY29tcGxldGVkX3ZhbGlkYXRpb25fYmF0Y2g6CiAgZm9jdXNlZF9jb21tYW5kOiBweXRob24gLUIgLW0gcHl0ZXN0IC1xIC1wIG5vOmNhY2hlcHJvdmlkZXIgdGVzdHMvdGVzdF9jdWJlc2FuZGJveF9iYWNrZW5kX2FjY2VwdGFuY2VfY29udHJhY3QucHkKICByZXN1bHQ6IDU2IHBhc3NlZCBpbiAyLjU3czsgZXhpdCAwOyBwcm90ZWN0ZWQgaW5wdXQgYnl0ZXMgZXF1YWwgYmVmb3JlIGRpc3BhdGNoLgogIGZ1bGxfc3VpdGVfMTogNCBmYWlsZWQsIDk2NCBwYXNzZWQgaW4gNzIuMzZzOyBleGl0IDE7IG9yaWdpbmFsIGxpbnQgZmFpbGVkIHdpdGggMyBkaWFnbm9zdGljczsgYWxsIGZvdXIgcmVwb3NpdG9yeSB2YWxpZGF0b3JzIHBhc3NlZC4KICBmdWxsX3N1aXRlXzI6IDMgZmFpbGVkLCA5NjUgcGFzc2VkIGluIDcxLjUyczsgZXhpdCAxOyBsaW50IGFuZCBhbGwgZm91ciByZXBvc2l0b3J5IHZhbGlkYXRvcnMgcGFzc2VkLiBSZW1haW5pbmcgZmFpbHVyZXMgYXJlIHR3byBncm91cC13cml0YWJsZSBmaXh0dXJlLWRpcmVjdG9yeSBjaGVja3MgYW5kIG1pc3Npbmcgbm9kZSBpbiB0aGUgdmFsaWRhdGlvbiBQQVRILgpyb2xsYmFjazoKICBtZXRob2Q6IHBhdGNoX3JldmVyc2UKICByZWZlcmVuY2U6IFJldmVyc2Ugb25seSB0aGUgdGVuLXBhdGggY2FuZGlkYXRlIHBhdGNoIGFmdGVyIHJldmlldzsgcHJlc2VydmUgb3JpZ2luYWwgbG9jYWwgbWFpbiBhbmQgYWxsIGV4aXN0aW5nIGV2aWRlbmNlLgpzdG9wOgogIHRlcm1pbmFsOiBSZXZpZXdhYmxlIGxvY2FsIGNvbnRyYWN0IHdpdGggZml4dHVyZSByZXN1bHRzIGFuZCBleHBsaWNpdCByZWFsLWhvc3QgYmxvY2tlcnM7IHN0b3AgZm9yIGluZGVwZW5kZW50IHJldmlldy4KICBvbl9zY29wZV9kcmlmdDogdHJ1ZQogIG9uX2J1ZGdldF9leGhhdXN0aW9uOiB0cnVlCiAgb25fcmVwZWF0ZWRfbm9fcHJvZ3Jlc3M6IHRydWUKICBjb21taXQ6IGZhbHNlCiAgcHVsbF9yZXF1ZXN0OiBmYWxzZQogIG1lcmdlOiBmYWxzZQogIHJlYWxfYmFja2VuZF9hY2NlcHRhbmNlX2F1dGhvcml6ZWQ6IGZhbHNlCnJldmlld19jb3JyZWN0aW9uX2F1dGhvcml6YXRpb246CiAgc291cmNlOiBFeHBsaWNpdCBzYW1lLXRhc2sgdXNlciBjb250aW51YXRpb24gYWZ0ZXIgaW5kZXBlbmRlbnQgc291cmNlIHJldmlldzsgbm8gbmV3IGJyYW5jaCwgdGFzayBpZGVudGl0eSwgZnJhbWV3b3JrIG9yIHBhdGguCiAgcHJlc2VydmVkX3VzZWRfYnVkZ2V0OiAncmVwYWlyIDIvMjsgZm9jdXNlZCAzLzM7IGZ1bGwgc3VpdGUgMi8yOyBicmFuY2ggMS8xOyBleGFjdCBwYXRocyAxMC8xMCcKICBhZGRpdGlvbmFsX2J1ZGdldDogJ29uZSBjb3JyZWN0aW9uIGJhdGNoOyB0d28gdGFyZ2V0ZWQgcm91bmRzIChjb3VudGVyZXhhbXBsZXMgdGhlbiBmaW5hbCByZWdyZXNzaW9uKTsgYXQgbW9zdCBvbmUgZXhhY3QtYmFzZSBjb21wYXJpc29uIG9mIHRoZSB0aHJlZSBoaXN0b3JpY2FsIGZhaWx1cmVzOyBhdCBtb3N0IG9uZSBmdWxsIHN1aXRlIG9ubHkgaWYgZXhpc3RpbmcgZW52aXJvbm1lbnQgcHJlcmVxdWlzaXRlcyBwYXNzJwogIHJlYWRzX2JlZm9yZV93cml0ZTogJ1ZlcmlmaWVkIGluZGV4IGVxdWFscyB3b3JrdHJlZSBhbmQgYWxsIG5pbmUgcmV0YWluZWQgc291cmNlIFNIQTI1NiB2YWx1ZXM7IHJlYWQgb3JpZ2luYWwgdG9vbCByZWNlaXB0cyBhbmQgbG9jYWwgZXZpZGVuY2U7IHJlLXJlYWQgYm90aCBjdXJyZW50IGNlbnRyYWwgbWFpbiBmb3JtYWwgcGF0aHMuIFBhcmVudCBzZWN0aW9uIDYgYmluZHMgZGVueV9hbGwgYW5kIGZyZXNoIGV4ZWN1dGlvbiBzdGF0ZS4nCiAgY29ycmVjdGlvbl9yZWdpb25zOgogICAgLSAnRzEgb3JhY2xlIF9jb21wb25lbnRzIGFuZCBzY2hlbWEgYXJ0aWZhY3QvY29tcG9uZW50L2NhdGFsb2c6IGZpeGVkIG1pbmltdW0gdHlwZWQgYXJ0aWZhY3Qgb2JsaWdhdGlvbnM7IE9DSSBhbmQgZmlsZSBpZGVudGl0aWVzIHVzZSBkaXN0aW5jdCBzaGFwZXM7IG5vIGpvaW50bHkgZW1wdHkgZW1iZWRkZWQgY2xvc3VyZSBQQVNTLicKICAgIC0gJ0cyIG9yYWNsZSBfcmVhcCBhbmQgcmVhcCBldmlkZW5jZTogZmluYWwgdHdvIHNhbXBsZXMgbXVzdCBlYWNoIGJlIGNvbXBsZXRlIGFuZCBlbXB0eSBieSBkZWFkbGluZTsgUElEMSByZXRhaW5lZC1GRCBwb3NpdGl2ZSBjb250cm9sIGlzIG9wdGlvbmFsLCBzY2FuIGNvbXBsZXRlbmVzcyBhbmQgYWxsIGV4ZWN1dGlvbiBoZWxwZXJzIHJlbWFpbiBtYW5kYXRvcnkuJwogICAgLSAnRzQgb3JhY2xlIF9uZXR3b3JrIGFuZCByZXNvdXJjZS9yb3VuZCBzY2hlbWE6IHJldGFpbiBpbW11dGFibGUgb3duZWQgaWRlbnRpdGllcyBhY3Jvc3MgZXZlcnkgbGF0ZXIgcG9zdCBzYW1wbGU7IHJlcXVpcmUgcnVudGltZSBkZW55X2FsbCBldmlkZW5jZSwgZ3Vlc3QgZGV2aWNlL2NvbnRyb2wgcGF0aCBhYnNlbmNlIGFuZCBzZWFsZWQgQVJNNjQgc29ja2V0LUFCSSBlbmZvcmNlbWVudCBiZWZvcmUgd29ya2xvYWQgYW5kIHRocm91Z2ggcnVudGltZS9yZXN0b3Jlcy4nCiAgICAtICdHMyBvcmFjbGUgX3NuYXBzaG90IGFuZCBzbmFwc2hvdC9yZXN0b3JlIHNjaGVtYTogcmUtZXZhbHVhdGUgcmVzdG9yZWQgY29tcG9uZW50IG9ic2VydmF0aW9ucyB3aXRoIEcxOyBiaW5kIHNhbWUgZXhlY3V0aW9uL3JlcXVlc3QsIHNlcGFyYXRlbHkgYXBwcm92ZWQgY2xlYW4gdGVtcGxhdGUgYW5kIG5ldyBleGVjdXRpb24sIG9yIHJlamVjdCBjcm9zcy1leGVjdXRpb24gbXV0YWJsZSBzdGF0ZS4nCiAgICAtICdLZWVwIHRlc3RzL3Rlc3RfcmVwb19tYW5pZmVzdC5weSBhbmQgUkVQT19NQU5JRkVTVC5tZCB1bmNoYW5nZWQgZnJvbSB0aGUgaW5pdGlhbCB0ZW4tZmlsZSBjYW5kaWRhdGUuIFNhdmUgcmF3IHJlY2VpcHRzIGFuZCBmaW5hbCBkaWdlc3QgaW52ZW50b3J5IGluc2lkZSB0aGUgZXhpc3RpbmcgZXZpZGVuY2UgcmVwb3J0LCBub3QgYW4gZWxldmVudGggZmlsZS4nCiAgYmFzZWxpbmVfY29tcGFyaXNvbjogJ1NhbWUgZW52aXJvbm1lbnQsIGV4YWN0IDMwNmEwMWZhNmJmM2JjOGVkNDIwNGI4OGFiZGNiNGYxNmY3NTM2MGUgc291cmNlL3Rlc3QvZml4dHVyZSBkZXBlbmRlbmN5IGJ5dGVzIHZlcmlmaWVkIGJlZm9yZSBvbmUgdGhyZWUtbm9kZSBydW47IG5vIGNoZWNrb3V0LCBuZXcgYnJhbmNoLCBwZXJtaXNzaW9uIG9yIFBBVEggcmVwYWlyLicKICBlbnZpcm9ubWVudF9zdG9wOiAnRXhpc3RpbmcgUHl0aG9uIDMuMTQuMywgcHl0ZXN0IDkuMS4xIGFuZCByZXRhaW5lZCBqc29uc2NoZW1hIDQuMjYuMCBpbXBvcnQgc3VjY2Vzc2Z1bGx5LiBOb2RlIGlzIGFic2VudC4gTm8gZGVwZW5kZW5jeSBpbnN0YWxsYXRpb24gb3IgZnVsbCBzdWl0ZSB3aGlsZSB0aGlzIHByZXJlcXVpc2l0ZSBpcyBtaXNzaW5nLicKICBjb3VudGVyZXhhbXBsZV9yb3VuZDogJ2FkZGl0aW9uYWwgdGFyZ2V0ZWQgMS8yOyAxMCBmYWlsZWQsIDU4IHBhc3NlZCBpbiAzLjAwczsgZXhpdCAxOyBhbGwgdGVuIG5ldyByZXZpZXcgYXNzZXJ0aW9ucyBmYWlsZWQgb24gdGhlIHZlcmlmaWVkIG9yaWdpbmFsIG9yYWNsZS9zY2hlbWEgd2hpbGUgYWxsIG9yaWdpbmFsIHJlZ3Jlc3Npb25zIHBhc3NlZCcKICBiYXNlbGluZV9jb21wYXJpc29uX3Jlc3VsdDogJzEvMSB1c2VkOyAxNDQgc291cmNlL3Rlc3QvZml4dHVyZSBkZXBlbmRlbmN5IGZpbGVzIGVxdWFsIGV4YWN0IGJhc2VsaW5lOyAzIGZhaWxlZCBpbiAwLjM0cywgZXhpdCAxLCBzYW1lIGRpcmVjdG9yeS1tb2RlIHJlamVjdGlvbnMgYW5kIG1pc3Npbmcgbm9kZScKICBmdWxsX3N1aXRlX2Rpc3Bvc2l0aW9uOiAnYWRkaXRpb25hbCAwLzEgdXNlZDsgTk9UX0VYRUNVVEVEX0VOVklST05NRU5UX0JMT0NLRUQ7IG5vZGUgdW5hdmFpbGFibGUgYW5kIGV4aXN0aW5nIGRpcmVjdG9yeS1tb2RlIHByZXJlcXVpc2l0ZXMgZmFpbDsgZG8gbm90IHJ1biBhIGtub3duIGZhaWxpbmcgZnVsbCBzdWl0ZScKICBmaW5hbF90YXJnZXRlZF9yb3VuZDogJ2FkZGl0aW9uYWwgMi8yOyAxMDcgcGFzc2VkIGluIDYuNDBzOyBleGl0IDA7IGFsbCBvcmlnaW5hbCA1OCByZWdyZXNzaW9ucyByZXRhaW5lZDsgUnVmZiBhbmQgZm91ciByZXBvc2l0b3J5IHZhbGlkYXRvcnMgUEFTUycKICBjdW11bGF0aXZlX3VzZWRfYnVkZ2V0OiAncmVwYWlyIGJhdGNoZXMgMyAob3JpZ2luYWwgMiBwbHVzIGF1dGhvcml6ZWQgMSk7IHRhcmdldGVkIHJvdW5kcyA1IChvcmlnaW5hbCAzIHBsdXMgYXV0aG9yaXplZCAyKTsgZnVsbCBzdWl0ZSBydW5zIDIgKG9yaWdpbmFsIDIgcGx1cyBhZGRpdGlvbmFsIDApOyBleGFjdCBiYXNlbGluZSBjb21wYXJpc29ucyAxOyBicmFuY2hlcyAxOyBjYW5kaWRhdGUgcGF0aHMgMTAnCiAgc3RhdGU6IHNvdXJjZV9jb3JyZWN0aW9uX2NvbXBsZXRlX3dhaXRpbmdfZm9yX2luZGVwZW5kZW50X3JldmlldwpyMV9yNF9jb3JyZWN0aW9uX2F1dGhvcml6YXRpb246CiAgc291cmNlOiBFeHBsaWNpdCBzYW1lLXRhc2sgUjEtUjQgdXNlciBhdXRob3JpemF0aW9uOyByZXN1bWVkIGFmdGVyIGV4YWN0IHJldmlldyBwYWNrYWdlIHRyYW5zZmVyLiBObyBhZGRpdGlvbmFsIGJ1ZGdldCBmcm9tIHRoZSB0cmFuc2ZlciBtZXNzYWdlLgogIHJldmlld196aXA6IC90bXAvdHMtYjAyYS1yMXI0LXJldmlldy5QMkZLS0hZbC90b29sX3N5c3RlbV9jdWJlc2FuZGJveF9leGFjdF9jYW5kaWRhdGVfcmV2aWV3LnppcAogIHJldmlld196aXBfc2hhMjU2OiBkYTg4NDNkMjFlNWMwMjdhMzU2Njk4ZmFkZjVhYjBmNWY4ZDVkN2Y3YjZmZmIwZTIwNjQ4NTEzY2I2YzRlMWIxCiAgZW50cnlfdXNlZF9idWRnZXQ6ICdjb3JyZWN0aW9uIDM7IGRpcmVjdGVkIDU7IGZ1bGwgc3VpdGUgMjsgYmFzZWxpbmUgY29tcGFyaXNvbiAxOyBicmFuY2hlcyAxOyBjYW5kaWRhdGUgcGF0aHMgMTAnCiAgYWRkaXRpb25hbF9saW1pdHM6ICdjb3JyZWN0aW9uIDE7IGRpcmVjdGVkIHJvdW5kcyAyOyBmaW5hbCBzdGF0aWMvZ292ZXJuYW5jZSBiYXRjaCAxOyBmaW5hbCBleHBvcnQgMTsgYWN0aXZlIHdvcmsgbWludXRlcyA5MCBpbmNsdWRpbmcgcHJlLXRyYW5zZmVyIHJlYWQtb25seSB3b3JrOyBkZXBlbmRlbmN5L2Z1bGwtc3VpdGUvYmFzZWxpbmUvaG9zdC9wdWJsaWNhdGlvbiBvcGVyYXRpb25zIDAnCiAgdGltZV9hY2NvdW50aW5nOiAnUHJlLXRyYW5zZmVyIGluc3BlY3Rpb24gdXNlZCBhcHByb3hpbWF0ZWx5IDUgbWludXRlczsgaW5wdXQtd2FpdCBpbnRlcnZhbCB3YXMgc3RvcHBlZCwgd2l0aCBubyB3b3JrIG9yIGJ1ZGdldCBjb25zdW1wdGlvbi4gUmVzdW1lIDIwMjYtMDktMDkgMDc6Mzc6MjYgVVRDOyByZXRhaW4gcHJpb3IgdXNhZ2UuJwogIHJlYWRfYmVmb3JlX3dyaXRlOiAnQWxsIHRlbiBkaXNrL2luZGV4L2V4cG9ydC9yZXZpZXcgY2FuZGlkYXRlIGJ5dGVzIGVxdWFsOyBIRUFEL3RyZWUvYnJhbmNoIGFuZCBzYWZlIHBhdGNoIGlkZW50aXR5IG1hdGNoLiBDdXJyZW50IGNlbnRyYWwgbWFpbiBmaXhlZCBwYXRocywgbG9jYWwgcHJpbmNpcGxlcywgcGFyZW50IHNlY3Rpb25zIDYtNywgZXhpc3RpbmcgY29udHJhY3Qgc2VjdGlvbnMgNi03LCBvcmFjbGUgX3JlYXAvX3NuYXBzaG90L19uZXR3b3JrLCBzY2hlbWEgcHJvY2Vzcy9yZXN0b3JlL2V2aWRlbmNlIGFuZCBleGFjdCBzZXZlbiByZXZpZXcgaW5wdXRzIHJlYWQuJwogIGZpeGVkX2NvcnJlY3Rpb25zOgogICAgLSAnUjFfUE9TVF9PTkxZX1JFTEFCRUxMSU5HIGFuZCBSMV9QT1NUX09OTFlfQ1JPU1NfUk9VTkQ6IGFic29yYiBleHBsaWNpdCBwcmUvYWN0aXZlL3Bvc3Qgb3duZXIgb3IgcmVmZXJlbmNlIG9ic2VydmF0aW9ucyBpbiBwZXJzaXN0ZW50IGltbXV0YWJsZS1rZXkgaGlzdG9yeTsgcHJlc2VydmUgbGF3ZnVsIHByZS1leGlzdGluZyBzaGFyZWQtcG9vbCByZWxlYXNlLicKICAgIC0gJ1IyX0ZPUkVJR05fUE9PTF9SRUZFUkVOQ0VfREVMRVRFRDogcHJvdGVjdCBmb3JlaWduIGV4Y2x1c2l2ZSBvd25lcnMgYW5kIGZvcmVpZ24gc2hhcmVkIHJlZmVyZW5jZXMgaW4gYWN0aXZlIGFuZCBwb3N0LCBhbGxvd2luZyB1bnJlbGF0ZWQgYmFja2dyb3VuZCBjaGFuZ2VzLicKICAgIC0gJ1IzX1JVTlRJTUVfRVhFQ1VUSU9OX0pPSU4gYW5kIFIzX1RFUk1JTkFUSU9OX0VYRUNVVElPTl9KT0lOOiBqb2luIHNhbWUtb3duZXIgdGVybWluYXRpb24gYW5kIHJ1bnRpbWUgZXhlY3V0aW9ucyBmb3IgZXZlcnkgYXBwbGljYWJsZSBjYXNlOyBkaXN0aW5jdCBpbmRlcGVuZGVudCBzY2VuYXJpb3MgcmVtYWluIGRpc3RpbmN0LicKICAgIC0gJ1I0X1JFU1RPUkVfRk9SRUlHTl9QUk9DRVNTIGFuZCBSNF9SRVNUT1JFX1VOT0JTRVJWRURfUFJPQ0VTUzogYmluZCBlYWNoIHJlc3RvcmUgdG8gdHlwZWQgaG9zdCBwcm9jZXNzIG9ic2VydmF0aW9ucyBhbmQgb3duZXIvZXhlY3V0aW9uLCByZWplY3QgZm9yZWlnbiBrZXlzIGFuZCBibG9jayBtaXNzaW5nIG9ic2VydmF0aW9uczsgbm8gc2Vjb25kIHRlcm1pbmFsIGRlc3Ryb3kgcmVxdWlyZW1lbnQuJwogIHBsYW5uZWRfcm91bmRzOiAnRmlyc3Q6IG9yaWdpbmFsIDEwNyBwbHVzIHNldmVuIGV4YWN0IHJldmlldy1pbnB1dCByZWdyZXNzaW9ucyBhZ2FpbnN0IHVuY2hhbmdlZCBvcmFjbGUvc2NoZW1hL2ZpeHR1cmUuIFRoZW4gb25lIGNvcnJlY3Rpb24gYmF0Y2ggYW5kIGZpbmFsIGNvbXBsZXRlIGRpcmVjdGVkIHN1aXRlLCBpbmNsdWRpbmcgc3RydWN0dXJhbCBtaWdyYXRpb24gZXF1aXZhbGVuY2UgYW5kIGRpcmVjdGx5IHJlbGF0ZWQgcG9zaXRpdmVzLicKICBmaW5hbF9zdGF0aWNfYmF0Y2g6ICdSdWZmIGNoZWNrIGFuZCBmb3JtYXQgLS1jaGVjayB3aXRoIC0tbm8tY2FjaGUgb24gdGhlIHR3byBjb250cmFjdCBQeXRob24gZmlsZXM7IGV4aXN0aW5nIGFjdGl2ZS1nYXRlcywgcHJvY2Vzcy1hdXRob3JpdHksIG1vZHVsZS1yZWdpc3RyeSBhbmQgcmVwby1tYW5pZmVzdCB2YWxpZGF0b3JzOyBnaXQgZGlmZiAtLWNoZWNrOyBBU1QgZXF1YWxpdHkgb2YgYWxsIG9yaWdpbmFsIHRlc3QgZGVmaW5pdGlvbnMgYW5kIHVuY2hhbmdlZCB0ZW4tcGF0aCBjbG9zdXJlLiBObyBmdWxsIHB5dGVzdCBvciBiYXNlbGluZSBjaGVja3MuJwogIHNjb3BlOiAnTW9kaWZ5IG9ubHkgZXhpc3RpbmcgY29udHJhY3QvZXZpZGVuY2Uvc2NoZW1hL29yYWNsZS9maXh0dXJlL2NvbnRyYWN0LXRlc3RzL29yaWdpbmFsIG1hbmlmZXN0L3BsYW4uIEtlZXAgUkVQT19NQU5JRkVTVC5tZCBhbmQgdGVzdHMvdGVzdF9yZXBvX21hbmlmZXN0LnB5IGJ5dGUtaWRlbnRpY2FsIHRvIGVudHJ5LicKICByZWNvcmRfcmV0ZW50aW9uOiAnQXBwZW5kIG9yaWdpbmFsIHN0ZG91dC9zdGRlcnIvZXhpdCwgc291cmNlIGhhc2hlcyBhbmQgZXhhY3QgdGVzdC10aW1lIHBhaXIgYnl0ZXMgdG8gZXhpc3RpbmcgZXZpZGVuY2UvZmluYWwgWklQOyByZXRhaW4gYWxsIG9yaWdpbmFsIGZhaWx1cmVzIGFuZCB1bmtub3duIGhpc3RvcmljYWwgMTQ0LWZpbGUvdGVzdC10aW1lLXBsYW4gYnl0ZXMuJwogIHRlcm1pbmFsOiAnT25lIGZpbmFsIHRlbi1maWxlIFpJUCBmb3IgaW5kZXBlbmRlbnQgcmV2aWV3OyBubyBmaW5hbCBzb3VyY2UgYWNjZXB0YW5jZSwgcmVhbCBiYWNrZW5kIGFjY2VwdGFuY2UsIGhvc3QgYXV0aG9yaXphdGlvbiBvciBuZXh0IHN0YWdlLicKICBmaXJzdF9kaXJlY3RlZF9yZXN1bHQ6ICdBZGRpdGlvbmFsIGRpcmVjdGVkIDEvMjsgY3VtdWxhdGl2ZSA2LiBTZXZlbiBleGFjdCByZXZpZXcgaW5wdXQgaGFzaGVzIHZlcmlmaWVkLCBhbGwgc2V2ZW4gYWN0dWFsIGVycm9uZW91cyBQQVNTOyA3IGZhaWxlZCwgMTA3IHBhc3NlZCBpbiA3LjE4czsgZXhpdCAxOyBvcmlnaW5hbCBvcmFjbGUvc2NoZW1hL2ZpeHR1cmUgaGFzaGVzIHVuY2hhbmdlZC4nCiAgY29ycmVjdGlvbl9iYXRjaF91c2VkOiAnQWRkaXRpb25hbCAxLzE7IGN1bXVsYXRpdmUgNC4gUjEtUjQgb25seSwgdHlwZWQgcmVzdG9yZSBvYnNlcnZhdGlvbiBtaWdyYXRpb24gYW5kIHByZXNlcnZhdGlvbiBvZiBleGFjdCBjb3VudGVyZXhhbXBsZSBwcm9qZWN0aW9uOyBzb3VyY2UgZm9ybWF0dGluZyBpbmNsdWRlZCBhcyBhbiBlZGl0LicKICBmaXh0dXJlX21pZ3JhdGlvbjogJ0FkZGVkIHJlc3RvcmVfcHJvY2Vzc19vYnNlcnZhdGlvbnMgZm9yIGJvdGggcmVzdG9yZXM7IHNlY29uZCBob3N0X3Byb2Nlc3NlcyByZXBsYWNlZCBieSBoYXNoZXMgZGVyaXZlZCBmcm9tIHN5bnRoZXRpYyB0eXBlZCBwcm9jZXNzIHJvd3MuIENhbm9uaWNhbCBwcm9qZWN0aW9uIHJlbW92ZXMgb25seSB0aGVzZSBjaGFuZ2VzIHdoZW4gY2hlY2tpbmcgdGhlIHNldmVuIG9yaWdpbmFsIHJldmlldyBpbnB1dCBkaWdlc3RzLiBPcmlnaW5hbCAxMDcgdGVzdCBhc3NlcnRpb25zIHJldGFpbmVkOyBjbGVhbi10ZW1wbGF0ZSBoZWxwZXIgYmluZHMgbmV3IG9ic2VydmF0aW9ucy4nCiAgc3RhdGU6IHNpbmdsZV9jb3JyZWN0aW9uX3JlYWR5X2Zvcl9maW5hbF9kaXJlY3RlZF9hbmRfc3RhdGljX2JhdGNoCg=="
  },
  "static_scope_and_original_test_check": {
    "exit_code": 0,
    "stdout": "{\n  \"original_test_definitions\": 40,\n  \"changed_original_test_definitions\": [],\n  \"original_107_semantics_retained\": true,\n  \"manifest_files_unchanged\": true,\n  \"changed_paths\": [\n    \"REPO_MANIFEST.md\",\n    \"docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md\",\n    \"docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1_evidence.md\",\n    \"examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml\",\n    \"examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml\",\n    \"harness/cubesandbox_backend_acceptance_v1.schema.json\",\n    \"tests/cubesandbox_contract_oracle.py\",\n    \"tests/fixtures/cubesandbox_backend_acceptance_v1.json\",\n    \"tests/test_cubesandbox_backend_acceptance_contract.py\",\n    \"tests/test_repo_manifest.py\"\n  ],\n  \"exact_ten_path_closure\": true,\n  \"extra_untracked_paths\": []\n}\\n",
    "stderr": ""
  }
}
```

### R1–R4 actual before/after outcomes

| Exact case | Before | After | Required semantic reason |
| --- | --- | --- | --- |
| R1_POST_ONLY_RELABELLING | PASS | FAIL | 0:SANDBOX_NETWORK_RESOURCE_LEAK |
| R1_POST_ONLY_CROSS_ROUND | PASS | FAIL | 1:SANDBOX_NETWORK_RESOURCE_LEAK |
| R2_FOREIGN_POOL_REFERENCE_DELETED | PASS | FAIL | 0:CROSS_SANDBOX_CONTAMINATION |
| R3_RUNTIME_EXECUTION_JOIN | PASS | FAIL | 1:EXECUTION_JOIN_MISMATCH |
| R3_TERMINATION_EXECUTION_JOIN | PASS | FAIL | payload_sigkill:EXECUTION_JOIN_MISMATCH |
| R4_RESTORE_FOREIGN_PROCESS | PASS | FAIL | RESTORE_PROCESS_FOREIGN_BINDING |
| R4_RESTORE_UNOBSERVED_PROCESS | PASS | BLOCKED | RESTORE_PROCESS_OBSERVATION_MISSING |

### Retained limits and unresolved conditions

Cumulative actual usage: correction batches **4**, directed rounds **7**, full suite runs **2**, exact baseline comparisons **1**, candidate branches **1**, candidate paths **10**. This authorization used correction **1/1**, directed **2/2**, static/governance **1/1**; final export is reserved for one following invocation. No additional source correction or test run is authorized by these results. The elapsed active-work receipt is recorded in the export index, including approximately five minutes before the missing-input stop and excluding the stopped transfer-wait interval.

The original all-repository outcome remains **NOT_PASSED**. No full suite or baseline was rerun, and no host/environment prerequisite was repaired or probed. Retain the two historical group-writable fixture-directory safety rejections and missing Node condition as prior observations; this round does not claim a fresh whole-environment assessment. The earlier 144-file aggregate receipt exists, but its complete per-file manifest was not retained; old test-time plan bytes remain unknown. Neither missing historical artifact was reconstructed. This round does retain its own exact first/final test-time manifest and plan bytes, so the final plan's result-only update is byte-comparable.

Source: the R1–R4 synthetic regressions now meet their frozen expectations, but independent review of the changed region remains pending and final source acceptance is not declared. No R5 diagnosis was promoted into a repair item. Real host: the lifecycle-manager ARM64 OCI digest and complete immutable asset closure remain unfrozen; reviewed observers, identity/permission and capacity checks, parent deny_all/topology and host crash/cleanup prerequisites plus separate exact execution authorization remain outstanding. No actual backend evidence was collected.

```text
SOURCE_AND_CONTRACT_ONLY=true
DGX_EXECUTION=false
HOST_INSTALLATION=false
NETWORK_MUTATION=false
SYSTEMD_MUTATION=false
CANONICAL_MAIN_WRITE=false
REAL_BACKEND_ACCEPTANCE_EXECUTED=false
G1_SPEC_COMPLETE=true
G2_SPEC_COMPLETE=true
G3_SPEC_COMPLETE=true
G4_SPEC_COMPLETE=true
REAL_BACKEND_ACCEPTANCE_AUTHORIZED=false
INDEPENDENT_R1_R4_SOURCE_REVIEW=PENDING
WHOLE_REPOSITORY_TEST_STATUS=NOT_PASSED
```


### R1–R4 final source file SHA-256 inventory

Evidence SHA-256 and the final staged patch SHA-256 are recorded externally in the export index to avoid self-reference. No source, schema, fixture or test bytes changed after final validation.

```json
{
  "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
  "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
  "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ca8c54254f4e74ae327c47f910128ad2fe8cf5d757e2546bc2252adfd5b2037a",
  "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml": "ec72bf9fb18bad9e06138098eeae5a894c9212bc43c01ca9ccd546378a8e7969",
  "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
  "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
  "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
  "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
  "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
}
```


### Automatic staging approval rejection and export disposition

The command-specific approval mechanism rejected the proposed eight-file git add before execution, citing the earlier user prohibition on index changes. No index mutation occurred and no alternate write route was attempted. Exact rejection reason: 该命令会修改 Git 暂存区，而用户明确禁止修改暂存区；即使范围限于八个候选文件，也超出当前授权边界。

The final export therefore preserves final WORKTREE source bytes and its complete HEAD-relative patch as the review candidate. It also includes the ORIGINAL staged patch under a distinct name, whose SHA-256 remains 6ace6f90f5c0114e1d24b705fcfb1dd37e8c68507798c20e269689a375dc9a6e. The index/worktree mismatch for the eight authorized correction paths is disclosed in the export index. The two manifest-registration files remain equal to the original index. No staged patch is misrepresented as containing the R1–R4 repair. Source/test results stand; synchronizing the Git index requires explicit clarification of authorization. This is an index-delivery limitation, not a backend or test PASS.


## Explicit eight-file index synchronization and environment-only check (2026-09-09)

Same task/branch/HEAD. The user's latest authorization expressly lifts the prior index-write prohibition only for the eight enumerated paths. One finite environment inspection, one minimal three-record update/pair-validation batch, and one exact git add/readback are allowed within 20 minutes, starting 09:10:13 UTC. No source correction, pytest/full suite/baseline, dependency installation, ZIP export, remote publication, host probe, permission/sandbox change or alternate index is permitted. Original cumulative usage remains correction 4, directed 7, full suites 2, baseline 1, branch 1, candidate paths 10. Index sync and environment inspection are counted separately.

Entry verification: exact ZIP 8cbf93d07a863802cadb15b6ebab09c2b95cd1f6e409fe35af0332b3c80a6664 and all ten worktree bytes matched the reviewed index. Final worktree patch bc3ded0a5a3494fed868ba0a8d38759c537d8fbc1abc185c7cec51a4c2665318 and old staged patch 6ace6f90f5c0114e1d24b705fcfb1dd37e8c68507798c20e269689a375dc9a6e were separately verified, without requiring their equality. Branch and HEAD match; main remains 027dbb3fb83c38def70e81d58712f80dbe613483; no extra candidate/untracked paths. No archive was extracted over the worktree.

Current central main fixed paths re-read directly: principles observed blob 17741fb79252b43d6ff820dcffc7c92ab349acfc and registry observed blob 20c9ec3cd74337bbf4cf5c5ab19de3b7ccd7eaf3. Applicable local principles and current process authority/pair were read. No central pin or new authority framework is introduced.

External review input supplied by the user: R1–R4 and directly related review passed, 37/37 independent examples matched expectations. This is an externally reported review result, NOT a local rerun. The author's retained 160-case pytest is a separate historical receipt. Whole-repository status remains NOT_PASSED. Real backend acceptance remains unexecuted and unauthorized.

### Bounded read-only environment findings

```json
{
  "python": {
    "path": "/home/rich/.pyenv/versions/3.14.3/bin/python",
    "version": "3.14.3 (main, Mar 30 2026, 15:58:42) [GCC 13.3.0]",
    "requires_python": ">=3.10",
    "satisfied": true
  },
  "modules": {
    "pytest": {
      "version": "9.1.1",
      "module_path": "/home/rich/.pyenv/versions/3.14.3/lib/python3.14/site-packages/pytest/__init__.py"
    },
    "jsonschema": {
      "version": "4.26.0",
      "module_path": "/tmp/ts-b02a-cubesandbox-contract-v1-deps/jsonschema/__init__.py"
    },
    "PyYAML": {
      "version": "6.0.3",
      "module_path": "/home/rich/.pyenv/versions/3.14.3/lib/python3.14/site-packages/yaml/__init__.py"
    },
    "setuptools": {
      "error": "No module named 'setuptools'"
    },
    "wheel": {
      "error": "No module named 'wheel'"
    }
  },
  "requirements": [
    {
      "kind": "runtime",
      "requirement": "PyYAML>=6.0",
      "active": true,
      "version": "6.0.3",
      "satisfied": true
    },
    {
      "kind": "runtime",
      "requirement": "jsonschema==4.26.0",
      "active": true,
      "version": "4.26.0",
      "satisfied": true
    },
    {
      "kind": "runtime",
      "requirement": "tomli>=2.0; python_version < '3.11'",
      "active": false,
      "version": null,
      "satisfied": true
    },
    {
      "kind": "test",
      "requirement": "pytest>=8.0",
      "active": true,
      "version": "9.1.1",
      "satisfied": true
    },
    {
      "kind": "build",
      "requirement": "setuptools>=69",
      "active": true,
      "version": null,
      "satisfied": false
    },
    {
      "kind": "build",
      "requirement": "wheel",
      "active": true,
      "version": null,
      "satisfied": false
    }
  ],
  "validation_PATH": "/home/rich/.pyenv/versions/3.14.3/bin:/snap/ruff/current/bin:/usr/bin:/bin",
  "validation_node": null,
  "node_checked_directories": [
    "/home/rich/.pyenv/versions/3.14.3/bin",
    "/snap/ruff/current/bin",
    "/usr/bin",
    "/bin",
    "/home/rich/.codex/packages/standalone/releases/0.153.4-aarch64-unknown-linux-musl/codex-path",
    "/home/rich/.local/bin",
    "/home/rich/bin",
    "/usr/local/cuda/bin",
    "/opt/bin/",
    "/home/rich/.codex/tmp/arg0/codex-arg059UEv0",
    "/home/rich/.pyenv/shims",
    "/home/rich/.pyenv/bin",
    "/usr/local/sbin",
    "/usr/local/bin",
    "/usr/sbin",
    "/sbin",
    "/usr/games",
    "/usr/local/games",
    "/snap/bin"
  ],
  "node_candidates": []
}
```

Current umask was read as 0002, without modification. The two existing tests call Path.mkdir() without mode (tests/test_durable_orchestrator_reliability.py:153 and :304/:308). Requested 0777 masked by 0002 normally yields 0775 (absent a default-ACL override), leaving group write set. The constructor at src/tool_system/orchestrator/durable.py:127 rejects S_IWGRP|S_IWOTH before the intended record-limit/parent-substitution assertions. No directories were created or chmodded to demonstrate this calculation, and no safety predicate was altered.

Python/runtime/dev-test requirements in pyproject.toml are satisfied by the existing explicit source-test interpreter and retained task dependencies. setuptools>=69 and wheel are missing in this interpreter; they are declared build-system requirements, not an installed-package build requirement for directly running existing tests through PYTHONPATH=src. tomli's marker is inactive on Python 3.14.3. The first metadata query exited 1 on absent setuptools metadata; the bounded query then reported missing packages explicitly, without installation.

No node or nodejs executable was found in the validation PATH, current shell PATH directories or directories explicitly referenced by ~/.profile and ~/.bashrc, as enumerated above. These are bounded locations, not a whole-machine absence claim. No executable was available for a version query. A shell configuration excerpt unexpectedly included an unrelated credential line in tool output; its value is deliberately omitted from this evidence and all further output.

Proposed minimum next full-suite arrangement, NOT executed: retain the existing Python/PYTHONPATH and disable bytecode/cache writes; use a test-child-only umask 0022 (or stricter 0077) for newly created fixtures; if a separately supplied installed Node path is verified, include only its directory in the test child's PATH. Current checked paths do not supply Node, so a known installed location or separately authorized provisioning remains necessary. No global PATH/umask change or chmod of prior fixtures is needed. Build dependencies would require separate provisioning only if a build/install step is introduced. A full-suite run and any child-environment adjustment still require separate authorization; these checks are not a full-suite PASS.

### Exact authorized index operation

```text
git add -- docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1_evidence.md harness/cubesandbox_backend_acceptance_v1.schema.json tests/cubesandbox_contract_oracle.py tests/fixtures/cubesandbox_backend_acceptance_v1.json tests/test_cubesandbox_backend_acceptance_contract.py examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml
```

Only manifest, change plan and this evidence record receive current authorization/result notes; the other seven candidate paths must remain byte-identical to the reviewed ZIP. One protected dispatch will validate the current explicit pair and issue this exact command once through command-specific approval. On approval rejection, stop without alternate execution. Its actual exit/readback and final patch hash will be returned in the external delivery receipt; they are not prefilled here, avoiding any post-staging record mutation or second git add.


### Task-pair validation within the one record-update batch

Initial pair validation exited 1 because the closed manifest schema rejected the newly added index_sync_authorization top-level key. The same authorization text was moved into existing scope/approval fields; no schema, policy or protected source changed. This failed validation is retained, and is not a pytest/test run.

```json
{
  "manifest": {
    "status": "BLOCK",
    "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "policy_path": "policy/repo_write_policy.yaml",
    "reasons": [
      "TASK_MANIFEST_SCHEMA_VIOLATION instance= schema=/additionalProperties keyword=additionalProperties detail=unknown=[\"index_sync_authorization\"]"
    ],
    "autonomy_policy_path": "policy/autonomy_policy.yaml"
  },
  "plan": {
    "status": "BLOCK",
    "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "reasons": [
      "TASK_MANIFEST_SCHEMA_VIOLATION instance= schema=/additionalProperties keyword=additionalProperties detail=unknown=[\"index_sync_authorization\"]"
    ]
  },
  "binding": {
    "status": "PASS",
    "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "binding_mode": "explicit_manifest_change_plan_pair",
    "writes_target_repo": false,
    "executes_target_repo_mutation": false,
    "reasons": []
  }
}

```

Final task-pair validation in this record-update batch: exit 0, manifest/plan/binding PASS; stderr empty. The protected dispatcher will revalidate the exact final pair immediately before its sole git add. No test suite was started.

```json
{
  "manifest": {
    "status": "PASS",
    "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "policy_path": "policy/repo_write_policy.yaml",
    "reasons": [],
    "autonomy_policy_path": "policy/autonomy_policy.yaml"
  },
  "plan": {
    "status": "PASS",
    "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "reasons": []
  },
  "binding": {
    "status": "PASS",
    "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
    "binding_mode": "explicit_manifest_change_plan_pair",
    "writes_target_repo": false,
    "executes_target_repo_mutation": false,
    "reasons": []
  }
}

```

Seven protected reviewed-file SHA-256 values (unchanged):

```json
{
  "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
  "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
  "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
  "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
  "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
  "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
  "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
}
```


## Fixed Node and conditional final full-suite authorization (2026-09-09)

Entry branch/HEAD, exact ten paths, index/worktree equality and seven reviewed files verified. Entry staged patch SHA-256 6503f5e17ee4260c9cbd0f7daa0c2420fa1d78baf43ebd1bbcd889559f169334. Central main fixed formal paths re-read; Node official release source blob 5ca096e09916a123111edbaf114cf9dc4773c687 confirms the supplied archive digest. New task-only root: /tmp/tool-system-ts-b02a-full-validation-wk6tvh3a. Current authorization and limits are recorded in the original change plan; seven protected files remain frozen. All prior failures and external 37/37 versus author 160-case evidence remain separate. Full suite stays NOT_PASSED until actually executed successfully. Real backend execution and authorization remain false.

Preparation and test-wrapper source hashes:
```json
{
  "prepare_node.py": "42aca1a66caa4fea79d2bdc0f3d0772f975e6676cc0907c22fd1832c478be41e",
  "test_exec.py": "2abc1b5da68ba066f1765af3224f6912ac9b49e54715b30f3c2fd4b8f3396c75"
}
```


### Actual fixed-Node and final full-suite results

Fixed artifact preparation completed once; official HTTPS source and expected digest matched, not PGP verification. Only the two allowed regular members were extracted (122836553 bytes total). Binary hash recorded before execution and rechecked after testing.

```json
{
  "url": "https://nodejs.org/dist/v24.20.0/node-v24.20.0-linux-arm64.tar.xz",
  "download_attempts": 1,
  "pgp_verified": false,
  "archive_bytes": 30778928,
  "archive_sha256": "5f4ddab610c1ab2016b3c227cebdbf6d9495161487e4739c7b90090595f465f7",
  "node_path": "/tmp/tool-system-ts-b02a-full-validation-wk6tvh3a/bin/node",
  "node_sha256": "23a5637c2470fde09fcc1acc77c1b92e04e3d7e3e6e80ff7df6f5831958d1477",
  "extracted_bytes": 122836553,
  "identity_exit": 0,
  "identity": {
    "version": "v24.20.0",
    "platform": "linux",
    "arch": "arm64"
  },
  "status": "PASS"
}
```

Three-test confirmation is current-candidate environment evidence, not a historical baseline rerun. Its PASS enabled the single full-suite run. Exact outputs and real exits:

```json
{
  "three": {
    "stdout": "...                                                                      [100%]\n3 passed in 0.73s\n",
    "stderr": "",
    "exit": {
      "exit_code": 0,
      "timeout": false
    }
  },
  "full": {
    "stdout": "........................................................................ [  6%]\n........................................................................ [ 13%]\n........................................................................ [ 20%]\n........................................................................ [ 26%]\n........................................................................ [ 33%]\n........................................................................ [ 40%]\n........................................................................ [ 47%]\n........................................................................ [ 53%]\n........................................................................ [ 60%]\n........................................................................ [ 67%]\n........................................................................ [ 73%]\n........................................................................ [ 80%]\n........................................................................ [ 87%]\n........................................................................ [ 94%]\n................................................................         [100%]\n1072 passed in 79.62s (0:01:19)\n",
    "stderr": "",
    "exit": {
      "exit_code": 0,
      "timeout": false
    }
  }
}
```

JUnit and final one-batch checks:

```json
{
  "scope": "EXACT_TEN",
  "protected": {
    "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
    "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
    "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
    "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
    "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
    "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
    "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
  },
  "junit": {
    "three": [
      {
        "name": "pytest",
        "errors": "0",
        "failures": "0",
        "skipped": "0",
        "tests": "3",
        "time": "0.734",
        "timestamp": "2026-09-09T19:33:53.752145+09:30",
        "hostname": "apolo-9004"
      }
    ],
    "full": [
      {
        "name": "pytest",
        "errors": "0",
        "failures": "0",
        "skipped": "0",
        "tests": "1072",
        "time": "79.614",
        "timestamp": "2026-09-09T19:34:13.326129+09:30",
        "hostname": "apolo-9004"
      }
    ]
  },
  "governance_exits": [
    0,
    0,
    0,
    0,
    0
  ]
}
```

Each test uses its own new task basetemp and JUnit XML. Exact test-time pair bytes, source before/after, command/timeout and environment records are retained under /tmp/tool-system-ts-b02a-full-validation-wk6tvh3a. Whitelisted test-child environment is PATH with verified task Node plus existing Python/Ruff/Git directories, task HOME/TMPDIR, PYTHONPATH, PYTHONDONTWRITEBYTECODE, LANG and LC_ALL only; child umask 0022. No provider credentials or injection variables inherited. Parent PATH hash and umask 0002 were equal before preparation and after full testing; no parent environment or existing directory modes were changed.

Raw protected-dispatch receipts:

```json
{
  "prepare": {
    "status": "PASS",
    "preflight": {
      "process_authority_result": {
        "status": "PASS",
        "authority_path": "config/process_authority_v1.yaml",
        "module_id": "process-authority",
        "module_version": "2.3.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.1.0",
        "current_task_input_mode": "explicit_manifest_change_plan_pair",
        "implicit_repository_index_allowed": false,
        "legacy_authority": false,
        "replay_result": {
          "status": "PASS",
          "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
          "pair_count": 108,
          "authority": false,
          "replay_only": true,
          "executes_target_repo_mutation": false,
          "reasons": []
        },
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "production_deployment": false,
        "cleanup_execution": false,
        "reasons": []
      },
      "manifest_result": {
        "status": "PASS",
        "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "policy_path": "policy/repo_write_policy.yaml",
        "reasons": [],
        "autonomy_policy_path": "policy/autonomy_policy.yaml"
      },
      "pair_binding_result": {
        "status": "PASS",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "binding_mode": "explicit_manifest_change_plan_pair",
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "change_plan_result": {
        "status": "PASS",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "reasons": []
      },
      "replay_execution_requested": false,
      "validation_to_dispatch_inputs_equal": true
    },
    "input_sha256_before": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "ed2058d3f86d2fdeb56c4776fc77870f13b44233a4634a42afb889e1a876097c",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "108bf48f1423bc072838863d8e6b387a58c473a88c864053b61089a73e70de13"
    },
    "input_sha256_after": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "ed2058d3f86d2fdeb56c4776fc77870f13b44233a4634a42afb889e1a876097c",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "108bf48f1423bc072838863d8e6b387a58c473a88c864053b61089a73e70de13"
    },
    "command_results": [
      {
        "name": "/home/rich/.pyenv/versions/3.14.3/bin/python -B /tmp/tool-system-ts-b02a-full-validation-wk6tvh3a/prepare_node.py",
        "exit_code": 0,
        "stdout": "{\"url\": \"https://nodejs.org/dist/v24.20.0/node-v24.20.0-linux-arm64.tar.xz\", \"download_attempts\": 1, \"pgp_verified\": false, \"archive_bytes\": 30778928, \"archive_sha256\": \"5f4ddab610c1ab2016b3c227cebdbf6d9495161487e4739c7b90090595f465f7\", \"node_path\": \"/tmp/tool-system-ts-b02a-full-validation-wk6tvh3a/bin/node\", \"node_sha256\": \"23a5637c2470fde09fcc1acc77c1b92e04e3d7e3e6e80ff7df6f5831958d1477\", \"extracted_bytes\": 122836553, \"identity_exit\": 0, \"identity\": {\"version\": \"v24.20.0\", \"platform\": \"linux\", \"arch\": \"arm64\"}, \"status\": \"PASS\"}\n",
        "stderr": ""
      }
    ],
    "subprocess_call_count": 1,
    "reasons": [],
    "source_before": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "source_after": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "parent_before": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    },
    "parent_after": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    }
  },
  "three": {
    "status": "PASS",
    "preflight": {
      "process_authority_result": {
        "status": "PASS",
        "authority_path": "config/process_authority_v1.yaml",
        "module_id": "process-authority",
        "module_version": "2.3.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.1.0",
        "current_task_input_mode": "explicit_manifest_change_plan_pair",
        "implicit_repository_index_allowed": false,
        "legacy_authority": false,
        "replay_result": {
          "status": "PASS",
          "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
          "pair_count": 108,
          "authority": false,
          "replay_only": true,
          "executes_target_repo_mutation": false,
          "reasons": []
        },
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "production_deployment": false,
        "cleanup_execution": false,
        "reasons": []
      },
      "manifest_result": {
        "status": "PASS",
        "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "policy_path": "policy/repo_write_policy.yaml",
        "reasons": [],
        "autonomy_policy_path": "policy/autonomy_policy.yaml"
      },
      "pair_binding_result": {
        "status": "PASS",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "binding_mode": "explicit_manifest_change_plan_pair",
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "change_plan_result": {
        "status": "PASS",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "reasons": []
      },
      "replay_execution_requested": false,
      "validation_to_dispatch_inputs_equal": true
    },
    "input_sha256_before": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "3be8a78171198ca832003bd14a3360d31a09782f2bc84265e7ebab3a492f78ec",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "5f17f9cd2aa58c823c43f0a3c59d44d29d388b4907ac36dfac7894fd0255574f"
    },
    "input_sha256_after": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "3be8a78171198ca832003bd14a3360d31a09782f2bc84265e7ebab3a492f78ec",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "5f17f9cd2aa58c823c43f0a3c59d44d29d388b4907ac36dfac7894fd0255574f"
    },
    "command_results": [
      {
        "name": "/usr/bin/timeout --signal=TERM --kill-after=5s 115s /home/rich/.pyenv/versions/3.14.3/bin/python -B /tmp/tool-system-ts-b02a-full-validation-wk6tvh3a/test_exec.py three",
        "exit_code": 0,
        "stdout": "",
        "stderr": ""
      }
    ],
    "subprocess_call_count": 1,
    "reasons": [],
    "source_before": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "source_after": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "parent_before": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    },
    "parent_after": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    }
  },
  "full": {
    "status": "PASS",
    "preflight": {
      "process_authority_result": {
        "status": "PASS",
        "authority_path": "config/process_authority_v1.yaml",
        "module_id": "process-authority",
        "module_version": "2.3.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.1.0",
        "current_task_input_mode": "explicit_manifest_change_plan_pair",
        "implicit_repository_index_allowed": false,
        "legacy_authority": false,
        "replay_result": {
          "status": "PASS",
          "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
          "pair_count": 108,
          "authority": false,
          "replay_only": true,
          "executes_target_repo_mutation": false,
          "reasons": []
        },
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "production_deployment": false,
        "cleanup_execution": false,
        "reasons": []
      },
      "manifest_result": {
        "status": "PASS",
        "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "policy_path": "policy/repo_write_policy.yaml",
        "reasons": [],
        "autonomy_policy_path": "policy/autonomy_policy.yaml"
      },
      "pair_binding_result": {
        "status": "PASS",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "binding_mode": "explicit_manifest_change_plan_pair",
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "change_plan_result": {
        "status": "PASS",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "reasons": []
      },
      "replay_execution_requested": false,
      "validation_to_dispatch_inputs_equal": true
    },
    "input_sha256_before": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "715406202c45c6586910450ea15c78770df4719e3c1561409aa9fdcd7cc684ca",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "999b4b53034ac8fcc7afe6a9656619c5dbe946347bfc57f2ce1477f010100b5e"
    },
    "input_sha256_after": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "715406202c45c6586910450ea15c78770df4719e3c1561409aa9fdcd7cc684ca",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "999b4b53034ac8fcc7afe6a9656619c5dbe946347bfc57f2ce1477f010100b5e"
    },
    "command_results": [
      {
        "name": "/usr/bin/timeout --signal=TERM --kill-after=5s 1195s /home/rich/.pyenv/versions/3.14.3/bin/python -B /tmp/tool-system-ts-b02a-full-validation-wk6tvh3a/test_exec.py full",
        "exit_code": 0,
        "stdout": "",
        "stderr": ""
      }
    ],
    "subprocess_call_count": 1,
    "reasons": [],
    "source_before": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "source_after": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "parent_before": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    },
    "parent_after": {
      "PATH_sha256": "5fd4f7d29c87ce25f4230ad2b0562920b8bd86829dc49fa3566e6ff433c52e57",
      "umask": "0002"
    }
  },
  "governance": {
    "status": "PASS",
    "preflight": {
      "process_authority_result": {
        "status": "PASS",
        "authority_path": "config/process_authority_v1.yaml",
        "module_id": "process-authority",
        "module_version": "2.3.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.1.0",
        "current_task_input_mode": "explicit_manifest_change_plan_pair",
        "implicit_repository_index_allowed": false,
        "legacy_authority": false,
        "replay_result": {
          "status": "PASS",
          "snapshot_path": "/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml",
          "pair_count": 108,
          "authority": false,
          "replay_only": true,
          "executes_target_repo_mutation": false,
          "reasons": []
        },
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "production_deployment": false,
        "cleanup_execution": false,
        "reasons": []
      },
      "manifest_result": {
        "status": "PASS",
        "manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "policy_path": "policy/repo_write_policy.yaml",
        "reasons": [],
        "autonomy_policy_path": "policy/autonomy_policy.yaml"
      },
      "pair_binding_result": {
        "status": "PASS",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "binding_mode": "explicit_manifest_change_plan_pair",
        "writes_target_repo": false,
        "executes_target_repo_mutation": false,
        "reasons": []
      },
      "change_plan_result": {
        "status": "PASS",
        "change_plan_path": "examples/change_plans/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "task_manifest_path": "examples/task_manifests/tool_system_ts_b02a_cubesandbox_acceptance_contract_v1.yaml",
        "reasons": []
      },
      "replay_execution_requested": false,
      "validation_to_dispatch_inputs_equal": true
    },
    "input_sha256_before": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "4a2356112ab65c1e6341740ddf766bdfceb2d7f5bb9dec13383ed5547e19d6f1",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "999b4b53034ac8fcc7afe6a9656619c5dbe946347bfc57f2ce1477f010100b5e"
    },
    "input_sha256_after": {
      "autonomy_policy": "0ba97dfde9e0aad86737fe53cdb7e8f21df57a5f0d335baeb595b540f42f5964",
      "change_plan": "4a2356112ab65c1e6341740ddf766bdfceb2d7f5bb9dec13383ed5547e19d6f1",
      "process_authority": "6cead3cee9c89f3b7cde5a579ecf372c633da720aa38c03a4a265d742961346a",
      "repo_write_policy": "9ab121156dd69f2ee231b827699f3378f23094ada5a50d52b866b7eceb9e6005",
      "task_manifest": "999b4b53034ac8fcc7afe6a9656619c5dbe946347bfc57f2ce1477f010100b5e"
    },
    "command_results": [
      {
        "name": "python -B -m tool_system.cli.validate_active_gates tests/fixtures/manifest_validation/strict_active_gates_v1.yaml",
        "exit_code": 0,
        "stdout": "{\n  \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n  \"reasons\": [],\n  \"results\": [\n    {\n      \"autonomy_policy_path\": \"policy/autonomy_policy.yaml\",\n      \"kind\": \"task_manifest\",\n      \"manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n      \"policy_path\": \"policy/repo_write_policy.yaml\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"change_plan_path\": \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n      \"kind\": \"change_plan\",\n      \"reasons\": [],\n      \"status\": \"PASS\",\n      \"task_manifest_path\": \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\"\n    },\n    {\n      \"alignment_gate_enabled\": false,\n      \"checked\": [],\n      \"index_path\": \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n      \"kind\": \"alignment_gate\",\n      \"reasons\": [],\n      \"status\": \"PASS\"\n    }\n  ],\n  \"status\": \"PASS\"\n}\n",
        "stderr": ""
      },
      {
        "name": "python -B -m tool_system.cli.validate_process_authority config/process_authority_v1.yaml",
        "exit_code": 0,
        "stdout": "{\n  \"authority_path\": \"config/process_authority_v1.yaml\",\n  \"cleanup_execution\": false,\n  \"current_task_input_mode\": \"explicit_manifest_change_plan_pair\",\n  \"executes_target_repo_mutation\": false,\n  \"implicit_repository_index_allowed\": false,\n  \"legacy_authority\": false,\n  \"module_id\": \"process-authority\",\n  \"module_version\": \"2.3.0\",\n  \"production_deployment\": false,\n  \"public_interface_id\": \"process-authority-api\",\n  \"public_interface_version\": \"2.1.0\",\n  \"reasons\": [],\n  \"replay_result\": {\n    \"authority\": false,\n    \"executes_target_repo_mutation\": false,\n    \"pair_count\": 108,\n    \"reasons\": [],\n    \"replay_only\": true,\n    \"snapshot_path\": \"/home/rich/projects/tool-system/config/replay_snapshot_v1.yaml\",\n    \"status\": \"PASS\"\n  },\n  \"status\": \"PASS\",\n  \"writes_target_repo\": false\n}\n",
        "stderr": ""
      },
      {
        "name": "python -B -m tool_system.cli.validate_module_registry config/module_registry_v1.yaml --require-current-authority",
        "exit_code": 0,
        "stdout": "{\n  \"compatibility_adapter\": {\n    \"applied\": false,\n    \"authority\": false,\n    \"cache_registry\": false,\n    \"caller_boundary\": \"registry_loader_and_validator_entrypoints_only\",\n    \"current_formal_registry_owner\": \"config/module_registry_v1.yaml\",\n    \"generated_projection\": false,\n    \"mapping_owner_path\": \"docs/tool_system_module_registry_contract_v1.md\",\n    \"persistence\": \"none\",\n    \"persistent_projection\": false,\n    \"registry_files_read\": [\n      \"config/module_registry_v1.yaml\"\n    ],\n    \"second_registry_authority\": false,\n    \"second_schema_authority\": false,\n    \"serializes_projection\": false,\n    \"translation_boundary\": \"memory_only\"\n  },\n  \"contract_reference_count\": 253,\n  \"current_registry_authority\": true,\n  \"declared_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"execution_order\": [\n    \"agent-worker-runtime\",\n    \"blueprint-compiler\",\n    \"development-loop\",\n    \"durable-orchestrator\",\n    \"local-git\",\n    \"manifest-validation\",\n    \"architecture-registry\",\n    \"process-authority\",\n    \"ai-worker-runtime\",\n    \"adaptive-model-portfolio-and-economics\",\n    \"release-governance\",\n    \"operational-observability\",\n    \"record-retention\",\n    \"repository-context\",\n    \"repository-controller\",\n    \"cleanup-planner\",\n    \"state-migration\",\n    \"recovery-planning\",\n    \"subscription-capacity\",\n    \"production-readiness\",\n    \"target-repo-adapter\",\n    \"task-planner\",\n    \"role-runtime\",\n    \"worker-adapter\",\n    \"task-runner\",\n    \"cli-frontend\"\n  ],\n  \"external_provider_count\": 0,\n  \"module_count\": 26,\n  \"observed_import_graph\": {\n    \"adaptive-model-portfolio-and-economics\": [],\n    \"agent-worker-runtime\": [\n      \"role-runtime\",\n      \"worker-adapter\"\n    ],\n    \"ai-worker-runtime\": [\n      \"adaptive-model-portfolio-and-economics\"\n    ],\n    \"architecture-registry\": [],\n    \"blueprint-compiler\": [\n      \"task-runner\"\n    ],\n    \"cleanup-planner\": [\n      \"cli-frontend\"\n    ],\n    \"cli-frontend\": [],\n    \"development-loop\": [\n      \"local-git\",\n      \"task-runner\"\n    ],\n    \"durable-orchestrator\": [\n      \"local-git\",\n      \"process-authority\"\n    ],\n    \"local-git\": [\n      \"task-runner\"\n    ],\n    \"manifest-validation\": [\n      \"architecture-registry\",\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"process-authority\",\n      \"repository-controller\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"operational-observability\": [\n      \"production-readiness\",\n      \"record-retention\"\n    ],\n    \"process-authority\": [\n      \"ai-worker-runtime\",\n      \"task-planner\",\n      \"task-runner\"\n    ],\n    \"production-readiness\": [],\n    \"record-retention\": [\n      \"production-readiness\"\n    ],\n    \"recovery-planning\": [\n      \"production-readiness\"\n    ],\n    \"release-governance\": [\n      \"operational-observability\",\n      \"state-migration\",\n      \"subscription-capacity\"\n    ],\n    \"repository-context\": [\n      \"task-runner\"\n    ],\n    \"repository-controller\": [\n      \"cleanup-planner\",\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"target-repo-adapter\",\n      \"task-runner\",\n      \"worker-adapter\"\n    ],\n    \"role-runtime\": [\n      \"cli-frontend\"\n    ],\n    \"state-migration\": [\n      \"recovery-planning\"\n    ],\n    \"subscription-capacity\": [\n      \"production-readiness\"\n    ],\n    \"target-repo-adapter\": [\n      \"cli-frontend\"\n    ],\n    \"task-planner\": [\n      \"cli-frontend\",\n      \"role-runtime\",\n      \"task-runner\"\n    ],\n    \"task-runner\": [\n      \"cli-frontend\"\n    ],\n    \"worker-adapter\": [\n      \"task-runner\"\n    ]\n  },\n  \"owned_path_count\": 130,\n  \"reasons\": [],\n  \"registry_input_mode\": \"current_module_registry\",\n  \"registry_path\": \"config/module_registry_v1.yaml\",\n  \"required_owned_path_count\": 124,\n  \"status\": \"PASS\",\n  \"validation_scope\": \"tool_system_current_module_registry\"\n}\n",
        "stderr": ""
      },
      {
        "name": "python -B -m tool_system.cli.validate_repo_manifest REPO_MANIFEST.md",
        "exit_code": 0,
        "stdout": "{\n  \"cleanup_authorized\": false,\n  \"executes_target_repo_mutation\": false,\n  \"formal_execution_order\": [\n    \"docs/tool_system_global_development_principles_v1.md\",\n    \".gitignore\",\n    \"blueprint/schema/tool_system_blueprint.schema.json\",\n    \"pyproject.toml\",\n    \"blueprint/tool_system_v0.yaml\",\n    \"config/module_registry_schema_v1.json\",\n    \"config/module_registry_v1.yaml\",\n    \"docs/agent_role_taxonomy_v1.md\",\n    \"docs/model_provider_portfolio_and_economics_contract_v1.md\",\n    \"docs/operator_runbook_and_deprecation_policy_v1.md\",\n    \"docs/tool_system_module_registry_contract_v1.md\",\n    \"docs/tool_system_project_state_v1.yaml\",\n    \"harness/task_manifest.schema.json\",\n    \"policy/autonomy_policy.yaml\",\n    \"tests/fixtures/p14h/python_cli/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/python_cli/STATUS.md\",\n    \"tests/fixtures/p14h/python_cli/blueprint.yaml\",\n    \"tests/fixtures/p14h/typescript_package/GOVERNANCE.md\",\n    \"tests/fixtures/p14h/typescript_package/STATUS.md\",\n    \"tests/fixtures/p14h/typescript_package/blueprint.yaml\",\n    \"tests/test_product_objective_alignment.py\",\n    \"tests/test_ts_b02a_core_local_os_isolation_backend_feasibility.py\",\n    \"config/process_authority_schema_v1.json\",\n    \"config/process_authority_v1.yaml\",\n    \"docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md\",\n    \"docs/modules/agent-worker-runtime-contract-v1.md\",\n    \"docs/modules/ai-worker-runtime-contract-v1.md\",\n    \"docs/modules/architecture-registry-contract-v1.md\",\n    \"docs/modules/blueprint-compiler-contract-v1.md\",\n    \"docs/modules/cleanup-planner-contract-v1.md\",\n    \"docs/modules/cli-frontend-contract-v1.md\",\n    \"docs/modules/development-loop-contract-v1.md\",\n    \"docs/modules/durable-orchestrator-contract-v1.md\",\n    \"docs/modules/local-git-contract-v1.md\",\n    \"docs/modules/manifest-validation-contract-v1.md\",\n    \"docs/modules/operational-observability-contract-v1.md\",\n    \"docs/modules/process-authority-contract-v1.md\",\n    \"docs/modules/production-readiness-contract-v1.md\",\n    \"docs/modules/record-retention-contract-v1.md\",\n    \"docs/modules/recovery-planning-contract-v1.md\",\n    \"docs/modules/release-governance-contract-v1.md\",\n    \"docs/modules/repository-context-contract-v1.md\",\n    \"docs/modules/repository-controller-contract-v1.md\",\n    \"docs/modules/role-runtime-contract-v1.md\",\n    \"docs/modules/state-migration-contract-v1.md\",\n    \"docs/modules/subscription-capacity-contract-v1.md\",\n    \"docs/modules/target-repo-adapter-contract-v1.md\",\n    \"docs/modules/task-planner-contract-v1.md\",\n    \"docs/modules/task-runner-contract-v1.md\",\n    \"docs/modules/worker-adapter-contract-v1.md\",\n    \"config/p15c_execution_packet_freeze_v1.yaml\",\n    \"config/p15d_failure_economics_corpus_prerequisite_v1.yaml\",\n    \"tests/test_p16a_sustainable_operations_specification.py\",\n    \"tests/test_phase_alignment.py\",\n    \"policy/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/src/calculator.py\",\n    \"tests/fixtures/p14h/typescript_package/package.json\",\n    \"tests/fixtures/p14h/typescript_package/src/index.ts\",\n    \"tests/fixtures/p14h/typescript_package/src/legacy.ts\",\n    \"tests/test_p14h_multi_stack_e2e.py\",\n    \"REPO_MANIFEST.md\",\n    \"config/replay_snapshot_v1.yaml\",\n    \"examples/requirements/tool_system_p7d.yaml\",\n    \"examples/task_graphs/tool_system_p7a_task_graph.yaml\",\n    \"src/tool_system/__init__.py\",\n    \"src/tool_system/agent_worker/__init__.py\",\n    \"src/tool_system/agent_worker/interface.py\",\n    \"src/tool_system/agent_worker/process_runtime.py\",\n    \"src/tool_system/ai_worker/__init__.py\",\n    \"src/tool_system/ai_worker/contract.py\",\n    \"src/tool_system/ai_worker/fixture_provider.py\",\n    \"src/tool_system/ai_worker/live_evidence.py\",\n    \"src/tool_system/ai_worker/live_provider.py\",\n    \"src/tool_system/architecture/__init__.py\",\n    \"src/tool_system/architecture/module_registry.py\",\n    \"src/tool_system/architecture/repo_manifest.py\",\n    \"src/tool_system/blueprint_compiler/__init__.py\",\n    \"src/tool_system/blueprint_compiler/compiler.py\",\n    \"src/tool_system/cleanup/__init__.py\",\n    \"src/tool_system/cleanup/residue_plan.py\",\n    \"src/tool_system/cli/__init__.py\",\n    \"src/tool_system/cli/cleanup_plan.py\",\n    \"src/tool_system/cli/controller_run.py\",\n    \"src/tool_system/cli/controller_self_check.py\",\n    \"src/tool_system/cli/evaluate_github_state.py\",\n    \"src/tool_system/cli/evaluate_repo_write.py\",\n    \"src/tool_system/cli/execute_change_plan.py\",\n    \"src/tool_system/cli/main.py\",\n    \"src/tool_system/cli/observe_main_ci.py\",\n    \"src/tool_system/cli/plan_requirement.py\",\n    \"src/tool_system/cli/plan_task_graph.py\",\n    \"src/tool_system/cli/run_batch.py\",\n    \"src/tool_system/cli/run_role_graph.py\",\n    \"src/tool_system/cli/run_stage.py\",\n    \"src/tool_system/cli/run_task.py\",\n    \"src/tool_system/cli/run_task_graph.py\",\n    \"src/tool_system/cli/target_repo_dry_run.py\",\n    \"src/tool_system/cli/target_repo_pr_plan_preview.py\",\n    \"src/tool_system/cli/validate_active_gates.py\",\n    \"src/tool_system/cli/validate_alignment_gate.py\",\n    \"src/tool_system/cli/validate_change_plan.py\",\n    \"src/tool_system/cli/validate_module_registry.py\",\n    \"src/tool_system/cli/validate_process_authority.py\",\n    \"src/tool_system/cli/validate_repo_manifest.py\",\n    \"src/tool_system/cli/validate_task_manifest.py\",\n    \"src/tool_system/development_loop/__init__.py\",\n    \"src/tool_system/gate/README.md\",\n    \"src/tool_system/gate/__init__.py\",\n    \"src/tool_system/gate/alignment_gate.py\",\n    \"src/tool_system/gate/change_plan.py\",\n    \"src/tool_system/gate/command_runner.py\",\n    \"src/tool_system/gate/test_gate.py\",\n    \"src/tool_system/local_git/__init__.py\",\n    \"src/tool_system/manifest/__init__.py\",\n    \"src/tool_system/manifest/task_manifest.py\",\n    \"src/tool_system/orchestrator/__init__.py\",\n    \"src/tool_system/planner/__init__.py\",\n    \"src/tool_system/planner/requirement_graph.py\",\n    \"src/tool_system/planner/task_graph.py\",\n    \"src/tool_system/policy/__init__.py\",\n    \"src/tool_system/policy/autonomy_policy.py\",\n    \"src/tool_system/policy/repo_write_policy.py\",\n    \"src/tool_system/process_authority/__init__.py\",\n    \"src/tool_system/process_authority/contract.py\",\n    \"src/tool_system/provider_portfolio/__init__.py\",\n    \"src/tool_system/provider_portfolio/fixtures.py\",\n    \"src/tool_system/repo_controller/__init__.py\",\n    \"src/tool_system/repo_controller/actions.py\",\n    \"src/tool_system/repo_controller/artifact.py\",\n    \"src/tool_system/repo_controller/audit_log.py\",\n    \"src/tool_system/repo_controller/controller.py\",\n    \"src/tool_system/repo_controller/controller_run.py\",\n    \"src/tool_system/repo_controller/github_state.py\",\n    \"src/tool_system/repo_controller/live_github_collector.py\",\n    \"src/tool_system/repo_controller/main_ci.py\",\n    \"src/tool_system/repo_controller/self_check.py\",\n    \"src/tool_system/repository_context/__init__.py\",\n    \"src/tool_system/repository_context/builder.py\",\n    \"src/tool_system/runner/active_gate_resolver.py\",\n    \"src/tool_system/runner/stage_runner.py\",\n    \"src/tool_system/runner/task_graph_runner.py\",\n    \"src/tool_system/runtime/__init__.py\",\n    \"src/tool_system/runtime/audit_bundle.py\",\n    \"src/tool_system/runtime/role_runtime.py\",\n    \"src/tool_system/runtime/transition_gate.py\",\n    \"src/tool_system/target_repo/__init__.py\",\n    \"src/tool_system/target_repo/dry_run_adapter.py\",\n    \"src/tool_system/target_repo/execution_approval.py\",\n    \"src/tool_system/target_repo/execution_state_snapshot.py\",\n    \"src/tool_system/target_repo/mutation_command_packet.py\",\n    \"src/tool_system/target_repo/p4c_preview_module.py\",\n    \"src/tool_system/target_repo/p4d_precheck.py\",\n    \"src/tool_system/target_repo/p5h_record.py\",\n    \"src/tool_system/target_repo/p5i_bundle.py\",\n    \"src/tool_system/target_repo/pr_plan_preview.py\",\n    \"src/tool_system/target_repo/state_collector.py\",\n    \"src/tool_system/target_repo/write_intent_record.py\",\n    \"src/tool_system/target_repo/write_packet.py\",\n    \"src/tool_system/worker_adapter/__init__.py\",\n    \"src/tool_system/worker_adapter/policy_gate.py\",\n    \"src/tool_system/development_loop/loop.py\",\n    \"src/tool_system/orchestrator/durable.py\",\n    \"src/tool_system/local_git/orchestrator.py\",\n    \"src/tool_system/production_readiness/__init__.py\",\n    \"src/tool_system/production_readiness/policy.py\",\n    \"src/tool_system/release_governance/__init__.py\",\n    \"src/tool_system/release_governance/policy.py\",\n    \"harness/cubesandbox_backend_acceptance_v1.schema.json\",\n    \"src/tool_system/runner/task_runner.py\",\n    \"src/tool_system/worker_adapter/contract.py\",\n    \"src/tool_system/worker_adapter/orchestration.py\",\n    \"examples/operator_config/tool_system_settings.example.toml\",\n    \"src/tool_system/ai_worker/p15c_controls.py\",\n    \"tests/test_p15c_execution_packet_freeze.py\",\n    \"tests/test_p15d_failure_economics_corpus_prerequisite.py\",\n    \"tests/fixtures/target_repo/repo_write_policy.yaml\",\n    \"tests/fixtures/manifest_validation/forward_valid_change_plan_v1.yaml\",\n    \"tests/fixtures/p14h/python_cli/tests/calculator_spec.py\",\n    \"tests/fixtures/p14h/typescript_package/tests/index.test.ts\",\n    \".github/workflows/tool-system-ci.yml\",\n    \"AGENTS.md\",\n    \"README.md\",\n    \"docs/process_authority_contract_v1.md\",\n    \"examples/batches/tool_system_batch_runner.yaml\",\n    \"examples/batches/tool_system_resolved_batch.yaml\",\n    \"examples/cleanup/tool_system_residue_state.yaml\",\n    \"examples/gate_decisions/pass.yaml\",\n    \"examples/github_states/tool_system_p3b_pass.yaml\",\n    \"examples/repo_write_decisions/tool_system_p3_pass.yaml\",\n    \"tests/fixtures/p11_worker_fixture.py\",\n    \"tests/test_active_gate_resolver.py\",\n    \"tests/test_active_gates.py\",\n    \"tests/test_agent_role_taxonomy.py\",\n    \"tests/test_agent_worker_interface.py\",\n    \"tests/test_ai_worker_contract.py\",\n    \"tests/test_ai_worker_fixture_provider.py\",\n    \"tests/test_ai_worker_live_provider.py\",\n    \"tests/test_alignment_gate.py\",\n    \"tests/test_audit_bundle.py\",\n    \"tests/test_blueprint_compiler.py\",\n    \"tests/test_change_plan_gate.py\",\n    \"tests/test_change_plan_scope_extra.py\",\n    \"tests/test_cleanup_plan.py\",\n    \"tests/test_command_runner.py\",\n    \"tests/test_controller_actions.py\",\n    \"tests/test_controller_run.py\",\n    \"tests/test_controller_self_check.py\",\n    \"tests/test_development_loop.py\",\n    \"tests/test_durable_orchestrator_recovery.py\",\n    \"tests/test_durable_orchestrator_side_effects.py\",\n    \"tests/test_durable_orchestrator_state.py\",\n    \"tests/test_execution_approval.py\",\n    \"tests/test_execution_state_snapshot.py\",\n    \"tests/test_final_record.py\",\n    \"tests/test_github_state_adapter.py\",\n    \"tests/test_global_principles.py\",\n    \"tests/test_live_github_collector.py\",\n    \"tests/test_local_git_orchestrator.py\",\n    \"tests/test_main_ci.py\",\n    \"tests/test_milestone_module_invariant.py\",\n    \"tests/test_module_contracts.py\",\n    \"tests/test_module_import_graph.py\",\n    \"tests/test_module_registry.py\",\n    \"tests/test_multi_task.py\",\n    \"tests/test_mutation_command_packet.py\",\n    \"tests/test_p10r_a_machine_policy_enforcement.py\",\n    \"tests/test_p13_integrated_security_reliability.py\",\n    \"tests/test_p14_phase_entry_contract.py\",\n    \"tests/test_p14c_execution_contract.py\",\n    \"tests/test_p4d_precheck.py\",\n    \"tests/test_process_authority.py\",\n    \"tests/test_process_worker_runtime_adversarial.py\",\n    \"tests/test_process_worker_runtime_execution.py\",\n    \"tests/test_process_worker_runtime_preflight.py\",\n    \"tests/test_provider_portfolio_fixtures.py\",\n    \"tests/test_repo_controller.py\",\n    \"tests/test_repo_manifest.py\",\n    \"tests/test_repository_context_builder.py\",\n    \"tests/test_requirement_graph.py\",\n    \"tests/test_role_runtime.py\",\n    \"tests/test_role_transition_gate.py\",\n    \"tests/test_root_cli.py\",\n    \"tests/test_runtime_audit_bundle.py\",\n    \"tests/test_stage_runner.py\",\n    \"tests/test_state_collector.py\",\n    \"tests/test_target_repo_dry_run.py\",\n    \"tests/test_target_repo_pr_plan_preview.py\",\n    \"tests/test_task_graph.py\",\n    \"tests/test_task_graph_runner.py\",\n    \"tests/test_task_manifest_policy.py\",\n    \"tests/test_worker_adapter_contract.py\",\n    \"tests/test_worker_adapter_orchestration.py\",\n    \"tests/test_worker_adapter_policy_gate.py\",\n    \"tests/test_write_intent.py\",\n    \"tests/test_write_packet.py\",\n    \"src/tool_system/ai_worker/runtime.py\",\n    \"src/tool_system/provider_portfolio/failure_control.py\",\n    \"tests/test_target_identity_decoupling.py\",\n    \"tests/test_durable_orchestrator_reliability.py\",\n    \"tests/test_production_readiness.py\",\n    \"src/tool_system/operational_observability/__init__.py\",\n    \"src/tool_system/state_migration/__init__.py\",\n    \"src/tool_system/subscription_capacity/__init__.py\",\n    \"src/tool_system/operational_observability/policy.py\",\n    \"src/tool_system/state_migration/planner.py\",\n    \"src/tool_system/subscription_capacity/policy.py\",\n    \"tests/test_release_governance.py\",\n    \"tests/cubesandbox_contract_oracle.py\",\n    \"tests/fixtures/cubesandbox_backend_acceptance_v1.json\",\n    \"tests/test_task_runner.py\",\n    \"examples/operator_config/tool_system_credentials.example.toml\",\n    \"src/tool_system/ai_worker/p15c_benchmark.py\",\n    \"tests/test_ai_worker_p15c_controls.py\",\n    \"tests/fixtures/target_repo/task_manifest.yaml\",\n    \"tests/fixtures/manifest_validation/strict_active_gates_v1.yaml\",\n    \"tests/test_central_governance_consumption.py\",\n    \"tests/test_model_provider_portfolio_contract.py\",\n    \"src/tool_system/process_authority/live_provider_approval.py\",\n    \"src/tool_system/provider_portfolio/provider_mode.py\",\n    \"tests/test_ai_worker_provider_mode.py\",\n    \"tests/test_provider_portfolio_failure_control.py\",\n    \"src/tool_system/record_retention/__init__.py\",\n    \"src/tool_system/recovery_planning/__init__.py\",\n    \"src/tool_system/record_retention/policy.py\",\n    \"tests/test_operational_observability.py\",\n    \"src/tool_system/recovery_planning/planner.py\",\n    \"tests/test_state_migration.py\",\n    \"tests/test_subscription_capacity.py\",\n    \"tests/test_cubesandbox_backend_acceptance_contract.py\",\n    \"src/tool_system/ai_worker/p15c_entry.py\",\n    \"tests/test_ai_worker_p15c_benchmark.py\",\n    \"tests/test_target_repo_dry_run_probe.py\",\n    \"tests/test_p14c_live_issuer.py\",\n    \"tests/test_provider_portfolio_provider_mode.py\",\n    \"tests/test_record_retention.py\",\n    \"tests/test_recovery_planning.py\",\n    \"tests/test_ai_worker_p15c_entry.py\",\n    \"tests/test_p15c_local_operator_config.py\"\n  ],\n  \"formal_file_count\": 299,\n  \"formal_path_count\": 299,\n  \"formal_set_count\": 0,\n  \"legacy_path_count\": 543,\n  \"legacy_set_count\": 6,\n  \"manifest_path\": \"REPO_MANIFEST.md\",\n  \"parser_mode\": \"exact_formal_files\",\n  \"reasons\": [],\n  \"retained_inputs_are_current_authority\": false,\n  \"status\": \"PASS\",\n  \"tracked_path_count\": 842,\n  \"unclassified_path_count\": 0,\n  \"writes_target_repo\": false\n}\n",
        "stderr": ""
      },
      {
        "name": "git --no-optional-locks --no-pager diff --check --no-ext-diff --no-textconv HEAD --",
        "exit_code": 0,
        "stdout": "",
        "stderr": ""
      }
    ],
    "subprocess_call_count": 5,
    "reasons": [],
    "source_before": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "source_after": {
      "REPO_MANIFEST.md": "73eac2c5ea05a8e88d9f91cd590aee572c277d21264e8f4c37475b7331fa2e59",
      "docs/reports/ts_b02a_cubesandbox_backend_acceptance_contract_v1.md": "43be50411d826033c550b43343f45b83b8e164c98d038cfa5de1417d425794fe",
      "harness/cubesandbox_backend_acceptance_v1.schema.json": "0437963d1d2e7e74e9177960825c5f498406cdd60ae40ae8b6f6197d8576486f",
      "tests/cubesandbox_contract_oracle.py": "4bbbd58893ed41a57fa3003fa577652ebf17b1b55b9c79ed0cbb242818815326",
      "tests/fixtures/cubesandbox_backend_acceptance_v1.json": "7ba03d4a5f7233a009a02bca2cb61a8c0197535fbf05ee15720041b240ec0f5f",
      "tests/test_cubesandbox_backend_acceptance_contract.py": "a4320a3ad249cde550964acf7dedb05fb6acc2bfcaacc6fdc578ff5b73741785",
      "tests/test_repo_manifest.py": "98f644e569cd0a65b776437a989589ac6e80c302887a8d47014741769e98f362"
    },
    "parent_before": {
      "PATH_sha256": "236151d1e5208af63b2fd0aa80355a3ae23b70394f6e67fbf0e15be2c0d6f21c",
      "umask": "0002"
    },
    "parent_after": {
      "PATH_sha256": "236151d1e5208af63b2fd0aa80355a3ae23b70394f6e67fbf0e15be2c0d6f21c",
      "umask": "0002"
    }
  }
}
```

Current whole-repository result: PASS in this explicitly scoped source-test environment, 1072 passed, no skipped cases, not a replacement for any historical failed receipt. Original failures remain above. Cumulative correction 4, directed total 8 (original contract rounds 7 plus this three-case confirmation), full suites 3, baseline 1, branches 1, candidate paths 10. This authorization used Node preparation 1/1, confirmation 1/1, full suite 1/1 and final governance/identity batch 1/1; one exact three-record staging is reserved next. No algorithms, protected source, baseline, remote publishing, ZIP or real backend operations. External 37/37 review remains external and separate from author tests.

Remaining real-backend prerequisites include frozen lifecycle-manager ARM64 digest and complete approved artifact/observer closure plus separate exact host authorization; no real acceptance follows from pytest PASS.

REAL_BACKEND_ACCEPTANCE_EXECUTED=false
REAL_BACKEND_ACCEPTANCE_AUTHORIZED=false


## Bounded commit / ordinary push / Draft PR authorization (2026-09-09)

The latest explicit same-task user instruction opens only one local commit on the existing candidate branch, one ordinary same-name push to apolo183/tool-system, and one Draft PR to main. It permits the unchanged existing PR workflow to run automatically and read-only verification of that run. Earlier publication prohibitions and consumed budgets remain historical records; only this finite permission supersedes those prohibitions. No merge, auto-merge, Ready transition, force push, rebase/amend, branch replacement/deletion, dependency installation, workflow/policy change or host/backend action is permitted.

Authenticated GitHub main-ref then commit-object reads match HEAD 306a01fa6bf3bc8ed4204b88abdcb4f16f75360e and tree ec74af108b6f1d7d4c9c7e440aec128261f3f251. Initial staged patch matches 8552bc02191e4ce7eebd8b99f3d20c0d13b2749c1bf0f55af3768c30ae7eb45c using the original no-external-diff/no-textconv command. All ten staged files equal their worktree bytes; all seven reviewed/protected hashes match the retained full-validation record. Initial authenticated duplicate checks found no same-name remote branch or PR; the mechanical wrapper checks again before mutation.

Raw full.stdout ends with 1072 passed in 79.62s; full-exit.json records exit 0 and no timeout; full.xml independently records 1072 tests, zero failures/errors/skips. Execution-time full-manifest/full-plan snapshots match dispatcher input hashes, and protected source hashes match before/after. This is the completed local task-scoped source-test result. Author contract tests 160 passed and external independent R1-R4 review 37/37 are separate retained evidence. Hosted CI has not occurred for this publication and is PENDING; no commit SHA, PR number or CI success is prefilled.

Only this evidence, the original task manifest and original change plan are updated for publication. The seven contract/oracle/Schema/fixture/test/manifest files remain reviewed/tested bytes. The ten intended files and exact PR body are inspected for sensitive values and unrelated private content before staging/commit; no shell configuration, credential source, complete environment dump, Node binary/archive or unrelated raw temporary material is published.

Use the existing protected task-pair dispatcher with the exact original manifest/plan/policy/cwd bindings. The task-local mechanical wrapper captures mutation argv/exit and readbacks, stages the exact three records once, commits the original ten paths once, checks parent/tree/path closure and clean index/worktree, pushes only the original branch without force, reads its SHA back, creates one Draft PR, and verifies head/base/Draft and unchanged canonical main. A failed or uncertain write stops for read-only reconciliation, never a renamed branch, extra commit or duplicate PR. After commit no repository file is edited to chase PR/CI evidence; actual publication and Hosted results belong in the final external receipt.

Publication receipt root: /tmp/tool-system-ts-b02a-draft-publication-j80aea3j. This named external temporary exception stores only this task's PR body and command/identity/CI receipts; retain for independent review, no automatic cleanup and no raw-directory upload. It creates no formal repository path or parallel governance mechanism. Direct parent topology/conditional-host boundaries and blueprint product_objective remain unchanged: publishing fixture contracts grants no execution evidence or host authority.

New limits: record update/validation batch 1; exact three-record staging 1; local commit 1; ordinary push 1; Draft PR 1; automatic Hosted run 1; CI wait at most 30 minutes with status queries at least 60 seconds apart. New algorithm fixes, local pytest, ZIP export and host operations 0. Preserve cumulative correction 4, directed 8, local full suites 3, baseline 1, branch 1, paths 10. Hosted runs are accounted separately. Keep Draft on success, failure or pending timeout; no automatic next milestone.

Real prerequisites remain unfrozen lifecycle-manager ARM64 digest and approved artifact/observer closure, systemd termination interface and independently authorized host acceptance. Published provenance/SBOM attestations absent from upstream v0.7.0 are not completed evidence.

REAL_BACKEND_ACCEPTANCE_EXECUTED=false
REAL_BACKEND_ACCEPTANCE_AUTHORIZED=false
