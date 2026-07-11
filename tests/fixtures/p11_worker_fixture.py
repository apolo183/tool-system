from __future__ import annotations

import json
import os


def _import_is_blocked(module_name: str) -> bool:
    try:
        __import__(module_name)
    except PermissionError:
        return True
    return False


def _outside_read_is_blocked() -> bool:
    try:
        with open("/etc/passwd", encoding="utf-8") as handle:
            handle.read(1)
    except PermissionError:
        return True
    return False


with open("fixture-output.txt", "w", encoding="utf-8") as handle:
    handle.write("fixture-only\n")

secret_markers = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH", "COOKIE")
environment_names = sorted(os.environ)
record = {
    "mode": "p11_fixture_only",
    "cwd_matches_workspace": os.getcwd() == os.environ.get("TOOL_SYSTEM_WORKSPACE"),
    "network_mode": os.environ.get("TOOL_SYSTEM_NETWORK"),
    "socket_import_blocked": _import_is_blocked("socket"),
    "subprocess_import_blocked": _import_is_blocked("subprocess"),
    "outside_read_blocked": _outside_read_is_blocked(),
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
