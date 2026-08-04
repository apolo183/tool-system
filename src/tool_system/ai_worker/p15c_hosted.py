from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import io
import json
import os
import re
import stat
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from tool_system.ai_worker.p15c_controls import (
    P15C_AUTHORIZATION_ID,
    P15CControlError,
    load_execution_policy,
    load_target_packet,
    load_target_snapshot,
)

P15C_HOSTED_BUNDLE_SCHEMA_VERSION = 1
P15C_HOSTED_MAX_BASE64_BYTES = 48 * 1024
P15C_HOSTED_MAX_TAR_BYTES = 2 * 1024 * 1024
P15C_HOSTED_MAX_MEMBERS = 65
P15C_HOSTED_MIN_EXPIRY_SECONDS = 60
P15C_HOSTED_MAX_EXPIRY_SECONDS = 3600
P15C_HOSTED_BUNDLE_ENV = "P15C_PRIVATE_BUNDLE_B64"
P15C_HOSTED_DEEPSEEK_ENV = "P15C_DEEPSEEK_API_KEY"
P15C_HOSTED_OPENAI_ENV = "P15C_OPENAI_API_KEY"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_CONTROL_FIELDS = {
    "schema_version",
    "authorization_id",
    "expires_after_seconds",
    "execution_policy",
    "target_packet",
}
_POLICY_TEMPLATE_FIELDS = {
    "schema_version",
    "enabled",
    "total_budget_micro_usd",
    "provider_enabled",
    "provider_budget_micro_usd",
    "private_repository_transfer_enabled",
    "provider_transfer_enabled",
    "allowed_case_ids",
    "max_provider_invocations",
}
_TARGET_TEMPLATE_FIELDS = {
    "schema_version",
    "packet_id",
    "repository_identity",
    "visibility",
    "branch",
    "exact_commit",
    "exact_file_allowlist",
    "content_addressed_inventory",
    "durable_module_contract",
    "inventory_read_authority",
    "benchmark_read_authority",
    "provider_transfer_authority_by_provider",
    "mutation_authority",
}


class P15CHostedBridgeError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class P15CHostedPrivateInputs:
    private_root: Path
    policy_path: Path
    credential_path: Path
    target_packet_path: Path
    ledger_path: Path
    target_file_count: int
    target_total_bytes: int
    policy_sha256: str

    def public_record(self) -> dict[str, object]:
        return {
            "status": "PASS",
            "mode": "hosted-materialize",
            "authorization_id": P15C_AUTHORIZATION_ID,
            "policy_sha256": self.policy_sha256,
            "target_file_count": self.target_file_count,
            "target_total_bytes": self.target_total_bytes,
            "credential_secret_references_resolved": 2,
            "credential_values_recorded": 0,
            "private_target_identity_recorded": False,
            "private_target_paths_recorded": False,
            "provider_invocations": 0,
            "network_operations": 0,
            "benchmark_executions": 0,
            "target_mutations": 0,
            "production_operations": 0,
            "cleanup_operations": 0,
            "rollback_operations": 0,
        }


