# TS-B02A DGX Spark Linux ARM64 primary target and ephemeral KVM isolation path realignment specification v1

## 1. Decision, authority, and frozen baseline

This report implements only
`TOOL-SYSTEM-TS-B02A-DGX-SPARK-LINUX-ARM64-PRIMARY-TARGET-AND-EPHEMERAL-KVM-ISOLATION-PATH-REALIGNMENT-SPEC-v1`.
Its terminal disposition is:

`SPECIFICATION_ONLY / DGX_SPARK_LINUX_ARM64_PRIMARY_TARGET / EPHEMERAL_ARM64_KVM_GUEST_CONDITIONAL_CANDIDATE / CAPABILITY_NOT_PROVED / PR_231_PRESERVED_DRAFT / REAL_EXECUTION_BLOCKED`.

Before any write, the authenticated GitHub App read `refs/heads/main` and
then the referenced Git commit object in that order. They agreed exactly on:

- repository: `apolo183/tool-system`;
- commit: `1324107cb8b17e2b9829eacbe5d2d13979576f12`; and
- tree: `dce37ed35d27b30b485287487163fda228aafb97`.

The preflight also re-read the current central-governance paths required by
`AGENTS.md`, the local principles, blueprint, repository manifest, project
state, parent TS-B02 and TS-B02A specifications, and the current authenticated
state of Draft PR #231.

This package adds exactly this report and its task manifest and change plan.
All three paths are non-authority records covered by the existing
`REPO_MANIFEST.md` globs. It changes no blueprint, project state, module,
contract, source, test, workflow, runner, permission, dependency, supply-chain
input, infrastructure, external service, public result, or acceptance state.
Its `authority_effect` is `none`.

No command was run on the DGX, no DGX path or setting was read or changed by
this task, and no VM was created, booted, probed, stopped, reset, or deleted.
The DGX facts in this report are bounded user-supplied observations, not
observations made by this package.

## 2. Frozen bounded closure

The pre-execution closure is:

- task ID:
  `tool-system-ts-b02a-dgx-spark-linux-arm64-ephemeral-kvm-path-realignment-spec-v1`;
- task digest:
  `e8b7fb755376bb9e47cddadc97b727a741bb2f7478cbacb533149debfcc78e98`;
- baseline tree: `dce37ed35d27b30b485287487163fda228aafb97`;
- allowed write scope: the exact three additions in Section 13;
- acceptance set: baseline identity, exact three-path non-authority scope,
  DGX primary target, conditional ARM64 KVM candidate, architecture and trust
  boundary, preservation of every frozen core guarantee, PR #231 preservation,
  exact next-authority boundary, preserved findings and blockers, zero DGX/VM
  operations, and unchanged Hosted CI;
- validation set: task-manifest, change-plan, full pytest, active-gate,
  process-authority, module-registry, repository-manifest, exact diff, and
  whitespace checks;
- terminal predicate: one exact three-path Draft PR passes the unchanged
  Hosted gates, remains drift-free, is guardedly squash-merged, retains the
  original feature branch, and stops without accessing the DGX or starting a
  later task;
- finite budgets: three changed paths, zero runtime changes, zero new
  dependencies, zero DGX operations, zero VM operations, zero external review
  cycles, one local repair cycle, and at most two Hosted runs; and
- recurrence stop: a repeated blocker or validation state, two consecutive
  no-progress cycles, an out-of-scope requirement, or exhaustion of a finite
  budget stops the task.

The canonical JSON used for the task digest is the UTF-8 encoding of the
following value with lexicographically sorted keys and separators `,` and `:`:

```json
{"acceptance":["base_identity","exact_three_path_non_authority_scope","dgx_primary_target","arm64_ephemeral_kvm_conditional_candidate","architecture_and_trust_boundary","core_guarantee_preservation","pr231_preservation","next_authority_boundary","preserved_findings_and_blockers","no_dgx_access_or_vm_action","hosted_ci"],"allowed_paths":["docs/reports/subscription_worker_ts_b02a_dgx_spark_linux_arm64_primary_target_and_ephemeral_kvm_isolation_path_realignment_specification_v1.md","examples/change_plans/tool_system_subscription_worker_ts_b02a_dgx_spark_linux_arm64_ephemeral_kvm_path_realignment_spec_v1.yaml","examples/task_manifests/tool_system_subscription_worker_ts_b02a_dgx_spark_linux_arm64_ephemeral_kvm_path_realignment_spec_v1.yaml"],"baseline_tree":"dce37ed35d27b30b485287487163fda228aafb97","budgets":{"changed_paths":3,"dgx_operations":0,"external_review_cycles":0,"hosted_runs":2,"local_repair_cycles":1,"new_dependencies":0,"runtime_changes":0,"vm_operations":0},"task_id":"tool-system-ts-b02a-dgx-spark-linux-arm64-ephemeral-kvm-path-realignment-spec-v1","validation":["task_manifest","change_plan","pytest","active_gates","process_authority","module_registry","repo_manifest","exact_diff","diff_check","pr231_and_lifecycle_no_drift"]}
```

