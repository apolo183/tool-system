from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.repo_controller.main_ci import observe_main_ci

EXIT_SUCCESS_STATUSES = {"PASS", "UNAVAILABLE"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe post-merge main CI for a commit.")
    parser.add_argument("repository_full_name")
    parser.add_argument("commit_sha")
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/main_ci_observation.jsonl"))
    args = parser.parse_args()

    output = observe_main_ci(
        repository_full_name=args.repository_full_name,
        commit_sha=args.commit_sha,
        audit_path=args.audit_path,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] in EXIT_SUCCESS_STATUSES else 1


if __name__ == "__main__":
    raise SystemExit(main())
