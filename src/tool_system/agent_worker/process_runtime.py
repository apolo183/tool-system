from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import selectors
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
_GUARD_MODE = "python_audit_guard_v2"
_BLOCKED_AUDIT_PREFIXES = (
    "socket.",
    "subprocess.",
    "syslog.",
    "resource.",
    "http.client.",
    "ftplib.",
    "imaplib.",
    "poplib.",
    "smtplib.",
)
_BLOCKED_AUDIT_EVENTS = {
    "cpython.remote_debugger_script",
    "gc.get_objects",
    "gc.get_referents",
    "gc.get_referrers",
    "os.system",
    "os.fork",
    "os.forkpty",
    "os.kill",
    "os.killpg",
    "os.posix_spawn",
    "os.spawn",
    "os.exec",
    "pty.spawn",
    "signal.pthread_kill",
    "sqlite3.enable_load_extension",
    "sqlite3.load_extension",
    "sys._current_exceptions",
    "sys._current_frames",
    "sys._getframe",
    "sys.addaudithook",
    "sys.monitoring.register_callback",
    "sys.remote_exec",
    "sys.setprofile",
    "sys.settrace",
    "urllib.Request",
    "webbrowser.open",
}
_BLOCKED_IMPORT_ROOTS = {"ctypes", "multiprocessing", "socket", "subprocess"}
_LINK_AUDIT_EVENTS = {"os.link", "os.symlink"}
_READ_PATH_EVENTS = {
    "glob.glob": (0,),
    "glob.glob/2": (0, 2),
    "os.fwalk": (0,),
    "os.getxattr": (0,),
    "os.listdir": (0,),
    "os.listxattr": (0,),
    "os.scandir": (0,),
    "os.walk": (0,),
    "pathlib.Path.glob": (0,),
    "pathlib.Path.rglob": (0,),
}
_WORKSPACE_PATH_EVENTS = {
    "os.chdir": (0,),
    "os.chflags": (0,),
    "os.chmod": (0,),
    "os.chown": (0,),
    "os.mkdir": (0,),
    "os.remove": (0,),
    "os.removexattr": (0,),
    "os.rename": (0, 1),
    "os.rmdir": (0,),
    "os.setxattr": (0,),
    "os.truncate": (0,),
    "os.utime": (0,),
    "shutil.chown": (0,),
    "shutil.copyfile": (0, 1),
    "shutil.copymode": (0, 1),
    "shutil.copystat": (0, 1),
    "shutil.copytree": (0, 1),
    "shutil.move": (0, 1),
    "shutil.rmtree": (0,),
    "sqlite3.connect": (0,),
    "tempfile.mkdtemp": (0,),
    "tempfile.mkstemp": (0,),
}


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
    entrypoint_device: int | None
    entrypoint_inode: int | None
    entrypoint_size: int | None
    entrypoint_mtime_ns: int | None
    entrypoint_sha256: str | None
    readable_library_roots: tuple[str, ...]
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


def approved_stdlib_roots() -> tuple[str, ...]:
    roots: set[str] = set()
    paths = sysconfig.get_paths()
    for name in ("stdlib", "platstdlib"):
        value = paths.get(name)
        if value:
            path = Path(value).resolve(strict=True)
            if path.is_dir():
                roots.add(str(path))
    if not roots:
        raise RuntimeError("approved standard-library roots are unavailable")
    return tuple(sorted(roots))


