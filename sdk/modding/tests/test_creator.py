"""Real Creator CLI tests using existing Python gates; no native adapter executes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest
import zipfile

SDK = Path(__file__).resolve().parents[1]
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

    def invoke(self, *extra, environment=True, mutates=False, tools=TOOLS):
        before = self.snapshot()
        args = [PWSH, "-NoProfile", "-File", str(SDK / "Creator.ps1"), "-Project", str(self.project),
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


if __name__ == "__main__":
    unittest.main()