No review text, CI metadata, suggestion, or status transition may add an
acceptance condition, authorize a fourth path, or turn the candidate into a
capability claim.

## 3. Reason for the path realignment

The direct parent report selected a dedicated, task-scoped, ephemeral
non-pipe Linux/x86_64 runner or VM as the sole then-current path. Its stable
requirement was an execution boundary that does not rely on the observed
Hosted runner's pipe `core_pattern`. The parent froze Linux/x86_64 for that
candidate but explicitly left provider, owner, image, label, and lifecycle
unknown. It did not select or prove a cloud provider.

The intended primary deployment target is now known: a user-owned NVIDIA DGX
Spark running Linux on ARM64. The user has no cloud account, which is an
operational constraint rather than evidence about the parent. No concrete
x86_64 runner identity or authority has been supplied, and the parent
architecture does not match the known primary target. Linux/x86_64 is not a
blueprint-level product requirement.

This specification consequently makes two narrow decisions:

1. DGX Spark Linux/aarch64 is the primary intended tool-system target.
2. A fresh, task-scoped, ephemeral ARM64 KVM guest on that DGX is the sole
   current candidate for the TS-B02A isolation boundary, conditional on later
   proof of every capability and evidence obligation in this report.

The earlier x86_64 runner route remains retained historical planning evidence
and may remain an optional alternative if separately supplied later. It is no
longer the primary implementation prerequisite. Neither target selection nor
candidate selection is an implementation, capability PASS, acceptance, or
real-execution authorization.

## 4. User-supplied DGX observations and unknowns

### 4.1 Observed clues

The user supplied read-only terminal output reporting:

- architecture `aarch64`;
- Ubuntu 24.04.4 LTS and NVIDIA kernel `6.17.0-1026-nvidia`;
- the platform identifying as NVIDIA DGX Spark and as a DGX server for KVM;
- a host `core_pattern` whose first byte is `|` and which names an Apport pipe
  helper;
- a cgroup v2 mount whose reported options include `rw`, advertising `cpuset`,
  `cpu`, `io`, `memory`,
  `hugetlb`, `pids`, `rdma`, `misc`, and `dmem` controllers;
- no virtualization detected by `systemd-detect-virt`;
- `/dev/kvm` present with mode `0660`, owner `root`, group `kvm`;
- kernel configuration values `CONFIG_ARM64=y`, `CONFIG_VIRTUALIZATION=y`, and
  `CONFIG_KVM=y`;
- the observed account in the `sudo` group but not the `kvm` group; and
- approximately 121 GiB memory and 2.7 TiB free space on the reported root
  filesystem.

The report intentionally omits the machine hostname and serial number because
neither is needed to freeze this design.

### 4.2 What those clues do not prove

The observations do **not** prove:

- that the intended execution identity can open `/dev/kvm` or successfully
  issue the required KVM ioctls;
- that hardware-accelerated ARM64 guests can be created or booted;
- that a supported userspace VMM, firmware, guest kernel, initrd, or sealed
  guest image exists locally;
- that any such component has an acceptable exact version, digest, license,
  machine type, or security configuration;
- that the task identity owns a writable delegated cgroup subtree rather than
  only seeing a read-write cgroup v2 mount;
- that AppArmor, seccomp, device policy, IOMMU, storage, networking, console,
  or helper-process behavior permits the frozen design;
- that the guest's `core_pattern` is non-pipe or immutable to the workload;
- that guest namespace, cgroup, mount, quota, pidfd, `openat2`, `execveat`,
  ptrace, streaming, timeout, and cleanup primitives work as required; or
- that a VMM crash cannot invoke the host's pipe core handler or expose guest
  memory or create unobserved host effects.

