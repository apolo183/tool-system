from __future__ import annotations

import dataclasses
import ctypes
import hashlib
import importlib.util
import json
import mmap
import os
import selectors
import signal
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from tool_system.isolated_execution.contract import (
    CLONE_NAMESPACE_FLAGS_MASK_V1,
    FUTEX_PRIVATE_FLAG_V1,
    NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1,
    SOCKET_DENIAL_FILTER_ROWS_V1,
    SOCKET_DENIAL_FILTER_SHA256_V1,
    SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1,
    canonical_sha256,
    validate_isolation_request_v1,
)
from tool_system.isolated_execution.evidence import (
    EvidenceValidationErrorCodeV1,
    ExecutionOutcomeV1,
    validate_execution_evidence_v1,
)
from tool_system.isolated_execution.linux_backend import (
    CGROUP_ROOT,
    IdentityMismatch,
    InvalidIsolationRequest,
    LinuxNativeSupervisorV1,
    ObservationLoss,
    _PreparedRequest,
    _ReportWriter,
    _RunRecord,
    _inside_path,
    _mark_pass,
    _scan_read_only_tree,
    _scan_residue,
    _seccomp_process_controls,
    _seccomp_socket_control,
    _seccomp_filter_identity,
    _run_prepared,
)


_HELPER_SPEC = importlib.util.spec_from_file_location(
    "ts_b02a_backend_test_helpers",
    Path(__file__).with_name("test_isolated_execution_linux_backend.py"),
)
assert _HELPER_SPEC is not None and _HELPER_SPEC.loader is not None
_HELPERS = importlib.util.module_from_spec(_HELPER_SPEC)
_HELPER_SPEC.loader.exec_module(_HELPERS)

HOSTED_RESULT_PREFIX = "TS_B02A_ADVERSARIAL_HOSTED_RESULT="
ROOT_MARKER = "TS_B02A_ADVERSARIAL_ROOT_TEST"


def test_seccomp_program_identity_is_the_exact_installed_row_set() -> None:
    rows = tuple(SOCKET_DENIAL_FILTER_ROWS_V1)
    assert _seccomp_filter_identity(rows) == SOCKET_DENIAL_FILTER_SHA256_V1
    assert SOCKET_DENIAL_FILTER_SHA256_V1 == canonical_sha256(
        {
            "version": "tool-system-seccomp-cbpf-v1",
            "native_syscall_exclusive_ceiling_x86_64": (
                NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
            ),
            "rows": [list(row) for row in rows],
        }
    )
    denied = {name for name, _ in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1}
    assert {
        "socket",
        "socketpair",
        "clone3",
        "io_setup",
        "io_destroy",
        "io_getevents",
        "io_submit",
        "io_cancel",
        "io_pgetevents",
        "io_uring_setup",
        "add_key",
        "request_key",
        "keyctl",
        "setrlimit",
        "prlimit64",
        "memfd_create",
        "memfd_secret",
        "setxattr",
        "lsetxattr",
        "fsetxattr",
        "removexattr",
        "lremovexattr",
        "fremovexattr",
        "setxattrat",
        "removexattrat",
        "open_tree_attr",
        "file_setattr",
        "flock",
        "sync",
        "syncfs",
        "quotactl",
        "quotactl_fd",
        "perf_event_open",
        "futex_waitv",
        "futex_wake",
        "futex_wait",
        "futex_requeue",
        "membarrier",
        "getpriority",
        "setpriority",
        "ioprio_set",
        "ioprio_get",
    }.issubset(denied)
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00010000  # CLONE_THREAD
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00800000  # CLONE_UNTRACED
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00000100  # CLONE_VM
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00000200  # CLONE_FS
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00000400  # CLONE_FILES
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 & 0x00000800  # CLONE_SIGHAND
    assert FUTEX_PRIVATE_FLAG_V1 == 0x80


def test_private_path_join_rejects_double_slash_and_depth_escape(tmp_path: Path) -> None:
    for candidate in ("//output", "///output", "/a/../b", "/" + "a/" * 65 + "z"):
        try:
            _inside_path(tmp_path, candidate)
        except IdentityMismatch:
            pass
        else:
            raise AssertionError(f"unsafe private path accepted: {candidate!r}")


def test_invalid_typed_request_fails_before_backend_side_effects(tmp_path: Path) -> None:
    binary = _HELPERS._compile_fixture(tmp_path, "int main(void){return 0;}\n")
    request = _HELPERS._request(binary, deadline_seconds=5)
    malformed = dataclasses.replace(request, filesystem=object())
    before_fds = set(os.listdir("/proc/self/fd"))
    before_roots = set(Path("/tmp").glob("tool-system-isolated-execution-*"))
    try:
        LinuxNativeSupervisorV1().execute(malformed)
    except InvalidIsolationRequest:
        pass
    else:
        raise AssertionError("malformed typed request reached the backend")
    assert set(os.listdir("/proc/self/fd")) == before_fds
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == before_roots


def _assert_complete(request, expected: ExecutionOutcomeV1):
    roots_before = set(Path("/tmp").glob("tool-system-isolated-execution-*"))
    validation = validate_isolation_request_v1(request)
    assert validation.ok, validation.reasons
    evidence = LinuxNativeSupervisorV1().execute(request)
    validation = validate_execution_evidence_v1(request, evidence)
    assert evidence.outcome is expected, evidence.to_record()
    assert evidence.complete is True, validation.reasons
    assert validation.ok is True, validation.reasons
    assert evidence.process.cgroup_kill_written is True
    assert evidence.process.populated_before_kill == 1
    assert evidence.process.current_execution_survivor_count == 0
    assert not (CGROUP_ROOT / request.execution_id).exists()
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == roots_before
    return evidence


