from __future__ import annotations

import hashlib
import shlex
import subprocess
from pathlib import Path
from typing import Any

import yaml

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.process_authority.contract import (
    validate_explicit_task_pair,
    validate_process_authority,
)


def commands_from_change_plan(plan: dict[str, Any]) -> list[str]:
    verification = plan.get("verification") or {}
    commands = verification.get("commands") or []
    if not isinstance(commands, list) or not all(
        isinstance(command, str) for command in commands
    ):
        raise ValueError("verification.commands must be a list of strings")
    return commands


def _capture_input_bytes(
    paths: dict[str, Path],
) -> tuple[dict[str, bytes], list[str]]:
    captured: dict[str, bytes] = {}
    reasons: list[str] = []
    for label, path in paths.items():
        if path.is_symlink():
            reasons.append(f"{label} must not be a symlink: {path}")
            continue
        if not path.is_file():
            reasons.append(f"{label} is missing or not a regular file: {path}")
            continue
        try:
            captured[label] = path.read_bytes()
        except OSError as exc:
            reasons.append(f"unable to read {label}: {exc}")
    return captured, reasons


def _input_sha256(captured: dict[str, bytes]) -> dict[str, str]:
    return {
        label: hashlib.sha256(payload).hexdigest()
        for label, payload in sorted(captured.items())
    }


def _blocked_result(
    *,
    reasons: list[str],
    preflight: dict[str, object],
    before: dict[str, bytes] | None = None,
    after: dict[str, bytes] | None = None,
) -> dict[str, object]:
    return {
        "status": "BLOCK",
        "preflight": preflight,
        "input_sha256_before": _input_sha256(before or {}),
        "input_sha256_after": _input_sha256(after or {}),
        "command_results": [],
        "subprocess_call_count": 0,
        "reasons": reasons,
    }


def _run_validation(
    label: str,
    validator: Any,
    *args: object,
) -> dict[str, object]:
    try:
        result = validator(*args)
    except Exception as exc:  # noqa: BLE001 - fail closed at the execution boundary
        return {
            "status": "BLOCK",
            "reasons": [f"{label} validation raised an exception: {exc}"],
        }
    if not isinstance(result, dict):
        return {
            "status": "BLOCK",
            "reasons": [f"{label} validator did not return a mapping"],
        }
    return result


def run_commands(
    *,
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
    process_authority_path: str | Path,
    policy_path: str | Path,
    autonomy_policy_path: str | Path,
    cwd: str | Path,
    timeout_seconds: int = 120,
) -> dict[str, object]:
    """Validate real process inputs and run only the captured plan commands.

    This is the module's only command execution API. It accepts no caller-created
    validation status, authorization receipt, token, command list, or executor.
    """

    paths = {
        "process_authority": Path(process_authority_path),
        "task_manifest": Path(task_manifest_path),
        "change_plan": Path(change_plan_path),
        "repo_write_policy": Path(policy_path),
        "autonomy_policy": Path(autonomy_policy_path),
    }
    before, capture_reasons = _capture_input_bytes(paths)
    preflight: dict[str, object] = {
        "process_authority_result": None,
        "manifest_result": None,
        "pair_binding_result": None,
        "change_plan_result": None,
        "replay_execution_requested": False,
        "validation_to_dispatch_inputs_equal": False,
    }
    if capture_reasons:
        return _blocked_result(
            reasons=capture_reasons,
            preflight=preflight,
            before=before,
        )

    authority_result = _run_validation(
        "process authority",
        validate_process_authority,
        paths["process_authority"],
    )
    manifest_result = _run_validation(
        "task manifest",
        validate_task_manifest,
        paths["task_manifest"],
        paths["repo_write_policy"],
        paths["autonomy_policy"],
    )
    pair_result = _run_validation(
        "explicit pair",
        validate_explicit_task_pair,
        paths["task_manifest"],
        paths["change_plan"],
    )
    plan_result = _run_validation(
        "change plan",
        validate_change_plan,
        paths["change_plan"],
    )

    preflight.update(
        {
            "process_authority_result": authority_result,
            "manifest_result": manifest_result,
            "pair_binding_result": pair_result,
            "change_plan_result": plan_result,
        }
    )
    reasons: list[str] = []
    for label, result in (
        ("process authority", authority_result),
        ("task manifest", manifest_result),
        ("explicit pair", pair_result),
        ("change plan", plan_result),
    ):
        if result.get("status") != "PASS":
            result_reasons = list(result.get("reasons") or [])
            reasons.extend(
                f"{label}: {reason}" for reason in result_reasons
            )
            if not result_reasons:
                reasons.append(f"{label}: validation did not PASS")

    after, final_capture_reasons = _capture_input_bytes(paths)
    reasons.extend(final_capture_reasons)
    changed_inputs = sorted(
        label
        for label in paths
        if before.get(label) != after.get(label)
    )
    if changed_inputs:
        reasons.append(
            "validated input changed before command dispatch: "
            + ", ".join(changed_inputs)
        )
    preflight["validation_to_dispatch_inputs_equal"] = not changed_inputs

    working_dir = Path(cwd)
    if working_dir.is_symlink() or not working_dir.is_dir():
        reasons.append(f"cwd is missing, symlinked, or not a directory: {working_dir}")
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        reasons.append("timeout_seconds must be a positive integer")
    if reasons:
        return _blocked_result(
            reasons=reasons,
            preflight=preflight,
            before=before,
            after=after,
        )

    try:
        plan = yaml.safe_load(before["change_plan"].decode("utf-8"))
        if not isinstance(plan, dict):
            raise ValueError("change plan top level must be a mapping")
        commands = commands_from_change_plan(plan)
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        return _blocked_result(
            reasons=[f"unable to extract commands from validated plan bytes: {exc}"],
            preflight=preflight,
            before=before,
            after=after,
        )

    command_results: list[dict[str, Any]] = []
    for command in commands:
        completed = subprocess.run(
            shlex.split(command),
            cwd=working_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        command_results.append(
            {
                "name": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    return {
        "status": "PASS",
        "preflight": preflight,
        "input_sha256_before": _input_sha256(before),
        "input_sha256_after": _input_sha256(after),
        "command_results": command_results,
        "subprocess_call_count": len(command_results),
        "reasons": [],
    }
