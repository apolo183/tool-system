from __future__ import annotations

from pathlib import Path

import yaml

from tool_system.cli.validate_active_gates import validate


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "examples" / "active_gates.yaml"


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _manifest(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "task_type": "code_add",
        "target_repo": "apolo183/tool-system",
        "target_branch": f"{task_id}-branch",
        "phase": "P2_PATCH_AND_TEST_GATE",
        "approved_blueprint_refs": [
            {
                "repo": "apolo183/tool-system",
                "path": "blueprint/tool_system_v0.yaml",
                "section_or_key": "milestones.P2_PATCH_AND_TEST_GATE",
            }
        ],
        "scope": {
            "summary": f"Validate active gate pairing for {task_id}.",
            "in_scope": ["tests/fixture.py"],
            "out_of_scope": ["runtime execution"],
        },
        "evidence": [
            {
                "repo": "apolo183/tool-system",
                "path": "blueprint/tool_system_v0.yaml",
                "why_relevant": "Defines the local fixture phase.",
            }
        ],
        "allowed_files": ["tests/fixture.py"],
        "forbidden_files": ["finance/**"],
        "write_mode": "pull_request",
        "verification": {
            "commands": ["python -m pytest -q tests/fixture.py"],
            "pass_conditions": ["pytest exits 0"],
        },
        "rollback": {"method": "git_revert", "reference": "fixture commit"},
        "approval": {"required": True, "approved_by": "test"},
    }


def _plan(plan_id: str, manifest_path: Path) -> dict[str, object]:
    return {
        "plan_id": plan_id,
        "target_repo": "apolo183/tool-system",
        "task_manifest": manifest_path.as_posix(),
        "changed_files": ["tests/fixture.py"],
        "verification": {
            "commands": ["python -m pytest -q tests/fixture.py"]
        },
        "rollback": {"method": "git_revert", "reference": "fixture commit"},
    }


def _pair(tmp_path: Path, name: str) -> tuple[Path, Path]:
    manifest_path = tmp_path / "manifests" / f"{name}.yaml"
    plan_path = tmp_path / "plans" / f"{name}.yaml"
    _write_yaml(manifest_path, _manifest(f"fixture-{name}"))
    _write_yaml(plan_path, _plan(f"fixture-{name}-plan", manifest_path))
    return manifest_path, plan_path


def _index(
    tmp_path: Path,
    manifests: list[Path],
    plans: list[Path],
    *,
    alignment_gate: dict[str, object] | None = None,
) -> Path:
    index_path = tmp_path / "active_gates.yaml"
    _write_yaml(
        index_path,
        {
            "alignment_gate": alignment_gate or {"enabled": False},
            "task_manifests": [path.as_posix() for path in manifests],
            "change_plans": [path.as_posix() for path in plans],
        },
    )
    return index_path


