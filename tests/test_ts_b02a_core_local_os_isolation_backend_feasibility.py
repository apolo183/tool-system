from __future__ import annotations

import ctypes
import errno
import fcntl
import hashlib
import json
import os
import platform
import selectors
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path


NOT_EXECUTED = "NOT_EXECUTED"
CAPABILITY_PASS = "HOSTED_CAPABILITY_PASS"
RESULT_PREFIX = "TS_B02A_HOSTED_PROBE_RESULT="
CGROUP_ROOT = Path("/sys/fs/cgroup")
COMBINED_STREAM_LIMIT = 16_384
PER_STREAM_LIMIT = 12_288
HELPER_WALL_SECONDS = 90
POLL_INTERVAL_SECONDS = 0.02

CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_REMOUNT = 32
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18
MNT_DETACH = 2
AT_FDCWD = -100
AT_EMPTY_PATH = 0x1000
O_PATH = 0o10000000
RESOLVE_NO_XDEV = 0x01
RESOLVE_NO_MAGICLINKS = 0x02
RESOLVE_NO_SYMLINKS = 0x04
RESOLVE_BENEATH = 0x08
SYS_PIVOT_ROOT_X86_64 = 155
SYS_EXECVEAT_X86_64 = 322
SYS_OPENAT2_X86_64 = 437
PTRACE_TRACEME = 0
PTRACE_CONT = 7
PTRACE_SETOPTIONS = 0x4200
PTRACE_O_TRACEEXEC = 0x10
PTRACE_EVENT_EXEC = 4
PR_SET_NO_NEW_PRIVS = 38
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_ALLOW = 0x7FFF0000
AUDIT_ARCH_X86_64 = 0xC000003E
__NR_SOCKET_X86_64 = 41

libc = ctypes.CDLL(None, use_errno=True)


class OpenHow(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("mode", ctypes.c_uint64),
        ("resolve", ctypes.c_uint64),
    ]


class SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class SockFprog(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_ushort),
        ("filter", ctypes.POINTER(SockFilter)),
    ]


def _raise_errno(operation: str) -> None:
    value = ctypes.get_errno()
    raise OSError(value, f"{operation}: {os.strerror(value)}")


def _mount(
    source: str | None,
    target: Path | str,
    fs_type: str | None,
    flags: int,
    data: str | None = None,
) -> None:
    result = libc.mount(
        source.encode() if source is not None else None,
        os.fsencode(target),
        fs_type.encode() if fs_type is not None else None,
        ctypes.c_ulong(flags),
        data.encode() if data is not None else None,
    )
    if result != 0:
        _raise_errno(f"mount({target})")


def _umount(target: Path | str, flags: int = 0) -> None:
    if libc.umount2(os.fsencode(target), flags) != 0:
        _raise_errno(f"umount2({target})")


def _sys_openat2(dirfd: int, path: str, *, resolve: int) -> int:
    how = OpenHow(flags=os.O_RDONLY, mode=0, resolve=resolve)
    fd = libc.syscall(
        SYS_OPENAT2_X86_64,
        dirfd,
        path.encode(),
        ctypes.byref(how),
        ctypes.sizeof(how),
    )
    if fd < 0:
        _raise_errno(f"openat2({path})")
    return int(fd)


def _execveat(fd: int, argv: list[str], environment: dict[str, str]) -> None:
    encoded_argv = [item.encode() for item in argv]
    encoded_env = [f"{key}={value}".encode() for key, value in environment.items()]
    argv_array = (ctypes.c_char_p * (len(encoded_argv) + 1))(
        *encoded_argv, None
    )
    env_array = (ctypes.c_char_p * (len(encoded_env) + 1))(*encoded_env, None)
    result = libc.syscall(
        SYS_EXECVEAT_X86_64,
        fd,
        ctypes.c_char_p(b""),
        argv_array,
        env_array,
        AT_EMPTY_PATH,
    )
    if result != 0:
        _raise_errno("execveat")


def _sha256_fd(fd: int) -> str:
    position = os.lseek(fd, 0, os.SEEK_CUR)
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while True:
        chunk = os.read(fd, 65_536)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(fd, position, os.SEEK_SET)
    return digest.hexdigest()


def _identity(fd: int) -> dict[str, int | str]:
    value = os.fstat(fd)
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "size": value.st_size,
        "sha256": _sha256_fd(fd),
    }


def _read_pt_interp(fd: int) -> str:
    position = os.lseek(fd, 0, os.SEEK_CUR)
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        header = os.read(fd, 64)
        if len(header) != 64 or header[:4] != b"\x7fELF" or header[4] != 2:
            raise AssertionError("fixture is not ELF64")
        endian = "<" if header[5] == 1 else ">"
        phoff = struct.unpack_from(endian + "Q", header, 32)[0]
        phentsize = struct.unpack_from(endian + "H", header, 54)[0]
        phnum = struct.unpack_from(endian + "H", header, 56)[0]
        for index in range(phnum):
            os.lseek(fd, phoff + index * phentsize, os.SEEK_SET)
            program = os.read(fd, phentsize)
            if len(program) < 56:
                raise AssertionError("truncated ELF program header")
            p_type = struct.unpack_from(endian + "I", program, 0)[0]
            if p_type != 3:
                continue
            offset = struct.unpack_from(endian + "Q", program, 8)[0]
            size = struct.unpack_from(endian + "Q", program, 32)[0]
            os.lseek(fd, offset, os.SEEK_SET)
            return os.read(fd, size).split(b"\0", 1)[0].decode("utf-8")
        raise AssertionError("ELF fixture has no PT_INTERP")
    finally:
        os.lseek(fd, position, os.SEEK_SET)


def _namespace_links(pid: str = "self") -> dict[str, str]:
    return {
        name: os.readlink(f"/proc/{pid}/ns/{name}")
        for name in ("mnt", "pid", "net", "ipc", "uts")
    }


def _wait_until(predicate, deadline: float, description: str) -> None:
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(f"deadline expired: {description}")


def _cgroup_populated(path: Path) -> int:
    rows = dict(
        line.split(maxsplit=1)
        for line in (path / "cgroup.events").read_text(encoding="utf-8").splitlines()
    )
    return int(rows["populated"])


