"""Synthetic contract checks only; no CubeSandbox, systemd or network invocation."""

from __future__ import annotations

import ast
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from cubesandbox_contract_oracle import (
    GATES,
    canonical_hash,
    evaluate_for_development_loop,
    evaluate_json,
)
from jsonschema import Draft202012Validator

from tool_system.development_loop import (
    DevelopmentLoopLimits,
    FrozenDevelopmentContract,
    run_development_loop,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "harness/cubesandbox_backend_acceptance_v1.schema.json").read_text()
)
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/cubesandbox_backend_acceptance_v1.json").read_text()
)


@pytest.fixture
def inputs():
    return deepcopy(FIXTURE["passing_evidence"]), deepcopy(FIXTURE["synthetic_catalog"])


def evaluate(evidence, catalog):
    result = evaluate_json(json.dumps(evidence), catalog, SCHEMA)
    Draft202012Validator({"$ref": "#/$defs/result", "$defs": SCHEMA["$defs"]}).validate(
        result
    )
    return result


def gate(result, index):
    assert [g["gate"] for g in result["gates"]] == list(GATES)
    return result["gates"][index]


def rebind_fixture_snapshot(evidence, catalog):
    digest = canonical_hash(catalog["components"])
    evidence["snapshot"]["component_manifest_sha256"] = digest
    for restored in evidence["snapshot"]["restores"]:
        restored["component_manifest_sha256"] = digest


def expire_samples(sample):
    return [{**deepcopy(sample), "elapsed_ms": ms} for ms in range(0, 60_001, 250)]


def test_pass_input_passes_all_gates_without_host_authority(inputs):
    evidence, catalog = inputs
    before = deepcopy(inputs)
    result = evaluate(evidence, catalog)
    assert result["status"] == "PASS"
    assert [g["status"] for g in result["gates"]] == ["PASS"] * 4
    assert result["real_backend_acceptance_authorized"] is False
    assert result["real_backend_acceptance_executed"] is False
    assert inputs == before


@pytest.mark.parametrize("omit", [False, True])
def test_missing_lifecycle_digest_is_blocked_never_warn(inputs, omit):
    evidence, catalog = inputs
    component = catalog["components"][-1]
    if omit:
        del component["oci_digest"]
    else:
        component["oci_digest"] = None
    rebind_fixture_snapshot(evidence, catalog)
    result = evaluate(evidence, catalog)
    assert result["status"] == "BLOCKED"
    assert gate(result, 0)["status"] == "BLOCKED"
    assert (
        "cube-lifecycle-manager:APPROVED_DIGEST_MISSING" in gate(result, 0)["reasons"]
    )


def test_actual_candidate_remains_unfrozen_and_blocked(inputs):
    evidence, _ = inputs
    candidate = deepcopy(FIXTURE["candidate_catalog"])
    evidence["catalog_id"] = candidate["catalog_id"]
    rebind_fixture_snapshot(evidence, candidate)
    result = evaluate(evidence, candidate)
    assert gate(result, 0)["status"] == "BLOCKED"
    assert (
        "cube-lifecycle-manager:APPROVED_DIGEST_MISSING" in gate(result, 0)["reasons"]
    )
    assert candidate["components"][-1]["oci_digest"] is None
    assert (
        candidate["components"][5]["oci_digest"]
        == "sha256:1fc7ed98650e91edb8ead48094950370ed30c0e7016796c3036063ccc6e4ea71"
    )
    assert candidate["published_attestations"] is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("oci_digest", "sha256:" + "0" * 64, "OCI_DIGEST_MISMATCH"),
        ("release_tag", "v0.7.1", "RELEASE_TAG_MISMATCH"),
        ("source_commit", "0" * 40, "SOURCE_COMMIT_MISMATCH"),
        ("architecture", "linux/amd64", "ARCHITECTURE_MISMATCH"),
        ("registry", "unapproved.invalid/cubelet", "REGISTRY_MISMATCH"),
    ],
)
def test_component_mismatch_fails_backend(inputs, field, value, reason):
    evidence, catalog = inputs
    evidence["components"][0][field] = value
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert "cubelet:" + reason in gate(result, 0)["reasons"]


@pytest.mark.parametrize("tag", ["latest", "v0.7.0", "v0.7.0-arm64"])
def test_mutable_reference_cannot_pass(inputs, tag):
    evidence, catalog = inputs
    evidence["components"][0]["requested_ref"] = "ghcr.io/tencentcloud/cubelet:" + tag
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert "cubelet:DIGEST_REFERENCE_REQUIRED" in gate(result, 0)["reasons"]


def test_embedded_vmm_hash_mismatch_fails(inputs):
    evidence, catalog = inputs
    evidence["components"][1]["embedded_artifacts"][0]["sha256"] = "0" * 64
    assert (
        "cube-shim:EMBEDDED_ARTIFACT_MISMATCH"
        in gate(evaluate(evidence, catalog), 0)["reasons"]
    )


@pytest.mark.parametrize(
    "resource",
    [
        "helper",
        "async_close",
        "payload",
        "vmm",
        "controller",
        "pid1_fd",
        "cgroup",
        "unit",
    ],
)
def test_unit_disappearance_or_main_exit_cannot_hide_reap_residue(inputs, resource):
    evidence, catalog = inputs
    case = evidence["termination_cases"][0]
    sample = deepcopy(case["observations"][-1])
    if resource in {"helper", "async_close", "payload", "vmm", "controller"}:
        sample["processes"] = [
            p for p in case["active"]["processes"] if p["role"] == resource
        ]
    elif resource == "pid1_fd":
        sample["fds"] = deepcopy(case["active"]["fds"])
    elif resource == "cgroup":
        sample["cgroups"] = deepcopy(case["active"]["cgroups"])
    else:
        sample["units"] = deepcopy(case["active"]["units"])
    case["observations"] = expire_samples(sample)
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert "normal_exit:REAP_DEADLINE_RESIDUE" in gate(result, 1)["reasons"]


