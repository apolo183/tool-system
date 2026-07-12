from __future__ import annotations

import os
import subprocess
from collections import deque
from pathlib import Path, PurePosixPath


FORMAL_SECTION = "## Formal File Sets"
LEGACY_SECTION = "## Retained Non-Authority Sets"
FORMAL_COLUMNS = (
    "path",
    "role",
    "purpose",
    "owner",
    "lifecycle",
    "upstream",
    "downstream",
    "validation",
    "status",
)
LEGACY_COLUMNS = (
    "path",
    "classification",
    "authority",
    "runtime_default",
    "disposition",
    "validation",
)


def _git_environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }


def _tracked_paths(repo_root: Path) -> set[str]:
    result = subprocess.run(
        [
            "git",
            "--no-pager",
            "--no-replace-objects",
            "-c",
            "core.fsmonitor=false",
            "ls-files",
            "-z",
        ],
        cwd=repo_root,
        env=_git_environment(),
        check=False,
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise ValueError("unable to read tracked repository paths")
    paths: set[str] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if any(ord(character) < 32 or ord(character) == 127 for character in path):
            raise ValueError("tracked repository path contains a control character")
        paths.add(path)
    return paths


def _table_rows(
    text: str,
    section: str,
    columns: tuple[str, ...],
) -> tuple[list[dict[str, str]], list[str]]:
    reasons: list[str] = []
    lines = text.splitlines()
    if lines.count(section) != 1:
        return [], [f"manifest section must appear exactly once: {section}"]
    try:
        section_index = lines.index(section)
    except ValueError:
        return [], [f"missing manifest section: {section}"]
    table_lines: list[str] = []
    for line in lines[section_index + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            table_lines.append(line)
    if len(table_lines) < 3:
        return [], [f"{section} must contain a header and at least one row"]

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    header = tuple(cells(table_lines[0]))
    if header != columns:
        reasons.append(f"{section} columns must be exactly {list(columns)}")
    separator = cells(table_lines[1])
    if len(separator) != len(columns) or not all(
        value and set(value) <= {"-", ":"} for value in separator
    ):
        reasons.append(f"{section} separator row is invalid")

    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(table_lines[2:], start=1):
        values = cells(line)
        if len(values) != len(columns):
            reasons.append(f"{section} row {line_number} has the wrong column count")
            continue
        if any(not value for value in values):
            reasons.append(f"{section} row {line_number} has an empty field")
            continue
        rows.append(dict(zip(columns, values, strict=True)))
    return rows, reasons


def _safe_pattern(pattern: str) -> bool:
    if pattern.startswith(("/", "-")) or "\\" in pattern:
        return False
    parts = PurePosixPath(pattern).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def _expand_tracked_pattern(
    repo_root: Path,
    pattern: str,
    tracked: set[str],
) -> set[str]:
    if not _safe_pattern(pattern):
        raise ValueError(f"unsafe manifest path expression: {pattern}")
    return {
        path.relative_to(repo_root).as_posix()
        for path in repo_root.glob(pattern)
        if path.is_file()
        and path.relative_to(repo_root).as_posix() in tracked
    }


def _validate_path_sets(
    repo_root: Path,
    tracked: set[str],
    rows: list[dict[str, str]],
    label: str,
    reasons: list[str],
) -> set[str]:
    claimed: set[str] = set()
    seen_patterns: set[str] = set()
    for row in rows:
        pattern = row["path"]
        if pattern in seen_patterns:
            reasons.append(f"duplicate {label} path expression: {pattern}")
            continue
        seen_patterns.add(pattern)
        try:
            matches = _expand_tracked_pattern(repo_root, pattern, tracked)
        except ValueError as exc:
            reasons.append(str(exc))
            continue
        if not matches:
            reasons.append(f"{label} path expression has no tracked match: {pattern}")
            continue
        overlap = sorted(claimed & matches)
        if overlap:
            reasons.append(
                f"{label} path expressions overlap at: {', '.join(overlap)}"
            )
        for relative in sorted(matches):
            path = repo_root / relative
            if path.is_symlink():
                reasons.append(f"{label} path must not be a symlink: {relative}")
            elif label == "formal" and path.stat().st_size == 0:
                reasons.append(f"formal file must be non-empty: {relative}")
        claimed.update(matches)
    return claimed


def _validate_authority_dag(
    rows: list[dict[str, str]],
    reasons: list[str],
) -> list[str]:
    nodes = {row["path"] for row in rows}
    upstream: dict[str, set[str]] = {}
    root_count = 0
    for row in rows:
        node = row["path"]
        tokens = [token.strip() for token in row["upstream"].split(";")]
        if len(tokens) != len(set(tokens)):
            reasons.append(f"formal upstream repeats a token: {node}")
        if "ROOT" in tokens:
            root_count += 1
            if tokens != ["ROOT"]:
                reasons.append(f"ROOT must be exclusive in formal upstream: {node}")
            upstream[node] = set()
            continue
        unknown = sorted(token for token in tokens if token not in nodes)
        if unknown:
            reasons.append(
                f"formal upstream references unknown path expression for {node}: "
                f"{', '.join(unknown)}"
            )
        if node in tokens:
            reasons.append(f"formal upstream cannot reference itself: {node}")
        upstream[node] = {token for token in tokens if token in nodes}
    if root_count != 1:
        reasons.append(f"formal authority DAG must contain exactly one ROOT, found {root_count}")

    indegree = {node: len(dependencies) for node, dependencies in upstream.items()}
    downstream: dict[str, set[str]] = {node: set() for node in nodes}
    for node, dependencies in upstream.items():
        for dependency in dependencies:
            downstream[dependency].add(node)
    ready = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for dependent in sorted(downstream[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    if len(order) != len(nodes):
        reasons.append("formal authority path-expression graph must be acyclic")
    return order


def validate_repo_manifest(
    manifest_path: str | Path = "REPO_MANIFEST.md",
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    path = Path(manifest_path)
    root = Path(repo_root).resolve() if repo_root is not None else path.resolve().parent
    if path.is_symlink():
        return {
            "status": "BLOCK",
            "manifest_path": str(path),
            "reasons": ["repository manifest must not be a symlink"],
        }
    try:
        text = path.read_text(encoding="utf-8")
        tracked = _tracked_paths(root)
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        return {
            "status": "BLOCK",
            "manifest_path": str(path),
            "reasons": [f"unable to read repository manifest inputs: {exc}"],
        }

    formal_rows, formal_reasons = _table_rows(
        text,
        FORMAL_SECTION,
        FORMAL_COLUMNS,
    )
    legacy_rows, legacy_reasons = _table_rows(
        text,
        LEGACY_SECTION,
        LEGACY_COLUMNS,
    )
    reasons = formal_reasons + legacy_reasons
    formal_paths = _validate_path_sets(
        root,
        tracked,
        formal_rows,
        "formal",
        reasons,
    )
    legacy_paths = _validate_path_sets(
        root,
        tracked,
        legacy_rows,
        "legacy",
        reasons,
    )
    overlap = sorted(formal_paths & legacy_paths)
    if overlap:
        reasons.append(f"formal and legacy sets overlap at: {', '.join(overlap)}")
    unclassified = sorted(tracked - formal_paths - legacy_paths)
    if unclassified:
        reasons.append(f"tracked paths are unclassified: {', '.join(unclassified)}")

    for row in formal_rows:
        if row["lifecycle"] != "ACTIVE":
            reasons.append(f"formal lifecycle must be ACTIVE: {row['path']}")
        if row["status"] != "REGISTERED":
            reasons.append(f"formal status must be REGISTERED: {row['path']}")
    for row in legacy_rows:
        if row["authority"] != "false":
            reasons.append(f"legacy authority must be false: {row['path']}")
        if row["runtime_default"] != "false":
            reasons.append(f"legacy runtime_default must be false: {row['path']}")
        if not row["classification"].startswith("retained "):
            reasons.append(f"legacy classification must start with retained: {row['path']}")
        if row["disposition"] != "pending separate cleanup authorization":
            reasons.append(
                f"legacy disposition must preserve the cleanup boundary: {row['path']}"
            )

    execution_order = _validate_authority_dag(formal_rows, reasons)
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "manifest_path": str(path),
        "tracked_path_count": len(tracked),
        "formal_set_count": len(formal_rows),
        "formal_path_count": len(formal_paths),
        "legacy_set_count": len(legacy_rows),
        "legacy_path_count": len(legacy_paths),
        "unclassified_path_count": len(unclassified),
        "formal_execution_order": execution_order,
        "group_process_file_compliance_claimed": False,
        "cleanup_authorized": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
