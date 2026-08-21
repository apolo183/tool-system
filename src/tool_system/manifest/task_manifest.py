from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import yaml

_TASK_MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "harness" / "task_manifest.schema.json"
)


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("YAML root must be a mapping")
    return value


def validate_manifest_structure(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    non_json_reasons = _non_json_reasons(manifest)
    if non_json_reasons:
        return False, non_json_reasons

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return False, [
            "TASK_MANIFEST_SCHEMA_UNAVAILABLE detail=dependency_missing"
        ]

    try:
        schema_text = _TASK_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError:
        return False, ["TASK_MANIFEST_SCHEMA_UNAVAILABLE detail=read_failed"]

    try:
        schema = json.loads(schema_text)
        _guard_local_schema(schema)
        Draft202012Validator.check_schema(schema)
    except (TypeError, ValueError):
        return False, ["TASK_MANIFEST_SCHEMA_INVALID detail=preparation_failed"]
    except Exception:
        return False, ["TASK_MANIFEST_SCHEMA_INVALID detail=metaschema_failed"]

    try:
        errors = tuple(Draft202012Validator(schema).iter_errors(manifest))
    except Exception:
        return False, ["TASK_MANIFEST_SCHEMA_INVALID detail=resolution_failed"]

    records = {
        (
            _pointer(tuple(error.absolute_path)),
            _pointer(tuple(error.absolute_schema_path)),
            str(error.validator),
            _normalized_detail(error),
        )
        for error in errors
    }
    reasons = [
        "TASK_MANIFEST_SCHEMA_VIOLATION "
        f"instance={instance_pointer} schema={schema_pointer} "
        f"keyword={keyword} detail={detail}"
        for instance_pointer, schema_pointer, keyword, detail in sorted(records)
    ]
    return not reasons, reasons


def _pointer(parts: tuple[object, ...]) -> str:
    if not parts:
        return ""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


def _type_code(value: object) -> str:
    if isinstance(value, tuple):
        return "TUPLE"
    if isinstance(value, bytes):
        return "BYTES"
    if isinstance(value, set):
        return "SET"
    if isinstance(value, float) and not math.isfinite(value):
        return "NON_FINITE_FLOAT"
    return "CUSTOM_VALUE"


def _non_json_reasons(value: object) -> list[str]:
    records: set[tuple[str, str]] = set()

    def walk(current: object, path: tuple[object, ...], ancestors: set[int]) -> None:
        if current is None or isinstance(current, (bool, int, str)):
            return
        if isinstance(current, float):
            if not math.isfinite(current):
                records.add((_pointer(path), "NON_FINITE_FLOAT"))
            return
        if isinstance(current, (dict, list)):
            identity = id(current)
            if identity in ancestors:
                records.add((_pointer(path), "CYCLIC_CONTAINER"))
                return
            ancestors.add(identity)
            try:
                if isinstance(current, dict):
                    for key in current:
                        if not isinstance(key, str):
                            records.add((_pointer(path), "NON_STRING_KEY"))
                            continue
                        walk(current[key], (*path, key), ancestors)
                else:
                    for index, item in enumerate(current):
                        walk(item, (*path, index), ancestors)
            finally:
                ancestors.remove(identity)
            return
        records.add((_pointer(path), _type_code(current)))

    walk(value, (), set())
    return [
        f"TASK_MANIFEST_NON_JSON_VALUE instance={pointer} type={type_code}"
        for pointer, type_code in sorted(records)
    ]


def _guard_local_schema(schema: object) -> None:
    def walk(node: object, *, root: bool) -> None:
        if isinstance(node, dict):
            if not root and "$id" in node:
                raise ValueError("nested schema identity is prohibited")
            for prohibited in ("$dynamicRef", "$recursiveRef"):
                if prohibited in node:
                    raise ValueError("dynamic schema reference is prohibited")
            if "$ref" in node:
                reference = node["$ref"]
                if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
                    raise ValueError("non-local schema reference is prohibited")
            for value in node.values():
                walk(value, root=False)
        elif isinstance(node, list):
            for value in node:
                walk(value, root=False)

    walk(schema, root=True)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalized_detail(error: Any) -> str:
    keyword = str(error.validator)
    constraint = error.validator_value
    if keyword == "required" and isinstance(error.instance, dict):
        missing = sorted(set(constraint) - set(error.instance))
        return "missing=" + _canonical_json(missing)
    if keyword == "additionalProperties" and isinstance(error.instance, dict):
        properties = error.schema.get("properties", {})
        allowed = set(properties) if isinstance(properties, dict) else set()
        unknown = sorted(key for key in error.instance if key not in allowed)
        return "unknown=" + _canonical_json(unknown)
    if keyword == "type":
        return "expected=" + _canonical_json(constraint)
    if keyword == "enum":
        return "allowed=" + _canonical_json(constraint)
    if keyword == "const":
        return "expected=" + _canonical_json(constraint)
    if keyword == "pattern":
        return "pattern=" + _canonical_json(constraint)
    if keyword in {"minLength", "maxLength", "minItems", "maxItems"}:
        return "limit=" + _canonical_json(constraint)
    return "constraint=" + _canonical_json(constraint)