def test_late_complete_reap_fails_even_with_empty_final_sample(inputs):
    evidence, catalog = inputs
    evidence["termination_cases"][0]["observations"][-1]["elapsed_ms"] = 60_001
    result = evaluate(evidence, catalog)
    assert "normal_exit:TERMINATION_DEADLINE_EXCEEDED" in gate(result, 1)["reasons"]
    assert result["status"] == "FAIL"


def test_missing_pid1_visibility_is_blocked(inputs):
    evidence, catalog = inputs
    evidence["termination_cases"][0]["observations"][-1]["complete"]["fds"] = False
    result = evaluate(evidence, catalog)
    assert gate(result, 1)["status"] == "BLOCKED"
    assert "normal_exit:REAP_OBSERVATION_INCOMPLETE" in gate(result, 1)["reasons"]


def test_snapshot_hash_mismatch_fails(inputs):
    evidence, catalog = inputs
    evidence["snapshot"]["restores"][0]["sentinel"]["sha256"] = "0" * 64
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert "SNAPSHOT_HASH_MISMATCH" in gate(result, 2)["reasons"]


@pytest.mark.parametrize(
    "mutation",
    [
        "after_state",
        "process_state",
        "host_pid",
        "instance",
        "generation",
        "network",
        "artifact",
    ],
)
def test_restore_isolation_has_explicit_field_comparisons(inputs, mutation):
    evidence, catalog = inputs
    snapshot = evidence["snapshot"]
    restored = snapshot["restores"][1]
    reasons = {
        "after_state": "POST_SNAPSHOT_STATE_CONTAMINATION",
        "process_state": "CHECKPOINT_PROCESS_STATE_MISMATCH",
        "host_pid": "HOST_PROCESS_NOT_REINITIALIZED",
        "instance": "RESTORE_IDENTITY_COLLISION",
        "generation": "RESTORE_IDENTITY_COLLISION",
        "network": "RESTORE_NETWORK_IDENTITY_COLLISION",
        "artifact": "RESTORE_ARTIFACT_IDENTITY_MISMATCH",
    }
    if mutation == "after_state":
        restored["post_snapshot_paths"].append(snapshot["post_snapshot_path"])
    if mutation == "process_state":
        restored["checkpoint_processes"][0]["state_sha256"] = "0" * 64
    if mutation == "host_pid":
        restored["host_processes"][0] = snapshot["host_processes_before"][0]
    if mutation == "instance":
        restored["identity"]["instance_id"] = snapshot["restores"][0]["identity"][
            "instance_id"
        ]
    if mutation == "generation":
        restored["identity"]["generation"] = 0
    if mutation == "network":
        restored["network_resource_keys"][0] = snapshot["other_sandbox_network_keys"][0]
    if mutation == "artifact":
        restored["snapshot_id"] = "wrong-snapshot"
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert reasons[mutation] in gate(result, 2)["reasons"]


@pytest.mark.parametrize(
    "kind",
    [
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
    ],
)
def test_every_owned_network_resource_must_disappear_by_deadline(inputs, kind):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    sample = deepcopy(round_["post"][-1])
    sample["resources"].append(
        next(
            r
            for r in round_["active"]["resources"]
            if r["kind"] == kind and r["owner"] == round_["owner"]
        )
    )
    round_["post"] = expire_samples(sample)
    result = evaluate(evidence, catalog)
    assert result["status"] == "FAIL"
    assert "0:SANDBOX_NETWORK_RESOURCE_LEAK" in gate(result, 3)["reasons"]


@pytest.mark.parametrize(
    ("first_clean_ms", "reason"),
    [
        (60_000, "NETWORK_RELEASE_DEADLINE_UNPROVED"),
        (60_001, "NETWORK_DEADLINE_EXCEEDED"),
    ],
)
def test_network_release_needs_two_clean_samples_before_deadline(
    inputs, first_clean_ms, reason
):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    clean = deepcopy(round_["post"][-1])
    residue = deepcopy(clean)
    residue["resources"].append(
        next(r for r in round_["active"]["resources"] if r["owner"] == round_["owner"])
    )
    round_["post"] = expire_samples(residue)
    clean["elapsed_ms"] = first_clean_ms
    if first_clean_ms == 60_000:
        round_["post"][-1] = clean
    else:
        round_["post"].append(clean)
    result = evaluate(evidence, catalog)
    assert gate(result, 3)["status"] == "FAIL"
    assert "0:" + reason in gate(result, 3)["reasons"]
    assert result["status"] == "FAIL"


def test_unrelated_background_network_change_is_not_a_leak(inputs):
    evidence, catalog = inputs
    for sample in evidence["network_rounds"][0]["post"]:
        sample["resources"][0]["fingerprint_sha256"] = "f" * 64
        unrelated = deepcopy(sample["resources"][0])
        unrelated["key"] = "unrelated-host-route-added"
        sample["resources"].append(unrelated)
    assert evaluate(evidence, catalog)["status"] == "PASS"


def test_cross_sandbox_contamination_fails_even_without_leak(inputs):
    evidence, catalog = inputs
    evidence["network_rounds"][0]["post"][-1]["resources"][1]["fingerprint_sha256"] = (
        "0" * 64
    )
    result = evaluate(evidence, catalog)
    assert gate(result, 3)["status"] == "FAIL"
    assert "0:CROSS_SANDBOX_CONTAMINATION" in gate(result, 3)["reasons"]


