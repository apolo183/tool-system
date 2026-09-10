# TS-B02A CubeSandbox backend acceptance contract v1

Task: `TOOL-SYSTEM-TS-B02A-CUBESANDBOX-V070-ARM64-BACKEND-ACCEPTANCE-CONTRACT-v1`.
Disposition: source, contract and synthetic evidence only; independent review pending.
`authority_effect: none`. This document grants no execution, installation,
service, network, VM, publication, milestone acceptance or cleanup authority.

## 1. Parent, objective and existing mechanisms

The direct parent is
`subscription_worker_ts_b02a_dgx_spark_linux_arm64_primary_target_and_ephemeral_kvm_isolation_path_realignment_specification_v1.md`,
especially sections 9–11. Its inventory, conditional enablement, bounded probe,
and future TS-B02A/B/C/D implementation/acceptance remain distinct. This contract
specializes the requested evidence for one upstream candidate. It neither selects
that candidate as an accepted runtime nor reopens the stopped PR #231 authority.
The global anchor is `blueprint/tool_system_v0.yaml:product_objective`: bounded
isolated development and evidence without silent scope expansion. The existing
arbitrary-untrusted-code-containment non-goal and trusted-host boundary remain.

This proposal uses the existing directory and governance structure:

| Mechanism | Reuse and boundary |
| --- | --- |
| `config/process_authority_v1.yaml` and explicit manifest/change-plan pair | Sole current task authority; unchanged. The task pair permits only local candidate work. `write_mode: pull_request` denotes the existing branch-change workflow; the explicit user prohibition overrides any implied publication step. No PR or commit is permitted. |
| `harness/` and `jsonschema.Draft202012Validator` | Existing Schema 2020-12 dependency and local-definition pattern; no new schema engine, resolver or governance registry. |
| `development-loop-api`, `FrozenDevelopmentContract`, Validator callback | Four fixed acceptance items, standard `validation_results` and `satisfied_acceptance_items`; fixture tests consume these through the existing pure loop. `FAIL` and `BLOCKED` map to existing `BLOCK`, preserving exact reasons in diagnostics. |
| `runner/task_runner.py` execution-binding-v2 obligations and receipts | Existing `subscription_acceptance_evidence_obligation_v1` and `subscription_acceptance_evidence_receipt_v1` remain the code-development acceptance mechanism. Future integration uses one existing `contract` or `behavior` obligation per item, exact command/output hashes, candidate assertions, tree and diff. This task neither duplicates their schema nor fabricates runner-issued receipts. Code-review acceptance is not host acceptance. |
| `gate/test_gate.py` | Command exit checking only; never a substitute for G1–G4. |
| `production_readiness/policy.py` | P16 operations evidence has different scope; unchanged and supplies no CubeSandbox acceptance. |
| Parent `IsolationRequestV1` / `ExecutionEvidenceV1` | Caller request versus provider observations and consumer revalidation remain separate. This test specialization is not a new runtime interface or provider adapter. |

The machine contract is `harness/cubesandbox_backend_acceptance_v1.schema.json`.
The evaluator is **test-only** `tests/cubesandbox_contract_oracle.py`; it accepts
in-memory JSON and an independently supplied catalog, uses no host I/O, and blocks
`host_os` input with `REAL_HOST_IMPORT_NOT_IMPLEMENTED_OR_AUTHORIZED`. It cannot
issue a host receipt, approve a catalog, invoke a command or start a workload.
The schema describing `host_os` data is a proposed record shape, not a usable
live importer. Host observation/normalization/validation is a future prerequisite.

## 2. Frozen upstream identity and source findings

