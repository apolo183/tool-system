from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "p15c-read-only-benchmark.yml"
TASK_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_hosted_benchmark_bridge_v1.yaml"
)
CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_hosted_benchmark_bridge_v1.yaml"
)
REPORT = ROOT / "docs" / "reports" / "p15c_hosted_benchmark_bridge.md"
EXPECTED_BASE = "432ab42b56e45a4fc469301cef17b7c35324e0f8"
ACTIVATION_ID = "c5336d4bd331a747c00547f7b7d99558"
EXPECTED_SCOPE = {
    ".github/workflows/p15c-read-only-benchmark.yml",
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/p15c_hosted_benchmark_bridge.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_hosted_benchmark_bridge_v1.yaml",
    "examples/task_manifests/tool_system_p15c_hosted_benchmark_bridge_v1.yaml",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "src/tool_system/ai_worker/p15c_hosted.py",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_entry.py",
    "tests/test_ai_worker_p15c_hosted.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_hosted_benchmark_workflow.py",
    "tests/test_repo_manifest.py",
}


def _load(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _workflow() -> tuple[str, dict[str, object]]:
    text = WORKFLOW.read_text(encoding="utf-8")
    value = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(value, dict)
    return text, value


def test_workflow_is_one_exact_non_replayable_main_push() -> None:
    text, workflow = _workflow()
    triggers = workflow["on"]
    assert isinstance(triggers, dict)
    assert triggers == {"push": {"branches": ["main"]}}
    assert "pull_request_target" not in text
    assert "workflow_dispatch" not in text
    assert "repository_dispatch" not in text
    assert "schedule:" not in text

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert set(jobs) == {"execute-once"}
    job = jobs["execute-once"]
    assert isinstance(job, dict)
    condition = str(job["if"])
    assert "github.run_attempt == 1" in condition
    assert f"github.event.before == '{EXPECTED_BASE}'" in condition
    assert "github.event.deleted == false" in condition
    assert "p15c: add hosted benchmark bridge (#175)" in condition
    assert f"P15C-ACTIVATION-ID: {ACTIVATION_ID}" in condition
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "p15c-read-only-benchmark-v1",
        "cancel-in-progress": "false",
    }


def test_workflow_uses_only_existing_provider_secrets_and_private_bundle() -> None:
    text, workflow = _workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    job = jobs["execute-once"]
    assert isinstance(job, dict)
    assert job["env"] == {
        "P15C_PRIVATE_BUNDLE_B64": "${{ secrets.P15C_PRIVATE_BUNDLE_B64 }}",
        "P15C_DEEPSEEK_API_KEY": "${{ secrets.DEEPSEEK_API_KEY }}",
        "P15C_OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}",
        "P15C_PRIVATE_ROOT": "${{ runner.temp }}/p15c-private",
        "P15C_PUBLIC_ROOT": "${{ runner.temp }}/p15c-public",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "${{ github.workspace }}/src:${{ runner.temp }}/p15c-deps",
    }
    assert "QWEN" not in text.upper()
    assert "GLM" not in text.upper()
    assert "GH_PAT" not in text.upper()
    assert "PERSONAL_ACCESS_TOKEN" not in text.upper()
    assert "repository:" not in text
    assert "api_key =" not in text.lower()


def test_workflow_materializes_then_executes_once_and_uploads_only_receipts() -> None:
    text, workflow = _workflow()
    assert text.count("uses: actions/checkout@") == 1
    assert "ref: ${{ github.sha }}" in text
    assert "persist-credentials: false" in text
    assert "pip install --target \"$RUNNER_TEMP/p15c-deps\"" in text
    assert "pip install -e" not in text
    assert "python -m tool_system.ai_worker.p15c_hosted" in text
    assert "python -m tool_system.ai_worker.p15c_entry" in text
    assert "--execute" in text
    assert "--preflight" not in text
    assert text.index("p15c_hosted") < text.index("p15c_entry")
    assert "path: ${{ runner.temp }}/p15c-public/*.json" in text
    assert "if: always()" in text
    assert "p15c-private/*.json" not in text
    assert "usage.sqlite3" not in text.split("Upload redacted public receipts", 1)[1]

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    job = jobs["execute-once"]
    assert isinstance(job, dict)
    assert job["timeout-minutes"] == "20"


def test_frozen_scope_and_public_records_stay_project_neutral() -> None:
    task = _load(TASK_MANIFEST)
    plan = _load(CHANGE_PLAN)
    assert set(task["scope"]["in_scope"]) == EXPECTED_SCOPE  # type: ignore[index]
    assert set(task["allowed_files"]) == EXPECTED_SCOPE
    assert set(plan["changed_files"]) == EXPECTED_SCOPE
    assert task["scope"]["out_of_scope"]  # type: ignore[index]

    public_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            WORKFLOW,
            ROOT / "src" / "tool_system" / "ai_worker" / "p15c_hosted.py",
            REPORT,
        )
        if path.exists()
    ).lower()
    project_token = "finance" + "-us"
    assert project_token not in public_sources
    assert "example-owner/example-repository" not in public_sources
