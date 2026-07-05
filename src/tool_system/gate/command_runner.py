from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any


def run_commands(
    commands: list[str],
    cwd: str | Path | None = None,
    timeout_seconds: int = 120,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    working_dir = Path(cwd) if cwd is not None else None

    for command in commands:
        completed = subprocess.run(
            shlex.split(command),
            cwd=working_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        results.append(
            {
                "name": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    return results


def commands_from_change_plan(plan: dict[str, Any]) -> list[str]:
    verification = plan.get("verification") or {}
    commands = verification.get("commands") or []
    if not isinstance(commands, list) or not all(isinstance(command, str) for command in commands):
        raise ValueError("verification.commands must be a list of strings")
    return commands
