from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_active_gates import validate


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "examples" / "active_gates.yaml"


def test_active_gate_index_validates() -> None:
    result = validate(INDEX_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
