from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.process_authority.contract import validate_process_authority


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate explicit current-task authority and canonical replay evidence."
    )
    parser.add_argument(
        "authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
        nargs="?",
    )
    args = parser.parse_args()
    result = validate_process_authority(args.authority)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