The presence of `/dev/kvm`, KVM kernel configuration, free resources, or sudo
membership is therefore recorded only as feasibility evidence. It must never
be projected as `KVM_ACCESSIBLE`, `GUEST_BOOTABLE`, `ISOLATION_PASS`, or a
zero-effect result.

## 5. Blueprint and trust-boundary alignment

The global anchor remains `blueprint/tool_system_v0.yaml:product_objective`.
The product runs approved, bounded development work in an isolated repository
workspace, while `arbitrary_untrusted_code_containment` remains a non-goal.
The trusted core boundary remains the authorized operator, the selected DGX
host, its Linux kernel, KVM, the selected VMM/provider configuration, and the
guest kernel/provider configuration. This report does not claim protection
against a malicious host administrator, compromised kernel, compromised
hypervisor, hostile infrastructure control plane, covert channel, or
microarchitectural attack.

The candidate profile name is frozen as:

`dgx_spark_ephemeral_arm64_kvm_v1`.

KVM hardware virtualization is selected as the boundary class. The exact
userspace VMM is deliberately **unknown** until a separately authorized
inventory establishes what is already installed and usable. QEMU documentation
shows that its ARM `virt` machine can be used with KVM on a compatible aarch64
host, but that documentation does not prove QEMU is installed or selected on
this DGX. [K1][Q1]

The candidate permits no transparent substitution with:

- native execution on the DGX host;
- an ordinary subprocess, namespace-only host backend, or container;
- software-emulated TCG execution;
- a different architecture or remote cloud runner;
- a mock, skip, xfail, fallback, or evidence synthesis; or
- Draft PR #231's blocked native-host candidate.

An unavailable or unusable KVM/VMM/image/cgroup/guest primitive is a named
capability blocker and stops the future package. It is not authority to install
software, change groups or permissions, modify sysctls or services, download
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

1. terminate the workload and obtain preliminary guest terminal evidence;
2. quiesce the guest/VMM and detach the declared-output medium;
3. read it in a separate provider-owned, quota-bound parser/extraction boundary
   whose exact filesystem/archive format and parser identity are sealed;
4. validate the declared file set, paths, types, raw bytes, inode counts,
   digests and aggregate limits while rejecting symlink, hard-link, device,
   traversal, sparse-file, decompression-bomb, filesystem-corruption and helper-
   process escape cases;
5. remove or quarantine the medium and prove parser/helper/resource cleanup;
   and
6. only then finalize composite evidence and completeness.

The guest filesystem may not be live-mounted into an ordinary host namespace.
A one-way archive stream is an alternative only if its format, parser, byte/
file/depth limits, identity and cleanup meet the same boundary. Malformed or
over-limit output is a non-success result, never partial trusted extraction.

## 7. Preservation of the TS-B02 core guarantees

The KVM candidate must preserve every guarantee frozen by the TS-B02 blueprint
realignment specification. The VM boundary adds a host/guest split; it does
not replace or relax the guarantees.

| Guarantee | Required DGX ARM64/KVM realization |
| --- | --- |
| Filesystem boundary | Seal boot and input media; expose no host filesystem; permit writes only on quota-bound disposable scratch/output media; bind all block identities and access modes; reject symlink, mount, device, descriptor, and extraction escapes. |
| Complete process tree | Contain every guest workload descendant in a guest cgroup/process boundary and every host VMM/helper in an owned host cgroup. Guest shutdown alone is insufficient if host helpers survive; a child exit is insufficient if guest descendants survive. |
| Complete cleanup | On normal completion, violation, output breach, timeout, provider error, or observation loss, terminate guest workload, destroy/reset the VM boundary, kill and reap the host provider tree, and prove no process, cgroup population, overlay, channel, mount, or device-mapping residue. `cgroup.kill` and `populated=0` are useful kernel primitives but must be observed on the owned current-run cgroups. [K2] |
| Default-deny network | Omit every guest network device and host network backend, DNS path, loopback-crossing proxy, inherited socket, and control channel before the first workload instruction. The guest loopback interface must have `IFF_UP` clear. An ARM64-derived, identity-sealed seccomp filter or equivalent guest-OS mechanism must reject creation and use of the frozen network-capable socket ABI, including IPv4, IPv6, netlink, packet, DNS-related, inherited-network-FD, and network-namespace/bridge operations. Filter or observation absence blocks; no-NIC evidence cannot substitute for socket denial. |
| Executable/interpreter identity seal | Bind the actual ARM64 ELF or script, its interpreter, dynamic loader, libraries permitted by policy, guest kernel and boot image, and the host VMM/loader chain. x86_64 identities or syscall assumptions cannot be copied as evidence. |
| TOCTOU blocking | Use immutable content-addressed images and inputs, read-only open descriptors or block attachments, disposable overlays, and exec-critical revalidation inside the guest. Replacement of VMM, firmware, image, kernel, initrd, input, executable, interpreter, loader, policy, or device graph blocks. |
| Streaming output limit | Drain raw console/output bytes incrementally through a provider-owned bounded path; account emitted, retained, and discarded bytes before decoding; terminate the complete guest and host provider boundary on breach; never buffer unbounded output first. |
| Monotonic timeout | Enforce a host-provider monotonic deadline independent of guest clocks. Expiry performs bounded graceful termination, forced guest destruction/provider kill, and verified cleanup before evidence completion. |
| Matching OS-derived evidence | Produce a single current-run composite record from both host Linux/KVM/provider observations and guest Linux enforcement observations. Missing either layer, a boot/request mismatch, observation loss, or cleanup uncertainty makes the record incomplete and the result non-successful. |