def test_relabelling_owned_tap_as_background_cannot_hide_leak(inputs):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    leaked = deepcopy(round_["active"]["resources"][2])
    leaked.update(owner=None, sandbox_references=[], lifetime_owner="background")
    sample = deepcopy(round_["post"][-1])
    sample["resources"].append(leaked)
    round_["post"] = expire_samples(sample)
    assert (
        "0:SANDBOX_NETWORK_RESOURCE_LEAK"
        in gate(evaluate(evidence, catalog), 3)["reasons"]
    )


def test_preexisting_shared_pool_survives_only_without_lease_or_policy(inputs):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    pooled = deepcopy(round_["active"]["resources"][2])
    pooled.update(lifetime_owner="shared", owner=None, sandbox_references=[])
    round_["pre"]["resources"].append(deepcopy(pooled))
    for sample in round_["post"]:
        sample["resources"].append(deepcopy(pooled))
    assert evaluate(evidence, catalog)["status"] == "PASS"
    sample = deepcopy(round_["post"][-1])
    sample["resources"][-1]["sandbox_references"] = [round_["owner"]]
    round_["post"] = expire_samples(sample)
    assert gate(evaluate(evidence, catalog), 3)["status"] == "FAIL"


def test_reused_owner_generation_is_a_collision(inputs):
    evidence, catalog = inputs
    evidence["network_rounds"][-1]["owner"] = evidence["network_rounds"][0]["owner"]
    assert (
        "NETWORK_OWNER_GENERATION_REUSE"
        in gate(evaluate(evidence, catalog), 3)["reasons"]
    )


@pytest.mark.parametrize(
    "case", ["duplicate_key", "extra_pass", "nan", "missing_field", "wrong_type"]
)
def test_strict_parser_rejects_ambiguous_or_forged_evidence(inputs, case):
    evidence, catalog = inputs
    if case == "extra_pass":
        evidence["PASS"] = True
    if case == "missing_field":
        del evidence["snapshot"]
    if case == "wrong_type":
        evidence["termination_cases"][0]["observations"][0]["elapsed_ms"] = True
    raw = json.dumps(evidence)
    if case == "duplicate_key":
        raw = '{"run_id":"duplicate",' + raw[1:]
    if case == "nan":
        raw = raw.replace('"synthetic-only-run-v1"', "NaN")
    result = evaluate_json(raw, catalog, SCHEMA)
    assert result["status"] == "FAIL"


def test_host_evidence_is_blocked_by_test_only_import_boundary(inputs):
    evidence, catalog = inputs
    evidence["evidence_class"] = "host_os"
    result = evaluate(evidence, catalog)
    assert result["status"] == "BLOCKED"
    assert all(
        g["reasons"] == ["REAL_HOST_IMPORT_NOT_IMPLEMENTED_OR_AUTHORIZED"]
        for g in result["gates"]
    )


@pytest.mark.parametrize("failing", [False, True])
def test_existing_development_loop_consumes_gate_validation_without_new_framework(
    inputs, failing
):
    evidence, catalog = inputs
    if failing:
        evidence["snapshot"]["restores"][0]["sentinel"]["sha256"] = "0" * 64
    raw = json.dumps(evidence)
    result = run_development_loop(
        contract=FrozenDevelopmentContract(
            task_digest=canonical_hash(catalog),
            baseline_tree="b" * 40,
            allowed_scope=("fixture.json",),
            acceptance_set=GATES,
            validation_set=GATES,
        ),
        baseline_files={"fixture.json": "{}"},
        worker=lambda _: {
            "operations": [
                {
                    "op": "replace",
                    "path": "fixture.json",
                    "expected_sha256": hashlib.sha256(b"{}").hexdigest(),
                    "content": raw,
                }
            ]
        },
        validator=lambda files: evaluate_for_development_loop(
            files["fixture.json"], catalog, SCHEMA
        ),
        code_reviewer=lambda _: {"violated_acceptance_items": [], "suggestions": []},
        contract_reviewer=lambda _: {
            "violated_acceptance_items": [],
            "suggestions": [],
        },
        limits=DevelopmentLoopLimits(max_cycles=1, max_worker_calls=1),
    )
    assert result["status"] == ("BLOCK" if failing else "PASS")
    assert result["terminal_candidate_sealed"] is not failing
    assert all(
        result[key] is False
        for key in (
            "writes_filesystem",
            "calls_git",
            "calls_provider",
            "reads_credentials",
            "writes_target_repo",
        )
    )


def test_schema_reuses_local_definitions_and_oracle_has_no_execution_imports():
    Draft202012Validator.check_schema(SCHEMA)

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                assert value["$ref"].startswith("#/$defs/")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(SCHEMA)
    tree = ast.parse((ROOT / "tests/cubesandbox_contract_oracle.py").read_text())
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imports == {"__future__", "hashlib", "itertools", "json", "jsonschema"}


def test_review_jointly_empty_embedded_artifacts_cannot_pass(inputs):
    evidence, catalog = inputs
    for component in catalog["components"] + evidence["components"]:
        component["embedded_artifacts"] = []
    rebind_fixture_snapshot(evidence, catalog)
    assert gate(evaluate(evidence, catalog), 0)["status"] == "BLOCKED"


def test_review_previous_owned_identity_cannot_become_background(inputs):
    evidence, catalog = inputs
    first, second = evidence["network_rounds"][:2]
    old = deepcopy(
        next(r for r in first["active"]["resources"] if r["owner"] == first["owner"])
    )
    old.update(lifetime_owner="background", owner=None, sandbox_references=[])
    sample = deepcopy(second["post"][-1])
    sample["resources"].append(old)
    second["post"] = expire_samples(sample)
    assert gate(evaluate(evidence, catalog), 3)["status"] == "FAIL"


