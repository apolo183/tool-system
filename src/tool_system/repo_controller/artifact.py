from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_jsonl_record(path: str | Path, record: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return output_path


def build_controller_record(
    repository_full_name: str,
    pr_number: int,
    evaluation: dict[str, Any],
    action_plan: dict[str, Any],
    action_result: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    decision = evaluation.get("decision", {})
    snapshot = evaluation.get("snapshot", {})
    pull_request = snapshot.get("pull_request", {})
    rollback_reference = snapshot.get("rollback", {})
    return {
        "repository_full_name": repository_full_name,
        "pr_number": pr_number,
        "head_sha": pull_request.get("head_sha"),
        "decision": decision,
        "action_plan": action_plan,
        "action_result": action_result,
        "rollback": rollback_reference,
        "dry_run": dry_run,
    }
