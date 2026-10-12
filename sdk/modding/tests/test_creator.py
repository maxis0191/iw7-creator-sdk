"""Real Creator CLI tests using existing Python gates; no native adapter executes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile

SDK = Path(__file__).resolve().parents[1]
CREATOR = SDK / "Creator.ps1"
REPO = SDK.parents[1]
TOOLS = Path(os.environ.get("IW7_CREATOR_TEST_TOOLS_ROOT", REPO))
PWSH = shutil.which("pwsh")
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


@unittest.skipUnless(PWSH, "PowerShell 7 is required for the real Creator CLI")
class CreatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.manifest = json.loads((SDK / "examples/beacon/manifest.json").read_text())
        self.save_manifest()
        (self.project / "sdk_beacon.gsc").write_bytes((SDK / "examples/beacon/sdk_beacon.gsc").read_bytes())
        self.addCleanup(self.temp.cleanup)

    def save_manifest(self):
        (self.project / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def invoke(self, *extra, environment=True, mutates=False, tools=TOOLS, wrapper=None):
        before = self.snapshot()
        args = [PWSH, "-NoProfile", "-File", str(wrapper or CREATOR), "-Project", str(self.project),
                "-ToolsRoot", str(tools), "-Json"]
        if environment:
            args += ["-ClientSource", PIN, "-ServerSource", PIN, "-Protocol", "2"]
        run = subprocess.run([*args, *extra], text=True, capture_output=True, timeout=20)
        self.assertEqual(run.stderr, "", run.stderr)
        report = json.loads(run.stdout)
        if not mutates:
            self.assertEqual(before, self.snapshot(), "Plan/refused Build wrote or modified a file")
            self.assertFalse(report["build_executed"])
            self.assertFalse(report["materialized"])
            self.assertFalse(report["packaged"])
        self.assertFalse(report["runtime_ready"])
        self.assertFalse(report["owner_accepted"])
        return run.returncode, report

    def test_real_plan_and_exact_adapter_identity(self):
        code, report = self.invoke("-Adapter", "BeaconV1")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["plan_valid"])
        self.assertTrue(report["pending"])
        steps = {s["name"]: s for s in report["steps"]}
        self.assertEqual(steps["dependencies-and-target"]["status"], "passed")
        self.assertEqual(steps["adapter-plan"]["status"], "pending")
        self.assertEqual(steps["package"]["status"], "not-run")

    def test_case_insensitive_powershell_options_remain_canonical(self):
        code, report = self.invoke("-Action", "plan", "-Adapter", "beaconv1", "-Target", "STOCK")
        self.assertEqual(code, 0, report)
        self.assertEqual(report["action"], "Plan")
        self.assertEqual(report["adapter"], "BeaconV1")
        code, report = self.invoke("-Action", "build", "-Adapter", "beaconv1")
        self.assertEqual(code, 1, report)
        self.assertEqual(report["action"], "Build")
        self.assertIn("complete BuildParameters", " ".join(report["errors"]))

    def test_missing_environment_is_not_qualified(self):
        code, report = self.invoke(environment=False)
        self.assertEqual(code, 1)
        self.assertFalse(report["plan_valid"])
        self.assertTrue(any("Supply ClientSource" in p for p in report["pending"]))

    def test_missing_dependency_is_checked_by_real_distribution(self):
        self.manifest["dependencies"] = [{"id": "missing_mod", "version": "1.0.0"}]
        self.save_manifest()
        code, report = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("Missing exact dependency", " ".join(report["errors"]))

    def test_active_collision_is_checked(self):
        code, report = self.invoke("-ActiveProject", str(self.project))
        self.assertEqual(code, 1)
        self.assertIn("Namespace collision", " ".join(report["errors"]))

    def test_edited_gsc_is_not_accepted_as_fixed_beacon(self):
        with (self.project / "sdk_beacon.gsc").open("ab") as output:
            output.write(b"\n// changed project\n")
        code, report = self.invoke("-Adapter", "BeaconV1")
        self.assertEqual(code, 1)
        self.assertIn("exact reviewed template GSC", " ".join(report["errors"]))

    def test_build_refuses_before_any_mutation(self):
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1",
                                   "-FinalizeRoot", str(self.root / "candidate"),
                                   "-Output", str(self.root / "result.zip"))
        self.assertEqual(code, 1)
        self.assertIn("Build requires BeaconV1 and complete BuildParameters", " ".join(report["errors"]))
        self.assertFalse((self.root / "candidate").exists())
        self.assertFalse((self.root / "result.zip").exists())

    def test_parameter_file_cannot_smuggle_run(self):
        parameters = self.root / "parameters.json"
        parameters.write_text(json.dumps({"SourceRoot": str(self.project), "Run": "false"}))
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameters))
        self.assertEqual(code, 1)
        self.assertIn("unknown fields", " ".join(report["errors"]))

    def test_named_future_adapter_is_not_a_fake_success(self):
        code, report = self.invoke("-Adapter", "AnimationProbe")
        self.assertEqual(code, 1)
        self.assertIn("not connected or qualified", " ".join(report["errors"]))

    def test_missing_builder_parameters_refuse_without_interactive_prompt(self):
        parameters = self.root / "parameters.json"
        parameters.write_text(json.dumps({"SourceRoot": str(self.project), "OpsRoot": str(TOOLS / "ops")}))
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameters))
        self.assertEqual(code, 1)
        self.assertIn("missing required fields", " ".join(report["errors"]))

    def variant_project(self, manifest=False):
        self.project = self.root / "variant"
        self.project.mkdir()
        (self.project / "sdk_beacon_self_contained.gsc").write_bytes(
            (SDK / "examples/beacon-self-contained/sdk_beacon_self_contained.gsc").read_bytes())
        if manifest:
            (self.project / "manifest.json").write_bytes((SDK / "creator_beacon_self_contained.manifest.json").read_bytes())

    def test_self_contained_plan_selects_exact_source_and_preserves_all_evidence_gaps(self):
        self.variant_project()
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["plan_valid"])
        selected = report["source_selection"]
        self.assertTrue(selected["source_bytes_verified"])
        self.assertEqual(selected["source"]["sha256"], "9de9b76dc25293146999c71653bd407d8cb639e107293f6de87084fed90eee1c")
        self.assertFalse(selected["project_manifest_present"])
        for key in ("contract_written", "build_adapter_qualified", "compiled_input_bound", "bytecode_fully_consumed_verified",
                    "stack_fully_consumed_verified", "external_gsc_dependency_absence_verified", "recipient_closure_complete",
                    "package_ready", "runtime_ready", "owner_accepted"):
            self.assertIs(selected[key], False, key)
        contract = selected["proposed_contract"]
        self.assertEqual(contract["namespace"], "sdk_beacon_self_contained")
        self.assertEqual(contract["package"]["closure"]["status"], "incomplete")
        utility = "scriptfile:scripts/engine/utility.gsc"
        self.assertNotIn(utility, contract["package"]["closure"]["unresolved"])
        self.assertFalse(any(utility in node["requires"] for node in contract["package"]["closure"]["nodes"]))
        self.assertEqual(selected["unresolved_qualifications"][0]["status"], "unresolvedQualification")
        self.assertFalse(selected["unresolved_qualifications"][0]["dependency_edge_asserted"])
        self.assertIn("zero observed Far calls is insufficient", " ".join(selected["pending"]))
        self.assertNotIn("adapter_plan_requested", report)

    def test_self_contained_optional_manifest_must_be_exact_planning_contract(self):
        self.variant_project(manifest=True)
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["source_selection"]["project_manifest_present"])
        path = self.project / "manifest.json"
        data = json.loads(path.read_bytes())
        data["package"]["closure"]["status"] = "complete"
        data["package"]["closure"]["unresolved"] = []
        path.write_text(json.dumps(data))
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 1)
        self.assertIn("must equal the reviewed", " ".join(report["errors"]))

    def test_self_contained_duplicate_manifest_fields_are_refused(self):
        self.variant_project(manifest=True)
        path = self.project / "manifest.json"
        path.write_bytes(b'{"namespace":"sdk_beacon_self_contained",' + path.read_bytes()[1:])
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 1)
        self.assertIn("Duplicate Creator manifest key", " ".join(report["errors"]))

    def test_self_contained_is_explicit_and_keeps_original_adapter_identity(self):
        self.variant_project()
        code, report = self.invoke("-Adapter", "None")
        self.assertEqual(code, 1)
        self.assertNotIn("source_selection", report)
        (self.project / "manifest.json").write_bytes((SDK / "examples/beacon/manifest.json").read_bytes())
        (self.project / "sdk_beacon.gsc").write_bytes((self.project / "sdk_beacon_self_contained.gsc").read_bytes())
        code, report = self.invoke("-Adapter", "BeaconV1")
        self.assertEqual(code, 1)
        self.assertIn("exact reviewed template GSC", " ".join(report["errors"]))

    def test_self_contained_edited_source_is_refused_even_with_forged_audit_summary(self):
        self.variant_project()
        path = self.project / "sdk_beacon_self_contained.gsc"
        path.write_bytes(path.read_bytes() + b"\n// modified\n")
        (self.project / "validation.local.json").write_text(json.dumps({
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "observed_external_script_calls": 0,
            "external_gsc_dependency_absence_verified": True}))
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 1)
        self.assertIn("exact separate reviewed source", " ".join(report["errors"]))

    def test_self_contained_zero_far_summary_cannot_promote_consumption_or_closure(self):
        self.variant_project()
        (self.project / "validation.local.json").write_text(json.dumps({"observed_external_script_calls": 0,
            "external_gsc_dependency_absence_verified": True, "bytecode_fully_consumed_verified": True,
            "stack_fully_consumed_verified": True, "asset_closure_complete": True, "runtime_ready": True}))
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1")
        self.assertEqual(code, 0, report)
        selected = report["source_selection"]
        for key in ("bytecode_fully_consumed_verified", "stack_fully_consumed_verified", "external_gsc_dependency_absence_verified",
                    "recipient_closure_complete", "package_ready", "runtime_ready"):
            self.assertIs(selected[key], False)

    def test_self_contained_conflicts_and_real_asset_collision_with_original(self):
        original = self.project
        self.variant_project()
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-ActiveProject", str(original))
        self.assertEqual(code, 1)
        self.assertIn("Active conflict", " ".join(report["errors"]))
        self.assertIn("Delivered asset collision: xmodel:paris_model_probe", " ".join(report["errors"]))

    def test_self_contained_missing_compatibility_is_not_qualified(self):
        self.variant_project()
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", environment=False)
        self.assertEqual(code, 1)
        self.assertFalse(report["plan_valid"])
        self.assertTrue(any("Supply ClientSource" in x for x in report["pending"]))

    def test_self_contained_cli_options_are_canonical_and_build_is_refused(self):
        self.variant_project()
        code, report = self.invoke("-Adapter", "beaconselfcontainedv1", "-Action", "plan")
        self.assertEqual(code, 0, report)
        self.assertEqual(report["adapter"], "BeaconSelfContainedV1")
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-Action", "Build")
        self.assertEqual(code, 1)
        self.assertIn("Build is not connected or qualified", " ".join(report["errors"]))

    def test_self_contained_execution_parameters_cannot_enter_original_builder(self):
        tools, parameter_file = self.flow_fixture()
        for relative in ("creator_self_contained.py", "creator_beacon_self_contained.manifest.json",
                         "examples/beacon-self-contained/sdk_beacon_self_contained.gsc"):
            destination = tools / "sdk/modding" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((SDK / relative).read_bytes())
        (tools / "sdk/modding/Build-BeaconFF.ps1").write_text("throw 'ORIGINAL BUILDER MUST NEVER BE INVOKED'\n")
        self.variant_project()
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-Action", "Build", "-BuildParameters", str(parameter_file), tools=tools)
        self.assertEqual(code, 1)
        self.assertTrue(report["source_selection"]["source_bytes_verified"])
        self.assertIn("source-only Plan selection", " ".join(report["errors"]))
        self.assertNotIn("ORIGINAL BUILDER", " ".join(report["errors"]))
        for option in ("-BuildParameters", "-RecipientProof", "-RecipientRoot", "-FinalizeRoot", "-Output"):
            with self.subTest(option=option):
                code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", option, str(self.root / "absent"), tools=tools)
                self.assertEqual(code, 1)
                self.assertIn("source-only Plan selection", " ".join(report["errors"]))

    def test_self_contained_tools_source_pin_cannot_be_replaced_with_project_bytes(self):
        tools, _ = self.flow_fixture()
        for relative in ("creator_self_contained.py", "creator_beacon_self_contained.manifest.json",
                         "examples/beacon-self-contained/sdk_beacon_self_contained.gsc"):
            destination = tools / "sdk/modding" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((SDK / relative).read_bytes())
        self.variant_project()
        fake = b"// both copies changed to the same unreviewed source\n"
        (self.project / "sdk_beacon_self_contained.gsc").write_bytes(fake)
        (tools / "sdk/modding/examples/beacon-self-contained/sdk_beacon_self_contained.gsc").write_bytes(fake)
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", tools=tools)
        self.assertEqual(code, 1)
        self.assertIn("source pin changed in ToolsRoot", " ".join(report["errors"]))

    def test_self_contained_tools_contract_cannot_silently_claim_closure(self):
        tools, _ = self.flow_fixture()
        for relative in ("creator_self_contained.py", "creator_beacon_self_contained.manifest.json",
                         "examples/beacon-self-contained/sdk_beacon_self_contained.gsc"):
            destination = tools / "sdk/modding" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((SDK / relative).read_bytes())
        self.variant_project()
        path = tools / "sdk/modding/creator_beacon_self_contained.manifest.json"
        data = json.loads(path.read_bytes())
        data["package"]["closure"]["status"] = "complete"
        data["package"]["closure"]["unresolved"] = []
        path.write_text(json.dumps(data))
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", tools=tools)
        self.assertEqual(code, 1)
        self.assertIn("planning contract pin changed", " ".join(report["errors"]))

    def flow_fixture(self, mode="incomplete"):
        """Real validators/ZIP writer; explicit doubles for native builder/finalizer.

        These prove orchestration only. The tiny .ff is text, never a game asset.
        """
        tools = self.root / "fixture-tools"
        paths = ["sdk/modding/manifest.py", "sdk/modding/manifest.schema.json", "sdk/modding/capabilities.json",
                 "sdk/modding/examples/beacon/sdk_beacon.gsc", "ops/Validate-ModPackage.py",
                 "ops/modding/Package-CommunityMod.py", "ops/modding/Distribution-Compat.py"]
        for relative in paths:
            destination = tools / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((TOOLS / relative).read_bytes())
        (tools / "fixture-mode.txt").write_text(mode)
        parameters = {name: "fixture-unused" for name in (
            "SourceReceiptSHA256", "StockRoot", "StockReceipt", "StockReceiptSHA256", "CandidateRoot",
            "CandidateArtifactSHA256", "ReaderRoot", "JobSource", "JobSourceSHA256", "StockBindingReceipt",
            "StockBindingReceiptSHA256", "ReviewedStockManifest", "ReviewedStockManifestSHA256")}
        parameters.update(SourceRoot=str(self.project), OpsRoot=str(tools / "ops"), RunRoot=str(self.root / "run"))
        parameter_file = self.root / "parameters.json"
        parameter_file.write_text(json.dumps(parameters))
        declarations = ",".join("[string]$" + name for name in parameters)
        builder = "param(" + declarations + ",[switch]$Run)\n" + textwrap.dedent('''\
            $ErrorActionPreference='Stop'
            $mode=Get-Content (Join-Path $PSScriptRoot '../../fixture-mode.txt') -Raw
            if(!$Run){@{Schema='iw7.beacon-ff-plan/1';Ready=$false;CandidatePending=$false}|ConvertTo-Json;return}
            if($mode -ceq 'build-failure'){throw 'Synthetic builder refusal, no native process'}
            New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop|Out-Null
            'Synthetic orchestration only; no native build'|Set-Content (Join-Path $RunRoot 'fixture.txt')
            ''')
        (tools / "sdk/modding/Build-BeaconFF.ps1").write_text(builder)
        finalizer = textwrap.dedent('''\
            import argparse, hashlib, json
            from pathlib import Path
            parser = argparse.ArgumentParser()
            for field in ('project', 'build-root', 'output-root', 'client-source', 'server-source', 'recipient-proof', 'recipient-root'):
                parser.add_argument('--' + field)
            args = parser.parse_args()
            mode = (Path(__file__).parents[2] / 'fixture-mode.txt').read_text()
            if mode == 'finalize-failure':
                print(json.dumps({'api': 'beacon-finalize/1', 'materialized': False, 'errors': ['Synthetic refusal']}))
                raise SystemExit(1)
            output = Path(args.output_root)
            output.mkdir()
            manifest = json.loads((Path(args.project) / 'manifest.json').read_text())
            for entry in manifest['package']['files']:
                entry['source'] = 'fixture.ff' if entry['role'] == 'client' else 'sdk_beacon.gsc'
                payload = b'SYNTHETIC TEXT - NOT A FASTFILE' if entry['role'] == 'client' else (Path(args.project) / entry['source']).read_bytes()
                (output / entry['source']).write_bytes(payload)
                entry.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            complete = mode != 'incomplete'
            if complete:
                closure = manifest['package']['closure']
                closure.update(status='complete', evidence_ref='SYNTHETIC ORCHESTRATION TEST ONLY')
                for node in closure['nodes']:
                    node['sha256'] = hashlib.sha256(('SYNTHETIC ' + node['id']).encode()).hexdigest()
            path = output / 'manifest.json'
            path.write_text(json.dumps(manifest))
            if mode == 'tamper':
                (output / 'fixture.ff').write_bytes(b'changed')
            print(json.dumps({'api': 'beacon-finalize/1', 'materialized': True, 'candidate_root': str(output),
                'manifest_path': str(path), 'closure_complete': complete, 'package_ready': complete,
                'runtime_ready': mode == 'bad-contract', 'blockers': [] if complete else ['Missing recipient closure']}))
            ''')
        (tools / "sdk/modding/Finalize-BeaconProject.py").write_text(finalizer)
        return tools, parameter_file

    def invoke_flow(self, mode, *extra):
        tools, parameters = self.flow_fixture(mode)
        return self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameters),
                           "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"),
                           *extra, tools=tools, mutates=True)

    def test_flow_incomplete_closure_materializes_but_never_packages(self):
        code, report = self.invoke_flow("incomplete")
        self.assertEqual(code, 1, report)
        self.assertTrue(report["build_executed"])
        self.assertTrue(report["build_verified"])
        self.assertTrue(report["materialized"])
        self.assertFalse(report["packaged"])
        self.assertIn("Missing recipient closure", report["pending"])
        self.assertFalse((self.root / "result.zip").exists())

    def test_flow_builder_failure_never_finalizes(self):
        code, report = self.invoke_flow("build-failure")
        self.assertEqual(code, 1, report)
        self.assertTrue(report["build_executed"])
        self.assertFalse(report["build_verified"])
        self.assertFalse(report["materialized"])
        self.assertFalse((self.root / "candidate").exists())

    def test_flow_finalizer_failure_keeps_build_artifacts_without_zip(self):
        code, report = self.invoke_flow("finalize-failure")
        self.assertEqual(code, 1, report)
        self.assertTrue((self.root / "run/fixture.txt").exists())
        self.assertFalse(report["materialized"])
        self.assertFalse(report["packaged"])

    def test_flow_real_packager_rechecks_tampered_candidate(self):
        code, report = self.invoke_flow("tamper")
        self.assertEqual(code, 1, report)
        self.assertTrue(report["materialized"])
        self.assertFalse(report["packaged"])
        self.assertIn("Payload size mismatch", " ".join(report["errors"]))
        self.assertFalse((self.root / "result.zip").exists())

    def test_flow_synthetic_archive_uses_real_zip_writer(self):
        code, report = self.invoke_flow("complete")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["packaged"])
        with zipfile.ZipFile(self.root / "result.zip") as archive:
            self.assertEqual(archive.read("fastdl/mods/sdk_beacon/mod.ff"), b"SYNTHETIC TEXT - NOT A FASTFILE")
        self.assertEqual(report["package_result"]["archive_sha256"], hashlib.sha256((self.root / "result.zip").read_bytes()).hexdigest())

    def test_flow_unexpected_finalizer_contract_is_refused(self):
        code, report = self.invoke_flow("bad-contract")
        self.assertEqual(code, 1, report)
        self.assertFalse(report["build_verified"])
        self.assertFalse(report["packaged"])

    def test_flow_existing_output_refuses_before_builder(self):
        tools, parameters = self.flow_fixture()
        (self.root / "result.zip").write_bytes(b"preserve existing")
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameters),
                                   "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"), tools=tools)
        self.assertEqual(code, 1, report)
        self.assertIn("Fresh output path required", " ".join(report["errors"]))
        self.assertFalse((self.root / "run").exists())

    def test_flow_nested_outputs_refuse_before_builder(self):
        tools, parameters = self.flow_fixture()
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameters),
                                   "-FinalizeRoot", str(self.root / "run"), "-Output", str(self.root / "result.zip"), tools=tools)
        self.assertEqual(code, 1, report)
        self.assertIn("separate, non-nested", " ".join(report["errors"]))

    def test_flow_stale_builder_refuses_before_calling_its_plan(self):
        tools, parameters = self.flow_fixture()
        builder = tools / "sdk/modding/Build-BeaconFF.ps1"
        builder.write_text(builder.read_text().replace("[string]$StockBindingReceipt,", ""))
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameters),
                                   "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"), tools=tools)
        self.assertEqual(code, 1, report)
        self.assertIn("does not support parameter StockBindingReceipt", " ".join(report["errors"]))
        self.assertFalse((self.root / "run").exists())

    def test_flow_recipient_pair_is_required_before_native_work(self):
        tools, parameters = self.flow_fixture()
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameters),
                                   "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"),
                                   "-RecipientProof", str(self.root / "missing.json"), tools=tools)
        self.assertEqual(code, 1, report)
        self.assertIn("must be supplied together", " ".join(report["errors"]))

    def test_parameter_rewrite_after_python_read_cannot_inject_run(self):
        tools, parameter_file = self.flow_fixture()
        malicious = json.loads(parameter_file.read_text())
        malicious["Run"] = True
        # Deterministic file rewrite at the first Python parameter read boundary.
        # Only the isolated fixture's Path.open is wrapped; production has no hook.
        hook = textwrap.dedent('''\
            from pathlib import Path as _RacePath
            _race_original_open = _RacePath.open
            _race_done = False
            class _RaceReader:
                def __init__(self, stream):
                    self.stream = stream
                def __enter__(self):
                    return self.stream.__enter__()
                def __exit__(self, *args):
                    result = self.stream.__exit__(*args)
                    with _race_original_open(_race_target, 'wb') as output:
                        output.write(_race_bytes)
                    return result
            def _race_open(self, *args, **kwargs):
                global _race_done
                stream = _race_original_open(self, *args, **kwargs)
                if not _race_done and self == _race_target and args == ('rb',):
                    _race_done = True
                    return _RaceReader(stream)
                return stream
            _RacePath.open = _race_open
            ''')
        validator = tools / "sdk/modding/manifest.py"
        with validator.open("a", encoding="utf-8") as output:
            output.write("\n_race_target = Path(" + repr(str(parameter_file)) + ")\n")
            output.write("_race_bytes = " + repr(json.dumps(malicious).encode()) + "\n")
            output.write(hook)
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameter_file), tools=tools, mutates=True)
        self.assertIs(json.loads(parameter_file.read_text())["Run"], True, "The rewrite hook must actually fire")
        self.assertFalse((self.root / "run").exists(), "Plan invoked the synthetic builder's Run branch")
        self.assertEqual(code, 1, report)
        self.assertIn("BuildParameters changed during planning", " ".join(report["errors"]))
        self.assertFalse(report["build_executed"])

    def test_parameter_rewrite_after_powershell_hash_does_not_change_snapshot(self):
        tools, parameter_file = self.flow_fixture()
        malicious = json.loads(parameter_file.read_text())
        malicious["Run"] = True
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        wrapper = self.root / "hash-rewrite-wrapper.ps1"
        wrapper.write_text("$raceTarget=" + quote(parameter_file) + "\n$raceBytes=" + quote(json.dumps(malicious)) + "\n" + textwrap.dedent('''\
            function Get-FileHash {
                param([string]$LiteralPath,[IO.Stream]$InputStream,[string]$Algorithm='SHA256')
                if($InputStream){$result=Microsoft.PowerShell.Utility\\Get-FileHash -InputStream $InputStream -Algorithm $Algorithm}
                else{$result=Microsoft.PowerShell.Utility\\Get-FileHash -LiteralPath $LiteralPath -Algorithm $Algorithm}
                if($InputStream -or $LiteralPath -eq $raceTarget){[IO.File]::WriteAllText($raceTarget,$raceBytes)}
                return $result
            }
            ''') + "& " + quote(CREATOR) + " @args\nexit $LASTEXITCODE\n")
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameter_file),
                                   tools=tools, mutates=True, wrapper=wrapper)
        self.assertIs(json.loads(parameter_file.read_text())["Run"], True, "The rewrite hook must actually fire")
        self.assertFalse((self.root / "run").exists(), "A rewrite replaced the already-hashed snapshot")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["plan_valid"])
        self.assertFalse(report["build_executed"])

    def test_parameter_rewrite_during_adapter_plan_blocks_explicit_build(self):
        tools, parameter_file = self.flow_fixture()
        malicious = json.loads(parameter_file.read_text())
        malicious["Run"] = True
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        builder = tools / "sdk/modding/Build-BeaconFF.ps1"
        rewrite = "[IO.File]::WriteAllText(" + quote(parameter_file) + "," + quote(json.dumps(malicious)) + ");"
        builder.write_text(builder.read_text().replace("if(!$Run){", "if(!$Run){" + rewrite))
        code, report = self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameter_file),
                                   "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"),
                                   tools=tools, mutates=True)
        self.assertIs(json.loads(parameter_file.read_text())["Run"], True)
        self.assertEqual(code, 1, report)
        self.assertIn("BuildParameters changed during planning", " ".join(report["errors"]))
        self.assertFalse(report["build_executed"])
        self.assertFalse((self.root / "run").exists())

    def test_last_splat_allowlist_does_not_inherit_builder_run_parameter(self):
        tools, parameter_file = self.flow_fixture()
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        wrapper = self.root / "metadata-injection-wrapper.ps1"
        marker = self.root / "metadata-hook.txt"
        wrapper.write_text("$metadataMarker=" + quote(marker) + "\n" + textwrap.dedent('''\
            function Get-Command {
                [CmdletBinding()]param([Parameter(Position=0)][string]$Name)
                $result=Microsoft.PowerShell.Core\\Get-Command -Name $Name
                if($Name.EndsWith('Build-BeaconFF.ps1')){
                    # Simulate a changed splat after snapshot validation, at the
                    # metadata check that previously admitted every builder key.
                    $splat=Get-Variable -Name parameters -Scope 1 -ValueOnly
                    $splat['Run']=$true
                    [IO.File]::WriteAllText($metadataMarker,'Injected Run into caller splat')
                }
                return $result
            }
            ''') + "& " + quote(CREATOR) + " @args\nexit $LASTEXITCODE\n")
        code, report = self.invoke("-Adapter", "BeaconV1", "-BuildParameters", str(parameter_file),
                                   tools=tools, mutates=True, wrapper=wrapper)
        self.assertTrue(marker.is_file(), "Metadata hook must reach the already-parsed splat")
        self.assertEqual(code, 1, report)
        self.assertIn("Run and arbitrary commands are prohibited", " ".join(report["errors"]))
        self.assertFalse(report["build_executed"])
        self.assertFalse((self.root / "run").exists())

    def real_finalizer_flow(self, *, tamper=False):
        """Real Creator/finalizer; reuse asset-free receipt fixtures, no native work."""
        spec = importlib.util.spec_from_file_location("creator_finalizer_fixture", TOOLS / "sdk/modding/tests/test_beacon_finalize.py")
        fixture_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_module)
        fixture = fixture_module.FinalizeTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.root, self.project = fixture.root, fixture.project
        tools, parameter_file = self.flow_fixture()
        for relative in ("sdk/modding/Finalize-BeaconProject.py", "sdk/modding/examples/beacon/manifest.json",
                         "sdk/modding/examples/beacon/zone.csv"):
            (tools / relative).write_bytes((TOOLS / relative).read_bytes())
        parameters = json.loads(parameter_file.read_text())
        source_hash = hashlib.sha256((self.project / "source-receipt.local.json").read_bytes()).hexdigest()
        parameters["SourceReceiptSHA256"] = source_hash
        parameter_file.write_text(json.dumps(parameters))
        fixture.state["Plan"]["SourceReceiptSHA256"] = source_hash
        fixture.save_state()
        if tamper:
            (fixture.build / "mod.ff").write_bytes(b"tampered synthetic fixture")
        copier = tools / "copy_fixture.py"
        copier.write_text(textwrap.dedent('''\
            import json, shutil, sys
            from pathlib import Path
            source, destination = map(Path, sys.argv[1:])
            shutil.copytree(source, destination)
            path = destination / 'state.local.json'
            state = json.loads(path.read_text())
            state['Work'] = str(destination / 'work')
            path.write_text(json.dumps(state))
            '''))
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        builder = "param(" + ",".join("[string]$" + key for key in parameters) + ",[switch]$Run)\n"
        builder += "$ErrorActionPreference='Stop'\n"
        builder += "if(!$Run){@{Schema='iw7.beacon-ff-plan/1';Ready=$false;CandidatePending=$false}|ConvertTo-Json;return}\n"
        builder += "& " + quote(sys.executable) + " -B " + quote(copier) + " " + quote(fixture.build) + " $RunRoot\n"
        builder += "if($LASTEXITCODE -ne 0){throw 'Synthetic fixture copy failed'}\n"
        (tools / "sdk/modding/Build-BeaconFF.ps1").write_text(builder)
        return self.invoke("-Action", "Build", "-Adapter", "BeaconV1", "-BuildParameters", str(parameter_file),
                           "-FinalizeRoot", str(self.root / "candidate"), "-Output", str(self.root / "result.zip"),
                           tools=tools, mutates=True)

    def test_real_finalizer_materializes_bound_receipts_and_keeps_package_blocked(self):
        code, report = self.real_finalizer_flow()
        self.assertEqual(code, 1, report)
        self.assertTrue(report["build_executed"])
        self.assertTrue(report["build_verified"])
        self.assertTrue(report["materialized"])
        self.assertTrue(report["finalization"]["source_receipt_bound"])
        self.assertFalse(report["finalization"]["closure_complete"])
        self.assertFalse(report["finalization"]["package_ready"])
        self.assertEqual(len(report["finalization"]["blockers"]), 2)
        self.assertFalse(report["packaged"])
        self.assertFalse((self.root / "result.zip").exists())

    def test_real_finalizer_rejects_altered_ff_without_candidate_or_archive(self):
        code, report = self.real_finalizer_flow(tamper=True)
        self.assertEqual(code, 1, report)
        self.assertTrue(report["build_executed"])
        self.assertFalse(report["build_verified"])
        self.assertFalse(report["materialized"])
        self.assertFalse(report["packaged"])
        self.assertIn("FF differs from measured build", report["finalization"]["errors"])
        self.assertFalse((self.root / "candidate").exists())
        self.assertFalse((self.root / "result.zip").exists())

    def gsc_audit_fixture(self, version=2):
        spec = importlib.util.spec_from_file_location("creator_audit_fixture", SDK / "tests/test_creator_gsc_audit.py")
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        fixture = fixtures.AuditFixture(self.root / ("gsc-audit-" + str(version)), version)
        self.project = fixture.project
        path = fixture.base / "expectations.json"
        path.write_text(json.dumps(fixture.evidence), encoding="utf-8")
        return fixture, path

    def test_real_cli_links_v2_audit_records_without_build_or_package(self):
        fixture, path = self.gsc_audit_fixture()
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-GscAuditEvidence", str(path))
        self.assertEqual(code, 0, report)
        self.assertTrue(report["plan_valid"])
        self.assertTrue(report["gsc_audit"]["global_completion_record_linked"])
        self.assertTrue(report["gsc_audit"]["native_witness_bytes_bound"])
        self.assertFalse(report["gsc_audit"]["external_gsc_dependency_absence_verified"])
        self.assertFalse(report["gsc_audit"]["finalization_allowed"])
        self.assertFalse(report["build_verified"])
        self.assertFalse(report.get("adapter_plan_requested", False))
        self.assertEqual(report["gsc_audit_evidence_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_real_cli_displays_v1_global_failure_without_reclassifying_it(self):
        fixture, path = self.gsc_audit_fixture(version=1)
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-GscAuditEvidence", str(path))
        self.assertEqual(code, 0, report)
        self.assertTrue(report["gsc_audit"]["structural_consumption_measured"])
        self.assertFalse(report["gsc_audit"]["global_completion_record_linked"])
        self.assertFalse(report["gsc_audit"]["supervision_success_reported"])
        self.assertIn("supervision recorded failure", " ".join(report["pending"]))

    def test_real_cli_refuses_altered_pinned_audit_input(self):
        fixture, path = self.gsc_audit_fixture()
        fixture.paths["input"].write_bytes(b"different container")
        code, report = self.invoke("-Adapter", "BeaconSelfContainedV1", "-GscAuditEvidence", str(path))
        self.assertEqual(code, 1, report)
        self.assertFalse(report["plan_valid"])
        self.assertIn("hash differs", " ".join(report["errors"]))
        self.assertNotIn("gsc_audit", report)

    def test_audit_option_requires_selected_variant_plan_before_any_evidence_read(self):
        for options in (("-Adapter", "BeaconV1"), ("-Adapter", "None"),
                        ("-Adapter", "BeaconSelfContainedV1", "-Action", "Build")):
            code, report = self.invoke(*options, "-GscAuditEvidence", str(self.root / "does-not-exist.json"))
            self.assertEqual(code, 1, report)
            self.assertIn("requires explicit BeaconSelfContainedV1 Plan", " ".join(report["errors"]))
            self.assertNotIn("gsc_audit", report)

    def materialize_fixture(self, bound=True):
        spec = importlib.util.spec_from_file_location("creator_materialize_fixture", TOOLS / "sdk/modding/tests/test_beacon_finalize.py")
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        fixture = fixtures.FinalizeTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.root, self.project = fixture.root, fixture.project
        if bound:
            fixture.state["Plan"]["SourceReceiptSHA256"] = hashlib.sha256((self.project / "source-receipt.local.json").read_bytes()).hexdigest()
            fixture.save_state()
        return fixture

    def invoke_materialize(self, fixture, *extra, mutates=False, tools=TOOLS, action="Materialize"):
        return self.invoke("-Action", action, "-Adapter", "BeaconV1", "-BuildRoot", str(fixture.build),
                           "-FinalizeRoot", str(fixture.output), *extra, mutates=mutates, tools=tools)

    def test_materialize_creates_real_checked_candidate_and_succeeds_with_blockers(self):
        fixture = self.materialize_fixture()
        before = self.snapshot()
        code, report = self.invoke_materialize(fixture, mutates=True, action="materialize")
        self.assertEqual(code, 0, report)
        self.assertEqual(report["action"], "Materialize")
        self.assertTrue(report["plan_valid"])
        self.assertTrue(report["build_verified"])
        self.assertTrue(report["materialized"])
        self.assertFalse(report["build_executed"])
        self.assertFalse(report["packaged"])
        self.assertNotIn("adapter_plan_requested", report)
        final = report["finalization"]
        self.assertTrue(final["creator_output_verified"])
        self.assertTrue(final["source_receipt_bound"])
        self.assertFalse(final["package_ready"])
        self.assertFalse(final["closure_complete"])
        self.assertEqual(len(final["blockers"]), 2)
        self.assertEqual(report["pending"], final["blockers"])
        self.assertIn("Payload not established", " ".join(report["source_project_pending"]))
        self.assertEqual(len(final["candidate_files_verified"]), 10)
        self.assertEqual(final["bytes_written"], sum(p.stat().st_size for p in fixture.output.rglob("*") if p.is_file()))
        self.assertFalse(list(self.root.rglob("*.zip")))
        for name, checksum in before.items():
            self.assertEqual(self.snapshot()[name], checksum)
        step = next(x for x in report["steps"] if x["name"] == "materialize")
        self.assertTrue(all(x in step["details"] and x in report["pending"] for x in final["blockers"]))

    def test_materialize_preserves_historical_source_binding_blocker(self):
        fixture = self.materialize_fixture(bound=False)
        code, report = self.invoke_materialize(fixture, mutates=True)
        self.assertEqual(code, 0, report)
        self.assertFalse(report["finalization"]["source_receipt_bound"])
        self.assertEqual(len(report["finalization"]["blockers"]), 3)
        self.assertIn("lacks Plan.SourceReceiptSHA256", " ".join(report["pending"]))

    def test_materialize_rejects_changed_ff_and_source_receipt_before_writing(self):
        fixture = self.materialize_fixture()
        path = fixture.build / "mod.ff"
        original = path.read_bytes()
        path.write_bytes(b"changed")
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        self.assertIn("FF differs from measured build", " ".join(report["errors"]))
        self.assertFalse(fixture.output.exists())
        path.write_bytes(original)
        fixture.state["Plan"]["SourceReceiptSHA256"] = "0" * 64
        fixture.save_state()
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        self.assertIn("SourceReceiptSHA256 differs", " ".join(report["errors"]))
        self.assertFalse(fixture.output.exists())

    def test_materialize_rejects_unclosed_or_unrestored_build(self):
        fixture = self.materialize_fixture()
        fixture.state["Phases"][0]["JobActiveAtClose"] = 1
        fixture.save_state()
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        self.assertIn("job remains active", " ".join(report["errors"]))
        fixture.state["Phases"][0]["JobActiveAtClose"] = 0
        fixture.state["Restored"] = False
        fixture.save_state()
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        self.assertIn("Build gate not established: Restored", " ".join(report["errors"]))

    def test_materialize_requires_existing_build_and_fresh_separate_destination(self):
        fixture = self.materialize_fixture()
        for output in (fixture.project / "nested", fixture.build / "nested", fixture.root, fixture.root / "missing-parent/candidate"):
            fixture.output = output
            code, report = self.invoke_materialize(fixture)
            self.assertEqual(code, 1, report)
        fixture.output = fixture.root / "candidate"
        fixture.output.mkdir()
        (fixture.output / "owner.txt").write_text("preserve")
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        self.assertEqual((fixture.output / "owner.txt").read_text(), "preserve")

    def test_materialize_refuses_missing_build_and_missing_explicit_action_inputs(self):
        fixture = self.materialize_fixture()
        fixture.build = fixture.root / "missing-build"
        code, report = self.invoke_materialize(fixture)
        self.assertEqual(code, 1, report)
        for options in (("-Action", "Materialize"), ("-Action", "Materialize", "-Adapter", "BeaconV1"),
                        ("-Action", "Materialize", "-Adapter", "BeaconSelfContainedV1")):
            code, report = self.invoke(*options)
            self.assertEqual(code, 1, report)
            self.assertIn("Materialize requires BeaconV1", " ".join(report["errors"]))

    def test_materialize_forbids_compilation_zip_and_gsc_audit_arguments(self):
        fixture = self.materialize_fixture()
        for field in ("-BuildParameters", "-Output", "-GscAuditEvidence"):
            code, report = self.invoke_materialize(fixture, field, str(fixture.root / "unused"))
            self.assertEqual(code, 1, report)
            self.assertFalse(fixture.output.exists())

    def test_materialize_preserves_recipient_pair_and_proof_validation(self):
        fixture = self.materialize_fixture()
        proof = fixture.root / "recipient.json"
        proof.write_text('{}')
        code, report = self.invoke_materialize(fixture, "-RecipientProof", str(proof))
        self.assertEqual(code, 1, report)
        self.assertIn("must be supplied together", " ".join(report["errors"]))
        code, report = self.invoke_materialize(fixture, "-RecipientProof", str(proof), "-RecipientRoot", str(fixture.root))
        self.assertEqual(code, 1, report)
        self.assertIn("snapshot-only recipient evidence", " ".join(report["errors"]))
        self.assertFalse(fixture.output.exists())

    def test_materialize_preserves_active_project_compatibility_gate(self):
        fixture = self.materialize_fixture()
        code, report = self.invoke_materialize(fixture, "-ActiveProject", str(self.project))
        self.assertEqual(code, 1, report)
        self.assertIn("Namespace collision", " ".join(report["errors"]))
        self.assertFalse(fixture.output.exists())

    def test_build_root_cannot_change_plan_or_build_actions(self):
        for action in ("Plan", "Build"):
            code, report = self.invoke("-Action", action, "-Adapter", "BeaconV1", "-BuildRoot", str(self.root / "unused"))
            self.assertEqual(code, 1, report)
            self.assertIn("BuildRoot is reserved", " ".join(report["errors"]))

    def materialize_tools(self):
        tools, _ = self.flow_fixture()
        for relative in ("sdk/modding/creator_materialize.py", "sdk/modding/Finalize-BeaconProject.py",
                         "sdk/modding/examples/beacon/manifest.json", "sdk/modding/examples/beacon/zone.csv"):
            (tools / relative).write_bytes((TOOLS / relative).read_bytes())
        (tools / "sdk/modding/Build-BeaconFF.ps1").write_text("throw 'MATERIALIZE MUST NOT CALL BUILDER'\n")
        return tools

    def test_materialize_does_not_even_call_builder_planning(self):
        fixture = self.materialize_fixture()
        tools = self.materialize_tools()
        code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
        self.assertEqual(code, 0, report)
        self.assertTrue(report["materialized"])
        self.assertFalse(report["build_executed"])

    def test_materialize_does_not_trust_positive_boolean_without_actual_candidate(self):
        fixture = self.materialize_fixture()
        tools = self.materialize_tools()
        path = tools / "sdk/modding/Finalize-BeaconProject.py"
        path.write_text(path.read_text() + "\n" + textwrap.dedent('''\
            # Intentional broken finalizer double: reports success but writes nothing.
            def finalize(*args, **kwargs):
                return {'api':'beacon-finalize/1','materialized':True,'closure_complete':False,
                        'package_ready':False,'runtime_ready':False}
            '''))
        code, report = self.invoke_materialize(fixture, tools=tools)
        self.assertEqual(code, 1, report)
        self.assertFalse(report["materialized"])
        self.assertFalse(fixture.output.exists())

    def test_materialize_rechecks_created_payload_hash_before_success(self):
        fixture = self.materialize_fixture()
        tools = self.materialize_tools()
        path = tools / "sdk/modding/Finalize-BeaconProject.py"
        path.write_text(path.read_text() + "\n" + textwrap.dedent('''\
            # Intentional drift after the real finalizer wrote its candidate.
            original_finalize = finalize
            def finalize(*args, **kwargs):
                result = original_finalize(*args, **kwargs)
                file = Path(result['candidate_root']) / 'mod.ff'
                data = file.read_bytes()
                file.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
                return result
            '''))
        code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
        self.assertEqual(code, 1, report)
        self.assertFalse(report["materialized"])
        self.assertIn("candidate hash differs: ff", " ".join(report["errors"]))
        self.assertTrue(fixture.output.exists(), "Preserve the changed candidate for inspection; never delete external replacements")

    def materialize_post_write_tools(self, mutation):
        tools = self.materialize_tools()
        path = tools / "sdk/modding/Finalize-BeaconProject.py"
        path.write_text(path.read_text() + "\n" + textwrap.dedent('''\
            # Fault injection only after the real finalizer has written all files.
            original_finalize = finalize
            def finalize(*args, **kwargs):
                result = original_finalize(*args, **kwargs)
                root = Path(result['candidate_root'])
            ''') + textwrap.indent(textwrap.dedent(mutation).strip() + "\n", "    ") + "    return result\n")
        return tools

    def test_materialize_rejects_same_size_corruption_of_each_serialized_node(self):
        for relative in ("xmodel/paris_model_probe.xmb", "xsurface/paris_model_probe_lod0.xsb",
                         "netconststrings/ncs_mdl_paris_model_probe.json", "sdk_beacon"):
            with self.subTest(node=relative):
                fixture = self.materialize_fixture()
                tools = self.materialize_post_write_tools(f'''\
                    file = root / 'evidence/serialized-nodes' / {relative!r}
                    raw = file.read_bytes()
                    file.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                    assert file.stat().st_size == len(raw)
                    ''')
                code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
                self.assertEqual(code, 1, report)
                self.assertFalse(report["materialized"])
                self.assertIn("node representation differs", " ".join(report["errors"]))
                self.assertTrue(fixture.output.exists())

    def test_materialize_rejects_changed_node_mapping_and_metadata(self):
        for field, mutation, message in (
                ("id", "nodes[0]['id'] = nodes[1]['id']", "node representation identities differ"),
                ("path", "nodes[0]['path'] = nodes[0]['path'][:-1] + 'z'", "node representation differs"),
                ("bytes", "nodes[0]['bytes'] += 1", "node representation differs"),
                ("sha256", "nodes[0]['sha256'] = '0' * 64", "node representation differs")):
            with self.subTest(field=field):
                fixture = self.materialize_fixture()
                tools = self.materialize_post_write_tools(f'''\
                    file = root / 'finalization.json'
                    original = file.read_bytes()
                    evidence = decoded(original)
                    nodes = evidence['node_representations']
                    {mutation}
                    changed = encoded(evidence)
                    file.write_bytes(changed)
                    result['bytes_written'] += len(changed) - len(original)
                    ''')
                code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
                self.assertEqual(code, 1, report)
                self.assertFalse(report["materialized"])
                self.assertIn(message, " ".join(report["errors"]))

    def test_materialize_checks_manifest_even_when_node_receipt_matches_corrupted_bytes(self):
        fixture = self.materialize_fixture()
        tools = self.materialize_post_write_tools('''\
            receipt = root / 'finalization.json'
            original = receipt.read_bytes()
            evidence = decoded(original)
            node = evidence['node_representations'][0]
            file = root / node['path']
            raw = file.read_bytes()
            changed = raw[:-1] + bytes([raw[-1] ^ 1])
            file.write_bytes(changed)
            node['sha256'] = sha(changed)
            receipt.write_bytes(encoded(evidence))
            assert receipt.stat().st_size == len(original)
            ''')
        code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
        self.assertEqual(code, 1, report)
        self.assertFalse(report["materialized"])
        self.assertIn("node closure hash differs", " ".join(report["errors"]))

    def test_materialize_recomputes_both_validation_reports(self):
        for stage in ("plan", "package"):
            with self.subTest(stage=stage):
                fixture = self.materialize_fixture()
                tools = self.materialize_post_write_tools(f'''\
                    file = root / 'validation-{stage}.json'
                    original = file.read_bytes()
                    validation = decoded(original)
                    validation['schema'] = 'x' + validation['schema'][1:]
                    file.write_bytes(encoded(validation))
                    assert file.stat().st_size == len(original)
                    ''')
                code, report = self.invoke_materialize(fixture, tools=tools, mutates=True)
                self.assertEqual(code, 1, report)
                self.assertFalse(report["materialized"])
                self.assertIn("validation report differs: " + stage, " ".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
