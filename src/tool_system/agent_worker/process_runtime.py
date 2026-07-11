from __future__ import annotations

import hashlib
import json
import os
import resource
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Event
from typing import Literal

ProcessWorkerStatus = Literal[
    "PASS", "BLOCK", "TIMEOUT", "CANCELLED", "OUTPUT_LIMIT"
]

_SECRET_MARKERS = (
    "TOKEN",
    "KEY",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
    "AUTH",
    "COOKIE",
)
_RESOURCE_NAMES = (
    "RLIMIT_CPU",
    "RLIMIT_AS",
    "RLIMIT_NPROC",
    "RLIMIT_NOFILE",
    "RLIMIT_FSIZE",
    "RLIMIT_CORE",
)
_BLOCKED_AUDIT_PREFIXES = ("socket.", "subprocess.")
_BLOCKED_AUDIT_EVENTS = {
    "os.system",
    "os.fork",
    "os.forkpty",
    "os.posix_spawn",
    "os.spawn",
    "os.exec",
}
_BLOCKED_IMPORT_ROOTS = {"ctypes", "multiprocessing", "socket", "subprocess"}


@dataclass(frozen=True)
class ProcessWorkerLimits:
    timeout_seconds: float = 5.0
    cpu_seconds: int = 2
    memory_bytes: int = 512 * 1024 * 1024
    max_processes: int = 1
    max_open_files: int = 32
    max_file_bytes: int = 1024 * 1024
    max_stdout_bytes: int = 64 * 1024
    max_stderr_bytes: int = 64 * 1024
    max_fixture_bytes: int = 64 * 1024


@dataclass(frozen=True)
class ProcessWorkerRequest:
    request_id: str
    entrypoint: Path
    allowed_fixture_root: Path
    workspace_root: Path
    forbidden_roots: tuple[Path, ...]
    network_mode: str = "disabled"
    writes_target_repo: bool = False
    executes_target_repo_mutation: bool = False
    production: bool = False
    limits: ProcessWorkerLimits = field(default_factory=ProcessWorkerLimits)


@dataclass(frozen=True)
class ProcessWorkerPreflight:
    status: Literal["PASS", "BLOCK"]
    reasons: tuple[str, ...]
    request_id: str
    entrypoint: str | None
    fixture_root: str | None
    workspace_root: str | None
    python_executable: str | None
    argv_template: tuple[str, ...]
    environment_names: tuple[str, ...]
    resource_limits: dict[str, int | float]
    guard_mode: str
    termination_triggers: tuple[str, ...]
    workspace_cleanup_required: bool
    starts_process: bool = False

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessWorkerResult:
    request_id: str
    status: ProcessWorkerStatus
    reasons: tuple[str, ...]
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    stdout_bytes: int
    stderr_bytes: int
    stdout_sha256: str
    stderr_sha256: str
    limits: dict[str, int | float]
    guard_mode: str
    network_mode: str
    workspace_deleted: bool
    writes_target_repo: bool = False
    executes_target_repo_mutation: bool = False
    production: bool = False

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_existing(path: Path, label: str, reasons: list[str]) -> Path | None:
    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError):
        reasons.append(f"{label} must exist and resolve safely")
        return None


def _limits_reasons(limits: ProcessWorkerLimits) -> list[str]:
    reasons: list[str] = []
    for name, value in asdict(limits).items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            reasons.append(f"limits.{name} must be positive")
    return reasons


def _resource_limit_record(limits: ProcessWorkerLimits) -> dict[str, int | float]:
    return {
        "timeout_seconds": limits.timeout_seconds,
        "RLIMIT_CPU": limits.cpu_seconds,
        "RLIMIT_AS": limits.memory_bytes,
        "RLIMIT_NPROC": limits.max_processes,
        "RLIMIT_NOFILE": limits.max_open_files,
        "RLIMIT_FSIZE": limits.max_file_bytes,
        "RLIMIT_CORE": 0,
        "stdout_bytes": limits.max_stdout_bytes,
        "stderr_bytes": limits.max_stderr_bytes,
        "fixture_bytes": limits.max_fixture_bytes,
    }


