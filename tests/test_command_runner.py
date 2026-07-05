from __future__ import annotations

import sys

from tool_system.gate.command_runner import commands_from_change_plan, run_commands
from tool_system.gate.test_gate import build_gate_decision


def test_run_commands_captures_success() -> None:
    results = run_commands([f"{sys.executable} -c 'print(42)'"])

    assert results[0]["exit_code"] == 0
    assert results[0]["stdout"].strip() == "42"


def test_run_commands_captures_failure() -> None:
    results = run_commands([f"{sys.executable} -c 'import sys; sys.exit(3)'"])

    assert results[0]["exit_code"] == 3


def test_commands_from_change_plan_requires_list_of_strings() -> None:
    plan = {"verification": {"commands": ["python -V"]}}

    assert commands_from_change_plan(plan) == ["python -V"]


def test_gate_decision_blocks_failed_command_result() -> None:
    results = run_commands([f"{sys.executable} -c 'import sys; sys.exit(4)'"])

    decision = build_gate_decision(plan_ok=True, plan_reasons=[], command_results=results)

    assert decision["status"] == "BLOCK"
    assert decision["reasons"]
