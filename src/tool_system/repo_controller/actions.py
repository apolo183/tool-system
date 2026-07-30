from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any

GhRunner = Callable[[list[str]], dict[str, Any]]


class ControllerActionError(RuntimeError):
    """Raised when a controller action cannot be executed."""


_TEST_CAPABILITY_ISSUER = object()


class RepositoryActionCapability:
    """Opaque, single-use authority for one exact repository mutation."""

    __slots__ = ("_binding", "_consumed")

    def __init__(
        self,
        *,
        issuer: object,
        repository_full_name: str,
        pr_number: int,
        action: str,
        base_branch: str,
        expected_head_sha: str,
        approval_record_sha256: str,
        runner_kind: str,
        runner: GhRunner,
    ) -> None:
        if issuer is not _TEST_CAPABILITY_ISSUER:
            raise ControllerActionError(
                "repository action capability requires a trusted issuer"
            )
        self._binding = {
            "repository_full_name": repository_full_name,
            "pr_number": pr_number,
            "action": action,
            "base_branch": base_branch,
            "expected_head_sha": expected_head_sha,
            "approval_record_sha256": approval_record_sha256,
            "runner_kind": runner_kind,
            "runner": runner,
        }
        self._consumed = False

    def _consume(
        self,
        *,
        repository_full_name: str,
        action: dict[str, Any],
        runner_kind: str,
        runner: GhRunner,
    ) -> None:
        if self._consumed:
            raise ControllerActionError(
                "repository action capability has already been consumed"
            )
        expected = {
            "repository_full_name": repository_full_name,
            "pr_number": action.get("pr_number"),
            "action": action.get("action"),
            "base_branch": action.get("base_branch"),
            "expected_head_sha": action.get("expected_head_sha"),
            "approval_record_sha256": action.get("approval_record_sha256"),
            "runner_kind": runner_kind,
            "runner": runner,
        }
        if self._binding != expected:
            raise ControllerActionError(
                "repository action capability does not match current action context"
            )
        self._consumed = True


def _issue_test_repository_action_capability(
    *,
    repository_full_name: str,
    pr_number: int,
    action: str,
    base_branch: str,
    expected_head_sha: str,
    approval_record_sha256: str,
    runner: GhRunner,
) -> RepositoryActionCapability:
    """Issue a capability only for the injected fake-runner test boundary."""

    if runner is run_gh:
        raise ControllerActionError(
            "test repository action capability cannot bind the live gh runner"
        )
    return RepositoryActionCapability(
        issuer=_TEST_CAPABILITY_ISSUER,
        repository_full_name=repository_full_name,
        pr_number=pr_number,
        action=action,
        base_branch=base_branch,
        expected_head_sha=expected_head_sha,
        approval_record_sha256=approval_record_sha256,
        runner_kind="injected_fake",
        runner=runner,
    )


def run_gh(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": args,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_action_plan(
    decision: dict[str, Any],
    pull_request: dict[str, Any],
) -> dict[str, object]:
    if decision.get("status") != "PASS":
        return {"status": "BLOCK", "actions": [], "reasons": decision.get("reasons", [])}
    if pull_request.get("draft") is True:
        return {"status": "BLOCK", "actions": [], "reasons": ["pull request must not be draft before action planning"]}

    repository_full_name = pull_request.get("repository")
    pr_number = pull_request.get("number")
    base_branch = pull_request.get("base")
    head_sha = pull_request.get("head_sha")
    approval_record_sha256 = decision.get("approval_record_sha256")
    if not repository_full_name:
        return {
            "status": "BLOCK",
            "actions": [],
            "reasons": ["pull request repository is required"],
        }
    if not pr_number:
        return {"status": "BLOCK", "actions": [], "reasons": ["pull request number is required"]}
    if not base_branch:
        return {
            "status": "BLOCK",
            "actions": [],
            "reasons": ["pull request base is required"],
        }
    if not head_sha:
        return {"status": "BLOCK", "actions": [], "reasons": ["pull request head_sha is required"]}
    if not approval_record_sha256:
        return {
            "status": "BLOCK",
            "actions": [],
            "reasons": ["approval record SHA-256 is required"],
        }

    actions = [
        {
            "action": "pr_squash",
            "repository_full_name": repository_full_name,
            "pr_number": pr_number,
            "base_branch": base_branch,
            "expected_head_sha": head_sha,
            "approval_record_sha256": approval_record_sha256,
            "merge_method": decision.get("merge_method", "squash"),
        }
    ]
    return {"status": "PASS", "actions": actions, "reasons": []}


def _command_for_action(repository_full_name: str, action: dict[str, Any]) -> list[str]:
    action_name = action.get("action")
    pr_number = str(action.get("pr_number"))
    if action_name == "pr_squash":
        command = ["pr", "merge", pr_number, "--repo", repository_full_name, "--squash"]
        expected_head_sha = action.get("expected_head_sha")
        if expected_head_sha:
            command.extend(["--match-head-commit", str(expected_head_sha)])
        return command
    raise ControllerActionError(f"unsupported controller action: {action_name}")


def execute_action_plan(
    repository_full_name: str,
    plan: dict[str, Any],
    runner: GhRunner = run_gh,
    dry_run: bool = True,
    capability: RepositoryActionCapability | None = None,
    runner_kind: str = "live_gh",
) -> dict[str, object]:
    if plan.get("status") != "PASS":
        return {"status": "BLOCK", "results": [], "reasons": plan.get("reasons", [])}

    results: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        command = _command_for_action(repository_full_name, action)
        if dry_run:
            results.append({"action": action, "command": command, "exit_code": 0, "dry_run": True})
            continue
        if capability is None:
            return {
                "status": "BLOCK",
                "results": results,
                "reasons": [
                    "repository action capability is required before mutation"
                ],
            }
        try:
            capability._consume(
                repository_full_name=repository_full_name,
                action=action,
                runner_kind=runner_kind,
                runner=runner,
            )
        except ControllerActionError as exc:
            return {
                "status": "BLOCK",
                "results": results,
                "reasons": [str(exc)],
            }
        result = runner(command)
        result = {"action": action, "command": command, **result, "dry_run": False}
        results.append(result)
        if result.get("exit_code") != 0:
            return {
                "status": "BLOCK",
                "results": results,
                "reasons": [str(result.get("stderr") or result.get("stdout") or "controller action failed")],
            }
    return {"status": "PASS", "results": results, "reasons": []}
