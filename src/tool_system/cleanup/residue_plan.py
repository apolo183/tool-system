from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.artifact import write_jsonl_record


PROTECTED_BRANCHES = {"main", "master", "develop", "dev", "trunk"}
PROBE_PREFIXES = ("tmp", "probe", "noop", "bad", "wrong", "last", "stop")


def _branch_name(item: object) -> str | None:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("name"), str):
        return str(item["name"])
    return None


def _is_cleanup_candidate_branch(name: str) -> bool:
    if name in PROTECTED_BRANCHES:
        return False
    lowered = name.lower()
    return lowered.startswith(PROBE_PREFIXES) or "probe" in lowered or "tmp" in lowered


def build_cleanup_plan(state: dict[str, Any]) -> dict[str, object]:
    actions: list[dict[str, object]] = []
    reasons: list[str] = []

    for branch in state.get("branches", []) or []:
        name = _branch_name(branch)
        if name is None:
            reasons.append("branch entries must be strings or mappings with name")
            continue
        if _is_cleanup_candidate_branch(name):
            actions.append({
                "action": "delete_branch",
                "target": name,
                "reason": "temporary or probe branch name",
                "execute": False,
            })

    for pull_request in state.get("pull_requests", []) or []:
        if not isinstance(pull_request, dict):
            reasons.append("pull_requests entries must be mappings")
            continue
        state_value = pull_request.get("state")
        branch = pull_request.get("head") or pull_request.get("branch")
        if state_value == "closed" and isinstance(branch, str) and _is_cleanup_candidate_branch(branch):
            actions.append({
                "action": "delete_branch",
                "target": branch,
                "reason": "closed pull request probe branch",
                "execute": False,
            })

    for artifact in state.get("artifacts", []) or []:
        if isinstance(artifact, str) and (artifact.endswith(".tmp") or "/tmp" in artifact or artifact.startswith("tmp")):
            actions.append({
                "action": "remove_artifact",
                "target": artifact,
                "reason": "temporary artifact path",
                "execute": False,
            })

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_cleanup_plan",
        "actions": actions,
        "action_count": len(actions),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "execute": False,
        "reasons": reasons,
    }


def build_cleanup_plan_file(
    state_path: str | Path,
    audit_path: str | Path | None = None,
) -> dict[str, object]:
    state = load_yaml_file(state_path)
    result = build_cleanup_plan(state)
    output = {**result, "state_path": str(state_path)}
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output