| Field | Frozen value |
| --- | --- |
| Repository | `TencentCloud/CubeSandbox` |
| Product release | `v0.7.0` |
| Source commit | `d0081641c59822e4e5653b7462e914410b81910a` |
| Release workflow run | `33152639150`; queried metadata reports attempt 2, completed/success, matching commit and tag |
| Architecture | `linux/arm64` |
| cube-egress per-arch OCI manifest | `sha256:1fc7ed98650e91edb8ead48094950370ed30c0e7016796c3036063ccc6e4ea71` — user-frozen digest, not independently pulled or run in this task |
| Proposed registry reference | `ghcr.io/tencentcloud/cube-egress@sha256:1fc7ed98650e91edb8ead48094950370ed30c0e7016796c3036063ccc6e4ea71`; registry-resolution and manifest/config ARM64 proof still required before a probe |
| cube-lifecycle-manager ARM64 digest | **null / UNFROZEN / G1 BLOCKED**; `v0.7.0-arm64` is only a discovery label |

At the frozen source, per-architecture image publication explicitly sets
`provenance: false` and explains that provenance/SBOM attestations are not
published. No published attestation is claimed or counted as a satisfied gate.
The release run is build metadata, not a signed source-to-runtime attestation.
Source/blob identity, workflow-input binding, exact OCI manifest/config/layer
hashes, extracted-artifact hashes and future operator approval must be recorded
separately. If their chain is incomplete, G1 stays BLOCKED; a contradictory chain
is FAIL. Do not substitute a tag, workflow success or an invented attestation.
[Workflow source](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/.github/workflows/release-docker-images.yml#L725),
[release run](https://github.com/TencentCloud/CubeSandbox/actions/runs/33152639150).

The upstream network interface says `ReleaseNetwork` returns after cleanup
ownership is handed off, possibly before kernel effects finish. TAP lifecycle
source retains FDs for pooled TAPs and resets policy before reuse. These source
facts motivate asynchronous observation and explicit pool attribution; they
prove no host cleanup behavior.
[Network interface](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/Cubelet/network/runtime/network_runtime.go),
[TAP lifecycle](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/Cubelet/network/runtime/tap_lifecycle.go).

Upstream destroy logic captures runtime PIDs before deleting the task and waits
before storage cleanup. Its presence does not establish PID1 FD release,
asynchronous-close completion or complete process discovery on the target host.
[Destroy wait source](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/Cubelet/services/cubebox/destroy_shim_wait.go).

Upstream documentation distinguishes cloning into new sandboxes from rollback
that preserves logical sandbox ID. Runtime snapshot labels separately track
snapshot attachment and the actual last restore base. The contract below adopts
explicit generation and restored-state comparisons, rather than assuming labels
alone prove restored contents.
[Snapshot guide](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/docs/guide/snapshot-rollback-clone.md),
[restore binding](https://github.com/TencentCloud/CubeSandbox/blob/d0081641c59822e4e5653b7462e914410b81910a/Cubelet/services/cubebox/snapshot_runtime_binding.go).

## 3. Common evidence and verdict contract

Each gate is independently evaluated as `PASS`, `FAIL`, or `BLOCKED`.
Aggregate precedence is **FAIL > BLOCKED > PASS**. PASS requires every gate to
pass; no WARN, skipped, xfail, ACK or success-code conversion is permitted.
Known contradiction, identity collision, integrity mismatch, observed deadline
failure or owned resource surviving the deadline is FAIL. Missing digest,
permission, observer coverage or unfinished bounded observation is BLOCKED;
failure to establish the terminal condition by the deadline is FAIL. A positive
violation is retained even when another gate is BLOCKED. These are result values
in this contract, not new module lifecycle or governance states.

Example shape (values are illustrative, never execution authority):

```json
{"gate":"COMPONENT_VERSION_BINDING","status":"BLOCKED","reasons":["cube-lifecycle-manager:APPROVED_DIGEST_MISSING"],"components":[{"component_name":"cube-lifecycle-manager","status":"BLOCKED","reasons":["APPROVED_DIGEST_MISSING"]}]}
```

Before any future host probe, an independently approved package must bind the
catalog bytes/hash, complete executable and observer closure, backend effective
configuration hash, host boot/kernel/architecture, run nonce, scenario IDs and
owners, observer identity/digest, raw-output limits, monotonic clock source,
deadline origin, per-kind enumeration scope, and exact commands/effects. Every
raw sample binds that same run and carries its raw artifact hash; missing,
truncated, reordered, duplicated or unreadable observations cannot mean absence.
The future trusted provider must normalize actual OS observations into the
closed schema and retain their raw bytes. Boolean completeness fields describe
that verified coverage, not caller permission to assert completeness. A supplied
hash or `status=PASS` is not independent evidence. No real importer or observer
is implemented here; fixture identities and hashes are deliberately synthetic.

The approved component catalog is supplied separately from observations. The
observer cannot rewrite expectations to match its results. Duplicate JSON keys,
non-finite numbers, unknown fields, type confusion, duplicate identity keys and
missing required structure fail closed. The fixture parser bounds input at
2 MiB. All hashes are lowercase SHA-256; canonical structured hashing uses JSON
with sorted keys, ASCII escaping and separators `,` and `:`. Raw byte hashes are
hashes of the actual bytes, with no newline or whitespace normalization.

## 4. G1 — COMPONENT_VERSION_BINDING

For every execution component record `component_name`, `release_tag`,
`source_commit`, `architecture`, `artifact_type`, `requested_ref`,
`binding_evidence`, and the complete `embedded_artifacts` list. OCI components
have `artifact_type=oci_image`, a registry and per-architecture `oci_digest`,
and null `file_identity`. Ordinary files have `artifact_type=file`, null registry
and OCI digest, and `file_identity={path,sha256}`; their requested path and actual
file hash must match the approved identity. The schema rejects an OCI digest
on a file. Egress and lifecycle-manager remain OCI components. The approved
catalog's `required_components` must exactly match its component list, and the
observed execution closure must match it without duplicate or extra entries.
`closure_complete` and `component_inventory_complete` must be established from
the selected deployment and actual process/image inventory, not just an image
name allowlist. Missing observations or an incomplete closure block.

The minimum explicitly named closure is cubelet, cube-shim, cube-kernel,
cube-guest, cube-agent, cube-egress and cube-lifecycle-manager. This is a floor,
not a claim that seven images cover a real deployment. All used controller,
manager, cube-master, API/proxy, cube-egress-net, node-init/wait helpers, storage,
container runtime, database/cache, DNS and other support components must be
enumerated or explicitly excluded with source/effective-topology evidence.
Host executables not distributed as OCI components need an approved enclosing
distribution identity and exact executable/loader/library hashes; they cannot
be assigned a fictitious OCI digest. That selected deployment closure is not
frozen here and remains a probe blocker.

For OCI artifacts, resolve the **linux/arm64 child manifest**, config platform
and every referenced blob, not merely a multiarch index. Record the index digest
as additional raw evidence if used; it cannot replace the child digest. Before
execution and after restore, actual resolved digest must equal approved digest,
and the executed reference must be `registry@sha256:<64 hex>`. `latest`,
`v0.7.0`, `v0.7.0-arm64` and any other mutable tag alone are rejected even when
they currently resolve to an expected image. Version, commit, architecture,
registry or digest mismatch makes G1 and overall backend acceptance FAIL.

VMM, shim helpers, guest kernel, guest rootfs and agent also require byte hashes
and explicit source/platform bindings as embedded artifacts, including any
dedicated-release provenance from `deploy/release-assets.yaml`. The product
release does not imply those external sources have the product commit. The
synthetic fixture's product-commit values are test data, not a real asset claim.
An empty actual asset closure is not an accepted substitute for these assets.

The independently supplied catalog's `required_artifacts` participates directly
in G1, including component owner, artifact name and type. The test oracle also
enforces this non-erasable minimum: cube-shim hypervisor and shim-helper,
cube-kernel guest-kernel, cube-guest guest-rootfs, and cube-agent guest-agent,
all ordinary files with path, source commit, ARM64 architecture and byte SHA-256.
Additional catalog obligations are conjunctive. Jointly clearing the catalog
and observation asset lists, even while also clearing declared obligations,
returns `REQUIRED_ARTIFACT_MISSING / BLOCKED`; it cannot pass. Observed closure,
source, type, architecture, path or hash contradictions fail. Missing approved
file/OCI identities block. Synthetic kernel/rootfs/agent components use actual
file-shaped identities; their fixture paths are illustrative, not a proposed
host installation location or an invented OCI distribution.

`tests/fixtures/cubesandbox_backend_acceptance_v1.json:candidate_catalog` keeps
the real candidate incomplete. In particular, the lifecycle-manager digest is
null. It **must block G1 before a host probe can be approved**, never WARN or a
guessed digest. `synthetic_catalog` uses visibly labelled synthetic digests to
exercise the PASS branch; none of them authorize a pull or execution.

## 5. G2 — ABNORMAL_TERMINATION_COMPLETE_REAP

Every termination case joins by canonical owner to exactly one G4 runtime
record, and their `execution_id` values must agree. Duplicate or missing joins
and single-record execution contradictions are `EXECUTION_JOIN_MISMATCH / FAIL`
in both G2 and G4. This applies to all six scenarios, including those not
referenced by a snapshot. Independent scenarios keep distinct execution IDs;
only records describing the same owner/execution are joined.

Freeze `termination_deadline = 60000 ms` from the **observed trigger**, using
the host monotonic clock, and `poll_interval = 250 ms` maximum. Include observer
execution time in this budget; no indefinite retry or extension. Require two
consecutive fully observed empty samples separated by at most 250 ms and both
no later than the deadline. Poll records must be strictly increasing, start no
later than 250 ms, and preserve intervening failures. Missing coverage is
BLOCKED before the deadline and FAIL if completion remains unproved at it.

| Required condition | Independent observations |
| --- | --- |
| `required_process_absence` | payload, VMM, execution-owned controller and all helpers/async-close processes absent; track `(host_boot_id, pid, start_ticks, pid_namespace, scope)` and owner, not PID number alone. Include descendants, reparented/double-forked processes, escaped cgroups and zombies until reaped. Guest payload identity/exit must be observed through the protected guest observer; VMM disappearance alone does not prove its exit history. |
| `required_fd_absence` | No sandbox stdio pipe/socket/file object remains retained by PID1, controller, helper or close worker. Record holder identity, fd number and kernel object identity from the active state; scan PID1 and all attributable holders even after the unit disappears. Inability to inspect PID1 FDs blocks before injection. |
| `required_cgroup_empty` | Every owned subtree has no members and `populated=0`, or its disappearance plus an independent process scan proves complete removal. A missing main PID is insufficient; deletion is not evidence of absence of escaped members. |
| `required_unit_absence` | Execution-owned unit removed, keyed by manager identity/boot and InvocationID, without a substituted unit reusing the name. Long-lived host control-plane services must be frozen separately as shared resources, never called execution-owned cleanup. |
| `required_helper_absence` | Controller helper processes and asynchronous close / `(sd-close)` helpers absent, including those outside the disappeared unit's cgroup. Process name alone is insufficient attribution; bind ancestry, birth identity and retained FD object. |

Active witnesses must show the expected payload/VMM/controller/helper roles
and an actual occupied cgroup/unit before termination. Every
sample includes explicit process, FD, cgroup, unit and helper scan completeness.
An empty list without complete enumeration is not a negative observation.
The fixture includes a PID1-retained-FD positive control, but retaining such an
FD is not a prerequisite imposed on every real channel. A complete active scan
may observe no PID1 retention, followed by complete negative terminal scans.
This changes no requirement to enumerate relevant FD holders and execution-owned
helpers, including async-close helpers outside a unit. It authorizes no sealed
stdin/h route, control-channel workaround, systemd change or helper exemption.
Both final samples must each be complete AND empty. At the deadline, an
incomplete penultimate FD scan followed by only one complete empty sample is
`REAP_DEADLINE_UNPROVED / FAIL`, never BLOCKED or PASS.

ACK, EOF, payload or main-process exit, unit inactive/disappeared,
`systemctl stop` returning zero, or cgroup main-PID disappearance **cannot alone
pass**. All conjunctive conditions must hold. A residual helper with a vanished
unit at the deadline is `REAP_DEADLINE_RESIDUE / FAIL`; a final empty sample first
observed after 60000 ms is `TERMINATION_DEADLINE_EXCEEDED / FAIL`.

Every approved host matrix must include:

| Case | Trigger to observe and retain |
| --- | --- |
| A normal_exit | Known synthetic payload completion; observe asynchronous destroy/reap |
| B payload_sigkill | Exact synthetic payload identity receives SIGKILL |
| C controller_death | Exact execution controller abnormal death; independently surviving observer records descendant cleanup |
| D vmm_death | Exact VMM abnormal death; payload and retained FD outcomes remain separate |
| E timeout | Frozen workload deadline fires; reap deadline starts at observed timeout trigger |
| F service_forced_termination | Exact execution-owned service forced termination, not a shared host manager |

No fault injection is executable in this stage. In particular, VMM/controller
crash probes require the parent's host pipe-core-handler containment and exact
possible audit/core side effects to be approved first. Shared manager death is
not silently substituted for execution-controller death.

## 6. G3 — SNAPSHOT_RESTORE_INTEGRITY

Freeze a snapshot record containing snapshot ID, source identity, component
catalog hash, filesystem sentinel bytes/hash, checkpoint-process state hashes,
host-process identities and the protected negative-control marker path.

1. Write a synthetic sentinel **before snapshot** in a future approved workload.
   Capture exact path, bytes as `content_hex`, and SHA-256. After snapshot, write
   a different marker at `post_snapshot_path` and mutate the sentinel. Each
   restore must yield the pre-snapshot sentinel bytes and hash, and the marker
   must be absent. Comparing only two supplied hashes is insufficient: the
   parser recomputes the hash from bytes and compares both with the frozen copy.
2. Bind every restore to the approved component catalog hash and snapshot ID.
   Every restore carries actual `components`, `component_inventory_complete`
   and `catalog_id`; the machine evaluator invokes the same G1 predicate on
   those observations and retains its detailed failure/block reasons under
   `RESTORE_COMPONENT_BINDING`. Matching copied catalog hashes cannot hide a
   changed OCI digest, file hash, embedded artifact, version, source or arch.
   Missing source or asset binding blocks; a mismatched binding fails.
3. Only the enumerated guest checkpoint payload may restore its logical process
   identity, instruction/checkpoint marker and state hash. Host VMM, controller
   and helpers must have fresh process birth identities. Host FDs, unit
   InvocationIDs, cgroup ownership, external sockets and network-policy leases
   must be recreated/rebound and verified before workload release, never copied
   blindly from snapshot metadata. Preserved guest boot/PID values are scoped to
   the new host generation and do not establish a new independent identity.
4. The `same_execution` profile restores/rolls back the same logical sandbox ID,
   requires a fresh `instance_id` and a strictly increasing `generation`, then
   uses exactly `restore → destroy → recreate → restore`. The second restore
   must also obtain a fresh instance/process identity and the original snapshot
   contents. Destroy cannot reset generation to zero. Old-generation records
   remain retained for collision detection. `source_kind=execution_state` binds
   source execution ID and request hash; each restore must preserve both.
   A new request with the old execution ID also fails. An explicit
   `cross_execution_state` mode always fails under this contract; no field can
   authorize cross-execution mutable state reuse.
5. `owner` is the canonical `sandbox_id/instance_id/generation` tuple; network
   lease ownership must equal it. Resource identities include namespace inode,
   ifindex/object identity and birth generation, not only interface name or IP.
   They must not collide with another live sandbox or an unretired prior restore.
   Reuse of numerical IP/ifindex after proven release needs a new birth identity;
   it does not license concurrent ownership or stale policy.
6. At least two restores are required in that sequence. Each uses the frozen
   checkpoint process set, compares state fields/hashes, and reinitializes all
   host processes. G2/G4 must independently prove destroy between restores; an
   event-list declaration or successful restore command is not that proof.

`SNAPSHOT_HASH_MISMATCH`, `POST_SNAPSHOT_STATE_CONTAMINATION`,
`CHECKPOINT_PROCESS_STATE_MISMATCH`, `HOST_PROCESS_NOT_REINITIALIZED`,
`RESTORE_IDENTITY_COLLISION`, or `RESTORE_NETWORK_IDENTITY_COLLISION` are FAIL.
Missing observation is BLOCKED. No manual visual comparison is an oracle.

A distinct `clean_template_new_execution` profile requires
`source_kind=clean_template`, null source execution/request, exactly the `base`
state domain, no checkpoint payload and no prior host-process state. A separate
catalog entry in `approved_clean_templates` must match snapshot ID, content hash
and approval-record hash. Missing approval blocks; execution state labelled as
a template fails. Each restore gets a distinct execution ID, request hash,
sandbox ID, instance and generation, and reinitializes its processes. Restored
state domains must equal the approved source domains; scratch, credentials,
input/output or old leases cannot enter a clean template. This is synthetic
contract approval data, not real execution authorization.

Both profiles join restore execution/request identities to the matching G4
runtime record and the first destroy's G2 execution/process record. Every
restore, including the second, additionally joins one typed record in
`restore_process_observations` by owner and snapshot ID. That record requires
execution ID, process-scan completeness, and actual process rows using the
existing `process` schema: owner, role, host boot, PID, start ticks, namespace
and host/guest scope. Required host roles are VMM, controller and helper; any
additional observed host helpers must also be represented. A completeness flag
alone cannot replace those rows. The claim list must equal the canonical
SHA-256 keys computed from `(host_boot_id, pid, start_ticks, pid_namespace,
scope)` of the observed processes, without duplicates. Only host processes
with the restored owner/execution qualify.

Known identities from all termination samples and restore observations retain
their owner/execution bindings. A claimed key known under another binding is
`RESTORE_PROCESS_FOREIGN_BINDING / FAIL`, even if a later observation relabels
it. An absent observation or a claim without a corresponding observed key is
`RESTORE_PROCESS_OBSERVATION_MISSING / BLOCKED`; arbitrary strings cannot pass.
Missing scan or role coverage blocks; duplicate identities/records, observed
owner/execution contradictions or guest-scope rows fail. Freshness against
prior restores remains mandatory. The second restore needs its own process
observation, without requiring another termination case after that restore.
All observations here are synthetic. No host observer or process access is
implemented. Thus
`restore → destroy → recreate → restore` within one request is distinguished
from two fresh executions initialized from a sealed clean base. Cross-request
mutable guest reuse remains prohibited by parent section 6.

## 7. G4 — NETWORK_RESOURCE_NON_LEAKAGE

For each case capture **pre-state → create → active-state → destroy or abnormal
termination → post-state**, retaining a complete typed inventory and its raw
evidence hash at each phase. Post samples use the same 60000 ms/250 ms deadline
and two consecutive clean observations. At least all six G2 scenarios plus
three total normal create/destroy cycles are required (eight rounds minimum).
Run one unrelated live sandbox as a protected synthetic control in a future
approved probe. This stage uses only fixture records for that control.

G4 is the conjunction of runtime `deny_all` and attributed release. Every round
requires a `runtime_network` record joined to owner, execution and request.
The catalog separately binds ARM64 architecture, configuration, enforcement
filter and socket-ABI hashes plus a non-erasable minimum socket-operation set.
Actual hashes must match. The machine checks enforcement installation before
the first workload instruction, complete coverage through workload end, and
ordered observations before first instruction, during runtime, and after a
restore before resume when applicable. Incomplete evidence blocks; a late or
inactive filter, architecture/hash mismatch or exposed path fails even when
post-state cleanup succeeds.

Every phase must show no guest NIC/TAP/bridge/macvtap/SLIRP/passt path, inherited
network socket, vsock/QMP/monitor/provider endpoint, or equivalent workload
network/control exposure. `exposed_paths` must be empty; an active attributable
resource with `guest_attachment=true` independently fails. All socket probes
required by the approved ARM64 ABI must be present exactly once and denied with
EPERM or EACCES, including INET/INET6/PACKET/NETLINK creation, socketpair,
connect/bind/listen/accept/accept4 and send/receive variants. A successful probe
fails. These are structured synthetic observations, never real socket calls.
The future observer must independently verify the ABI/filter and continuous
coverage; supplied booleans or source configuration alone are not host proof.

Fixture-owned TAPs and other cleanup resources model unattached host staging
objects, not guest networking permission. Their `guest_attachment=false` is
compared alongside the complete runtime path observations. All such owned
objects still require release. An actual topology with workload connectivity
fails this parent profile even if CubeSandbox subsequently removes everything.

Inventory all applicable resources, including TAP, network namespace, route,
ip rule, iptables, nftables, eBPF objects/maps/programs and attachments, veth,
bridge attachment, policy records, and sandbox-specific sockets/listeners.
`complete_kinds` must cover every category; unsupported observer/permission is
BLOCKED. A zero inventory for an unused category is allowed only with the frozen
source/effective-topology non-use proof and complete observation of its relevant
kernel/control-plane scope. Source inspection here identifies TAP/CubeVS/policy
paths; it does not prove every optional mechanism is used or absent on a host.

The future observer must encode each `key` from explicit raw fields, not invent
an arbitrary identifier:

| Kind | Minimum identity and comparison fields |
| --- | --- |
| TAP/veth | host boot, netns inode, ifindex, creation epoch, ifname, peer identity, master/bridge ifindex, flags, owner lease |
| netns | namespace inode, bind-mount identity, holder FDs and processes, owner generation |
| route | netns, family, table, prefix, gateway, device identity, protocol, metric and multipath payload |
| ip rule | netns, family, priority, selectors, mark/mask, action and table |
| iptables/nftables | netns, family, table/chain, stable handle or canonical rule expression, owned sets/elements and references |
| eBPF | program ID/tag, map ID/type and canonical owned entries, link/attach point, pin path/inode, referencing process/FD, map-to-sandbox policy bindings |
| bridge attachment | bridge and port birth identities, VLAN/FDB state where owned |
| policy | backend, policy ID/version/hash, sandbox address+generation, active references and remote/local control-plane deletion observation |
| socket/listener | netns, inode, family/protocol/address/port or Unix path, holder process birth identity and owner |

Each record has `lifetime_owner` (`sandbox`, `shared`, `background`, `unknown`),
`owner`, `sandbox_references`, and a canonical fingerprint of the fields above.
Attribution is established from the approved creator inventory, active-state
object identity, effective configuration, cgroup/process/FD ancestry, assigned
namespace/interface identities and policy mappings. Name-prefix matching alone
is insufficient. Ownership history is retained after rename, relabel, owner
death, control-plane disappearance and ID reuse. The observer is trusted to
capture these facts; the synthetic parser cannot discover them on the host.

The diff rules are:

- Any post-state object explicitly owned by a tested sandbox/generation, or any
  surviving reference to it, is a leak if still present at the deadline: FAIL.
  Explicit owned objects or references observed in pre, active or any cleanup
  sample enter the immutable history immediately. Their keys remain tracked
  even if later relabelled background or their owner/references are cleared.
  The immutable identity ledger persists across every later round and post
  sample, not merely the round that created the object. A previous round's
  owned TAP reappearing as background at a later deadline is still FAIL,
  including an object first discovered during cleanup.
- A **pre-existing, separately approved shared pool** TAP/object may survive
  only if its baseline lifetime ownership was shared, no sandbox lease or
  reference remains, its baseline clean-policy fingerprint is restored, and the
  descriptor/attachment ownership belongs to the approved shared controller.
  A newly created sandbox-owned TAP cannot be retroactively promoted into that
  pool to pass. A pool object reset or lease release does not excuse retained
  sandbox-specific FD/policy state. A deployment unable to prove this mapping
  stays BLOCKED; this contract does not change pool settings.
- A pre-state resource owned by another sandbox, or with any reference to
  another sandbox even when `owner=null`, must still match exactly in active
  and every post sample. Deletion, lease reassignment or field/hash drift is
  `CROSS_SANDBOX_CONTAMINATION`. This protects known foreign leases without
  imposing whole-host equality on unrelated background resources.
- Unrelated, proven background route or other background churn is retained in
  the diff but does not count as sandbox leakage. Whole-host byte equality is
  not required. Newly unclassified objects remain `ORPHAN_ATTRIBUTION_UNKNOWN`,
  not ignored as background.
- Objects from dead prior generations are orphans. A known old owner or a
  previous active object's immutable key is enough to fail on persistence;
  uncertainty in attribution blocks. Do not reset the ownership ledger between
  repeated rounds. Duplicate object keys, repeated owner/generation tuples,
  cross-sandbox references or recycled identities while old leases survive fail.
- Aggregate all repetitions; an early clean round cannot hide later leaks or
  steadily growing sandbox-owned resources. Incomplete scanning at the deadline
  is FAIL even when no object happened to be listed.

Resource destruction and ownership release must be observed, not inferred from
an API's ACK, a daemon's log or `ReleaseNetwork` success. Observing a route,
iptables, nftables or eBPF object is not permission to delete or modify it.

## 8. Test obligations and remaining host prerequisites

The pure fixture suite asserts each requested outcome and exact rejection
reason: full PASS; missing digest BLOCKED; digest/version/commit/arch mismatch
FAIL; disappeared unit with helper or PID1 FD residue FAIL; every owned network
kind including TAP residue FAIL; snapshot hash mismatch FAIL; finite timeout
FAIL; unrelated background network changes PASS. It additionally tests mutable
tags, embedded VMM hash, schema ambiguity, observation gaps, restore generations,
process and network reuse, contamination, pooling and the existing pure-loop
consumer. Its PASS is **synthetic contract evidence only**.

Before any real host probe can be authorized, all of the following remain open:

1. Independent review of this contract and its fixture oracle, then a separate
   exact host authorization. The fixed earlier collector's 1/1 budget is spent
   and cannot authorize a CubeSandbox probe or a retry.
2. Lifecycle-manager ARM64 final OCI digest, registry/manifest/config verification,
   complete approved component/embedded-asset closure, source-to-artifact chain,
   licensing and configuration identities. Missing published attestations are
   acknowledged as unavailable, never fabricated as evidence.
3. Current target identity and a permitted execution identity with KVM and
   necessary observation access. The earlier receipt reported KVM and PID1
   namespace PermissionError in that process; it is historical input, not a
   fresh permission check or proof about a different session.
4. An implemented and separately reviewed host/guest observer that binds raw
   evidence to the same run, sees PID1 retained stdio and `(sd-close)` helpers,
   tracks process/cgroup/unit and network ownership across deaths and restores,
   and proves completeness without caller-supplied PASS values.
5. Exact systemd/controller/shared-service ownership, privileged observation
   route, permitted effects, host core-handler containment, resource quotas,
   fault targets, observation capacity, cleanup/rollback scope and stop controls.
6. Snapshot media/kernel/rootfs identity, checkpoint and generation rules, full
   network policy/lease attribution and selected deployment topology satisfying
   the parent's deny-all/no-host-sharing requirements. CubeSandbox's ordinary
   networking defaults or architecture alone do not establish those guarantees.

No commands to install CubeSandbox, start services or VMMs, create units or
network resources, or run a real sandbox are supplied or executed by this stage.
All G1–G4 specification completion is separate from actual backend acceptance,
which remains unexecuted and unauthorized. Stop after the local review package;
do not create a PR, merge, update canonical main, or continue into a host probe.