The future ARM64 profile must re-freeze architecture-specific ELF machine
identity, page size and ABI assumptions, dynamic loader identity, syscall and
seccomp rules, ptrace event handling, KVM/virtual-device behavior, and guest
kernel interfaces. No x86_64 syscall ceiling, executable fixture, loader path,
or machine-code assumption from PR #231 may be reused without ARM64-specific
derivation and adversarial proof.

The host provider's `CLOCK_MONOTONIC` domain is the deadline authority. Guest
monotonic timestamps may order events only within that guest boot; their raw
values are never compared across host and guest clocks. Execution nonce,
request digest, guest boot identity and event sequence join the two timelines.

## 8. Host pipe core_pattern and two-layer failure semantics

The physical DGX host's observed `core_pattern` begins with `|`. Linux defines
such a value as a request to pass a core dump to a user-space helper; under a
pipe pattern, `RLIMIT_CORE` is not enforced for suppressing delivery to that
helper. [K3][K4] A normal `execve()` also resets the dumpable attribute to one
in the usual non-privileged case. [K5] Moving the workload into a guest changes
which kernel handles a guest workload crash, but it does not make the physical
host configuration disappear.

The future gate must separately prove:

1. the guest initial namespace has a frozen non-pipe core-dump configuration,
   immutable to the workload, with matching before/after evidence; every actual
   post-exec tracee and descendant has soft and hard `RLIMIT_CORE=(0,0)`, and
   attempts to restore it through `setrlimit` or `prlimit64` are denied and
   observed; and
2. a host VMM/provider/helper crash cannot create an unbounded or unobserved
   host pipe-helper effect that invalidates cleanup or leaks guest/workload
   data.

For the host provider, pre-exec `PR_SET_DUMPABLE=0`, `RLIMIT_CORE=0`, or the
absence of a core file is insufficient. The future design must establish and
causally observe a post-exec VMM dumpability or equally strong invariant before
sensitive guest state exists, prevent or observe its reversal, and bind it to
the current VMM PID/start time/exec identity. Event-complete observation of
provider death, host pipe-helper creation and payload-relevant effects for the
matching interval is mandatory; lack of an observation mechanism is a blocker,
not permission to omit the field. `PR_SET_DUMPABLE` semantics alone do not
create that observation. [K6]

The guest adversarial proof must cover sealed static and dynamic ARM64 ELF,
actual loader, shebang/interpreter chains, first-user-instruction crash,
fork/vfork/clone descendants, the frozen core-generating signal classes, and
attempts to restore dumpability or core limits. Guest self-report, no core file,
or a crash-free run cannot establish the core gate.

At minimum, mandatory handler observation, provider stable identities,
post-exec dumpability/core-limit invariant, cgroup membership, terminal process
state, authorized terminal-cleanup transition, expected provider exit and
cleanup interval must be bound to the same execution. If the host's pipe helper
starts, unexpected provider death or crash occurs before the authorized
terminal-cleanup transition, guest memory may have been delivered outside the
owned provider boundary, or the absence of those effects cannot be established,
then:

- `ExecutionEvidenceV1.complete` is false;
- the terminal result is non-successful;
- no absolute zero-effect, hard-zero, no-leak, or complete-cleanup conclusion
  may be constructed; and
- the path stops with a named host-provider core-containment blocker.

