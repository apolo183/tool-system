from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.cleanup.residue_plan import build_cleanup_plan_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a no-write cleanup plan for repository residue.")
    parser.add_argument("state", type=Path)
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/cleanup_plan_audit.jsonl"))
    args = parser.parse_args()

    output = build_cleanup_plan_file(args.state, args.audit_path)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
