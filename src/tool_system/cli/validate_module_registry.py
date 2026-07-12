from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.architecture.module_registry import validate_module_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the durable tool-system module registry."
    )
    parser.add_argument(
        "registry",
        type=Path,
        default=Path("config/module_registry_v1.yaml"),
        nargs="?",
    )
    args = parser.parse_args()
    result = validate_module_registry(args.registry)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
