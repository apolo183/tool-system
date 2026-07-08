from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
GLOBAL_PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
README = ROOT / "README.md"
CHANGE_PLAN = ROOT / "examples" / "change_plans" / "tool_system_global_principles.yaml"


def test_global_principles_define_core_gates() -> None:
    text = GLOBAL_PRINCIPLES.read_text(encoding="utf-8")

    assert "## 2. Evidence hierarchy" in text
    assert "## 4. Drift gate" in text
    assert "## 5. Authorization gate" in text
    assert "## 7. File disposition" in text
    assert "## 10. Claims boundary" in text
    assert "writes_target_repo" not in text


def test_entrypoints_point_to_global_principles() -> None:
    readme_text = README.read_text(encoding="utf-8")
    agents_text = AGENTS.read_text(encoding="utf-8")

    assert "docs/tool_system_global_development_principles_v1.md" in readme_text
    assert "docs/tool_system_global_development_principles_v1.md" in agents_text


def test_global_principles_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