def materialize_hosted_private_inputs(
    *,
    bundle_base64: str,
    deepseek_api_key: str,
    openai_api_key: str,
    private_root: str | Path,
    expected_commit: str,
    expected_tree: str,
    now: datetime | None = None,
) -> P15CHostedPrivateInputs:
    """Materialize one exact private bundle without exposing its secret values."""

    _validate_api_key(deepseek_api_key, "deepseek")
    _validate_api_key(openai_api_key, "openai")
    commit = _require_sha(expected_commit, "expected commit")
    tree = _require_sha(expected_tree, "expected tree")
    members = _decode_bundle(bundle_base64)
    control = _parse_control(members)
    target_template = _require_mapping(control["target_packet"], "target packet")
    if set(target_template) != _TARGET_TEMPLATE_FIELDS:
        raise P15CHostedBridgeError(
            "HOSTED_TARGET_FIELDS",
            "private target template fields are invalid",
        )
    allowlist = target_template.get("exact_file_allowlist")
    if not isinstance(allowlist, list) or not allowlist:
        raise P15CHostedBridgeError(
            "HOSTED_TARGET_ALLOWLIST",
            "private target allowlist is invalid",
        )
    normalized_allowlist = tuple(_safe_snapshot_path(item) for item in allowlist)
    expected_members = {"control.json"} | {
        f"snapshot/{relative}" for relative in normalized_allowlist
    }
    if set(members) != expected_members:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_FILE_SET",
            "private bundle file set does not match its target allowlist",
        )

    root = _create_private_root(private_root)
    snapshot_root = root / "snapshot"
    _mkdir_owner_only(snapshot_root)
    for relative in normalized_allowlist:
        destination = snapshot_root.joinpath(*PurePosixPath(relative).parts)
        _create_owner_directories(snapshot_root, destination.parent)
        _write_owner_only(destination, members[f"snapshot/{relative}"])

    target_source = dict(target_template)
    target_source["snapshot_root"] = str(snapshot_root)
    target_path = root / "target_packet.json"
    _write_owner_only(target_path, _json_bytes(target_source))
    target_packet = load_target_packet(target_path)
    snapshot = load_target_snapshot(target_packet)

    policy_template = _require_mapping(
        control["execution_policy"], "execution policy"
    )
    if set(policy_template) != _POLICY_TEMPLATE_FIELDS:
        raise P15CHostedBridgeError(
            "HOSTED_POLICY_FIELDS",
            "private execution-policy template fields are invalid",
        )
    expiry_seconds = control["expires_after_seconds"]
    if (
        type(expiry_seconds) is not int
        or expiry_seconds < P15C_HOSTED_MIN_EXPIRY_SECONDS
        or expiry_seconds > P15C_HOSTED_MAX_EXPIRY_SECONDS
    ):
        raise P15CHostedBridgeError(
            "HOSTED_POLICY_EXPIRY",
            "private execution-policy expiry window is invalid",
        )
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise P15CHostedBridgeError(
            "HOSTED_CLOCK",
            "hosted materialization clock must be timezone aware",
        )
    expiry = current.astimezone(timezone.utc) + timedelta(seconds=expiry_seconds)
    policy_source = {
        **dict(policy_template),
        "authorization_id": P15C_AUTHORIZATION_ID,
        "expires_at_utc": expiry.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_tool_system_commit": commit,
        "expected_tool_system_tree": tree,
        "expected_target_packet_sha256": target_packet.packet_sha256,
    }
    policy_path = root / "execution_policy.json"
    _write_owner_only(policy_path, _json_bytes(policy_source))
    policy = load_execution_policy(policy_path)
    policy.assert_active(now=current.astimezone(timezone.utc))

    credential_path = root / "credentials.toml"
    credential_payload = (
        "[providers.deepseek]\n"
        f"api_key = {json.dumps(deepseek_api_key)}\n\n"
        "[providers.openai]\n"
        f"api_key = {json.dumps(openai_api_key)}\n"
    ).encode("utf-8")
    _write_owner_only(credential_path, credential_payload)

    return P15CHostedPrivateInputs(
        private_root=root,
        policy_path=policy_path,
        credential_path=credential_path,
        target_packet_path=target_path,
        ledger_path=root / "usage.sqlite3",
        target_file_count=len(snapshot),
        target_total_bytes=sum(len(item.content.encode("utf-8")) for item in snapshot),
        policy_sha256=policy.policy_sha256,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize the owner-only P15C Hosted execution boundary."
    )
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-tree", required=True)
    parser.add_argument("--bundle-env", default=P15C_HOSTED_BUNDLE_ENV)
    parser.add_argument("--deepseek-key-env", default=P15C_HOSTED_DEEPSEEK_ENV)
    parser.add_argument("--openai-key-env", default=P15C_HOSTED_OPENAI_ENV)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        bundle = _required_environment(arguments.bundle_env, "private bundle")
        deepseek_key = _required_environment(
            arguments.deepseek_key_env, "DeepSeek credential"
        )
        openai_key = _required_environment(
            arguments.openai_key_env, "OpenAI credential"
        )
        result = materialize_hosted_private_inputs(
            bundle_base64=bundle,
            deepseek_api_key=deepseek_key,
            openai_api_key=openai_key,
            private_root=arguments.private_root,
            expected_commit=arguments.expected_commit,
            expected_tree=arguments.expected_tree,
        )
        del bundle, deepseek_key, openai_key
        _print_json(result.public_record())
        return 0
    except (P15CHostedBridgeError, P15CControlError) as exc:
        _print_json(
            {
                "status": "BENCHMARK_BLOCKED",
                "mode": "hosted-materialize",
                "failure_code": exc.code,
                "credential_values_recorded": 0,
                "private_target_identity_recorded": False,
                "private_target_paths_recorded": False,
                "provider_invocations": 0,
                "network_operations": 0,
                "benchmark_executions": 0,
                "target_mutations": 0,
            }
        )
        return 2


