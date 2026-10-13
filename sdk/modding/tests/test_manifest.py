"""Asset-free contract regression tests. No native compiler, game or network."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manifest
import prepare_beacon


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.plan = manifest.load_manifest(manifest.HERE / "examples/beacon/manifest.json")

    def invalid(self, data, fragment=None, **kwargs):
        report = manifest.validate(data, **kwargs)
        self.assertFalse(report["valid"], report)
        self.assertFalse(report["ready"], report)
        if fragment:
            self.assertIn(fragment, " ".join(report["errors"]))

    def test_example_is_a_plan_only(self):
        report = manifest.validate(self.plan)
        self.assertTrue(report["valid"], report)
        self.assertFalse(report["ready"])
        self.assertFalse(report["runtime_ready"])
        self.assertFalse(report["owner_accepted"])
        self.assertTrue(report["pending"])
        self.invalid(self.plan, stage="package")

    def test_unknown_and_missing_keys_fail_at_each_contract_object(self):
        for path in [(), ("requires",), ("lifecycle",), ("compatibility",), ("package",)]:
            for change in ("extra", "missing"):
                with self.subTest(path=path, change=change):
                    data = copy.deepcopy(self.plan)
                    obj = data
                    for key in path:
                        obj = obj[key]
                    if change == "extra":
                        obj["quietly_ignored"] = True
                    else:
                        obj.pop(next(iter(obj)))
                    self.invalid(data)

    def test_malformed_types_fail_closed(self):
        for value in [None, True, [], "v1", 12]:
            self.invalid(value)
        for key in self.plan:
            data = copy.deepcopy(self.plan)
            data[key] = ["wrong-shape"]
            self.invalid(data)
        data = copy.deepcopy(self.plan)
        data["package"]["closure"]["nodes"] = [False]
        self.invalid(data)

    def test_schema_and_namespace_are_exact(self):
        for key, value in [("schema", "iw7.community-mod/2"), ("namespace", "other"), ("namespace", "../bad")]:
            data = copy.deepcopy(self.plan)
            data[key] = value
            self.invalid(data)

    def test_capability_side_unknown_and_asset_requirements(self):
        data = copy.deepcopy(self.plan)
        data["requires"]["server"].append("imaginary/1")
        self.invalid(data, "Unknown capability")
        data = copy.deepcopy(self.plan)
        data["requires"]["server"].append("xmodel-rigid/1")
        self.invalid(data, "wrong side")
        for side, capability in [("engine", "model-netconststrings/1"), ("client", "xmodel-rigid/1"),
                                 ("server", "gsc-custom-scripts/1"), ("client", "mod-fastfile-download/1")]:
            data = copy.deepcopy(self.plan)
            data["requires"][side].remove(capability)
            self.invalid(data, "Missing capability")

    def test_blocked_capability_is_not_runtime_support(self):
        data = copy.deepcopy(self.plan)
        data["requires"]["client"].append("h1-rigid-import/1")
        report = manifest.validate(data)
        self.assertTrue(report["valid"])
        self.assertIn("Capability not qualified", " ".join(report["pending"]))

    def test_explicit_skeletal_plan_does_not_borrow_rigid_cube_capabilities(self):
        data = manifest.load_manifest(manifest.HERE / "examples/original-rig-probe/manifest.json")
        report = manifest.validate(data)
        self.assertTrue(report["valid"], report)
        self.assertIn("Capability not qualified: skeletal-animation-import/1", report["pending"])
        self.assertEqual(report["capability_evidence"]["skeletal-animation-import/1"], "blocked")
        self.assertNotIn("xmodel-rigid/1", data["requires"]["client"])
        self.assertNotIn("model-netconststrings/1", data["requires"]["engine"])
        self.assertFalse(report["runtime_ready"])
        data["requires"]["client"].remove("skeletal-animation-import/1")
        self.invalid(data, "Missing capability: client/skeletal-animation-import/1")

    def test_protocol_type_and_modality(self):
        for value in [True, 0, -1, 65536, "2", [], {}]:
            data = copy.deepcopy(self.plan)
            data["compatibility"]["network_protocol"] = value
            self.invalid(data)
        data = copy.deepcopy(self.plan)
        data["compatibility"]["network_protocol"] = None
        self.assertTrue(manifest.validate(data)["valid"])
        for key, value in [("engine", "h1"), ("mode", "mp"), ("coexistence", "server-only")]:
            data = copy.deepcopy(self.plan)
            data["compatibility"][key] = value
            self.invalid(data)

    def test_dependencies_and_conflicts(self):
        for dependencies in [[{"id": "sdk_beacon", "version": "1.0.0"}],
                             [{"id": "common", "version": "^1.0.0"}],
                             [{"id": "common", "version": "01.0.0"}],
                             [{"id": "common", "version": "1.0.0"}] * 2]:
            data = copy.deepcopy(self.plan)
            data["dependencies"] = dependencies
            self.invalid(data)
        data = copy.deepcopy(self.plan)
        data["dependencies"] = [{"id": "paris_model_probe", "version": "1.0.0"}]
        self.invalid(data, "required conflict")
        data = copy.deepcopy(self.plan)
        data["dependencies"] = [{"id": "shared_gsc", "version": "1.2.3"}]
        self.assertTrue(manifest.validate(data)["valid"])
        # Actual installed version, cycles and bidirectional conflicts belong
        # to the separate distribution graph checker, not this single manifest.

    def test_lifecycle_and_cleanup(self):
        for key, value in [("hot_reload", True), ("activation", "hot"), ("entrypoints", [])]:
            data = copy.deepcopy(self.plan)
            data["lifecycle"][key] = value
            self.invalid(data)
        for kind in ["entities", "hud", "threads", "player-state"]:
            data = copy.deepcopy(self.plan)
            data["lifecycle"]["cleanup"].remove(kind)
            self.invalid(data, "cleanup")

    def test_entrypoint_cannot_escape_or_invent_loader(self):
        for path in ["../custom_scripts/cp/sdk_beacon.gsc", "scripts/other.gsc", "C:/evil.gsc", "scripts/CON.gsc"]:
            data = copy.deepcopy(self.plan)
            data["lifecycle"]["entrypoints"][0]["path"] = path
            self.invalid(data)
        data = copy.deepcopy(self.plan)
        data["lifecycle"]["entrypoints"] *= 2
        self.invalid(data, "Duplicate")

    def test_existing_transport_is_authoritative(self):
        for destination in ["../mod.ff", "mods/sdk_beacon/mod.pak", "mods/sdk_beacon/iw7.exe"]:
            data = copy.deepcopy(self.plan)
            data["package"]["files"][0]["destination"] = destination
            self.invalid(data)
        data = copy.deepcopy(self.plan)
        data["package"]["closure"]["nodes"][1]["requires"].append("unlisted")
        self.invalid(data, "Dependency not inventoried")

    def test_loader_rejects_duplicate_nonfinite_large_and_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for raw in [b'{"schema":1,"schema":2}', b'{"x":NaN}', b'{"x":1e999}', b'{' + b' ' * (1024 * 1024), b'{invalid']:
                path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    manifest.load_manifest(path)

    def test_normalized_package_version(self):
        self.plan["package"]["version"] = "01.0.0"
        self.invalid(self.plan, "normalized")

    def test_bounded_mutations_never_raise_or_claim_runtime(self):
        import random
        rng = random.Random(71012)
        paths = []
        def inventory(node, path):
            if isinstance(node, dict):
                for key, value in node.items():
                    paths.append(path + [key])
                    inventory(value, path + [key])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    paths.append(path + [index])
                    inventory(value, path + [index])
        inventory(self.plan, [])
        for _ in range(300):
            data = copy.deepcopy(self.plan)
            path = rng.choice(paths)
            node = data
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = rng.choice([None, False, 2.5, {}, [False], "../bad"])
            report = manifest.validate(data)
            self.assertFalse(report["ready"])
            self.assertFalse(report["runtime_ready"])
            self.assertFalse(report["owner_accepted"])

    def source_package(self, root):
        data = copy.deepcopy(self.plan)
        data["requires"] = {"engine": ["iw7-cp/1"], "client": [], "server": ["gsc-custom-scripts/1"]}
        data["compatibility"]["coexistence"] = "server-only"
        package = data["package"]
        package["delivery"] = "server-only"
        package["files"] = [package["files"][1]]
        contents = b"// synthetic fixture, not a linked game script\n"
        (root / "sdk_beacon.gsc").write_bytes(contents)
        digest = hashlib.sha256(contents).hexdigest()
        package["files"][0].update(bytes=len(contents), sha256=digest)
        node = package["closure"]["nodes"][0]
        node.update(requires=[], sha256=digest)
        package["closure"] = {"status": "complete", "roots": [node["id"]], "nodes": [node],
                              "unresolved": [], "evidence_ref": "synthetic unit test"}
        return data

    def test_package_hash_tamper_and_null_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.source_package(root)
            report = manifest.validate(data, root=root, stage="package")
            self.assertTrue(report["ready"], report)
            self.assertFalse(report["runtime_ready"])
            self.assertFalse(report["owner_accepted"])
            data["compatibility"]["network_protocol"] = None
            self.invalid(data, "network_protocol", root=root, stage="package")
            data["compatibility"]["network_protocol"] = 2
            (root / "sdk_beacon.gsc").write_bytes(b"changed")
            self.invalid(data, "hash mismatch", root=root, stage="package")

    def test_blocked_capability_rejects_otherwise_complete_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.source_package(root)
            data["requires"]["client"].append("h1-rigid-import/1")
            self.invalid(data, "Capability not qualified", root=root, stage="package")

    def test_skeletal_capability_cannot_promote_an_otherwise_complete_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.source_package(root)
            data["requires"]["client"].append("skeletal-animation-import/1")
            self.invalid(data, "Capability not qualified: skeletal-animation-import/1", root=root, stage="package")

    def test_delivery_does_not_inherit_package_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.invalid(self.source_package(root), root=root, stage="delivery")

    def test_prepare_uses_bounded_original_writer_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = root / "writer"
            writer.mkdir()
            # Only synthetic tiny byte strings; this test does not claim an
            # engine format roundtrip. Actual format validation is upstream.
            artifacts = []
            for name in ("xmodel/paris_model_probe.xmb", "xsurface/paris_model_probe_lod0.xsb"):
                path = writer / "artifacts" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic")
                artifacts.append({"Path": name, "Bytes": 9, "SHA256": hashlib.sha256(b"synthetic").hexdigest().upper()})
            material = "mopw/character_park_clown_zombie_shoes"
            metadata = {"lod0_dist": 1000000, "has_lods": True, "shadow_cutoff_lod": 6, "collision_lod": 255,
                        "material_reference": material, "candidate_variable": "lodInfo[0].dist"}
            proof = {"Schema": "iw7.model-writer-build/1", "SourcePin": "fab935826c898806855376662a8a03317b3ad8f1",
                     "Source": metadata, "Roundtrip": dict(metadata, geometry_roundtrip_verified=True,
                     vertices=24, triangles=12, bones=1, surfaces=1, lods=1), "Ready": False, "FFBuilt": False,
                     "Artifacts": artifacts}
            (writer / "writer-provenance.json").write_text(json.dumps(proof), encoding="utf-8")
            output = root / "prepared"
            report = prepare_beacon.prepare(writer, output)
            self.assertFalse(report["ff_built"])
            self.assertFalse(report["runtime_ready"])
            plan = manifest.load_manifest(output / "manifest.json")
            self.assertTrue(manifest.validate(plan)["valid"])
            self.assertEqual(plan["package"]["files"][1]["sha256"], hashlib.sha256((output / "sdk_beacon.gsc").read_bytes()).hexdigest())
            self.assertIsNone(plan["package"]["files"][0]["sha256"])
            self.assertIn("xmodel,paris_model_probe", (output / "zone_source/sdk_beacon.csv").read_text())
            with self.assertRaises(ValueError):
                prepare_beacon.prepare(writer, output)
            (writer / "artifacts/xmodel/paris_model_probe.xmb").write_bytes(b"bad")
            with self.assertRaises(ValueError):
                prepare_beacon.prepare(writer, root / "rejected")
            self.assertFalse((root / "rejected").exists())


if __name__ == "__main__":
    unittest.main()