def _safe_cgroup_path(execution_id: str, suffix: str = "") -> Path:
    if not execution_id.startswith("ts-b02a-") or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for character in execution_id
    ):
        raise AssertionError("unsafe execution id")
    base = CGROUP_ROOT / execution_id
    path = base if not suffix else base / suffix
    if path.parent not in {CGROUP_ROOT, base}:
        raise AssertionError("cgroup path escaped root")
    return path


def _kill_and_remove_cgroup(path: Path, failures: list[str]) -> None:
    if not path.exists():
        return
    try:
        kill_path = path / "cgroup.kill"
        if kill_path.exists():
            kill_path.write_text("1", encoding="ascii")
        _wait_until(
            lambda: _cgroup_populated(path) == 0,
            time.monotonic() + 8,
            f"{path} populated=0",
        )
    except BaseException as exc:  # cleanup failure must survive the original error
        failures.append(f"cgroup cleanup {path}: {exc!r}")
    try:
        if path.exists():
            path.rmdir()
    except FileNotFoundError:
        pass
    except BaseException as exc:
        failures.append(f"cgroup removal {path}: {exc!r}")


def _compile_fixture(temp_root: Path) -> Path:
    source = temp_root / "synthetic_fixture.c"
    binary = temp_root / "synthetic_fixture"
    source.write_text(
        r'''
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

int main(void) {
    const char *blocked = getenv("TS_B02A_BLOCKED_FD");
    int blocked_fd = blocked ? atoi(blocked) : -1;
    const int domains[] = {AF_INET, AF_INET6, AF_NETLINK, AF_PACKET};
    if (getuid() == 0 || getgid() == 0) return 21;
    if (blocked_fd < 0 || fcntl(blocked_fd, F_GETFD) != -1 || errno != EBADF) return 22;
    for (unsigned long index = 0; index < sizeof(domains) / sizeof(domains[0]); index++) {
        errno = 0;
        if (socket(domains[index], SOCK_STREAM, 0) != -1 || errno != EPERM) return 23 + (int)index;
    }
    if (write(STDOUT_FILENO, "NATIVE_SEALED_OK\n", 17) != 17) return 24;
    if (write(STDERR_FILENO, "NETWORK_DENIED_OK\n", 18) != 18) return 25;
    return 0;
}
'''.lstrip(),
        encoding="utf-8",
    )
    compiler = Path("/usr/bin/cc")
    if not compiler.is_file():
        raise AssertionError("/usr/bin/cc is unavailable")
    completed = subprocess.run(
        [str(compiler), "-O2", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "synthetic ELF compilation failed: "
            + completed.stderr.decode("utf-8", "replace")
        )
    return binary


def _install_socket_seccomp() -> None:
    # BPF: reject a non-x86_64 ABI, return EPERM for socket(2), allow otherwise.
    instructions = (SockFilter * 7)(
        SockFilter(0x20, 0, 0, 4),
        SockFilter(0x15, 1, 0, AUDIT_ARCH_X86_64),
        SockFilter(0x06, 0, 0, SECCOMP_RET_KILL_PROCESS),
        SockFilter(0x20, 0, 0, 0),
        SockFilter(0x15, 0, 1, __NR_SOCKET_X86_64),
        SockFilter(0x06, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM),
        SockFilter(0x06, 0, 0, SECCOMP_RET_ALLOW),
    )
    program = SockFprog(len=len(instructions), filter=instructions)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        _raise_errno("prctl(PR_SET_NO_NEW_PRIVS)")
    if libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(program)) != 0:
        _raise_errno("prctl(PR_SET_SECCOMP)")


def _drop_privileges_and_close_fds(keep: set[int]) -> None:
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    descriptors = [
        int(entry.name)
        for entry in Path("/proc/self/fd").iterdir()
        if entry.name.isdigit()
    ]
    for fd in descriptors:
        if fd > 2 and fd not in keep:
            try:
                os.close(fd)
            except OSError:
                pass
    _install_socket_seccomp()


def _loader_observed(pid: int, expected: os.stat_result) -> bool:
    expected_device = f"{os.major(expected.st_dev):02x}:{os.minor(expected.st_dev):02x}"
    for line in Path(f"/proc/{pid}/maps").read_text(encoding="utf-8").splitlines():
        columns = line.split(maxsplit=5)
        if len(columns) < 5:
            continue
        if columns[3] == expected_device and int(columns[4]) == expected.st_ino:
            return True
    return False


def _status_at_exec(pid: int) -> dict[str, str]:
    return {
        line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines()
        if ":" in line
    }


def _ptraced_exec(
    executable_fd: int,
    argv: list[str],
    environment: dict[str, str],
    expected_loader: os.stat_result,
    blocked_socket_fd: int,
) -> dict[str, object]:
    expected_executable = os.fstat(executable_fd)
    child = os.fork()
    if child == 0:
        try:
            if libc.ptrace(PTRACE_TRACEME, 0, None, None) != 0:
                _raise_errno("ptrace(TRACEME)")
            os.kill(os.getpid(), signal.SIGSTOP)
            _drop_privileges_and_close_fds({executable_fd})
            environment = dict(environment)
            environment["TS_B02A_BLOCKED_FD"] = str(blocked_socket_fd)
            _execveat(executable_fd, argv, environment)
        except BaseException:
            os._exit(126)
        os._exit(127)

    first_pid, first_status = os.waitpid(child, 0)
    if first_pid != child or not os.WIFSTOPPED(first_status):
        raise AssertionError("ptrace child did not enter initial stop")
    if libc.ptrace(PTRACE_SETOPTIONS, child, None, PTRACE_O_TRACEEXEC) != 0:
        _raise_errno("ptrace(SETOPTIONS)")
    if libc.ptrace(PTRACE_CONT, child, None, None) != 0:
        _raise_errno("ptrace(CONT)")

    deadline = time.monotonic() + 8
    exec_observation: dict[str, object] | None = None
    exit_code: int | None = None
    while time.monotonic() < deadline:
        waited_pid, status = os.waitpid(child, 0)
        if waited_pid != child:
            continue
        if os.WIFEXITED(status):
            exit_code = os.WEXITSTATUS(status)
            break
        if os.WIFSIGNALED(status):
            raise AssertionError(f"ptraced child signaled: {os.WTERMSIG(status)}")
        if not os.WIFSTOPPED(status):
            continue
        event = status >> 16
        if event == PTRACE_EVENT_EXEC:
            actual_executable = os.stat(f"/proc/{child}/exe")
            status_rows = _status_at_exec(child)
            exec_observation = {
                "event": event,
                "exe_identity_match": (
                    actual_executable.st_dev == expected_executable.st_dev
                    and actual_executable.st_ino == expected_executable.st_ino
                ),
                "loader_identity_match": _loader_observed(
                    child, expected_loader
                ),
                "uid_non_root": not status_rows["Uid"].startswith("0\t"),
                "gid_non_root": not status_rows["Gid"].startswith("0\t"),
                "cap_eff_zero": int(status_rows["CapEff"], 16) == 0,
                "no_new_privs": status_rows["NoNewPrivs"] == "1",
            }
        if libc.ptrace(PTRACE_CONT, child, None, None) != 0:
            _raise_errno("ptrace(CONT after stop)")
    if exit_code is None:
        os.kill(child, signal.SIGKILL)
        os.waitpid(child, 0)
        raise AssertionError("ptraced child exceeded deadline")
    if exec_observation is None:
        raise AssertionError("PTRACE_EVENT_EXEC observation missing")
    exec_observation["exit_code"] = exit_code
    return exec_observation