def test_review_penultimate_fd_gap_at_deadline_is_fail(inputs):
    evidence, catalog = inputs
    case = evidence["termination_cases"][0]
    case["observations"] = expire_samples(case["observations"][-1])
    case["observations"][-2]["complete"]["fds"] = False
    assert gate(evaluate(evidence, catalog), 1)["status"] == "FAIL"


def test_review_no_pid1_retention_with_complete_scan_can_pass(inputs):
    evidence, catalog = inputs
    for case in evidence["termination_cases"]:
        case["active"]["fds"] = []
    assert gate(evaluate(evidence, catalog), 1)["status"] == "PASS"


def test_review_runtime_deny_all_evidence_cannot_be_omitted(inputs):
    evidence, catalog = inputs
    evidence["network_rounds"][0].pop("runtime_network", None)
    assert gate(evaluate(evidence, catalog), 3)["status"] == "FAIL"


def test_review_restored_actual_components_cannot_be_omitted(inputs):
    evidence, catalog = inputs
    evidence["snapshot"]["restores"][0].pop("components", None)
    assert gate(evaluate(evidence, catalog), 2)["status"] == "FAIL"


@pytest.mark.parametrize(
    ("definition", "fields"),
    [
        ("component", {"artifact_type"}),
        (
            "catalog",
            {"required_artifacts", "network_policy", "approved_clean_templates"},
        ),
        (
            "snapshot",
            {
                "source_kind",
                "source_execution_id",
                "source_request_sha256",
                "state_domains",
            },
        ),
        ("restore", {"restore_mode", "execution_id", "request_sha256", "components"}),
    ],
)
def test_review_binding_fields_are_machine_required(definition, fields):
    assert fields <= set(SCHEMA["$defs"][definition]["required"])


def test_required_artifact_floor_cannot_be_erased_from_both_inputs(inputs):
    evidence, catalog = inputs
    catalog["required_artifacts"] = []
    for c in catalog["components"] + evidence["components"]:
        c["embedded_artifacts"] = []
    rebind_fixture_snapshot(evidence, catalog)
    result = gate(evaluate(evidence, catalog), 0)
    assert result["status"] == "BLOCKED"
    assert "REQUIRED_ARTIFACT_SET_UNFROZEN" in result["reasons"]
    assert "REQUIRED_ARTIFACT_MISSING" in result["reasons"]


@pytest.mark.parametrize("field", ["sha256", "path", "fake_oci"])
def test_plain_file_identity_is_compared_without_fictitious_oci(inputs, field):
    evidence, catalog = inputs
    c = evidence["components"][2]
    assert c["artifact_type"] == "file" and c["oci_digest"] is None
    if field == "fake_oci":
        c["oci_digest"] = "sha256:" + "0" * 64
        reason = "SCHEMA_VIOLATION"
    else:
        c["file_identity"][field] = "0" * 64 if field == "sha256" else "/wrong/kernel"
        reason = (
            "cube-kernel:FILE_DIGEST_MISMATCH"
            if field == "sha256"
            else "cube-kernel:FILE_PATH_MISMATCH"
        )
    result = gate(evaluate(evidence, catalog), 0)
    assert result["status"] == "FAIL"
    assert reason in result["reasons"]


@pytest.mark.parametrize("omit", [False, True])
def test_unfrozen_plain_file_digest_blocks(inputs, omit):
    evidence, catalog = inputs
    identity = catalog["components"][2]["file_identity"]
    if omit:
        identity.pop("sha256")
    else:
        identity["sha256"] = None
    rebind_fixture_snapshot(evidence, catalog)
    result = gate(evaluate(evidence, catalog), 0)
    assert result["status"] == "BLOCKED"
    assert "cube-kernel:APPROVED_DIGEST_MISSING" in result["reasons"]


@pytest.mark.parametrize("role", ["helper", "async_close"])
def test_no_pid1_positive_control_does_not_exempt_helpers(inputs, role):
    evidence, catalog = inputs
    case = evidence["termination_cases"][0]
    case["active"]["fds"] = []
    sample = deepcopy(case["observations"][-1])
    sample["processes"] = [p for p in case["active"]["processes"] if p["role"] == role]
    case["observations"] = expire_samples(sample)
    result = gate(evaluate(evidence, catalog), 1)
    assert result["status"] == "FAIL"
    assert "normal_exit:REAP_DEADLINE_RESIDUE" in result["reasons"]


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("allow", "DENY_ALL_POLICY_OR_ARCH_MISMATCH"),
        ("late", "DENY_ALL_INSTALLED_TOO_LATE"),
        ("inactive", "DENY_ALL_ENFORCEMENT_INACTIVE"),
        ("nic", "DENY_ALL_NETWORK_OR_CONTROL_PATH_EXPOSED"),
        ("vsock", "DENY_ALL_NETWORK_OR_CONTROL_PATH_EXPOSED"),
        ("guest_tap", "DENY_ALL_GUEST_NETWORK_ATTACHMENT"),
        ("filter", "DENY_ALL_IDENTITY_MISMATCH"),
        ("abi", "DENY_ALL_IDENTITY_MISMATCH"),
        ("socket_success", "DENY_ALL_SOCKET_OPERATION_SUCCEEDED"),
        ("restore_path", "DENY_ALL_NETWORK_OR_CONTROL_PATH_EXPOSED"),
    ],
)
def test_runtime_deny_all_is_independent_of_successful_cleanup(
    inputs, mutation, reason
):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    runtime = round_["runtime_network"]
    if mutation == "allow":
        runtime["mode"] = "allow_network"
    elif mutation == "late":
        runtime["installed_before_workload"] = False
    elif mutation == "inactive":
        runtime["observations"][1]["enforcement_active"] = False
    elif mutation in {"nic", "vsock"}:
        runtime["observations"][1]["exposed_paths"] = [mutation]
    elif mutation == "guest_tap":
        round_["active"]["resources"][2]["guest_attachment"] = True
    elif mutation in {"filter", "abi"}:
        runtime["filter_sha256" if mutation == "filter" else "socket_abi_sha256"] = (
            "0" * 64
        )
    elif mutation == "socket_success":
        runtime["observations"][1]["socket_probes"][0].update(denied=False, errno=0)
    else:
        runtime["observations"][-1]["exposed_paths"] = ["restored-inherited-socket"]
    result = gate(evaluate(evidence, catalog), 3)
    assert result["status"] == "FAIL"
    assert "0:" + reason in result["reasons"]


