from __future__ import annotations

from typing import Any


def evaluate_command_results(results: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not results:
        return False, ["command results must be non-empty"]

    for index, result in enumerate(results):
        name = result.get("name") or f"command[{index}]"
        exit_code = result.get("exit_code")
        if exit_code != 0:
            reasons.append(f"{name} exited with {exit_code}")
    return not reasons, reasons


def build_gate_decision(
    plan_ok: bool,
    plan_reasons: list[str],
    command_results: list[dict[str, Any]],
) -> dict[str, object]:
    commands_ok, command_reasons = evaluate_command_results(command_results)
    reasons = plan_reasons + command_reasons
    return {
        "status": "PASS" if plan_ok and commands_ok else "BLOCK",
        "reasons": reasons,
    }