def _probe_openat2(root: Path) -> dict[str, object]:
    boundary = root / "openat2-boundary"
    boundary.mkdir()
    (boundary / "inside").write_bytes(b"inside")
    (boundary / "outside-link").symlink_to("/etc/passwd")
    (boundary / "magic-link").symlink_to("/proc/self/fd/0")
    (boundary / "mounted").mkdir()
    _mount("tmpfs", boundary / "mounted", "tmpfs", MS_NOSUID | MS_NODEV, "size=4096")
    root_fd = os.open(boundary, O_PATH | os.O_DIRECTORY)
    resolution = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS | RESOLVE_NO_XDEV
    denied: dict[str, int] = {}
    magiclink_only_denied = False
    try:
        fd = _sys_openat2(root_fd, "inside", resolve=resolution)
        try:
            positive = os.read(fd, 6) == b"inside"
        finally:
            os.close(fd)
        for label, candidate in (
            ("traversal", "../etc/passwd"),
            ("symlink", "outside-link"),
            ("xdev", "mounted"),
        ):
            try:
                escaped = _sys_openat2(root_fd, candidate, resolve=resolution)
            except OSError as exc:
                if exc.errno not in {errno.EXDEV, errno.ELOOP}:
                    raise
                denied[label] = exc.errno
            else:
                os.close(escaped)
                raise AssertionError(f"openat2 {label} was not denied")
        proc_fd = os.open("/proc", O_PATH | os.O_DIRECTORY)
        try:
            try:
                magic = _sys_openat2(
                    proc_fd,
                    "self/fd/0",
                    resolve=RESOLVE_NO_MAGICLINKS,
                )
            except OSError as exc:
                if exc.errno != errno.ELOOP:
                    raise
                magiclink_only_denied = True
            else:
                os.close(magic)
                raise AssertionError("openat2 real procfs magic link was not denied")
        finally:
            os.close(proc_fd)
        return {
            "positive": positive,
            "denied": denied,
            "magiclink_only_denied": magiclink_only_denied,
        }
    finally:
        os.close(root_fd)
        _umount(boundary / "mounted")


