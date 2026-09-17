"""Build the packaged projection of the sole task-manifest schema authority."""

from pathlib import Path

from setuptools.command.build_py import build_py


class BuildPy(build_py):
    """Include the canonical schema in both source and wheel distributions."""

    def run(self):
        super().run()
        destination = Path(self.build_lib) / "tool_system/manifest/task_manifest.schema.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        # No independently maintained second schema and no fallback on build failure.
        destination.write_bytes(Path("harness/task_manifest.schema.json").read_bytes())

    def get_source_files(self):
        return [*super().get_source_files(), "harness/build_support.py",
                "harness/task_manifest.schema.json"]

    def get_outputs(self, include_bytecode=1):
        return [*super().get_outputs(include_bytecode),
                str(Path(self.build_lib) / "tool_system/manifest/task_manifest.schema.json")]
