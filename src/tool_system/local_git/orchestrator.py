from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from tool_system.development_loop import (
    DevelopmentLoopError,
    DevelopmentLoopLimits,
    FrozenDevelopmentContract,
    run_development_loop,
)
from tool_system.orchestrator import DurableOrchestratorStore, StateConflict

_SHA = re.compile(r"^[0-9a-f]{40}$")
_BRANCH = re.compile(r"^agent/[a-z0-9][a-z0-9._/-]{0,119}$")


class DurableLocalGitError(RuntimeError):
    """A frozen local-Git precondition or durable transition failed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LocalGitIdentity:
    expected_head_sha: str
    expected_tree_sha: str
    branch_name: str
    commit_message: str

    def validate(self) -> None:
        if _SHA.fullmatch(self.expected_head_sha) is None:
            raise DurableLocalGitError("INVALID_EXPECTED_HEAD")
        if _SHA.fullmatch(self.expected_tree_sha) is None:
            raise DurableLocalGitError("INVALID_EXPECTED_TREE")
        if _BRANCH.fullmatch(self.branch_name) is None or ".." in self.branch_name:
            raise DurableLocalGitError("INVALID_LOCAL_BRANCH")
        if not self.commit_message.strip() or "\n" in self.commit_message:
            raise DurableLocalGitError("INVALID_COMMIT_MESSAGE")


def _git_environment() -> dict[str, str]:
    names = (
        "PATH",
        "HOME",
        "LANG",
        "LC_ALL",
        "SYSTEMROOT",
        "WINDIR",
        "TMPDIR",
        "TEMP",
        "TMP",
    )
    return {
        **{name: os.environ[name] for name in names if name in os.environ},
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    }


def _git(root: Path, *args: str, check: bool = True) -> str:
    try:
        completed = subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=" + os.devnull,
                "-c",
                "commit.gpgSign=false",
                *args,
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
            env=_git_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurableLocalGitError("LOCAL_GIT_COMMAND_FAILED") from exc
    if check and completed.returncode:
        raise DurableLocalGitError("LOCAL_GIT_COMMAND_FAILED")
    if (
        len((completed.stdout or "").encode("utf-8")) > 1_048_576
        or len((completed.stderr or "").encode("utf-8")) > 1_048_576
    ):
        raise DurableLocalGitError("LOCAL_GIT_OUTPUT_LIMIT")
    return (completed.stdout or "").strip()


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _validate_repository(
    root: Path,
    identity: LocalGitIdentity,
    *,
    completed_branch: Mapping[str, object] | None,
    completed_commit: Mapping[str, object] | None,
) -> None:
    identity.validate()
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise DurableLocalGitError("INVALID_REPOSITORY_ROOT")
    git_dir = root / ".git"
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise DurableLocalGitError("INVALID_GIT_DIRECTORY")
    if Path(_git(root, "rev-parse", "--show-toplevel")) != root:
        raise DurableLocalGitError("REPOSITORY_ROOT_MISMATCH")
    if _git(root, "remote"):
        raise DurableLocalGitError("REMOTE_REPOSITORY_FORBIDDEN")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise DurableLocalGitError("DIRTY_WORKTREE")
    current_head = _git(root, "rev-parse", "HEAD")
    current_tree = _git(root, "rev-parse", "HEAD^{tree}")
    branch_exists = bool(
        _git(root, "show-ref", "--verify", f"refs/heads/{identity.branch_name}", check=False)
    )
    if completed_commit is not None:
        result = completed_commit.get("result")
        if not isinstance(result, Mapping) or current_head != result.get("commit") or current_tree != result.get("tree"):
            raise DurableLocalGitError("COMPLETED_COMMIT_RECEIPT_DRIFT")
        if _git(root, "branch", "--show-current") != identity.branch_name:
            raise DurableLocalGitError("COMPLETED_BRANCH_RECEIPT_DRIFT")
        return
    if completed_branch is not None:
        result = completed_branch.get("result")
        if not isinstance(result, Mapping) or result.get("branch") != identity.branch_name:
            raise DurableLocalGitError("COMPLETED_BRANCH_RECEIPT_DRIFT")
        if not branch_exists or _git(root, "branch", "--show-current") != identity.branch_name:
            raise DurableLocalGitError("COMPLETED_BRANCH_RECEIPT_DRIFT")
    elif branch_exists:
        raise DurableLocalGitError("BRANCH_ALREADY_EXISTS_WITHOUT_RECEIPT")
    if current_head != identity.expected_head_sha:
        raise DurableLocalGitError("HEAD_PRECONDITION_DRIFT")
    if current_tree != identity.expected_tree_sha:
        raise DurableLocalGitError("TREE_PRECONDITION_DRIFT")


def _validate_baseline_topology(
    root: Path,
    baseline_files: Mapping[str, object],
    scope: tuple[str, ...],
) -> None:
    scope_set = set(scope)
    if not scope_set or not set(baseline_files) <= scope_set:
        raise DurableLocalGitError("BASELINE_SCOPE_MISMATCH")
    existing: set[str] = set()
    for name in scope:
        record = _git(root, "ls-tree", "HEAD", "--", name)
        if not record:
            continue
        metadata, separator, recorded_name = record.partition("\t")
        parts = metadata.split()
        if separator != "\t" or recorded_name != name or len(parts) != 3:
            raise DurableLocalGitError("UNSAFE_BASELINE_PATH")
        mode, kind, blob_sha = parts
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise DurableLocalGitError("UNSAFE_BASELINE_PATH")
        existing.add(name)
        content = baseline_files.get(name)
        if not isinstance(content, str):
            raise DurableLocalGitError("BASELINE_SCOPE_MISMATCH")
        completed = subprocess.run(
            ["git", "hash-object", "--stdin"],
            cwd=root,
            check=False,
            input=content.encode("utf-8"),
            capture_output=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if completed.returncode or completed.stdout.decode().strip() != blob_sha:
            raise DurableLocalGitError("BASELINE_CONTENT_MISMATCH")
    if existing != set(baseline_files):
        raise DurableLocalGitError("BASELINE_SCOPE_MISMATCH")


def _changed_paths(
    baseline_files: Mapping[str, object],
    candidate_files: Mapping[str, object],
    scope: tuple[str, ...],
) -> tuple[str, ...]:
    scope_set = set(scope)
    if not set(candidate_files) <= scope_set:
        raise DurableLocalGitError("SEALED_SCOPE_MISMATCH")
    for content in candidate_files.values():
        if not isinstance(content, str):
            raise DurableLocalGitError("INVALID_CANDIDATE_CONTENT")
    changed = tuple(
        name
        for name in scope
        if (name in baseline_files) != (name in candidate_files)
        or baseline_files.get(name) != candidate_files.get(name)
    )
    if not changed:
        raise DurableLocalGitError("EMPTY_CANDIDATE_CHANGE")
    return changed


def _write_candidate(
    root: Path,
    files: Mapping[str, object],
    changed_paths: tuple[str, ...],
) -> None:
    for name in changed_paths:
        target = root / name
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise DurableLocalGitError("PATH_ESCAPE") from exc
        parent = root
        for part in Path(name).parts[:-1]:
            parent /= part
            if parent.is_symlink() or (
                parent.exists() and not parent.is_dir()
            ):
                raise DurableLocalGitError("UNSAFE_CANDIDATE_PATH")
        if target.is_symlink() or (
            target.exists() and not stat.S_ISREG(target.lstat().st_mode)
        ):
            raise DurableLocalGitError("UNSAFE_CANDIDATE_PATH")
        if name in files:
            content = files[name]
            if not isinstance(content, str):
                raise DurableLocalGitError("INVALID_CANDIDATE_CONTENT")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        else:
            if not target.exists():
                raise DurableLocalGitError("DELETE_PRECONDITION_DRIFT")
            target.unlink()


def _validated_local_repository(root: Path) -> tuple[str, str]:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise DurableLocalGitError("INVALID_SOURCE_REPOSITORY_ROOT")
    git_dir = root / ".git"
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise DurableLocalGitError("INVALID_SOURCE_GIT_DIRECTORY")
    if Path(_git(root, "rev-parse", "--show-toplevel")) != root:
        raise DurableLocalGitError("SOURCE_REPOSITORY_ROOT_MISMATCH")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise DurableLocalGitError("DIRTY_SOURCE_WORKTREE")
    return _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")


def create_isolated_local_workspace(
    *,
    source_repository_root: str | Path,
    workspace_root: str | Path,
    expected_head_sha: str,
    expected_tree_sha: str,
) -> dict[str, object]:
    """Create or identify one exact remote-free local workspace.

    The source is read locally at one clean commit. Clone checkout disables hooks,
    global/system Git configuration, prompting, signing, submodules, and every
    remote after the local object transfer. Existing workspaces are not changed;
    durable-local-Git receipt reconciliation remains authoritative for resume.
    """

    source = Path(source_repository_root).resolve(strict=True)
    raw_workspace = Path(workspace_root)
    try:
        if _SHA.fullmatch(expected_head_sha) is None:
            raise DurableLocalGitError("INVALID_EXPECTED_HEAD")
        if _SHA.fullmatch(expected_tree_sha) is None:
            raise DurableLocalGitError("INVALID_EXPECTED_TREE")
        source_head, source_tree = _validated_local_repository(source)
        if source_head != expected_head_sha:
            raise DurableLocalGitError("SOURCE_HEAD_PRECONDITION_DRIFT")
        if source_tree != expected_tree_sha:
            raise DurableLocalGitError("SOURCE_TREE_PRECONDITION_DRIFT")
        if not raw_workspace.is_absolute() or raw_workspace.name in {"", ".", ".."}:
            raise DurableLocalGitError("INVALID_WORKSPACE_ROOT")
        parent = raw_workspace.parent.resolve(strict=True)
        if raw_workspace.parent.is_symlink() or not parent.is_dir():
            raise DurableLocalGitError("INVALID_WORKSPACE_PARENT")
        parent_stat = parent.lstat()
        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise DurableLocalGitError("UNSAFE_WORKSPACE_PARENT")
        target = parent / raw_workspace.name
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_dir():
                raise DurableLocalGitError("UNSAFE_EXISTING_WORKSPACE")
            git_dir = target / ".git"
            if git_dir.is_symlink() or not git_dir.is_dir():
                raise DurableLocalGitError("UNSAFE_EXISTING_WORKSPACE")
            if _git(target, "remote"):
                raise DurableLocalGitError("REMOTE_REPOSITORY_FORBIDDEN")
            return {
                "status": "PASS",
                "workspace_state": "EXISTING",
                "workspace_created": False,
                "workspace_identity_sha256": hashlib.sha256(
                    str(target).encode("utf-8")
                ).hexdigest(),
                "source_head": source_head,
                "source_tree": source_tree,
                "remote_count": 0,
                "network_operations": 0,
            }
        with tempfile.TemporaryDirectory(
            prefix=".tool-system-workspace-",
            dir=parent,
        ) as temporary_directory:
            stage = Path(temporary_directory) / "repository"
            _git(
                parent,
                "-c",
                "protocol.file.allow=always",
                "clone",
                "--no-local",
                "--no-hardlinks",
                "--no-checkout",
                "--no-tags",
                "--",
                str(source),
                str(stage),
            )
            if _git(stage, "remote"):
                _git(stage, "remote", "remove", "origin")
            _git(stage, "checkout", "--detach", expected_head_sha)
            if _git(stage, "remote"):
                raise DurableLocalGitError("REMOTE_REPOSITORY_FORBIDDEN")
            if _git(stage, "rev-parse", "HEAD") != expected_head_sha:
                raise DurableLocalGitError("WORKSPACE_HEAD_PRECONDITION_DRIFT")
            if _git(stage, "rev-parse", "HEAD^{tree}") != expected_tree_sha:
                raise DurableLocalGitError("WORKSPACE_TREE_PRECONDITION_DRIFT")
            if _git(stage, "status", "--porcelain=v1", "--untracked-files=all"):
                raise DurableLocalGitError("DIRTY_WORKSPACE_AFTER_CLONE")
            os.replace(stage, target)
        return {
            "status": "PASS",
            "workspace_state": "CREATED",
            "workspace_created": True,
            "workspace_identity_sha256": hashlib.sha256(
                str(target).encode("utf-8")
            ).hexdigest(),
            "source_head": source_head,
            "source_tree": source_tree,
            "remote_count": 0,
            "network_operations": 0,
        }
    except (OSError, DurableLocalGitError) as exc:
        return {
            "status": "BLOCK",
            "terminal_code": (
                exc.code
                if isinstance(exc, DurableLocalGitError)
                else "WORKSPACE_CREATION_FAILED"
            ),
            "workspace_created": False,
            "remote_count": 0,
            "network_operations": 0,
        }


def run_durable_local_git(
    *,
    repository_root: str | Path,
    store: DurableOrchestratorStore,
    run_id: str,
    task_id: str,
    lease_owner: str,
    identity: LocalGitIdentity,
    contract: FrozenDevelopmentContract,
    baseline_files: Mapping[str, object],
    worker: Callable[[Mapping[str, object]], Mapping[str, object]],
    validator: Callable[[Mapping[str, str]], Mapping[str, object]],
    code_reviewer: Callable[[Mapping[str, object]], Mapping[str, object]],
    contract_reviewer: Callable[[Mapping[str, object]], Mapping[str, object]],
    limits: DevelopmentLoopLimits | None = None,
    lease_seconds: float = 60.0,
    after_effect: Callable[[str], None] | None = None,
    cancellation_requested: Callable[[], bool] | None = None,
) -> dict[str, object]:
    """Seal one P14F candidate and commit it in an isolated local repository.

    The caller owns callbacks and authority. This function rejects remotes, records
    branch/commit effects durably, and emits plans—not execution—for rollback,
    creator cleanup, and a future draft PR.
    """

    root = Path(repository_root).resolve(strict=True)
    try:
        branch_receipt = store.get_side_effect(f"{run_id}:branch")
        commit_receipt = store.get_side_effect(f"{run_id}:commit")
        completed_branch = (
            branch_receipt if branch_receipt and branch_receipt["state"] == "COMPLETED" else None
        )
        completed_commit = (
            commit_receipt if commit_receipt and commit_receipt["state"] == "COMPLETED" else None
        )
        if branch_receipt and branch_receipt["state"] != "COMPLETED":
            raise DurableLocalGitError("AMBIGUOUS_BRANCH_SIDE_EFFECT")
        if commit_receipt and commit_receipt["state"] != "COMPLETED":
            raise DurableLocalGitError("AMBIGUOUS_COMMIT_SIDE_EFFECT")
        _validate_repository(
            root,
            identity,
            completed_branch=completed_branch,
            completed_commit=completed_commit,
        )
        contract.validate()
        if completed_commit is None:
            _validate_baseline_topology(
                root,
                baseline_files,
                contract.allowed_scope,
            )
        store.create_run(run_id, blueprint_ref="P14G", manifest_ref=contract.task_digest)
        if store.get_task(run_id, task_id) is None:
            store.add_task(
                run_id,
                task_id,
                idempotency_key=f"{run_id}:{task_id}",
                expected_precondition_sha=identity.expected_head_sha,
                max_attempts=2,
                checkpoint={"phase": "FROZEN", "contract_digest": _digest(contract.__dict__)},
            )
        store.recover_expired_leases()
        task = store.claim_task(
            run_id, task_id, lease_owner=lease_owner, lease_seconds=lease_seconds
        )
        attempt = int(task["attempt"])
        if completed_commit is not None:
            store.complete_task(run_id, task_id, lease_owner=lease_owner, attempt=attempt)
            store.complete_run(run_id)
            result = completed_commit["result"]
            assert isinstance(result, Mapping)
            return {
                "status": "PASS",
                "terminal_code": "RESUMED_COMPLETED_LOCAL_COMMIT",
                "branch": identity.branch_name,
                "commit": result["commit"],
                "tree": result["tree"],
                "candidate_tree": result.get("candidate_tree"),
                "worker_call_count": int(result.get("worker_call_count", 0)),
                "total_duration_ms": int(result.get("total_duration_ms", 0)),
                "total_cost_microunits": int(
                    result.get("total_cost_microunits", 0)
                ),
                "rollback_plan": {"authorized": False, "base": identity.expected_head_sha},
                "cleanup_plan": {"authorized": False, "branch": identity.branch_name},
                "draft_pr_plan": {"authorized": False, "remote_operations": 0},
                "provider_calls": 0,
                "credential_reads": 0,
                "remote_operations": 0,
            }
        loop_result = run_development_loop(
            contract=contract,
            baseline_files=baseline_files,
            worker=worker,
            validator=validator,
            code_reviewer=code_reviewer,
            contract_reviewer=contract_reviewer,
            limits=limits,
            resume_state=task["checkpoint"].get("loop_result"),
            cancellation_requested=cancellation_requested,
        )
        store.checkpoint_task(
            run_id,
            task_id,
            lease_owner=lease_owner,
            attempt=attempt,
            checkpoint={"phase": "CANDIDATE_EVALUATED", "loop_result": loop_result},
        )
        if loop_result["status"] != "PASS" or not loop_result["terminal_candidate_sealed"]:
            store.fail_task(
                run_id,
                task_id,
                lease_owner=lease_owner,
                attempt=attempt,
                retryable=False,
                checkpoint={"phase": "LOOP_BLOCKED", "loop_result": loop_result},
            )
            return {"status": "BLOCK", "terminal_code": loop_result["terminal_code"]}

        branch_effect = store.plan_side_effect(
            run_id,
            task_id,
            effect_id=f"{run_id}:branch",
            effect_kind="local_git_branch",
            action="create",
            resource_scope="local_fixture",
            idempotency_key=f"{run_id}:branch:{identity.branch_name}",
            expected_precondition_sha=identity.expected_head_sha,
            payload={"branch": identity.branch_name},
            lease_owner=lease_owner,
            task_attempt=attempt,
        )
        if completed_branch is None:
            store.begin_side_effect(branch_effect["effect_id"], lease_owner=lease_owner, task_attempt=attempt)
            _git(root, "switch", "-c", identity.branch_name, identity.expected_head_sha)
            store.complete_side_effect(
                branch_effect["effect_id"],
                lease_owner=lease_owner,
                task_attempt=attempt,
                expected_precondition_sha=identity.expected_head_sha,
                result={"branch": identity.branch_name, "head": identity.expected_head_sha},
                event_kind="local_git_branch_created",
                event_payload={"branch": identity.branch_name},
            )
            if after_effect is not None:
                after_effect("branch")

        candidate_files = loop_result["candidate_files"]
        assert isinstance(candidate_files, Mapping)
        changed_paths = _changed_paths(
            baseline_files,
            candidate_files,
            contract.allowed_scope,
        )
        _write_candidate(root, candidate_files, changed_paths)
        _git(root, "add", "-A", "--", *changed_paths)
        staged = tuple(filter(None, _git(root, "diff", "--cached", "--name-only").splitlines()))
        if set(staged) != set(changed_paths):
            raise DurableLocalGitError("STAGED_SCOPE_MISMATCH")

        commit_effect = store.plan_side_effect(
            run_id,
            task_id,
            effect_id=f"{run_id}:commit",
            effect_kind="local_git_commit",
            action="create",
            resource_scope="local_fixture",
            idempotency_key=f"{run_id}:commit:{loop_result['candidate_tree']}",
            expected_precondition_sha=identity.expected_head_sha,
            payload={
                "branch": identity.branch_name,
                "candidate_tree": loop_result["candidate_tree"],
                "changed_paths": list(changed_paths),
            },
            lease_owner=lease_owner,
            task_attempt=attempt,
        )
        store.begin_side_effect(commit_effect["effect_id"], lease_owner=lease_owner, task_attempt=attempt)
        _git(
            root,
            "-c", "user.name=tool-system fixture",
            "-c", "user.email=fixture@tool-system.invalid",
            "commit", "-m", identity.commit_message,
        )
        commit_sha = _git(root, "rev-parse", "HEAD")
        commit_tree = _git(root, "rev-parse", "HEAD^{tree}")
        store.complete_side_effect(
            commit_effect["effect_id"],
            lease_owner=lease_owner,
            task_attempt=attempt,
            expected_precondition_sha=identity.expected_head_sha,
            result={
                "commit": commit_sha,
                "tree": commit_tree,
                "candidate_tree": loop_result["candidate_tree"],
                "worker_call_count": loop_result["worker_call_count"],
                "total_duration_ms": loop_result["total_duration_ms"],
                "total_cost_microunits": loop_result["total_cost_microunits"],
            },
            event_kind="local_git_commit_created",
            event_payload={"commit": commit_sha, "tree": commit_tree},
        )
        if after_effect is not None:
            after_effect("commit")
        store.checkpoint_task(
            run_id,
            task_id,
            lease_owner=lease_owner,
            attempt=attempt,
            checkpoint={"phase": "LOCAL_COMMIT_RECORDED", "commit": commit_sha, "tree": commit_tree, "loop_result": loop_result},
        )
        store.complete_task(run_id, task_id, lease_owner=lease_owner, attempt=attempt)
        store.complete_run(run_id)
        return {
            "status": "PASS",
            "terminal_code": "LOCAL_COMMIT_RECORDED",
            "branch": identity.branch_name,
            "commit": commit_sha,
            "tree": commit_tree,
            "candidate_tree": loop_result["candidate_tree"],
            "worker_call_count": int(loop_result["worker_call_count"]),
            "total_duration_ms": int(loop_result["total_duration_ms"]),
            "total_cost_microunits": int(
                loop_result["total_cost_microunits"]
            ),
            "rollback_plan": {"authorized": False, "action": "reset_fixture_to_base", "base": identity.expected_head_sha},
            "cleanup_plan": {"authorized": False, "action": "delete_creator_owned_fixture_branch", "branch": identity.branch_name},
            "draft_pr_plan": {"authorized": False, "remote_operations": 0},
            "provider_calls": 0,
            "credential_reads": 0,
            "remote_operations": 0,
        }
    except (DevelopmentLoopError, DurableLocalGitError, StateConflict) as exc:
        return {
            "status": "BLOCK",
            "terminal_code": (
                exc.code
                if isinstance(exc, (DevelopmentLoopError, DurableLocalGitError))
                else "DURABLE_STATE_CONFLICT"
            ),
            "provider_calls": 0,
            "credential_reads": 0,
            "remote_operations": 0,
        }
