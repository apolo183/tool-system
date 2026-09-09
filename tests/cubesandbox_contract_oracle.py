"""Pure fixture oracle for a proposed contract; no host importer or execution API.

Uses the repository's JSON Schema 2020-12 dependency. Inputs are already-held
bytes/mappings; this module performs no filesystem, process, network or clock I/O.
"""

from __future__ import annotations

import hashlib
import json
from itertools import pairwise

from jsonschema import Draft202012Validator

VERSION = "cubesandbox_backend_acceptance_v1"
COMMIT = "d0081641c59822e4e5653b7462e914410b81910a"
GATES = (
    "COMPONENT_VERSION_BINDING",
    "ABNORMAL_TERMINATION_COMPLETE_REAP",
    "SNAPSHOT_RESTORE_INTEGRITY",
    "NETWORK_RESOURCE_NON_LEAKAGE",
)
SCENARIOS = {
    "normal_exit",
    "payload_sigkill",
    "controller_death",
    "vmm_death",
    "timeout",
    "service_forced_termination",
}
ROLES = {"payload", "vmm", "controller", "helper", "async_close"}
KINDS = {
    "tap",
    "netns",
    "route",
    "ip_rule",
    "iptables",
    "nftables",
    "ebpf",
    "veth",
    "bridge_attachment",
    "policy",
    "socket_listener",
}
REQUIRED_COMPONENTS = {
    "cubelet",
    "cube-shim",
    "cube-kernel",
    "cube-guest",
    "cube-agent",
    "cube-egress",
    "cube-lifecycle-manager",
}
DEADLINE_MS = 60_000
POLL_MS = 250
REQUIRED_ARTIFACTS = {
    ("cube-shim", "hypervisor", "file"),
    ("cube-shim", "shim-helper", "file"),
    ("cube-kernel", "guest-kernel", "file"),
    ("cube-guest", "guest-rootfs", "file"),
    ("cube-agent", "guest-agent", "file"),
}
SOCKET_OPERATIONS = {
    "socket_inet",
    "socket_inet6",
    "socket_packet",
    "socket_netlink",
    "socketpair",
    "connect",
    "bind",
    "listen",
    "accept",
    "accept4",
    "sendto",
    "sendmsg",
    "sendmmsg",
    "recvfrom",
    "recvmsg",
    "recvmmsg",
}