This specification does not assume that post-exec dumpability enforcement or
another mechanism will satisfy that gate. If the future bounded probe cannot
prove it with current-run OS evidence, the KVM route remains blocked. The
application must not fill a missing host observation with a configured zero or
infer absence from the lack of a visible core file.

VMM/provider crash injection is prohibited until host-provider core
containment is first bounded and a separate authorization freezes the crash
fixture, possible Apport/root-helper file or report effects, observation,
cleanup and rollback. A crash-free VMM run is not proof of the crash gate. If
no accepted causal proof is available without that injection, the bounded
probe must stop before capability PASS and request the exact side-effect
authority; it may not trigger a host core handler opportunistically.

## 9. Interface semantics and evidence ownership

This report changes no canonical runtime interface. It preserves the frozen
semantic names `IsolationRequestV1` and `ExecutionEvidenceV1` for the future
TS-B02A chain.

`IsolationRequestV1` is caller-owned policy, not a container for provider
actuals. For the KVM candidate it must bind at least:

- required profile/version and capability-policy digest, target Linux/aarch64
  platform constraints, and any caller-authorized pinned provider-profile
  reference;
- task, source, candidate, input and declared-output identities, expected ARM64
  workload executable/interpreter/loader/library chain, and exec-transition
  TOCTOU policy;
- allowed and forbidden topology, including no host sharing, network device/
  backend, uncontrolled channel, GPU or host-device passthrough;
- expected ARM64 network-socket denial policy, inherited-network-descriptor
  closure, DNS state, exact loopback-down rule and namespace controls;
- resource, scratch/output byte/inode, raw stream and combined-output limits,
  host-monotonic duration/deadline policy, and termination/cleanup policy; and
- required host and guest observation classes and failure behavior.

Actual host boot, kernel/KVM result, permission route, VMM/loader, firmware,
machine/device graph, launch instance, guest image/boot, overlay instance,
cgroup and channel identities are owned by TS-B02A provider preflight. Before
workload release, the provider seals them into one provider-effective plan and
configuration digest that satisfies the request's constraints. Evidence binds
the request digest, effective-plan digest and actual observations. If this
requires a new public provider-plan interface or a V2 request/evidence type, a
later task stops for an exact interface/path authorization; it may not smuggle
provider actuals into caller-owned V1 fields.

`ExecutionEvidenceV1` must be one immutable composite current-run record that
binds the request digest and includes:

- actual host boot/kernel/KVM/VMM/firmware/machine/device/configuration
  identities and preflight result;
- actual guest boot/kernel/image/device/storage/network/configuration
  identities and guest readiness result;
- provider-effective plan/configuration digest plus the bounded one-way
  evidence-channel identity, execution nonce, request digest, guest boot
  identity, event sequence/byte counts, and channel completeness result;
- host provider and guest workload stable process/cgroup identities,
  descendant observations, terminal reasons, forced-kill results, and
  survivor checks;
- actual ARM64 executable/interpreter/loader chain and exec-critical identity
  match;
- raw ordinary-stream byte counts and limit event, host-monotonic timing,
  guest-local event ordering, guest and host termination, bounded parser/
  extraction validation, and full parser/storage/provider cleanup observations;
- guest and host core-dump/core-handler observations for the matching interval;
  and
- required-event classes, missing observations, provider errors, residue,
  completeness, and record digest.

The record may not be assembled solely from guest self-report or provider
configuration. Both host and guest enforcement observations are mandatory.
Ordinary stdout/stderr bytes cannot be parsed as evidence. The guest-side
collector must be provider-owned and inaccessible to the workload; its one-way
channel must fail closed on loss, truncation, reordering, duplication, identity
mismatch, quota breach, or workload writability. This remains evidence within
the trusted local provider boundary, not independent attestation.
If the existing proposed V1 shape cannot represent the required composite
binding without ambiguity, a later task must stop and request a separately
authorized interface-version and path update. It must not silently reinterpret
an existing field.

Ownership remains:

