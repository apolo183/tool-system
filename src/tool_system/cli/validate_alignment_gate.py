from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.gate.alignment_gate import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate blueprint-alignment gate enforcement.")
    parser.add_argument("index", type=Path, default=Path("examples/active_gates.yaml"), nargs="?")
    args = parser.parse_args()

    result = validate(args.index)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