def _probe_tmpfs_quotas(root: Path) -> dict[str, object]:
    byte_root = root / "tmpfs-bytes"
    inode_root = root / "tmpfs-inodes"
    byte_root.mkdir()
    inode_root.mkdir()
    byte_enospc = False
    inode_enospc = False
    try:
        _mount("tmpfs", byte_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=65536,nr_inodes=1024")
        try:
            fd = os.open(byte_root / "payload", os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                for _ in range(256):
                    try:
                        os.write(fd, b"x" * 4096)
                    except OSError as exc:
                        if exc.errno != errno.ENOSPC:
                            raise
                        byte_enospc = True
                        break
            finally:
                os.close(fd)
        finally:
            _umount(byte_root)

        _mount("tmpfs", inode_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=1048576,nr_inodes=16")
        try:
            for index in range(128):
                try:
                    fd = os.open(inode_root / f"f-{index}", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except OSError as exc:
                    if exc.errno != errno.ENOSPC:
                        raise
                    inode_enospc = True
                    break
                else:
                    os.close(fd)
        finally:
            _umount(inode_root)
    finally:
        shutil.rmtree(byte_root, ignore_errors=True)
        shutil.rmtree(inode_root, ignore_errors=True)
    return {"byte_enospc": byte_enospc, "inode_enospc": inode_enospc}


def _probe_loopback_control() -> dict[str, object]:
    ip = Path("/usr/sbin/ip")
    if not ip.is_file():
        ip = Path("/usr/bin/ip")
    if not ip.is_file():
        raise AssertionError("iproute2 ip command unavailable")
    subprocess.run([str(ip), "link", "set", "lo", "up"], check=True, timeout=5)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    accepted: socket.socket | None = None
    positive = False
    inherited_fd = -1
    try:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        client.connect(server.getsockname())
        accepted, _ = server.accept()
        client.sendall(b"p")
        positive = accepted.recv(1) == b"p"
        inherited_fd = os.dup(client.fileno())
    finally:
        if accepted is not None:
            accepted.close()
        client.close()
        server.close()
        subprocess.run([str(ip), "link", "set", "lo", "down"], check=True, timeout=5)
    state = Path("/sys/class/net/lo/operstate").read_text(encoding="ascii").strip()
    if state != "down":
        raise AssertionError(f"loopback did not become down: {state}")
    connect_denied = False
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.2)
    try:
        try:
            probe.connect(("127.0.0.1", 9))
        except OSError:
            connect_denied = True
    finally:
        probe.close()
    return {
        "positive_control": positive,
        "loopback_state": state,
        "connectivity_denied": connect_denied,
        "inherited_fd": inherited_fd,
    }


def _make_detached_descendant() -> dict[str, object]:
    read_fd, write_fd = os.pipe()
    first = os.fork()
    if first == 0:
        os.close(read_fd)
        os.setsid()
        second = os.fork()
        if second == 0:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            cgroup_membership = Path("/proc/self/cgroup").read_text(encoding="utf-8").strip()
            os.write(
                write_fd,
                json.dumps(
                    {
                        "namespace_pid": os.getpid(),
                        "cgroup_membership": cgroup_membership,
                    },
                    sort_keys=True,
                ).encode("utf-8"),
            )
            os.close(write_fd)
            while True:
                signal.pause()
        os._exit(0)
    os.close(write_fd)
    os.waitpid(first, 0)
    value = os.read(read_fd, 4096)
    os.close(read_fd)
    return json.loads(value)


def _inside_namespace(execution_id: str, temp_root: Path, report_fd: int, parent_ns_json: str) -> None:
    failures: list[str] = []
    result: dict[str, object] = {"execution_id": execution_id}
    open_fds: list[int] = []
    try:
        current_ns = _namespace_links()
        parent_ns = json.loads(parent_ns_json)
        result["namespace_ids"] = current_ns
        result["namespaces_distinct"] = all(
            current_ns[name] != parent_ns[name] for name in current_ns
        )
        _mount(None, "/", None, MS_REC | MS_PRIVATE)
        root_mount_line = next(
            line for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
            if line.split()[4] == "/"
        )
        optional = root_mount_line.split(" - ", 1)[0].split()[6:]
        result["private_mount_propagation"] = not any(
            field.startswith(("shared:", "master:", "propagate_from:"))
            for field in optional
        )

        result["openat2"] = _probe_openat2(temp_root)
        result["tmpfs_quota"] = _probe_tmpfs_quotas(temp_root)
        network = _probe_loopback_control()
        inherited_fd = int(network.pop("inherited_fd"))
        open_fds.append(inherited_fd)
        result["network"] = network

        compiled = _compile_fixture(temp_root)
        new_root = temp_root / "private-root"
        new_root.mkdir()
        _mount("tmpfs", new_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=8388608,nr_inodes=512,mode=0755")
        for directory in ("usr", "proc", "fixtures", "scratch", "old-root"):
            (new_root / directory).mkdir()
        _mount("/usr", new_root / "usr", None, MS_BIND | MS_REC)
        _mount(None, new_root / "usr", None, MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV)
        for name, target in (("bin", "usr/bin"), ("lib", "usr/lib"), ("lib64", "usr/lib64"), ("sbin", "usr/sbin")):
            (new_root / name).symlink_to(target)
        _mount("tmpfs", new_root / "scratch", "tmpfs", MS_NOSUID | MS_NODEV, "size=1048576,nr_inodes=64,mode=0700")

        selected = new_root / "fixtures" / "selected-elf"
        shutil.copy2(compiled, selected)
        selected.chmod(0o755)
        sealed_fd = os.open(selected, os.O_RDONLY)
        open_fds.append(sealed_fd)
        selected_identity = _identity(sealed_fd)
        selected.unlink()
        shutil.copy2("/usr/bin/false", selected)
        selected.chmod(0o755)
        result["path_swap_digest_differs"] = (
            hashlib.sha256(selected.read_bytes()).hexdigest()
            != selected_identity["sha256"]
        )

        script_path = new_root / "fixtures" / "sealed-script"
        script_path.write_text("#!/bin/sh\nprintf 'SCRIPT_INTERPRETER_OK\\n'\n", encoding="utf-8")
        script_path.chmod(0o555)
        script_fd = os.open(script_path, os.O_RDONLY)
        open_fds.append(script_fd)
        script_identity = _identity(script_fd)
        if not os.read(script_fd, 10).startswith(b"#!/bin/sh"):
            raise AssertionError("synthetic shebang parse failed")
        os.lseek(script_fd, 0, os.SEEK_SET)

        _mount(str(new_root / "fixtures"), new_root / "fixtures", None, MS_BIND)
        _mount(None, new_root / "fixtures", None, MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV)

        if libc.syscall(SYS_PIVOT_ROOT_X86_64, os.fsencode(new_root), os.fsencode(new_root / "old-root")) != 0:
            _raise_errno("pivot_root")
        os.chdir("/")
        _umount("/old-root", MNT_DETACH)
        Path("/old-root").rmdir()
        _mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV, None)
        result["pivot_root_old_root_hidden"] = not Path(str(temp_root / "host-sentinel")).exists()
        result["private_root_device"] = os.stat("/").st_dev
        result["scratch_quota_mount"] = Path("/scratch").is_dir()

        native_loader = _read_pt_interp(sealed_fd)
        loader_fd = os.open(native_loader, os.O_RDONLY)
        open_fds.append(loader_fd)
        loader_identity = _identity(loader_fd)
        loader_stat = os.fstat(loader_fd)
        result["native"] = _ptraced_exec(
            sealed_fd,
            ["/fixtures/selected-elf"],
            {"PATH": "/usr/bin", "LANG": "C"},
            loader_stat,
            inherited_fd,
        )

        interpreter_fd = os.open("/bin/sh", os.O_RDONLY)
        open_fds.append(interpreter_fd)
        interpreter_identity = _identity(interpreter_fd)
        interpreter_loader = _read_pt_interp(interpreter_fd)
        interpreter_loader_fd = os.open(interpreter_loader, os.O_RDONLY)
        open_fds.append(interpreter_loader_fd)
        interpreter_observation = _ptraced_exec(
            interpreter_fd,
            ["/bin/sh", "/fixtures/sealed-script"],
            {"PATH": "/usr/bin", "LANG": "C"},
            os.fstat(interpreter_loader_fd),
            inherited_fd,
        )
        interpreter_observation["script_identity_match"] = (
            os.fstat(script_fd).st_dev == os.stat("/fixtures/sealed-script").st_dev
            and os.fstat(script_fd).st_ino == os.stat("/fixtures/sealed-script").st_ino
            and _sha256_fd(script_fd) == script_identity["sha256"]
        )
        result["interpreter"] = interpreter_observation
        result["sealed_identities"] = {
            "native": selected_identity,
            "script": script_identity,
            "interpreter": interpreter_identity,
            "loader": loader_identity,
        }
        result["detached_descendant"] = _make_detached_descendant()
        result["ready"] = True
    except BaseException as exc:
        failures.append(repr(exc))
    result["failures"] = failures
    payload = json.dumps(result, sort_keys=True).encode("utf-8")
    os.write(report_fd, payload)
    os.fsync(report_fd)
    os.close(report_fd)
    for fd in open_fds:
        try:
            os.close(fd)
        except OSError:
            pass
    if failures:
        os._exit(120)
    for _ in range(8):
        os.write(1, b"O" * 4096)
        os.write(2, b"E" * 4096)
    while True:
        signal.pause()


def _spawn_gated(
    argv: list[str],
    cgroup: Path,
    *,
    stdout,
    stderr,
    extra_fds: tuple[int, ...] = (),
) -> tuple[subprocess.Popen[bytes], int]:
    if not (cgroup / "cgroup.kill").is_file() or not (cgroup / "cgroup.events").is_file():
        raise AssertionError("cgroup kill/events capability missing before workload gate")
    if _cgroup_populated(cgroup) != 0:
        raise AssertionError("new cgroup was populated before workload gate")
    read_gate, write_gate = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "--gate-exec",
            str(read_gate),
            json.dumps(argv),
        ],
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        close_fds=True,
        pass_fds=(read_gate, *extra_fds),
    )
    os.close(read_gate)
    try:
        (cgroup / "cgroup.procs").write_text(str(process.pid), encoding="ascii")
        pidfd = os.pidfd_open(process.pid)
        os.write(write_gate, b"g")
        return process, pidfd
    except BaseException:
        os.close(write_gate)
        process.kill()
        process.wait(timeout=2)
        raise
    finally:
        try:
            os.close(write_gate)
        except OSError:
            pass


def _drain_until_limit(
    process: subprocess.Popen[bytes],
    deadline: float,
    *,
    per_stream_limit: int = PER_STREAM_LIMIT,
    combined_stream_limit: int = COMBINED_STREAM_LIMIT,
    retained_combined_limit: int = COMBINED_STREAM_LIMIT,
) -> dict[str, object]:
    selector = selectors.DefaultSelector()
    emitted = {"stdout": 0, "stderr": 0}
    retained = {"stdout": bytearray(), "stderr": bytearray()}
    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        if stream is None:
            raise AssertionError(f"missing {name} pipe")
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)
    trigger = None
    while selector.get_map() and time.monotonic() < deadline:
        for key, _ in selector.select(timeout=POLL_INTERVAL_SECONDS):
            chunk = os.read(key.fileobj.fileno(), 4096)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            name = key.data
            emitted[name] += len(chunk)
            stream_room = max(0, per_stream_limit - len(retained[name]))
            combined_room = max(
                0,
                retained_combined_limit
                - sum(len(value) for value in retained.values()),
            )
            keep = min(len(chunk), stream_room, combined_room)
            retained[name].extend(chunk[:keep])
            if emitted[name] > per_stream_limit:
                trigger = f"{name}_raw_stream_limit"
                break
            if sum(emitted.values()) > combined_stream_limit:
                trigger = "combined_raw_stream_limit"
                break
        if trigger:
            break
    selector.close()
    return {
        "trigger": trigger,
        "emitted": emitted,
        "retained": {key: len(value) for key, value in retained.items()},
        "discarded": {
            key: emitted[key] - len(retained[key]) for key in emitted
        },
    }