def test_active_gate_index_validates() -> None:
    result = validate(INDEX_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_active_gate_blocks_duplicate_manifest_path(tmp_path: Path) -> None:
    manifest, plan = _pair(tmp_path, "duplicate-manifest")
    result = validate(_index(tmp_path, [manifest, manifest], [plan]))

    assert result["status"] == "BLOCK"
    assert f"duplicate task manifest path: {manifest}" in result["reasons"]


def test_active_gate_blocks_duplicate_plan_path(tmp_path: Path) -> None:
    manifest, plan = _pair(tmp_path, "duplicate-plan")
    result = validate(_index(tmp_path, [manifest], [plan, plan]))

    assert result["status"] == "BLOCK"
    assert f"duplicate change plan path: {plan}" in result["reasons"]


def test_active_gate_blocks_plan_for_unregistered_manifest(tmp_path: Path) -> None:
    registered_manifest, _ = _pair(tmp_path, "registered")
    unregistered_manifest, unregistered_plan = _pair(tmp_path, "unregistered")
    result = validate(
        _index(tmp_path, [registered_manifest], [unregistered_plan])
    )

    assert result["status"] == "BLOCK"
    assert (
        "change plan references unregistered task manifest: "
        f"{unregistered_plan} -> {unregistered_manifest}"
    ) in result["reasons"]


def test_active_gate_blocks_registered_manifest_without_plan(tmp_path: Path) -> None:
    first_manifest, first_plan = _pair(tmp_path, "paired")
    unpaired_manifest, _ = _pair(tmp_path, "unpaired")
    result = validate(
        _index(tmp_path, [first_manifest, unpaired_manifest], [first_plan])
    )

    assert result["status"] == "BLOCK"
    assert (
        f"registered task manifest has no change plan: {unpaired_manifest}"
        in result["reasons"]
    )


def test_active_gate_blocks_two_plans_for_one_manifest(tmp_path: Path) -> None:
    manifest, first_plan = _pair(tmp_path, "shared")
    second_plan = tmp_path / "plans" / "shared-second.yaml"
    _write_yaml(second_plan, _plan("shared-second-plan", manifest))
    result = validate(_index(tmp_path, [manifest], [first_plan, second_plan]))

    assert result["status"] == "BLOCK"
    assert (
        f"registered task manifest has multiple change plans: {manifest}"
        in result["reasons"]
    )


def test_active_gate_blocks_empty_manifest_list(tmp_path: Path) -> None:
    _, plan = _pair(tmp_path, "empty-manifests")
    result = validate(_index(tmp_path, [], [plan]))

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["task_manifests must be a non-empty list"]


def test_active_gate_blocks_empty_plan_list(tmp_path: Path) -> None:
    manifest, _ = _pair(tmp_path, "empty-plans")
    result = validate(_index(tmp_path, [manifest], []))

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["change_plans must be a non-empty list"]


def test_active_gate_blocks_blank_manifest_path_without_exception(
    tmp_path: Path,
) -> None:
    _, plan = _pair(tmp_path, "blank-manifest")
    index_path = tmp_path / "active_gates.yaml"
    _write_yaml(
        index_path,
        {
            "alignment_gate": {"enabled": False},
            "task_manifests": ["   "],
            "change_plans": [plan.as_posix()],
        },
    )

    result = validate(index_path)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "task_manifests entries must be non-empty strings"
    ]


def test_active_gate_blocks_blank_plan_path_without_exception(
    tmp_path: Path,
) -> None:
    manifest, _ = _pair(tmp_path, "blank-plan")
    index_path = tmp_path / "active_gates.yaml"
    _write_yaml(
        index_path,
        {
            "alignment_gate": {"enabled": False},
            "task_manifests": [manifest.as_posix()],
            "change_plans": [""],
        },
    )

    result = validate(index_path)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "change_plans entries must be non-empty strings"
    ]


def test_active_gate_pairing_is_independent_of_list_order(tmp_path: Path) -> None:
    first_manifest, first_plan = _pair(tmp_path, "first")
    second_manifest, second_plan = _pair(tmp_path, "second")
    result = validate(
        _index(
            tmp_path,
            [second_manifest, first_manifest],
            [first_plan, second_plan],
        )
    )

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_active_gate_preserves_policy_validation(tmp_path: Path) -> None:
    manifest, plan = _pair(tmp_path, "policy")
    manifest_value = _manifest("fixture-policy")
    manifest_value["allowed_files"] = ["finance/secret.py"]
    _write_yaml(manifest, manifest_value)
    plan_value = _plan("fixture-policy-plan", manifest)
    plan_value["changed_files"] = ["finance/secret.py"]
    _write_yaml(plan, plan_value)

    result = validate(_index(tmp_path, [manifest], [plan]))

    assert result["status"] == "BLOCK"
    assert "blocked path: finance/secret.py" in result["reasons"]


def test_active_gate_preserves_alignment_validation(tmp_path: Path) -> None:
    manifest, plan = _pair(tmp_path, "alignment")
    result = validate(
        _index(
            tmp_path,
            [manifest],
            [plan],
            alignment_gate={
                "enabled": True,
                "task_manifest_marker": manifest.as_posix(),
                "change_plan_marker": plan.as_posix(),
            },
        )
    )

    assert result["status"] == "BLOCK"
    assert any("must define alignment" in reason for reason in result["reasons"])