| Surface | Natural owner | Preserved interface boundary |
| --- | --- | --- |
| DGX/KVM inventory and bounded capability proof | separately authorized DGX-local capability packages plus the named operator | Establish installed identities and synthetic feasibility only; do not implement the runtime or select business work. |
| `IsolationRequestV1` construction | future TS-B02B worker-adapter | Select expected worker, workload identity, and policy; do not launch, seal, or synthesize evidence. |
| provider-effective plan, enforcement and `ExecutionEvidenceV1` | future TS-B02A isolated-execution backend/provider | Resolve and seal actual provider configuration, gate, boot, execute, enforce, observe, terminate, parse declared output, clean, and return the immutable composite record; do not choose business policy or publish acceptance. |
| independent matching and TS-B01/TS-B02 join | future TS-B02C task-runner | Revalidate every worker/validation execution record and join it with matching TS-B01 semantic evidence before any execution/effect projection. |
| affected-closure acceptance | future TS-B02D evidence owner | Revalidate adversarial and consumer closure; do not implement runtime or enable real execution. |

The order remains capability path closure, TS-B02A, TS-B02B, TS-B02C,
TS-B02D, then a separately authorized public-entry reacceptance decision.
Functional `subscription_transport_only` work, if ever authorized, remains a
separate post-`deny_all` boundary and is not started here.

## 10. Capability gates and adversarial obligations

Before any later runtime implementation may release a synthetic workload, a
separately authorized capability package must freeze and prove:

- actual open/ioctl access to `/dev/kvm`, required KVM API/capability results,
  ARM64 hardware acceleration, and no TCG fallback; [K1]
- exact installed VMM, helper, interpreter/loader, firmware and license
  identities, or a blocker if any is absent;
- exact candidate local ARM64 guest image/kernel/initrd identities, provenance
  and license evidence, or a blocker if none exists; inventory does not itself
  authorize any candidate image;
- an owned writable cgroup v2 delegation for every host provider process and
  a suitable guest cgroup v2 boundary, including effective controllers,
  `cgroup.kill`, and `populated=0`; a required shared system daemon blocks this
  profile unless separately re-frozen as a trusted long-lived control plane,
  and its survival may never be reported as execution-owned cleanup; [K2]
- the exact minimal device graph, no host sharing, no network backend, no
  inherited socket, no uncontrolled console/monitor/vsock/agent channel, and no
  host/GPU/device passthrough;
- an ARM64-derived and identity-sealed seccomp filter or equivalent guest-OS
  control that is active before the first workload instruction and fails closed
  on the frozen network-capable socket ABI; absence of that filter or its
  current-run observation is a blocker even when no NIC exists;
- guest `IFF_UP`-clear loopback, guest non-pipe `core_pattern`, post-exec
  tracee/descendant soft and hard `RLIMIT_CORE=(0,0)`, blocked restoration, and
  mandatory host-provider pipe-handler observations from Section 8;
- sealed media, quota enforcement, guest filesystem/mount boundary,
  `openat2`, `execveat`, ptrace/pidfd or accepted equivalents, and ARM64
  executable/interpreter/loader identity;
- a workload-inaccessible, one-way, bounded and sequenced evidence channel
  distinct from ordinary output, plus nonce/request/boot/provider binding and
  fail-closed loss/duplication/truncation behavior;
- a sealed quota-bound output parser/extraction boundary covering hostile
  filesystem/archive structure, exact declared files, raw-byte/inode/file/depth
  limits, digests, helper cleanup and quarantine;
- raw incremental stream limits, host monotonic timeout, complete guest and
  provider termination, and no-residue disposal; and
- current-run composite evidence with no skip, xfail, mock, fallback,
  observation loss, unsupported substitution, or fabricated zero.

The later adversarial matrix must include at least image/input substitution,
overlay quota byte and inode exhaustion, prohibited host-path and device
access, guest NIC and provider control-channel enumeration and use, DNS,
IPv4, IPv6, loopback, netlink, packet socket, inherited network descriptor,
network-namespace and bridge attempts, ARM64 socket-filter substitution or
observation loss, evidence-channel forgery/writability/loss/reordering/
duplication/truncation/quota cases, malicious output path/type/link/device/
sparse/compression/corruption cases, ARM64 ELF/script/interpreter/loader
replacement, exec TOCTOU, fork/vfork/clone/double-fork/reparent escape, output
flood, timeout, guest panic or provider loss, guest static/dynamic/shebang/
first-instruction/descendant core cases, core-limit restoration, tracer/
observer loss, cleanup failure, and residue detection. Positive controls must
show that each observer detects a deliberately exposed synthetic boundary;
negative controls must show the frozen boundary blocks before transfer or
escape. Exact fixtures, tools, temporary paths, time/byte budgets, and fault
mechanisms are not authorized by this report and must be frozen before use.

