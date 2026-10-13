"""Original authored synthetic source only; no native, game or retail inputs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SDK = Path(__file__).resolve().parents[1]
ROOT = SDK.parents[1]
WORLD = ROOT / "tools-source/asset-bridge/world/original-arena"
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


m = load(SDK / "creator_model_materialize.py", "arena_creator_tested")
sdk = load(SDK / "manifest.py", "arena_sdk_tested")


def fixture(root):
    # Reuse the asset owner's original fault-injection fixtures. Restore global
    # aliases/path after their conventional test-only imports; production uses
    # the independent World reader's uniquely named modules.
    saved_path = sys.path[:]
    try:
        with patch.dict(sys.modules):
            sys.path.insert(0, str(ROOT / "ops/model-lab"))
            geometry = load(ROOT / "ops/model-lab/geometry.py", "arena_geometry_fixture")
            bridge = load(WORLD.parent / "trigger_bridge.py", "arena_trigger_fixture")
            sys.modules.update(geometry=geometry, trigger_bridge=bridge)
            arena = load(WORLD / "arena.py", "arena_source_fixture")
            reader = load(WORLD / "readback.py", "arena_reader_fixture")
            sys.modules.update(arena=arena, readback=reader)
            prepare = load(WORLD / "prepare.py", "arena_prepare_fixture")
            model_lab = load(WORLD / "model_lab.py", "arena_model_lab_fixture")
            sys.modules.update(prepare=prepare, model_lab=model_lab,
                               prepare_writer=load(ROOT / "ops/model-lab/prepare_writer.py", "arena_writer_fixture"))
            tests = load(WORLD / "test_arena.py", "arena_shared_test_fixture")
            prepared, artifacts = tests.ModelLabTests().prepare_fixture(root)
            source = root / "source"
            plan = model_lab.stage(artifacts, prepared, source)
            return source, artifacts, plan, model_lab
    finally:
        sys.path[:] = saved_path


class ArenaCreatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project, self.build, self.output = [self.root / p for p in ("project", "build", "candidate")]
        self.project.mkdir(); self.build.mkdir()
        self.source, self.artifacts, self.plan, self.reader = fixture(self.root)
        self.manifest = sdk.load_manifest(SDK / "examples/original-arena/manifest.json")
        (self.project / "manifest.json").write_bytes(encoded(self.manifest))

    def bind_build_fixture(self):
        # This is intentionally text, not a fastfile. No compiler or tool runs.
        (self.build / "mod.ff").write_bytes(b"SYNTHETIC TEST TEXT; NOT AN IW7 FASTFILE\n")
        for name in self.reader.PAIR:
            path = self.build / "roundtrip" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((self.source / name).read_bytes())
        proof = self.reader.verify_dump(self.source, self.build / "roundtrip", self.build / "mod.ff")
        raw = encoded(proof)
        (self.build / "geometry-roundtrip.json").write_bytes(raw)
        (self.build / "reader.stdout.json").write_bytes(raw)
        rows = ["material,," + m.MATERIAL, "xmodel:paris_original_arena".replace(":", ",", 1),
                "xmodelsurfs,paris_original_arena_lod0", "netconststrings,ncs_mdl_paris_model_probe", "rawfile,paris_model_probe"]
        (self.build / "assets.csv").write_text("\n".join(rows) + "\n")
        log = 'Loading zone "paris_model_probe"\n'
        for row in rows:
            kind, name = row.split(",", 1)
            log += f'Loading asset "{name}" of type {kind}.\n'
        (self.build / "inventory.stdout.log").write_text(log)
        self.state = dict(Schema="iw7.model-ff-build/1", Status="BootstrapInventoryVerified", Restored=True,
            StockPreserved=True, InventoryVerified=True, GeometryRoundtripVerified=True, RestorationStatus="Confirmed",
            RetainedLeaseToken=None, CleanupError=None, Failure=None, Ready=False, SourcePlan=self.plan,
            SourcePlanSHA256=proof["source_plan_sha256"], GeometryEvidenceSHA256=sha(raw),
            Build={"ExitCode": 0}, Dump={"ExitCode": 0},
            Offline={"ExitCode": 0, "Stdout": str(self.build / "inventory.stdout.log")},
            GeometryReader={"ExitCode": 0, "Stdout": str(self.build / "reader.stdout.json")},
            FF={"Path": "mod.ff", "Bytes": proof["ff"]["bytes"], "SHA256": proof["ff"]["sha256"]})
        (self.build / "state.local.json").write_bytes(encoded(self.state))
        (self.project / "sdk_original_arena.gsc").write_bytes(b"// SYNTHETIC SOURCE; NEVER COMPILED OR RUN\ninit(){}\n")
        return m.bind(self.project, self.source, self.build, ROOT, manifest=self.manifest,
                      review_reference="Synthetic declaration only", adapter="OriginalArenaV1")

    def invoke(self):
        return m.materialize(self.project, self.build, self.output, ROOT, manifest=self.manifest,
                             client_source=PIN, server_source=PIN, adapter="OriginalArenaV1")

    def test_plan_keeps_explicit_blocked_capability_and_required_ncs(self):
        report = sdk.validate(self.manifest, stage="plan", client_source=PIN, server_source=PIN)
        self.assertTrue(report["valid"], report["errors"])
        self.assertIn("Capability not qualified: original-arena-display/1", report["pending"])
        self.assertFalse(report["ready"])
        self.assertTrue(all(e["status"] == "pending" for e in self.manifest["package"]["evidence"]))
        for mixed in (False, True):
            data = copy.deepcopy(self.manifest)
            data["requires"]["engine"].remove("model-netconststrings/1")
            if mixed: data["requires"]["client"].append("skeletal-animation-import/1")
            errors = sdk.validate(data, stage="plan")["errors"]
            self.assertIn("Missing capability: engine/model-netconststrings/1", errors)
        data = copy.deepcopy(self.manifest)
        data["requires"]["client"].remove("original-arena-display/1")
        self.assertIn("Missing capability: client/xmodel-rigid/1", sdk.validate(data, stage="plan")["errors"])

    def test_source_selection_reads_only_exact_eight_source_inputs(self):
        before = {p: sha(p.read_bytes()) for p in self.source.rglob("*") if p.is_file()}
        result = m.select_arena(self.source, ROOT, manifest=self.manifest)
        self.assertEqual(result["origin"], "authored-arena")
        self.assertEqual(result["selected_counts"], m.ARENA_COUNTS)
        self.assertEqual(len(result["inputs"]), 8)
        self.assertEqual(before, {p: sha(p.read_bytes()) for p in before})
        for flag in ("build_executed", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertFalse(result[flag])

    def mutated_reader(self, name, method):
        original_module = m.module
        def changed(path, label):
            module = original_module(path, label)
            if label == "creator_original_arena_verifier":
                verify = getattr(module, method)
                def corrupt(*args):
                    result = verify(*args)
                    path = self.source / name
                    path.write_bytes(path.read_bytes() + b"changed after verification")
                    return result
                setattr(module, method, corrupt)
            return module
        return changed

    def test_every_reader_time_source_mutation_refused(self):
        for name in self.plan["validation_files"]:
            path = self.source / name; original = path.read_bytes()
            try:
                with self.subTest(name=name), patch.object(m, "module", self.mutated_reader(name, "verify_stage")):
                    with self.assertRaisesRegex(ValueError, "Input changed"):
                        m.select_arena(self.source, ROOT, manifest=self.manifest)
            finally: path.write_bytes(original)

    def test_wrong_profile_names_counts_and_cube_capability_refused(self):
        path = self.source / "model-ff-plan.json"
        for key, value in (("geometry_profile", m.PROFILE), ("model_name", "paris_model_probe"),
                           ("selected_counts", dict(m.ARENA_COUNTS, vertices=True)), ("physics_serialized", True)):
            data = copy.deepcopy(self.plan); data[key] = value; path.write_bytes(encoded(data))
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.select_arena(self.source, ROOT, manifest=self.manifest)
        path.write_bytes(self.reader.json_bytes(self.plan))
        self.manifest["requires"]["client"].append("xmodel-rigid/1")
        with self.assertRaisesRegex(ValueError, "historical cube"):
            m.select_arena(self.source, ROOT, manifest=self.manifest)

    def test_bind_and_materialize_reuse_existing_schema_without_qualification(self):
        bound = self.bind_build_fixture()
        descriptor = bound["composition"]
        self.assertEqual(descriptor["schema"], "iw7.creator-model-composition/1")
        self.assertEqual(descriptor["assets"]["derived_receipt_sha256"], sha((self.source / m.ARENA_WRITER).read_bytes()))
        result = self.invoke()
        self.assertTrue(result["materialized"])
        for flag in ("closure_complete", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertFalse(result[flag])
        evidence = json.loads((self.output / "finalization.json").read_bytes())
        self.assertEqual(evidence["origin"], "authored-arena")
        self.assertEqual(evidence["adapter"], "OriginalArenaV1")
        self.assertEqual(evidence["selected_counts"], m.ARENA_COUNTS)
        self.assertNotIn("surface_records", evidence)
        self.assertFalse(evidence["physics_serialized"])
        self.assertFalse(json.loads((self.output / "validation-package.json").read_bytes())["ready"])

    def test_materialize_keeps_first_ncs_and_all_source_snapshots(self):
        self.bind_build_fixture()
        for name in self.plan["validation_files"]:
            path = self.source / name; original = path.read_bytes()
            try:
                with self.subTest(name=name), patch.object(m, "module", self.mutated_reader(name, "verify_dump")):
                    with self.assertRaisesRegex(ValueError, "Input changed"):
                        self.invoke()
                self.assertFalse(self.output.exists())
            finally: path.write_bytes(original)

    def test_unrestored_build_or_wrong_reader_result_refused(self):
        self.bind_build_fixture()
        self.state["Restored"] = False
        raw = encoded(self.state); (self.build / "state.local.json").write_bytes(raw)
        path = self.project / "composition.json"; descriptor = json.loads(path.read_bytes())
        descriptor["assets"]["build_receipt_sha256"] = sha(raw); path.write_bytes(encoded(descriptor))
        with self.assertRaisesRegex(ValueError, "Restored successful"):
            self.invoke()
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell required")
    def test_real_creator_plan_reports_selection_and_honest_compatibility_refusal(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        base = [shutil.which("pwsh"), "-NoProfile", "-File", str(SDK / "Creator.ps1"),
                "-Project", str(self.project), "-Adapter", "OriginalArenaV1", "-ClientSource", PIN,
                "-ServerSource", PIN, "-Protocol", "2", "-ToolsRoot", str(ROOT), "-Json"]
        result = subprocess.run(base + ["-Action", "Plan", "-ModelSourceRoot", str(self.source)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["source_selection"]["selected_counts"], m.ARENA_COUNTS)
        self.assertIn("Capability source proof missing: client/original-arena-display/1", " ".join(report["errors"]))
        self.assertFalse(report["plan_valid"])
        for flag in ("bindings_written", "build_executed", "materialized", "packaged", "runtime_ready", "owner_accepted"):
            self.assertFalse(report[flag])
        result = subprocess.run(base + ["-Action", "Build"], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no Build adapter", " ".join(json.loads(result.stdout)["errors"]))
        self.assertEqual(before, {p: p.read_bytes() for p in before})


if __name__ == "__main__":
    unittest.main()
