from __future__ import annotations

import json
import os


with open("fixture-output.txt", "w", encoding="utf-8") as handle:
    handle.write("fixture-only\n")

secret_markers = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH", "COOKIE")
environment_names = sorted(os.environ)
record = {
    "mode": "p13_hardened_fixture_only",
    "cwd_matches_workspace": os.getcwd() == os.environ.get("TOOL_SYSTEM_WORKSPACE"),
    "guard_mode": os.environ.get("TOOL_SYSTEM_GUARD_MODE"),
    "network_mode": os.environ.get("TOOL_SYSTEM_NETWORK"),
    "denied_probes_run_in_dedicated_processes": True,
    "workspace_write_succeeded": os.path.isfile("fixture-output.txt"),
    "secret_like_environment_names": [
        name
        for name in environment_names
        if any(marker in name.upper() for marker in secret_markers)
    ],
    "home_inherited": "HOME" in os.environ,
    "path_inherited": "PATH" in os.environ,
}
print(json.dumps(record, sort_keys=True))