@pytest.mark.parametrize(
    "missing", ["probe", "coverage", "complete", "approved_identity", "abi_floor"]
)
def test_incomplete_deny_all_proof_blocks(inputs, missing):
    evidence, catalog = inputs
    runtime = evidence["network_rounds"][0]["runtime_network"]
    if missing == "probe":
        runtime["observations"][0]["socket_probes"].pop()
    elif missing == "coverage":
        runtime["coverage_through_workload_end"] = False
    elif missing == "complete":
        runtime["observations"][1]["complete"] = False
    elif missing == "approved_identity":
        catalog["network_policy"]["filter_sha256"] = None
    else:
        catalog["network_policy"]["required_socket_operations"].pop()
    assert gate(evaluate(evidence, catalog), 3)["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "mutation", ["digest", "version", "commit", "arch", "file", "embedded"]
)
def test_restored_components_are_revalidated_even_with_matching_catalog_hash(
    inputs, mutation
):
    evidence, catalog = inputs
    restored = evidence["snapshot"]["restores"][1]
    c = restored["components"][0]
    if mutation == "digest":
        c["oci_digest"] = "sha256:" + "0" * 64
    elif mutation == "version":
        c["release_tag"] = "v0.6.0"
    elif mutation == "commit":
        c["source_commit"] = "0" * 40
    elif mutation == "arch":
        c["architecture"] = "linux/amd64"
    elif mutation == "file":
        restored["components"][2]["file_identity"]["sha256"] = "0" * 64
    else:
        restored["components"][1]["embedded_artifacts"][0]["sha256"] = "0" * 64
    result = evaluate(evidence, catalog)
    assert gate(result, 0)["status"] == "PASS"
    assert gate(result, 2)["status"] == "FAIL"
    assert any(
        r.startswith("RESTORE_COMPONENT_BINDING:") for r in gate(result, 2)["reasons"]
    )
    assert result["status"] == "FAIL"


@pytest.mark.parametrize(
    "mutation", ["execution", "request", "explicit_cross_execution"]
)
def test_mutable_snapshot_cannot_cross_execution_boundary(inputs, mutation):
    evidence, catalog = inputs
    restored = evidence["snapshot"]["restores"][1]
    if mutation == "execution":
        restored["execution_id"] = "another-execution"
    elif mutation == "request":
        restored["request_sha256"] = "0" * 64
    else:
        restored["restore_mode"] = "cross_execution_state"
    result = gate(evaluate(evidence, catalog), 2)
    assert result["status"] == "FAIL"
    assert "CROSS_EXECUTION_STATE_REUSE_UNAUTHORIZED" in result["reasons"]


def clean_template_inputs(inputs):
    evidence, catalog = inputs
    s = evidence["snapshot"]
    approval = catalog["approved_clean_templates"][0]
    s.update(
        source_kind="clean_template",
        source_execution_id=None,
        source_request_sha256=None,
        state_domains=["base"],
        template_content_sha256=approval["content_sha256"],
        template_approval_sha256=approval["approval_sha256"],
        snapshot_id=approval["snapshot_id"],
        checkpoint_processes=[],
        host_processes_before=[],
    )
    s["source_identity"]["sandbox_id"] = "template-origin"
    for index, restored in enumerate(s["restores"]):
        old_owner = restored["owner"]
        restored["identity"]["sandbox_id"] = "fresh-template-sandbox-" + str(index)
        identity = restored["identity"]
        owner = f"{identity['sandbox_id']}/{identity['instance_id']}/{identity['generation']}"
        restored.update(
            restore_mode="clean_template_new_execution",
            execution_id="fresh-execution-" + str(index),
            request_sha256=str(index + 4) * 64,
            owner=owner,
            network_owner=owner,
            snapshot_id=s["snapshot_id"],
            state_domains=["base"],
            checkpoint_processes=[],
        )
        for case in evidence["termination_cases"]:
            if case["owner"] == old_owner:
                case.update(owner=owner, execution_id=restored["execution_id"])
                for sample in [case["active"], *case["observations"]]:
                    for row in sample["processes"] + sample["fds"]:
                        row["owner"] = owner
        for observation in evidence["restore_process_observations"]:
            if observation["owner"] == old_owner:
                observation.update(
                    owner=owner,
                    execution_id=restored["execution_id"],
                    snapshot_id=s["snapshot_id"],
                )
                for row in observation["processes"]:
                    row["owner"] = owner
        round_ = next(r for r in evidence["network_rounds"] if r["owner"] == old_owner)
        round_["owner"] = owner
        round_["runtime_network"].update(
            owner=owner,
            execution_id=restored["execution_id"],
            request_sha256=restored["request_sha256"],
        )
        for sample in [round_["pre"], round_["active"], *round_["post"]]:
            for resource in sample["resources"]:
                if resource["owner"] == old_owner:
                    resource["owner"] = owner
                resource["sandbox_references"] = [
                    owner if r == old_owner else r
                    for r in resource["sandbox_references"]
                ]
    return evidence, catalog