def _run_prepared_after_source_replacement(
    request,
    replacements: tuple[tuple[Path, Path], ...],
    expected_output: bytes,
) -> _RunRecord:
    """Run the real backend after its selected objects are immutably sealed."""

    roots_before = set(Path("/tmp").glob("tool-system-isolated-execution-*"))
    validation = validate_isolation_request_v1(request)
    assert validation.ok, validation.reasons
    seccomp_controls = _seccomp_socket_control(_seccomp_process_controls())
    prepared = _PreparedRequest.create(request)
    sealed_digests = {
        item.expected.file_type.value: item.sealed_identity["sha256"]
        for item in (prepared.entrypoint, prepared.interpreter, prepared.loader)
        if item is not None
    }
    try:
        for target, replacement in replacements:
            os.replace(replacement, target)
        record = _RunRecord(started_ns=time.monotonic_ns())
        _mark_pass(record, "request.validate")
        _mark_pass(record, "host.gate")
        _mark_pass(record, "identity.seal")
        _run_prepared(prepared, record, seccomp_controls)
    finally:
        prepared.close()
    assert record.workload_exit_code == 0, record.provider_errors
    assert not record.provider_errors and not record.observer_errors
    assert record.cleanup["temporary_root_removed"] is True
    assert record.cleanup["failures"] == []
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == roots_before
    retained = record.exit_observation["retained_outputs"]
    assert isinstance(retained, list) and len(retained) == 1
    assert retained[0]["sha256"] == hashlib.sha256(expected_output).hexdigest()
    assert record.exec_observation["actual_entrypoint"]["sha256"] == sealed_digests[
        "script" if request.executable.format.value == "script" else "elf"
    ]
    if request.executable.format.value == "script":
        assert record.exec_observation["actual_interpreter"]["sha256"] == (
            sealed_digests["interpreter"]
        )
    if request.executable.loader is not None:
        assert record.exec_observation["actual_loader"]["sha256"] == (
            sealed_digests["loader"]
        )
    return record


def test_structured_report_limit_is_prewrite_and_never_partial() -> None:
    read_fd, write_fd = os.pipe()
    try:
        writer = _ReportWriter(write_fd, 32)
        try:
            writer.write({"kind": "x", "payload": "z" * 64})
        except ObservationLoss:
            pass
        else:
            raise AssertionError("oversized structured report was published")
        os.set_blocking(read_fd, False)
        try:
            assert os.read(read_fd, 1) == b""
        except BlockingIOError:
            pass
        assert writer.emitted_bytes == 0
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_read_only_input_scan_rejects_existing_fifo(tmp_path: Path) -> None:
    (tmp_path / "regular").write_bytes(b"ok")
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        observed = _scan_read_only_tree(descriptor)
    finally:
        os.close(descriptor)
    assert observed["entries_scanned"] == 1
    os.mkfifo(tmp_path / "host-fifo")
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            _scan_read_only_tree(descriptor)
        except IdentityMismatch:
            pass
        else:
            raise AssertionError("host FIFO was accepted in a read-only input")
    finally:
        os.close(descriptor)


def test_proc_residue_scan_is_bounded_and_empty_for_unowned_path(
    tmp_path: Path,
) -> None:
    assert _scan_residue(tmp_path / "never-created-run-root", {}) == ()


def test_linux_backend_hosted_adversarial_matrix(tmp_path: Path) -> None:
    if not _HELPERS._is_github_hosted():
        print(
            HOSTED_RESULT_PREFIX
            + '{"capability_pass":false,"disposition":"NOT_EXECUTED"}'
        )
        return
    if os.geteuid() != 0:
        command = [
            "/usr/bin/sudo",
            "-n",
            "--",
            "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1",
            f"{ROOT_MARKER}=1",
            "GITHUB_ACTIONS=true",
            "RUNNER_ENVIRONMENT=github-hosted",
            "RUNNER_OS=Linux",
            "RUNNER_ARCH=X64",
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "-s",
            f"{Path(__file__).resolve()}::test_linux_backend_hosted_adversarial_matrix",
        ]
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        assert completed.returncode == 0, (
            completed.stdout.decode("utf-8", "replace")
            + completed.stderr.decode("utf-8", "replace")
        )
        assert b'"disposition":"HOSTED_ADVERSARIAL_PASS"' in completed.stdout
        return

    assert os.environ.get(ROOT_MARKER) == "1"
    control = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <linux/fscrypt.h>