def _snapshot_entrypoint(
    path: Path, *, max_bytes: int
) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("entrypoint must be a regular file")
        if before.st_nlink != 1:
            raise ValueError("entrypoint must have exactly one hard link")
        if before.st_size > max_bytes:
            raise ValueError("entrypoint exceeds limits.max_fixture_bytes")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("entrypoint exceeds limits.max_fixture_bytes")
        after = os.fstat(descriptor)
        stable_fields = (
            "st_dev",
            "st_ino",
            "st_size",
            "st_mtime_ns",
            "st_nlink",
        )
        if any(getattr(before, name) != getattr(after, name) for name in stable_fields):
            raise ValueError("entrypoint changed while being snapshotted")
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def _limits_reasons(limits: ProcessWorkerLimits) -> list[str]:
    reasons: list[str] = []
    for name, value in asdict(limits).items():
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
        ):
            reasons.append(f"limits.{name} must be positive")
        elif name != "timeout_seconds" and not isinstance(value, int):
            reasons.append(f"limits.{name} must be an integer")
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
        "TOOL_SYSTEM_GUARD_MODE": _GUARD_MODE,
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
    if not isinstance(request.request_id, str) or not request.request_id.strip():
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
    entrypoint_bytes: bytes | None = None
    entrypoint_stat: os.stat_result | None = None

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
    if entrypoint is not None and isinstance(request.limits.max_fixture_bytes, int):
        try:
            entrypoint_bytes, entrypoint_stat = _snapshot_entrypoint(
                entrypoint, max_bytes=request.limits.max_fixture_bytes
            )
        except (OSError, ValueError) as exc:
            reasons.append(str(exc) or "entrypoint metadata must be read safely")
        if fixture_root is not None and not _is_relative_to(entrypoint, fixture_root):
            reasons.append("entrypoint must resolve under allowed_fixture_root")

    if executable is not None:
        if not executable.is_file() or not os.access(executable, os.X_OK):
            reasons.append("python_executable must be an executable regular file")
        approved_executable = Path(sys.executable).resolve(strict=True)
        if executable != approved_executable:
            reasons.append("python_executable must match the approved interpreter")

    if fixture_root is not None and workspace_root is not None:
        if _is_relative_to(fixture_root, workspace_root) or _is_relative_to(
            workspace_root, fixture_root
        ):
            reasons.append("fixture_root and workspace_root must be disjoint")

    if workspace_root is not None:
        for raw_root in request.forbidden_roots:
            forbidden = _resolve_existing(Path(raw_root), "forbidden_root", reasons)
            if forbidden is not None and _is_relative_to(workspace_root, forbidden):
                reasons.append("workspace_root must be outside every forbidden_root")

    try:
        library_roots = approved_stdlib_roots()
    except (OSError, RuntimeError):
        library_roots = ()
        reasons.append("approved standard-library roots must resolve safely")
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
        entrypoint_device=entrypoint_stat.st_dev if entrypoint_stat else None,
        entrypoint_inode=entrypoint_stat.st_ino if entrypoint_stat else None,
        entrypoint_size=entrypoint_stat.st_size if entrypoint_stat else None,
        entrypoint_mtime_ns=entrypoint_stat.st_mtime_ns if entrypoint_stat else None,
        entrypoint_sha256=(
            hashlib.sha256(entrypoint_bytes).hexdigest()
            if entrypoint_bytes is not None
            else None
        ),
        readable_library_roots=library_roots,
        argv_template=argv_template,
        environment_names=environment_names,
        resource_limits=_resource_limit_record(request.limits),
        guard_mode=_GUARD_MODE,
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
    if (
        event.startswith(_BLOCKED_AUDIT_PREFIXES)
        or event in _BLOCKED_AUDIT_EVENTS
        or event in _LINK_AUDIT_EVENTS
    ):
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
    link_events = repr(_LINK_AUDIT_EVENTS)
    read_path_events = repr(_READ_PATH_EVENTS)
    workspace_path_events = repr(_WORKSPACE_PATH_EVENTS)
    return f'''import os
import sys

def _build_guard(workspace, stdlib_roots):
    realpath = os.path.realpath
    commonpath = os.path.commonpath
    fspath = os.fspath
    write_stderr = os.write
    exit_now = os._exit
    workspace = realpath(workspace)
    stdlib_roots = tuple(realpath(path) for path in stdlib_roots)
    blocked_prefixes = {blocked_prefixes}
    blocked_events = frozenset({blocked_events})
    blocked_imports = frozenset({blocked_imports})
    link_events = frozenset({link_events})
    read_path_events = {read_path_events}
    workspace_path_events = {workspace_path_events}
    write_mask = (
        os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC | os.O_EXCL
    )

    def inside(path, root):
        try:
            return commonpath((realpath(fspath(path)), root)) == root
        except (OSError, ValueError, TypeError):
            return False

    def deny(event):
        message = ("tool-system guard denied: " + event + "\\n").encode(
            "utf-8", errors="replace"
        )[:512]
        try:
            write_stderr(2, message)
        finally:
            exit_now(126)

    def selected_paths(args, positions):
        return tuple(
            args[position]
            for position in positions
            if position < len(args) and args[position] is not None
        )

    def audit(event, args):
        if (
            event.startswith(blocked_prefixes)
            or event in blocked_events
            or event in link_events
        ):
            deny(event)
        if event == "import" and args:
            name = str(args[0]).split(".", 1)[0]
            if name in blocked_imports:
                deny("import:" + name)
        if event == "open" and args and not isinstance(args[0], int):
            mode = str(args[1]) if len(args) > 1 and args[1] is not None else ""
            flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
            writing = any(marker in mode for marker in ("w", "a", "+", "x")) or bool(
                flags & write_mask
            )
            allowed = inside(args[0], workspace) or (
                not writing and any(inside(args[0], root) for root in stdlib_roots)
            )
            if not allowed:
                deny(event)
        positions = read_path_events.get(event)
        if positions is not None:
            for path in selected_paths(args, positions):
                if isinstance(path, int):
                    continue
                if not inside(path, workspace) and not any(
                    inside(path, root) for root in stdlib_roots
                ):
                    deny(event)
        positions = workspace_path_events.get(event)
        if positions is not None:
            for path in selected_paths(args, positions):
                if isinstance(path, int):
                    continue
                if not inside(path, workspace):
                    deny(event)

    return audit

def _load_worker_code(entrypoint):
    with open(entrypoint, "rb") as handle:
        source = handle.read()
    return compile(source, entrypoint, "exec")

def _main(builder=_build_guard, loader=_load_worker_code):
    workspace = os.path.realpath(sys.argv[1])
    entrypoint = os.path.realpath(sys.argv[2])
    worker_code = loader(entrypoint)
    audit = builder(workspace, {roots_json})
    sys.addaudithook(audit)
    os.chdir(workspace)
    worker_globals = {{
        "__name__": "__main__",
        "__file__": entrypoint,
        "__builtins__": __builtins__,
    }}
    exec(worker_code, worker_globals)

del _build_guard
del _load_worker_code
_main()
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
            writes_target_repo=request.writes_target_repo,
            executes_target_repo_mutation=request.executes_target_repo_mutation,
            production=request.production,
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
        entrypoint_bytes, entrypoint_stat = _snapshot_entrypoint(
            Path(preflight.entrypoint or ""),
            max_bytes=request.limits.max_fixture_bytes,
        )
        current_identity = (
            entrypoint_stat.st_dev,
            entrypoint_stat.st_ino,
            entrypoint_stat.st_size,
            entrypoint_stat.st_mtime_ns,
            hashlib.sha256(entrypoint_bytes).hexdigest(),
        )
        preflight_identity = (
            preflight.entrypoint_device,
            preflight.entrypoint_inode,
            preflight.entrypoint_size,
            preflight.entrypoint_mtime_ns,
            preflight.entrypoint_sha256,
        )
        if current_identity != preflight_identity:
            raise RuntimeError("entrypoint identity changed after preflight")
        with tempfile.TemporaryDirectory(
            prefix="tool-system-p13-worker-", dir=preflight.workspace_root
        ) as temporary:
            workspace_path = Path(temporary)
            worker_path = workspace_path / "worker.py"
            guard_path = workspace_path / "guard.py"
            worker_path.write_bytes(entrypoint_bytes)
            worker_path.chmod(0o400)
            stdlib_paths = preflight.readable_library_roots
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
            try:
                process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                pass
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
        writes_target_repo=request.writes_target_repo,
        executes_target_repo_mutation=request.executes_target_repo_mutation,
        production=request.production,
    )


def required_resource_limit_names() -> tuple[str, ...]:
    return _RESOURCE_NAMES