def canonical_hash(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _no_constant(value):
    raise ValueError("NON_FINITE_JSON_NUMBER")


def _decision(gate, failures=(), blockers=(), **extra):
    return {
        "gate": gate,
        "status": "FAIL" if failures else "BLOCKED" if blockers else "PASS",
        "reasons": sorted(set(failures) | set(blockers)),
        **extra,
    }


def _result(gates):
    states = {g["status"] for g in gates}
    return {
        "schema_version": VERSION,
        "evidence_class": "synthetic",
        "status": "FAIL"
        if "FAIL" in states
        else "BLOCKED"
        if "BLOCKED" in states
        else "PASS",
        "gates": gates,
        "real_backend_acceptance_authorized": False,
        "real_backend_acceptance_executed": False,
    }


def _index(rows, key):
    values = {row[key]: row for row in rows}
    if len(values) != len(rows):
        raise ValueError("DUPLICATE_IDENTITY")
    return values


def _components(evidence, catalog):
    fail, block, rows = [], [], []
    expected = _index(catalog["components"], "component_name")
    actual = _index(evidence["components"], "component_name")
    required = set(catalog["required_components"])
    if len(required) != len(catalog["required_components"]):
        fail.append("DUPLICATE_REQUIRED_COMPONENT")
    if not REQUIRED_COMPONENTS <= required or required != set(expected):
        block.append("COMPONENT_CLOSURE_UNFROZEN")
    if not catalog["closure_complete"] or not evidence["component_inventory_complete"]:
        block.append("COMPONENT_CLOSURE_INCOMPLETE")
    if evidence["catalog_id"] != catalog["catalog_id"]:
        fail.append("CATALOG_ID_MISMATCH")
    if actual.keys() - expected.keys():
        fail.append("UNAPPROVED_COMPONENT")
    obligations = {
        (a["component_name"], a["name"], a["artifact_type"])
        for a in catalog["required_artifacts"]
    }
    if len(obligations) != len(catalog["required_artifacts"]):
        fail.append("DUPLICATE_ARTIFACT_OBLIGATION")
    if not REQUIRED_ARTIFACTS <= obligations:
        block.append("REQUIRED_ARTIFACT_SET_UNFROZEN")
    approved_assets = {
        (c["component_name"], a["name"], a["artifact_type"])
        for c in expected.values()
        for a in c["embedded_artifacts"]
    }
    if not (REQUIRED_ARTIFACTS | obligations) <= approved_assets:
        block.append("REQUIRED_ARTIFACT_MISSING")
    for name, approved in expected.items():
        cf, cb = [], []
        observed = actual.get(name)
        file_component = approved["artifact_type"] == "file"
        approved_digest = (
            approved["file_identity"].get("sha256")
            if file_component
            else approved.get("oci_digest")
        )
        if not approved_digest:
            cb.append("APPROVED_DIGEST_MISSING")
        if name in {"cube-egress", "cube-lifecycle-manager"} and file_component:
            cf.append("OCI_COMPONENT_TYPE_REQUIRED")
        if (
            approved["release_tag"],
            approved["source_commit"],
            approved["architecture"],
        ) != ("v0.7.0", COMMIT, "linux/arm64"):
            cf.append("APPROVED_VERSION_COMMIT_ARCH_MISMATCH")
        if observed is None:
            cb.append("COMPONENT_OBSERVATION_MISSING")
        else:
            for field in (
                "release_tag",
                "source_commit",
                "architecture",
                "registry",
                "artifact_type",
            ):
                if observed[field] != approved[field]:
                    cf.append(field.upper() + "_MISMATCH")
            observed_file = observed["artifact_type"] == "file"
            resolved = (
                observed["file_identity"].get("sha256")
                if observed_file
                else observed.get("oci_digest")
            )
            if not resolved:
                cb.append("RESOLVED_DIGEST_MISSING")
            elif approved_digest and resolved != approved_digest:
                cf.append(
                    "FILE_DIGEST_MISMATCH" if file_component else "OCI_DIGEST_MISMATCH"
                )
            if (
                not file_component
                and not observed_file
                and resolved
                and observed["requested_ref"] != approved["registry"] + "@" + resolved
            ):
                cf.append("DIGEST_REFERENCE_REQUIRED")
            if (
                file_component
                and observed_file
                and (
                    observed["file_identity"]["path"]
                    != approved["file_identity"]["path"]
                    or observed["requested_ref"] != approved["file_identity"]["path"]
                )
            ):
                cf.append("FILE_PATH_MISMATCH")
            assets = _index(approved["embedded_artifacts"], "name")
            actual_assets = _index(observed["embedded_artifacts"], "name")
            if set(assets) != set(actual_assets):
                cf.append("EMBEDDED_ARTIFACT_CLOSURE_MISMATCH")
            for asset_name, asset in assets.items():
                if asset["architecture"] != "linux/arm64":
                    cf.append("EMBEDDED_ARTIFACT_ARCH_MISMATCH")
                if not asset.get("sha256"):
                    cb.append("EMBEDDED_ARTIFACT_DIGEST_UNFROZEN")
                elif actual_assets.get(asset_name) != asset:
                    cf.append("EMBEDDED_ARTIFACT_MISMATCH")
        row = _decision(GATES[0], cf, cb)
        rows.append(
            {"component_name": name, "status": row["status"], "reasons": row["reasons"]}
        )
        fail.extend(name + ":" + reason for reason in cf)
        block.extend(name + ":" + reason for reason in cb)
    return _decision(GATES[0], fail, block, components=rows)


def _process_key(process):
    return tuple(
        process[k]
        for k in ("host_boot_id", "pid", "start_ticks", "pid_namespace", "scope")
    )


def _sample_empty(sample):
    return not (
        sample["processes"]
        or sample["fds"]
        or sample["units"]
        or any(cg["populated"] or cg["members"] for cg in sample["cgroups"])
    )


def _timing(samples):
    elapsed = [s["elapsed_ms"] for s in samples]
    return (
        bool(elapsed)
        and elapsed[0] <= POLL_MS
        and all(0 < after - before <= POLL_MS for before, after in pairwise(elapsed))
    )


def _execution_join_mismatches(evidence):
    """Join each termination owner to its runtime record, including non-restores."""
    mismatches = set()
    cases = evidence["termination_cases"]
    for case in cases:
        matches = [r for r in evidence["network_rounds"] if r["owner"] == case["owner"]]
        if (
            sum(c["owner"] == case["owner"] for c in cases) != 1
            or len(matches) != 1
            or matches[0]["runtime_network"]["execution_id"] != case["execution_id"]
        ):
            mismatches.add(case["owner"])
    return mismatches


def _reap(evidence):
    fail, block = [], []
    cases = evidence["termination_cases"]
    execution_mismatches = _execution_join_mismatches(evidence)
    if {c["scenario"] for c in cases} != SCENARIOS:
        block.append("TERMINATION_SCENARIO_COVERAGE_MISSING")
    for case in cases:
        label = case["scenario"] + ":"
        if case["owner"] in execution_mismatches:
            fail.append(label + "EXECUTION_JOIN_MISMATCH")
        active, samples = case["active"], case["observations"]
        if not {"payload", "vmm", "controller", "helper"} <= {
            p["role"] for p in active["processes"]
        }:
            block.append(label + "ACTIVE_PROCESS_WITNESS_MISSING")
        if not active["units"] or not any(
            cg["members"] and cg["populated"] for cg in active["cgroups"]
        ):
            block.append(label + "ACTIVE_UNIT_CGROUP_WITNESS_MISSING")
        for sample in [active, *samples]:
            if not all(sample["complete"].values()):
                block.append(label + "REAP_OBSERVATION_INCOMPLETE")
            keys = [_process_key(p) for p in sample["processes"]]
            if len(keys) != len(set(keys)):
                fail.append(label + "PROCESS_IDENTITY_COLLISION")
            if any(
                p["owner"] != case["owner"] for p in sample["processes"] + sample["fds"]
            ):
                fail.append(label + "REAP_OWNER_MISMATCH")
        if not _timing(samples):
            fail.append(label + "POLL_TIMING_INVALID")
        if samples[-1]["elapsed_ms"] > DEADLINE_MS:
            fail.append(label + "TERMINATION_DEADLINE_EXCEEDED")
        if len(samples) < 2 or not all(_sample_empty(s) for s in samples[-2:]):
            if samples[-1]["elapsed_ms"] >= DEADLINE_MS:
                fail.append(label + "REAP_DEADLINE_RESIDUE")
            else:
                block.append(label + "COMPLETE_REAP_NOT_OBSERVED")
        # A terminal caller-supplied unit disappearance cannot hide an async helper.
        if samples[-1]["elapsed_ms"] >= DEADLINE_MS and (
            len(samples) < 2
            or not all(all(s["complete"].values()) for s in samples[-2:])
        ):
            fail.append(label + "REAP_DEADLINE_UNPROVED")
    return _decision(GATES[1], fail, block)


def _owner(identity):
    return "/".join(
        str(identity[k]) for k in ("sandbox_id", "instance_id", "generation")
    )


def _sentinel_valid(sentinel):
    return (
        hashlib.sha256(bytes.fromhex(sentinel["content_hex"])).hexdigest()
        == sentinel["sha256"]
    )


def _restore_process_binding(restored, evidence):
    """Compare every restore claim with typed observations, never a verified flag."""
    fail, block = [], []
    observations = evidence["restore_process_observations"]
    known = {}
    for case in evidence["termination_cases"]:
        for sample in [case["active"], *case["observations"]]:
            for process in sample["processes"]:
                known.setdefault(canonical_hash(_process_key(process)), set()).add(
                    (process["owner"], case["execution_id"])
                )
    for observation in observations:
        for process in observation["processes"]:
            known.setdefault(canonical_hash(_process_key(process)), set()).add(
                (process["owner"], observation["execution_id"])
            )
    binding = (restored["owner"], restored["execution_id"])
    if any(known.get(key, set()) - {binding} for key in restored["host_processes"]):
        fail.append("RESTORE_PROCESS_FOREIGN_BINDING")
    matches = [
        o
        for o in observations
        if o["owner"] == restored["owner"]
        and o["snapshot_id"] == restored["snapshot_id"]
    ]
    if not matches:
        block.append("RESTORE_PROCESS_OBSERVATION_MISSING")
        return fail, block
    if len(matches) != 1:
        fail.append("RESTORE_PROCESS_OBSERVATION_COLLISION")
        return fail, block
    observed = matches[0]
    if observed["execution_id"] != restored["execution_id"]:
        fail.append("RESTORE_PROCESS_EXECUTION_MISMATCH")
    if not observed["complete"]:
        block.append("RESTORE_PROCESS_OBSERVATION_INCOMPLETE")
    processes = observed["processes"]
    if any(p["owner"] != restored["owner"] for p in processes):
        fail.append("RESTORE_PROCESS_OWNER_MISMATCH")
    if any(p["scope"] != "host" or p["role"] == "payload" for p in processes):
        fail.append("RESTORE_PROCESS_SCOPE_OR_ROLE_MISMATCH")
    if not {"vmm", "controller", "helper"} <= {p["role"] for p in processes}:
        block.append("RESTORE_PROCESS_ROLE_COVERAGE_MISSING")
    keys = [canonical_hash(_process_key(p)) for p in processes]
    if len(set(keys)) != len(keys):
        fail.append("RESTORE_PROCESS_IDENTITY_COLLISION")
    if set(restored["host_processes"]) != set(keys):
        block.append("RESTORE_PROCESS_OBSERVATION_MISSING")
    return fail, block


def _snapshot(evidence, catalog):
    s = evidence["snapshot"]
    fail, block = [], []
    if not s["observation_complete"]:
        block.append("SNAPSHOT_OBSERVATION_INCOMPLETE")
    if not _sentinel_valid(s["sentinel_before"]):
        fail.append("SNAPSHOT_SOURCE_HASH_MISMATCH")
    manifest_hash = canonical_hash(catalog["components"])
    if s["component_manifest_sha256"] != manifest_hash:
        fail.append("SNAPSHOT_COMPONENT_BINDING_MISMATCH")
    seen_instances = {s["source_identity"]["instance_id"]}
    previous_generation = s["source_identity"]["generation"]
    seen_processes = set(s["host_processes_before"])
    network_keys = set(s["other_sandbox_network_keys"])
    template = s["source_kind"] == "clean_template"
    if template:
        approved_template = {
            "snapshot_id": s["snapshot_id"],
            "content_sha256": s["template_content_sha256"],
            "approval_sha256": s["template_approval_sha256"],
        }
        if approved_template not in catalog["approved_clean_templates"]:
            block.append("CLEAN_TEMPLATE_NOT_APPROVED")
        if (
            s["source_execution_id"] is not None
            or s["source_request_sha256"] is not None
            or s["state_domains"] != ["base"]
            or s["checkpoint_processes"]
            or s["host_processes_before"]
        ):
            fail.append("TEMPLATE_CONTAINS_EXECUTION_STATE")
    elif (
        not s["source_execution_id"]
        or not s["source_request_sha256"]
        or not s["checkpoint_processes"]
        or len(s["host_processes_before"]) < 3
        or s["template_content_sha256"] is not None
        or s["template_approval_sha256"] is not None
    ):
        fail.append("SNAPSHOT_SOURCE_EXECUTION_BINDING_INVALID")
    seen_executions, seen_requests = set(), set()
    seen_sandboxes = {s["source_identity"]["sandbox_id"]}
    for index, restored in enumerate(s["restores"]):
        process_fail, process_block = _restore_process_binding(restored, evidence)
        fail.extend(process_fail)
        block.extend(process_block)
        ident = restored["identity"]
        mode = restored["restore_mode"]
        if mode == "cross_execution_state":
            fail.append("CROSS_EXECUTION_STATE_REUSE_UNAUTHORIZED")
        elif mode == "same_execution":
            if (
                template
                or restored["execution_id"] != s["source_execution_id"]
                or restored["request_sha256"] != s["source_request_sha256"]
            ):
                fail.append("CROSS_EXECUTION_STATE_REUSE_UNAUTHORIZED")
        elif (
            not template
            or restored["execution_id"] in seen_executions
            or restored["request_sha256"] in seen_requests
            or ident["sandbox_id"] in seen_sandboxes
        ):
            fail.append("CLEAN_TEMPLATE_NEW_EXECUTION_BINDING_INVALID")
        seen_executions.add(restored["execution_id"])
        seen_requests.add(restored["request_sha256"])
        seen_sandboxes.add(ident["sandbox_id"])
        if restored["state_domains"] != s["state_domains"]:
            fail.append("RESTORE_STATE_DOMAIN_CONTAMINATION")
        component_gate = _components(restored, catalog)
        if component_gate["status"] == "FAIL":
            fail.extend(
                "RESTORE_COMPONENT_BINDING:" + r for r in component_gate["reasons"]
            )
        elif component_gate["status"] == "BLOCKED":
            block.extend(
                "RESTORE_COMPONENT_BINDING:" + r for r in component_gate["reasons"]
            )
        if (
            (not template and ident["sandbox_id"] != s["source_identity"]["sandbox_id"])
            or ident["instance_id"] in seen_instances
            or ident["generation"] <= previous_generation
            or restored["owner"] != _owner(ident)
        ):
            fail.append("RESTORE_IDENTITY_COLLISION")
        seen_instances.add(ident["instance_id"])
        previous_generation = ident["generation"]
        if (
            restored["snapshot_id"] != s["snapshot_id"]
            or restored["component_manifest_sha256"] != manifest_hash
        ):
            fail.append("RESTORE_ARTIFACT_IDENTITY_MISMATCH")
        if restored["sentinel"] != s["sentinel_before"] or not _sentinel_valid(
            restored["sentinel"]
        ):
            fail.append("SNAPSHOT_HASH_MISMATCH")
        if s["post_snapshot_path"] in restored["post_snapshot_paths"]:
            fail.append("POST_SNAPSHOT_STATE_CONTAMINATION")
        if restored["checkpoint_processes"] != s["checkpoint_processes"]:
            fail.append("CHECKPOINT_PROCESS_STATE_MISMATCH")
        processes = restored["host_processes"]
        if len(set(processes)) != len(processes) or seen_processes.intersection(
            processes
        ):
            fail.append("HOST_PROCESS_NOT_REINITIALIZED")
        seen_processes.update(processes)
        keys = restored["network_resource_keys"]
        if (
            restored["network_owner"] != restored["owner"]
            or len(set(keys)) != len(keys)
            or network_keys.intersection(keys)
        ):
            fail.append("RESTORE_NETWORK_IDENTITY_COLLISION")
        network_keys.update(keys)
        linked_network = [
            r for r in evidence["network_rounds"] if r["owner"] == restored["owner"]
        ]
        if len(linked_network) != 1 or set(keys) != {
            r["key"]
            for r in linked_network[0]["active"]["resources"]
            if r["owner"] == restored["owner"]
        }:
            fail.append("RESTORE_NETWORK_EVIDENCE_JOIN_MISMATCH")
        if len(linked_network) == 1 and (
            linked_network[0]["runtime_network"]["execution_id"]
            != restored["execution_id"]
            or linked_network[0]["runtime_network"]["request_sha256"]
            != restored["request_sha256"]
        ):
            fail.append("RESTORE_NETWORK_EXECUTION_JOIN_MISMATCH")
        if index == 0:
            linked_reap = [
                c
                for c in evidence["termination_cases"]
                if c["owner"] == restored["owner"]
            ]
            if len(linked_reap) != 1 or set(processes) != {
                canonical_hash(_process_key(p))
                for p in linked_reap[0]["active"]["processes"]
                if p["role"] in {"vmm", "controller", "helper"}
            }:
                fail.append("RESTORE_DESTROY_EVIDENCE_JOIN_MISMATCH")
            if (
                len(linked_reap) == 1
                and linked_reap[0]["execution_id"] != restored["execution_id"]
            ):
                fail.append("RESTORE_DESTROY_EXECUTION_JOIN_MISMATCH")
    return _decision(GATES[2], fail, block)


def _resources(sample):
    return _index(sample["resources"], "key")


def _deny_all(round_, catalog, restored_owners):
    fail, block = [], []
    observed, approved = round_["runtime_network"], catalog["network_policy"]
    if observed["owner"] != round_["owner"]:
        fail.append("NETWORK_RUNTIME_OWNER_MISMATCH")
    if observed["mode"] != "deny_all" or observed["architecture"] != "linux/arm64":
        fail.append("DENY_ALL_POLICY_OR_ARCH_MISMATCH")
    for field in ("configuration_sha256", "filter_sha256", "socket_abi_sha256"):
        if approved[field] is None:
            block.append("DENY_ALL_IDENTITY_UNFROZEN")
        elif observed[field] != approved[field]:
            fail.append("DENY_ALL_IDENTITY_MISMATCH")
    if not observed["installed_before_workload"]:
        fail.append("DENY_ALL_INSTALLED_TOO_LATE")
    if not observed["coverage_through_workload_end"]:
        block.append("DENY_ALL_RUNTIME_COVERAGE_INCOMPLETE")
    required = set(approved["required_socket_operations"])
    if not SOCKET_OPERATIONS <= required or len(required) != len(
        approved["required_socket_operations"]
    ):
        block.append("DENY_ALL_SOCKET_ABI_UNFROZEN")
    samples = observed["observations"]
    phases = ["before_first_instruction", "running"]
    if round_["owner"] in restored_owners:
        phases.append("after_restore_before_resume")
    if [s["phase"] for s in samples] != phases or [
        s["sequence"] for s in samples
    ] != list(range(len(samples))):
        fail.append("DENY_ALL_PHASE_SEQUENCE_INVALID")
    for sample in samples:
        if not sample["complete"]:
            block.append("DENY_ALL_OBSERVATION_INCOMPLETE")
        if not sample["enforcement_active"]:
            fail.append("DENY_ALL_ENFORCEMENT_INACTIVE")
        if sample["exposed_paths"]:
            fail.append("DENY_ALL_NETWORK_OR_CONTROL_PATH_EXPOSED")
        probes = _index(sample["socket_probes"], "operation")
        if set(probes) != required:
            block.append("DENY_ALL_SOCKET_PROBE_COVERAGE_MISSING")
        if any(not p["denied"] or p["errno"] not in {1, 13} for p in probes.values()):
            fail.append("DENY_ALL_SOCKET_OPERATION_SUCCEEDED")
    if any(
        r["guest_attachment"]
        and (
            r["owner"] == round_["owner"] or round_["owner"] in r["sandbox_references"]
        )
        for r in round_["active"]["resources"]
    ):
        fail.append("DENY_ALL_GUEST_NETWORK_ATTACHMENT")
    return fail, block


def _remember_owned(resources, pre, owners, history):
    for key, resource in resources.items():
        if resource["owner"] in owners or owners.intersection(
            resource["sandbox_references"]
        ):
            baseline = pre.get(key)
            history.setdefault(
                key,
                baseline
                if baseline and baseline["lifetime_owner"] == "shared"
                else None,
            )


def _foreign_resource(resource, owner):
    return (resource["owner"] is not None and resource["owner"] != owner) or bool(
        set(resource["sandbox_references"]) - {owner}
    )


def _network(evidence, catalog):
    fail, block = [], []
    rounds = evidence["network_rounds"]
    owners = {r["owner"] for r in rounds}
    if len(owners) != len(rounds):
        fail.append("NETWORK_OWNER_GENERATION_REUSE")
    if [r["cycle_index"] for r in rounds] != list(range(len(rounds))):
        fail.append("NETWORK_CYCLE_SEQUENCE_INVALID")
    if {r["scenario"] for r in rounds} != SCENARIOS or sum(
        r["scenario"] == "normal_exit" for r in rounds
    ) < 3:
        block.append("NETWORK_SCENARIO_OR_REPEAT_COVERAGE_MISSING")
    seen_owned_keys = set()
    ownership_history = {}
    execution_mismatches = _execution_join_mismatches(evidence)
    restored_owners = {r["owner"] for r in evidence["snapshot"]["restores"]}
    for round_ in rounds:
        label, owner = str(round_["cycle_index"]) + ":", round_["owner"]
        if owner in execution_mismatches:
            fail.append(label + "EXECUTION_JOIN_MISMATCH")
        runtime_fail, runtime_block = _deny_all(round_, catalog, restored_owners)
        fail.extend(label + reason for reason in runtime_fail)
        block.extend(label + reason for reason in runtime_block)
        pre, active = _resources(round_["pre"]), _resources(round_["active"])
        samples = round_["post"]
        if not _timing(samples):
            fail.append(label + "NETWORK_POLL_TIMING_INVALID")
        if samples[-1]["elapsed_ms"] > DEADLINE_MS:
            fail.append(label + "NETWORK_DEADLINE_EXCEEDED")
        observed_owned = {
            k: v
            for k, v in active.items()
            if v["owner"] == owner or owner in v["sandbox_references"]
        }
        exclusive_keys = {
            k
            for k in observed_owned
            if k not in pre or pre[k]["lifetime_owner"] != "shared"
        }
        if seen_owned_keys.intersection(exclusive_keys):
            fail.append(label + "NETWORK_OBJECT_BIRTH_ID_REUSE")
        seen_owned_keys.update(exclusive_keys)
        _remember_owned(pre, pre, owners, ownership_history)
        _remember_owned(active, pre, owners, ownership_history)
        if not observed_owned:
            block.append(label + "ACTIVE_NETWORK_WITNESS_MISSING")
        if any(set(r["sandbox_references"]) - {owner} for r in observed_owned.values()):
            fail.append(label + "ACTIVE_CROSS_SANDBOX_REFERENCE")
        for key, old in pre.items():
            if _foreign_resource(old, owner) and active.get(key) != old:
                fail.append(label + "CROSS_SANDBOX_CONTAMINATION")
        clean = []
        for sample in [round_["pre"], round_["active"], *samples]:
            if (
                set(sample["complete_kinds"]) != KINDS
                or len(sample["complete_kinds"]) != len(KINDS)
                or sample["scan_errors"]
            ):
                block.append(label + "NETWORK_OBSERVATION_INCOMPLETE")
            _resources(sample)
            if any(
                r["lifetime_owner"] == "background"
                and (r["owner"] or r["sandbox_references"])
                for r in sample["resources"]
            ):
                fail.append(label + "BACKGROUND_ATTRIBUTION_CONTRADICTION")
        for sample in samples:
            post = _resources(sample)
            _remember_owned(post, pre, owners, ownership_history)
            residue = False
            for key, resource in post.items():
                if resource["owner"] in owners or owners.intersection(
                    resource["sandbox_references"]
                ):
                    residue = True
                if key in ownership_history:
                    baseline = ownership_history[key]
                    # Only a pre-existing shared pool object may survive release.
                    if (
                        baseline is None
                        or baseline["lifetime_owner"] != "shared"
                        or baseline["owner"] is not None
                        or baseline["sandbox_references"]
                        or resource != baseline
                    ):
                        residue = True
                if resource["lifetime_owner"] == "unknown" or (
                    resource["lifetime_owner"] == "sandbox"
                    and resource["owner"] is None
                ):
                    block.append(label + "ORPHAN_ATTRIBUTION_UNKNOWN")
                if (
                    key not in pre
                    and key not in active
                    and resource["lifetime_owner"] != "background"
                ):
                    residue = True
            for key, old in pre.items():
                if _foreign_resource(old, owner) and post.get(key) != old:
                    fail.append(label + "CROSS_SANDBOX_CONTAMINATION")
            clean.append(not residue)
            if residue and sample["elapsed_ms"] >= DEADLINE_MS:
                fail.append(label + "SANDBOX_NETWORK_RESOURCE_LEAK")
        if len(clean) < 2 or not all(clean[-2:]):
            if samples[-1]["elapsed_ms"] >= DEADLINE_MS:
                fail.append(label + "NETWORK_RELEASE_DEADLINE_UNPROVED")
            else:
                block.append(label + "NETWORK_RELEASE_NOT_OBSERVED")
        if samples[-1]["elapsed_ms"] >= DEADLINE_MS and any(
            set(s["complete_kinds"]) != KINDS or s["scan_errors"] for s in samples[-2:]
        ):
            fail.append(label + "NETWORK_DEADLINE_UNPROVED")
    return _decision(GATES[3], fail, block)


def evaluate_json(evidence_json, catalog, schema):
    """Evaluate synthetic evidence only. Never dispatch, trust a PASS, or grant authority."""
    try:
        if len(evidence_json.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("EVIDENCE_BYTE_LIMIT")
        evidence = json.loads(
            evidence_json, object_pairs_hook=_strict_pairs, parse_constant=_no_constant
        )
        Draft202012Validator.check_schema(schema)
        # This trusted local schema has local refs only; no network resolver is used.
        for value, definition in ((evidence, "evidence"), (catalog, "catalog")):
            validator = Draft202012Validator(
                {"$ref": "#/$defs/" + definition, "$defs": schema["$defs"]}
            )
            if not validator.is_valid(value):
                raise ValueError("SCHEMA_VIOLATION")
        if evidence["evidence_class"] != "synthetic":
            return _result(
                [
                    _decision(
                        g, blockers=["REAL_HOST_IMPORT_NOT_IMPLEMENTED_OR_AUTHORIZED"]
                    )
                    for g in GATES
                ]
            )
        return _result(
            [
                _components(evidence, catalog),
                _reap(evidence),
                _snapshot(evidence, catalog),
                _network(evidence, catalog),
            ]
        )
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        return _result([_decision(g, failures=[str(exc)]) for g in GATES])


def evaluate_for_development_loop(evidence_json, catalog, schema):
    """Use the existing development-loop Validator shape, preserving every gate."""
    result = evaluate_json(evidence_json, catalog, schema)
    return {
        "validation_results": {
            gate["gate"]: {
                "status": "PASS" if gate["status"] == "PASS" else "BLOCK",
                "diagnostic": json.dumps(gate, sort_keys=True),
            }
            for gate in result["gates"]
        },
        "satisfied_acceptance_items": [
            gate["gate"] for gate in result["gates"] if gate["status"] == "PASS"
        ],
    }