def _scan_for_residue(temp_root: Path, namespace_links: dict[str, str]) -> list[str]:
    findings: list[str] = []
    target = str(temp_root)
    namespace_values = set(namespace_links.values())
    for proc in Path("/proc").glob("[0-9]*"):
        for name in ("cwd", "root"):
            try:
                link = os.readlink(proc / name)
            except OSError:
                continue
            if link.startswith(target):
                findings.append(f"{proc.name}/{name}->{link}")
        for directory in ("fd", "ns"):
            try:
                entries = list((proc / directory).iterdir())
            except OSError:
                continue
            for entry in entries:
                try:
                    link = os.readlink(entry)
                except OSError:
                    continue
                if link.startswith(target) or link in namespace_values:
                    findings.append(f"{proc.name}/{directory}/{entry.name}->{link}")
    return findings[:32]


def _host_mounts_under(temp_root: Path) -> list[Path]:
    prefix = str(temp_root.resolve()) + "/"
    mounts: list[Path] = []
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        mount_point = line.split()[4].replace("\\040", " ")
        if mount_point == str(temp_root) or mount_point.startswith(prefix):
            mounts.append(Path(mount_point))
    return sorted(mounts, key=lambda value: len(value.parts), reverse=True)


def _unmount_then_remove_temp_root(temp_root: Path, failures: list[str]) -> None:
    for mount_point in _host_mounts_under(temp_root):
        try:
            _umount(mount_point, MNT_DETACH)
        except BaseException as exc:
            failures.append(f"host mount cleanup {mount_point}: {exc!r}")
    remaining = _host_mounts_under(temp_root)
    if remaining:
        failures.append(f"host mounts remain; recursive deletion suppressed: {remaining}")
        return
    if temp_root.exists():
        try:
            shutil.rmtree(temp_root, ignore_errors=False)
        except BaseException as exc:
            failures.append(f"temporary-root removal: {exc!r}")


def _run_timeout_probe(execution_id: str, path: Path) -> dict[str, object]:
    path.mkdir()
    failures: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    pidfd = -1
    started = time.monotonic()
    try:
        process, pidfd = _spawn_gated(
            ["/usr/bin/sleep", "30"], path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        deadline = started + 0.35
        _wait_until(lambda: time.monotonic() >= deadline, deadline + 0.2, "monotonic timeout")
        (path / "cgroup.kill").write_text("1", encoding="ascii")
        _wait_until(lambda: _cgroup_populated(path) == 0, time.monotonic() + 5, "timeout cgroup empty")
        poller = selectors.DefaultSelector()
        poller.register(pidfd, selectors.EVENT_READ)
        readable = bool(poller.select(timeout=2))
        poller.close()
        process.wait(timeout=2)
        return {
            "trigger": "monotonic_timeout",
            "elapsed_seconds": time.monotonic() - started,
            "pidfd_exit_observed": readable,
            "populated_zero": _cgroup_populated(path) == 0,
        }
    finally:
        if pidfd >= 0:
            os.close(pidfd)
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=2)
        _kill_and_remove_cgroup(path, failures)
        if failures:
            raise AssertionError(failures)