Host VMM/provider crash injection is excluded from an ordinary Stage 2 probe
unless the separate Section 8 side-effect authorization has already been
granted. Without an accepted causal proof of that failure path, Stage 2 must
return a blocker rather than capability PASS.

## 11. Exact next prerequisites and authorization boundary

No follow-on starts automatically. The path has a read-only inventory, zero or
more conditional enablement/acquisition packages if the inventory finds a
missing prerequisite, and then a bounded probe. Only the read-only inventory
is immediately eligible for a new authorization.

### 11.1 First: read-only DGX inventory

The exact next task identity is:

`TOOL-SYSTEM-TS-B02A-DGX-SPARK-EPHEMERAL-ARM64-KVM-GUEST-READ-ONLY-HYPERVISOR-IMAGE-AND-PERMISSION-INVENTORY-v1`.

It must be separately authorized for execution by the DGX-local Codex CLI; the
current chat task neither delegates nor starts it. Its scope must be read-only
inspection of:

- actual KVM device access and non-mutating API/capability information;
- already installed VMM, helper, firmware and loader paths, versions, hashes,
  licenses, machine/device support, and security integration;
- candidate local ARM64 guest images, kernels and initrds, with digests,
  provenance and license evidence; discovery does not authorize their use;
- current cgroup delegation and controller permissions;
- AppArmor/seccomp/device/IOMMU/channel/network defaults; and
- the exact non-mutating permission route available to the intended provider.

That task may not install a package, add a user to a group, use sudo to mutate
state, change permissions, sysctls, services, cgroups or security policy,
download or create an image, create or boot a VM, write the repository, or run
a workload. If a required component or permission is absent, it stops with an
exact enablement prerequisite rather than changing the machine.

The inventory evidence owner is the user. The DGX-local CLI must return the
complete commands, raw bounded outputs, explicit errors and stable byte digests
to the user. The user must bring that evidence back to the current decision
context and explicitly accept or reject the inventory. There is no repository
artifact, automatic acceptance, delegated approval, or automatic next-task
start under this specification. If a future inventory requires a repository
path, that path needs separate prior authorization.

### 11.2 Conditional enablement or acquisition

If the inventory finds a missing VMM, firmware, image, permission, cgroup
delegation, security-policy rule, service arrangement or other prerequisite,
one or more separately authorized packages must name each exact package/image,
source, version, digest, license, path, group/permission/service/configuration
change, owner, cost, rollback, validation and residual effect. Read-only
inventory is not authority for any such mutation or acquisition.

After each conditional package, a newly authorized read-only verification must
establish the resulting exact state. Any inability to name a safe, licensed,
reversible route leaves the KVM path blocked.

### 11.3 Bounded synthetic guest probe

Only after the inventory is explicitly accepted, every required conditional
enablement is separately completed and verified, and a new authorization
freezes exact toolchain/image identities, creator-owned temporary paths,
resource/time/cost budgets, side effects, cleanup, and rollback may the
following task become eligible:

`TOOL-SYSTEM-TS-B02A-DGX-SPARK-EPHEMERAL-ARM64-KVM-GUEST-NON-PIPE-CORE-PATTERN-CAPABILITY-PROBE-AND-PATH-CLOSURE-v1`.

That task may use only synthetic fixtures and a bounded ephemeral guest
lifecycle. It must prove or block the capability and adversarial obligations
in Section 10. It is not TS-B02A implementation, may not run a real repository
or business workload, and may not auto-enable missing host capabilities.

An accepted probe still does not revive an earlier implementation closure.
From the then-current canonical base, a new specification must re-derive the
exact TS-B02A ARM64/KVM paths, dependencies, licenses, host launcher and helper
identities, guest bootstrap/supervisor and evidence/output protocols, image
handling/provenance, tests and artifact ownership. Any required public
interface version is part of that new authorization.

If either prerequisite requires a repository path, package, image, group,
permission, sysctl, service, workflow, runner, network, infrastructure, secret,
or other authority not exactly pre-frozen, it stops and requests a new exact
authorization. Neither prerequisite may fall back to native DGX execution,
ordinary subprocess execution, a container, TCG, Hosted x86_64, or PR #231.

## 12. PR #231, findings, and publication stop

Draft PR #231 remains preserved as an unaccepted and unmerged historical
candidate:

- state: open Draft, not merged;
- feature branch:
  `agent/subscription-worker-ts-b02a-core-local-os-isolated-execution-v1`;