def _minimal_environment(workspace: Path) -> dict[str, str]:
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "TOOL_SYSTEM_NETWORK": "disabled",
        "TOOL_SYSTEM_WORKSPACE": str(workspace),
    }
    if any(marker in name.upper() for name in environment for marker in _SECRET_MARKERS):
        raise RuntimeError("safe environment unexpectedly contains a secret-like name")
    return environment


def preflight_process_worker(
    request: ProcessWorkerRequest,
    *,
    python_executable: str | Path = sys.executable,
) -> ProcessWorkerPreflight:
    reasons: list[str] = []
    if not request.request_id.strip():
        reasons.append("request_id is required")
    if request.network_mode != "disabled":
        reasons.append("network_mode must be disabled")
    if request.writes_target_repo:
        reasons.append("writes_target_repo must be false")
    if request.executes_target_repo_mutation:
        reasons.append("executes_target_repo_mutation must be false")
    if request.production:
        reasons.append("production must be false")
    if not request.forbidden_roots:
        reasons.append("forbidden_roots must be non-empty")
    reasons.extend(_limits_reasons(request.limits))

    fixture_root = _resolve_existing(
        Path(request.allowed_fixture_root), "allowed_fixture_root", reasons
    )
    entrypoint = _resolve_existing(Path(request.entrypoint), "entrypoint", reasons)
    workspace_root = _resolve_existing(Path(request.workspace_root), "workspace_root", reasons)
    executable = _resolve_existing(Path(python_executable), "python_executable", reasons)

    if Path(request.allowed_fixture_root).is_symlink():
        reasons.append("allowed_fixture_root must not be a symlink")
    if Path(request.entrypoint).is_symlink():
        reasons.append("entrypoint must not be a symlink")
    if Path(request.workspace_root).is_symlink():
        reasons.append("workspace_root must not be a symlink")

    if fixture_root is not None and not fixture_root.is_dir():
        reasons.append("allowed_fixture_root must be a directory")
    if workspace_root is not None and not workspace_root.is_dir():
        reasons.append("workspace_root must be a directory")
    if entrypoint is not None:
        try:
            mode = entrypoint.stat().st_mode
            size = entrypoint.stat().st_size
        except OSError:
            reasons.append("entrypoint metadata must be readable")
        else:
            if not stat.S_ISREG(mode):
                reasons.append("entrypoint must be a regular file")
            if size > request.limits.max_fixture_bytes:
                reasons.append("entrypoint exceeds limits.max_fixture_bytes")
        if fixture_root is not None and not _is_relative_to(entrypoint, fixture_root):
            reasons.append("entrypoint must resolve under allowed_fixture_root")

    if executable is not None:
        if not executable.is_file() or not os.access(executable, os.X_OK):
            reasons.append("python_executable must be an executable regular file")

    if workspace_root is not None:
        for raw_root in request.forbidden_roots:
            forbidden = _resolve_existing(Path(raw_root), "forbidden_root", reasons)
            if forbidden is not None and _is_relative_to(workspace_root, forbidden):
                reasons.append("workspace_root must be outside every forbidden_root")

    environment_names = tuple(sorted(_minimal_environment(Path("<workspace>"))))
    executable_text = str(executable) if executable is not None else None
    argv_template = (
        executable_text or "<python_executable>",
        "-I",
        "-S",
        "-B",
        "<workspace>/guard.py",
        "<workspace>/worker.py",
    )
    return ProcessWorkerPreflight(
        status="BLOCK" if reasons else "PASS",
        reasons=tuple(dict.fromkeys(reasons)),
        request_id=request.request_id,
        entrypoint=str(entrypoint) if entrypoint is not None else None,
        fixture_root=str(fixture_root) if fixture_root is not None else None,
        workspace_root=str(workspace_root) if workspace_root is not None else None,
        python_executable=executable_text,
        argv_template=argv_template,
        environment_names=environment_names,
        resource_limits=_resource_limit_record(request.limits),
        guard_mode="python_audit_guard_v1",
        termination_triggers=("timeout", "cancellation", "stdout_limit", "stderr_limit"),
        workspace_cleanup_required=True,
    )