def _required_environment(name: object, label: str) -> str:
    if not isinstance(name, str) or not name or "=" in name or "\x00" in name:
        raise P15CHostedBridgeError(
            "HOSTED_ENV_REFERENCE",
            f"{label} environment reference is invalid",
        )
    value = os.environ.get(name)
    if not isinstance(value, str) or not value:
        raise P15CHostedBridgeError(
            "HOSTED_SECRET_UNAVAILABLE",
            f"{label} is unavailable",
        )
    return value


def _validate_api_key(value: object, provider: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > 16_384
        or any(character.isspace() for character in value)
        or "\x00" in value
    ):
        raise P15CHostedBridgeError(
            "HOSTED_CREDENTIAL_INVALID",
            f"{provider} credential is invalid",
        )


def _decode_bundle(value: object) -> dict[str, bytes]:
    if not isinstance(value, str) or not value:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_UNAVAILABLE",
            "private bundle is unavailable",
        )
    try:
        encoded = value.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_ENCODING",
            "private bundle is not canonical base64",
        ) from exc
    if len(encoded) > P15C_HOSTED_MAX_BASE64_BYTES:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_TOO_LARGE",
            "private bundle exceeds its base64 ceiling",
        )
    try:
        compressed = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_ENCODING",
            "private bundle is not canonical base64",
        ) from exc
    if base64.b64encode(compressed) != encoded:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_ENCODING",
            "private bundle is not canonical base64",
        )
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as handle:
            tar_bytes = handle.read(P15C_HOSTED_MAX_TAR_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_GZIP",
            "private bundle gzip payload is invalid",
        ) from exc
    if len(tar_bytes) > P15C_HOSTED_MAX_TAR_BYTES:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_TOO_LARGE",
            "private bundle exceeds its expanded ceiling",
        )
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
            raw_members = archive.getmembers()
            if len(raw_members) > P15C_HOSTED_MAX_MEMBERS:
                raise P15CHostedBridgeError(
                    "HOSTED_BUNDLE_MEMBER_COUNT",
                    "private bundle has too many members",
                )
            members: dict[str, bytes] = {}
            for member in raw_members:
                name = _safe_bundle_member(member.name)
                if not member.isfile() or member.islnk() or member.issym():
                    raise P15CHostedBridgeError(
                        "HOSTED_BUNDLE_MEMBER_TYPE",
                        "private bundle contains a non-regular member",
                    )
                if name in members:
                    raise P15CHostedBridgeError(
                        "HOSTED_BUNDLE_DUPLICATE",
                        "private bundle repeats a member",
                    )
                if member.size < 1 or member.size > P15C_HOSTED_MAX_TAR_BYTES:
                    raise P15CHostedBridgeError(
                        "HOSTED_BUNDLE_MEMBER_SIZE",
                        "private bundle member size is invalid",
                    )
                stream = archive.extractfile(member)
                if stream is None:
                    raise P15CHostedBridgeError(
                        "HOSTED_BUNDLE_MEMBER_READ",
                        "private bundle member is unreadable",
                    )
                payload = stream.read(member.size + 1)
                if len(payload) != member.size:
                    raise P15CHostedBridgeError(
                        "HOSTED_BUNDLE_MEMBER_READ",
                        "private bundle member size drifted",
                    )
                members[name] = payload
    except P15CHostedBridgeError:
        raise
    except (tarfile.TarError, OSError) as exc:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_TAR",
            "private bundle tar payload is invalid",
        ) from exc
    return members


