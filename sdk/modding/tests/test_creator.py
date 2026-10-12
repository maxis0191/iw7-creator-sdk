"""Real Creator CLI tests using existing Python gates; no native adapter executes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SDK = Path(__file__).resolve().parents[1]
REPO = SDK.parents[1]
TOOLS = Path(os.environ.get("IW7_CREATOR_TEST_TOOLS_ROOT", REPO))
PWSH = shutil.which("pwsh")
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


@unittest.skipUnless(PWSH, "PowerShell 7 is required for the real Creator CLI")
class CreatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.manifest = json.loads((SDK / "examples/beacon/manifest.json").read_text())
        self.save_manifest()
        (self.project / "sdk_beacon.gsc").write_bytes((SDK / "examples/beacon/sdk_beacon.gsc").read_bytes())
        self.addCleanup(self.temp.cleanup)

    def save_manifest(self):
        (self.project / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def invoke(self, *extra, environment=True):
        before = self.snapshot()
        args = [PWSH, "-NoProfile", "-File", str(SDK / "Creator.ps1"), "-Project", str(self.project),
                "-ToolsRoot", str(TOOLS), "-Json"]
        if environment:
            args += ["-ClientSource", PIN, "-ServerSource", PIN, "-Protocol", "2"]
        run = subprocess.run([*args, *extra], text=True, capture_output=True, timeout=20)
        self.assertEqual(run.stderr, "", run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(before, self.snapshot(), "Plan/refused Build wrote or modified a file")
        self.assertFalse(report["build_executed"])
        self.assertFalse(report["materialized"])
        self.assertFalse(report["packaged"])
        self.assertFalse(report["runtime_ready"])
        self.assertFalse(report["owner_accepted"])
        return run.returncode, report

    def test_real_plan_and_exact_adapter_identity(self):
        code, report = self.invoke("-Adapter", "BeaconV1")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["plan_valid"])
        self.assertTrue(report["pending"])
        steps = {s["name"]: s for s in report["steps"]}
        self.assertEqual(steps["dependencies-and-target"]["status"], "passed")
        self.assertEqual(steps["adapter-plan"]["status"], "pending")
        self.assertEqual(steps["package"]["status"], "not-run")

    def test_missing_environment_is_not_qualified(self):
        code, report = self.invoke(environment=False)
        self.assertEqual(code, 1)
        self.assertFalse(report["plan_valid"])
        self.assertTrue(any("Supply ClientSource" in p for p in report["pending"]))

    def test_missing_dependency_is_checked_by_real_distribution(self):
        self.manifest["dependencies"] = [{"id": "missing_mod", "version": "1.0.0"}]
        self.save_manifest()
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("Missing exact dependency", " ".join(report["errors"]))

    def test_active_collision_is_checked(self):
        code, report = self.invoke("-ActiveProject", str(self.project))
        self.assertEqual(code, 1)
        self.assertIn("Namespace collision", " ".join(report["errors"]))

    def test_edited_gsc_is_not_accepted_as_fixed_beacon(self):
        with (self.project / "sdk_beacon.gsc").open("ab") as output:
            output.write(b"\n// changed project\n")
        code, report = self.invoke("-Adapter", "BeaconV1")
        self.assertEqual(code, 1)
        self.assertIn("exact reviewed template GSC", " ".join(report["errors"]))

    def test_build_refuses_before_any_mutation(self):
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1",
                                   "-FinalizeRoot", str(self.root / "candidate"),
                                   "-Output", str(self.root / "result.zip"))
        self.assertEqual(code, 1)
        self.assertIn("Build chain is not connected", " ".join(report["errors"]))
        self.assertFalse((self.root / "candidate").exists())
        self.assertFalse((self.root / "result.zip").exists())

    def test_parameter_file_cannot_smuggle_run(self):
        parameters = self.root / "parameters.json"
        parameters.write_text(json.dumps({"SourceRoot": str(self.project), "Run": "false"}))
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameters))
        self.assertEqual(code, 1)
        self.assertIn("unknown fields", " ".join(report["errors"]))

    def test_named_future_adapter_is_not_a_fake_success(self):
        code, report = self.invoke("-Adapter", "AnimationProbe")
        self.assertEqual(code, 1)
        self.assertIn("not connected or qualified", " ".join(report["errors"]))

    def test_missing_builder_parameters_refuse_without_interactive_prompt(self):
        parameters = self.root / "parameters.json"
        parameters.write_text(json.dumps({"SourceRoot": str(self.project), "OpsRoot": str(TOOLS / "ops")}))
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameters))
        self.assertEqual(code, 1)
        self.assertIn("missing required fields", " ".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
