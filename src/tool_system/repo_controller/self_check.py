from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tool_system.repo_controller.actions import run_gh
from tool_system.repo_controller.controller_run import run_controller
from tool_system.repo_controller.live_github_collector import run_gh_json


class SelfCheckContextError(RuntimeError):
    """Raised when controller self-check context cannot be resolved."""


def context_from_event_file(path: str | Path) -> dict[str, object]:
    event_path = Path(path)
    value = json.loads(event_path.read_text(encoding="utf-8"))
    repository = value.get("repository") or {}
    pull_request = value.get("pull_request") or {}
    repository_full_name = repository.get("full_name")
    pr_number = pull_request.get("number")
    if not repository_full_name:
        raise SelfCheckContextError("repository.full_name is required")
    if not isinstance(pr_number, int):
        raise SelfCheckContextError("pull_request.number is required")
    return {"repository_full_name": repository_full_name, "pr_number": pr_number}


def resolve_self_check_context(
    repository_full_name: str | None = None,
    pr_number: int | None = None,
    event_path: str | Path | None = None,
) -> dict[str, object]:
    if repository_full_name and pr_number is not None:
        return {"repository_full_name": repository_full_name, "pr_number": pr_number}

    resolved_event_path = event_path or os.environ.get("GITHUB_EVENT_PATH")
    if not resolved_event_path:
        raise SelfCheckContextError("explicit repo/pr or GITHUB_EVENT_PATH is required")
    return context_from_event_file(resolved_event_path)


def run_self_check(
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    repository_full_name: str | None = None,
    pr_number: int | None = None,
    event_path: str | Path | None = None,
    collector_runner=run_gh_json,
    action_runner=run_gh,
) -> dict[str, object]:
    context = resolve_self_check_context(
        repository_full_name=repository_full_name,
        pr_number=pr_number,
        event_path=event_path,
    )
    return run_controller(
        repository_full_name=str(context["repository_full_name"]),
        pr_number=int(context["pr_number"]),
        gate_decision=gate_decision,
        repo_policy=repo_policy,
        audit_path=audit_path,
        dry_run=True,
        collector_runner=collector_runner,
        action_runner=action_runner,
    )