#include <linux/futex.h>
#include <linux/if_packet.h>
#include <linux/netlink.h>
#include <linux/perf_event.h>
#include <linux/quota.h>
#include <linux/dqblk_xfs.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    struct rlimit tiny_limit={1,1};
    int input_fd=open("/inputs/fixture/control",O_RDONLY); if(input_fd<0)return 76;
    errno=0; if (syscall(470,0,0,0,0,0,0) != -1 || errno != EPERM) return 123;
    errno=0; if (syscall(160,RLIMIT_FSIZE,&tiny_limit) != -1 || errno != EPERM) return 38;
    errno=0; if (syscall(302,0,RLIMIT_FSIZE,&tiny_limit,0) != -1 || errno != EPERM) return 69;
    errno=0; if (fcntl(1,F_SETPIPE_SZ,8192) != -1 || errno != EPERM) return 39;
    errno=0; if (fcntl(2,F_SETPIPE_SZ,8192) != -1 || errno != EPERM) return 40;
    errno=0; if (fcntl(input_fd,F_SETFL,O_NONBLOCK) != -1 || errno != EPERM) return 105;
    if (fcntl(1,F_GETPIPE_SZ) != 4096 || fcntl(2,F_GETPIPE_SZ) != 4096) return 62;
    int packet_pipe[2];
    errno=0; if(pipe2(packet_pipe,O_DIRECT)!=-1 || errno!=EPERM)return 106;
    errno=0; if(pipe2(packet_pipe,O_EXCL)!=-1 || errno!=EPERM)return 107;
    if(pipe2(packet_pipe,0)!=0)return 108;
    close(packet_pipe[0]); close(packet_pipe[1]);
    errno=0; if (syscall(SYS_clone, CLONE_THREAD|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 41;
    errno=0; if (syscall(SYS_clone, CLONE_UNTRACED|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 42;
    errno=0; if (syscall(SYS_clone, CLONE_VM|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 70;
    errno=0; if (syscall(SYS_clone, CLONE_FS|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 71;
    errno=0; if (syscall(SYS_clone, CLONE_FILES|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 72;
    errno=0; if (syscall(SYS_clone, CLONE_SIGHAND|SIGCHLD, 0,0,0,0) != -1 || errno != EPERM) return 73;
    errno=0; if (syscall(206, 0, 0) != -1 || errno != EPERM) return 43;
    errno=0; if (syscall(319,"ts-b02a",0) != -1 || errno != EPERM) return 77;
    errno=0; if (syscall(447,0) != -1 || errno != EPERM) return 78;
    errno=0; if (syscall(188,"/scratch","user.ts-b02a","x",1,0) != -1 || errno != EPERM) return 79;
    errno=0; if (syscall(189,"/scratch","user.ts-b02a","x",1,0) != -1 || errno != EPERM) return 80;
    errno=0; if (syscall(190,input_fd,"user.ts-b02a","x",1,0) != -1 || errno != EPERM) return 81;
    errno=0; if (syscall(197,"/scratch","user.ts-b02a") != -1 || errno != EPERM) return 82;
    errno=0; if (syscall(198,"/scratch","user.ts-b02a") != -1 || errno != EPERM) return 83;
    errno=0; if (syscall(199,input_fd,"user.ts-b02a") != -1 || errno != EPERM) return 84;
    errno=0; if (syscall(463,AT_FDCWD,"/scratch",0,"user.ts-b02a",0,0) != -1 || errno != EPERM) return 121;
    errno=0; if (syscall(466,AT_FDCWD,"/scratch",0,"user.ts-b02a") != -1 || errno != EPERM) return 122;
    errno=0; if (syscall(467,0,0,0,0,0,0) != -1 || errno != EPERM) return 124;
    errno=0; if (syscall(469,0,0,0,0,0,0) != -1 || errno != EPERM) return 125;
    errno=0; if (syscall(73,input_fd,LOCK_EX|LOCK_NB) != -1 || errno != EPERM) return 85;
    errno=0; if (syscall(162) != -1 || errno != EPERM) return 93;
    errno=0; if (syscall(306,input_fd) != -1 || errno != EPERM) return 94;
    errno=0; if (syscall(179,QCMD(Q_SYNC,USRQUOTA),"/",0,0) != -1 || errno != EPERM) return 116;
    errno=0; if (syscall(179,QCMD(Q_XQUOTASYNC,USRQUOTA),"/",0,0) != -1 || errno != EPERM) return 117;
    errno=0; if (syscall(443,input_fd,QCMD(Q_SYNC,USRQUOTA),0,0) != -1 || errno != EPERM) return 118;
    errno=0; if (syscall(443,input_fd,QCMD(Q_XQUOTASYNC,USRQUOTA),0,0) != -1 || errno != EPERM) return 119;
    struct perf_event_attr perf_attr={0};
    perf_attr.type=PERF_TYPE_SOFTWARE; perf_attr.size=sizeof(perf_attr);
    perf_attr.config=PERF_COUNT_SW_CPU_CLOCK; perf_attr.disabled=0;
    errno=0; if (syscall(298,&perf_attr,-1,0,-1,0) != -1 || errno != EPERM) return 120;
    int futex_word=0;
    errno=0; if (syscall(SYS_futex,&futex_word,FUTEX_WAKE,1,0,0,0) != -1 || errno != EPERM) return 98;
    errno=0; if (syscall(SYS_futex,&futex_word,FUTEX_WAKE_PRIVATE,1,0,0,0) != 0 || errno != 0) return 99;
    errno=0; if (syscall(449,0,0,0,0,0) != -1 || errno != EPERM) return 100;
    errno=0; if (syscall(454,0,0,0,0,0) != -1 || errno != EPERM) return 101;
    errno=0; if (syscall(455,0,0,0,0,0) != -1 || errno != EPERM) return 102;
    errno=0; if (syscall(456,0,0,0,0,0) != -1 || errno != EPERM) return 103;
    errno=0; if (syscall(324,0,0,0,0,0) != -1 || errno != EPERM) return 104;
    errno=0; if (syscall(140,2,65534) != -1 || errno != EPERM) return 109;
    errno=0; if (syscall(141,2,65534,10) != -1 || errno != EPERM) return 110;
    errno=0; if (syscall(251,3,65534,0) != -1 || errno != EPERM) return 111;
    errno=0; if (syscall(252,3,65534) != -1 || errno != EPERM) return 112;
    errno=0; if (syscall(16,input_fd,FS_IOC_ADD_ENCRYPTION_KEY,0) != -1 || errno != EPERM) return 95;
    errno=0; if (syscall(16,input_fd,FS_IOC_REMOVE_ENCRYPTION_KEY,0) != -1 || errno != EPERM) return 96;
    errno=0; if (syscall(16,input_fd,FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS,0) != -1 || errno != EPERM) return 97;
    struct flock lock={0}; lock.l_type=F_WRLCK; lock.l_whence=SEEK_SET;
    int lock_commands[]={6,7,37,38};
    for(unsigned i=0;i<sizeof(lock_commands)/sizeof(lock_commands[0]);i++) {
        errno=0; if(fcntl(input_fd,lock_commands[i],&lock)!=-1 || errno!=EPERM)return 86;
    }
    errno=0; if(fcntl(input_fd,1024,F_WRLCK)!=-1 || errno!=EPERM)return 87;
    uint64_t rw_hint=0;
    errno=0; if(fcntl(input_fd,1036,&rw_hint)!=-1 || errno!=EPERM)return 90;
    errno=0; if(fcntl(input_fd,1038,&rw_hint)!=-1 || errno!=EPERM)return 91;
    errno=0; if(fcntl(input_fd,1040,&rw_hint)!=-1 || errno!=EPERM)return 92;
    lock.l_type=F_WRLCK; if(fcntl(input_fd,F_GETLK,&lock)<0)return 88;
    if(fcntl(input_fd,1025)<0)return 89;
    errno=0; if (syscall(248, "ts-b02a", "x", 1, 0) != -1 || errno != EPERM) return 63;
    errno=0; if (syscall(249, "user", "ts-b02a", 0, 0) != -1 || errno != EPERM) return 64;
    errno=0; if (syscall(250, 0, 0, 0, 0) != -1 || errno != EPERM) return 65;
    errno=0; if (socket(AF_INET, SOCK_DGRAM, 0) != -1 || errno != EPERM) return 44;
    errno=0; if (socket(AF_INET, SOCK_STREAM, 0) != -1 || errno != EPERM) return 52;
    errno=0; if (socket(AF_INET6, SOCK_STREAM, 0) != -1 || errno != EPERM) return 53;
    errno=0; if (socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE) != -1 || errno != EPERM) return 54;
    errno=0; if (socket(AF_PACKET, SOCK_RAW, 0) != -1 || errno != EPERM) return 55;
    int pair[2]; errno=0; if (socketpair(AF_UNIX,SOCK_STREAM,0,pair) != -1 || errno != EPERM) return 56;
    errno=0; if (syscall(SYS_unshare, CLONE_NEWNET) != -1 || errno != EPERM) return 57;
    errno=0; if (syscall(SYS_setns, -1, CLONE_NEWNET) != -1 || errno != EPERM) return 58;
    errno=0; if (open("/proc/cpuinfo", O_RDONLY) != -1 || errno != ENOENT) return 45;
    errno=0; if (open("/sys/kernel", O_RDONLY) != -1 || errno != ENOENT) return 46;
    errno=0; if (open("/dev/null", O_RDONLY) != -1 || errno != ENOENT) return 47;
    char *exec_argv[]={(char *)"/inputs/fixture/control",0}; char *exec_env[]={0};
    errno=0; execve(exec_argv[0],exec_argv,exec_env); if(errno!=EPERM)return 66;
    errno=0; if(syscall(SYS_execveat,input_fd,"",exec_argv,exec_env,AT_EMPTY_PATH)!=-1 || errno!=EPERM)return 68;
    close(input_fd);
    pid_t child=fork(); if (child < 0) return 48; if (child == 0) _exit(0);
    int status=0; if (waitpid(child,&status,0)!=child || !WIFEXITED(status) || WEXITSTATUS(status)!=0) return 59;
    pid_t vf=vfork(); if(vf<0)return 60; if(vf==0)_exit(0);
    if(waitpid(vf,&status,0)!=vf || !WIFEXITED(status) || WEXITSTATUS(status)!=0)return 61;
    int fd=open("/output/result.txt", O_WRONLY|O_TRUNC); if (fd < 0) return 49;
    if (write(fd,"ok\n",3) != 3) return 50;
    close(fd);
    errno=0; if (open("/output/nope", O_WRONLY|O_CREAT,0600) != -1 || errno != EACCES) return 51;
    errno=0; if (open("/inputs/nope", O_WRONLY|O_CREAT,0600) != -1 || errno != EACCES) return 113;
    errno=0; if (open("/fixture/nope", O_WRONLY|O_CREAT,0600) != -1 || errno != EACCES) return 114;
    errno=0; if (open("/run/nope", O_WRONLY|O_CREAT,0600) != -1 || errno != EACCES) return 115;
    return 0;
}
'''.lstrip(),
        name="control",
    )
    control_request = _HELPERS._request(control, deadline_seconds=30)
    priority_ready_read = -1
    priority_ready_write = -1
    priority_sibling = -1
    priority_pidfd = -1
    priority_reaped = False
    priority_selector: selectors.BaseSelector | None = None
    priority_cleanup_failures: list[str] = []
    try:
        priority_ready_read, priority_ready_write = os.pipe2(os.O_CLOEXEC)
        priority_sibling = os.fork()
        if priority_sibling == 0:
            try:
                os.close(priority_ready_read)
                os.setgroups([])
                os.setgid(65534)
                os.setuid(65534)
                os.write(priority_ready_write, b"r")
                os.close(priority_ready_write)
                while True:
                    signal.pause()
            except BaseException:
                os._exit(125)
        os.close(priority_ready_write)
        priority_ready_write = -1
        priority_pidfd = os.pidfd_open(priority_sibling)
        os.set_blocking(priority_ready_read, False)
        priority_selector = selectors.DefaultSelector()
        priority_selector.register(priority_ready_read, selectors.EVENT_READ)
        ready_events = priority_selector.select(timeout=2)
        assert ready_events, "same-UID priority sibling readiness timed out"
        assert os.read(priority_ready_read, 1) == b"r"
        initial_nice = os.getpriority(os.PRIO_PROCESS, priority_sibling)
        host_libc_for_priority = ctypes.CDLL(None, use_errno=True)
        ctypes.set_errno(0)
        initial_ioprio = int(
            host_libc_for_priority.syscall(252, 1, priority_sibling)
        )
        assert initial_ioprio >= 0, ctypes.get_errno()
        provider_umask = os.umask(0)
        try:
            control_evidence = LinuxNativeSupervisorV1().execute(control_request)
        finally:
            os.umask(provider_umask)
        assert os.getpriority(os.PRIO_PROCESS, priority_sibling) == initial_nice
        ctypes.set_errno(0)
        assert int(host_libc_for_priority.syscall(252, 1, priority_sibling)) == (
            initial_ioprio
        )
    finally:
        if priority_selector is not None:
            try:
                priority_selector.close()
            except BaseException as exc:
                priority_cleanup_failures.append(
                    f"selector close: {type(exc).__name__}:{exc}"
                )
        for descriptor in (priority_ready_read, priority_ready_write):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    priority_cleanup_failures.append(
                        f"pipe close: {type(exc).__name__}:{exc}"
                    )
        if priority_sibling > 0 and not priority_reaped:
            try:
                if priority_pidfd >= 0:
                    signal.pidfd_send_signal(
                        priority_pidfd, signal.SIGKILL, None, 0
                    )
                else:
                    # This is the unreaped direct child created by this test;
                    # its PID cannot be reused before waitpid consumes it.
                    os.kill(priority_sibling, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as exc:
                priority_cleanup_failures.append(
                    f"sibling kill: {type(exc).__name__}:{exc}"
                )
            try:
                linux_backend._bounded_waitpid_status(
                    priority_sibling, timeout=2
                )
                priority_reaped = True
            except BaseException as exc:
                priority_cleanup_failures.append(
                    f"sibling reap: {type(exc).__name__}:{exc}"
                )
        if priority_pidfd >= 0:
            try:
                os.close(priority_pidfd)
            except BaseException as exc:
                priority_cleanup_failures.append(
                    f"pidfd close: {type(exc).__name__}:{exc}"
                )
        if priority_cleanup_failures:
            raise AssertionError(
                "priority control cleanup failed: "
                + "; ".join(priority_cleanup_failures)
            )
    control_validation = validate_execution_evidence_v1(
        control_request, control_evidence
    )
    assert control_evidence.outcome is ExecutionOutcomeV1.SUCCESS, control_evidence.to_record()
    assert control_evidence.complete and control_validation.ok, control_validation.reasons
    assert "fork" in control_evidence.process.event_classes
    assert "exec_denied" in control_evidence.process.event_classes
    assert [
        item.syscall_number
        for item in control_evidence.process.secondary_exec_denials
    ] == [59, 322]
    assert control_evidence.process.member_count_observed >= 2
    assert all(
        item.pidfd_opened and item.identity_revalidated and item.pidfd_exit_observed
        for item in control_evidence.process.member_observations
    )
    assert any(
        item.observed_before_grace
        and not item.observed_before_kill
        and not item.pidfd_unreadable_before_kill
        and item.pidfd_exit_observed
        for item in control_evidence.process.member_observations
    )
    assert control_evidence.network.inherited_network_fd_absent_at_exec is True
    assert control_evidence.filesystem.output_observed_inode_ceiling == 128
    assert control_evidence.filesystem.observed_output_paths == ("result.txt",)
    assert control_evidence.filesystem.undeclared_output_blocked is True

    shared_futex_path = tmp_path / "futex-shared.bin"
    shared_futex_path.write_bytes(b"\0" * 4096)
    shared_futex_path.chmod(0o644)
    futex_boundary = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/futex.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
int main(void) {
    int fd=open("/inputs/fixture/futex-shared.bin",O_RDONLY); if(fd<0)return 1;
    int *word=mmap(0,4096,PROT_READ,MAP_SHARED,fd,0); if(word==MAP_FAILED)return 2;
    errno=0; if(syscall(SYS_futex,word,FUTEX_WAKE,1,0,0,0)!=-1 || errno!=EPERM)return 3;
    int local=0; errno=0;
    if(syscall(SYS_futex,&local,FUTEX_WAKE_PRIVATE,1,0,0,0)!=0 || errno!=0)return 4;
    if(munmap(word,4096)!=0 || close(fd)!=0)return 5;
    fd=open("/output/result.txt",O_WRONLY|O_TRUNC); if(fd<0)return 6;
    if(write(fd,"ok\n",3)!=3)return 7;
    return close(fd)!=0;
}
'''.lstrip(),
        name="futex-boundary",
    )
    host_futex_fd = os.open(shared_futex_path, os.O_RDWR)
    try:
        host_mapping = mmap.mmap(
            host_futex_fd,
            4096,
            flags=mmap.MAP_SHARED,
            prot=mmap.PROT_READ | mmap.PROT_WRITE,
        )
    finally:
        os.close(host_futex_fd)
    host_word = ctypes.c_int.from_buffer(host_mapping)
    host_libc = ctypes.CDLL(None, use_errno=True)

    class Timespec(ctypes.Structure):
        _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]

    waiter_ready = threading.Event()
    waiter_result: list[int] = []

    def host_waiter() -> None:
        timeout = Timespec(60, 0)
        waiter_ready.set()
        waiter_result.append(
            int(
                host_libc.syscall(
                    202,
                    ctypes.byref(host_word),
                    0,
                    0,
                    ctypes.byref(timeout),
                    0,
                    0,
                )
            )
        )

    waiter = threading.Thread(target=host_waiter, daemon=True)
    waiter.start()
    wake_result = -1
    try:
        assert waiter_ready.wait(timeout=1)
        assert waiter.native_id is not None
        waiter_wchan = Path(
            f"/proc/self/task/{waiter.native_id}/wchan"
        )
        wchan_deadline = time.monotonic_ns() + 2_000_000_000
        observed_wchan = ""
        while time.monotonic_ns() < wchan_deadline:
            assert waiter.is_alive(), "host futex waiter exited before observation"
            observed_wchan = waiter_wchan.read_text(encoding="ascii").strip()
            if "futex_wait" in observed_wchan:
                break
            time.sleep(0.01)
        else:
            raise AssertionError(
                f"host waiter never reached futex_wait*: {observed_wchan!r}"
            )
        _assert_complete(
            _HELPERS._request(futex_boundary, deadline_seconds=30),
            ExecutionOutcomeV1.SUCCESS,
        )
        assert waiter.is_alive(), "workload woke a host shared-inode futex waiter"
    finally:
        ctypes.set_errno(0)
        wake_result = int(
            host_libc.syscall(202, ctypes.byref(host_word), 1, 1, 0, 0, 0)
        )
        waiter.join(timeout=2)
        del host_word
        host_mapping.close()
    assert wake_result == 1
    assert not waiter.is_alive()
    assert waiter_result == [0]

    nonroot_request = _HELPERS._request(control, deadline_seconds=10)
    nonroot_roots_before = set(
        Path("/tmp").glob("tool-system-isolated-execution-*")
    )
    nonroot_read = -1
    nonroot_write = -1
    nonroot_child = -1
    nonroot_pidfd = -1
    nonroot_reaped = False
    nonroot_bytes = bytearray()
    nonroot_cleanup_failures: list[str] = []
    try:
        nonroot_read, nonroot_write = os.pipe2(os.O_CLOEXEC)
        nonroot_child = os.fork()
        if nonroot_child == 0:
            try:
                os.close(nonroot_read)
                try:
                    os.setgroups([])
                    os.setgid(65534)
                    os.setuid(65534)
                    blocked = LinuxNativeSupervisorV1().execute(nonroot_request)
                    payload = {
                        "outcome": blocked.outcome.value,
                        "complete": blocked.complete,
                        "workload_released": blocked.workload_released,
                        "cgroup_exists": (
                            CGROUP_ROOT / nonroot_request.execution_id
                        ).exists(),
                    }
                except BaseException as exc:
                    payload = {"error": f"{type(exc).__name__}:{exc}"[:512]}
                os.write(
                    nonroot_write,
                    json.dumps(
                        payload, separators=(",", ":"), sort_keys=True
                    ).encode("utf-8"),
                )
                os.close(nonroot_write)
            except BaseException:
                os._exit(125)
            os._exit(0)
        os.close(nonroot_write)
        nonroot_write = -1
        nonroot_pidfd = os.pidfd_open(nonroot_child)
        os.set_blocking(nonroot_read, False)
        nonroot_deadline = time.monotonic_ns() + 5_000_000_000
        while time.monotonic_ns() < nonroot_deadline:
            try:
                chunk = os.read(nonroot_read, 4_096)
            except BlockingIOError:
                chunk = None
            if chunk:
                nonroot_bytes.extend(chunk)
            waited, status_value = os.waitpid(nonroot_child, os.WNOHANG)
            if waited == nonroot_child:
                nonroot_reaped = True
                assert os.WIFEXITED(status_value)
                assert os.WEXITSTATUS(status_value) == 0
                while True:
                    try:
                        trailing = os.read(nonroot_read, 4_096)
                    except BlockingIOError:
                        break
                    if not trailing:
                        break
                    nonroot_bytes.extend(trailing)
                break
            time.sleep(0.01)
        else:
            raise AssertionError("non-root pre-release gate exceeded its bound")
    finally:
        for descriptor in (nonroot_read, nonroot_write):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    nonroot_cleanup_failures.append(
                        f"pipe close: {type(exc).__name__}:{exc}"
                    )
        if nonroot_child > 0 and not nonroot_reaped:
            try:
                if nonroot_pidfd >= 0:
                    signal.pidfd_send_signal(
                        nonroot_pidfd, signal.SIGKILL, None, 0
                    )
                else:
                    # The direct child remains unreaped, so this numeric PID
                    # cannot have been reused outside the test's ownership.
                    os.kill(nonroot_child, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as exc:
                nonroot_cleanup_failures.append(
                    f"child kill: {type(exc).__name__}:{exc}"
                )
            try:
                linux_backend._bounded_waitpid_status(nonroot_child, timeout=2)
                nonroot_reaped = True
            except BaseException as exc:
                nonroot_cleanup_failures.append(
                    f"child reap: {type(exc).__name__}:{exc}"
                )
        if nonroot_pidfd >= 0:
            try:
                os.close(nonroot_pidfd)
            except BaseException as exc:
                nonroot_cleanup_failures.append(
                    f"pidfd close: {type(exc).__name__}:{exc}"
                )
        if nonroot_cleanup_failures:
            raise AssertionError(
                "non-root control cleanup failed: "
                + "; ".join(nonroot_cleanup_failures)
            )
    nonroot_result = json.loads(bytes(nonroot_bytes).decode("utf-8"))
    assert nonroot_result == {
        "cgroup_exists": False,
        "complete": False,
        "outcome": "capability_blocker",
        "workload_released": False,
    }
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == (
        nonroot_roots_before
    )

    native_sealed = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <fcntl.h>
#include <unistd.h>
int main(void) {
    int fd=open("/output/result.txt",O_WRONLY|O_TRUNC);
    if(fd<0) return 70;
    if(write(fd,"native-sealed\n",14)!=14) return 71;
    close(fd);
    return 0;
}
'''.lstrip(),
        name="native-sealed",
    )
    native_replacement = tmp_path / "native-replacement"
    shutil.copyfile("/usr/bin/false", native_replacement)
    native_replacement.chmod(0o755)
    _run_prepared_after_source_replacement(
        _HELPERS._request(native_sealed, deadline_seconds=30),
        ((native_sealed, native_replacement),),
        b"native-sealed\n",
    )

    script = tmp_path / "sealed-script"
    script.write_text(
        "#!/bin/sh\nprintf 'script-sealed\\n' > /output/result.txt\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    interpreter = tmp_path / "sealed-interpreter"
    shutil.copyfile("/usr/bin/dash", interpreter)
    interpreter.chmod(0o755)
    interpreter_request = _HELPERS._request(interpreter, deadline_seconds=30)
    assert interpreter_request.executable.loader is not None
    loader = tmp_path / "sealed-loader"
    shutil.copyfile(
        interpreter_request.executable.loader.source_path,
        loader,
    )
    loader.chmod(
        interpreter_request.executable.loader.mode & 0o7777
    )
    script_request = dataclasses.replace(
        interpreter_request,
        executable=_HELPERS.ExecutablePolicyV1(
            format=_HELPERS.ExecutableFormatV1.SCRIPT,
            entrypoint=_HELPERS._expected(
                script,
                "/fixture/script",
                _HELPERS.ExpectedFileTypeV1.SCRIPT,
            ),
            interpreter=_HELPERS._expected(
                interpreter,
                "/bin/sh",
                _HELPERS.ExpectedFileTypeV1.INTERPRETER,
            ),
            loader=_HELPERS._expected(
                loader,
                interpreter_request.executable.loader.private_path,
                _HELPERS.ExpectedFileTypeV1.LOADER,
            ),
            parsed_interpreter_path="/bin/sh",
            argv=("/fixture/script",),
            environment=(),
        ),
    )
    script_replacement = tmp_path / "script-replacement"
    script_replacement.write_text("#!/bin/sh\nexit 91\n", encoding="utf-8")
    script_replacement.chmod(0o755)
    interpreter_replacement = tmp_path / "interpreter-replacement"
    shutil.copyfile("/usr/bin/false", interpreter_replacement)
    interpreter_replacement.chmod(0o755)
    loader_replacement = tmp_path / "loader-replacement"
    shutil.copyfile("/usr/bin/false", loader_replacement)
    loader_replacement.chmod(0o755)
    _run_prepared_after_source_replacement(
        script_request,
        (
            (script, script_replacement),
            (interpreter, interpreter_replacement),
            (loader, loader_replacement),
        ),
        b"script-sealed\n",
    )

    deep_scratch = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <sys/stat.h>
#include <unistd.h>
int main(void) {
    if(chdir("/scratch")!=0) return 73;
    for(int i=0;i<1500;i++) {
        if(mkdir("d",0700)!=0 || chdir("d")!=0) return 74;
    }
    return 0;
}
'''.lstrip(),
        name="deep-scratch",
    )
    deep_request = _HELPERS._request(deep_scratch, deadline_seconds=30)
    deep_request = dataclasses.replace(
        deep_request,
        filesystem=dataclasses.replace(
            deep_request.filesystem,
            scratch_inode_limit=2048,
        ),
    )
    _assert_complete(deep_request, ExecutionOutcomeV1.SUCCESS)

    stream_cases = (
        (
            "stdout-stream",
            'for(;;){if(write(1,b,sizeof b)<0)return 90;}',
            "stdout",
        ),
        (
            "stderr-stream",
            'for(;;){if(write(2,b,sizeof b)<0)return 91;}',
            "stderr",
        ),
        (
            "combined-stream",
            'for(;;){if(write(1,b,sizeof b)<0)return 92;'
            'if(write(2,b,sizeof b)<0)return 93;}',
            "combined",
        ),
    )
    for name, loop, triggered in stream_cases:
        stream = _HELPERS._compile_fixture(
            tmp_path,
            (
                '#include <signal.h>\n#include <unistd.h>\n'
                'int main(void){signal(SIGTERM,SIG_IGN);char b[4096]={0};'
                + loop
                + '}\n'
            ),
            name=name,
        )
        stream_evidence = _assert_complete(
            _HELPERS._request(stream, deadline_seconds=30),
            ExecutionOutcomeV1.LIMIT,
        )
        assert getattr(stream_evidence.streams, triggered).limit_triggered is True
        assert stream_evidence.streams.pipe_capacity_bytes == 4096
        assert (
            stream_evidence.process.grace_started_monotonic_ns
            == stream_evidence.process.grace_finished_monotonic_ns
        )
        assert stream_evidence.streams.combined.emitted_bytes <= (
            stream_evidence.streams.combined.limit_bytes + 8193
        )

    simultaneous_stream = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <signal.h>
#include <unistd.h>
int main(void) {
    signal(SIGTERM,SIG_IGN);
    char b[4096]={0};
    pid_t c=fork(); if(c<0)return 1;
    int fd=c==0?1:2;
    for(;;) if(write(fd,b,sizeof b)<0)return 2;
}
'''.lstrip(),
        name="simultaneous-streams",
    )
    for _ in range(3):
        simultaneous_evidence = _assert_complete(
            _HELPERS._request(simultaneous_stream, deadline_seconds=30),
            ExecutionOutcomeV1.LIMIT,
        )
        assert simultaneous_evidence.streams.combined.emitted_bytes <= (
            simultaneous_evidence.streams.combined.limit_bytes + 8193
        )

    finite_stream = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <unistd.h>
int main(void) {
    char b[4096]={0};
    int left=65537;
    while(left>0) {
        int n=left>4096?4096:left;
        if(write(1,b,n)!=n) return 60;
        left-=n;
    }
    return 0;
}
'''.lstrip(),
        name="finite-stream",
    )
    finite_stream_evidence = _assert_complete(
        _HELPERS._request(finite_stream, deadline_seconds=30),
        ExecutionOutcomeV1.LIMIT,
    )
    assert finite_stream_evidence.streams.stdout.limit_triggered is True

    asymmetric_quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <fcntl.h>
#include <unistd.h>
int main(void) {
    char b[4096]={0};
    int f=open("/scratch/over-output-limit",O_WRONLY|O_CREAT|O_EXCL,0600);
    if(f<0) return 63;
    for(int i=0;i<384;i++) {
        if(write(f,b,sizeof b)!=sizeof b) return 64;
    }
    close(f);
    f=open("/output/result.txt",O_WRONLY|O_TRUNC);
    if(f<0) return 65;
    if(write(f,"ok",2)!=2) return 66;
    close(f);
    return 0;
}
'''.lstrip(),
        name="asymmetric-quota",
    )
    asymmetric_request = _HELPERS._request(
        asymmetric_quota, deadline_seconds=30
    )
    asymmetric_request = dataclasses.replace(
        asymmetric_request,
        filesystem=dataclasses.replace(
            asymmetric_request.filesystem,
            scratch_byte_limit=2_097_152,
        ),
    )
    asymmetric_evidence = _assert_complete(
        asymmetric_request,
        ExecutionOutcomeV1.SUCCESS,
    )
    exec_payload = next(
        item.payload()
        for item in asymmetric_evidence.observations
        if item.event_id == "exec.ptrace"
    )
    assert exec_payload["file_size_soft_limit"] == 2_097_152

    quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
int main(void) {
    char b[4096]={0};
    int f=open("/scratch/fill",O_WRONLY|O_CREAT,0600);
    if(f<0) return 61;
    while(write(f,b,sizeof b)==sizeof b) {}
    if(errno!=ENOSPC) return 62;
    for(;;) pause();
}
'''.lstrip(),
        name="quota",
    )
    quota_request = _HELPERS._request(quota, deadline_seconds=30)
    quota_evidence = LinuxNativeSupervisorV1().execute(quota_request)
    quota_validation = validate_execution_evidence_v1(quota_request, quota_evidence)
    assert quota_evidence.outcome is ExecutionOutcomeV1.LIMIT, quota_evidence.to_record()
    assert quota_evidence.complete and quota_validation.ok, quota_validation.reasons
    assert quota_evidence.filesystem.limit_observation is not None

    for short_name, write_expression, extra_include in (
        (
            "positive-short-write",
            "ssize_t n=write(f,b,2097152);",
            "",
        ),
        (
            "positive-short-writev",
            (
                "struct iovec v[2]={{b,1048576},{b+1048576,1048576}};"
                "ssize_t n=writev(f,v,2);"
            ),
            "#include <sys/uio.h>\n",
        ),
    ):
        short_write = _HELPERS._compile_fixture(
            tmp_path,
            (
                "#include <errno.h>\n#include <fcntl.h>\n#include <signal.h>\n"
                "#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n"
                + extra_include
                + "int main(void){signal(SIGXFSZ,SIG_IGN);"
                "char *b=malloc(2097152);if(!b)return 1;memset(b,'x',2097152);"
                "int f=open(\"/scratch/short\",O_WRONLY|O_CREAT|O_TRUNC,0600);"
                "if(f<0)return 2;"
                + write_expression
                + "if(n<=0||n>=2097152)return 3;close(f);free(b);return 0;}\n"
            ),
            name=short_name,
        )
        short_request = _HELPERS._request(short_write, deadline_seconds=30)
        short_roots_before = set(
            Path("/tmp").glob("tool-system-isolated-execution-*")
        )
        short_evidence = LinuxNativeSupervisorV1().execute(short_request)
        short_validation = validate_execution_evidence_v1(
            short_request, short_evidence
        )
        assert short_evidence.outcome is (
            ExecutionOutcomeV1.OBSERVATION_INCOMPLETE
        ), short_evidence.to_record()
        assert short_evidence.complete is False
        assert short_validation.error_code is (
            EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
        )
        assert short_evidence.process.limit_triggered is False
        assert short_evidence.completeness.cleanup.complete is True
        assert not (CGROUP_ROOT / short_request.execution_id).exists()
        assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == (
            short_roots_before
        )

    inode_quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    pid_t c=fork();
    if(c<0) return 64;
    if(c==0) {
        char p[128];
        for(int i=0;i<10000;i++) {
            snprintf(p,sizeof p,"/scratch/inode-%d",i);
            int f=openat(AT_FDCWD,p,O_WRONLY|O_CREAT|O_EXCL,0600);
            if(f<0) {
                if(errno==ENOSPC) for(;;) pause();
                _exit(65);
            }
            close(f);
        }
        _exit(66);
    }
    int s=0;
    if(waitpid(c,&s,0)<0) return 67;
    return 68;
}
'''.lstrip(),
        name="inode-quota",
    )
    inode_request = _HELPERS._request(inode_quota, deadline_seconds=30)
    inode_request = dataclasses.replace(
        inode_request,
        filesystem=dataclasses.replace(
            inode_request.filesystem,
            scratch_inode_limit=32,
        ),
    )
    inode_roots_before = set(Path("/tmp").glob("tool-system-isolated-execution-*"))
    inode_evidence = LinuxNativeSupervisorV1().execute(inode_request)
    inode_validation = validate_execution_evidence_v1(
        inode_request, inode_evidence
    )
    assert (
        inode_evidence.outcome
        is ExecutionOutcomeV1.OBSERVATION_INCOMPLETE
    ), inode_evidence.to_record()
    assert inode_evidence.complete is False
    assert inode_validation.error_code is (
        EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    )
    assert inode_evidence.filesystem.limit_observation is None
    assert inode_evidence.process.limit_triggered is False
    assert inode_evidence.completeness.cleanup.complete is True
    assert "fork" in inode_evidence.process.event_classes
    assert not (CGROUP_ROOT / inode_request.execution_id).exists()
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == (
        inode_roots_before
    )

    output_quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
int main(void) {
    signal(SIGXFSZ,SIG_IGN);
    char b[4096]={0};
    int f=open("/output/result.txt",O_WRONLY|O_TRUNC);
    if(f<0) return 71;
    while(write(f,b,sizeof b)==sizeof b) {}
    if(errno!=EFBIG && errno!=ENOSPC) return 72;
    for(;;) pause();
}
'''.lstrip(),
        name="output-quota",
    )
    output_evidence = _assert_complete(
        _HELPERS._request(output_quota, deadline_seconds=30),
        ExecutionOutcomeV1.LIMIT,
    )
    assert output_evidence.filesystem.limit_observation is not None

    path_quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <errno.h>
#include <signal.h>
#include <unistd.h>
int main(void) {
    signal(SIGXFSZ,SIG_IGN);
    errno=0;
    if(truncate("/inputs/fixture/cross-scope-input",2097152)!=-1 || errno!=EFBIG) return 75;
    return 0;
}
'''.lstrip(),
        name="path-quota-not-promoted",
    )
    (tmp_path / "cross-scope-input").symlink_to("/output/result.txt")
    path_quota_request = _HELPERS._request(path_quota, deadline_seconds=30)
    path_quota_roots_before = set(
        Path("/tmp").glob("tool-system-isolated-execution-*")
    )
    path_quota_evidence = LinuxNativeSupervisorV1().execute(path_quota_request)
    path_quota_validation = validate_execution_evidence_v1(
        path_quota_request, path_quota_evidence
    )
    assert (
        path_quota_evidence.outcome
        is ExecutionOutcomeV1.OBSERVATION_INCOMPLETE
    ), path_quota_evidence.to_record()
    assert path_quota_evidence.complete is False
    assert path_quota_validation.error_code is (
        EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    )
    assert path_quota_evidence.process.limit_triggered is False
    assert path_quota_evidence.filesystem.limit_observation is None
    assert path_quota_evidence.completeness.cleanup.complete is True
    assert not (CGROUP_ROOT / path_quota_request.execution_id).exists()
    assert set(Path("/tmp").glob("tool-system-isolated-execution-*")) == (
        path_quota_roots_before
    )

    sigbus_quota = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <fcntl.h>
#include <signal.h>
#include <sys/mman.h>
#include <unistd.h>
static void handled(int value) { (void)value; _exit(0); }
int main(void) {
    if(signal(SIGBUS,handled)==SIG_ERR) return 1;
    char seed[4096]={0};
    int s=open("/scratch/seed",O_WRONLY|O_CREAT|O_TRUNC,0600);
    if(s<0 || write(s,seed,sizeof seed)!=(ssize_t)sizeof seed || close(s)!=0) return 5;
    int f=open("/scratch/mapped",O_RDWR|O_CREAT|O_TRUNC,0600);
    if(f<0 || ftruncate(f,1048576)!=0) return 2;
    volatile unsigned char *p=mmap(0,1048576,PROT_READ|PROT_WRITE,MAP_SHARED,f,0);
    if(p==MAP_FAILED) return 3;
    for(int i=0;i<1048576;i+=4096) p[i]=1;
    return 4;
}
'''.lstrip(),
        name="handled-sigbus-not-limit",
    )
    sigbus_request = _HELPERS._request(sigbus_quota, deadline_seconds=30)
    sigbus_evidence = LinuxNativeSupervisorV1().execute(sigbus_request)
    sigbus_validation = validate_execution_evidence_v1(
        sigbus_request, sigbus_evidence
    )
    assert sigbus_evidence.outcome is (
        ExecutionOutcomeV1.OBSERVATION_INCOMPLETE
    ), sigbus_evidence.to_record()
    assert sigbus_evidence.complete is False
    assert sigbus_validation.error_code is (
        EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    )
    assert sigbus_evidence.process.limit_triggered is False
    assert sigbus_evidence.filesystem.limit_observation is None
    assert sigbus_evidence.completeness.cleanup.complete is True
    assert not (CGROUP_ROOT / sigbus_request.execution_id).exists()

    signal_failure = _HELPERS._compile_fixture(
        tmp_path,
        '#include <signal.h>\nint main(void){raise(SIGTRAP);return 0;}\n',
        name="signal-failure",
    )
    signal_evidence = _assert_complete(
        _HELPERS._request(signal_failure, deadline_seconds=30),
        ExecutionOutcomeV1.WORKLOAD_FAILURE,
    )
    assert signal_evidence.workload_exit_code == 128 + 5

    core_crash = _HELPERS._compile_fixture(
        tmp_path,
        '#include <signal.h>\nint main(void){raise(SIGSEGV);return 0;}\n',
        name="core-crash",
    )
    core_files_before = set(tmp_path.glob("core*"))
    core_evidence = _assert_complete(
        _HELPERS._request(core_crash, deadline_seconds=30),
        ExecutionOutcomeV1.WORKLOAD_FAILURE,
    )
    assert core_evidence.workload_exit_code == 128 + 11
    assert set(tmp_path.glob("core*")) == core_files_before

    timeout = _HELPERS._compile_fixture(
        tmp_path,
        r'''
#include <signal.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
int main(void){signal(SIGTERM,SIG_IGN); if(setsid()<0)return 81; pid_t a=fork(); if(a<0)return 82;
if(a==0){pid_t b=fork(); if(b<0)_exit(83); for(;;)pause();} raise(SIGSTOP); for(;;)pause();}
'''.lstrip(),
        name="timeout",
    )
    timeout_evidence = _assert_complete(
        _HELPERS._request(timeout, deadline_seconds=15),
        ExecutionOutcomeV1.TIMEOUT,
    )
    assert timeout_evidence.process.member_count_observed >= 3
    print(
        HOSTED_RESULT_PREFIX
        + '{"capability_pass":true,"disposition":"HOSTED_ADVERSARIAL_PASS"}',
        flush=True,
    )
