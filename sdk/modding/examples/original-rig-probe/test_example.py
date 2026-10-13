"""Existing SDK/Creator gates for an observed original rig plan; no game inputs."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import json
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location("original_rig_sdk", ROOT / "sdk/modding/manifest.py")
sdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdk)
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


class OriginalRigPlanTests(unittest.TestCase):
    def setUp(self):
        self.manifest = sdk.load_manifest(HERE / "manifest.json")

    def test_generic_plan_keeps_missing_sources_and_runtime_pending(self):
        result = sdk.validate(self.manifest, stage="plan", client_source=PIN, server_source=PIN)
        self.assertTrue(result["valid"], result["errors"])
        for flag in ("ready", "runtime_ready", "owner_accepted"):
            self.assertFalse(result[flag])
        self.assertEqual(result["checked"], [])
        self.assertEqual(self.manifest["package"]["closure"]["status"], "incomplete")
        self.assertTrue(all(record["status"] == "pending" for record in self.manifest["package"]["evidence"]))

    def test_asset_observation_is_not_mislabeled_as_rigid_or_bo3(self):
        nodes = {n["id"]: n for n in self.manifest["package"]["closure"]["nodes"]}
        self.assertEqual(len(nodes), 8)  # Seven inventoried assets plus the proposed server source.
        self.assertFalse(any(n.startswith("netconststrings:") for n in nodes))
        self.assertEqual(nodes["xanim:paris_original_probe_bend"]["kind"], "anim")
        self.assertEqual(nodes["material:mopw/character_park_clown_zombie_shoes"]["scope"], "recipient")
        self.assertEqual(self.manifest["requires"]["client"], ["mod-fastfile-download/1"])
        self.assertIsNone(self.manifest["package"]["files"][1]["source"])

    def test_package_refuses_missing_lifecycle_and_incomplete_closure(self):
        result = sdk.validate(self.manifest, root=HERE, stage="package", client_source=PIN, server_source=PIN)
        self.assertFalse(result["valid"])
        self.assertFalse(result["ready"])
        self.assertIn("package: Dependency closure incomplete", result["errors"])

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell required")
    def test_real_creator_plan_is_read_only_and_animation_adapter_stays_explicit(self):
        before = {p: p.read_bytes() for p in HERE.iterdir() if p.is_file()}
        base = [shutil.which("pwsh"), "-NoProfile", "-File", str(ROOT / "sdk/modding/Creator.ps1"),
                "-Project", str(HERE), "-Action", "Plan", "-ClientSource", PIN,
                "-ServerSource", PIN, "-Protocol", "2", "-Json"]
        result = subprocess.run(base + ["-Adapter", "None"], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["plan_valid"])
        for flag in ("bindings_written", "build_executed", "build_verified", "materialized", "packaged", "runtime_ready", "owner_accepted"):
            self.assertFalse(report[flag])
        blocked = subprocess.run(base + ["-Adapter", "AnimationProbe"], capture_output=True, text=True, timeout=20)
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        self.assertIn("not connected", " ".join(json.loads(blocked.stdout)["errors"]))
        self.assertEqual(before, {p: p.read_bytes() for p in HERE.iterdir() if p.is_file()})


if __name__ == "__main__":
    unittest.main()
