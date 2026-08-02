"""Build deterministic, bounded context from one clean local Git snapshot.

The module deliberately reads committed blobs through Git instead of following
working-tree paths.  It does not write a cache, mutate the repository, contact a
remote, or turn its natural-owner proposal into authority.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import posixpath
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".pyi",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
_IMPLEMENTATION_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".py",
    ".pyi",
    ".rs",
    ".ts",
    ".tsx",
}
_JS_IMPORT_RE = re.compile(
    r"(?:from\s+|require\s*\(\s*|import\s*\(\s*)"
    r"['\"]([^'\"]+)['\"]"
)


class RepositoryContextError(ValueError):
    """Fail-closed repository-context error with a stable redacted code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class RepositoryContextLimits:
    """Finite input, scan, and selected-context ceilings."""

    max_tracked_files: int = 512
    max_selected_files: int = 32
    max_file_bytes: int = 131_072
    max_scan_bytes: int = 4_194_304
    max_selected_bytes: int = 1_048_576
    max_query_terms: int = 24

    def validate(self) -> None:
        values = asdict(self)
        if any(not isinstance(value, int) or value <= 0 for value in values.values()):
            raise RepositoryContextError("INVALID_LIMITS")
        if self.max_selected_files > self.max_tracked_files:
            raise RepositoryContextError("INVALID_LIMITS")
        if self.max_selected_bytes > self.max_scan_bytes:
            raise RepositoryContextError("INVALID_LIMITS")


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }


def _run_git(root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "filter.lfs.required=false",
                *arguments,
            ],
            cwd=root,
            env=_git_environment(),
            check=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RepositoryContextError("LOCAL_GIT_READ_FAILED") from error
    return result.stdout


def _normalize_root(repository_root: str | os.PathLike[str]) -> Path:
    supplied = Path(repository_root)
    if supplied.is_symlink():
        raise RepositoryContextError("SYMLINK_REPOSITORY_ROOT")
    try:
        resolved = supplied.resolve(strict=True)
    except OSError as error:
        raise RepositoryContextError("REPOSITORY_ROOT_UNAVAILABLE") from error
    if not resolved.is_dir():
        raise RepositoryContextError("REPOSITORY_ROOT_NOT_DIRECTORY")
    try:
        top_level = Path(
            _run_git(resolved, "rev-parse", "--show-toplevel")
            .decode("utf-8")
            .strip()
        ).resolve(strict=True)
    except (UnicodeDecodeError, OSError) as error:
        raise RepositoryContextError("INVALID_REPOSITORY_ROOT") from error
    if top_level != resolved:
        raise RepositoryContextError("REPOSITORY_ROOT_NOT_TOP_LEVEL")
    return resolved


def _safe_repo_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RepositoryContextError("INVALID_REPOSITORY_PATH")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value:
        raise RepositoryContextError("INVALID_REPOSITORY_PATH")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise RepositoryContextError("INVALID_REPOSITORY_PATH")
    return value


