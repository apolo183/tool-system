from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.architecture.module_registry import validate_module_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the single durable tool-system module registry. The "
            "fixed config/module_registry_v1.yaml path uses the central format "
            "as current local authority; legacy parsing is memory-only "
            "compatibility and creates no projection or second authority."
        )
    )
    parser.add_argument(
        "registry",
        type=Path,
        default=Path("config/module_registry_v1.yaml"),
        nargs="?",
    )
    parser.add_argument(
        "--require-current-authority",
        action="store_true",
        help=(
            "Block unless the input is the fixed-path central registry current "
            "authority. Central input at any other path and all legacy input "
            "remain non-authoritative compatibility results."
        ),
    )
    args = parser.parse_args()
    result = validate_module_registry(
        args.registry,
        require_current_authority=args.require_current_authority,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
