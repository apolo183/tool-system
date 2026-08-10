from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.runner.task_graph_runner import run_task_graph_pipeline
from tool_system.runner.task_runner import (
    run_batch_file,
    run_subscription_public_entry_context_compilation,
    run_subscription_public_entry_execution,
    run_task_pipeline,
)
from tool_system.worker_adapter import CodexCLIAdapterConfig


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--process-authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
    )
    parser.add_argument(
        "--active-gates",
        type=Path,
        help="Legacy replay-only pair index; never authorizes command execution.",
    )
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--autonomy-policy", type=Path, default=Path("policy/autonomy_policy.yaml"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--skip-commands", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool-system", description="Run tool-system local automation gates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run one explicit manifest/change-plan pair or a non-executing legacy replay.",
    )
    run_parser.add_argument("task_manifest", type=Path)
    run_parser.add_argument(
        "--change-plan",
        type=Path,
        help="Required for current execution; omission is allowed only for legacy replay.",
    )
    run_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_runner_audit.jsonl"))
    _add_common_options(run_parser)

    develop_parser = subparsers.add_parser(
        "develop",
        help="Validate exact manifest-bound read authority and compile one repository context without worker execution.",
    )
    develop_parser.add_argument("task_manifest", type=Path)
    develop_parser.add_argument("--change-plan", type=Path, required=True)
    develop_parser.add_argument("--repository-root", type=Path, required=True)
    develop_parser.add_argument("--expected-head", required=True)
    develop_parser.add_argument(
        "--blueprint-path",
        default="blueprint/tool_system_v0.yaml",
    )
    develop_parser.add_argument(
        "--module-registry-path",
        default="config/module_registry_v1.yaml",
    )
    develop_parser.add_argument("--milestone", action="append", required=True)
    develop_parser.add_argument("--acceptance", action="append", required=True)
    develop_parser.add_argument("--governance-path", action="append", required=True)
    develop_parser.add_argument("--query-term", action="append", required=True)
    develop_parser.add_argument("--seed-path", action="append", default=[])
    develop_parser.add_argument(
        "--repository-read-authorized",
        "--isolated-fixture-repository",
        dest="repository_read_authorized",
        action="store_true",
        required=True,
        help=(
            "Request the exact manifest-bound read-only repository context; "
            "the flag alone grants no authority."
        ),
    )
    develop_parser.add_argument(
        "--process-authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
    )
    develop_parser.add_argument(
        "--policy",
        type=Path,
        default=Path("policy/repo_write_policy.yaml"),
    )
    develop_parser.add_argument(
        "--autonomy-policy",
        type=Path,
        default=Path("policy/autonomy_policy.yaml"),
    )

    execute_parser = subparsers.add_parser(
        "develop-execute",
        help=(
            "Run one exact manifest-bound subscription development workflow "
            "in an isolated local workspace."
        ),
    )
    execute_parser.add_argument("task_manifest", type=Path)
    execute_parser.add_argument("--change-plan", type=Path, required=True)
    execute_parser.add_argument("--repository-root", type=Path, required=True)
    execute_parser.add_argument("--workspace-root", type=Path, required=True)
    execute_parser.add_argument("--durable-state", type=Path, required=True)
    execute_parser.add_argument("--expected-head", required=True)
    execute_parser.add_argument("--expected-tree", required=True)
    execute_parser.add_argument(
        "--blueprint-path",
        default="blueprint/tool_system_v0.yaml",
    )
    execute_parser.add_argument(
        "--module-registry-path",
        default="config/module_registry_v1.yaml",
    )
    execute_parser.add_argument("--milestone", action="append", required=True)
    execute_parser.add_argument("--acceptance", action="append", required=True)
    execute_parser.add_argument(
        "--governance-path",
        action="append",
        required=True,
    )
    execute_parser.add_argument("--query-term", action="append", required=True)
    execute_parser.add_argument("--seed-path", action="append", default=[])
    execute_parser.add_argument("--codex-executable", required=True)
    execute_parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=120,
    )
    execute_parser.add_argument(
        "--codex-termination-grace-seconds",
        type=int,
        default=2,
    )
    execute_parser.add_argument(
        "--codex-max-prompt-bytes",
        type=int,
        default=1_048_576,
    )
    execute_parser.add_argument(
        "--codex-max-output-bytes",
        type=int,
        default=1_048_576,
    )
    for option, destination in (
        ("--repository-read-authorized", "repository_read_authorized"),
        (
            "--subscription-worker-execution-authorized",
            "worker_execution_authorized",
        ),
        (
            "--validation-execution-authorized",
            "validation_execution_authorized",
        ),
        (
            "--subscription-data-transfer-authorized",
            "subscription_data_transfer_authorized",
        ),
        ("--local-git-write-authorized", "local_git_write_authorized"),
    ):
        execute_parser.add_argument(
            option,
            dest=destination,
            action="store_true",
            required=True,
            help="Explicit request only; the exact manifest binding remains authoritative.",
        )
    execute_parser.add_argument(
        "--process-authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
    )
    execute_parser.add_argument(
        "--policy",
        type=Path,
        default=Path("policy/repo_write_policy.yaml"),
    )
    execute_parser.add_argument(
        "--autonomy-policy",
        type=Path,
        default=Path("policy/autonomy_policy.yaml"),
    )

    batch_parser = subparsers.add_parser("batch", help="Run multiple task manifest and change-plan pairs.")
    batch_parser.add_argument("batch", type=Path)
    batch_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/batch_runner_audit.jsonl"))
    _add_common_options(batch_parser)

    graph_parser = subparsers.add_parser("graph", help="Run a task graph through the compiled batch runner.")
    graph_parser.add_argument("graph", type=Path)
    graph_parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    graph_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_graph_runner_audit.jsonl"))
    _add_common_options(graph_parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        output = run_task_pipeline(
            task_manifest_path=args.task_manifest,
            change_plan_path=args.change_plan,
            process_authority_path=args.process_authority,
            active_gates_path=args.active_gates,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
            cwd=args.cwd,
            audit_path=args.audit_path,
            execute_commands=not args.skip_commands,
        )
    elif args.command == "develop":
        output = run_subscription_public_entry_context_compilation(
            task_manifest_path=args.task_manifest,
            change_plan_path=args.change_plan,
            repository_root=args.repository_root,
            expected_head=args.expected_head,
            blueprint_path=args.blueprint_path,
            module_registry_path=args.module_registry_path,
            milestone_ids=args.milestone,
            acceptance_requirements=args.acceptance,
            governance_paths=args.governance_path,
            query_terms=args.query_term,
            seed_paths=args.seed_path,
            repository_read_authorized=args.repository_read_authorized,
            process_authority_path=args.process_authority,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
        )
    elif args.command == "develop-execute":
        output = run_subscription_public_entry_execution(
            task_manifest_path=args.task_manifest,
            change_plan_path=args.change_plan,
            repository_root=args.repository_root,
            workspace_root=args.workspace_root,
            durable_state_path=args.durable_state,
            expected_head=args.expected_head,
            expected_tree=args.expected_tree,
            blueprint_path=args.blueprint_path,
            module_registry_path=args.module_registry_path,
            milestone_ids=args.milestone,
            acceptance_requirements=args.acceptance,
            governance_paths=args.governance_path,
            query_terms=args.query_term,
            seed_paths=args.seed_path,
            codex_config=CodexCLIAdapterConfig(
                executable=args.codex_executable,
                enabled=True,
                timeout_seconds=args.codex_timeout_seconds,
                termination_grace_seconds=(
                    args.codex_termination_grace_seconds
                ),
                max_prompt_bytes=args.codex_max_prompt_bytes,
                max_output_bytes=args.codex_max_output_bytes,
            ),
            repository_read_authorized=(
                args.repository_read_authorized
            ),
            worker_execution_authorized=(
                args.worker_execution_authorized
            ),
            validation_execution_authorized=(
                args.validation_execution_authorized
            ),
            subscription_data_transfer_authorized=(
                args.subscription_data_transfer_authorized
            ),
            local_git_write_authorized=(
                args.local_git_write_authorized
            ),
            process_authority_path=args.process_authority,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
        )
    elif args.command == "batch":
        output = run_batch_file(
            batch_path=args.batch,
            process_authority_path=args.process_authority,
            active_gates_path=args.active_gates,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
            cwd=args.cwd,
            audit_path=args.audit_path,
            execute_commands=not args.skip_commands,
        )
    else:
        output = run_task_graph_pipeline(
            graph_path=args.graph,
            blueprint_path=args.blueprint,
            process_authority_path=args.process_authority,
            active_gates_path=args.active_gates,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
            cwd=args.cwd,
            audit_path=args.audit_path,
            execute_commands=not args.skip_commands,
        )

    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