def audit_event_denial_reason(
    event: str,
    *,
    path: str | Path | None = None,
    workspace: str | Path,
    stdlib_roots: tuple[str | Path, ...] = (),
    write: bool = False,
    import_name: str | None = None,
) -> str | None:
    if event.startswith(_BLOCKED_AUDIT_PREFIXES) or event in _BLOCKED_AUDIT_EVENTS:
        return f"audit event denied: {event}"
    if event == "import" and import_name:
        if import_name.split(".", 1)[0] in _BLOCKED_IMPORT_ROOTS:
            return f"import denied: {import_name}"
    if path is None:
        return None
    resolved = Path(path).resolve(strict=False)
    workspace_path = Path(workspace).resolve(strict=False)
    if _is_relative_to(resolved, workspace_path):
        return None
    if not write:
        for root in stdlib_roots:
            if _is_relative_to(resolved, Path(root).resolve(strict=False)):
                return None
    return f"path denied outside workspace: {resolved}"


def terminal_status_for_trigger(trigger: str | None, exit_code: int | None) -> ProcessWorkerStatus:
    return {
        "timeout": "TIMEOUT",
        "cancellation": "CANCELLED",
        "stdout_limit": "OUTPUT_LIMIT",
        "stderr_limit": "OUTPUT_LIMIT",
    }.get(trigger, "PASS" if exit_code == 0 else "BLOCK")


def _guard_source(stdlib_roots: tuple[str, ...]) -> str:
    roots_json = json.dumps(stdlib_roots)
    blocked_prefixes = repr(_BLOCKED_AUDIT_PREFIXES)
    blocked_events = repr(_BLOCKED_AUDIT_EVENTS)
    blocked_imports = repr(_BLOCKED_IMPORT_ROOTS)
    return f'''import os
import runpy
import sys

WORKSPACE = os.path.realpath(sys.argv[1])
ENTRYPOINT = os.path.realpath(sys.argv[2])
STDLIB_ROOTS = tuple(os.path.realpath(p) for p in {roots_json})
BLOCKED_PREFIXES = {blocked_prefixes}
BLOCKED_EVENTS = {blocked_events}
BLOCKED_IMPORTS = {blocked_imports}

def inside(path, root):
    try:
        return os.path.commonpath((os.path.realpath(path), root)) == root
    except (OSError, ValueError, TypeError):
        return False

def audit(event, args):
    if event.startswith(BLOCKED_PREFIXES) or event in BLOCKED_EVENTS:
        raise PermissionError("worker audit event denied: " + event)
    if event == "import" and args:
        name = str(args[0]).split(".", 1)[0]
        if name in BLOCKED_IMPORTS:
            raise PermissionError("worker import denied: " + name)
    if event == "open" and args and not isinstance(args[0], int):
        path = os.fspath(args[0])
        mode = str(args[1]) if len(args) > 1 else "r"
        writing = any(flag in mode for flag in ("w", "a", "+", "x"))
        allowed = inside(path, WORKSPACE) or (
            not writing and any(inside(path, root) for root in STDLIB_ROOTS)
        )
        if not allowed:
            raise PermissionError("worker path denied outside workspace")

sys.addaudithook(audit)
os.chdir(WORKSPACE)
runpy.run_path(ENTRYPOINT, run_name="__main__")
'''


def _apply_resource_limits(limits: ProcessWorkerLimits) -> None:
    os.umask(0o077)
    values = {
        "RLIMIT_CPU": limits.cpu_seconds,
        "RLIMIT_AS": limits.memory_bytes,
        "RLIMIT_NPROC": limits.max_processes,
        "RLIMIT_NOFILE": limits.max_open_files,
        "RLIMIT_FSIZE": limits.max_file_bytes,
        "RLIMIT_CORE": 0,
    }
    for name, value in values.items():
        if hasattr(resource, name):
            resource.setrlimit(getattr(resource, name), (value, value))


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        process.kill()


def _collect_output(
    process: subprocess.Popen[bytes],
    limits: ProcessWorkerLimits,
    cancellation: Event | None,
) -> tuple[bytes, bytes, str | None]:
    selector = selectors.DefaultSelector()
    streams = {process.stdout: ("stdout", limits.max_stdout_bytes), process.stderr: ("stderr", limits.max_stderr_bytes)}
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    for stream in streams:
        if stream is not None:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
    deadline = time.monotonic() + limits.timeout_seconds
    trigger: str | None = None
    try:
        while selector.get_map():
            if trigger is None and cancellation is not None and cancellation.is_set():
                trigger = "cancellation"
                _kill_process_group(process)
            if trigger is None and time.monotonic() >= deadline:
                trigger = "timeout"
                _kill_process_group(process)
            for key, _ in selector.select(timeout=0.05):
                stream = key.fileobj
                label, cap = streams[stream]
                try:
                    chunk = os.read(stream.fileno(), 8192)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                remaining = max(0, cap - len(buffers[label]))
                buffers[label].extend(chunk[:remaining])
                if len(chunk) > remaining and trigger is None:
                    trigger = f"{label}_limit"
                    _kill_process_group(process)
            if process.poll() is not None and not selector.get_map():
                break
    finally:
        selector.close()
    return bytes(buffers["stdout"]), bytes(buffers["stderr"]), trigger


