"""Tiny synthetic packaging/compatibility cases; no retail bytes or processes."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("community_distribution", ROOT / "ops/modding/Package-CommunityMod.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-distribution-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = b"123456789"  # Standard CRC32 check vector, not an IW7 FF.
        (self.root / "fixture.ff").write_bytes(self.payload)
        package = json.loads((ROOT / "ops/mod-packages/hud-lua-plan.json").read_text())
        package["files"][0].update(source="fixture.ff", bytes=len(self.payload), sha256=hashlib.sha256(self.payload).hexdigest())
        package["closure"].update(status="complete", evidence_ref="synthetic-only")
        package["closure"]["nodes"][0]["sha256"] = hashlib.sha256(b"synthetic-original-node").hexdigest()
        self.manifest = {"schema": "iw7.community-mod/1", "namespace": package["id"], "package": package,
                         "dependencies": [], "conflicts": [],
                         "requires": {"engine": ["iw7-cp/1"], "client": ["mod-fastfile-download/1", "lua-fastfile/1"],
                                      "server": ["mod-fastfile-host/1"]},
                         "compatibility": {"engine": "iw7", "mode": "cp", "network_protocol": 2,
                                           "client_match": "exact-content", "coexistence": "exclusive-fs-game"},
                         "lifecycle": {"activation": "map-load", "deactivation": "map-unload", "hot_reload": False,
                                       "entrypoints": [{"side": "client", "path": "ui_scripts/paris_hud_probe/__init__.lua", "symbol": "module"}],
                                       "cleanup": ["threads", "player-state"]}}

    def environment(self, manifests=None, **overrides):
        options = dict(client_source=PIN, server_source=PIN, protocol=2, mode="cp")
        options.update(overrides)
        return mod.compat.check_environment(manifests or [self.manifest], **options)

    def other(self, name="support", client=False):
        other = copy.deepcopy(self.manifest)
        other["dependencies"] = []
        other["conflicts"] = []
        other["namespace"] = other["package"]["id"] = name
        other["package"]["native_requirements"]["client_capabilities"] = []
        other["requires"] = {"engine": ["iw7-cp/1"], "client": [], "server": ["gsc-custom-scripts/1"]}
        other["package"]["delivery"] = "mod" if client else "server-only"
        other["compatibility"]["coexistence"] = "exclusive-fs-game" if client else "server-only"
        for item in other["package"]["files"]:
            item["destination"] = f"mods/{name}/mod.ff" if client else f"iw7-mod/custom_scripts/cp/{name}.gsc"
            item["role"] = "client" if client else "server"
        other["package"]["closure"]["nodes"][0]["id"] = "scriptfile:" + name
        return other

    def test_deterministic_bytes_metadata_and_exact_layout(self):
        first = mod.write_archive(self.manifest, self.root, self.root / "one.zip")
        os.utime(self.root / "fixture.ff", (1_000_000, 1_000_000))
        reordered = dict(reversed(list(self.manifest.items())))
        second = mod.write_archive(reordered, self.root, self.root / "two.zip")
        self.assertEqual(first["archive_sha256"], second["archive_sha256"])
        with zipfile.ZipFile(self.root / "one.zip") as archive:
            self.assertEqual(archive.namelist(), ["fastdl/mods/paris_hud_probe/mod.ff", "manifest.json", "server/mods/paris_hud_probe/mod.ff"])
            self.assertEqual(archive.read("manifest.json"), mod.canonical_json(self.manifest))
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 3)
        self.assertEqual(first["files"][0]["aurora_crc32"], "2639F4CB")

    def test_tamper_refuses_and_leaves_no_archive_or_temp(self):
        for data in (b"123456780", b"1", b"1234567890"):
            (self.root / "fixture.ff").write_bytes(data)
            with self.assertRaises(ValueError):
                mod.write_archive(self.manifest, self.root, self.root / "failed.zip")
            self.assertFalse((self.root / "failed.zip").exists())
            self.assertEqual(list(self.root.glob(".iw7-package-*")), [])

    def test_source_replacement_between_duplicate_writes_fails(self):
        original = mod.stream_payload
        calls = 0
        def replacing(*args):
            nonlocal calls
            result = original(*args)
            calls += 1
            if calls == 1:
                (self.root / "fixture.ff").write_bytes(b"changed!!")
            return result
        with patch.object(mod, "stream_payload", replacing):
            with self.assertRaises(ValueError):
                mod.write_archive(self.manifest, self.root, self.root / "failed.zip")
        self.assertFalse((self.root / "failed.zip").exists())

    def test_no_overwrite_and_budget_precedes_payload_reads(self):
        destination = self.root / "keep.zip"
        destination.write_bytes(b"preserve")
        with self.assertRaises(ValueError):
            mod.write_archive(self.manifest, self.root, destination)
        self.assertEqual(destination.read_bytes(), b"preserve")
        with patch.object(mod, "stream_payload", side_effect=AssertionError("Must not read")):
            with self.assertRaisesRegex(ValueError, "budget"):
                mod.write_archive(self.manifest, self.root, self.root / "large.zip", max_bytes=20)
        self.assertFalse((self.root / "large.zip").exists())
        with self.assertRaisesRegex(ValueError, "verification.*budget"):
            mod.preflight_payload_budget([(self.manifest, self.root)], 1)
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            (self.root / "fixture.ff").write_bytes(b"bad")
            mod.preflight_payload_budget([(self.manifest, self.root)], 1024)

    def test_final_name_race_preserves_other_output(self):
        original = os.link
        def racing(source, destination):
            Path(destination).write_bytes(b"created by other task")
            return original(source, destination)
        with patch.object(mod.os, "link", racing):
            with self.assertRaises(FileExistsError):
                mod.write_archive(self.manifest, self.root, self.root / "raced.zip")
        self.assertEqual((self.root / "raced.zip").read_bytes(), b"created by other task")
        self.assertEqual(list(self.root.glob(".iw7-package-*")), [])

    def test_no_incidental_directory_files(self):
        (self.root / "secrets.local").write_text("never package")
        (self.root / "launcher.exe").write_bytes(b"never package")
        mod.write_archive(self.manifest, self.root, self.root / "safe.zip")
        with zipfile.ZipFile(self.root / "safe.zip") as archive:
            self.assertFalse(any("secrets" in name or "launcher" in name for name in archive.namelist()))

    def test_traversal_and_symlink_boundary(self):
        with self.assertRaises(ValueError):
            mod.payload_path(self.root, "../fixture.ff")
        link = self.root / "redirect.ff"
        try:
            link.symlink_to(self.root / "fixture.ff")
        except OSError:
            self.skipTest("Host does not grant symlink creation")
        with self.assertRaisesRegex(ValueError, "Redirected"):
            mod.payload_path(self.root, "redirect.ff")

    def test_json_duplicate_nonfinite_and_oversize_refused(self):
        path = self.root / "manifest.json"
        for value in ('{"schema":1,"schema":2}', '{"value":NaN}', ' ' * (mod.MAX_MANIFEST + 1)):
            path.write_text(value)
            with self.assertRaises(ValueError):
                mod.read_manifest(path)

    def test_protocol_mode_source_and_usermap_fail_closed(self):
        self.assertEqual(self.environment(), [])
        for options in (dict(protocol=3), dict(mode="mp"), dict(client_source="f" * 40), dict(server_source="f" * 40)):
            self.assertTrue(self.environment(**options), options)
        self.manifest["package"]["delivery"] = "usermap"
        self.assertTrue(any("Usermap" in value for value in self.environment()))
        server_only = self.other()
        server_only["compatibility"]["network_protocol"] = 3
        self.assertTrue(any("source protocol" in value for value in self.environment([server_only], protocol=3)))

    def test_dependencies_missing_version_cycle_and_conflict(self):
        self.manifest["dependencies"] = [{"id": "support", "version": "0.1.0"}]
        self.assertTrue(any("Missing" in value for value in self.environment()))
        other = self.other()
        self.assertEqual(self.environment([self.manifest, other]), [])
        other["package"]["version"] = "9.0.0"
        self.assertTrue(any("version" in value for value in self.environment([self.manifest, other])))
        other["package"]["version"] = "0.1.0"
        other["dependencies"] = [{"id": "paris_hud_probe", "version": "0.1.0"}]
        self.assertTrue(any("cycle" in value for value in self.environment([self.manifest, other])))
        other["dependencies"] = []
        other["conflicts"] = [{"id": "paris_hud_probe", "reason": "test"}]
        self.assertTrue(any("conflict" in value for value in self.environment([self.manifest, other])))

    def test_multiple_fs_game_and_collisions(self):
        self.assertTrue(any("one active fs_game" in value for value in self.environment([self.manifest, self.other(client=True)])))
        self.assertTrue(any("Duplicate" in value for value in self.environment([self.manifest, self.manifest])))
        other = self.other()
        other["package"]["files"][0]["destination"] = self.manifest["package"]["files"][0]["destination"].upper()
        other["package"]["closure"]["nodes"][0]["id"] = self.manifest["package"]["closure"]["nodes"][0]["id"].upper()
        errors = self.environment([self.manifest, other])
        self.assertTrue(any("destination collision" in value for value in errors))
        self.assertTrue(any("asset collision" in value for value in errors))

    def test_unknown_capability_and_unproven_source_blocked(self):
        self.manifest["requires"]["client"].append("future-loader/1")
        self.assertTrue(any("Capability source proof missing" in value for value in self.environment()))
        self.manifest["requires"]["client"].remove("future-loader/1")
        self.manifest["requires"]["engine"].append("model-netconststrings/1")
        self.assertTrue(any("Capability source proof missing" in value for value in self.environment(server_source="36f7afedb9e4c8c665b6e29227e3f5c660ed63d6")))

    def cli(self, manifest=None, *extra):
        sdk_root = os.environ.get("IW7_MODDING_SDK_ROOT", str(ROOT / "sdk/modding"))
        if not (Path(sdk_root) / "manifest.py").is_file():
            self.fail("Common SDK missing. Integrate SDK commit or set IW7_MODDING_SDK_ROOT to its reviewed local directory.")
        path = self.root / "input.json"
        path.write_bytes(mod.canonical_json(manifest or self.manifest))
        run = subprocess.run([sys.executable, str(ROOT / "ops/modding/Package-CommunityMod.py"), str(path),
                              "--root", str(self.root), "--output", str(self.root / "cli.zip"),
                              "--sdk-root", sdk_root, "--client-source", PIN, "--server-source", PIN,
                              "--protocol", "2", *extra], capture_output=True, text=True, timeout=15)
        self.assertFalse(run.stderr, run.stderr)
        return run.returncode, json.loads(run.stdout)

    def test_real_sdk_cli_success_is_not_deployment(self):
        code, result = self.cli()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["packaged"])
        self.assertFalse(result["ready_to_deploy"])
        self.assertFalse(self.manifest["package"]["evidence"][0]["status"] == "pass")

    def test_real_sdk_cli_rejects_bad_contract_missing_native_and_dependency(self):
        for mutate in (lambda m: m.update(unexpected=True),
                       lambda m: m["package"]["native_requirements"].update(client_source=PIN),
                       lambda m: m["dependencies"].append({"id": "absent", "version": "1.0.0"}),
                       lambda m: m["package"]["closure"].update(status="incomplete")):
            candidate = copy.deepcopy(self.manifest)
            mutate(candidate)
            code, result = self.cli(candidate)
            self.assertEqual(code, 1, result)
            self.assertFalse(result["packaged"])
            self.assertFalse((self.root / "cli.zip").exists())

    def test_real_sdk_cli_native_requirement_needs_explicit_target(self):
        self.manifest["package"]["native_requirements"]["client_source"] = PIN
        code, result = self.cli(self.manifest, "--target", "native")
        self.assertEqual(code, 0, result)

    def test_real_sdk_cli_rejects_arbitrary_native_payload(self):
        self.manifest["package"]["files"][0]["destination"] = "mods/paris_hud_probe/loader.dll"
        code, result = self.cli()
        self.assertEqual(code, 1, result)
        self.assertFalse((self.root / "cli.zip").exists())

    def test_real_sdk_cli_validates_active_dependency_bytes(self):
        other = self.other()
        node = other["package"]["closure"]["nodes"][0]
        node.update(id="scriptfile:custom_scripts/cp/support.gsc", kind="scriptfile", scope="server")
        other["package"]["closure"]["roots"] = [node["id"]]
        other["package"]["files"][0].update(source="support.gsc", closure_roots=[node["id"]])
        other["lifecycle"]["entrypoints"] = [{"side": "server", "path": "custom_scripts/cp/support.gsc", "symbol": "init"}]
        (self.root / "support.gsc").write_bytes(self.payload)
        path = self.root / "support.json"
        path.write_bytes(mod.canonical_json(other))
        self.manifest["dependencies"] = [{"id": "support", "version": "0.1.0"}]
        code, result = self.cli(self.manifest, "--active", str(path), str(self.root))
        self.assertEqual(code, 0, result)
        (self.root / "cli.zip").unlink()
        (self.root / "support.gsc").write_bytes(b"corrupted")
        code, result = self.cli(self.manifest, "--active", str(path), str(self.root))
        self.assertEqual(code, 1, result)
        self.assertFalse((self.root / "cli.zip").exists())


if __name__ == "__main__":
    unittest.main()