def _tracked_entries(root: Path, limit: int) -> list[dict[str, Any]]:
    raw = _run_git(root, "ls-tree", "-rz", "-l", "--full-tree", "HEAD")
    entries: list[dict[str, Any]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, encoded_path = record.split(b"\t", 1)
            mode, object_type, object_id, size = metadata.split()
            path = encoded_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise RepositoryContextError("UNSUPPORTED_TRACKED_ENTRY") from error
        if object_type != b"blob" or size == b"-":
            raise RepositoryContextError("UNSUPPORTED_TRACKED_ENTRY")
        safe_path = _safe_repo_path(path)
        entries.append(
            {
                "path": safe_path,
                "mode": mode.decode("ascii"),
                "object_id": object_id.decode("ascii"),
                "size": int(size),
                "symlink": mode == b"120000",
            }
        )
        if len(entries) > limit:
            raise RepositoryContextError("TRACKED_FILE_LIMIT_EXCEEDED")
    return sorted(entries, key=lambda entry: entry["path"])


def _capture_snapshot(
    root: Path,
    expected_head: str,
    max_tracked_files: int,
) -> dict[str, Any]:
    if _SHA1_RE.fullmatch(expected_head) is None:
        raise RepositoryContextError("INVALID_EXPECTED_HEAD")
    head = _run_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    tree = _run_git(root, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
    if head != expected_head:
        raise RepositoryContextError("STALE_EXPECTED_HEAD")
    if _run_git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RepositoryContextError("DIRTY_WORKTREE")
    entries = _tracked_entries(root, max_tracked_files)
    tracked_digest_input = [
        {
            "mode": entry["mode"],
            "object_id": entry["object_id"],
            "path": entry["path"],
            "size": entry["size"],
        }
        for entry in entries
    ]
    return {
        "head": head,
        "tree": tree,
        "entries": entries,
        "tracked_set_sha256": _canonical_sha256(tracked_digest_input),
    }


def _blob(root: Path, entry: Mapping[str, Any]) -> bytes:
    if entry["symlink"]:
        raise RepositoryContextError("SYMLINK_INPUT_BLOCKED")
    return _run_git(root, "cat-file", "blob", str(entry["object_id"]))


def _decode_text(data: bytes) -> str:
    if b"\0" in data:
        raise RepositoryContextError("BINARY_INPUT_BLOCKED")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RepositoryContextError("NON_UTF8_INPUT_BLOCKED") from error


def _is_test_path(path: str) -> bool:
    pure = PurePosixPath(path)
    stem = pure.stem.casefold()
    return (
        "tests" in pure.parts
        or "test" in pure.parts
        or stem.startswith("test_")
        or stem.endswith("_test")
        or stem.endswith(".test")
        or stem.endswith(".spec")
    )


def _is_implementation_path(path: str) -> bool:
    return (
        PurePosixPath(path).suffix.casefold() in _IMPLEMENTATION_SUFFIXES
        and not _is_test_path(path)
    )


def _normalize_terms(query_terms: Iterable[str], maximum: int) -> tuple[str, ...]:
    tokens: set[str] = set()
    for term in query_terms:
        if not isinstance(term, str):
            raise RepositoryContextError("INVALID_QUERY_TERM")
        tokens.update(re.findall(r"[a-z0-9_]+", term.casefold()))
    if not tokens or len(tokens) > maximum:
        raise RepositoryContextError("INVALID_QUERY_TERMS")
    return tuple(sorted(tokens))


def _python_module_map(paths: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        pure = PurePosixPath(path)
        if pure.suffix not in {".py", ".pyi"}:
            continue
        parts = list(pure.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            result[".".join(parts)] = path
    return result


def _resolve_python_name(name: str, module_map: Mapping[str, str]) -> str | None:
    candidate = name
    while candidate:
        if candidate in module_map:
            return module_map[candidate]
        candidate = candidate.rpartition(".")[0]
    return None


def _python_dependencies(
    path: str,
    text: str,
    module_map: Mapping[str, str],
) -> set[str]:
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as error:
        raise RepositoryContextError("SOURCE_PARSE_FAILED") from error
    pure = PurePosixPath(path).with_suffix("")
    package = list(pure.parts)
    if package[-1] != "__init__":
        package.pop()
    dependencies: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = list(package)
            if node.level:
                remove = max(node.level - 1, 0)
                prefix = prefix[: len(prefix) - remove] if remove else prefix
            elif node.module:
                prefix = []
            module_parts = node.module.split(".") if node.module else []
            names.append(".".join([*prefix, *module_parts]))
        for name in names:
            resolved = _resolve_python_name(name, module_map)
            if resolved and resolved != path:
                dependencies.add(resolved)
    return dependencies


def _javascript_dependencies(path: str, text: str, known: set[str]) -> set[str]:
    dependencies: set[str] = set()
    parent = PurePosixPath(path).parent.as_posix()
    for reference in _JS_IMPORT_RE.findall(text):
        if not reference.startswith("."):
            continue
        normalized = posixpath.normpath(posixpath.join(parent, reference))
        if normalized == ".." or normalized.startswith("../"):
            continue
        candidates = [normalized]
        candidates.extend(f"{normalized}{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx"))
        candidates.extend(
            f"{normalized}/index{suffix}"
            for suffix in (".ts", ".tsx", ".js", ".jsx")
        )
        target = next((candidate for candidate in candidates if candidate in known), None)
        if target and target != path:
            dependencies.add(target)
    return dependencies


def _language(path: str) -> str:
    suffix = PurePosixPath(path).suffix.casefold()
    return {
        ".py": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
    }.get(suffix, suffix.removeprefix(".") or "text")


def _natural_owner_path(paths: Sequence[str]) -> str:
    if len(paths) == 1:
        return paths[0]
    parents = [PurePosixPath(path).parent.as_posix() for path in paths]
    common = posixpath.commonpath(parents)
    return common if common not in {"", "."} else paths[0]


def build_repository_context(
    repository_root: str | os.PathLike[str],
    *,
    expected_head: str,
    blueprint_path: str,
    governance_paths: Sequence[str],
    query_terms: Sequence[str],
    seed_paths: Sequence[str] = (),
    limits: RepositoryContextLimits | None = None,
) -> dict[str, Any]:
    """Return one content-addressed context from a clean committed snapshot."""

    bounded = limits or RepositoryContextLimits()
    bounded.validate()
    root = _normalize_root(repository_root)
    terms = _normalize_terms(query_terms, bounded.max_query_terms)
    blueprint = _safe_repo_path(blueprint_path)
    governance = tuple(_safe_repo_path(path) for path in governance_paths)
    seeds = tuple(_safe_repo_path(path) for path in seed_paths)
    if not governance or len(set(governance)) != len(governance):
        raise RepositoryContextError("INVALID_GOVERNANCE_PATHS")
    if len(set(seeds)) != len(seeds):
        raise RepositoryContextError("INVALID_SEED_PATHS")

    start = _capture_snapshot(root, expected_head, bounded.max_tracked_files)
    entries = start["entries"]
    by_path = {str(entry["path"]): entry for entry in entries}
    mandatory = {blueprint, *governance, *seeds}
    if not mandatory <= set(by_path):
        raise RepositoryContextError("REQUIRED_EVIDENCE_MISSING")
    for path in mandatory:
        entry = by_path[path]
        if entry["symlink"]:
            raise RepositoryContextError("SYMLINK_INPUT_BLOCKED")
        if entry["size"] > bounded.max_file_bytes:
            raise RepositoryContextError("REQUIRED_FILE_LIMIT_EXCEEDED")

    text_cache: dict[str, str] = {}
    scan_bytes = 0
    for entry in entries:
        path = str(entry["path"])
        suffix = PurePosixPath(path).suffix.casefold()
        if suffix not in _TEXT_SUFFIXES or entry["symlink"]:
            continue
        if entry["size"] > bounded.max_file_bytes:
            continue
        scan_bytes += int(entry["size"])
        if scan_bytes > bounded.max_scan_bytes:
            raise RepositoryContextError("SCAN_LIMIT_EXCEEDED")
        text_cache[path] = _decode_text(_blob(root, entry))
    if not mandatory <= set(text_cache):
        raise RepositoryContextError("REQUIRED_TEXT_EVIDENCE_UNREADABLE")

    known_paths = set(by_path)
    module_map = _python_module_map(tuple(known_paths))
    dependency_map: dict[str, list[str]] = {}
    for path, text in sorted(text_cache.items()):
        suffix = PurePosixPath(path).suffix.casefold()
        dependencies: set[str] = set()
        if suffix in {".py", ".pyi"}:
            dependencies = _python_dependencies(path, text, module_map)
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            dependencies = _javascript_dependencies(path, text, known_paths)
        if dependencies:
            dependency_map[path] = sorted(dependencies)

    reasons: dict[str, set[str]] = {path: set() for path in text_cache}
    scores = {path: 0 for path in text_cache}
    for path in governance:
        scores[path] += 10_000
        reasons[path].add("governance-evidence")
    scores[blueprint] += 10_000
    reasons[blueprint].add("blueprint-evidence")
    for path in seeds:
        scores[path] += 8_000
        reasons[path].add("caller-seed")
    for path, text in text_cache.items():
        folded_path = path.casefold()
        folded_text = text.casefold()
        for term in terms:
            if term in folded_path:
                scores[path] += 500
                reasons[path].add(f"path-term:{term}")
            if term in folded_text:
                scores[path] += 50
                reasons[path].add(f"content-term:{term}")
        if _is_implementation_path(path):
            scores[path] += 10

    relevant_code = {
        path
        for path in text_cache
        if _is_implementation_path(path)
        and (path in seeds or any(reason.startswith(("path-term:", "content-term:")) for reason in reasons[path]))
    }
    if not relevant_code:
        raise RepositoryContextError("INSUFFICIENT_OWNER_EVIDENCE")

    reverse_dependencies: dict[str, set[str]] = {}
    for source, dependencies in dependency_map.items():
        for dependency in dependencies:
            reverse_dependencies.setdefault(dependency, set()).add(source)
    closure = set(relevant_code)
    for source in tuple(relevant_code):
        closure.update(dependency_map.get(source, ()))
        closure.update(reverse_dependencies.get(source, ()))
    for path in closure:
        if path not in scores:
            continue
        scores[path] += 2_000
        reasons[path].add("dependency-or-consumer-closure")

    test_map: dict[str, list[str]] = {}
    test_paths = {path for path in text_cache if _is_test_path(path)}
    for source in sorted(path for path in text_cache if _is_implementation_path(path)):
        source_stem = PurePosixPath(source).stem.casefold()
        matches = {
            test
            for test in test_paths
            if source in dependency_map.get(test, ())
            or source_stem in PurePosixPath(test).stem.casefold()
        }
        if matches:
            test_map[source] = sorted(matches)
            if source in closure:
                for test in matches:
                    scores[test] += 1_500
                    reasons[test].add("mapped-test")

    ordered = sorted(text_cache, key=lambda path: (-scores[path], path))
    selected: list[dict[str, Any]] = []
    selected_bytes = 0
    for path in ordered:
        if scores[path] <= 0:
            continue
        encoded_size = len(text_cache[path].encode("utf-8"))
        required = path in mandatory
        if len(selected) >= bounded.max_selected_files:
            if required:
                raise RepositoryContextError("SELECTED_FILE_LIMIT_EXCEEDED")
            continue
        if selected_bytes + encoded_size > bounded.max_selected_bytes:
            if required:
                raise RepositoryContextError("SELECTED_BYTE_LIMIT_EXCEEDED")
            continue
        selected_bytes += encoded_size
        selected.append(
            {
                "path": path,
                "language": _language(path),
                "object_id": by_path[path]["object_id"],
                "size": encoded_size,
                "content_sha256": hashlib.sha256(
                    text_cache[path].encode("utf-8")
                ).hexdigest(),
                "relevance_score": scores[path],
                "relevance_reasons": sorted(reasons[path]),
                "content": text_cache[path],
            }
        )
    selected_paths = {record["path"] for record in selected}
    if not mandatory <= selected_paths:
        raise RepositoryContextError("REQUIRED_CONTEXT_NOT_SELECTED")
    selected_code = [
        record["path"]
        for record in selected
        if record["path"] in relevant_code
    ]
    if not selected_code:
        raise RepositoryContextError("INSUFFICIENT_OWNER_EVIDENCE")

    index = [
        {
            "path": entry["path"],
            "mode": entry["mode"],
            "object_id": entry["object_id"],
            "size": entry["size"],
            "language": _language(str(entry["path"])),
            "symlink": entry["symlink"],
        }
        for entry in entries
    ]
    context_sha256 = _canonical_sha256(
        [
            {
                key: record[key]
                for key in (
                    "content_sha256",
                    "object_id",
                    "path",
                    "relevance_reasons",
                    "relevance_score",
                    "size",
                )
            }
            for record in selected
        ]
    )
    end = _capture_snapshot(root, expected_head, bounded.max_tracked_files)
    if any(
        start[key] != end[key]
        for key in ("head", "tree", "tracked_set_sha256")
    ):
        raise RepositoryContextError("STALE_SNAPSHOT_DURING_BUILD")

    owner_evidence = sorted(
        {
            *selected_code,
            *(
                test
                for source in selected_code
                for test in test_map.get(source, ())
                if test in selected_paths
            ),
        }
    )
    return {
        "status": "PASS",
        "snapshot": {
            "repository_root": str(root),
            "head": start["head"],
            "tree": start["tree"],
            "tracked_file_count": len(entries),
            "tracked_set_sha256": start["tracked_set_sha256"],
            "context_sha256": context_sha256,
            "clean_worktree": True,
        },
        "limits": asdict(bounded),
        "query_terms": list(terms),
        "mandatory_evidence_paths": sorted(mandatory),
        "repository_index": index,
        "dependency_map": dependency_map,
        "test_map": test_map,
        "selected_context": selected,
        "selected_file_count": len(selected),
        "selected_bytes": selected_bytes,
        "natural_owner_proposal": {
            "authority_effect": "none",
            "owner_path": _natural_owner_path(selected_code),
            "evidence_paths": owner_evidence,
            "proposal_status": "EVIDENCE_SUPPORTED",
        },
        "evidence_sufficiency": {
            "status": "PASS",
            "blueprint_present": blueprint in selected_paths,
            "governance_paths_present": all(path in selected_paths for path in governance),
            "relevant_implementation_paths": sorted(selected_code),
        },
        "side_effects": {
            "repository_writes": 0,
            "network_operations": 0,
            "provider_invocations": 0,
            "credential_accesses": 0,
        },
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
    }


def validate_repository_context_freshness(
    repository_root: str | os.PathLike[str],
    snapshot: Mapping[str, Any],
    *,
    max_tracked_files: int = 512,
) -> dict[str, Any]:
    """Revalidate a prior context snapshot without reading selected content."""

    root = _normalize_root(repository_root)
    expected = snapshot.get("head")
    if not isinstance(expected, str):
        raise RepositoryContextError("INVALID_SNAPSHOT")
    current = _capture_snapshot(root, expected, max_tracked_files)
    expected_fields = {
        "head": snapshot.get("head"),
        "tree": snapshot.get("tree"),
        "tracked_set_sha256": snapshot.get("tracked_set_sha256"),
    }
    observed_fields = {key: current[key] for key in expected_fields}
    if expected_fields != observed_fields:
        raise RepositoryContextError("STALE_REPOSITORY_CONTEXT")
    return {
        "status": "PASS",
        "head": current["head"],
        "tree": current["tree"],
        "tracked_set_sha256": current["tracked_set_sha256"],
        "clean_worktree": True,
        "repository_writes": 0,
        "network_operations": 0,
    }