- feature head: `f94a9072eefe012b1d17bc9f87682b4287e1274d`;
- feature head tree: `d8ab0d44a5947345bdf258b0aea9b28af8ca71bb`;
- changed paths: 17; and
- Hosted blocker: `HOST_CAPABILITY_BLOCKER` at `host.gate` because the
  observed runner `core_pattern` invokes a pipe helper; the workload was not
  released.

This specification does not update, rebase, merge, close, mark Ready, comment
on, label, or otherwise mutate PR #231 or its feature branch. Advancing
canonical `main` with this report may move the PR's displayed base relationship
without changing its head; that is not authority to reconcile it.

PR #231's earlier 17-path implementation authority stopped at its Hosted
capability blocker and cannot be resumed, transferred, rebased or interpreted
as authority for an ARM64/KVM backend. After an accepted probe, a separate
lifecycle decision must choose whether #231 remains historical, is closed, or
has particular blobs reconsidered under a new exact closure. This report makes
none of those choices.

The following states are preserved without correction or acceptance:

- TS-B01: `corrected_pending_reacceptance`;
- TS-B02: confirmed blocker;
- subscription-worker public entry: not accepted;
- real repository execution: blocked;
- TS-H01, TS-H02, TS-H03, TS-H04, and TS-H05: unchanged;
- TS-M01, TS-M02, TS-M03, and TS-M04: unchanged by this package; and
- TS-B02A implementation, TS-B02B, TS-B02C, TS-B02D, public reacceptance,
  subscription transport, and every real workload: not started.

The exact publication branch is:

`agent/subscription-worker-ts-b02a-dgx-spark-linux-arm64-ephemeral-kvm-path-realignment-spec-v1`.

The exact commit message is:

`Realign TS-B02A isolation path to DGX ARM64`.

Validation requires strict task-manifest and change-plan validation, full
pytest, all four current governance validators, exact one-commit/three-addition
mode-`100644` closure, `git diff --check`, and unchanged Hosted CI. One Draft PR
is allowed. It may become Ready and be squash-merged only after the GitHub App
re-reads and confirms unchanged base, head, paths, commit count, checks,
comments, reviews, and review threads. The original feature branch must remain
at its original head.

A base/tree drift, fourth path, DGX or VM operation, lifecycle drift,
validation failure beyond the frozen repair/run budget, or new authority need
stops. Success also stops: it does not start either Section 11 task, TS-B02A,
or real execution.

## 13. Exact path closure

Add exactly these regular `100644` paths:

1. `docs/reports/subscription_worker_ts_b02a_dgx_spark_linux_arm64_primary_target_and_ephemeral_kvm_isolation_path_realignment_specification_v1.md`;
2. `examples/task_manifests/tool_system_subscription_worker_ts_b02a_dgx_spark_linux_arm64_ephemeral_kvm_path_realignment_spec_v1.yaml`;
3. `examples/change_plans/tool_system_subscription_worker_ts_b02a_dgx_spark_linux_arm64_ephemeral_kvm_path_realignment_spec_v1.yaml`.

No path is modified or deleted. `REPO_MANIFEST.md` already classifies these
locations through retained non-authority globs and therefore remains unchanged.

## References

- [K1] Linux KVM API: <https://docs.kernel.org/virt/kvm/api.html>
- [K2] Linux cgroup v2, including `cgroup.kill` and `populated`:
  <https://docs.kernel.org/admin-guide/cgroup-v2.html>
- [K3] Linux kernel `core_pattern` sysctl documentation:
  <https://docs.kernel.org/admin-guide/sysctl/kernel.html#core-pattern>
- [K4] Linux `core(5)`, including pipe handlers and `RLIMIT_CORE`:
  <https://man7.org/linux/man-pages/man5/core.5.html>
- [K5] Linux `execve(2)`, including the dumpable-attribute transition:
  <https://man7.org/linux/man-pages/man2/execve.2.html>
- [K6] Linux `PR_SET_DUMPABLE(2const)`:
  <https://man7.org/linux/man-pages/man2/PR_SET_DUMPABLE.2const.html>
- [Q1] QEMU ARM `virt` machine documentation:
  <https://qemu.readthedocs.io/en/master/system/arm/virt.html>
- [Q2] QEMU invocation documentation, including `-nic none` and
  `-nodefaults`: <https://qemu.readthedocs.io/en/master/system/invocation.html>
- Draft PR #231: <https://github.com/apolo183/tool-system/pull/231>
