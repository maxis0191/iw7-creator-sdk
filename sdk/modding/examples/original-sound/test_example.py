"""Real Plan/materializer checks; synthetic metadata only, no game/audio payloads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IDENT = "sdk_original_sound_v1"
POWERSHELL = shutil.which("pwsh")


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sdk = load("sdk/modding/manifest.py", "original_sound_example_sdk")
compat = load("ops/modding/Distribution-Compat.py", "original_sound_example_compat")
closure_adapter = load("sdk/modding/examples/original-sound/Complete-StaticClosure.py", "original_sound_example_closure")
sound_source = load("tools-source/asset-bridge/surfaces/sound/prepare_sound.py", "original_sound_example_source")


def plan_result(manifest):
    return sdk.validate(manifest, root=None, stage="plan", target="native")


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.manifest = sdk.load_manifest(HERE / "manifest.json")

    def test_actual_plan_has_no_measured_payload_or_ready_claim(self):
        result = plan_result(self.manifest)
        self.assertTrue(result["valid"], result["errors"])
        for key in ("ready", "runtime_ready", "owner_accepted"):
            self.assertIs(result[key], False)
        self.assertEqual(result["checked"], [])
        self.assertIsNone(self.manifest["compatibility"]["network_protocol"])
        package = self.manifest["package"]
        self.assertEqual(package["closure"]["status"], "incomplete")
        for item in package["files"]:
            self.assertIsNone(item["bytes"])
            self.assertIsNone(item["sha256"])
        for node in package["closure"]["nodes"]:
            self.assertIsNone(node["sha256"])
        self.assertTrue(all(record["status"] == "pending" and record["reference"] is None
                            for record in package["evidence"]))

    def test_minimal_four_file_contract_and_canonical_entrypoint(self):
        package = self.manifest["package"]
        self.assertEqual([(f["role"], f["source"], f["destination"]) for f in package["files"]], [
            *(('client', 'client/' + name, 'mods/' + IDENT + '/' + name)
              for name in ('mod.ff', 'mod.sabl', 'mod.sabs')),
            ('server', 'server/' + IDENT + '.gsc', 'iw7-mod/custom_scripts/cp/' + IDENT + '.gsc'),
        ])
        self.assertEqual(self.manifest["lifecycle"]["entrypoints"], [
            {"side": "server", "path": "custom_scripts/cp/" + IDENT + ".gsc", "symbol": "init"}])
        self.assertEqual({node["kind"] for node in package["closure"]["nodes"]},
                         {"sound", "other", "scriptfile"})
        self.assertEqual(self.manifest["requires"], {
            "engine": ["iw7-cp/1"], "client": ["mod-fastfile-download/1"],
            "server": ["mod-fastfile-host/1", "gsc-custom-scripts/1"],
        })

    def test_unknown_environment_is_refused_by_real_compatibility_check(self):
        errors = compat.check_environment([self.manifest], client_source=None,
                                           server_source=None, protocol=None, mode="cp")
        self.assertIn("A measured integer network protocol is required", errors)
        self.assertTrue(any("Capability source proof missing" in error for error in errors))


class ServerSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-original-sound-server-")
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.cleanup)
        self.entry = sdk.load_manifest(HERE / "manifest.json")["package"]["files"][3]
        self.path = self.root / self.entry["source"]
        self.path.parent.mkdir()

    def cleanup(self):
        self.assertEqual(self.root.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(self.root.name.startswith("iw7-original-sound-server-"))
        self.temp.cleanup()

    def test_hash_is_of_the_delivered_bytes_not_the_repository_template(self):
        for raw in (b"// synthetic fixture A\ninit() { return; }\n", b"// synthetic fixture B\r\ninit() { return; }\r\n"):
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                report = closure_adapter.read_server_source(self.root, self.entry)
                self.assertEqual(report["bytes"], len(raw))
                self.assertEqual(report["sha256"], hashlib.sha256(raw).hexdigest())

    def test_missing_empty_and_oversized_gsc_are_refused(self):
        with self.assertRaises(FileNotFoundError):
            closure_adapter.read_server_source(self.root, self.entry)
        for raw in (b"", b"x" * 16385):
            self.path.write_bytes(raw)
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                closure_adapter.read_server_source(self.root, self.entry)

    def test_binding_cannot_select_an_unrelated_script(self):
        changed = copy.deepcopy(self.entry)
        changed["source"] = "server/unrelated.gsc"
        with self.assertRaisesRegex(ValueError, "canonical delivered"):
            closure_adapter.read_server_source(self.root, changed)

    def test_relative_package_root_is_refused(self):
        with self.assertRaisesRegex(ValueError, "absolute package root"):
            closure_adapter.read_server_source("relative", self.entry)


@unittest.skipUnless(POWERSHELL, "PowerShell 7 is required for the real materializer")
class MaterializerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iw7-original-sound-example-")
        self.directory = Path(self.temp.name).resolve()
        self.addCleanup(self.cleanup)
        self.manifest = sdk.load_manifest(HERE / "manifest.json")
        self.plan, self.state, self.phase_evidence = self.fixture()
        self.plan_path = self.directory / "execution-plan.json"
        self.state_path = Path(self.plan["RunRoot"]) / "state.local.json"
        self.output = self.directory / "materialized.json"
        self.package_root = None

    def cleanup(self):
        # Only the exact randomly allocated metadata directory is disposable.
        self.assertEqual(self.directory.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(self.directory.name.startswith("iw7-original-sound-example-"))
        self.temp.cleanup()

    def fixture(self):
        """Dummy declarations, never measurements of a producer run or binaries."""
        run = self.directory / "producer"
        work = run / "work"
        sound = ROOT / "tools-source/asset-bridge/surfaces/sound"
        plan = dict(Schema="iw7.original-sound-ff-execution/1", Profile="StandardMod",
                    RunRoot=str(run), Work=str(work), Python=str(self.directory / "absent-python.exe"),
                    Ready=False, HeavyExecutionAuthorizedByPlan=False,
                    MutableOutputs=["zone/" + name for name in ("mod.ff", "mod.sabl", "mod.sabs")],
                    Review=dict(source=str(self.directory / "absent-source"),
                                phase_adapter=str(sound / "sound_ff_phase.py"), phase_specs=[]))
        reader = dict(schema="iw7.original-sound-sab-read/1", status="SABBytesVerified",
                      dump_profile="StandardModC", dump_streaminfo_block_size=4096,
                      inventory_provenance="CurrentVerifyPhase", bank_zone="mod", disk_zone="mod",
                      standard_filenames=["mod.ff", "mod.sabl", "mod.sabs"], inventory_asset_count=2,
                      fastfile=dict(bytes=1200, sha256="a" * 64),
                      loaded=dict(bytes=114816, sha256="b" * 64,
                                  pcm_sha256="72cb02b5178ce424fd3df3dbfb28b0b9613f69a4da3af71a022b8b542a46ddd9"),
                      streamed=dict(bytes=4096, sha256="c" * 64))
        for key in ("standard_source_verified", "dump_bank_zone_verified", "standard_filenames_verified",
                    "source_alias_verified", "source_alias_matches_sab_asset", "dump_alias_values_verified",
                    "inventory_verified", "dump_seek_frame_bytes_verified"):
            reader[key] = True
        for key in ("native_alias_index_verified", "checksum_checksum_verified",
                    "dump_standalone_flac_validated", "playback_verified", "ready"):
            reader[key] = False
        state = dict(Schema="iw7.original-sound-ff-result/1", Status="SoundStandardModBytesVerified",
                     Profile="StandardMod", Work=str(work), RestorationStatus="Confirmed",
                     Transaction=dict(Schema="iw7.base-transaction/1", GameRoot=str(work),
                                      BackupRoot=str(run / "backup"), Restored=True),
                     OutputAccountingStatus="Converged", FinalObservedBytes=180000,
                     MaxObservedBytes=190000, Phases=[], Artifacts=[], Reader=reader)
        for key in ("Restored", "StockPreserved", "JobClosureVerified", "JobDisposeCompleted",
                    "SourceHashesUnchanged", "ReadGuardsReleased"):
            state[key] = True
        for key in ("Quarantined", "Ready", "PlaybackVerified"):
            state[key] = False
        for key in ("RetainedLeaseToken", "Failure", "CleanupError", "OutputAccountingError",
                    "OutputBudgetError", "JobCleanup"):
            state[key] = None
        for name, key in zip(("mod.ff", "mod.sabl", "mod.sabs"), ("fastfile", "loaded", "streamed")):
            state["Artifacts"].append(dict(Relative="zone/" + name, Bytes=reader[key]["bytes"],
                                           SHA256=reader[key]["sha256"], ArtifactPath=str(run / "artifacts" / name)))
        evidence = []
        for name in ("build", "verify", "dump", "read"):
            is_read = name == "read"
            timeout = 30 if is_read else 240
            arguments = (["-B", str(sound / "read_sab.py"), "--source", plan["Review"]["source"],
                          "--banks", str(work / "zone"), "--contract", str(sound / "sab_contract.json"),
                          "--dump", str(work / "dump/mod"), "--inventory", str(run / "logs/verify/stdout.log"),
                          "--dump-profile", "StandardModC"] if is_read else
                         ["-headless", "-unbuffered-io", "-strict-content-sources", "-" + name + "zone", "mod"])
            spec = dict(schema="iw7.material-v2-phase/1", phase=name,
                        exe=plan["Python"] if is_read else str(work / "zonetool.exe"), sha256="d" * 64,
                        arguments=arguments, cwd=str(work), logs=str(run / "logs" / name), timeout=timeout)
            plan["Review"]["phase_specs"].append(spec)
            state["Phases"].append(dict(
                Phase=name, PID=1234, Image=plan["Python"], Priority=16384,
                CreatedUtc="2026-10-12T00:00:00.0000000Z", StartedUtc="2026-10-12T00:00:01.0000000Z",
                SpecSHA256="e" * 64, NativeExecutableSHA256=spec["sha256"], SchedulerAttached=True,
                ExitCode=0, JobActiveAtClose=0, JobRootExitedAtClose=True, PostReceiptDecisionElapsedMs=120,
                Supervision=dict(Outcome="Closed", DrainLimitMs=2000, PhaseLimitMs=(timeout + 5) * 1000,
                                 DecisionElapsedMs=100, DrainElapsedMs=10),
                SoundReceipt=dict(schema="iw7.original-sound-ff-phase/1", phase=name, verified=True,
                                  explicit_normal_pipe_returns=True, drain_exception_types=[],
                                  existing_runner_receipt_sha256="f" * 64, ready=False, playback_verified=False)))
            evidence.append(dict(schema="iw7.material-v2-phase-result/1", phase=name,
                                 executable_sha256=spec["sha256"], failure=None, exit_code=0, log_limit_each=2097152))
        return plan, state, evidence

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(value, indent=2).encode("utf-8")
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def add_static_closure(self):
        """Synthetic metadata and one temporary GSC only; no FF/SAB/sample bytes."""
        r = closure_adapter.reader
        common = sdk.load_manifest(ROOT / "tools-source/asset-bridge/surfaces/source_contract.json")
        alias = sound_source.alias_csv(common["alias_csv_fields"])
        bank = dict(name=r.BANK, zone="mod", gameLanguage="all", soundLanguage="all", aliases=[r.ALIAS_PATH])
        bank.update({key: [path] for key, (path, _) in r.AUXILIARY.items()})
        self.bank_raw = json.dumps(bank, indent=2).encode() + b"\n"
        self.state["Reader"]["dump_streaminfo_rewritten"] = True
        self.state["Reader"]["closure_evidence"] = {
            "schema": "iw7.original-sound-static-closure/1",
            "representations": {"soundbank": r.representation(r.BANK_PATH, self.bank_raw),
                                "rawfile": r.representation("mod", r.RAWFILE)},
            "dependencies": {"source_alias": r.representation(r.ALIAS_PATH, alias),
                             "aliases": r.representation(r.ALIAS_PATH, alias.replace(b"0.5,0.5", b"0.500000,0.500000")),
                             "sample": {"bytes": 96394, "sha256": "1" * 64},
                             "inventory": {"bytes": 123, "sha256": "2" * 64},
                             "auxiliary": {key: r.representation(path, raw)
                                           for key, (path, raw) in r.AUXILIARY.items()}},
            "artifacts": {name: {key: self.state["Reader"][field][key] for key in ("bytes", "sha256")}
                          for name, field in zip(("mod.ff", "mod.sabl", "mod.sabs"), ("fastfile", "loaded", "streamed"))},
        }
        self.package_root = self.directory / "package"
        self.gsc = self.package_root / closure_adapter.SERVER_SOURCE
        self.gsc.parent.mkdir(parents=True)
        self.gsc.write_bytes(b"// Synthetic delivered source; no actual gameplay.\ninit() { return; }\n")

    def run_materializer(self, *, bad_state_pin=False):
        run = Path(self.plan["RunRoot"])
        for phase, spec, evidence in zip(self.state["Phases"], self.plan["Review"]["phase_specs"], self.phase_evidence):
            name = phase["Phase"]
            phase["SpecSHA256"] = self.write_json(run / (name + "-spec.json"), spec)
            phase["SoundReceipt"]["existing_runner_receipt_sha256"] = self.write_json(run / "logs" / name / "phase.json", evidence)
        plan_pin = self.write_json(self.plan_path, self.plan)
        state_pin = self.write_json(self.state_path, self.state)
        command = [
            POWERSHELL, "-NoLogo", "-NoProfile", "-File", str(HERE / "Materialize-Plan.ps1"),
            "-BuildPlanPath", str(self.plan_path), "-BuildPlanSHA256", plan_pin,
            "-BuildReceiptPath", str(self.state_path), "-BuildReceiptSHA256", "0" * 64 if bad_state_pin else state_pin,
            "-OutputPath", str(self.output),
        ]
        if self.package_root is not None:
            command += ["-PackageRoot", str(self.package_root)]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertFalse((run / "artifacts").exists(), "No test may create payloads")
        self.assertFalse((run / "work").exists(), "No producer executable or work is staged")
        return result

    def test_real_materializer_changes_only_three_client_measurements(self):
        result = self.run_materializer()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(report["ProducerMetadataVerified"])
        self.assertEqual(report["ClientMeasurementsCopiedFromReceipt"], 3)
        for key in ("PayloadMeasured", "PackageReady", "RuntimeReady", "OwnerAccepted"):
            self.assertIs(report[key], False)
        self.assertEqual(report["ManifestSHA256"].lower(), hashlib.sha256(self.output.read_bytes()).hexdigest())
        expected = copy.deepcopy(self.manifest)
        for entry, artifact in zip(expected["package"]["files"], self.state["Artifacts"]):
            entry.update(bytes=artifact["Bytes"], sha256=artifact["SHA256"])
        materialized = sdk.load_manifest(self.output)
        self.assertEqual(materialized, expected)
        validated = plan_result(materialized)
        self.assertTrue(validated["valid"], validated["errors"])
        self.assertEqual(validated["checked"], [])
        self.assertFalse(validated["ready"])

    def assert_refused_without_output(self, **kwargs):
        result = self.run_materializer(**kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        return result

    def test_unrestored_producer_is_rejected_by_actual_gate(self):
        self.state["Restored"] = False
        self.assert_refused_without_output()

    def test_tampered_state_pin_is_rejected(self):
        self.assert_refused_without_output(bad_state_pin=True)

    def test_valid_producer_size_still_must_pass_separate_http_cap(self):
        self.state["Artifacts"][0]["Bytes"] = 2000
        self.state["Reader"]["fastfile"]["bytes"] = 2000
        result = self.assert_refused_without_output()
        self.assertIn("1600", result.stderr)

    def test_output_cannot_modify_closed_producer_run(self):
        self.output = Path(self.plan["RunRoot"]) / "materialized.json"
        result = self.assert_refused_without_output()
        self.assertIn("outside the closed producer run", result.stderr)

    def test_existing_output_is_preserved(self):
        self.output.write_text("preserve this existing file", encoding="utf-8")
        result = self.run_materializer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "preserve this existing file")

    def test_static_closure_maps_exact_representations_and_delivered_gsc(self):
        self.add_static_closure()
        # Native PowerShell receipt hashes may be uppercase; digest identity is unchanged.
        for artifact in self.state["Artifacts"]:
            artifact["SHA256"] = artifact["SHA256"].upper()
        result = self.run_materializer()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        for key in ("ProducerMetadataVerified", "ServerSourceMeasured", "StaticClosureComplete", "RepresentationsRevalidated"):
            self.assertIs(report[key], True)
        for key in ("ClientPayloadMeasured", "PackageReady", "RuntimeReady", "OwnerAccepted"):
            self.assertIs(report[key], False)
        materialized = sdk.load_manifest(self.output)
        package = materialized["package"]
        nodes = {node["id"]: node for node in package["closure"]["nodes"]}
        self.assertEqual(package["closure"]["status"], "complete")
        self.assertEqual(nodes[closure_adapter.BANK_NODE]["sha256"], hashlib.sha256(self.bank_raw).hexdigest())
        self.assertNotEqual(nodes[closure_adapter.BANK_NODE]["sha256"], package["files"][0]["sha256"].lower())
        self.assertEqual(nodes[closure_adapter.RAWFILE_NODE]["sha256"], hashlib.sha256(closure_adapter.reader.RAWFILE).hexdigest())
        self.assertEqual(nodes[closure_adapter.SCRIPT_NODE]["sha256"], hashlib.sha256(self.gsc.read_bytes()).hexdigest())
        self.assertEqual(package["files"][3]["sha256"], nodes[closure_adapter.SCRIPT_NODE]["sha256"])
        self.assertIn(hashlib.sha256(self.state_path.read_bytes()).hexdigest(), package["closure"]["evidence_ref"])
        self.assertIsNone(materialized["compatibility"]["network_protocol"])
        self.assertEqual(package["evidence"], self.manifest["package"]["evidence"])
        validated = plan_result(materialized)
        self.assertTrue(validated["valid"], validated["errors"])
        self.assertEqual(validated["pending"], ["Exact network_protocol must be measured before packaging"])
        self.assertEqual(validated["checked"], [])
        for key in ("ready", "runtime_ready", "owner_accepted"):
            self.assertIs(validated[key], False)

    def test_closure_evidence_alone_does_not_measure_server_or_complete_plan(self):
        self.add_static_closure()
        self.package_root = None
        result = self.run_materializer()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        materialized = sdk.load_manifest(self.output)
        self.assertEqual(materialized["package"]["closure"]["status"], "incomplete")
        self.assertIsNone(materialized["package"]["files"][3]["sha256"])
        self.assertFalse(json.loads(result.stdout)["ServerSourceMeasured"])

    def test_old_receipt_cannot_complete_static_closure(self):
        self.package_root = self.directory / "absent-package"
        self.assert_refused_without_output()

    def test_static_closure_rejects_bank_pin_replaced_by_ff_pin(self):
        self.add_static_closure()
        self.state["Reader"]["closure_evidence"]["representations"]["soundbank"]["sha256"] = self.state["Reader"]["fastfile"]["sha256"]
        result = self.assert_refused_without_output()
        self.assertIn("representation bytes/hash mismatch", result.stderr)

    def test_static_closure_rejects_changed_rawfile_even_with_refreshed_hash(self):
        self.add_static_closure()
        self.state["Reader"]["closure_evidence"]["representations"]["rawfile"] = closure_adapter.reader.representation("mod", b"unrelated rawfile")
        self.assert_refused_without_output()

    def test_static_closure_rejects_artifacts_disconnected_from_producer(self):
        self.add_static_closure()
        self.state["Reader"]["closure_evidence"]["artifacts"]["mod.ff"]["sha256"] = "9" * 64
        result = self.assert_refused_without_output()
        self.assertIn("closure artifact differs from reader", result.stderr)

    def test_static_closure_requires_the_delivered_server_file(self):
        self.add_static_closure()
        self.gsc.unlink()
        self.assert_refused_without_output()


if __name__ == "__main__":
    unittest.main()
