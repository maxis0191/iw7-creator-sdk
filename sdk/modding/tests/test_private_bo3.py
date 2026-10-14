"""Bounded source contracts and explicit synthetic recipe inputs; never real FFs."""
from contextlib import ExitStack, redirect_stdout
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

SDK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("private_bo3_tested", SDK / "prepare_private_bo3.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PrivateBo3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-private-bo3-source-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.references = self.root / "references"
        self.references.mkdir()
        self.output = self.root / "project"
        self.test_sdk = self.root / "test-sdk"
        self.test_sdk.mkdir()
        self.production_manifest = m.f.sdk.load_manifest(SDK / "examples/private-bo3-prop/manifest.json")
        self.manifest = copy.deepcopy(self.production_manifest)
        self.paths = {label: self.inputs / name for label, name in (
            ("fastfile", "synthetic.ff"), ("server-script", "synthetic.gsc"), ("readback", "synthetic-readback.json"))}
        self.paths["fastfile"].write_bytes(b"SYNTHETIC TRANSPORT FIXTURE ONLY - NOT AN IW7 FASTFILE\n")
        self.paths["server-script"].write_bytes(b"// SYNTHETIC SOURCE ONLY - not compiled or run\ninit() { return; }\n")
        self.bindings = {label: self.binding(path.read_bytes()) for label, path in self.paths.items() if label != "readback"}
        self.reader = {
            "schema": "iw7.model-rigid-roundtrip/2", "geometry_profile": "t7-iw7-selected-streamed-render-only-v2",
            "model_name": "p7_fre_platform_cap_02", "mesh_name": "p7_fre_platform_cap_02_lod0ca80354f",
            "selected_counts": {"bones": 1, "roots": 1, "surfaces": 5, "vertices": 560, "triangles": 490},
            "lod0_dist": 1000000.0, "ff": self.bindings["fastfile"],
            "source_plan_sha256": "750d25d7d34c8c5849aa2048f1052fc1c5fd3c51cafd61e43268f4c003951686",
            "derived_receipt_sha256": "231e9fd55d19d1dd85a391d4e2b73cae2c21e39324ed6d69630f8df0240c0471",
            "inputs": [
                {"relative_path": "roundtrip/xmodel/p7_fre_platform_cap_02.xmb", "bytes": 1089,
                 "sha256": "af4cb78463b466fe9cb92f1d24b1dfb706664d255d3aa1d939af0e1e6a68b583"},
                {"relative_path": "roundtrip/xsurface/p7_fre_platform_cap_02_lod0ca80354f.xsb", "bytes": 22456,
                 "sha256": "5c93d1769b4fcf500729fbba49474e97dff471962797741a4bceae50a755fd4d"},
            ],
            "geometry_roundtrip_verified": True, "packed_attributes_byte_identical": True,
            "native_provenance_verified": False, "source_geometry_correspondence_verified": False,
            "dependency_payloads_verified": False, "runtime_verified": False, "pixels_verified": False, "ready": False,
            "material_references": ["mopw/character_park_clown_zombie_shoes"] * 5,
            "surface_records": [
                {"index": 0, "material_slot": 0, "vertices": 208, "triangles": 200},
                {"index": 1, "material_slot": 1, "vertices": 8, "triangles": 4},
                {"index": 2, "material_slot": 2, "vertices": 34, "triangles": 32},
                {"index": 3, "material_slot": 3, "vertices": 94, "triangles": 62},
                {"index": 4, "material_slot": 4, "vertices": 216, "triangles": 192},
            ], "geometry_work_bytes_upper_bound": 41656,
        }
        self.write_reader()
        self.reference_bindings = copy.deepcopy(m.REFERENCE_INPUTS)
        for index, expected in enumerate(self.reference_bindings.values()):
            raw = ("SYNTHETIC PRODUCER REFERENCE ONLY " + str(index) + "\n").encode()
            path = self.references / expected["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            expected.update(self.binding(raw))
        for entry, label in zip(self.manifest["package"]["files"], ("fastfile", "server-script")):
            entry.update(self.bindings[label])
        for node in self.manifest["package"]["closure"]["nodes"]:
            if node["id"].startswith("scriptfile:"):
                node["sha256"] = self.bindings["server-script"]["sha256"]
            elif node["id"] in self.reference_bindings:
                node["sha256"] = self.reference_bindings[node["id"]]["sha256"]
        template = self.test_sdk / "examples/private-bo3-prop/manifest.json"
        template.parent.mkdir(parents=True)
        template.write_bytes(m.f.encoded(self.manifest))
        for name in ("manifest.schema.json", "capabilities.json"):
            (self.test_sdk / name).write_bytes((SDK / name).read_bytes())

    @staticmethod
    def binding(raw):
        return {"bytes": len(raw), "sha256": m.f.sha(raw)}

    def write_reader(self):
        raw = m.f.encoded(self.reader)
        self.paths["readback"].write_bytes(raw)
        self.bindings["readback"] = self.binding(raw)

    def synthetic_context(self):
        # Only test-local expected tuples/templates are replaced. Production has
        # no CLI, manifest or environment option that can relax these bindings.
        stack = ExitStack()
        stack.enter_context(patch.object(m, "EXPECTED_INPUTS", self.bindings))
        stack.enter_context(patch.object(m, "REFERENCE_INPUTS", self.reference_bindings))
        stack.enter_context(patch.object(m, "TEMPLATE_ROOT", self.test_sdk))
        stack.enter_context(patch.object(m.f.sdk, "HERE", self.test_sdk))
        return stack

    def prepare(self):
        return m.prepare(self.paths["fastfile"], self.paths["server-script"], self.paths["readback"],
                         self.references, self.output)

    def test_production_template_plan_is_valid_and_never_runtime_ready(self):
        self.assertEqual(self.production_manifest["dependencies"], [])
        self.assertEqual(self.production_manifest["conflicts"], [])
        result = m.f.sdk.validate(self.production_manifest, stage="plan", target="native",
                                 client_source=m.UPSTREAM, server_source=m.UPSTREAM)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["ready"])
        self.assertFalse(result["runtime_ready"])
        self.assertFalse(result["owner_accepted"])
        self.assertEqual(self.production_manifest["package"]["files"][0]["bytes"], 9904)
        self.assertEqual(self.production_manifest["package"]["files"][0]["sha256"],
                         "50ca9124d35f4ea5e9f017adafcf012df01b9991d1fcde2597c8f0f58aabcd0c")

    def test_production_plan_guard_refuses_changed_bindings_graph_and_native_contract(self):
        mutations = []
        for index in (0, 1):
            for key, value in (("bytes", 1), ("sha256", "0" * 64)):
                mutations.append(("file-" + str(index) + "-" + key,
                                  lambda data, index=index, key=key, value=value: data["package"]["files"][index].update({key: value})))
        for index in (1, 2):
            for key, value in (("scope", "recipient"), ("kind", "material")):
                mutations.append(("node-" + str(index) + "-" + key,
                                  lambda data, index=index, key=key, value=value: data["package"]["closure"]["nodes"][index].update({key: value})))
        for kind in ("anim", "xmodel"):
            mutations.append(("extra-" + kind, lambda data, kind=kind: data["package"]["closure"]["nodes"].append(
                {"id": kind + ":extra", "kind": kind, "scope": "client", "sha256": "0" * 64, "requires": []})))
        mutations.append(("protocol-1", lambda data: data["compatibility"].update(network_protocol=1)))
        for side in ("client", "server"):
            mutations.append(("missing-native-" + side,
                              lambda data, side=side: data["package"]["native_requirements"].update({side + "_source": None})))
        for capability in ("original-arena-display/1", "skeletal-animation-import/1", "xmodel-rigid/1"):
            mutations.append(("mixed-" + capability, lambda data, capability=capability: data["requires"]["client"].append(capability)))
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                data = copy.deepcopy(self.production_manifest)
                mutate(data)
                result = m.f.sdk.validate(data, stage="plan", target="native",
                                         client_source=m.UPSTREAM, server_source=m.UPSTREAM)
                self.assertFalse(result["valid"], result)
                self.assertFalse(result["ready"])
                self.assertFalse(result["runtime_ready"])

    def test_synthetic_prepare_measures_only_delivered_bytes_and_source_references(self):
        failed = self.inputs / "original-failed.local.json"
        failed_raw = b'{"Status":"Failed","Ready":false}\n'
        failed.write_bytes(failed_raw)
        with self.synthetic_context():
            result = self.prepare()
        self.assertEqual(failed.read_bytes(), failed_raw)
        self.assertTrue(result["prepared"])
        self.assertTrue(result["package_ready"])
        for flag in ("runtime_ready", "owner_accepted", "installed", "copy_and_play_ready", "ready_to_deploy"):
            self.assertFalse(result[flag])
        self.assertEqual({path.name for path in self.output.iterdir()},
                         {"manifest.json", "mod.ff", m.GSC, "project-evidence.json", "validation-package.json"})
        self.assertEqual((self.output / "mod.ff").read_bytes(), self.paths["fastfile"].read_bytes())
        self.assertEqual((self.output / m.GSC).read_bytes(), self.paths["server-script"].read_bytes())
        evidence = json.loads((self.output / "project-evidence.json").read_text())
        nodes = evidence["node_representations"]
        for node_id in ("xmodel:" + m.MODEL, "xsurface:" + m.MESH):
            self.assertEqual(nodes[node_id]["representation"], "pinned-reader-declaration")
            self.assertFalse(nodes[node_id]["bytes_measured_by_recipe"])
        for node_id in self.reference_bindings:
            self.assertTrue(nodes[node_id]["reference_bytes_measured_by_recipe"])
            self.assertFalse(nodes[node_id]["serialized_payload_measured_by_recipe"])
        self.assertEqual(nodes["material:" + m.MATERIAL]["representation"], "recipient-csv-reference-only")
        self.assertEqual(nodes["rawfile:paris_model_probe"]["representation"], "zone-csv-inventory-only")
        self.assertFalse(evidence["physical_dependency_payloads_verified"])
        self.assertFalse(evidence["reader_executed_by_recipe"])
        native = evidence["native_prerequisite"]
        self.assertEqual(native["build_manifest_legacy_protocol"], 1)
        self.assertEqual(native["separately_reported_runtime_protocol"], 2)
        self.assertFalse(native["installed_binary_measured_by_recipe"])
        validation = json.loads((self.output / "validation-package.json").read_text())
        self.assertTrue(validation["ready"])
        self.assertFalse(validation["runtime_ready"])
        self.assertFalse(validation["owner_accepted"])
        self.assertEqual(set(validation["checked"]), {"client_fastfile", "server_display"})

    def test_standalone_synthetic_archive_stages_with_real_inspector_and_delivery_pending(self):
        installer = m.f.module(SDK.parents[1] / "ops/modding/Install-CommunityMod.Package.py", "private_bo3_install_test")
        stage = self.root / "installer-stage"
        with self.synthetic_context(), patch.object(installer.sdk, "HERE", self.test_sdk):
            prepared = self.prepare()
            self.assertTrue(prepared["package_ready"])
            manifest = installer.pack.read_manifest(self.output / "manifest.json")
            self.assertEqual(manifest["dependencies"], [])
            self.assertEqual(manifest["conflicts"], [])
            # Preparation already used the actual SDK package gate. The same
            # existing writer streams those measured synthetic files; no ZIP
            # implementation or validation result is substituted by this test.
            archive = installer.pack.write_archive(manifest, self.output, self.root / "synthetic-staging.zip")
            result = installer.inspect(SimpleNamespace(
                archive=archive["archive"], sha256=archive["archive_sha256"],
                client_source=m.UPSTREAM, server_source=m.UPSTREAM, protocol=2,
                target="native", max_bytes=64 * 1024 * 1024, stage_root=str(stage)))
        self.assertFalse(result["PackageGatePending"])
        self.assertEqual({path.name for path in stage.iterdir()}, {"mod.ff", m.GSC})
        for name, label in (("mod.ff", "fastfile"), (m.GSC, "server-script")):
            raw = (stage / name).read_bytes()
            self.assertEqual(raw, self.paths[label].read_bytes())
            self.assertEqual(self.binding(raw), self.bindings[label])
        self.assertEqual({row["Entry"] for row in result["Rows"]}, {
            "server/mods/paris_bo3_static_probe/mod.ff", "fastdl/mods/paris_bo3_static_probe/mod.ff",
            "server/iw7-mod/custom_scripts/cp/" + m.GSC})
        for row in result["Rows"]:
            label = "fastfile" if row["Relative"].endswith(".ff") else "server-script"
            self.assertEqual(row["Bytes"], self.bindings[label]["bytes"])
            self.assertEqual(row["SHA256"], self.bindings[label]["sha256"])
        delivery = result["DeliveryGate"]
        self.assertFalse(delivery["valid"])
        self.assertFalse(delivery["ready"])
        for kind in ("source-check", "offline-load", "runtime-link"):
            self.assertIn("package: Delivery requires passed " + kind + " evidence for every declared map", delivery["errors"])
        for report in (result, delivery):
            self.assertFalse(report["runtime_ready"])
            self.assertFalse(report["owner_accepted"])
        self.assertFalse(result["public_deployment"])

    def player_fixture(self):
        installer = m.f.module(SDK.parents[1] / "ops/modding/Install-CommunityMod.Package.py", "private_bo3_player_test")
        owner = self.root / "owned-stage-root"
        owner.mkdir()
        with self.synthetic_context(), patch.object(installer.sdk, "HERE", self.test_sdk):
            self.prepare()
            manifest = installer.pack.read_manifest(self.output / "manifest.json")
            result = installer.pack.write_archive(manifest, self.output, self.root / "synthetic-player.zip",
                                                  layout="player", player_language="fr")
        archive = Path(result["archive"])
        with zipfile.ZipFile(archive) as opened:
            entries = {name: opened.read(name) for name in opened.namelist()}
        validation = json.loads((SDK / "examples/private-bo3-prop/physical-validation.json").read_text())
        # Patch only this test-local source witness, never production policy or
        # a runtime option. All payloads were produced by the real sole writer.
        validation["physical"]["player_archive"] = dict(bytes=archive.stat().st_size,
            sha256=self.binding(archive.read_bytes())["sha256"],
            members={name: self.binding(raw) for name, raw in entries.items()})
        validation["physical"]["ff"] = self.bindings["fastfile"]
        witness = self.test_sdk / "examples/private-bo3-prop/physical-validation.json"
        witness.write_bytes(m.f.encoded(validation))
        args = SimpleNamespace(archive=str(archive), sha256=result["archive_sha256"], client_source=m.UPSTREAM,
            server_source=m.UPSTREAM, protocol=2, target="native", max_bytes=64 * 1024 * 1024,
            stage_root=None, stage_owner_root=None, layout="player")
        return installer, owner, entries, validation, witness, args

    def test_player_causal_operator_refusal_and_closed_source_inspection(self):
        installer, owner, entries, validation, witness, args = self.player_fixture()
        with patch.object(installer.sdk, "HERE", self.test_sdk):
            args.layout = "staging"
            with self.assertRaises(KeyError):
                installer.inspect(args)  # Old operator contract requires manifest.json.
            args.layout = "player"
            result = installer.inspect(args)
        self.assertTrue(result["PlayerPayloadVerified"])
        self.assertFalse(result["PlayerStageVerified"])
        self.assertEqual(result["Schema"], "iw7.private-bo3-player-stage/1")
        self.assertEqual(result["Rows"], [{"Area": "client", "Relative": "mods/paris_bo3_static_probe/mod.ff",
            "Entry": "mods/paris_bo3_static_probe/mod.ff", "Bytes": self.bindings["fastfile"]["bytes"],
            "SHA256": self.bindings["fastfile"]["sha256"]}])
        self.assertEqual(result["SnapshotMode"], "single-bounded-bytesio")
        self.assertTrue(result["PackageGatePending"])
        self.assertIsNone(result["DeliveryGate"])
        for flag in ("installed", "runtime_ready", "owner_accepted", "public_deployment", "NativePrerequisiteMeasured"):
            self.assertFalse(result[flag])
        self.assertEqual(list(owner.iterdir()), [])

    def test_player_stages_only_client_mod_under_fresh_owned_root(self):
        installer, owner, entries, validation, witness, args = self.player_fixture()
        args.stage_root, args.stage_owner_root = str(owner / "stage"), str(owner)
        with patch.object(installer.sdk, "HERE", self.test_sdk):
            result = installer.inspect(args)
            self.assertTrue(result["PlayerStageVerified"])
            with self.assertRaisesRegex(ValueError, "Fresh player staging root"):
                installer.inspect(args)
        staged = Path(args.stage_root)
        files = {p.relative_to(staged).as_posix() for p in staged.rglob("*") if p.is_file()}
        self.assertEqual(files, {"mods/paris_bo3_static_probe/mod.ff"})
        self.assertEqual((staged / "mods/paris_bo3_static_probe/mod.ff").read_bytes(), self.paths["fastfile"].read_bytes())
        self.assertEqual(result["StageIdentity"]["bytes"], self.bindings["fastfile"]["bytes"])
        self.assertEqual(result["StageModRoot"], str(staged / "mods/paris_bo3_static_probe"))
        self.assertEqual(result["StageModIdentity"]["inode"], str((staged / "mods/paris_bo3_static_probe").stat().st_ino))
        self.assertEqual(result["StageModIdentity"]["kind"], "python-os-stat/1")
        self.assertEqual(result["SourceReferences"]["physical_validation"], self.binding(witness.read_bytes()))
        self.assertTrue(result["PackageGatePending"])

    def test_player_refuses_wrong_pins_types_scope_and_source_contract(self):
        installer, owner, entries, validation, witness, original = self.player_fixture()
        cases = [("protocol", 1), ("protocol", True), ("protocol", "2"), ("target", "stock"),
                 ("client_source", "0" * 40), ("server_source", "0" * 40), ("sha256", "0" * 64),
                 ("max_bytes", True), ("max_bytes", 1), ("max_bytes", 64 * 1024 * 1024 + 1),
                 ("layout", "unknown")]
        with patch.object(installer.sdk, "HERE", self.test_sdk):
            for key, value in cases:
                with self.subTest(field=key, value=value):
                    args = copy.copy(original)
                    setattr(args, key, value)
                    with self.assertRaises(ValueError):
                        installer.inspect(args)
            for root, stage_owner in ((self.root / "outside", owner), (owner, owner),
                                      (Path("relative"), owner), (owner / "fresh", None)):
                with self.subTest(stage=str(root)):
                    args = copy.copy(original)
                    args.stage_root, args.stage_owner_root = str(root), str(stage_owner) if stage_owner else None
                    with self.assertRaises(ValueError):
                        installer.inspect(args)
            altered = copy.deepcopy(validation)
            altered["physical"]["ff"]["sha256"] = "0" * 64
            witness.write_bytes(m.f.encoded(altered))
            with self.assertRaisesRegex(ValueError, "Exact private player"):
                installer.inspect(original)
        self.assertEqual(list(owner.iterdir()), [])

    def test_player_rejects_unsafe_or_changed_zip_before_any_stage(self):
        installer, owner, entries, original_validation, witness, original = self.player_fixture()
        ff_name = "mods/paris_bo3_static_probe/mod.ff"
        for case in ("extra", "missing", "traversal", "duplicate", "directory", "symlink", "compressed",
                     "changed-play", "changed-ff", "member-size", "expanded-bomb", "wrong-global"):
            with self.subTest(case=case):
                archive = self.root / (case + ".zip")
                with zipfile.ZipFile(archive, "w") as opened:
                    for name, payload in entries.items():
                        if case == "missing" and name == "PLAY.txt":
                            continue
                        info = installer.pack.zip_info(name)
                        if case == "symlink" and name == ff_name:
                            info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        if case == "compressed":
                            info.compress_type = zipfile.ZIP_DEFLATED
                        if (case == "changed-play" and name == "PLAY.txt") or (case == "changed-ff" and name == ff_name):
                            payload = b"X" + payload[1:]
                        if case == "member-size" and name == ff_name:
                            payload += b"X"
                        opened.writestr(info, payload)
                    if case in ("extra", "traversal", "duplicate", "directory"):
                        extra = {"extra": "extra.txt", "traversal": "../escape.ff", "duplicate": "play.TXT",
                                 "directory": "extra/"}[case]
                        opened.writestr(installer.pack.zip_info(extra), b"X")
                raw = archive.read_bytes()
                if case == "expanded-bomb":
                    raw = bytearray(raw)
                    offset = raw.index(b"PK\x01\x02")
                    struct.pack_into("<I", raw, offset + 24, 64 * 1024 * 1024 + 1)
                    archive.write_bytes(raw)
                validation = copy.deepcopy(original_validation)
                binding = self.binding(archive.read_bytes())
                validation["physical"]["player_archive"].update(binding)
                witness.write_bytes(m.f.encoded(validation))
                args = copy.copy(original)
                args.archive, args.sha256 = str(archive), binding["sha256"]
                args.stage_root, args.stage_owner_root = str(owner / "stage"), str(owner)
                if case == "wrong-global":
                    archive.write_bytes(b"X" + archive.read_bytes()[1:])
                with patch.object(installer.sdk, "HERE", self.test_sdk), self.assertRaises(ValueError):
                    installer.inspect(args)
                self.assertFalse(Path(args.stage_root).exists())
                self.assertFalse((self.root / "escape.ff").exists())

    def test_player_refuses_filesystem_redirected_stage_owner(self):
        installer, owner, entries, validation, witness, args = self.player_fixture()
        redirected = self.root / "redirected-owner"
        try:
            redirected.symlink_to(owner, target_is_directory=True)
        except OSError:
            self.skipTest("Token cannot create directory symlinks")
        args.stage_root, args.stage_owner_root = str(redirected / "stage"), str(redirected)
        with patch.object(installer.sdk, "HERE", self.test_sdk), self.assertRaisesRegex(ValueError, "Redirected"):
            installer.inspect(args)
        self.assertFalse((owner / "stage").exists())

    def test_player_hash_and_members_use_one_snapshot_even_if_path_changes_later(self):
        installer, owner, entries, validation, witness, args = self.player_fixture()
        args.stage_root, args.stage_owner_root = str(owner / "stage"), str(owner)
        checked = installer.checked_entries

        def after_snapshot(archive, maximum):
            self.assertIsInstance(archive.fp, io.BytesIO)
            Path(args.archive).write_bytes(b"SYNTHETIC CONCURRENT REPLACEMENT AFTER SNAPSHOT")
            return checked(archive, maximum)

        with patch.object(installer.sdk, "HERE", self.test_sdk), patch.object(installer, "checked_entries", after_snapshot):
            result = installer.inspect(args)
        self.assertTrue(result["PlayerStageVerified"])
        self.assertEqual(result["ArchiveSHA256"], validation["physical"]["player_archive"]["sha256"])
        self.assertEqual((Path(args.stage_root) / "mods/paris_bo3_static_probe/mod.ff").read_bytes(), self.paths["fastfile"].read_bytes())

    def test_player_reparse_metadata_is_refused_before_archive_bytes(self):
        installer, owner, entries, validation, witness, args = self.player_fixture()
        original_lstat = Path.lstat
        original_open = Path.open

        def reparse_lstat(path, *values, **keywords):
            meta = original_lstat(path, *values, **keywords)
            if str(path) == args.archive:
                return SimpleNamespace(st_mode=meta.st_mode, st_file_attributes=0x400)
            return meta

        def refuse_archive_read(path, *values, **keywords):
            if str(path) == args.archive:
                raise AssertionError("Redirected archive must not be opened")
            return original_open(path, *values, **keywords)

        with patch.object(installer.sdk, "HERE", self.test_sdk), patch.object(Path, "lstat", reparse_lstat), \
                patch.object(Path, "open", refuse_archive_read), self.assertRaisesRegex(ValueError, "Redirected"):
            installer.inspect(args)

    def test_player_portable_identity_preserves_128_bit_values_through_json(self):
        installer = m.f.module(SDK.parents[1] / "ops/modding/Install-CommunityMod.Package.py", "private_bo3_identity_test")
        value = (1 << 127) + 42
        result = installer.file_identity(SimpleNamespace(st_dev=value, st_ino=value + 1, st_size=9904, st_mtime_ns=12345))
        decoded = json.loads(json.dumps(result))
        self.assertEqual(decoded["kind"], "python-os-stat/1")
        self.assertEqual(decoded["device"], str(value))
        self.assertEqual(decoded["inode"], str(value + 1))
        self.assertEqual(decoded["bytes"], 9904)

    def test_each_pinned_input_tamper_refuses_before_output(self):
        paths = [*self.paths.values(), *(self.references / value["path"] for value in self.reference_bindings.values())]
        for path in paths:
            with self.subTest(input=path.name):
                original = path.read_bytes()
                path.write_bytes(b"X" * len(original))
                try:
                    with self.synthetic_context(), self.assertRaisesRegex(ValueError, "size/hash mismatch"):
                        self.prepare()
                    self.assertFalse(self.output.exists())
                finally:
                    path.write_bytes(original)

    def test_rehashed_reader_cannot_promote_or_change_identity_counts_or_ff(self):
        original = copy.deepcopy(self.reader)
        for field, value in (("schema", "other"), ("geometry_profile", "other"), ("model_name", "other"),
                             ("mesh_name", "other"), ("selected_counts", dict(original["selected_counts"], vertices=561)),
                             ("ff", dict(original["ff"], sha256="0" * 64)),
                             ("geometry_roundtrip_verified", False), ("packed_attributes_byte_identical", False),
                             ("native_provenance_verified", True), ("runtime_verified", True),
                             ("pixels_verified", True), ("ready", True)):
            with self.subTest(field=field):
                self.reader = dict(original, **{field: value})
                self.write_reader()  # Explicitly rebind only this synthetic receipt.
                with self.synthetic_context(), self.assertRaisesRegex(ValueError, "Exact unpromoted"):
                    self.prepare()
                self.assertFalse(self.output.exists())

    def test_existing_missing_parent_and_nested_output_are_refused(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_bytes(b"preserve existing user content")
        with self.synthetic_context(), self.assertRaisesRegex(ValueError, "Fresh"):
            self.prepare()
        self.assertEqual(marker.read_bytes(), b"preserve existing user content")
        for target in (self.root / "missing-parent/project", self.inputs / "nested", self.references / "nested"):
            with self.subTest(output=target):
                self.output = target
                with self.synthetic_context(), self.assertRaises((OSError, ValueError)):
                    self.prepare()
                self.assertFalse(target.exists())

    def test_redirected_input_is_refused_without_following_it(self):
        target = self.paths["fastfile"]
        link = self.inputs / "redirect.ff"
        try:
            os.symlink(target, link)
        except OSError as error:
            self.skipTest("This token cannot create a source-test symlink: " + str(error))
        self.paths["fastfile"] = link
        with self.synthetic_context(), self.assertRaisesRegex(ValueError, "Redirected"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_reparse_attribute_refuses_before_any_input_read(self):
        original_lstat = Path.lstat

        def reparse_lstat(path, *args, **kwargs):
            if path == self.paths["fastfile"]:
                return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
            return original_lstat(path, *args, **kwargs)

        with self.synthetic_context(), patch.object(Path, "lstat", reparse_lstat), \
                patch.object(m.f.Inputs, "read", side_effect=AssertionError("Redirect must refuse before bytes are read")):
            with self.assertRaisesRegex(ValueError, "Redirected"):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_actual_sdk_rejects_each_corrupted_delivered_output_and_cleans_owned_files(self):
        original_write = m.f.OutputFiles.write
        for filename in ("mod.ff", m.GSC):
            with self.subTest(output=filename):
                def corrupt_writer(writer, name, raw):
                    original_write(writer, name, b"X" * len(raw) if name == filename else raw)

                with self.synthetic_context(), patch.object(m.f.OutputFiles, "write", corrupt_writer):
                    with self.assertRaisesRegex(ValueError, "package gate refused:.*Payload size/hash mismatch"):
                        self.prepare()
                self.assertFalse(self.output.exists())

    def test_source_drift_after_plan_is_rechecked_before_output_creation(self):
        original_validate = m.f.sdk.validate

        def change_after_plan(*args, **kwargs):
            result = original_validate(*args, **kwargs)
            if kwargs.get("stage") == "plan":
                path = self.paths["fastfile"]
                path.write_bytes(b"X" * path.stat().st_size)
            return result

        with self.synthetic_context(), patch.object(m.f.sdk, "validate", change_after_plan):
            with self.assertRaisesRegex(ValueError, "Input .*changed"):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_shared_nonrecursive_cleanup_preserves_concurrent_content(self):
        original_write = m.f.OutputFiles.write

        def fail_writer(writer, name, raw):
            if name == "project-evidence.json":
                (writer.root / "concurrent.txt").write_bytes(b"not created by recipe")
                raise ValueError("synthetic write interruption")
            original_write(writer, name, raw)

        with self.synthetic_context(), patch.object(m.f.OutputFiles, "write", fail_writer):
            with self.assertRaisesRegex(ValueError, "write interruption"):
                self.prepare()
        self.assertEqual([path.name for path in self.output.iterdir()], ["concurrent.txt"])
        self.assertEqual((self.output / "concurrent.txt").read_bytes(), b"not created by recipe")

    def test_cli_prepares_explicit_synthetic_inputs_without_acceptance(self):
        args = ["prepare_private_bo3.py", "--fastfile", str(self.paths["fastfile"]),
                "--server-script", str(self.paths["server-script"]), "--readback", str(self.paths["readback"]),
                "--reference-root", str(self.references), "--output", str(self.output)]
        stdout = io.StringIO()
        with self.synthetic_context(), patch.object(m.sys, "argv", args), redirect_stdout(stdout):
            status = m.main()
        self.assertEqual(status, 0, stdout.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertTrue(result["package_ready"])
        self.assertFalse(result["runtime_ready"])
        self.assertFalse(result["installed"])


if __name__ == "__main__":
    unittest.main()
