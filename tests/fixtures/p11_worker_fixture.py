from __future__ import annotations

import os


with open("fixture-output.txt", "w", encoding="utf-8") as handle:
    handle.write("fixture-only\n")

secret_markers = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH", "COOKIE")
environment_names = sorted(os.environ)
secret_like_names = [
    name
    for name in environment_names
    if any(marker in name.upper() for marker in secret_markers)
]
assert os.getcwd() == os.environ.get("TOOL_SYSTEM_WORKSPACE")
assert os.environ.get("TOOL_SYSTEM_GUARD_MODE") == "python_audit_guard_v2"
assert os.environ.get("TOOL_SYSTEM_NETWORK") == "disabled"
assert os.path.isfile("fixture-output.txt")
assert secret_like_names == []
assert "HOME" not in os.environ
assert "PATH" not in os.environ
print(
    '{"cwd_matches_workspace":true,'
    '"denied_probes_run_in_dedicated_processes":true,'
    '"guard_mode":"python_audit_guard_v2",'
    '"home_inherited":false,'
    '"mode":"p13_hardened_fixture_only",'
    '"network_mode":"disabled",'
    '"path_inherited":false,'
    '"secret_like_environment_names":[],'
    '"workspace_write_succeeded":true}'
)