def test_approved_clean_template_can_start_distinct_fresh_executions(inputs):
    evidence, catalog = clean_template_inputs(inputs)
    assert evaluate(evidence, catalog)["status"] == "PASS"


@pytest.mark.parametrize(
    "mutation",
    ["unapproved", "dirty", "live_process", "same_execution", "changed_content"],
)
def test_clean_template_label_cannot_authorize_mutable_or_unapproved_state(
    inputs, mutation
):
    evidence, catalog = clean_template_inputs(inputs)
    s = evidence["snapshot"]
    if mutation == "unapproved":
        catalog["approved_clean_templates"] = []
    elif mutation == "dirty":
        s["state_domains"].append("scratch")
    elif mutation == "live_process":
        s["checkpoint_processes"] = [
            {"logical_id": "old-payload", "state_sha256": "0" * 64}
        ]
    elif mutation == "same_execution":
        s["restores"][1]["execution_id"] = s["restores"][0]["execution_id"]
    else:
        s["template_content_sha256"] = "0" * 64
    result = gate(evaluate(evidence, catalog), 2)
    assert result["status"] == (
        "BLOCKED" if mutation in {"unapproved", "changed_content"} else "FAIL"
    )


def test_post_template_restore_state_domains_are_compared(inputs):
    evidence, catalog = clean_template_inputs(inputs)
    evidence["snapshot"]["restores"][1]["state_domains"].append("credentials")
    result = gate(evaluate(evidence, catalog), 2)
    assert result["status"] == "FAIL"
    assert "RESTORE_STATE_DOMAIN_CONTAMINATION" in result["reasons"]


# Seven exact review inputs, joined to the original package by canonical JSON hash.
# The review replay script is not imported and cannot select an archived oracle.
REVIEW_CASES = [
    (
        "R1_POST_ONLY_RELABELLING",
        3,
        "FAIL",
        "0:SANDBOX_NETWORK_RESOURCE_LEAK",
        "1048073208a4b26913e5516f5c3b284863bc9e2b5bd23db9ac1f2d7f59181fad",
    ),
    (
        "R1_POST_ONLY_CROSS_ROUND",
        3,
        "FAIL",
        "1:SANDBOX_NETWORK_RESOURCE_LEAK",
        "5dcb5a2f405bb39e02c86de2f863b0506bdc84d6c92400026f7b2f4307d15066",
    ),
    (
        "R2_FOREIGN_POOL_REFERENCE_DELETED",
        3,
        "FAIL",
        "0:CROSS_SANDBOX_CONTAMINATION",
        "efac03e97399e11168142c808423b92db3b7c874f4b1222a06cd6f7c1ce2379d",
    ),
    (
        "R3_RUNTIME_EXECUTION_JOIN",
        3,
        "FAIL",
        "1:EXECUTION_JOIN_MISMATCH",
        "1bd0433810452910837831ec1d9091d1697b25edddf1ea6213d7e3d3c94c850f",
    ),
    (
        "R3_TERMINATION_EXECUTION_JOIN",
        1,
        "FAIL",
        "payload_sigkill:EXECUTION_JOIN_MISMATCH",
        "b892ce093b8bf5cd21b2424b3a64f0eaae2fc3d59afb598484951d328a83d779",
    ),
    (
        "R4_RESTORE_FOREIGN_PROCESS",
        2,
        "FAIL",
        "RESTORE_PROCESS_FOREIGN_BINDING",
        "a9cc6e5cf6e37352ed4eace5123a77150ad9abe0c4004850eb8f279f2c14cdf2",
    ),
    (
        "R4_RESTORE_UNOBSERVED_PROCESS",
        2,
        "BLOCKED",
        "RESTORE_PROCESS_OBSERVATION_MISSING",
        "38fcd30c2424702e667402dbd90f7804e505caa31941b42999cf9ef96cf61ed4",
    ),
]


def process_identity(process):
    return canonical_hash(
        [
            process[k]
            for k in ("host_boot_id", "pid", "start_ticks", "pid_namespace", "scope")
        ]
    )


def exact_review_counterexample(evidence, name):
    first, second = evidence["network_rounds"][:2]
    if name.startswith("R1_"):
        obj = deepcopy(
            next(
                r
                for r in first["active"]["resources"]
                if r["kind"] == "tap" and r["owner"] == first["owner"]
            )
        )
        cross = name == "R1_POST_ONLY_CROSS_ROUND"
        obj["key"] = "post-only:tap:birth-" + ("9002" if cross else "9001")
        if cross:
            clean = deepcopy(first["post"][-1])
            first["post"] = [
                dict(deepcopy(clean), elapsed_ms=t) for t in (250, 500, 750)
            ]
            first["post"][0]["resources"].append(deepcopy(obj))
            second["post"] = expire_samples(second["post"][-1])
            target = second["post"]
        else:
            first["post"] = expire_samples(first["post"][-1])
            first["post"][0]["resources"].append(deepcopy(obj))
            target = first["post"][1:]
        obj.update(lifetime_owner="background", owner=None, sandbox_references=[])
        for sample in target:
            sample["resources"].append(deepcopy(obj))
    elif name.startswith("R2_"):
        obj = deepcopy(first["pre"]["resources"][1])
        obj.update(
            key="foreign-shared-pool:birth-9003",
            lifetime_owner="shared",
            sandbox_references=[obj["owner"]],
            owner=None,
        )
        first["pre"]["resources"].append(obj)
    elif name == "R3_RUNTIME_EXECUTION_JOIN":
        second["runtime_network"]["execution_id"] = (
            "different-execution-with-same-owner"
        )
    elif name == "R3_TERMINATION_EXECUTION_JOIN":
        evidence["termination_cases"][1]["execution_id"] = (
            "different-execution-with-same-owner"
        )
    elif name == "R4_RESTORE_FOREIGN_PROCESS":
        evidence["snapshot"]["restores"][1]["host_processes"] = [
            process_identity(p)
            for p in evidence["termination_cases"][1]["active"]["processes"]
            if p["role"] in {"vmm", "controller", "helper"}
        ]
    else:
        assert name == "R4_RESTORE_UNOBSERVED_PROCESS"
        evidence["snapshot"]["restores"][1]["host_processes"] = [
            "not-observed-vmm",
            "not-observed-controller",
            "not-observed-helper",
        ]


