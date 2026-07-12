from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.architecture.repo_manifest import validate_repo_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate tool-system formal and retained non-authority file sets."
    )
    parser.add_argument(
        "manifest",
        type=Path,
        default=Path("REPO_MANIFEST.md"),
        nargs="?",
    )
    args = parser.parse_args()
    result = validate_repo_manifest(args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
