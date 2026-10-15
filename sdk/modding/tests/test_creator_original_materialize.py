"""Receipt orchestration with explicit synthetic text payloads, not real assets.

Only the delegated asset reader is replaced. These fixtures do not qualify its
binary parser, a native writer, an FF or gameplay.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SDK = ROOT / "sdk/modding"


def load(name):
    spec = importlib.util.spec_from_file_location("original_receipt_" + name, SDK / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


consumer, author, sdk = load("creator_original_materialize"), load("creator_authoring"), load("manifest")


class OriginalReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-authored-receipt-text-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project, self.source, self.build = (self.root / name for name in ("project", "source", "build"))
        shutil.copytree(SDK / "examples/original-authoring/turn-prism", self.project)
        self.manifest = sdk.load_manifest(self.project / "manifest.json")
        data = sdk.load_manifest(self.project / "authoring.json")
        # Keep the actual source material-input orchestration; replace only its
        # asset producer with an explicitly synthetic text-only implementation.
        for role, name in data["material_template"].items():
            self.write(self.project, name, ("SYNTHETIC TEMPLATE TEXT: " + role + "\n").encode())
        def material(**args):
            return dict(synthetic_source_test=True, texture_slot=args["texture_slot"],
                template_sha256={role: digest(raw) for role, raw in args["template"].items()},
                files={"images/" + args["image_name"] + ".dds": args["dds"]})
        self.producer = SimpleNamespace(rgba8_dds=lambda w, h, pixels:
            ("SYNTHETIC DDS TEXT: " + str((w, h)) + ":" + digest(pixels) + "\n").encode(), prepare_material=material)
        self.addCleanup(patch.stopall)
        patch.object(author, "_material_producer", return_value=self.producer).start()
        selected, context = author._select(self.project, ROOT, manifest=self.manifest)
        self.material = author._material_inputs(selected, context, ROOT)
        metadata = {key: value for key, value in self.material.items() if key != "files"}
        metadata["files"] = {name: digest(raw) for name, raw in self.material["files"].items()}
        geometry = sdk.load_manifest(self.project / "geometry.source.json")
        surface = geometry["surfaces"][0]
        self.artifacts = ["xmodel/" + data["model_name"] + ".xmb", "xsurface/" + data["mesh_name"] + ".xsb"]
        self.dump_names = [*self.artifacts, "materials/" + data["material_name"] + ".json", "images/" + data["image_name"] + ".iw7Image"]
        ncs = "ncs_mdl_" + data["zone"]
        self.plan = dict(schema="iw7.model-ff-plan/3", geometry_profile=consumer.PROFILE,
            namespace=data["namespace"], zone=data["zone"], model_name=data["model_name"], mesh_name=data["mesh_name"],
            material_reference=data["material_name"], image={"name": data["image_name"]}, ncs_name=ncs,
            source_files={"netconststrings/" + ncs + ".json": digest(b"SOURCE TEST NCS\n")},
            artifact_paths=self.artifacts, dump_files=self.dump_names,
            selected_counts={"vertices": len(surface["vertices"]), "triangles": len(surface["triangles"])},
            recipient_references={"techset": "source_test_technique", "images": ["source_test_normal"]},
            ff_built=False, pixels_verified=False, ready=False, physics_serialized=False)
        self.write(self.source, "model-ff-plan.json", encoded(self.plan))
        self.write(self.source, "evidence/writer/writer-source.json", encoded({"geometry_input_sha256": digest((self.project / "geometry.source.json").read_bytes()), "source_files": {"geometry.source.json": digest((self.project / "geometry.source.json").read_bytes())}}))
        self.write(self.source, "evidence/writer/geometry.source.json", (self.project / "geometry.source.json").read_bytes())
        self.write(self.source, "evidence/writer/writer-provenance.json", encoded({"synthetic_source_test": True}))
        self.write(self.source, "evidence/material-inputs.json", encoded(metadata))
        self.write(self.source, "netconststrings/" + ncs + ".json", b"SOURCE TEST NCS\n")
        ff = b"SYNTHETIC SOURCE RECEIPT TEST, NOT AN FF\n"
        self.write(self.build, "mod.ff", ff)
        for name in self.dump_names:
            self.write(self.build, "roundtrip/" + name, ("SYNTHETIC TEXT ONLY, NOT A SERIALIZED ASSET: " + name + "\n").encode())
        raw_geometry = dict(schema="iw7.model-roundtrip/1", geometry_profile=consumer.PROFILE,
            namespace=data["namespace"], zone=data["zone"], model_name=data["model_name"], mesh_name=data["mesh_name"],
            material_reference=data["material_name"], vertices=len(surface["vertices"]), triangles=len(surface["triangles"]),
            geometry_roundtrip_verified=True, ready=False, physics_serialized=False, iw7_normal_encoding_verified=False)
        self.write(self.build, "geometry.stdout.json", encoded(raw_geometry))
        self.geometry = dict(raw_geometry, ff={"bytes": len(ff), "sha256": digest(ff)},
                             source_plan_sha256=digest(encoded(self.plan)), dumped_artifacts=[])
        for name in self.artifacts:
            raw = (self.build / "roundtrip" / name).read_bytes()
            self.geometry["dumped_artifacts"].append(dict(path=name, bytes=len(raw), sha256=digest(raw)))
        self.surface = dict(schema="iw7.authored-material-roundtrip/1", geometry_profile=consumer.PROFILE,
            ff={"bytes": len(ff), "sha256": digest(ff)}, source_plan_sha256=digest(encoded(self.plan)),
            material_fields_verified=True, native_cbt_semantics_verified=False, recipient_resolution_verified=False,
            pixels_rendered_verified=False, physics_serialized=False, ready=False,
            image={"serialized_pixel_bytes_verified": True})
        self.write(self.build, "geometry-roundtrip.json", encoded(self.geometry))
        self.write(self.build, "surface-roundtrip.json", encoded(self.surface))
        self.write(self.build, "surface.stdout.json", encoded(self.surface))
        self.state = dict(Schema="iw7.model-ff-build/1", Status="BootstrapInventoryVerified", Restored=True,
            StockPreserved=True, InventoryVerified=True, GeometryRoundtripVerified=True, MaterialFieldsVerified=True,
            SerializedImageBytesVerified=True, RestorationStatus="Confirmed", RetainedLeaseToken=None,
            Failure=None, CleanupError=None, Ready=False, SourcePlan=self.plan,
            SourcePlanSHA256=digest(encoded(self.plan)), GeometryEvidenceSHA256=digest(encoded(self.geometry)),
            SurfaceEvidenceSHA256=digest(encoded(self.surface)), FF={"Path": "mod.ff", "Bytes": len(ff), "SHA256": digest(ff)},
            Build={"ExitCode": 0}, Offline={"ExitCode": 0}, Dump={"ExitCode": 0},
            GeometryReader={"ExitCode": 0, "Stdout": str(self.build / "geometry.stdout.json")},
            SurfaceReader={"ExitCode": 0, "Stdout": str(self.build / "surface.stdout.json")})
        self.save_state()
        self.verifier = SimpleNamespace(verify_authored_stage=lambda *a: self.plan,
                                       verify_authored_dump=lambda *a: copy.deepcopy(self.surface))
        original_loader = author.module
        def loader(path, name):
            return self.verifier if name == "creator_authored_readback" else original_loader(path, name)
        patch.object(consumer, "_author", return_value=author).start()
        patch.object(author, "module", side_effect=loader).start()
        patch.object(author, "_model_producer", return_value=None).start()

    def write(self, root, name, raw):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def save_state(self):
        self.write(self.build, "state.local.json", encoded(self.state))

    def bind(self):
        return consumer.bind(self.project, self.source, self.build, ROOT, manifest=self.manifest,
                             review_reference="SYNTHETIC SOURCE TEST; not an actual review")

    def test_local_bind_and_materialize_preserve_unqualified_package_gate(self):
        binding = self.bind()
        self.assertTrue(binding["bindings_written"])
        self.assertIn("surface_roundtrip_sha256", binding["composition"]["assets"])
        output = self.root / "candidate"
        result = consumer.materialize(self.project, self.build, output, ROOT, manifest=self.manifest,
                                      client_source=None, server_source=None)
        self.assertTrue(result["materialized"])
        self.assertFalse(result["runtime_ready"])
        self.assertFalse(result["package_ready"])
        check = json.loads((output / "validation-package.json").read_text())
        self.assertFalse(check["valid"])
        self.assertTrue(any("Dependency closure incomplete" in error for error in check["errors"]))
        plan = json.loads((output / "validation-plan.json").read_text())
        self.assertTrue(any("Capability not qualified: original-rigid-authoring/1" in item for item in plan["pending"]))
        self.assertEqual((output / "mod.ff").read_bytes(), (self.build / "mod.ff").read_bytes())

    def nested_readers(self):
        names = {}
        for reader, phase in (("GeometryReader", "model-geometry"), ("SurfaceReader", "model-authored-material")):
            before = Path(self.state[reader]["Stdout"])
            name = "owned-" + phase + "/stdout.log"
            self.write(self.build, name, before.read_bytes())
            identity = dict(PID=123, Image="C:\\SYNTHETIC_SOURCE_TEST\\reader.exe",
                            CreatedUtc="2026-10-15T00:00:00.0000000Z")
            self.state[reader].update(Stdout=str(self.build / name), Phase=phase, Identity=identity,
                RootExited=True, ActiveProcesses=0, JobClosed=True, Arguments=["SYNTHETIC SOURCE TEST"],
                ImageSHA256="f" * 64, OwnerEvidence=dict(Stage="Fixture", Phase=phase, Identity=identity,
                    TreeClosureConfirmed=True, ExitCode=0))
            names[reader] = name
        self.save_state()
        return names

    def test_nested_h1_readers_bind_and_materialize_without_relabeling_original_receipts(self):
        names = self.nested_readers()
        original_state = (self.build / "state.local.json").read_bytes()
        binding = self.bind()
        self.assertEqual(binding["composition"]["assets"]["build_receipt_sha256"], digest(original_state))
        output = self.root / "candidate"
        result = consumer.materialize(self.project, self.build, output, ROOT,
            manifest=self.manifest, client_source=None, server_source=None)
        evidence = json.loads((output / "finalization.json").read_text())
        self.assertEqual(evidence["reader_outputs"], {"geometry": names["GeometryReader"], "surface": names["SurfaceReader"]})
        self.assertEqual(original_state, (self.build / "state.local.json").read_bytes())
        self.assertFalse(result["package_ready"])
        self.assertFalse(result["runtime_ready"])

    def test_reader_escape_traversal_relative_ads_and_device_paths_refuse(self):
        names = self.nested_readers()
        original = copy.deepcopy(self.state)
        outside = self.root / "build-sibling/stdout.log"
        self.write(outside.parent, outside.name, b"SYNTHETIC SOURCE TEXT\n")
        for reader in names:
            values = [str(outside), names[reader], str(self.build) + "/../build/" + names[reader],
                      str(self.build) + "/./" + names[reader], str(self.build / names[reader]) + ":stream",
                      str(self.build) + "/NUL/stdout.log", str(self.build) + "/dir./stdout.log",
                      "\\\\?\\C:\\SYNTHETIC_SOURCE_TEST\\stdout.log", "\\\\.\\NUL", True]
            for value in values:
                with self.subTest(reader=reader, value=value):
                    self.state = copy.deepcopy(original)
                    self.state[reader]["Stdout"] = value
                    self.save_state()
                    with self.assertRaises((ValueError, OSError)):
                        self.bind()
                    self.assertFalse((self.project / "composition.json").exists())

    def test_redirected_nested_reader_is_refused_before_resolving_its_target(self):
        self.nested_readers()
        target = self.build / "owned-model-geometry"
        alias = self.build / "redirected-reader"
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit an actual directory symlink")
        self.state["GeometryReader"]["Stdout"] = str(alias / "stdout.log")
        self.save_state()
        with self.assertRaisesRegex(ValueError, "Redirected"):
            self.bind()
        self.assertFalse((self.project / "composition.json").exists())

    def test_nested_reader_mutation_after_first_snapshot_refuses_bind_and_materialize(self):
        names = self.nested_readers()
        for action in ("Bind", "Materialize"):
            for reader, name in names.items():
                with self.subTest(action=action, reader=reader):
                    composition = self.project / "composition.json"
                    if composition.exists():
                        composition.unlink()
                    raw = (self.build / name).read_bytes()
                    self.verifier.verify_authored_dump = lambda *a: copy.deepcopy(self.surface)
                    if action == "Materialize":
                        self.bind()
                    def changed(*args):
                        (self.build / name).write_bytes(raw + b"\n")
                        return copy.deepcopy(self.surface)
                    self.verifier.verify_authored_dump = changed
                    with self.assertRaisesRegex(ValueError, "Input changed"):
                        if action == "Bind":
                            self.bind()
                        else:
                            consumer.materialize(self.project, self.build, self.root / "candidate", ROOT,
                                manifest=self.manifest, client_source=None, server_source=None)
                    (self.build / name).write_bytes(raw)
                    self.assertFalse((self.root / "candidate").exists())

    def test_pending_failed_boolean_exit_or_wrong_surface_hash_refuses_before_binding(self):
        original = copy.deepcopy(self.state)
        mutations = [dict(Restored=False), dict(RetainedLeaseToken="unclosed"), dict(Failure="failed"),
                     dict(SurfaceEvidenceSHA256="0" * 64), dict(GeometryReader={"ExitCode": False})]
        for change in mutations:
            self.state = dict(copy.deepcopy(original), **change)
            self.save_state()
            with self.subTest(change=change), self.assertRaises((ValueError, KeyError)):
                self.bind()
            self.assertFalse((self.project / "composition.json").exists())

    def test_actual_ff_dump_and_independent_reader_change_refuses(self):
        ff = self.build / "mod.ff"
        ff.write_bytes(ff.read_bytes() + b"changed")
        with self.assertRaises(ValueError):
            self.bind()
        ff.write_bytes(b"SYNTHETIC SOURCE RECEIPT TEST, NOT AN FF\n")
        path = self.build / "roundtrip" / self.artifacts[0]
        original = path.read_bytes()
        path.write_bytes(original + b"changed")
        with self.assertRaises(ValueError):
            self.bind()
        path.write_bytes(original)
        self.verifier.verify_authored_dump = lambda *a: dict(self.surface, material_fields_verified=False)
        with self.assertRaisesRegex(ValueError, "image/material readback differs"):
            self.bind()

    def test_changed_gsc_after_bind_is_not_reapproved_by_materialize(self):
        self.bind()
        script = self.project / "sdk_turn_prism.gsc"
        script.write_bytes(script.read_bytes() + b"// different author behavior\n")
        with self.assertRaises(ValueError):
            consumer.materialize(self.project, self.build, self.root / "candidate", ROOT,
                                 manifest=self.manifest, client_source=None, server_source=None)
        self.assertFalse((self.root / "candidate").exists())

    def test_current_pixels_slot_and_template_must_match_the_staged_material(self):
        descriptor = self.project / "authoring.json"
        original_descriptor = descriptor.read_bytes()
        pixels = self.project / "color.rgba8.json"
        original_pixels = pixels.read_bytes()
        value = json.loads(original_pixels)
        value["pixels"][0] ^= 1
        pixels.write_bytes(encoded(value))
        with self.assertRaisesRegex(ValueError, "current author pixels/template/slot"):
            self.bind()
        pixels.write_bytes(original_pixels)
        value = json.loads(original_descriptor)
        value["texture"]["slot"] = 0
        descriptor.write_bytes(encoded(value))
        with self.assertRaisesRegex(ValueError, "current author pixels/template/slot"):
            self.bind()
        descriptor.write_bytes(original_descriptor)
        (self.project / "templates/material.json").write_bytes(b"SYNTHETIC CHANGED TEMPLATE\n")
        with self.assertRaisesRegex(ValueError, "current author pixels/template/slot"):
            self.bind()
        self.assertFalse((self.project / "composition.json").exists())

    def pending_writer_receipts(self):
        root = self.source / "evidence/writer"
        self.write(root, "writer-provenance.json", encoded({"NativeReleasePending": True}))
        self.write(root, "writer-closure.json", encoded({"synthetic_text_closure": True}))
        self.write(root, "writer-native-run.json", encoded({"synthetic_text_native_run": True}))
        return root

    def test_new_writer_receipts_are_enrolled_for_bind_and_materialize(self):
        self.pending_writer_receipts()
        self.bind()
        result = consumer.materialize(self.project, self.build, self.root / "candidate", ROOT,
            manifest=self.manifest, client_source=None, server_source=None)
        evidence = json.loads((self.root / "candidate/finalization.json").read_text())
        for name in ("writer-closure.json", "writer-native-run.json"):
            self.assertIn("writer/evidence/writer/" + name, evidence["inputs"])
        self.assertFalse(result["package_ready"])
        self.assertFalse(result["runtime_ready"])

    def test_new_receipt_mutations_during_both_readers_refuse_bind_and_materialize(self):
        for action in ("Bind", "Materialize"):
            for phase in ("verify_authored_stage", "verify_authored_dump"):
                for name in ("writer-closure.json", "writer-native-run.json"):
                    with self.subTest(action=action, phase=phase, name=name):
                        root = self.pending_writer_receipts()
                        composition = self.project / "composition.json"
                        if composition.exists():
                            composition.unlink()
                        self.verifier.verify_authored_stage = lambda *a: self.plan
                        self.verifier.verify_authored_dump = lambda *a: copy.deepcopy(self.surface)
                        if action == "Materialize":
                            self.bind()
                        def changed(*args):
                            (root / name).write_bytes(encoded({"synthetic_changed": True}))
                            return self.plan if phase == "verify_authored_stage" else copy.deepcopy(self.surface)
                        setattr(self.verifier, phase, changed)
                        with self.assertRaisesRegex(ValueError, "Input changed"):
                            if action == "Bind":
                                self.bind()
                            else:
                                consumer.materialize(self.project, self.build, self.root / "candidate", ROOT,
                                    manifest=self.manifest, client_source=None, server_source=None)
                        self.assertFalse((self.root / "candidate").exists())
                        if action == "Bind":
                            self.assertFalse(composition.exists())

    def test_existing_dispatch_consumes_authored_receipts(self):
        dispatch = load("creator_model_materialize")
        # Both public entrypoints must reach this same authored consumer, rather
        # than the old resident format reader or a new builder.
        original = dispatch.module
        with patch.object(dispatch, "module", side_effect=lambda path, name:
                          consumer if name == "creator_original_materialize" else original(path, name)):
            dispatch.bind(self.project, self.source, self.build, ROOT, manifest=self.manifest,
                          review_reference="SYNTHETIC SOURCE REVIEW DECLARATION")
            result = dispatch.materialize(self.project, self.build, self.root / "candidate", ROOT,
                manifest=self.manifest, client_source=None, server_source=None)
        self.assertTrue(result["materialized"])
        self.assertFalse(result["package_ready"])

    @unittest.skipUnless((ROOT / "ops/model-lab/prepare_ff.py").is_file(), "Prepared exact producer sources required")
    def test_real_stage_reader_import_and_incomplete_text_receipt_refusal(self):
        # Fresh Python host; no mocks or opaque asset files. This verifies the
        # actual delegated reader's source dependencies, not successful FF IO.
        script = '''import importlib.util, sys
from pathlib import Path
root, invalid = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("fresh_authored_reader", root / "sdk/modding/creator_authoring.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
author._model_producer(root)
before = sys.path[:]
try:
    sys.path.insert(0, str(root / "ops/model-lab"))
    reader = author.module(root / "ops/model-lab/prepare_ff.py", "creator_authored_readback")
    try:
        reader.verify_authored_stage(invalid)
    except KeyError as error:
        assert error.args == ("files",), repr(error)
    else:
        raise AssertionError("real stage reader accepted incomplete source receipts")
finally:
    sys.path[:] = before
print("real existing stage reader rejected incomplete text receipt")
'''
        invalid = self.root / "invalid-source"
        self.write(invalid, "model-ff-plan.json", b"{}\n")
        self.write(invalid, "evidence/material-inputs.json", b"{}\n")
        run = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT), str(invalid)],
                             capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("real existing stage reader rejected", run.stdout)

    @unittest.skipUnless((ROOT / "ops/model-lab/prepare_ff.py").is_file(), "Prepared final producer sources required")
    def test_actual_new_closure_gate_accepts_bound_text_and_rejects_pending_or_missing_receipts(self):
        # Synthetic declared JSON fields, never real process identities/results.
        # The final producer alone interprets their contract in a fresh host.
        script = r'''import hashlib, json, sys
from pathlib import Path
tools, root = map(Path, sys.argv[1:])
sys.path.insert(0, str(tools / "ops/model-lab"))
from prepare_ff import validate_native_closure, PIN
root.mkdir()
encode = lambda value: (json.dumps(value, sort_keys=True) + "\n").encode()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
key = "IW7.ModelWriter.Root." + "1" * 32
provenance = dict(NativeReleasePending=True, NativeRootKey=key, NativeClosureEvidence="writer-closure.json",
    SourcePin=PIN, Source={"synthetic_source_test": True}, WriterSHA256="a"*64, CompilerSHA256="b"*64)
provenance_raw = encode(provenance)
native = dict(Schema="iw7.model-writer-native-run/1", Status="NativeRoundtripPassed", NativeRootKey=key,
    SourcePin=PIN, Source=provenance["Source"], WriterSHA256="a"*64, CompilerSHA256="b"*64,
    ReleasePending=True, LeaseReleased=False, TreeClosureConfirmed=True, Quarantined=False, Ready=False, Stages=[])
for index, (name, kind, image) in enumerate((("discovery","Fixture","vswhere.exe"), ("compile","Compile","cl.exe"), ("fixture","Fixture","model-writer.exe")), 1):
    native["Stages"].append(dict(Name=name, Stage=kind, ExitCode=0, TreeClosureConfirmed=True,
        ImageSHA256="b"*64 if name=="compile" else "a"*64,
        Identity=dict(PID=index, Image="C:\\SYNTHETIC_SOURCE_TEST\\"+image, CreatedUtc="2026-10-15T00:00:00.0000000Z")))
native_raw = encode(native)
closure = dict(Schema="iw7.model-writer-closure/1", NativeRootKey=key, WriterProvenanceSHA256=sha(provenance_raw),
    NativeRunSHA256=sha(native_raw), JobClosureVerified=True, LeaseReleased=True, InputGuardsClosed=True,
    PreReleasePublicationsVerified=True, Ready=False)
closure_raw = encode(closure)
(root/"writer-native-run.json").write_bytes(native_raw)
(root/"writer-closure.json").write_bytes(closure_raw)
assert validate_native_closure(root, provenance, provenance_raw) == (closure_raw, native_raw)
for name in ("writer-closure.json", "writer-native-run.json"):
    path = root/name
    raw = path.read_bytes()
    path.unlink()
    try:
        validate_native_closure(root, provenance, provenance_raw)
    except OSError:
        pass
    else:
        raise AssertionError("missing first receipt accepted")
    path.write_bytes(raw)
closure["LeaseReleased"] = False
(root/"writer-closure.json").write_bytes(encode(closure))
try:
    validate_native_closure(root, provenance, provenance_raw)
except ValueError:
    pass
else:
    raise AssertionError("unclosed receipt accepted")
assert validate_native_closure(root, {}, b"{}\n") == (None, None)
print("actual final closure gate checked synthetic text; no native operation")
'''
        run = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT), str(self.root / "closure-text")],
                             capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("actual final closure gate checked", run.stdout)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 required for real Creator refusal paths")
    def test_real_cli_offline_inspection_does_not_waive_other_or_package_errors(self):
        pin = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"
        self.bind()
        # This source contract is deliberately invalid. The real authored
        # dispatch must refuse it before reaching any opaque material reader.
        self.write(self.source, "model-ff-plan.json", encoded(dict(self.plan, schema="iw7.model-ff-plan/2")))
        def invoke(action, *, client=pin, extra=(), adapter="ModelLabV2"):
            args = [shutil.which("pwsh"), "-NoProfile", "-File", str(SDK / "Creator.ps1"),
                "-Project", str(self.project), "-ToolsRoot", str(ROOT), "-Adapter", adapter,
                "-Action", action, "-ClientSource", client, "-ServerSource", pin, "-Protocol", "2", "-Json"]
            if action == "Bind":
                args += ["-ModelSourceRoot", str(self.source), "-BuildRoot", str(self.build),
                         "-ReviewReference", "SYNTHETIC SOURCE REVIEW DECLARATION"]
            elif action == "Materialize":
                args += ["-BuildRoot", str(self.build), "-FinalizeRoot", str(self.root / "candidate")]
            elif action == "Package":
                args += ["-Output", str(self.root / "blocked.zip")]
            before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            run = subprocess.run([*args, *extra], capture_output=True, text=True, timeout=20)
            self.assertEqual(run.stderr, "", run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(run.returncode, 1, report)
            self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
            for key in ("plan_valid", "build_executed", "materialized", "packaged", "runtime_ready", "owner_accepted"):
                self.assertFalse(report[key], (key, report))
            return report
        # Remove only the binding just authored, so Bind can reach source checks.
        saved_binding = (self.project / "composition.json").read_bytes()
        (self.project / "composition.json").unlink()
        report = invoke("Bind")
        self.assertTrue(report["offline_author_inspection"])
        self.assertIn("Authored FF plan must use", " ".join(report["errors"]))
        (self.project / "composition.json").write_bytes(saved_binding)
        report = invoke("Materialize")
        self.assertTrue(report["offline_author_inspection"])
        self.assertIn("Authored FF plan must use", " ".join(report["errors"]))
        report = invoke("Materialize", client="f" * 40)
        self.assertIn("Capability source proof missing: engine/", " ".join(report["errors"]))
        original = (self.project / "manifest.json").read_bytes()
        value = json.loads(original)
        value["requires"]["client"].append("original-arena-display/1")
        (self.project / "manifest.json").write_bytes(encoded(value))
        report = invoke("Materialize")
        self.assertIn("client/original-arena-display/1", " ".join(report["errors"]))
        (self.project / "manifest.json").write_bytes(original)
        active = self.root / "active"
        shutil.copytree(SDK / "examples/original-authoring/step-lantern", active)
        report = invoke("Materialize", extra=("-ActiveProject", str(active)))
        self.assertIn("client/original-rigid-authoring/1 in sdk_step_lantern", " ".join(report["errors"]))
        report = invoke("Package", adapter="None")
        self.assertNotIn("offline_author_inspection", report)
        self.assertIn("client/original-rigid-authoring/1", " ".join(report["errors"]))
        report = invoke("Build")
        self.assertNotIn("offline_author_inspection", report)
        self.assertIn("supports only", " ".join(report["errors"]))

    def test_existing_composition_and_overlapping_output_are_preserved(self):
        self.bind()
        before = (self.project / "composition.json").read_bytes()
        with self.assertRaises(ValueError):
            self.bind()
        self.assertEqual((self.project / "composition.json").read_bytes(), before)
        with self.assertRaises(ValueError):
            consumer.materialize(self.project, self.build, self.project / "candidate", ROOT,
                                 manifest=self.manifest, client_source=None, server_source=None)

    def short_path(self, path):
        import ctypes
        function = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
        function.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        function.restype = ctypes.c_uint32
        buffer = ctypes.create_unicode_buffer(32768)
        self.assertTrue(function(str(path), buffer, len(buffer)))
        return Path(buffer.value)

    @unittest.skipUnless(sys.platform == "win32", "Windows 8.3 path identity")
    def test_short_path_receipts_work_and_output_alias_cannot_overlap_inputs(self):
        project_alias, build_alias = self.short_path(self.project), self.short_path(self.build)
        if project_alias == self.project:
            self.skipTest("Host has no distinct 8.3 alias")
        self.state["GeometryReader"]["Stdout"] = str(build_alias / "geometry.stdout.json")
        self.state["SurfaceReader"]["Stdout"] = str(build_alias / "surface.stdout.json")
        self.save_state()
        self.bind()
        with self.assertRaisesRegex(ValueError, "nonoverlapping"):
            consumer.materialize(self.project, self.build, project_alias / "candidate", ROOT,
                                 manifest=self.manifest, client_source=None, server_source=None)
        self.assertFalse((self.project / "candidate").exists())

    @unittest.skipUnless(sys.platform == "win32", "Windows 8.3 reader alias identity")
    def test_nested_reader_8dot3_component_alias_is_refused(self):
        names = self.nested_readers()
        reader = self.build / names["GeometryReader"]
        alias = self.short_path(reader.parent)
        if alias.name == reader.parent.name:
            self.skipTest("Host has no distinct reader-directory 8.3 alias")
        # Use the normal build root so the test specifically proves the child
        # component refusal, separate from valid equivalent TEMP root aliases.
        self.state["GeometryReader"]["Stdout"] = str(self.build / alias.name / reader.name)
        self.save_state()
        with self.assertRaisesRegex(ValueError, "alias refused"):
            self.bind()
        self.assertFalse((self.project / "composition.json").exists())


if __name__ == "__main__":
    unittest.main()
