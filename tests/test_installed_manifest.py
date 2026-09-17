"""Exercise a non-editable wheel built from the source distribution, outside checkout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import zipfile

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_sdist_wheel_installs_canonical_manifest_schema(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(ROOT / "pyproject.toml", source)
    shutil.copytree(ROOT / "src", source / "src", ignore=shutil.ignore_patterns(
        "__pycache__", "*.egg-info", "task_manifest.schema.json"))
    (source / "harness").mkdir()
    for name in ("build_support.py", "task_manifest.schema.json"):
        shutil.copy2(ROOT / "harness" / name, source / "harness" / name)
    dist = tmp_path / "dist"
    # The default build makes an sdist and builds its wheel from that sdist.
    built = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist), str(source)],
        cwd=tmp_path, text=True, capture_output=True, timeout=120,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    canonical = (ROOT / "harness/task_manifest.schema.json").read_bytes()
    with tarfile.open(next(dist.glob("*.tar.gz"))) as archive:
        members = [m for m in archive.getmembers()
                   if m.name.endswith("/harness/task_manifest.schema.json")]
        assert len(members) == 1
        assert archive.extractfile(members[0]).read() == canonical
        assert any(m.name.endswith("/harness/build_support.py") for m in archive.getmembers())
    wheel = next(dist.glob("*.whl"))
    resource = "tool_system/manifest/task_manifest.schema.json"
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read(resource) == canonical
    installed = tmp_path / "installed"
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--no-compile",
         "--target", str(installed), str(wheel)],
        cwd=tmp_path, text=True, capture_output=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = yaml.safe_load((ROOT / "tests/fixtures/manifest_validation/forward_valid_task_manifest_v1.yaml").read_text())
    manifest_path = tmp_path / "valid.json"
    manifest_path.write_text(json.dumps(manifest))
    outside = tmp_path / "outside"
    outside.mkdir()
    # -I -S excludes cwd, environment paths, and editable .pth hooks. Dependency
    # directories are added as plain paths; their .pth files are never executed.
    script = r'''
import hashlib, json, sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from tool_system.manifest import task_manifest as module
assert Path(module.__file__).is_relative_to(Path(sys.argv[1]))
assert Path(module._TASK_MANIFEST_SCHEMA_PATH).is_relative_to(Path(sys.argv[1]))
assert hashlib.sha256(module._TASK_MANIFEST_SCHEMA_PATH.read_bytes()).hexdigest() == sys.argv[4]
manifest = json.loads(Path(sys.argv[3]).read_text())
assert module.validate_manifest_structure(manifest) == (True, [])
manifest['unexpected_field'] = True
ok, reasons = module.validate_manifest_structure(manifest)
assert not ok and any('TASK_MANIFEST_SCHEMA_VIOLATION' in reason for reason in reasons)
module._TASK_MANIFEST_SCHEMA_PATH.unlink()
ok, reasons = module.validate_manifest_structure(manifest)
assert not ok and reasons == ['TASK_MANIFEST_SCHEMA_UNAVAILABLE detail=read_failed']
print('INSTALLED_SDIST_WHEEL_SCHEMA_PASS')
'''
    checked = subprocess.run(
        [sys.executable, "-I", "-S", "-c", script, str(installed),
         sysconfig.get_path("purelib"), str(manifest_path), hashlib.sha256(canonical).hexdigest()],
        cwd=outside, text=True, capture_output=True, timeout=30,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert checked.stdout.strip() == "INSTALLED_SDIST_WHEEL_SCHEMA_PASS"
