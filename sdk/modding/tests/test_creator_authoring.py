"""Editable source contracts only. No producer, DDS, model, FF or game run."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SDK = ROOT / "sdk/modding"
EXAMPLES = SDK / "examples/original-authoring"


def load(name):
    spec = importlib.util.spec_from_file_location("author_input_" + name, SDK / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


authoring, sdk = load("creator_authoring"), load("manifest")


class AuthorInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-author-text-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "author"
        shutil.copytree(EXAMPLES / "turn-prism", self.project)
        self.manifest = sdk.load_manifest(self.project / "manifest.json")

    def save(self, name, value):
        (self.project / name).write_text(json.dumps(value), encoding="utf-8")

    def descriptor(self):
        return sdk.load_manifest(self.project / "authoring.json")

    def select(self):
        return authoring.select(self.project, ROOT, manifest=self.manifest)

    def test_both_original_projects_bind_text_only_and_remain_unqualified(self):
        reports = []
        for path in (EXAMPLES / "turn-prism", EXAMPLES / "step-lantern"):
            manifest = sdk.load_manifest(path / "manifest.json")
            before = {p.relative_to(path): p.read_bytes() for p in path.rglob("*") if p.is_file()}
            report = authoring.select(path, ROOT, manifest=manifest)
            self.assertEqual(before, {p.relative_to(path): p.read_bytes() for p in path.rglob("*") if p.is_file()})
            self.assertTrue(sdk.validate(manifest, stage="plan")["valid"])
            self.assertFalse(sdk.validate(manifest, stage="package")["valid"])
            self.assertTrue(report["source_contract_valid"])
            self.assertEqual(report["descriptor"]["texture"]["slot"], 1)
            for key in ("geometry_verified", "opaque_inputs_read", "build_executed", "package_ready", "runtime_ready", "owner_accepted"):
                self.assertIs(report[key], False)
            self.assertTrue({"manifest", "authoring", "geometry", "script", "rgba8"} <= set(report["inputs"]))
            self.assertTrue(set(report["inputs"]) <= {"manifest", "authoring", "geometry", "script", "rgba8", "producer/geometry"})
            reports.append(report)
        self.assertNotEqual(reports[0]["descriptor"]["namespace"], reports[1]["descriptor"]["namespace"])
        self.assertNotEqual(reports[0]["inputs"]["geometry"]["sha256"], reports[1]["inputs"]["geometry"]["sha256"])
        self.assertNotEqual(reports[0]["inputs"]["script"]["sha256"], reports[1]["inputs"]["script"]["sha256"])
        self.assertNotEqual(reports[0]["inputs"]["rgba8"]["sha256"], reports[1]["inputs"]["rgba8"]["sha256"])

    def test_author_can_edit_geometry_pixels_and_script_without_changing_tools(self):
        geometry = sdk.load_manifest(self.project / "geometry.source.json")
        for vertex in geometry["surfaces"][0]["vertices"]:
            vertex["position"] = [value * 1.25 for value in vertex["position"]]
        for key in ("midpoint", "half_size"):
            geometry["bounds"][key] = [value * 1.25 for value in geometry["bounds"][key]]
        self.save("geometry.source.json", geometry)
        pixels = sdk.load_manifest(self.project / "color.rgba8.json")
        pixels["pixels"][0] = 91
        self.save("color.rgba8.json", pixels)
        script = self.project / "sdk_turn_prism.gsc"
        script.write_text(script.read_text().replace("Prism direction:", "Authored orientation:"))
        report = self.select()
        self.assertTrue(report["source_contract_valid"])
        self.assertFalse(report["geometry_verified"], "Editable input is not a geometry proof")

    def test_third_namespace_uses_same_selector_without_a_whitelist_change(self):
        old, new = "sdk_turn_prism", "my_original_fixture"
        for path in self.project.iterdir():
            if path.is_file():
                path.write_text(path.read_text().replace(old, new), encoding="utf-8")
        (self.project / (old + ".gsc")).rename(self.project / (new + ".gsc"))
        self.manifest = sdk.load_manifest(self.project / "manifest.json")
        report = self.select()
        self.assertEqual(report["descriptor"]["namespace"], new)
        self.assertTrue(report["source_contract_valid"])

    def test_extra_commands_and_identity_collisions_are_refused(self):
        for change in ({"command": "anything"}, {"zone": "other_project"},
                       {"model_name": "outside_namespace"}, {"mesh_name": "sdk_turn_prism_model"}):
            value = self.descriptor()
            value.update(change)
            self.save("authoring.json", value)
            with self.assertRaises(ValueError):
                self.select()
            shutil.copyfile(EXAMPLES / "turn-prism/authoring.json", self.project / "authoring.json")

    def test_script_and_graph_must_match_the_author_project(self):
        value = self.descriptor()
        value["script_source"] = "../foreign.gsc"
        self.save("authoring.json", value)
        with self.assertRaises(ValueError):
            self.select()
        shutil.copyfile(EXAMPLES / "turn-prism/authoring.json", self.project / "authoring.json")
        self.manifest["package"]["closure"]["nodes"][1]["requires"] = []
        self.save("manifest.json", self.manifest)
        with self.assertRaises(ValueError):
            self.select()

    def test_fractional_boolean_truncated_and_out_of_range_pixels_refuse(self):
        original = sdk.load_manifest(self.project / "color.rgba8.json")
        cases = [dict(original, width=True), dict(original, height=4.0),
                 dict(original, pixels=original["pixels"][:-1]),
                 dict(original, pixels=[256, *original["pixels"][1:]]),
                 dict(original, pixels=[False, *original["pixels"][1:]])]
        for value in cases:
            self.save("color.rgba8.json", value)
            with self.subTest(value=value.keys()), self.assertRaises(ValueError):
                self.select()

    def test_plan_does_not_open_dds_or_material_template_paths(self):
        value = self.descriptor()
        value["texture"] = {"kind": "dds-dx10", "source": "not-present.dds", "slot": 2}
        self.save("authoring.json", value)
        report = self.select()
        self.assertFalse(report["opaque_inputs_read"])
        self.assertNotIn("rgba8", report["inputs"])
        self.assertFalse(report["texture"]["dds_verified"])
        self.assertTrue(report["pending"])

    def test_template_unknown_roles_and_unsafe_paths_refuse(self):
        for roles in ({"material": "../foreign.json", "statebits": "a", "statebitsmap": "b"},
                      {"material": "a", "statebits": "b", "statebitsmap": "c", "script": "d"}):
            value = self.descriptor()
            value["material_template"] = roles
            self.save("authoring.json", value)
            with self.assertRaises(ValueError):
                self.select()

    def test_manifest_change_after_selection_is_not_blessed(self):
        changed = copy.deepcopy(self.manifest)
        changed["package"]["version"] = "0.2.0"
        self.save("manifest.json", changed)
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            self.select()

    def test_source_placement_is_data_and_not_a_physics_claim(self):
        value = self.descriptor()
        value["placement"]["offset_forward_right_up"] = [0, 0, 96]
        self.save("authoring.json", value)
        report = self.select()
        self.assertEqual(report["source_scene"]["placement"]["offset_forward_right_up"], [0, 0, 96])
        self.assertFalse(report["source_scene"]["transform_verified"])
        self.assertFalse(report["source_scene"]["physics_serialized"])
        value["placement"]["scale"] = True
        self.save("authoring.json", value)
        with self.assertRaises(ValueError):
            self.select()

    def test_writer_consumer_rejects_changed_geometry_without_claiming_preparation(self):
        native = Path(self.temp.name) / "native-source"
        native.mkdir()
        result = {"model_name": "sdk_turn_prism_model", "geometry_input_sha256": "0" * 64,
                  "compiled": False, "ff_built": False, "ready": False}
        producer = SimpleNamespace(prepare_authored=lambda *args, **kwargs: result)
        with patch.object(authoring, "_model_producer", return_value=producer), self.assertRaisesRegex(ValueError, "different author geometry"):
            authoring.prepare_writer_inputs(self.project, Path(self.temp.name) / "prepared", ROOT, native,
                                            manifest=self.manifest)

    def writer_receipts(self):
        writer = Path(self.temp.name) / "writer"
        writer.mkdir(exist_ok=True)
        data = self.descriptor()
        recipe = {key: data[key] for key in ("namespace", "zone", "model_name", "mesh_name")}
        recipe.update(material_reference=data["material_name"],
            geometry_input_sha256=hashlib.sha256((self.project / "geometry.source.json").read_bytes()).hexdigest(),
            source_files={"writer.cpp": "0" * 64}, artifact_paths=["xmodel/source_test.xmb", "xsurface/source_test.xsb"])
        for name, value in {"writer-source.json": recipe, "writer-provenance.json": {"NativeReleasePending": True},
                            "writer-native-run.json": {"synthetic_text_native_run": True},
                            "writer-closure.json": {"synthetic_text_closure": True}}.items():
            (writer / name).write_text(json.dumps(value), encoding="utf-8")
        for name in ("writer.cpp", *["artifacts/" + name for name in recipe["artifact_paths"]]):
            path = writer / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC SOURCE TEST TEXT; not a model or native result\n", encoding="utf-8")
        return writer

    def stage_with(self, writer, callback):
        loader = authoring.module
        producer = SimpleNamespace(stage_authored=callback)
        with patch.object(authoring, "_material_inputs", return_value={"synthetic_source_test": True}), \
             patch.object(authoring, "_model_producer", return_value=None), \
             patch.object(authoring, "module", side_effect=lambda path, name:
                          producer if name == "creator_original_ff_stage" else loader(path, name)):
            return authoring.stage_ff_inputs(self.project, writer, Path(self.temp.name) / "stage", ROOT,
                                             manifest=self.manifest)

    def test_stage_enrolls_first_writer_sources_artifacts_and_two_phase_receipts(self):
        writer = self.writer_receipts()
        called = []
        def stage(*args, **kwargs):
            called.append(True)
            return dict(ff_built=False, pixels_verified=False, ready=False)
        result = self.stage_with(writer, stage)
        self.assertEqual(called, [True])
        for name in ("writer/recipe", "writer/writer-provenance.json", "writer/writer-closure.json",
                     "writer/writer-native-run.json", "writer/writer.cpp", "writer/artifacts/xmodel/source_test.xmb"):
            self.assertIn(name, result["inputs"])
        self.assertFalse(result["ff_built"])
        self.assertFalse(result["runtime_ready"])

    def test_stage_refuses_missing_or_reader_mutated_new_receipts(self):
        for name in ("writer-closure.json", "writer-native-run.json"):
            with self.subTest(name=name):
                writer = self.writer_receipts()
                path = writer / name
                path.unlink()
                called = []
                def no_read(*args, **kwargs):
                    called.append(True)
                    raise AssertionError("Missing first receipt reached stage validation")
                with self.assertRaises(OSError):
                    self.stage_with(writer, no_read)
                self.assertEqual(called, [])
                writer = self.writer_receipts()
                def changed(*args, **kwargs):
                    path.write_text('{"synthetic_changed":true}', encoding="utf-8")
                    return dict(ff_built=False, pixels_verified=False, ready=False)
                with self.assertRaisesRegex(ValueError, "Input changed"):
                    self.stage_with(writer, changed)
                self.assertFalse((Path(self.temp.name) / "stage").exists())

    def test_material_dispatch_uses_validated_first_pixel_snapshot_and_no_writes(self):
        templates = self.project / "templates"
        templates.mkdir()
        for name in self.descriptor()["material_template"].values():
            (self.project / name).write_bytes(b"SYNTHETIC SOURCE DISPATCH TEST; not an IW7 template\n")
        observed = []
        def rgba(width, height, pixels):
            observed.append((width, height, pixels))
            return b"SYNTHETIC SOURCE DISPATCH TEST; not a DDS"
        producer = SimpleNamespace(rgba8_dds=rgba, prepare_material=lambda **kwargs: kwargs)
        original_loader = authoring.module
        def loader(path, name):
            return producer if name == "creator_original_material" else original_loader(path, name)
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        with patch.object(authoring, "module", side_effect=loader):
            result = authoring.material_inputs(self.project, ROOT, manifest=self.manifest)
        self.assertEqual(observed[0][:2], (4, 4))
        self.assertEqual(observed[0][2], bytes(json.loads(before[Path("color.rgba8.json")])["pixels"]))
        self.assertEqual(result["material_name"], "sdk_turn_prism_material")
        self.assertEqual(set(result["template"]), {"material", "statebits", "statebitsmap", "stateinfo", "cbi", "cbt"})
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()})

    @unittest.skipUnless((ROOT / "tools-source/asset-bridge/surfaces/authored_dds_material.py").is_file(),
                         "Prepared exact producer sources required")
    def test_real_material_producer_import_in_fresh_host_restores_search_path(self):
        # No producer mock, retail template, DDS/FF file or native process. The
        # invalid owned bytes must reach the real API and receive its refusal.
        script = Path(self.temp.name) / "fresh_import.py"
        script.write_text('''import importlib.util
from pathlib import Path
import sys
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("fresh_sdk_author", root / "sdk/modding/creator_authoring.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
before = sys.path[:]
producer = author._material_producer(root)
assert sys.path == before, "producer import leaked sys.path"
try:
    producer.prepare_material(zone="source_case", image_name="source_case_color",
        material_name="source_case_material", texture_slot=1,
        dds=b"INVALID OWNED SOURCE TEST BYTES; NOT A DDS", template={})
except ValueError:
    pass
else:
    raise AssertionError("real material producer accepted invalid source bytes")
print("actual pinned material API imported and refused invalid input")
''', encoding="utf-8")
        run = subprocess.run([__import__("sys").executable, "-B", str(script), str(ROOT)],
                             cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("actual pinned material API imported", run.stdout)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 required for actual Plan dispatch")
    def test_real_creator_plan_binds_inputs_but_refuses_unproved_capability(self):
        pin = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"
        run = subprocess.run([shutil.which("pwsh"), "-NoProfile", "-File", str(SDK / "Creator.ps1"),
            "-Project", str(self.project), "-ToolsRoot", str(ROOT), "-Adapter", "ModelLabV2", "-Action", "Plan",
            "-ClientSource", pin, "-ServerSource", pin, "-Protocol", "2", "-Json"],
            capture_output=True, text=True, timeout=20)
        report = json.loads(run.stdout)
        self.assertEqual(run.returncode, 1)
        self.assertTrue(report["source_selection"]["source_contract_valid"])
        self.assertFalse(report["source_selection"]["opaque_inputs_read"])
        self.assertTrue(any("Capability source proof missing" in error for error in report["errors"]))
        for field in ("plan_valid", "build_executed", "build_verified", "materialized", "packaged", "runtime_ready"):
            self.assertFalse(report[field])


if __name__ == "__main__":
    unittest.main()
