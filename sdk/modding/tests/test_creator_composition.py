"""Asset-free composition and real CLI routing; no native tool or stock access."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

SDK = Path(__file__).resolve().parents[1]
REPO = SDK.parents[1]
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


c = module(SDK / "creator_composition.py", "composition_under_test")
cli = module(SDK / "tests/test_creator.py", "composition_cli_fixtures")


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.cli = cli.CreatorTests()
        self.cli.setUp()
        self.addCleanup(self.cli.doCleanups)
        self.asset = self.cli.materialize_fixture()
        self.cli.variant_project()
        self.project, self.root = self.cli.project, self.asset.root
        self.descriptor = {"schema": "iw7.creator-composition/1",
            "script": {"policy": c.SCRIPT_POLICY, "path": "sdk_beacon_self_contained.gsc", "bytes": 5535,
                       "sha256": "9de9b76dc25293146999c71653bd407d8cb639e107293f6de87084fed90eee1c"},
            "assets": {"policy": c.ASSET_POLICY, "project": str(self.asset.project), "build_root": str(self.asset.build),
                "source_receipt_sha256": self.hash(self.asset.project / "source-receipt.local.json"),
                "build_receipt_sha256": self.hash(self.asset.build / "state.local.json"), "ff_sha256": self.hash(self.asset.build / "mod.ff")},
            "evidence": {"gsc": None, "recipient": None}}
        self.save()

    def hash(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save(self):
        (self.project / "composition.json").write_text(json.dumps(self.descriptor), encoding="utf-8")

    def materialize(self):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("No native process")):
            return c.materialize(self.project, self.asset.build, self.asset.output, REPO, client_source=PIN, server_source=PIN)

    def rejected(self, text):
        with self.assertRaisesRegex((ValueError, OSError, KeyError, TypeError), text):
            self.materialize()
        self.assertFalse(self.asset.output.exists())

    def test_composition_retains_original_asset_history_and_separate_variant_payload(self):
        before = self.cli.snapshot()
        result = self.materialize()
        self.assertTrue(result["creator_output_verified"])
        self.assertTrue(result["asset_build_reused"])
        self.assertTrue(result["asset_source_receipt_bound"])
        self.assertFalse(result["variant_ff_built"])
        self.assertEqual(len(result["candidate_files_verified"]), 10)
        for key in ("closure_complete", "package_ready", "runtime_ready"):
            self.assertFalse(result[key])
        for name, digest in before.items():
            self.assertEqual(self.cli.snapshot()[name], digest)
        output = self.asset.output
        self.assertEqual((output / "mod.ff").read_bytes(), (self.asset.build / "mod.ff").read_bytes())
        self.assertEqual((output / "sdk_beacon_self_contained.gsc").read_bytes(), (self.project / "sdk_beacon_self_contained.gsc").read_bytes())
        self.assertFalse((output / "sdk_beacon.gsc").exists())
        self.assertFalse(list(self.root.rglob("*.zip")))
        manifest = json.loads((output / "manifest.json").read_bytes())
        nodes = manifest["package"]["closure"]["nodes"]
        self.assertIn("rawfile:sdk_beacon", [n["id"] for n in nodes])
        self.assertNotIn("rawfile:sdk_beacon_self_contained", [n["id"] for n in nodes])
        self.assertNotIn("utility", json.dumps(manifest))
        receipt = json.loads((output / "finalization.json").read_bytes())
        self.assertEqual(receipt["composition"], self.descriptor)
        self.assertFalse(receipt["encoded_external_script_reference_absence"])
        self.assertFalse(receipt["unresolved_qualifications"][0]["dependency_edge_asserted"])

    def test_unreviewed_script_policy_cannot_accept_an_arbitrary_script(self):
        self.descriptor["script"]["policy"] = "arbitrary-source/1"
        self.save()
        self.rejected("Unreviewed composition policy")

    def test_changed_script_cannot_be_reapproved_by_repinning_descriptor(self):
        path = self.project / "sdk_beacon_self_contained.gsc"
        path.write_bytes(path.read_bytes() + b"\n// changed")
        self.descriptor["script"].update(bytes=path.stat().st_size, sha256=self.hash(path))
        self.save()
        self.rejected("exact separate reviewed source")

    def test_unknown_fields_and_executable_commands_are_refused(self):
        self.descriptor["command"] = "Run anything"
        self.save()
        self.rejected("descriptor fields")

    def test_asset_build_and_source_pins_cannot_be_swapped(self):
        for field in ("source_receipt_sha256", "build_receipt_sha256", "ff_sha256"):
            with self.subTest(field=field):
                original = self.descriptor["assets"][field]
                self.descriptor["assets"][field] = "0" * 64
                self.save()
                self.rejected("asset pin differs: " + field)
                self.descriptor["assets"][field] = original

    def test_changed_ff_and_rawfile_are_rejected_by_shared_build_validator(self):
        for name in ("mod.ff", "work/dump/sdk_beacon/sdk_beacon"):
            with self.subTest(name=name):
                path = self.asset.build / name
                raw = path.read_bytes()
                path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                self.rejected("FF differs|Unexpected generated beacon rawfile")
                path.write_bytes(raw)

    def test_original_source_binding_is_required_and_never_replaced_by_variant_source(self):
        self.asset.state["Plan"].pop("SourceReceiptSHA256")
        self.asset.save_state()
        self.descriptor["assets"]["build_receipt_sha256"] = self.hash(self.asset.build / "state.local.json")
        self.save()
        self.rejected("original source-bound asset build")

    def test_fresh_separate_output_is_required_for_all_three_input_roots(self):
        for root in (self.project, self.asset.project, self.asset.build):
            with self.subTest(root=root):
                self.asset.output = root / "candidate"
                self.rejected("output overlaps")

    def attach_recipient(self):
        fixtures = module(SDK / "tests/test_recipient_evidence.py", "composition_recipient_fixtures")
        fixture = fixtures.EvidenceTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        fixture.receipt_path = fixture.root / "references/phase.json"
        fixture.receipt_path.parent.mkdir()
        fixture.phase("references")
        self.descriptor["evidence"]["recipient"] = {"run_root": str(fixture.root),
            "phase_sha256": self.hash(fixture.receipt_path),
            "csv_sha256": self.hash(fixture.work / "enemy-catalog/sdk_beacon_recipient_a.csv")}
        self.save()
        return fixture

    def test_recipient_phase_attaches_only_four_reference_observations(self):
        self.attach_recipient()
        self.materialize()
        receipt = json.loads((self.asset.output / "finalization.json").read_bytes())
        observation = receipt["recipient_observation"]
        self.assertTrue(observation["phase_bytes_verified"])
        self.assertEqual(observation["observation"]["verified_references"], 4)
        self.assertFalse(observation["run_bound"])
        self.assertFalse(observation["stock_identity_verified"])
        self.assertFalse(observation["analysis"]["content_identity_measured"])
        self.assertFalse(observation["analysis"]["dependency_inventory_measured"])
        manifest = json.loads((self.asset.output / "manifest.json").read_bytes())
        material = next(n for n in manifest["package"]["closure"]["nodes"] if n["kind"] == "material")
        self.assertIsNone(material["sha256"])
        self.assertEqual(len(manifest["package"]["closure"]["unresolved"]), 3)

    def test_tampered_recipient_csv_cannot_remove_pending_questions(self):
        fixture = self.attach_recipient()
        (fixture.work / "enemy-catalog/sdk_beacon_recipient_a.csv").write_bytes(b"changed")
        self.rejected("recipient evidence pin differs")

    def test_historical_gsc_consumption_does_not_become_encoded_reference_qualification(self):
        fixtures = module(SDK / "tests/test_creator_gsc_audit.py", "composition_audit_fixtures")
        audit = fixtures.AuditFixture(self.root / "audit")
        path = audit.base / "expectations.json"
        path.write_text(json.dumps(audit.evidence), encoding="utf-8")
        self.descriptor["evidence"]["gsc"] = {"path": str(path), "sha256": self.hash(path)}
        self.save()
        self.materialize()
        receipt = json.loads((self.asset.output / "finalization.json").read_bytes())
        self.assertTrue(receipt["gsc_observation"]["global_completion_record_linked"])
        self.assertFalse(receipt["encoded_external_script_reference_absence"])
        self.assertTrue(receipt["unresolved_qualifications"])

    def reference_composition(self, failed=False):
        fixtures = module(SDK / "tests/test_creator_gsc_references.py", "composition_reference_fixtures")
        audit = fixtures.ReferenceFixture(self.root / "reference-audit")
        if failed:
            audit.supervision.update(Success=False, Failure="collector failure", CompletionEvidence=None)
            audit.save()
        path = audit.base / "expectations.json"
        path.write_text(json.dumps(audit.evidence), encoding="utf-8")
        self.descriptor["evidence"]["gsc"] = {"path": str(path), "sha256": self.hash(path)}
        self.save()
        finalizer = c._finalizer(REPO)
        original_module = finalizer.module
        def select_module(path, name):
            return fixtures.a if Path(path).name == "creator_gsc_audit.py" else original_module(path, name)
        with mock.patch.object(c, "_finalizer", return_value=finalizer), mock.patch.object(finalizer, "module", side_effect=select_module), \
             mock.patch.object(fixtures.a, "REFERENCE_SOURCES", audit.source_pins), \
             mock.patch.object(fixtures.a, "REFERENCE_INPUTS", {role: fixtures.a.sha(audit.raw["input"]) for role in ("variant", "original")}):
            return self.materialize()

    def test_synthetic_reference_qualification_removes_only_its_exact_question(self):
        self.reference_composition()
        receipt = json.loads((self.asset.output / "finalization.json").read_bytes())
        self.assertTrue(receipt["encoded_external_script_reference_absence"])
        self.assertEqual(receipt["unresolved_qualifications"], [])
        self.assertTrue(any("transitive" in text for text in receipt["blockers"]))
        self.assertTrue(any("builtin/loader" in text for text in receipt["blockers"]))
        for key in ("closure_complete", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertFalse(receipt[key])

    def test_failed_global_reference_run_cannot_create_a_candidate(self):
        with self.assertRaisesRegex(ValueError, "Global audit supervision failed"):
            self.reference_composition(failed=True)
        self.assertFalse(self.asset.output.exists())

    def test_shared_postwrite_verifier_rejects_composition_asset_and_receipt_corruption(self):
        original = c.finalize
        for name in ("evidence/serialized-nodes/xsurface/paris_model_probe_lod0.xsb", "finalization.json", "validation-package.json"):
            with self.subTest(name=name):
                self.asset.output = self.root / ("candidate-" + str(len(name)))
                def changed(*args, **kwargs):
                    result = original(*args, **kwargs)
                    path = Path(result["candidate_root"]) / name
                    raw = path.read_bytes()
                    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                    return result
                with mock.patch.object(c, "finalize", side_effect=changed):
                    with self.assertRaisesRegex(ValueError, "differs"):
                        self.materialize()
                self.assertTrue(self.asset.output.exists())

    @unittest.skipUnless(cli.PWSH, "PowerShell 7 required")
    def test_real_cli_materializes_composition_with_explicit_pending_and_no_builder(self):
        code, report = self.cli.invoke("-Adapter", "BeaconSelfContainedV1", "-Action", "Materialize", "-BuildRoot", str(self.asset.build),
                                      "-FinalizeRoot", str(self.asset.output), mutates=True)
        self.assertEqual(code, 0, report)
        self.assertTrue(report["materialized"])
        self.assertFalse(report["build_executed"])
        self.assertFalse(report["packaged"])
        self.assertNotIn("adapter_plan_requested", report)
        self.assertEqual(report["pending"], report["finalization"]["blockers"])
        self.assertIn("Variant Build is not connected", " ".join(report["source_project_pending"]))

    @unittest.skipUnless(cli.PWSH, "PowerShell 7 required")
    def test_real_cli_preserves_original_asset_collisions(self):
        code, report = self.cli.invoke("-Adapter", "BeaconSelfContainedV1", "-Action", "Materialize", "-BuildRoot", str(self.asset.build),
                                      "-FinalizeRoot", str(self.asset.output), "-ActiveProject", str(self.asset.project))
        self.assertEqual(code, 1, report)
        self.assertTrue(any("collision" in e.lower() or "conflict" in e.lower() for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
