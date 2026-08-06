from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "examples/operator_config/tool_system_settings.example.toml"
CREDENTIALS = ROOT / "examples/operator_config/tool_system_credentials.example.toml"


def test_public_templates_are_disabled_empty_and_project_neutral() -> None:
    settings = tomllib.loads(SETTINGS.read_text(encoding="utf-8"))
    credentials = tomllib.loads(CREDENTIALS.read_text(encoding="utf-8"))
    p15c = settings["p15c"]

    assert p15c["schema_version"] == 4
    assert p15c["enabled"] is False
    assert p15c["total_budget_micro_usd"] == 0
    assert p15c["cny_to_micro_usd_ceiling"] == 1_000_000
    assert p15c["transport_mode"] == "direct_tls"
    assert p15c["proxy_host"] == ""
    assert p15c["proxy_port"] == 0
    assert p15c["provider_priority"] == []
    assert p15c["allowed_case_ids"] == ["deterministic-corpus"]
    assert p15c["max_provider_invocations"] == 3
    assert set(p15c["provider_model"].values()) == {""}
    assert set(p15c["provider_enabled"].values()) == {False}
    assert set(p15c["provider_transfer_enabled"].values()) == {False}
    assert set(p15c["provider_budget_micro_usd"].values()) == {0}
    assert p15c["private_repository_transfer_enabled"] is False
    assert "expected_target_packet_sha256" not in p15c
    assert credentials == {
        "providers": {
            "deepseek": {"api_key": ""},
            "openai": {"api_key": ""},
            "qwen": {"api_key": ""},
        }
    }
    public = (
        SETTINGS.read_text(encoding="utf-8") + CREDENTIALS.read_text(encoding="utf-8")
    ).lower()
    assert "finance" + "-us" not in public
    assert "github.com/" not in public
    assert "127.0.0.1" not in public
    assert "http_proxy =" not in public
    assert "https_proxy =" not in public


def test_hosted_workflows_do_not_reference_provider_or_private_bundle_secrets() -> None:
    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )

    for forbidden in (
        "secrets.OPENAI_API_KEY",
        "secrets.DEEPSEEK_API_KEY",
        "secrets.QWEN_API_KEY",
        "P15C_PRIVATE_BUNDLE_B64",
        "tool_system.ai_worker.p15c_entry --execute",
    ):
        assert forbidden not in workflow_text