def run_process_worker(
    request: ProcessWorkerRequest,
    *,
    python_executable: str | Path = sys.executable,
    cancellation: Event | None = None,
) -> ProcessWorkerResult:
    preflight = preflight_process_worker(request, python_executable=python_executable)
    if preflight.status == "BLOCK":
        empty_hash = hashlib.sha256(b"").hexdigest()
        return ProcessWorkerResult(
            request_id=request.request_id,
            status="BLOCK",
            reasons=preflight.reasons,
            exit_code=None,
            duration_seconds=0.0,
            stdout="",
            stderr="",
            stdout_bytes=0,
            stderr_bytes=0,
            stdout_sha256=empty_hash,
            stderr_sha256=empty_hash,
            limits=preflight.resource_limits,
            guard_mode=preflight.guard_mode,
            network_mode=request.network_mode,
            workspace_deleted=True,
        )

    started = time.monotonic()
    process: subprocess.Popen[bytes] | None = None
    workspace_path: Path | None = None
    stdout = b""
    stderr = b""
    trigger: str | None = None
    exit_code: int | None = None
    reasons: list[str] = []
    try:
        with tempfile.TemporaryDirectory(
            prefix="tool-system-p11-worker-", dir=preflight.workspace_root
        ) as temporary:
            workspace_path = Path(temporary)
            worker_path = workspace_path / "worker.py"
            guard_path = workspace_path / "guard.py"
            shutil.copyfile(preflight.entrypoint or "", worker_path, follow_symlinks=False)
            worker_path.chmod(0o400)
            stdlib_paths = tuple(
                sorted(
                    {
                        str(Path(value).resolve())
                        for value in sysconfig.get_paths().values()
                        if value and Path(value).exists()
                    }
                )
            )
            guard_path.write_text(_guard_source(stdlib_paths), encoding="utf-8")
            guard_path.chmod(0o400)
            argv = [
                preflight.python_executable or str(python_executable),
                "-I",
                "-S",
                "-B",
                str(guard_path),
                str(workspace_path),
                str(worker_path),
            ]
            process = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workspace_path,
                env=_minimal_environment(workspace_path),
                shell=False,
                close_fds=True,
                start_new_session=True,
                preexec_fn=lambda: _apply_resource_limits(request.limits),
            )
            stdout, stderr, trigger = _collect_output(process, request.limits, cancellation)
            exit_code = process.wait(timeout=1)
    except Exception as exc:  # fail closed and return a bounded diagnostic
        if process is not None:
            _kill_process_group(process)
        reasons.append(f"worker runtime failed closed: {type(exc).__name__}: {exc}")
    workspace_deleted = workspace_path is None or not workspace_path.exists()
    status = "BLOCK" if reasons else terminal_status_for_trigger(trigger, exit_code)
    if trigger is not None:
        reasons.append(f"worker terminated by {trigger}")
    elif exit_code not in (None, 0):
        reasons.append(f"worker exited with code {exit_code}")
    if not workspace_deleted:
        status = "BLOCK"
        reasons.append("ephemeral workspace was not deleted")
    return ProcessWorkerResult(
        request_id=request.request_id,
        status=status,
        reasons=tuple(reasons),
        exit_code=exit_code,
        duration_seconds=round(time.monotonic() - started, 6),
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr.decode("utf-8", errors="replace"),
        stdout_bytes=len(stdout),
        stderr_bytes=len(stderr),
        stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        limits=_resource_limit_record(request.limits),
        guard_mode=preflight.guard_mode,
        network_mode=request.network_mode,
        workspace_deleted=workspace_deleted,
    )


def required_resource_limit_names() -> tuple[str, ...]:
    return _RESOURCE_NAMES