@pytest.mark.parametrize(
    ("name", "gate_index", "expected", "reason", "input_sha256"),
    REVIEW_CASES,
    ids=[c[0] for c in REVIEW_CASES],
)
def test_r1_r4_exact_review_counterexample(
    inputs, name, gate_index, expected, reason, input_sha256
):
    evidence, catalog = inputs
    exact_review_counterexample(evidence, name)
    # Only the documented observation migration is projected out. The seven
    # original residual/foreign/execution contradictions remain byte-comparable.
    legacy = deepcopy(evidence)
    legacy.pop("restore_process_observations")
    if not name.startswith("R4_"):
        legacy["snapshot"]["restores"][1]["host_processes"] = [
            "boot:420:202:pidns",
            "boot:421:202:pidns",
            "boot:422:202:pidns",
        ]
    assert canonical_hash({"evidence": legacy, "catalog": catalog}) == input_sha256
    Draft202012Validator(
        {"$ref": "#/$defs/evidence", "$defs": SCHEMA["$defs"]}
    ).validate(evidence)
    result = evaluate(evidence, catalog)
    selected = gate(result, gate_index)
    print(
        "R1_R4_RESULT "
        + json.dumps(
            {
                "case": name,
                "original_input_sha256": input_sha256,
                "expected": expected,
                "actual": selected["status"],
                "aggregate": result["status"],
                "reasons": selected["reasons"],
                "expected_reason": reason,
                "input_schema_valid": True,
            },
            sort_keys=True,
        )
    )
    assert selected["status"] == expected
    assert reason in selected["reasons"]
    assert "SCHEMA_VIOLATION" not in selected["reasons"]


@pytest.mark.parametrize("phase", ["pre", "post"])
@pytest.mark.parametrize("reference_only", [False, True])
def test_r1_ownership_from_each_phase_survives_label_removal(
    inputs, phase, reference_only
):
    evidence, catalog = inputs
    first, second = evidence["network_rounds"][:2]
    obj = deepcopy(first["active"]["resources"][2])
    obj["key"] = "history-from-" + phase
    if reference_only:
        obj.update(
            owner=None, lifetime_owner="shared", sandbox_references=[first["owner"]]
        )
    if phase == "pre":
        first["pre"]["resources"].append(deepcopy(obj))
    else:
        clean = deepcopy(first["post"][-1])
        first["post"] = [dict(deepcopy(clean), elapsed_ms=t) for t in (250, 500, 750)]
        first["post"][0]["resources"].append(deepcopy(obj))
    obj.update(lifetime_owner="background", owner=None, sandbox_references=[])
    second["post"] = expire_samples(second["post"][-1])
    for sample in second["post"]:
        sample["resources"].append(deepcopy(obj))
    result = gate(evaluate(evidence, catalog), 3)
    assert result["status"] == "FAIL"
    assert "1:SANDBOX_NETWORK_RESOURCE_LEAK" in result["reasons"]


def test_r1_late_shared_lease_can_return_to_known_pool_across_rounds(inputs):
    evidence, catalog = inputs
    first = evidence["network_rounds"][0]
    pool = deepcopy(first["pre"]["resources"][0])
    pool.update(
        key="approved-shared-pool",
        lifetime_owner="shared",
        owner=None,
        sandbox_references=[],
    )
    for round_ in evidence["network_rounds"]:
        for sample in [round_["pre"], round_["active"], *round_["post"]]:
            sample["resources"].append(deepcopy(pool))
    clean = deepcopy(first["post"][-1])
    first["post"] = [dict(deepcopy(clean), elapsed_ms=t) for t in (250, 500, 750)]
    first["post"][0]["resources"][-1]["sandbox_references"] = [first["owner"]]
    assert evaluate(evidence, catalog)["status"] == "PASS"


@pytest.mark.parametrize("phase", ["active", "post"])
@pytest.mark.parametrize("mutation", ["deleted", "reassigned", "polluted"])
def test_r2_foreign_shared_lease_is_protected_in_both_phases(inputs, phase, mutation):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    obj = deepcopy(round_["pre"]["resources"][1])
    obj.update(
        key="foreign-shared-lease",
        lifetime_owner="shared",
        sandbox_references=[obj["owner"]],
        owner=None,
    )
    for sample in [round_["pre"], round_["active"], *round_["post"]]:
        sample["resources"].append(deepcopy(obj))
    samples = [round_["active"]] if phase == "active" else round_["post"]
    for sample in samples:
        if mutation == "deleted":
            sample["resources"].pop()
        elif mutation == "reassigned":
            sample["resources"][-1]["sandbox_references"] = [round_["owner"]]
        else:
            sample["resources"][-1]["fingerprint_sha256"] = "0" * 64
    result = gate(evaluate(evidence, catalog), 3)
    assert result["status"] == "FAIL"
    assert "0:CROSS_SANDBOX_CONTAMINATION" in result["reasons"]