def _parse_control(members: Mapping[str, bytes]) -> dict[str, Any]:
    payload = members.get("control.json")
    if payload is None:
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_MISSING",
            "private bundle control is missing",
        )
    try:
        source = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_INVALID",
            "private bundle control is invalid",
        ) from exc
    if not isinstance(source, dict) or set(source) != _CONTROL_FIELDS:
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_FIELDS",
            "private bundle control fields are invalid",
        )
    if source["schema_version"] != P15C_HOSTED_BUNDLE_SCHEMA_VERSION:
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_SCHEMA",
            "private bundle control schema is invalid",
        )
    if source["authorization_id"] != P15C_AUTHORIZATION_ID:
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_AUTHORIZATION",
            "private bundle authorization does not match P15C",
        )
    return source


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _safe_bundle_member(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 600:
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_PATH",
            "private bundle member path is invalid",
        )
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(
        part in {"", ".", ".."} for part in pure.parts
    ):
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_PATH",
            "private bundle member path is invalid",
        )
    if value != "control.json" and not value.startswith("snapshot/"):
        raise P15CHostedBridgeError(
            "HOSTED_BUNDLE_PATH",
            "private bundle member is outside its allowed roots",
        )
    return value


def _safe_snapshot_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 512:
        raise P15CHostedBridgeError(
            "HOSTED_TARGET_PATH",
            "private target path is invalid",
        )
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(
        part in {"", ".", ".."} for part in pure.parts
    ):
        raise P15CHostedBridgeError(
            "HOSTED_TARGET_PATH",
            "private target path is invalid",
        )
    return value


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise P15CHostedBridgeError(
            "HOSTED_CONTROL_TYPE",
            f"{label} must be an object",
        )
    return value


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise P15CHostedBridgeError(
            "HOSTED_SOURCE_SHA",
            f"{label} is invalid",
        )
    return value


def _create_private_root(value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute() or candidate.exists() or candidate.is_symlink():
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_ROOT",
            "private root must be a new absolute path",
        )
    try:
        parent = candidate.parent.resolve(strict=True)
        metadata = candidate.parent.lstat()
    except OSError as exc:
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_ROOT",
            "private root parent is unavailable",
        ) from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or parent != candidate.parent.absolute()
    ):
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_ROOT",
            "private root parent is unsafe",
        )
    try:
        os.mkdir(candidate, mode=0o700)
        os.chmod(candidate, 0o700)
    except OSError as exc:
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_ROOT",
            "private root could not be created",
        ) from exc
    return candidate.resolve(strict=True)


def _mkdir_owner_only(path: Path) -> None:
    try:
        os.mkdir(path, mode=0o700)
        os.chmod(path, 0o700)
    except OSError as exc:
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_DIRECTORY",
            "private directory could not be created",
        ) from exc


def _create_owner_directories(root: Path, destination: Path) -> None:
    current = root
    relative = destination.relative_to(root)
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            try:
                metadata = current.lstat()
            except OSError as exc:
                raise P15CHostedBridgeError(
                    "HOSTED_PRIVATE_DIRECTORY",
                    "private directory is unavailable",
                ) from exc
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise P15CHostedBridgeError(
                    "HOSTED_PRIVATE_DIRECTORY",
                    "private directory is unsafe",
                )
            continue
        _mkdir_owner_only(current)


def _write_owner_only(path: Path, payload: bytes) -> None:
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, 0o600)
    except OSError as exc:
        raise P15CHostedBridgeError(
            "HOSTED_PRIVATE_FILE",
            "private file could not be created",
        ) from exc


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _print_json(value: object) -> None:
    print(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