def _run_combined_stream_probe(path: Path) -> dict[str, object]:
    path.mkdir()
    failures: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    pidfd = -1
    try:
        command = [
            sys.executable,
            "-I",
            "-c",
            "import os; [(os.write(1,b'O'*4096),os.write(2,b'E'*4096)) for _ in range(8)]",
        ]
        process, pidfd = _spawn_gated(
            command,
            path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = _drain_until_limit(
            process,
            time.monotonic() + 8,
            per_stream_limit=PER_STREAM_LIMIT * 4,
            combined_stream_limit=COMBINED_STREAM_LIMIT,
        )
        (path / "cgroup.kill").write_text("1", encoding="ascii")
        _wait_until(
            lambda: _cgroup_populated(path) == 0,
            time.monotonic() + 5,
            "combined stream cgroup empty",
        )
        remaining_stdout, remaining_stderr = process.communicate(timeout=3)
        for name, remaining in (("stdout", remaining_stdout), ("stderr", remaining_stderr)):
            result["emitted"][name] += len(remaining)
            result["discarded"][name] += len(remaining)
        return result
    finally:
        if pidfd >= 0:
            os.close(pidfd)
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=2)
        _kill_and_remove_cgroup(path, failures)
        if failures:
            raise AssertionError(failures)


def _root_probe(execution_id: str, temp_root: Path, source_file: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise AssertionError("root helper is not root")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise AssertionError("root helper requires Linux x86_64")
    if not (CGROUP_ROOT / "cgroup.controllers").is_file():
        raise AssertionError("unified cgroup v2 is unavailable")
    unshare = Path("/usr/bin/unshare")
    if not unshare.is_file():
        raise AssertionError("/usr/bin/unshare is unavailable")
    if temp_root.parent.resolve() == Path("/") or not temp_root.name.startswith("ts-b02a-"):
        raise AssertionError("unsafe temporary root")

    parent_cgroup = _safe_cgroup_path(execution_id)
    composition_cgroup = _safe_cgroup_path(execution_id, "composition")
    timeout_cgroup = _safe_cgroup_path(execution_id, "timeout")
    combined_stream_cgroup = _safe_cgroup_path(execution_id, "combined-stream")
    cleanup_failures: list[str] = []
    probe_failures: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    process_pidfd = -1
    report: dict[str, object] = {}
    streams: dict[str, object] = {}
    timeout_result: dict[str, object] = {}
    combined_stream_result: dict[str, object] = {}
    parent_ns = _namespace_links()
    temp_root.mkdir(mode=0o700)
    (temp_root / "host-sentinel").write_text("host-only", encoding="utf-8")
    report_path = temp_root / "inside-report.json"
    report_fd = os.open(report_path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
    os.set_inheritable(report_fd, True)
    try:
        parent_cgroup.mkdir()
        composition_cgroup.mkdir()
        command = [
            str(unshare),
            "--mount",
            "--pid",
            "--net",
            "--ipc",
            "--uts",
            "--fork",
            "--kill-child=KILL",
            str(sys.executable),
            "-I",
            str(source_file),
            "--inside-namespace",
            execution_id,
            str(temp_root),
            str(report_fd),
            json.dumps(parent_ns, sort_keys=True),
        ]
        process, process_pidfd = _spawn_gated(
            command,
            composition_cgroup,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            extra_fds=(report_fd,),
        )
        def report_is_complete() -> bool:
            try:
                json.loads(report_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
                return False
            return True

        _wait_until(
            report_is_complete,
            time.monotonic() + 35,
            "inside compositional report",
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("failures"):
            probe_failures.extend(str(item) for item in report["failures"])
        descendant = report.get("detached_descendant")
        if not isinstance(descendant, dict):
            probe_failures.append("detached descendant identity observation missing")
        else:
            expected_cgroup_suffix = f"/{execution_id}/composition"
            if not str(descendant.get("cgroup_membership", "")).endswith(
                expected_cgroup_suffix
            ):
                probe_failures.append(
                    f"detached descendant escaped cgroup: {descendant}"
                )
            namespace_pid = int(descendant.get("namespace_pid", 0))
            host_descendants = []
            for candidate in Path("/proc").glob("[0-9]*"):
                try:
                    status_rows = _status_at_exec(int(candidate.name))
                    nspid = [int(item) for item in status_rows["NSpid"].split()]
                    cgroup_rows = (candidate / "cgroup").read_text(
                        encoding="utf-8"
                    )
                except (OSError, KeyError, ValueError):
                    continue
                if (
                    nspid
                    and nspid[-1] == namespace_pid
                    and cgroup_rows.strip().endswith(expected_cgroup_suffix)
                ):
                    host_descendants.append(int(candidate.name))
            if len(host_descendants) != 1:
                probe_failures.append(
                    f"detached descendant host PID mapping not unique: {host_descendants}"
                )
            else:
                detached_host_pid = host_descendants[0]
                os.kill(detached_host_pid, signal.SIGTERM)
                time.sleep(0.05)
                try:
                    os.kill(detached_host_pid, 0)
                except ProcessLookupError:
                    probe_failures.append(
                        "TERM-ignore detached descendant positive control failed"
                    )
                if detached_host_pid not in {
                    int(line)
                    for line in (composition_cgroup / "cgroup.procs")
                    .read_text(encoding="ascii")
                    .splitlines()
                    if line
                }:
                    probe_failures.append(
                        "exact detached descendant is not in the composition cgroup"
                    )
        members_before_kill = {
            int(line)
            for line in (composition_cgroup / "cgroup.threads").read_text(encoding="ascii").splitlines()
            if line
        }
        if len(members_before_kill) < 3:
            probe_failures.append(f"complete-tree positive control too small: {members_before_kill}")
        member_pidfds: list[int] = []
        for pid in members_before_kill:
            try:
                member_pidfds.append(os.pidfd_open(pid))
            except ProcessLookupError as exc:
                probe_failures.append(f"pidfd observation lost for cgroup member {pid}: {exc}")
        streams = _drain_until_limit(
            process,
            time.monotonic() + 10,
            per_stream_limit=PER_STREAM_LIMIT,
            combined_stream_limit=PER_STREAM_LIMIT * 4,
        )
        if streams.get("trigger") not in {
            "stdout_raw_stream_limit",
            "stderr_raw_stream_limit",
        }:
            probe_failures.append(f"stream limit did not trigger: {streams}")
        (composition_cgroup / "cgroup.kill").write_text("1", encoding="ascii")
        _wait_until(
            lambda: _cgroup_populated(composition_cgroup) == 0,
            time.monotonic() + 8,
            "composition cgroup populated=0",
        )
        remaining_stdout, remaining_stderr = process.communicate(timeout=5)
        for name, remaining in (
            ("stdout", remaining_stdout),
            ("stderr", remaining_stderr),
        ):
            streams["emitted"][name] += len(remaining)
            streams["discarded"][name] += len(remaining)
        streams["per_stream_breach"] = streams["trigger"]
        combined_stream_result = _run_combined_stream_probe(
            combined_stream_cgroup
        )
        streams["combined_probe"] = combined_stream_result
        poller = selectors.DefaultSelector()
        for fd in member_pidfds:
            poller.register(fd, selectors.EVENT_READ)
        events = poller.select(timeout=2)
        if len(events) != len(member_pidfds):
            probe_failures.append("not every cgroup member exit was pidfd-observed")
        poller.close()
        for fd in member_pidfds:
            os.close(fd)
        if process_pidfd >= 0:
            os.close(process_pidfd)
            process_pidfd = -1
        composition_cgroup.rmdir()
        timeout_result = _run_timeout_probe(execution_id, timeout_cgroup)
    except BaseException as exc:
        probe_failures.append(repr(exc))
    finally:
        try:
            os.close(report_fd)
        except OSError:
            pass
        if process is not None and process.poll() is None:
            _kill_and_remove_cgroup(composition_cgroup, cleanup_failures)
            try:
                process.wait(timeout=3)
            except BaseException as exc:
                cleanup_failures.append(f"composition process wait: {exc!r}")
        if process_pidfd >= 0:
            os.close(process_pidfd)
        _kill_and_remove_cgroup(timeout_cgroup, cleanup_failures)
        _kill_and_remove_cgroup(combined_stream_cgroup, cleanup_failures)
        _kill_and_remove_cgroup(composition_cgroup, cleanup_failures)
        _kill_and_remove_cgroup(parent_cgroup, cleanup_failures)

        namespace_links = report.get("namespace_ids", {})
        if isinstance(namespace_links, dict):
            residue = _scan_for_residue(temp_root, namespace_links)
            if residue:
                cleanup_failures.append(f"process/namespace residue: {residue}")
        escaped_mounts = _host_mounts_under(temp_root)
        if escaped_mounts:
            cleanup_failures.append(
                f"probe mount escaped into host mount namespace: {escaped_mounts}"
            )
        _unmount_then_remove_temp_root(temp_root, cleanup_failures)
        if temp_root.exists():
            cleanup_failures.append("temporary root remains")

    checks = {
        "namespace_set": report.get("namespaces_distinct") is True,
        "private_propagation": report.get("private_mount_propagation") is True,
        "openat2": (
            isinstance(report.get("openat2"), dict)
            and report["openat2"].get("positive") is True
            and set(report["openat2"].get("denied", {})) == {"traversal", "symlink", "xdev"}
            and report["openat2"].get("magiclink_only_denied") is True
        ),
        "quotas": report.get("tmpfs_quota") == {"byte_enospc": True, "inode_enospc": True},
        "network": (
            isinstance(report.get("network"), dict)
            and report["network"].get("positive_control") is True
            and report["network"].get("loopback_state") == "down"
            and report["network"].get("connectivity_denied") is True
        ),
        "pivot_root": report.get("pivot_root_old_root_hidden") is True,
        "path_swap": report.get("path_swap_digest_differs") is True,
        "native_exec": (
            isinstance(report.get("native"), dict)
            and report["native"].get("event") == PTRACE_EVENT_EXEC
            and report["native"].get("exe_identity_match") is True
            and report["native"].get("loader_identity_match") is True
            and report["native"].get("uid_non_root") is True
            and report["native"].get("gid_non_root") is True
            and report["native"].get("cap_eff_zero") is True
            and report["native"].get("no_new_privs") is True
            and report["native"].get("exit_code") == 0
        ),
        "interpreter_exec": (
            isinstance(report.get("interpreter"), dict)
            and report["interpreter"].get("event") == PTRACE_EVENT_EXEC
            and report["interpreter"].get("exe_identity_match") is True
            and report["interpreter"].get("loader_identity_match") is True
            and report["interpreter"].get("script_identity_match") is True
            and report["interpreter"].get("exit_code") == 0
        ),
        "stream_limit": (
            streams.get("trigger") in {"stdout_raw_stream_limit", "stderr_raw_stream_limit"}
            and isinstance(streams.get("combined_probe"), dict)
            and streams["combined_probe"].get("trigger") == "combined_raw_stream_limit"
            and all(streams.get("emitted", {}).get(name, 0) > 0 for name in ("stdout", "stderr"))
            and sum(streams.get("discarded", {}).values()) > 0
            and sum(streams.get("retained", {}).values()) <= COMBINED_STREAM_LIMIT
            and all(
                streams["discarded"][name]
                == streams["emitted"][name] - streams["retained"][name]
                for name in ("stdout", "stderr")
            )
            and all(
                streams["combined_probe"]["discarded"][name]
                == streams["combined_probe"]["emitted"][name]
                - streams["combined_probe"]["retained"][name]
                for name in ("stdout", "stderr")
            )
        ),
        "timeout": (
            timeout_result.get("trigger") == "monotonic_timeout"
            and timeout_result.get("pidfd_exit_observed") is True
            and timeout_result.get("populated_zero") is True
        ),
    }
    for name, passed in checks.items():
        if not passed:
            probe_failures.append(f"capability check failed: {name}")
    if cleanup_failures:
        probe_failures.extend(cleanup_failures)
    return {
        "disposition": CAPABILITY_PASS if not probe_failures else "HOSTED_CAPABILITY_BLOCKER",
        "execution_id": execution_id,
        "checks": checks,
        "streams": streams,
        "timeout": timeout_result,
        "cleanup_complete": not cleanup_failures,
        "failures": probe_failures,
    }


def _root_cleanup(execution_id: str, temp_root: Path) -> dict[str, object]:
    failures: list[str] = []
    for suffix in ("timeout", "combined-stream", "composition", ""):
        _kill_and_remove_cgroup(_safe_cgroup_path(execution_id, suffix), failures)
    _unmount_then_remove_temp_root(temp_root, failures)
    return {"cleanup_complete": not failures and not temp_root.exists(), "failures": failures}


def _root_main(argv: list[str]) -> int:
    mode = argv[1]
    execution_id = argv[2]
    temp_root = Path(argv[3])
    if mode == "--root-probe":
        result = _root_probe(execution_id, temp_root, Path(argv[4]).resolve())
    elif mode == "--root-cleanup":
        result = _root_cleanup(execution_id, temp_root)
    else:
        raise AssertionError(f"unknown root mode: {mode}")
    print(RESULT_PREFIX + json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("cleanup_complete") else 1


def _parse_root_result(stdout: bytes) -> dict[str, object]:
    lines = stdout.decode("utf-8", "replace").splitlines()
    matches = [line[len(RESULT_PREFIX) :] for line in lines if line.startswith(RESULT_PREFIX)]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one root result, got {len(matches)}: {lines[-20:]}")
    return json.loads(matches[0])


def _execute_hosted_capability_test(tmp_path: Path) -> None:
    github_actions = os.environ.get("GITHUB_ACTIONS")
    runner_environment = os.environ.get("RUNNER_ENVIRONMENT")
    if github_actions != "true" or runner_environment == "self-hosted":
        observation = {
            "disposition": NOT_EXECUTED,
            "capability_pass": False,
            "reason": "not running on an identified GitHub-hosted Actions runner",
        }
        print(RESULT_PREFIX + json.dumps(observation, sort_keys=True))
        assert observation["disposition"] == NOT_EXECUTED
        assert observation["capability_pass"] is False
        return

    assert runner_environment == "github-hosted", (
        "GitHub Actions execution without the github-hosted identity is not "
        "eligible for capability PASS"
    )
    assert os.environ.get("RUNNER_OS") == "Linux"
    assert os.environ.get("RUNNER_ARCH") == "X64"
    assert os.environ.get("GITHUB_REPOSITORY") == "apolo183/tool-system"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    assert platform.system() == "Linux"
    assert platform.machine() == "x86_64"

    sudo_gate = subprocess.run(
        ["/usr/bin/sudo", "-n", "--", "/usr/bin/id", "-u"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
    )
    assert sudo_gate.returncode == 0, sudo_gate.stderr.decode("utf-8", "replace")
    assert sudo_gate.stdout == b"0\n"

    execution_id = "ts-b02a-" + uuid.uuid4().hex[:20]
    creator_root = tmp_path / execution_id
    source_file = Path(__file__).resolve()
    command = [
        "/usr/bin/sudo",
        "-n",
        "--",
        sys.executable,
        "-I",
        str(source_file),
        "--root-probe",
        execution_id,
        str(creator_root),
        str(source_file),
    ]
    completed: subprocess.CompletedProcess[bytes] | None = None
    cleanup_result: dict[str, object] = {}
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=HELPER_WALL_SECONDS,
        )
    finally:
        cleanup = subprocess.run(
            [
                "/usr/bin/sudo",
                "-n",
                "--",
                sys.executable,
                "-I",
                str(source_file),
                "--root-cleanup",
                execution_id,
                str(creator_root),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        cleanup_result = _parse_root_result(cleanup.stdout)
        assert cleanup.returncode == 0, cleanup.stderr.decode("utf-8", "replace")
        assert cleanup_result == {"cleanup_complete": True, "failures": []}
        assert not creator_root.exists()

    assert completed is not None
    result = _parse_root_result(completed.stdout)
    diagnostic = {
        "returncode": completed.returncode,
        "result": result,
        "stderr": completed.stderr.decode("utf-8", "replace")[-4000:],
        "outer_cleanup": cleanup_result,
    }
    print(RESULT_PREFIX + json.dumps(diagnostic, sort_keys=True))
    assert completed.returncode == 0, diagnostic
    assert result["disposition"] == CAPABILITY_PASS, diagnostic
    assert result["cleanup_complete"] is True, diagnostic
    assert result["failures"] == [], diagnostic
    assert all(result["checks"].values()), diagnostic
    assert result["streams"]["trigger"] in {
        "stdout_raw_stream_limit",
        "stderr_raw_stream_limit",
    }, diagnostic
    assert result["streams"]["combined_probe"]["trigger"] == "combined_raw_stream_limit", diagnostic
    assert sum(result["streams"]["retained"].values()) <= COMBINED_STREAM_LIMIT
    assert all(
        result["streams"]["retained"][name] <= PER_STREAM_LIMIT
        for name in ("stdout", "stderr")
    )
    assert all(
        result["streams"]["discarded"][name]
        == result["streams"]["emitted"][name] - result["streams"]["retained"][name]
        for name in ("stdout", "stderr")
    )
    assert NOT_EXECUTED not in json.dumps(result)


def test_ts_b02a_core_local_os_isolation_backend_feasibility(tmp_path: Path) -> None:
    try:
        _execute_hosted_capability_test(tmp_path)
    except BaseException as exc:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            blocker = {
                "disposition": "HOSTED_CAPABILITY_BLOCKER",
                "capability_pass": False,
                "failure_type": type(exc).__name__,
                "failure": str(exc)[-4000:],
            }
            print(RESULT_PREFIX + json.dumps(blocker, sort_keys=True), flush=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in {"--root-probe", "--root-cleanup"}:
        raise SystemExit(_root_main(sys.argv))
    if len(sys.argv) == 4 and sys.argv[1] == "--gate-exec":
        gate_fd = int(sys.argv[2])
        gated_argv = json.loads(sys.argv[3])
        if os.read(gate_fd, 1) != b"g":
            raise SystemExit(125)
        os.close(gate_fd)
        os.execv(gated_argv[0], gated_argv)
    if len(sys.argv) == 6 and sys.argv[1] == "--inside-namespace":
        _inside_namespace(
            sys.argv[2],
            Path(sys.argv[3]),
            int(sys.argv[4]),
            sys.argv[5],
        )
        raise SystemExit(0)
