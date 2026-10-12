"""Asset-free finalization tests. Synthetic FF/receipts are not native evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("beacon_finalize_test", HERE / "Finalize-BeaconProject.py")
finalizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalizer)
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="beacon-finalize-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project, self.build, self.output = (self.root / name for name in ("project", "build", "candidate"))
        self.project.mkdir()
        self.build.mkdir()
        template = HERE / "examples/beacon"
        self.gsc = (template / "sdk_beacon.gsc").read_bytes()
        self.ncs = {"stringType": 0, "sourceType": 2, "stringList": ["paris_model_probe"]}
        # No retail bytes or executable: only the expected names/envelope and
        # internally consistent declarations. Tests exercise bookkeeping only.
        files = {
            finalizer.BUILD_SOURCES[0]: b"synthetic original xmb",
            finalizer.BUILD_SOURCES[1]: b"synthetic original xsb",
            finalizer.BUILD_SOURCES[2]: (template / "zone.csv").read_bytes(),
            finalizer.BUILD_SOURCES[3]: ("material," + finalizer.MATERIAL + "\n").encode(),
            finalizer.BUILD_SOURCES[4]: finalizer.encoded(self.ncs),
            "manifest.json": (template / "manifest.json").read_bytes(),
            "sdk_beacon.gsc": self.gsc,
            "beacon-preparation.json": finalizer.encoded({"schema": "iw7.beacon-preparation/1",
                "writer_plan": "iw7.model-ff-plan/1", "zone": "sdk_beacon", "gsc_sha256": finalizer.sha(self.gsc),
                "ff_built": False, "runtime_ready": False}),
            "model-ff-plan.json": finalizer.encoded({"schema": "iw7.model-ff-plan/1", "synthetic_test_only": True}),
            "zone_source/paris_model_probe.csv": b"xmodel,paris_model_probe\n",
        }
        for name, raw in files.items():
            self.write(self.project, name, raw)
        self.receipt = {"schema": "iw7.beacon-source-receipt/1", "zone": "sdk_beacon", "ff_built": False,
                        "output": str(self.project), "files": []}
        self.refresh_receipt()
        self.geometry = {"schema": "iw7.model-roundtrip/1", "vertices": 24, "triangles": 12, "bones": 1,
            "surfaces": 1, "lods": 1, "shadow_cutoff_lod": 6, "collision_lod": 255, "lod0_dist": 1000000,
            "has_lods": True, "geometry_roundtrip_verified": True, "read_existing_supported": True,
            "normal_encoding": "H1-1010102-candidate", "iw7_normal_encoding_verified": False,
            "material_reference": finalizer.MATERIAL, "ff_built": False, "pixels_verified": False, "ready": False}
        ff = b"IWffu100\x00synthetic test envelope, not a valid compiled fastfile"
        self.state = {"Schema": "iw7.beacon-ff-build/1", "Status": "BootstrapInventoryAndGeometryVerified",
            "Restored": True, "StockPreserved": True, "InventoryVerified": True, "GeometryRoundtripVerified": True,
            "Ready": False, "RestorationStatus": "Confirmed", "RetainedLeaseToken": None, "CleanupError": None,
            "Work": str(self.build / "work"), "Plan": {"SourceRoot": str(self.project),
                "SourceFiles": list(finalizer.BUILD_SOURCES), "Candidate": {"SHA256": "a" * 64, "ArtifactSHA256": "b" * 64}},
            "FF": {"Path": "mod.ff", "Bytes": len(ff), "SHA256": finalizer.sha(ff)},
            "Geometry": self.geometry, "Phases": []}
        self.write(self.build, "mod.ff", ff)
        self.write(self.build, "assets.csv", ("\n".join(finalizer.INVENTORY) + "\n").encode())
        self.write(self.build, "work/dump/sdk_beacon/sdk_beacon.csv", ("\n".join(reversed(finalizer.INVENTORY)) + "\n").encode())
        log = ['Loading zone "sdk_beacon"...']
        for row in finalizer.INVENTORY:
            kind, name = row.split(",", 1)
            log.append('Loading asset "' + name + '" of type ' + kind + '.')
        self.write(self.build, "verify/stdout.log", ("\n".join(log) + "\n").encode())
        self.write_json(self.build, "read/stdout.log", self.geometry)
        for index, phase in enumerate(("build", "verify", "dump", "read")):
            self.state["Phases"].append({"Phase": phase, "PID": index + 10, "ExitCode": 0, "JobActiveAtClose": 0})
            self.write_json(self.build, phase + "/phase.json", {"schema": "iw7.beacon-tool-phase/1", "phase": phase,
                "pid": index + 100, "exit_code": 0, "failure": None})  # Native child != phase-parent PID.
        for ident, relative in finalizer.NODE_FILES.items():
            raw = b"synthetic FF dump " + relative.encode()
            if ident.startswith("netconststrings:"):
                raw = json.dumps(self.ncs).encode()  # Whitespace may differ from source.
            elif ident.startswith("rawfile:"):
                raw = b"Compiled using x64 ZoneTool."
            self.write(self.build, "work/dump/sdk_beacon/" + relative, raw)
            if relative in finalizer.BUILD_SOURCES[:2]:
                self.write(self.build, "roundtrip/" + relative, raw)
        self.save_state()

    def write(self, root, name, raw):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def write_json(self, root, name, value):
        self.write(root, name, finalizer.encoded(value))

    def refresh_receipt(self):
        self.receipt["files"] = [{"path": name, "bytes": (self.project / name).stat().st_size,
            "sha256": finalizer.sha((self.project / name).read_bytes())} for name in sorted(finalizer.PROJECT_FILES)]
        self.write_json(self.project, "source-receipt.local.json", self.receipt)

    def save_state(self):
        self.write_json(self.build, "state.local.json", self.state)

    def run_finalize(self, **kwargs):
        return finalizer.finalize(self.project, self.build, self.output, **kwargs)

    def rejected(self, fragment, **kwargs):
        with self.assertRaisesRegex((ValueError, OSError, TypeError, KeyError), fragment):
            self.run_finalize(**kwargs)
        self.assertFalse(self.output.exists())

    def load_output(self, name):
        return finalizer.decoded((self.output / name).read_bytes())

    def cli(self):
        return subprocess.run([sys.executable, "-B", str(HERE / "Finalize-BeaconProject.py"),
            "--project", str(self.project), "--build-root", str(self.build), "--output-root", str(self.output),
            "--client-source", PIN, "--server-source", PIN], capture_output=True, text=True, timeout=15)

    def test_candidate_measures_bytes_without_promoting_gates(self):
        self.write(self.project, "ignored-private-file.txt", b"never copy this")
        result = self.run_finalize(client_source=PIN, server_source=PIN)
        self.assertTrue(result["materialized"])
        for key in ("closure_complete", "package_ready", "runtime_ready", "source_receipt_bound"):
            self.assertIs(result[key], False)
        self.assertEqual(len(result["blockers"]), 3)
        manifest = self.load_output("manifest.json")
        closure = manifest["package"]["closure"]
        self.assertEqual(closure["status"], "incomplete")
        nodes = {node["id"]: node for node in closure["nodes"]}
        self.assertIsNone(nodes[finalizer.UTILITY]["sha256"])
        self.assertIsNone(nodes["material:" + finalizer.MATERIAL]["sha256"])
        self.assertIn(finalizer.UTILITY, nodes["scriptfile:custom_scripts/cp/sdk_beacon.gsc"]["requires"])
        for node in manifest["package"]["evidence"]:
            self.assertEqual(node["status"], "pending")
        for ident, relative in finalizer.NODE_FILES.items():
            raw = (self.build / "work/dump/sdk_beacon" / relative).read_bytes()
            self.assertEqual(nodes[ident]["sha256"], finalizer.sha(raw))
            self.assertEqual((self.output / "evidence/serialized-nodes" / relative).read_bytes(), raw)
        self.assertTrue(self.load_output("validation-plan.json")["valid"])
        package = self.load_output("validation-package.json")
        self.assertEqual(package["checked"], ["client_fastfile", "server_gameplay"])
        self.assertFalse(package["ready"])
        self.assertIn("closure incomplete", " ".join(package["errors"]))
        self.assertFalse((self.output / "ignored-private-file.txt").exists())
        self.assertEqual(result["bytes_written"], sum(p.stat().st_size for p in self.output.rglob("*") if p.is_file()))
        self.assertLess(result["bytes_written"], finalizer.LIMIT)
        self.assertFalse(list(self.output.rglob("*.zip")))
        self.assertNotIn("ready_to_deploy", (self.output / "finalization.json").read_text())

    def test_deterministic_same_inputs_in_distinct_output_roots(self):
        first = self.run_finalize(client_source=PIN, server_source=PIN)
        again = self.root / "candidate-again"
        second = finalizer.finalize(self.project, self.build, again, client_source=PIN, server_source=PIN)
        self.assertEqual(first["exact_hashes"], second["exact_hashes"])
        expected = {p.relative_to(self.output).as_posix(): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        actual = {p.relative_to(again).as_posix(): p.read_bytes() for p in again.rglob("*") if p.is_file()}
        self.assertEqual(expected, actual)

    def test_source_capability_assertions_do_not_create_proof(self):
        result = self.run_finalize()
        self.assertIn("Capability source proof missing", " ".join(result["blockers"]))
        evidence = self.load_output("finalization.json")
        self.assertEqual(evidence["target_source_assertions"], {"client": None, "server": None})
        self.assertFalse(evidence["recipient_current_resolution_verified"])
        self.assertFalse(evidence["owner_accepted"])

    def test_prospective_source_receipt_binding_is_measured(self):
        self.state["Plan"]["SourceReceiptSHA256"] = finalizer.sha((self.project / "source-receipt.local.json").read_bytes()).upper()
        self.save_state()
        result = self.run_finalize(client_source=PIN, server_source=PIN)
        self.assertTrue(result["source_receipt_bound"])
        self.assertTrue(self.load_output("finalization.json")["source_receipt_bound"])
        self.assertEqual(len(result["blockers"]), 2)
        self.assertFalse(result["package_ready"])

    def test_mismatched_prospective_binding_rejected(self):
        for value in (None, "", "a" * 64, True, []):
            with self.subTest(value=value):
                self.state["Plan"]["SourceReceiptSHA256"] = value
                self.save_state()
                self.rejected("SourceReceiptSHA256 differs")

    def test_source_pins_require_exact_lowercase_commits(self):
        for value in ("main", "A" * 40, "a" * 39, True):
            with self.subTest(value=value):
                self.rejected("exact lowercase commit", client_source=value)

    def test_source_receipt_hash_and_size_mismatch_rejected(self):
        for field, value in (("bytes", True), ("bytes", 1), ("sha256", "0" * 64)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt["files"][0][field] = value
                self.write_json(self.project, "source-receipt.local.json", receipt)
                self.rejected("size/hash mismatch")

    def test_exact_ten_file_allowlist_blocks_paths_and_duplicates(self):
        for path in ("../outside", str(self.root / "outside"), "C:/outside", "manifest.json:stream", "MANIFEST.json",
                     self.receipt["files"][1]["path"]):
            with self.subTest(path=path):
                receipt = copy.deepcopy(self.receipt)
                receipt["files"][0]["path"] = path
                self.write_json(self.project, "source-receipt.local.json", receipt)
                self.rejected("ten-file")

    def test_arbitrary_gsc_rejected_even_when_receipt_is_refreshed(self):
        self.write(self.project, "sdk_beacon.gsc", self.gsc + b"\n// edited\n")
        self.refresh_receipt()
        self.rejected("exact shipped beacon GSC")

    def test_arbitrary_manifest_rejected_even_when_receipt_is_refreshed(self):
        manifest = finalizer.decoded((self.project / "manifest.json").read_bytes())
        manifest["namespace"] = "another_mod"
        self.write_json(self.project, "manifest.json", manifest)
        self.refresh_receipt()
        self.rejected("fixed beacon manifest")

    def test_prepare_beacon_measured_manifest_accepted(self):
        manifest = finalizer.decoded((self.project / "manifest.json").read_bytes())
        manifest["package"]["files"][1].update(bytes=len(self.gsc), sha256=finalizer.sha(self.gsc))
        manifest["package"]["closure"]["nodes"][0]["sha256"] = finalizer.sha(self.gsc)
        self.write_json(self.project, "manifest.json", manifest)
        self.refresh_receipt()
        self.assertTrue(self.run_finalize()["materialized"])

    def test_ncs_and_zone_recipe_changes_rejected(self):
        for name, raw, error in ((finalizer.BUILD_SOURCES[2], b"xmodel,other\n", "zone recipe"),
                                (finalizer.BUILD_SOURCES[3], b"material,other\n", "Recipient recipe"),
                                (finalizer.BUILD_SOURCES[4], b"{}", "NCS source"),
                                (finalizer.BUILD_SOURCES[4], finalizer.encoded(dict(self.ncs, stringType=False)), "NCS source"),
                                (finalizer.BUILD_SOURCES[4], finalizer.encoded(dict(self.ncs, sourceType=2.0)), "NCS source")):
            with self.subTest(name=name):
                original = (self.project / name).read_bytes()
                self.write(self.project, name, raw)
                self.refresh_receipt()
                self.rejected(error)
                self.write(self.project, name, original)
                self.refresh_receipt()

    def test_failed_or_unrestored_build_rejected(self):
        original = copy.deepcopy(self.state)
        for key, value in (("Status", "Failed"), ("Restored", False), ("StockPreserved", 1), ("InventoryVerified", False),
                           ("GeometryRoundtripVerified", False), ("Ready", True), ("RestorationStatus", "Pending"),
                           ("RetainedLeaseToken", "active"), ("CleanupError", "failure"), ("Failure", "failed")):
            with self.subTest(key=key):
                self.state = copy.deepcopy(original)
                self.state[key] = value
                self.save_state()
                self.rejected("required|not established")

    def test_root_and_candidate_binding_rejected(self):
        original = copy.deepcopy(self.state)
        for key, value in (("SourceRoot", str(self.root)), ("SourceFiles", []), ("Candidate", {"SHA256": "bad", "ArtifactSHA256": "a" * 64})):
            with self.subTest(key=key):
                self.state = copy.deepcopy(original)
                self.state["Plan"][key] = value
                self.save_state()
                self.rejected("root|identity missing")

    def test_nonzero_active_and_reordered_phases_rejected(self):
        original = copy.deepcopy(self.state["Phases"])
        for key, value in (("ExitCode", 1), ("ExitCode", False), ("JobActiveAtClose", 1), ("Phase", "read")):
            with self.subTest(key=key, value=value):
                self.state["Phases"] = copy.deepcopy(original)
                self.state["Phases"][0][key] = value
                self.save_state()
                self.rejected("phase|four-phase")

    def test_native_phase_failure_rejected(self):
        self.write_json(self.build, "build/phase.json", {"schema": "iw7.beacon-tool-phase/1", "phase": "build", "exit_code": 0, "failure": "timeout"})
        self.rejected("Native phase receipt")

    def test_ff_mutation_and_non_ff_envelope_rejected(self):
        self.write(self.build, "mod.ff", b"changed")
        self.rejected("FF differs")
        self.state["FF"].update(Bytes=7, SHA256=finalizer.sha(b"changed"))
        self.save_state()
        self.rejected("FF envelope")

    def test_each_inventory_must_match_exactly(self):
        for name in ("assets.csv", "work/dump/sdk_beacon/sdk_beacon.csv", "verify/stdout.log"):
            with self.subTest(name=name):
                original = (self.build / name).read_bytes()
                self.write(self.build, name, original.replace(b"paris_model_probe_lod0", b"other_model"))
                self.rejected("inventor")
                self.write(self.build, name, original)

    def test_verification_error_log_rejected(self):
        path = self.build / "verify/stdout.log"
        path.write_bytes(path.read_bytes() + b"\n[ ERROR ] broken\n")
        self.rejected("Verification log missing or failed")

    def test_geometry_receipts_disagree_or_claim_wrong_semantics(self):
        self.geometry["vertices"] = 25
        self.save_state()
        self.rejected("Reader output differs")
        self.write_json(self.build, "read/stdout.log", self.geometry)
        self.rejected("geometry receipt differs")

    def test_reader_input_and_dump_ncs_rejected(self):
        name = "roundtrip/" + finalizer.BUILD_SOURCES[0]
        original = (self.build / name).read_bytes()
        self.write(self.build, name, b"changed")
        self.rejected("Reader input differs")
        self.write(self.build, name, original)
        self.write_json(self.build, "work/dump/sdk_beacon/" + finalizer.BUILD_SOURCES[4], {})
        self.rejected("Dumped NCS differs")

    def test_recipient_pair_and_unsupported_boolean_proof_rejected(self):
        self.rejected("supplied together", recipient_root=self.root)
        proof = self.root / "proof.json"
        proof.write_bytes(finalizer.encoded({"schema": "iw7.model-recipient-evidence/1", "runtime_verified": True}))
        self.rejected("snapshot-only", recipient_proof=proof, recipient_root=self.root)
        snapshot = finalizer.decoded((finalizer.REPO / "ops/model-lab/recipient.evidence.json").read_bytes())
        snapshot["runtime_verified"] = 0  # JSON type must not be coerced to false.
        proof.write_bytes(finalizer.encoded(snapshot))
        self.rejected("snapshot-only", recipient_proof=proof, recipient_root=self.root)

    def test_reviewed_snapshot_missing_payload_is_not_accepted(self):
        proof = finalizer.REPO / "ops/model-lab/recipient.evidence.json"
        with self.assertRaises(OSError):
            self.run_finalize(recipient_proof=proof, recipient_root=self.root)
        self.assertFalse(self.output.exists())

    def test_snapshot_hash_is_not_current_closure_even_with_matching_fixture(self):
        # A substituted review contract with tiny fixture payloads exercises the
        # optional hash path only. It is not a test of any real retail snapshot.
        fixture_repo = self.root / "fixture-repo"
        snapshot = {"schema": "iw7.model-recipient-evidence/1", "snapshot_only": True, "runtime_verified": False, "material_snapshot": {}}
        for key in ("closure", "load_log", "material_json"):
            raw = ("synthetic " + key).encode()
            name = key + ".data"
            self.write(self.root, name, raw)
            snapshot["material_snapshot"][key] = {"path": name, "bytes": len(raw), "sha256": finalizer.sha(raw)}
        self.write_json(fixture_repo, "ops/model-lab/recipient.evidence.json", snapshot)
        self.write_json(self.root, "proof.json", snapshot)
        with mock.patch.object(finalizer, "REPO", fixture_repo):
            result = self.run_finalize(recipient_proof=self.root / "proof.json", recipient_root=self.root)
        self.assertFalse(result["closure_complete"])
        self.assertFalse(result["package_ready"])
        evidence = self.load_output("finalization.json")
        self.assertTrue(evidence["recipient_snapshot_measured"])
        self.assertFalse(evidence["recipient_current_resolution_verified"])

    def test_existing_output_and_missing_parent_never_modified(self):
        self.output.mkdir()
        sentinel = self.output / "owner.txt"
        sentinel.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "Fresh output"):
            self.run_finalize()
        self.assertEqual(sentinel.read_text(), "preserve")
        self.output = self.root / "missing-parent" / "output"
        self.rejected("No such|cannot find|system cannot")

    def test_reparse_attribute_rejected(self):
        original = Path.lstat
        def attributes(path, *args, **kwargs):
            if path == self.project:
                return SimpleNamespace(st_mode=0o40755, st_file_attributes=0x400)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "lstat", attributes):
            self.rejected("Redirected")

    def test_actual_symlink_input_rejected_when_supported(self):
        target = self.project / "sdk_beacon.gsc"
        saved = self.project / "saved.gsc"
        target.rename(saved)
        try:
            target.symlink_to(saved)
        except OSError as error:
            saved.rename(target)
            self.skipTest("Symlink creation unavailable: " + str(error))
        self.rejected("Redirected")

    def test_source_change_before_materialization_rejected(self):
        original = finalizer.Inputs.recheck
        def mutate_then_recheck(inputs):
            self.write(self.project, "sdk_beacon.gsc", b"changed after validation")
            original(inputs)
        with mock.patch.object(finalizer.Inputs, "recheck", mutate_then_recheck):
            self.rejected("Input changed before materialization")

    def test_output_budget_includes_last_package_report(self):
        result = self.run_finalize(client_source=PIN, server_source=PIN)
        report_size = (self.output / "validation-package.json").stat().st_size
        self.output = self.root / "bounded-candidate"
        with mock.patch.object(finalizer, "LIMIT", result["bytes_written"] - report_size + 1):
            self.rejected("2 MiB byte budget", client_source=PIN, server_source=PIN)

    def test_post_write_failure_cleans_only_created_files(self):
        original = finalizer.OutputFiles.write
        def fail_report(writer, name, raw):
            if name == "validation-package.json":
                raise OSError("Injected write failure")
            original(writer, name, raw)
        with mock.patch.object(finalizer.OutputFiles, "write", fail_report):
            self.rejected("Injected write failure")

    def test_cleanup_preserves_replaced_and_unowned_files(self):
        original = finalizer.sdk.validate
        def corrupt_candidate(data, root=None, **kwargs):
            if root is not None:
                path = root / "sdk_beacon.gsc"
                path.rename(root / "concurrent-saved.gsc")
                path.write_bytes(b"concurrent replacement must survive")
                (root / "unowned.txt").write_bytes(b"owner data")
            return original(data, root=root, **kwargs)
        with mock.patch.object(finalizer.sdk, "validate", corrupt_candidate):
            with self.assertRaisesRegex(ValueError, "payload verification failed"):
                self.run_finalize()
        self.assertEqual((self.output / "sdk_beacon.gsc").read_bytes(), b"concurrent replacement must survive")
        self.assertEqual((self.output / "unowned.txt").read_bytes(), b"owner data")
        self.assertFalse((self.output / "mod.ff").exists())

    def test_cli_exit_zero_means_materialized_blocked_candidate(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        response = json.loads(result.stdout)
        self.assertTrue(response["materialized"])
        self.assertFalse(response["package_ready"])
        self.assertEqual(response["api"], "beacon-finalize/1")

    def test_cli_rejects_duplicate_nonfinite_or_nonobject_json_without_output(self):
        for raw in (b'{"Schema":1,"Schema":2}', b'{"Schema":NaN}', b'{"Schema":1e999}', b'[]', b'{'):
            with self.subTest(raw=raw):
                self.write(self.build, "state.local.json", raw)
                result = self.cli()
                self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                self.assertFalse(json.loads(result.stdout)["materialized"])
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
