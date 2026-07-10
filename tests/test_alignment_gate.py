from __future__ import annotations

from pathlib import Path

from tool_system.gate.alignment_gate import validate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(path: Path, blueprint_path: Path, *, with_alignment: bool = True) -> str:
    alignment = ""
    if with_alignment:
        alignment = f"""
alignment:
  parent:
    document: {blueprint_path}
    section_or_key: milestones.P9_WORKER_ADAPTER_ORCHESTRATION
    scope: follows parent P9 milestone
  global:
    document: {blueprint_path}
    section_or_key: milestones.P9_WORKER_ADAPTER_ORCHESTRATION
    scope: follows active blueprint P9 scope
"""
    return f"""task_id: {path.stem}
task_type: docs_update
target_repo: apolo183/tool-system
target_branch: test-branch
phase: P9_WORKER_ADAPTER_ORCHESTRATION
approved_blueprint_refs:
  - repo: apolo183/tool-system
    path: {blueprint_path}
    section_or_key: milestones.P9_WORKER_ADAPTER_ORCHESTRATION
scope:
  summary: test manifest
  in_scope:
    - docs/test.md
  out_of_scope:
    - production deployment
evidence:
  - repo: apolo183/tool-system
    path: {blueprint_path}
    why_relevant: active blueprint
allowed_files:
  - docs/test.md
forbidden_files:
  - finance/**
write_mode: pull_request
verification:
  commands:
    - python -m tool_system.cli.validate_alignment_gate active_gates.yaml
rollback:
  method: git_revert
  reference: test branch
approval:
  required: true
  approved_by: test
{alignment}"""


def _plan(path: Path, manifest_path: Path, blueprint_path: Path, *, parent_document: str | None = None) -> str:
    parent = parent_document or str(manifest_path)
    return f"""plan_id: {path.stem}
target_repo: apolo183/tool-system
task_manifest: {manifest_path}
changed_files:
  - docs/test.md
alignment:
  parent:
    document: {parent}
    section_or_key: task_id
    scope: follows task manifest
  global:
    document: {blueprint_path}
    section_or_key: milestones.P9_WORKER_ADAPTER_ORCHESTRATION
    scope: follows active blueprint P9 scope
verification:
  commands:
    - python -m tool_system.cli.validate_alignment_gate active_gates.yaml
rollback:
  method: git_revert
  reference: test branch
"""


def _index(index_path: Path, manifest_path: Path, plan_path: Path) -> str:
    return f"""alignment_gate:
  enabled: true
  task_manifest_marker: {manifest_path}
  change_plan_marker: {plan_path}
task_manifests:
  - {manifest_path}
change_plans:
  - {plan_path}
"""


def test_alignment_gate_passes_parent_and_global_alignment(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint" / "tool_system_v0.yaml"
    manifest = tmp_path / "examples" / "task_manifests" / "tool_system_p9m.yaml"
    plan = tmp_path / "examples" / "change_plans" / "tool_system_p9m.yaml"
    index = tmp_path / "examples" / "active_gates.yaml"

    _write(blueprint, "phase: P9_WORKER_ADAPTER_ORCHESTRATION\n")
    _write(manifest, _manifest(manifest, blueprint))
    _write(plan, _plan(plan, manifest, blueprint))
    _write(index, _index(index, manifest, plan))

    result = validate(index)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["alignment_gate_enabled"] is True


def test_alignment_gate_blocks_missing_alignment(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint" / "tool_system_v0.yaml"
    manifest = tmp_path / "examples" / "task_manifests" / "tool_system_p9m.yaml"
    plan = tmp_path / "examples" / "change_plans" / "tool_system_p9m.yaml"
    index = tmp_path / "examples" / "active_gates.yaml"

    _write(blueprint, "phase: P9_WORKER_ADAPTER_ORCHESTRATION\n")
    _write(manifest, _manifest(manifest, blueprint, with_alignment=False))
    _write(plan, _plan(plan, manifest, blueprint))
    _write(index, _index(index, manifest, plan))

    result = validate(index)

    assert result["status"] == "BLOCK"
    assert any("must define alignment" in reason for reason in result["reasons"])


def test_alignment_gate_blocks_change_plan_parent_mismatch(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint" / "tool_system_v0.yaml"
    manifest = tmp_path / "examples" / "task_manifests" / "tool_system_p9m.yaml"
    plan = tmp_path / "examples" / "change_plans" / "tool_system_p9m.yaml"
    index = tmp_path / "examples" / "active_gates.yaml"

    _write(blueprint, "phase: P9_WORKER_ADAPTER_ORCHESTRATION\n")
    _write(manifest, _manifest(manifest, blueprint))
    _write(plan, _plan(plan, manifest, blueprint, parent_document="wrong-parent.yaml"))
    _write(index, _index(index, manifest, plan))

    result = validate(index)

    assert result["status"] == "BLOCK"
    assert any("alignment.parent.document must match task_manifest" in reason for reason in result["reasons"])