def test_r2_unchanged_foreign_shared_lease_and_background_churn_pass(inputs):
    evidence, catalog = inputs
    round_ = evidence["network_rounds"][0]
    obj = deepcopy(round_["pre"]["resources"][1])
    obj.update(
        key="foreign-shared-lease",
        lifetime_owner="shared",
        sandbox_references=[obj["owner"]],
        owner=None,
    )
    for sample in [round_["pre"], round_["active"], *round_["post"]]:
        sample["resources"].append(deepcopy(obj))
    for sample in round_["post"]:
        sample["resources"][0]["fingerprint_sha256"] = "f" * 64
    assert evaluate(evidence, catalog)["status"] == "PASS"


@pytest.mark.parametrize("index", range(6))
@pytest.mark.parametrize("record", ["termination", "runtime"])
def test_r3_execution_join_applies_to_all_scenarios(inputs, index, record):
    evidence, catalog = inputs
    case = evidence["termination_cases"][index]
    round_ = next(r for r in evidence["network_rounds"] if r["owner"] == case["owner"])
    row = case if record == "termination" else round_["runtime_network"]
    row["execution_id"] = "single-record-contradiction"
    result = evaluate(evidence, catalog)
    assert gate(result, 1)["status"] == "FAIL"
    assert case["scenario"] + ":EXECUTION_JOIN_MISMATCH" in gate(result, 1)["reasons"]
    assert gate(result, 3)["status"] == "FAIL"
    assert (
        str(round_["cycle_index"]) + ":EXECUTION_JOIN_MISMATCH"
        in gate(result, 3)["reasons"]
    )


def test_r3_independent_scenarios_keep_distinct_executions(inputs):
    evidence, catalog = inputs
    assert len({c["execution_id"] for c in evidence["termination_cases"]}) == 6
    assert evaluate(evidence, catalog)["status"] == "PASS"


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize(
    ("mutation", "status", "reason"),
    [
        ("missing", "BLOCKED", "RESTORE_PROCESS_OBSERVATION_MISSING"),
        ("incomplete", "BLOCKED", "RESTORE_PROCESS_OBSERVATION_INCOMPLETE"),
        ("execution", "FAIL", "RESTORE_PROCESS_EXECUTION_MISMATCH"),
        ("owner", "FAIL", "RESTORE_PROCESS_OWNER_MISMATCH"),
        ("foreign", "FAIL", "RESTORE_PROCESS_FOREIGN_BINDING"),
        ("unobserved_key", "BLOCKED", "RESTORE_PROCESS_OBSERVATION_MISSING"),
        ("role_gap", "BLOCKED", "RESTORE_PROCESS_ROLE_COVERAGE_MISSING"),
        ("duplicate", "FAIL", "RESTORE_PROCESS_IDENTITY_COLLISION"),
        ("guest", "FAIL", "RESTORE_PROCESS_SCOPE_OR_ROLE_MISMATCH"),
    ],
)
def test_r4_each_restore_uses_actual_observed_processes(
    inputs, index, mutation, status, reason
):
    evidence, catalog = inputs
    restored = evidence["snapshot"]["restores"][index]
    observation = evidence["restore_process_observations"][index]
    if mutation == "missing":
        evidence["restore_process_observations"].pop(index)
    elif mutation == "incomplete":
        observation["complete"] = False
    elif mutation == "execution":
        observation["execution_id"] = "wrong-execution"
    elif mutation == "owner":
        observation["processes"][0]["owner"] = "another/instance/1"
    elif mutation == "foreign":
        restored["host_processes"][0] = process_identity(
            evidence["termination_cases"][1]["active"]["processes"][1]
        )
    elif mutation == "unobserved_key":
        # First restore is additionally bound to its existing destroy evidence.
        # Its original mismatch is a FAIL; absence at second restore is BLOCKED.
        restored["host_processes"][0] = "0" * 64
        if index == 0:
            status = "FAIL"
    elif mutation == "role_gap":
        observation["processes"] = observation["processes"][:2]
    elif mutation == "duplicate":
        observation["processes"].append(deepcopy(observation["processes"][0]))
    else:
        observation["processes"][0]["scope"] = "guest"
    result = gate(evaluate(evidence, catalog), 2)
    assert result["status"] == status
    assert reason in result["reasons"]
    assert "SCHEMA_VIOLATION" not in result["reasons"]


def test_r4_relabelled_foreign_observation_cannot_override_known_process(inputs):
    evidence, catalog = inputs
    restored = evidence["snapshot"]["restores"][1]
    observed = evidence["restore_process_observations"][1]
    rows = deepcopy(
        [
            p
            for p in evidence["termination_cases"][1]["active"]["processes"]
            if p["role"] in {"vmm", "controller", "helper"}
        ]
    )
    for p in rows:
        p["owner"] = restored["owner"]
    observed["processes"] = rows
    restored["host_processes"] = [process_identity(p) for p in rows]
    result = gate(evaluate(evidence, catalog), 2)
    assert result["status"] == "FAIL"
    assert "RESTORE_PROCESS_FOREIGN_BINDING" in result["reasons"]


def test_r4_second_restore_observation_does_not_require_another_destroy(inputs):
    evidence, catalog = inputs
    restored = evidence["snapshot"]["restores"][1]
    assert all(c["owner"] != restored["owner"] for c in evidence["termination_cases"])
    observation = evidence["restore_process_observations"][1]
    assert set(restored["host_processes"]) == {
        process_identity(p) for p in observation["processes"]
    }
    assert evaluate(evidence, catalog)["status"] == "PASS"


def test_r4_schema_requires_typed_observation_records():
    assert "restore_process_observations" in SCHEMA["$defs"]["evidence"]["required"]
    definition = SCHEMA["$defs"]["restore_process_observation"]
    assert set(definition["required"]) == {
        "owner",
        "execution_id",
        "snapshot_id",
        "complete",
        "processes",
    }
    assert definition["properties"]["processes"]["items"]["$ref"] == "#/$defs/process"
    assert definition["additionalProperties"] is False
