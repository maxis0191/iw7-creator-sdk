"""Synthetic records only. Never starts native tools or touches retail stock."""
import copy
import csv
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
from unittest import mock
import zlib

DIRECTORY = Path(__file__).resolve().parents[1] / "recipient"
SPEC = importlib.util.spec_from_file_location("recipient_run_binding_test", DIRECTORY / "bind_run.py")
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)
v = b.v


def csv_data(header, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode()


class RunBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="recipient-run-binding-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "run"
        self.work = self.root / "work"
        self.work.mkdir(parents=True)
        self.tool_bytes = b"synthetic tool; never executable"
        patch = mock.patch.object(v, "EXE_SHA", v.sha(self.tool_bytes))
        patch.start()
        self.addCleanup(patch.stop)
        self.make_fixture()

    def write(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return v.sha(data)

    def json(self, path, value):
        return self.write(path, json.dumps(value, indent=2).encode())

    def make_fixture(self, script=False):
        source = self.base / "producer"
        python = self.base / "python.exe"
        candidate_root = self.base / "candidate"
        tool = candidate_root / "bin/zonetool-community.exe"
        self.write(tool, self.tool_bytes)
        pins = {str(python): self.write(python, b"synthetic python; never executable")}
        providers = {}
        for name in b.PROVIDERS:
            path = self.base / "providers" / name
            providers[name] = {"Path": str(path), "SHA256": self.write(path, ("synthetic " + name).encode())}
        for name in b.PRODUCERS:
            path = source / name
            checksum = self.json(path, {k: x["SHA256"] for k, x in providers.items()}) if name == "provider-pins.json" else self.write(path, ("synthetic " + name).encode())
            pins[str(path)] = checksum
        requests = []
        for relative, name, data in zip(b.REQUESTS, ("recipient-material-requests.csv", "recipient-script-requests.txt"),
                                      ("".join(k + "," + n + "\n" for k, n in v.REFERENCES), v.MODULE + "\n")):
            path = source / name
            pins[str(path)] = self.write(path, data.encode())
            requests.append({"Relative": relative, "Source": str(path), "SHA256": pins[str(path)]})
        stock = []
        for directory in ("main", "zone"):
            for zone in ("techsets_cp_zmb", "cp_zmb"):
                stock.append({"Relative": directory + "/" + zone + ".ff", "Source": str(self.base / "stock" / directory / (zone + ".ff")),
                    "Mode": "HardLink", "Bytes": 17, "ModifiedUtc": "2026-10-12T00:00:00.0000000Z", "Attributes": 32,
                    "BaselineMode": "HardLink", "ExpectedSourceId": "12345678:0000000000000001", "ExpectedSHA256": "a" * 64})
        for name in ("build-artifact.local.json", "preparation.local.json", "result.local.json"):
            path = candidate_root / name
            pins[str(path)] = self.json(path, {"synthetic_record": name})
        self.spec_path = self.base / "spec.json"
        self.original_spec = {"RunRoot": str(self.root), "StockRoot": str(self.base / "stock"), "CandidateRoot": str(candidate_root),
            "CandidateArtifactSHA256": pins[str(candidate_root / "build-artifact.local.json")], "PythonExe": str(python), "PythonExeSHA256": pins[str(python)],
            "RequestRoot": str(source), "MaterialRequestSHA256": requests[0]["SHA256"], "ScriptRequestSHA256": requests[1]["SHA256"]}
        for field in ("StockReceipt", "StockBindingReceipt", "ReviewedStockManifest"):
            path = self.base / (field + ".json")
            pins[str(path)] = self.json(path, {"synthetic_record": field})
            self.original_spec[field] = str(path)
            self.original_spec[field + "SHA256"] = pins[str(path)]
        pins[str(self.spec_path)] = self.json(self.spec_path, self.original_spec)
        self.plan = {"Schema": "iw7.recipient-closure-plan/1", "RunRoot": str(self.root), "Work": str(self.work), "StockInputs": stock,
            "SourceZoneOrder": ["techsets_cp_zmb", "cp_zmb"], "Candidate": {"Path": str(tool), "SHA256": v.EXE_SHA,
            "ArtifactSHA256": self.original_spec["CandidateArtifactSHA256"]},
            "Requests": requests, "SourceHashes": pins, "ProviderBindings": providers, "PythonExe": str(python), "PythonSHA256": pins[str(python)],
            "Adapter": str(source / "recipient_phase.py"), **b.PROFILE, "Phases": ["references", "script"] if script else ["references"],
            "NativeExecuted": False, "ClosureComplete": False, "Ready": False}
        inputs = copy.deepcopy(stock)
        for item in inputs:
            item.update(SourceId=item["ExpectedSourceId"], TargetId=item["ExpectedSourceId"])
        for relative, path in [("zonetool.exe", tool), *[(x["Relative"], Path(x["Source"])) for x in requests]]:
            inputs.append({"Relative": relative, "Source": str(path), "Bytes": path.stat().st_size, "Mode": "HardLink",
                "SourceId": "12345678:0000000000000002", "TargetId": "12345678:0000000000000002", "Attributes": 32,
                "ModifiedUtc": "2026-10-12T00:00:00.0000000Z"})
        transaction = {"Schema": "iw7.base-transaction/1", "GameRoot": str(self.work), "BackupRoot": str(self.root / "backup"),
            "ProfileDirectory": "unused", "ProfileDirectories": [], "DirectoryBefore": [], "ProfileBefore": [], "ProtectedFiles": [],
            "Files": [{"Path": x["Relative"], "Existed": False, "SHA256": None} for x in inputs], "Restored": True}
        self.state = {"Schema": "iw7.recipient-closure-run/1", "Work": str(self.work), "Inputs": inputs, "Plan": copy.deepcopy(self.plan),
            "Status": "ReferenceAndScriptObservationsVerified" if script else "ReferencesObservedScriptNotRun", "Phases": [], "Restored": True,
            "StockPreserved": True, "RestorationStatus": "Confirmed", "CleanupError": None, "RetainedLeaseToken": None,
            "MaxObservedBytes": 30000, "FinalObservedBytes": 30000, "NativeExecuted": True, "ReferencesVerified": True,
            "ScriptBytesVerified": script, "ClosureComplete": False, "Ready": False, "RuntimeVerified": False, "Transaction": transaction}
        # PowerShell keeps the same stock entry objects in Plan and Inputs.
        self.state["Plan"]["StockInputs"] = copy.deepcopy(inputs[:len(stock)])
        self.run_pins = {"backup/recovery.local.json": self.json(self.root / "backup/recovery.local.json", transaction)}
        for phase in self.plan["Phases"]:
            self.add_phase(phase)
        selected = "script" if script else "references"
        observation_path = self.root / ("analysis-" + selected + ".json")
        observation_sha = self.json(observation_path, v.verify_phase(self.work, self.root / selected / "phase.json"))
        plan_path = self.base / "reviewed-plan.json"
        self.expect = {"schema": "iw7.recipient-run-expectations/1", "run_root": str(self.root),
            "state_sha256": self.json(self.root / "state.local.json", self.state),
            "plan": {"path": str(plan_path), "sha256": self.json(plan_path, self.plan)},
            "spec_path": str(self.spec_path),
            "source_pins": copy.deepcopy(pins), "provider_pins": copy.deepcopy(providers), "run_files": self.run_pins,
            "observation": {"path": str(observation_path), "sha256": observation_sha, "phase": selected}}

    def add_phase(self, phase):
        stdout = b'Loading zone "techsets_cp_zmb"...\nLoading zone "cp_zmb"...\n'
        if phase == "references":
            name = "enemy-catalog/sdk_beacon_recipient_a.csv"
            raw = csv_data(["type", "name", "status"], [[*row, "verified"] for row in v.REFERENCES])
            observation = {"verified_references": 4, "serialized_content_observed": False}
        else:
            name = "dump/" + v.PACK + "/scriptfile-manifest.csv"
            stack, code = b"synthetic string, not an import inventory", b"synthetic bytecode"
            compressed = zlib.compress(stack)
            script = v.MODULE.encode() + b"\0" + struct.pack("<iii", len(compressed), len(stack), len(code)) + compressed + code
            self.run_pins["work/" + v.SCRIPT_PATH] = self.write(self.work / v.SCRIPT_PATH, script)
            raw = csv_data(["donor_map", "pack_name", "module", "status", "path", "size_bytes", "sha256"],
                [["cp_zmb", v.PACK, v.MODULE, "dumped", v.SCRIPT_PATH, len(script), v.sha(script)]])
            observation = {"module": v.MODULE, "bytes": len(script), "sha256": v.sha(script), "compressed_len": len(compressed),
                "source_len": len(stack), "bytecode_len": len(code), "path": v.SCRIPT_PATH, "decompressed": False, "transitive_imports_verified": False}
        self.run_pins["work/" + name] = self.write(self.work / name, raw)
        observation.update(manifest_path=name, manifest_sha256=v.sha(raw), closure_complete=False, package_ready=False)
        receipt = {"schema": "iw7.recipient-phase-result/1", "phase": phase, "pid": 456, "exit_code": 0, "failure": None,
            "executable_sha256": v.EXE_SHA, "ownership": "outer original Windows job", "log_limit_each": v.LIMIT, "observation": observation,
            "capture": {"pipe_buffer_size": 0, "drain_threads_closed": True, "stdout_bytes_at_receipt": len(stdout),
                "stderr_bytes_at_receipt": 0, "tree_closure_verified": False}}
        spec = {"schema": "iw7.recipient-phase/1", "phase": phase, "exe": str(self.work / "zonetool.exe"), "sha256": v.EXE_SHA,
                "cwd": str(self.work), "logs": str(self.root / phase), "timeout": 240}
        for name, value in ((phase + ".json", spec), (phase + "/phase.json", receipt)):
            self.run_pins[name] = self.json(self.root / name, value)
        self.run_pins[phase + "/stdout.log"] = self.write(self.root / phase / "stdout.log", stdout)
        self.run_pins[phase + "/stderr.log"] = self.write(self.root / phase / "stderr.log", b"")
        self.state["Phases"].append({"Phase": phase, "PID": 123, "Image": self.plan["PythonExe"], "CreatedUtc": "2026-10-12T00:00:00.0000000Z",
            "Priority": 16384, "JobActiveAtClose": 0, "ExitCode": 0, "PostRootExitDrainSeconds": 5,
            "PostRootExitObservations": [{"PhaseSeconds": 20.0, "DrainSeconds": 0.0, "Active": 0, "RootExitCode": 0}],
            "ResourceRegistration": {"Registered": True, "Outcome": "Registered", "Attempts": 1},
            "ObservedSourceZoneOrder": list(self.plan["SourceZoneOrder"]), "Result": receipt})

    def save_state(self):
        self.expect["state_sha256"] = self.json(self.root / "state.local.json", self.state)

    def repin(self, name, data):
        self.run_pins[name] = self.write(self.root / name, data)

    def overlay_fixture(self, named=False, five=False, complete=False):
        """Metadata only; none of the declared retail sources exist."""
        if five or complete:
            named = True
        stock_root = Path(self.original_spec["StockRoot"])
        observation, history, rows = [], [], {}
        relatives = ["main/techsets_cp_zmb.ff", "main/cp_zmb.ff", "zone/techsets_cp_zmb.ff", "zone/cp_zmb.ff"]
        relatives += [f"fixture{n}.bin" for n in range(67)] + ["main/fileSysCheck.cfg"]
        if complete:
            relatives[4] = "zone/assetfile1.pak"
        for index, relative in enumerate(relatives):
            reviewed_name = relative.split("/")[-1] if relative.endswith(".ff") or relative == "zone/assetfile1.pak" else relative
            size = 77 if index == 71 else (17 if index < 4 else 100 + index)
            checksum = v.sha(reviewed_name.encode())
            if relative == "zone/assetfile1.pak":
                _, size, checksum = b.BASE_PAK
            mode = "HardLink" if index < 63 else "Copy"
            entry = {"Relative": relative, "Source": str(stock_root / reviewed_name), "Mode": mode, "Bytes": size,
                "ModifiedUtc": "2026-09-29T21:46:02.6684337Z", "Attributes": 33 if index == 71 else 32,
                "SourceId": f"AAAAAAAA:{(index % 2 + 1) if index < 4 else index + 1:016X}", "SHA256": checksum,
                "ReviewedStockRelative": reviewed_name, "ExternalToolDependency": False}
            observation.append(entry)
            history.append({"Relative": relative, "Bytes": size, "Mode": mode})
            rows[reviewed_name] = {"RelativePath": reviewed_name, "Length": size, "SHA256": checksum, "Operation": "NTFSHardLinkImmutableStock"}
        self.overlay = {"Schema": "iw7.recipient-stock-observation/1", "Profile": b.OVERLAY_PROFILE, "ToolSource": b.TOOL_SOURCE,
            "StockRoot": str(stock_root), "ReviewedStockManifestSHA256": "0" * 64, "CapturedUtc": "2026-10-12T06:30:00.1234567Z",
            "ContentVerification": "DeferredUntilAdmittedRun", "Inputs": []}
        if five:
            self.overlay.update(Schema="iw7.recipient-stock-observation/2", Profile=b.FIVE_PROFILE,
                                AdditionalDependencyEvidenceSHA256=b.E2_FATAL_SHA.upper())
        if complete:
            self.overlay.update(Schema="iw7.recipient-stock-observation/3", Profile=b.COMPLETE_PROFILE,
                                AdditionalDependencyEvidenceSHA256=b.F_FATAL_SHA.upper())
        for index, (name, size, checksum) in enumerate(b.COMPLETE_PAKS if complete else b.FIVE_PAKS if five else b.PAKS):
            self.overlay["Inputs"].append({"Relative": "zone/" + name, "Source": str(stock_root / name), "Mode": "HardLink",
                "Bytes": size, "ModifiedUtc": "2026-09-29T21:46:02.6684337Z", "Attributes": 32,
                "SourceId": f"BBBBBBBB:{index + 1:016X}", "SHA256": checksum, "ReviewedStockRelative": name})
            rows[name] = {"RelativePath": name, "Length": size, "SHA256": checksum, "Operation": "NTFSHardLinkImmutableStock"}
        self.reviewed = list(rows.values())
        reviewed_sha = self.json(self.original_spec["ReviewedStockManifest"], self.reviewed)
        self.baseline = {"Schema": "iw7.model-ff-build/1", "Restored": True, "StockPreserved": True, "RetainedLeaseToken": None, "Inputs": history}
        baseline_sha = self.json(self.original_spec["StockReceipt"], self.baseline)
        for field, checksum in (("BASELINE_SHA", baseline_sha), ("REVIEWED_SHA", reviewed_sha)):
            patch = mock.patch.object(b, field, checksum)
            patch.start()
            self.addCleanup(patch.stop)
        self.baseline_observation = {"Schema": "iw7.ff-stock-observation/1", "CapturedUtc": "2026-10-12T06:30:00Z", "StockRoot": str(stock_root),
            "BaselineReceiptSHA256": baseline_sha, "ReviewedStockManifestSHA256": reviewed_sha, "Inputs": observation}
        self.overlay["ReviewedStockManifestSHA256"] = reviewed_sha
        if complete:
            base_entry = next(x for x in observation if x["Relative"] == "zone/assetfile1.pak")
            entries = [{"Name": x["ReviewedStockRelative"], "Family": "assetfile", "Bytes": x["Bytes"],
                        "SourceId": x["SourceId"], "ModifiedUtc": x["ModifiedUtc"], "Attributes": x["Attributes"],
                        "ReviewedSHA256": x["SHA256"], "ContentVerified": False} for x in [base_entry, *self.overlay["Inputs"]]]
            entries += [{"Name": f"imagefile{n}.pak", "Family": "imagefile", "Bytes": 1, "SourceId": f"DDDDDDDD:{n:016X}",
                         "ModifiedUtc": "2026-09-29T00:00:00Z", "Attributes": 32, "ReviewedSHA256": "f" * 64,
                         "ContentVerified": False} for n in range(1, 50)]
            self.inventory = {"Schema": "iw7.recipient-pak-inventory-proposal/1", "StockRoot": str(stock_root),
                              "ReviewedManifest": self.original_spec["ReviewedStockManifest"], "ReviewedManifestSHA256": reviewed_sha,
                              "CapturedUtc": "2026-10-12T07:36:04.2604339Z", "Purpose": "Synthetic metadata only",
                              "DirectoryScope": "Direct root children", "RetailPayloadBytesRead": 0, "InventoryElapsedSeconds": 0,
                              "Summary": {}, "MissingReviewedFiles": [], "UnsafeAttributes": 0, "ProposedAllAssetBudget": {}, "Files": entries}
            path = self.base / "complete-inventory.json"
            checksum = self.json(path, self.inventory)
            patch = mock.patch.object(b, "INVENTORY_SHA", checksum)
            patch.start()
            self.addCleanup(patch.stop)
            self.original_spec.update(RecipientCompleteInventoryReceipt=str(path), RecipientCompleteInventoryReceiptSHA256=checksum)
            self.plan["SourceHashes"][str(path)] = checksum
            self.overlay["CompleteInventoryEvidenceSHA256"] = checksum
        self.original_spec["RecipientStockBindingReceipt"] = str(self.base / "overlay.json")
        for field, obj in (("StockReceipt", self.baseline), ("StockBindingReceipt", self.baseline_observation),
                           ("ReviewedStockManifest", self.reviewed), ("RecipientStockBindingReceipt", self.overlay)):
            path = self.original_spec[field]
            checksum = self.json(path, obj)
            self.original_spec[field + "SHA256"] = checksum
            self.plan["SourceHashes"][path] = checksum
        for name in b.OVERLAY_PRODUCERS:
            path = Path(self.plan["Adapter"]).parent / name
            self.plan["SourceHashes"][str(path)] = self.write(path, ("synthetic " + name).encode())
        base_inputs = [b.stock_descriptor(entry) for entry in observation]
        extras = [b.stock_descriptor(entry, supplemental=True) for entry in self.overlay["Inputs"]]
        if named:
            for entry in extras:
                entry["StockProfileId"] = self.overlay["Profile"]
        self.plan["StockInputs"] = base_inputs + extras
        self.plan["StockBudget"] = b.stock_budget(base_inputs, extras, self.overlay["Profile"] if named else None)
        self.plan.update(FatalTextDiagnostic=False, **b.DIAGNOSTIC_LIMITS)
        self.state["DiagnosticOnly"] = False
        inputs = copy.deepcopy(self.plan["StockInputs"])
        for item in inputs:
            item.update(SourceId=item["ExpectedSourceId"], TargetId=item["ExpectedSourceId"] if item["Mode"] == "HardLink" else "CCCCCCCC:0000000000000001")
        self.state["Inputs"] = inputs + self.state["Inputs"][-3:]
        self.state["Transaction"]["Files"] = [{"Path": x["Relative"], "Existed": False, "SHA256": None} for x in self.state["Inputs"]]
        self.run_pins["backup/recovery.local.json"] = self.json(self.root / "backup/recovery.local.json", self.state["Transaction"])
        self.sync_overlay()

    def sync_overlay(self):
        self.plan["SourceHashes"][str(self.spec_path)] = self.json(self.spec_path, self.original_spec)
        self.expect["source_pins"] = copy.deepcopy(self.plan["SourceHashes"])
        self.expect["plan"]["sha256"] = self.json(self.expect["plan"]["path"], self.plan)
        self.state["Plan"] = copy.deepcopy(self.plan)
        for entry, staged in zip(self.state["Plan"]["StockInputs"], self.state["Inputs"]):
            entry.update(SourceId=staged["SourceId"], TargetId=staged["TargetId"])
        self.save_state()

    def repin_stock_receipt(self, field, value):
        path = self.original_spec[field]
        checksum = self.json(path, value)
        self.original_spec[field + "SHA256"] = checksum
        self.plan["SourceHashes"][path] = checksum
        self.sync_overlay()

    def test_references_only_binds_bytes_without_script_or_graph_claim(self):
        report = b.bind_run(self.expect)
        self.assertTrue(report["closed_run_record_bound"])
        self.assertTrue(report["temporary_inputs_absent_now"])
        self.assertEqual(list(report["phases"]), ["references"])
        self.assertFalse(report["phases"]["references"]["analysis"]["content_identity_measured"])
        for field in ("native_execution_authenticated", "stock_content_remeasured", "argv_observed", "imports_analyzed",
                      "dependency_graph_complete", "closure_complete", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertIs(report[field], False)
        self.assertEqual(report["actions_reconstructed_from_pinned_contract"]["references"][4], "-enemy-reference-check")

    def test_two_phase_script_bytes_still_have_no_import_inventory(self):
        self.make_fixture(script=True)
        report = b.bind_run(self.expect)
        self.assertTrue(report["phases"]["script"]["analysis"]["stack_integrity_verified"])
        self.assertFalse(report["phases"]["script"]["analysis"]["imports_analyzed"])
        self.assertFalse(report["dependency_graph_complete"])

    def test_independent_state_hash_rejects_modified_metadata(self):
        self.state["Ready"] = True
        self.json(self.root / "state.local.json", self.state)
        with self.assertRaisesRegex(ValueError, "Independent file SHA-256"):
            b.bind_run(self.expect)

    def test_plan_root_work_and_phase_paths_cannot_mix_runs(self):
        for key in ("RunRoot", "Work"):
            with self.subTest(key=key):
                original = self.state["Plan"][key]
                self.state["Plan"][key] = str(self.base / "other")
                self.save_state()
                with self.assertRaisesRegex(ValueError, "reviewed plan"):
                    b.bind_run(self.expect)
                self.state["Plan"][key] = original
        self.save_state()
        spec = json.loads((self.root / "references.json").read_bytes())
        for key in ("exe", "cwd", "logs"):
            with self.subTest(key=key):
                changed = dict(spec, **{key: str(self.base / "other")})
                self.run_pins["references.json"] = self.json(self.root / "references.json", changed)
                with self.assertRaisesRegex(ValueError, "Phase spec .* path differs"):
                    b.bind_run(self.expect)

    def test_traversal_and_symlink_run_output_refused(self):
        self.expect["run_files"]["../outside"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "retained file pin set"):
            b.bind_run(self.expect)
        del self.expect["run_files"]["../outside"]
        real = Path.lstat
        target = self.root / "references" / "stdout.log"
        def redirected(path, *args, **kwargs):
            actual = real(path, *args, **kwargs)
            if Path(path) == target:
                return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
            return actual
        with mock.patch.object(Path, "lstat", redirected), self.assertRaisesRegex(ValueError, "Redirected"):
            b.bind_run(self.expect)

    def test_missing_log_output_or_pin_refused(self):
        for name in ("references/stdout.log", "work/enemy-catalog/sdk_beacon_recipient_a.csv"):
            path = self.root / name
            raw = path.read_bytes()
            path.unlink()
            with self.subTest(name=name), self.assertRaises(OSError):
                b.bind_run(self.expect)
            path.write_bytes(raw)
        del self.run_pins["references/stderr.log"]
        with self.assertRaises(ValueError):
            b.bind_run(self.expect)

    def test_stdout_zone_order_error_and_capture_count_checked_from_bytes(self):
        for raw in (b'Loading zone "cp_zmb"...\n', b'[ FATAL ] unknown\n',
                    b'Loading zone "techsets_cp_zmb"...\nLoading zone "cp_zmb"...\nextra\n'):
            with self.subTest(raw=raw):
                self.repin("references/stdout.log", raw)
                with self.assertRaises(ValueError):
                    b.bind_run(self.expect)

    def test_nested_receipt_and_external_report_cannot_be_declarations(self):
        self.state["Phases"][0]["Result"]["pid"] = 999
        self.save_state()
        with self.assertRaisesRegex(ValueError, "Nested phase receipt"):
            b.bind_run(self.expect)
        self.state["Phases"][0]["Result"]["pid"] = 456
        self.save_state()
        path = Path(self.expect["observation"]["path"])
        for value in ({"phase_bytes_verified": True}, {**json.loads(path.read_bytes()), "native_authenticated": True}):
            self.expect["observation"]["sha256"] = self.json(path, value)
            with self.assertRaisesRegex(ValueError, "External observation"):
                b.bind_run(self.expect)

    def test_refs_success_flags_do_not_substitute_for_original_job_closure(self):
        original = copy.deepcopy(self.state["Phases"][0])
        variants = [("JobActiveAtClose", 1), ("ExitCode", 2), ("PID", True), ("CreatedUtc", ""),
                    ("PostRootExitObservations", []), ("PostRootExitObservations", [{"PhaseSeconds": 20, "DrainSeconds": 0, "Active": 1, "RootExitCode": 0}])]
        for key, value in variants:
            with self.subTest(key=key):
                self.state["Phases"][0] = {**copy.deepcopy(original), key: value}
                self.save_state()
                with self.assertRaises(ValueError):
                    b.bind_run(self.expect)

    def test_short_phase_closed_before_registration_is_not_fabricated_registration(self):
        self.state["Phases"][0]["ResourceRegistration"] = {"Registered": False, "Outcome": "ClosedBeforeRegistration", "Attempts": 0}
        self.save_state()
        self.assertTrue(b.bind_run(self.expect)["closed_run_record_bound"])
        self.state["Phases"][0]["PostRootExitObservations"] = []
        self.save_state()
        with self.assertRaises(ValueError):
            b.bind_run(self.expect)

    def test_failed_or_unrestored_run_cannot_bind_positive_observation(self):
        original = copy.deepcopy(self.state)
        for key, value in (("Status", "Failed"), ("Restored", False), ("RetainedLeaseToken", "held"), ("ScriptBytesVerified", True),
                           ("Failure", "timeout"), ("CleanupError", "restore failed"), ("Ready", True)):
            with self.subTest(key=key):
                self.state = {**copy.deepcopy(original), key: value}
                self.save_state()
                with self.assertRaises(ValueError):
                    b.bind_run(self.expect)

    def test_restoration_recovery_record_and_actual_absence_are_both_required(self):
        self.write(self.work / "zonetool.exe", self.tool_bytes)
        with self.assertRaisesRegex(ValueError, "still exists"):
            b.bind_run(self.expect)
        (self.work / "zonetool.exe").unlink()
        tx = copy.deepcopy(self.state["Transaction"])
        tx["Restored"] = False
        self.run_pins["backup/recovery.local.json"] = self.json(self.root / "backup/recovery.local.json", tx)
        with self.assertRaisesRegex(ValueError, "Restoration transaction"):
            b.bind_run(self.expect)

    def test_tool_provider_request_and_python_are_rehashed(self):
        paths = [self.plan["Candidate"]["Path"], self.plan["PythonExe"], self.plan["Adapter"], self.plan["Requests"][0]["Source"],
                 next(iter(self.plan["ProviderBindings"].values()))["Path"]]
        for name in paths:
            path = Path(name)
            raw = path.read_bytes()
            self.write(path, raw + b"modified")
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, "SHA-256"):
                b.bind_run(self.expect)
            self.write(path, raw)

    def test_state_pins_cannot_self_authorize_producer_change(self):
        path = self.plan["Adapter"]
        self.state["Plan"]["SourceHashes"][path] = self.write(path, b"changed producer")
        self.save_state()
        with self.assertRaisesRegex(ValueError, "reviewed plan"):
            b.bind_run(self.expect)

    def test_changed_input_request_even_if_repinned_is_not_expected_action(self):
        path = self.plan["Requests"][0]["Source"]
        checksum = self.write(path, b"material,other\n")
        self.plan["Requests"][0]["SHA256"] = checksum
        self.plan["SourceHashes"][path] = checksum
        self.original_spec["MaterialRequestSHA256"] = checksum
        self.plan["SourceHashes"][str(self.spec_path)] = self.json(self.spec_path, self.original_spec)
        self.state["Plan"] = copy.deepcopy(self.plan)
        self.expect["source_pins"][path] = checksum
        self.expect["source_pins"][str(self.spec_path)] = self.plan["SourceHashes"][str(self.spec_path)]
        self.expect["plan"]["sha256"] = self.json(self.expect["plan"]["path"], self.plan)
        self.save_state()
        with self.assertRaisesRegex(ValueError, "Exact native request"):
            b.bind_run(self.expect)

    def test_script_observation_cannot_be_selected_for_refs_only_run(self):
        self.expect["observation"]["phase"] = "script"
        with self.assertRaisesRegex(ValueError, "not run"):
            b.bind_run(self.expect)

    def test_group_recheck_rejects_same_length_content_replacement(self):
        real_verify = v.verify_phase
        path = self.root / "references/stdout.log"
        def replace_after_read(*args):
            result = real_verify(*args)
            before = path.stat()
            raw = path.read_bytes()
            path.write_bytes(raw.replace(b"cp_zmb", b"cp_bad"))
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            return result
        with mock.patch.object(v, "verify_phase", replace_after_read), self.assertRaisesRegex(ValueError, "SHA-256"):
            b.bind_run(self.expect)

    def test_absence_is_rechecked_after_output_analysis(self):
        real_verify = v.verify_phase
        def reappear(*args):
            result = real_verify(*args)
            self.write(self.work / "zonetool.exe", self.tool_bytes)
            return result
        with mock.patch.object(v, "verify_phase", reappear), self.assertRaisesRegex(ValueError, "still exists"):
            b.bind_run(self.expect)

    def test_delayed_original_job_drain_is_bounded_and_ordered(self):
        phase = self.state["Phases"][0]
        phase["PostRootExitObservations"] = [
            {"PhaseSeconds": 20, "DrainSeconds": 0, "Active": 1, "RootExitCode": 0},
            {"PhaseSeconds": 20.1, "DrainSeconds": 0.1, "Active": 0, "RootExitCode": 0}]
        self.save_state()
        self.assertTrue(b.bind_run(self.expect)["closed_run_record_bound"])
        for key, value in (("PhaseSeconds", 246), ("DrainSeconds", 7), ("RootExitCode", False), ("Active", False)):
            original = copy.deepcopy(phase["PostRootExitObservations"])
            phase["PostRootExitObservations"][-1][key] = value
            self.save_state()
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)
            phase["PostRootExitObservations"] = original

    def test_phase_copied_between_references_and_script_is_rejected(self):
        self.make_fixture(script=True)
        raw = (self.root / "references/phase.json").read_bytes()
        self.repin("script/phase.json", raw)
        self.state["Phases"][1]["Result"] = json.loads(raw)
        self.save_state()
        # Even repinning a copied reference analysis cannot turn it into script evidence.
        self.expect["observation"]["sha256"] = self.json(self.expect["observation"]["path"], v.verify_phase(self.work, self.root / "script/phase.json"))
        with self.assertRaisesRegex(ValueError, "another phase"):
            b.bind_run(self.expect)

    def test_duplicate_json_fields_are_not_interpreted_as_last_writer_wins(self):
        raw = (self.root / "state.local.json").read_bytes()
        self.expect["state_sha256"] = self.write(self.root / "state.local.json", b'{"Ready":false,' + raw[1:])
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            b.bind_run(self.expect)

    def test_unbound_source_roles_are_rejected_even_in_repinned_plan(self):
        key = self.original_spec["StockBindingReceipt"]
        del self.expect["source_pins"][key]
        del self.plan["SourceHashes"][key]
        del self.state["Plan"]["SourceHashes"][key]
        self.expect["plan"]["sha256"] = self.json(self.expect["plan"]["path"], self.plan)
        self.save_state()
        with self.assertRaisesRegex(ValueError, "Original spec input pin absent"):
            b.bind_run(self.expect)

    def test_independent_provider_pins_cannot_be_replaced_by_plan_claims(self):
        first = next(iter(self.expect["provider_pins"]))
        self.expect["provider_pins"][first]["SHA256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Provider bindings"):
            b.bind_run(self.expect)

    def test_old_receipt_without_capture_diagnostic_can_still_bind_closed_run(self):
        del self.state["Phases"][0]["Result"]["capture"]
        self.run_pins["references/phase.json"] = self.json(self.root / "references/phase.json", self.state["Phases"][0]["Result"])
        self.save_state()
        self.expect["observation"]["sha256"] = self.json(self.expect["observation"]["path"], v.verify_phase(self.work, self.root / "references/phase.json"))
        self.assertTrue(b.bind_run(self.expect)["observation_bytes_bound"])

    def test_final_plan_cannot_disagree_with_shared_staged_stock_identity(self):
        self.state["Plan"]["StockInputs"][0]["SourceId"] = "12345678:0000000000000099"
        self.save_state()
        with self.assertRaisesRegex(ValueError, "Shared plan/input identity"):
            b.bind_run(self.expect)

    def test_overlay_binds_79_paths_and_receipt_budget_without_opening_retail(self):
        self.overlay_fixture()
        original_read = b.Reader.read
        stock_root = Path(self.original_spec["StockRoot"])
        def bounded_read(reader, path, *args, **kwargs):
            self.assertFalse(Path(path).is_relative_to(stock_root), "Retail files must not be opened")
            self.assertFalse(str(path).lower().endswith(".pak"))
            return original_read(reader, path, *args, **kwargs)
        with mock.patch.object(b.Reader, "read", bounded_read):
            report = b.bind_run(self.expect)
        self.assertEqual(len(self.state["Inputs"]), 79)
        binding = report["stock_profile_binding"]
        self.assertEqual(binding["profile"], b.OVERLAY_PROFILE)
        self.assertEqual([x["ExpectedSourceId"] for x in binding["supplemental_input_records"]],
                         [x["SourceId"] for x in self.overlay["Inputs"]])
        self.assertEqual(binding["budget_from_receipts"]["SupplementalLogicalBytes"], 580092048)
        self.assertEqual(binding["budget_from_receipts"]["SupplementalLimitBytes"], 600 * 1024**2)
        self.assertEqual(binding["budget_from_receipts"]["StockHardLinks"], 75)
        self.assertEqual(binding["budget_from_receipts"]["StockCopiedBytes"], 77)
        self.assertFalse(binding["content_remeasured"])
        self.assertFalse(report["closure_complete"])
        self.assertNotIn("script", report["phases"])

    def test_overlay_can_bind_two_phases_without_import_or_package_claim(self):
        self.make_fixture(script=True)
        self.overlay_fixture()
        result = b.bind_run(self.expect)
        self.assertEqual(set(result["phases"]), {"references", "script"})
        self.assertFalse(result["imports_analyzed"])
        self.assertFalse(result["package_ready"])

    def test_overlay_requires_complete_explicit_roles_and_reviewed_source_files(self):
        self.overlay_fixture()
        path = str(Path(self.plan["Adapter"]).parent / "Recipient.Stock.ps1")
        del self.plan["SourceHashes"][path]
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Incomplete explicit"):
            b.bind_run(self.expect)

    def test_overlay_does_not_accept_unknown_hash_role_or_missing_dialog_source(self):
        self.overlay_fixture()
        path = str(Path(self.plan["Adapter"]).parent / "recipient_dialog.py")
        checksum = self.plan["SourceHashes"].pop(path)
        self.plan["SourceHashes"][str(self.base / "unknown-source.py")] = checksum
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Exact source pin roles"):
            b.bind_run(self.expect)

    def test_overlay_receipt_profile_claims_and_order_are_strict(self):
        self.overlay_fixture()
        original = copy.deepcopy(self.overlay)
        for key, value in (("Schema", "future"), ("Profile", "all-paks"), ("ToolSource", "0" * 40),
                           ("ContentVerification", "Verified"), ("Ready", False), ("Restored", True),
                           ("Inputs", original["Inputs"][:3]), ("Inputs", list(reversed(original["Inputs"]))),
                           ("ReviewedStockManifestSHA256", "0" * 64), ("CapturedUtc", "invalid")):
            self.repin_stock_receipt("RecipientStockBindingReceipt", {**copy.deepcopy(original), key: value})
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                b.bind_run(self.expect)

    def test_overlay_entry_cannot_change_path_identity_hash_size_attributes_or_mode(self):
        self.overlay_fixture()
        original = copy.deepcopy(self.overlay)
        for key, value in (("Relative", "zone/../assetfile17.pak"), ("Source", str(self.base / "outside.pak")), ("SourceId", "unknown"),
                           ("SHA256", "0" * 64), ("Bytes", 104595491), ("Bytes", True), ("Mode", "Copy"), ("Attributes", 1),
                           ("Attributes", 16), ("Attributes", 1024), ("TargetId", "BBBBBBBB:0000000000000001"), ("ModifiedUtc", "invalid")):
            bad = copy.deepcopy(original)
            bad["Inputs"][0][key] = value
            self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_overlay_metadata_with_changed_identity_cannot_match_old_plan(self):
        self.overlay_fixture()
        bad = copy.deepcopy(self.overlay)
        bad["Inputs"][0]["SourceId"] = "BBBBBBBB:0000000000000099"
        self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
        with self.assertRaisesRegex(ValueError, "exact overlay descriptors"):
            b.bind_run(self.expect)

    def test_overlay_preserves_seventh_timestamp_digit(self):
        self.overlay_fixture()
        changed = copy.deepcopy(self.overlay)
        changed["Inputs"][0]["ModifiedUtc"] = "2026-09-29T21:46:02.6684338Z"
        self.repin_stock_receipt("RecipientStockBindingReceipt", changed)
        with self.assertRaisesRegex(ValueError, "exact overlay descriptors"):
            b.bind_run(self.expect)

    def test_overlay_requires_baseline_receipt_bytes_and_semantic_observation(self):
        self.overlay_fixture()
        original = copy.deepcopy(self.baseline_observation)
        for key, value in (("BaselineReceiptSHA256", "0" * 64), ("Restored", True), ("Inputs", original["Inputs"][:71]),
                           ("StockRoot", str(self.base / "other-stock"))):
            self.repin_stock_receipt("StockBindingReceipt", {**copy.deepcopy(original), key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)
        self.repin_stock_receipt("StockBindingReceipt", original)
        bad = copy.deepcopy(self.baseline)
        bad["Inputs"][0]["Mode"] = "Copy"
        self.repin_stock_receipt("StockReceipt", bad)
        with self.assertRaisesRegex(ValueError, "Reviewed baseline/manifest pins"):
            b.bind_run(self.expect)

    def test_overlay_budget_is_recomputed_not_promoted_from_declarations(self):
        self.overlay_fixture()
        original = copy.deepcopy(self.plan["StockBudget"])
        for key, value in (("SupplementalLimitBytes", 700 * 1024**2), ("SupplementalCopiedBytes", 1), ("UniqueHashReadFiles", 1),
                           ("UniqueHashReadBytes", 1), ("StockCopiedBytes", 0), ("ContentVerified", True),
                           ("AdditionalResidentBytesMeasured", True), ("SupplementalEntries", 5)):
            self.plan["StockBudget"] = {**original, key: value}
            self.sync_overlay()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "stock receipt budget"):
                b.bind_run(self.expect)

    def test_overlay_alias_size_hash_inconsistency_and_duplicate_baseline_are_rejected(self):
        self.overlay_fixture()
        bad = copy.deepcopy(self.baseline_observation)
        bad["Inputs"][4]["SourceId"] = bad["Inputs"][0]["SourceId"]
        self.repin_stock_receipt("StockBindingReceipt", bad)
        self.plan["StockInputs"][4]["ExpectedSourceId"] = bad["Inputs"][4]["SourceId"]
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Aliased stock identity"):
            b.bind_run(self.expect)
        bad["Inputs"][4] = copy.deepcopy(bad["Inputs"][0])
        self.repin_stock_receipt("StockBindingReceipt", bad)
        self.plan["StockInputs"][4] = copy.deepcopy(self.plan["StockInputs"][0])
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Duplicate stock target"):
            b.bind_run(self.expect)

    def test_overlay_diagnostic_and_unclosed_runs_remain_rejected(self):
        self.overlay_fixture()
        self.plan["FatalTextDiagnostic"] = True
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Diagnostic-only"):
            b.bind_run(self.expect)
        self.plan["FatalTextDiagnostic"] = False
        self.state["DiagnosticOnly"] = True
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Diagnostic-only"):
            b.bind_run(self.expect)
        self.state["DiagnosticOnly"] = False
        self.state["Phases"][0]["PostRootExitObservations"] = []
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "terminal observations"):
            b.bind_run(self.expect)

    def test_overlay_must_be_in_recovery_and_absent_after_restoration(self):
        self.overlay_fixture()
        self.write(self.work / "zone/assetfile17.pak", b"synthetic stale input")
        with self.assertRaisesRegex(ValueError, "still exists"):
            b.bind_run(self.expect)
        (self.work / "zone/assetfile17.pak").unlink()
        self.state["Transaction"]["Files"] = [x for x in self.state["Transaction"]["Files"] if x["Path"] != "zone/assetfile17.pak"]
        self.run_pins["backup/recovery.local.json"] = self.json(self.root / "backup/recovery.local.json", self.state["Transaction"])
        self.save_state()
        with self.assertRaisesRegex(ValueError, "restoration entries"):
            b.bind_run(self.expect)

    def test_named_four_pak_producer_preserves_original_receipt_schema_and_budget(self):
        self.overlay_fixture(named=True)
        result = b.bind_run(self.expect)["stock_profile_binding"]
        self.assertEqual(result["observation_schema"], "iw7.recipient-stock-observation/1")
        self.assertEqual(result["producer_contract"], "named-profile/1")
        self.assertEqual(result["budget_from_receipts"]["SupplementalProfile"], b.OVERLAY_PROFILE)
        self.assertEqual(result["budget_from_receipts"]["AdditionalBytesBeyondFourPAKs"], 0)
        self.assertEqual(result["budget_from_receipts"]["SupplementalLimitBytes"], 629145600)
        self.assertEqual(result["budget_from_receipts"]["SupplementalLogicalBytes"], 580092048)
        self.assertIsNone(result["additional_dependency_evidence_sha256"])

    def test_five_pak_binds_80_paths_without_opening_any_retail_source(self):
        self.overlay_fixture(five=True)
        original_read = b.Reader.read
        def metadata_only(reader, path, *args, **kwargs):
            self.assertFalse(Path(path).is_relative_to(Path(self.original_spec["StockRoot"])))
            self.assertFalse(str(path).lower().endswith(".pak"))
            return original_read(reader, path, *args, **kwargs)
        with mock.patch.object(b.Reader, "read", metadata_only):
            report = b.bind_run(self.expect)
        binding, budget = report["stock_profile_binding"], report["stock_profile_binding"]["budget_from_receipts"]
        self.assertEqual(binding["profile"], "observed-cp-paks-17-19-37-53-69")
        self.assertEqual(binding["observation_schema"], "iw7.recipient-stock-observation/2")
        self.assertEqual(binding["additional_dependency_evidence_sha256"], "867e858ecd4bffde50a04e62488e42b73f528177e0e01b51a081bc030dbbb280")
        self.assertEqual(len(self.state["Inputs"]), 80)
        self.assertEqual(budget["SupplementalLogicalBytes"], 966557876)
        self.assertEqual(budget["SupplementalLimitBytes"], 966557876)
        self.assertEqual(budget["AdditionalBytesBeyondFourPAKs"], 386465828)
        self.assertEqual(budget["SupplementalCopiedBytes"], 0)
        self.assertEqual(budget["UniqueHashReadBytes"], 966567166)  # Tiny synthetic baseline only.
        self.assertEqual(budget["UniqueHashReadFiles"], 75)
        self.assertEqual(budget["StockHardLinks"], 76)
        self.assertEqual(budget["StockCopiedBytes"], 77)
        for key in ("native_execution_authenticated", "stock_content_remeasured", "imports_analyzed",
                    "closure_complete", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertIs(report[key], False)

    def test_five_pak_both_phases_still_cannot_qualify_script_import_absence(self):
        self.make_fixture(script=True)
        self.overlay_fixture(five=True)
        report = b.bind_run(self.expect)
        self.assertEqual(set(report["phases"]), {"references", "script"})
        self.assertTrue(report["phases"]["script"]["analysis"]["stack_integrity_verified"])
        self.assertFalse(report["imports_analyzed"])
        self.assertFalse(report["dependency_graph_complete"])

    def test_five_pak_schema_evidence_order_and_count_are_exact(self):
        self.overlay_fixture(five=True)
        original = copy.deepcopy(self.overlay)
        changes = [("Schema", "iw7.recipient-stock-observation/1"), ("Profile", b.OVERLAY_PROFILE),
                   ("Profile", b.FIVE_PROFILE + "-70"), ("AdditionalDependencyEvidenceSHA256", None),
                   ("AdditionalDependencyEvidenceSHA256", "0" * 64), ("Inputs", original["Inputs"][:4]),
                   ("Inputs", original["Inputs"] + original["Inputs"][-1:]), ("Inputs", list(reversed(original["Inputs"])))]
        for key, value in changes:
            self.repin_stock_receipt("RecipientStockBindingReceipt", {**copy.deepcopy(original), key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                b.bind_run(self.expect)
        bad = copy.deepcopy(original)
        del bad["AdditionalDependencyEvidenceSHA256"]
        self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
        with self.assertRaisesRegex(ValueError, "fields differ"):
            b.bind_run(self.expect)

    def test_four_pak_receipt_cannot_silently_adopt_five_pak_schema_or_evidence(self):
        self.overlay_fixture(named=True)
        for key, value in (("Schema", "iw7.recipient-stock-observation/2"), ("AdditionalDependencyEvidenceSHA256", b.E2_FATAL_SHA)):
            self.repin_stock_receipt("RecipientStockBindingReceipt", {**self.overlay, key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_fifth_pak_names_hash_size_identity_and_writable_attributes_are_fixed(self):
        self.overlay_fixture(five=True)
        original = copy.deepcopy(self.overlay)
        for key, value in (("Relative", "zone/assetfile70.pak"), ("Source", str(self.base / "assetfile69.pak")),
                           ("Bytes", 386465827), ("Bytes", True), ("SHA256", "0" * 64), ("SourceId", "unknown"),
                           ("Mode", "Copy"), ("Attributes", 1), ("Attributes", 1024), ("ModifiedUtc", "invalid")):
            bad = copy.deepcopy(original)
            bad["Inputs"][4][key] = value
            self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_five_pak_budget_cannot_reuse_four_pak_ceiling_or_claim_content(self):
        self.overlay_fixture(five=True)
        original = copy.deepcopy(self.plan["StockBudget"])
        for key, value in (("SupplementalProfile", b.OVERLAY_PROFILE), ("AdditionalBytesBeyondFourPAKs", 0),
                           ("SupplementalLimitBytes", 629145600), ("SupplementalLimitBytes", 966557877),
                           ("SupplementalLogicalBytes", 580092048), ("SupplementalCopiedBytes", 1),
                           ("StockHardLinks", 75), ("ContentVerified", True), ("AdditionalResidentBytesMeasured", True)):
            self.plan["StockBudget"] = {**original, key: value}
            self.sync_overlay()
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_named_contract_rejects_missing_budget_fields_or_partial_input_ids(self):
        self.overlay_fixture(five=True)
        original_budget, original_inputs = copy.deepcopy(self.plan["StockBudget"]), copy.deepcopy(self.plan["StockInputs"])
        for field in ("SupplementalProfile", "AdditionalBytesBeyondFourPAKs", "one_input", "all_inputs", "legacy_shape"):
            self.plan["StockBudget"], self.plan["StockInputs"] = copy.deepcopy(original_budget), copy.deepcopy(original_inputs)
            if field in original_budget:
                del self.plan["StockBudget"][field]
            else:
                for entry in self.plan["StockInputs"][72:73 if field == "one_input" else 77]:
                    entry.pop("StockProfileId")
                if field == "legacy_shape":
                    self.plan["StockBudget"].pop("SupplementalProfile")
                    self.plan["StockBudget"].pop("AdditionalBytesBeyondFourPAKs")
            self.sync_overlay()
            with self.subTest(field=field), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_mixed_named_ids_are_rejected_even_with_repinned_staged_records(self):
        self.overlay_fixture(five=True)
        self.plan["StockInputs"][-1]["StockProfileId"] = b.OVERLAY_PROFILE
        self.state["Inputs"][76]["StockProfileId"] = b.OVERLAY_PROFILE
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "exact overlay descriptors"):
            b.bind_run(self.expect)
        with self.assertRaisesRegex(ValueError, "Mixed or incomplete"):
            b.stock_budget(self.plan["StockInputs"][:72], self.plan["StockInputs"][72:], b.FIVE_PROFILE)

    def test_five_pak_cannot_rebind_failed_e2_as_success(self):
        self.overlay_fixture(five=True)
        original = copy.deepcopy(self.state)
        for key, value in (("Status", "Failed"), ("Failure", "Could not find asset file assetfile69.pak"),
                           ("ReferencesVerified", False), ("CleanupError", "unresolved"), ("RetainedLeaseToken", "held")):
            self.state = {**copy.deepcopy(original), key: value}
            self.save_state()
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_fifth_pak_requires_original_job_closure_and_complete_restoration(self):
        self.overlay_fixture(five=True)
        original = copy.deepcopy(self.state)
        self.state["Phases"][0]["JobActiveAtClose"] = 1
        self.save_state()
        with self.assertRaisesRegex(ValueError, "JobActiveAtClose"):
            b.bind_run(self.expect)
        self.state = original
        self.save_state()
        self.write(self.work / "zone/assetfile69.pak", b"synthetic stale link")
        with self.assertRaisesRegex(ValueError, "still exists"):
            b.bind_run(self.expect)
        (self.work / "zone/assetfile69.pak").unlink()
        self.state["Transaction"]["Files"] = [x for x in self.state["Transaction"]["Files"] if x["Path"] != "zone/assetfile69.pak"]
        self.run_pins["backup/recovery.local.json"] = self.json(self.root / "backup/recovery.local.json", self.state["Transaction"])
        self.save_state()
        with self.assertRaisesRegex(ValueError, "restoration entries"):
            b.bind_run(self.expect)

    def test_complete_profile_binds_all_107_paths_with_zero_retail_reads(self):
        self.overlay_fixture(complete=True)
        original_read = b.Reader.read
        inventory_path = Path(self.original_spec["RecipientCompleteInventoryReceipt"])
        inventory_limits = []
        def metadata_only(reader, path, *args, **kwargs):
            self.assertFalse(Path(path).is_relative_to(Path(self.original_spec["StockRoot"])))
            self.assertFalse(str(path).lower().endswith(".pak"))
            if Path(path) == inventory_path:
                inventory_limits.append(kwargs.get("limit", v.LIMIT))
                self.assertLessEqual(kwargs.get("limit", v.LIMIT), 128 * 1024)
            return original_read(reader, path, *args, **kwargs)
        with mock.patch.object(b.Reader, "read", metadata_only):
            report = b.bind_run(self.expect)
        binding, budget = report["stock_profile_binding"], report["stock_profile_binding"]["budget_from_receipts"]
        self.assertEqual(binding["profile"], "doom-reviewed-all-asset-paks-20261012")
        self.assertEqual(binding["observation_schema"], "iw7.recipient-stock-observation/3")
        self.assertTrue(binding["complete_inventory_metadata_bound"])
        self.assertEqual(binding["complete_inventory_sha256"], b.INVENTORY_SHA)
        self.assertEqual(binding["additional_dependency_evidence_sha256"], "67995123ab95d54de3ddb9ffb0f52015daa0978f3c782c977a7c9a3a3c9f58f3")
        self.assertEqual(len(binding["supplemental_input_records"]), 32)
        self.assertEqual(len(self.state["Inputs"]), 107)
        self.assertEqual(budget["SupplementalLogicalBytes"], 4695508096)
        self.assertEqual(budget["SupplementalLimitBytes"], 4695508096)
        self.assertEqual(budget["AdditionalBytesBeyondFourPAKs"], 4115416048)
        self.assertEqual(budget["StockHardLinks"], 103)
        self.assertEqual(budget["StockCopiedBytes"], 77)
        self.assertEqual(budget["SupplementalCopiedBytes"], 0)
        self.assertGreaterEqual(len(inventory_limits), 3)
        for field in ("native_execution_authenticated", "stock_content_remeasured", "imports_analyzed", "dependency_graph_complete",
                      "closure_complete", "package_ready", "runtime_ready", "owner_accepted"):
            self.assertIs(report[field], False)

    def test_complete_profile_two_phases_does_not_claim_complete_imports(self):
        self.make_fixture(script=True)
        self.overlay_fixture(complete=True)
        result = b.bind_run(self.expect)
        self.assertTrue(result["phases"]["script"]["analysis"]["stack_integrity_verified"])
        self.assertFalse(result["imports_analyzed"])
        self.assertFalse(result["package_ready"])

    def test_complete_profile_rejects_mixed_schema_evidence_inventory_and_names(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.overlay)
        for key, value in (("Schema", "iw7.recipient-stock-observation/2"), ("Profile", b.FIVE_PROFILE),
                           ("AdditionalDependencyEvidenceSHA256", b.E2_FATAL_SHA), ("CompleteInventoryEvidenceSHA256", "0" * 64),
                           ("Inputs", original["Inputs"][:31]), ("Inputs", original["Inputs"] + original["Inputs"][-1:]),
                           ("Inputs", list(reversed(original["Inputs"])))):
            self.repin_stock_receipt("RecipientStockBindingReceipt", {**copy.deepcopy(original), key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)
        bad = copy.deepcopy(original)
        del bad["CompleteInventoryEvidenceSHA256"]
        self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
        with self.assertRaises(ValueError):
            b.bind_run(self.expect)

    def test_complete_inventory_requires_both_independent_spec_fields_and_source_pin(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.original_spec)
        for field in ("RecipientCompleteInventoryReceipt", "RecipientCompleteInventoryReceiptSHA256"):
            self.original_spec = copy.deepcopy(original)
            del self.original_spec[field]
            self.sync_overlay()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Incomplete complete inventory"):
                b.bind_run(self.expect)
        self.original_spec = original
        del self.plan["SourceHashes"][original["RecipientCompleteInventoryReceipt"]]
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "Original spec input pin absent"):
            b.bind_run(self.expect)

    def test_old_profiles_reject_complete_inventory_spec_and_observation_fields(self):
        self.overlay_fixture(five=True)
        self.repin_stock_receipt("RecipientStockBindingReceipt", {**self.overlay, "CompleteInventoryEvidenceSHA256": b.INVENTORY_SHA})
        with self.assertRaisesRegex(ValueError, "fields differ"):
            b.bind_run(self.expect)
        self.repin_stock_receipt("RecipientStockBindingReceipt", self.overlay)
        path = self.base / "irrelevant-inventory.json"
        checksum = self.json(path, {})
        self.original_spec.update(RecipientCompleteInventoryReceipt=str(path), RecipientCompleteInventoryReceiptSHA256=checksum)
        self.plan["SourceHashes"][str(path)] = checksum
        self.sync_overlay()
        with self.assertRaisesRegex(ValueError, "inventory spec/profile"):
            b.bind_run(self.expect)

    def test_complete_inventory_changed_bytes_cannot_self_authorize_new_fixed_pin(self):
        self.overlay_fixture(complete=True)
        changed = copy.deepcopy(self.inventory)
        changed["Files"][1]["Bytes"] -= 1
        self.repin_stock_receipt("RecipientCompleteInventoryReceipt", changed)
        # Even a caller repin cannot change the reviewed immutable inventory.
        self.overlay["CompleteInventoryEvidenceSHA256"] = self.original_spec["RecipientCompleteInventoryReceiptSHA256"]
        self.repin_stock_receipt("RecipientStockBindingReceipt", self.overlay)
        with self.assertRaisesRegex(ValueError, "inventory observation pin"):
            b.bind_run(self.expect)

    def test_complete_inventory_descriptor_comparison_covers_ids_time_attributes_and_hash(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.overlay)
        for key, value in (("SourceId", "BBBBBBBB:000000000000FFFF"), ("ModifiedUtc", "2026-09-29T21:46:02.6684338Z"),
                           ("Attributes", 0), ("SHA256", "0" * 64), ("Bytes", 104595491), ("Mode", "Copy"),
                           ("Relative", "zone/imagefile17.pak"), ("Relative", "zone/assetfile1.pak"),
                           ("Source", str(self.base / "assetfile17.pak"))):
            bad = copy.deepcopy(original)
            bad["Inputs"][0][key] = value
            self.repin_stock_receipt("RecipientStockBindingReceipt", bad)
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)

    def test_complete_inventory_binds_existing_baseline_pak1(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.baseline_observation)
        for key, value in (("SourceId", "AAAAAAAA:000000000000FFFF"), ("ModifiedUtc", "2026-09-29T21:46:02.6684338Z"), ("Attributes", 0)):
            bad = copy.deepcopy(original)
            bad["Inputs"][4][key] = value
            self.repin_stock_receipt("StockBindingReceipt", bad)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "descriptor differs from independent inventory"):
                b.bind_run(self.expect)

    def test_complete_inventory_semantics_are_checked_after_same_snapshot_hash(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.inventory)
        changes = [("Schema", "future"), ("StockRoot", str(self.base / "other")), ("RetailPayloadBytesRead", True),
                   ("MissingReviewedFiles", ["assetfile17.pak"]), ("UnsafeAttributes", 1), ("Files", original["Files"][:81])]
        for key, value in changes:
            bad = {**copy.deepcopy(original), key: value}
            checksum = v.sha(json.dumps(bad, indent=2).encode())
            with mock.patch.object(b, "INVENTORY_SHA", checksum):
                self.repin_stock_receipt("RecipientCompleteInventoryReceipt", bad)
                self.repin_stock_receipt("RecipientStockBindingReceipt", {**self.overlay, "CompleteInventoryEvidenceSHA256": checksum})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    b.bind_run(self.expect)

    def test_complete_inventory_rejects_asset_id_alias_or_content_claim(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.inventory)
        for key, value in (("SourceId", original["Files"][0]["SourceId"]), ("ContentVerified", True),
                           ("Name", "assetfile18.pak"), ("Family", "imagefile"), ("Bytes", True), ("ReviewedSHA256", "0" * 64)):
            bad = copy.deepcopy(original)
            bad["Files"][1][key] = value
            checksum = v.sha(json.dumps(bad, indent=2).encode())
            with mock.patch.object(b, "INVENTORY_SHA", checksum):
                self.repin_stock_receipt("RecipientCompleteInventoryReceipt", bad)
                self.repin_stock_receipt("RecipientStockBindingReceipt", {**self.overlay, "CompleteInventoryEvidenceSHA256": checksum})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    b.bind_run(self.expect)

    def test_complete_profile_budget_rejects_old_ceiling_ids_and_scope(self):
        self.overlay_fixture(complete=True)
        original = copy.deepcopy(self.plan["StockBudget"])
        for key, value in (("SupplementalProfile", b.FIVE_PROFILE), ("SupplementalLimitBytes", 966557876),
                           ("SupplementalLimitBytes", 4695508097), ("AdditionalBytesBeyondFourPAKs", 3728950220),
                           ("StockHardLinks", 76), ("ContentVerified", True), ("AdditionalResidentBytesMeasured", True)):
            self.plan["StockBudget"] = {**original, key: value}
            self.sync_overlay()
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bind_run(self.expect)
        extras = copy.deepcopy(self.plan["StockInputs"][72:])
        extras[0]["Relative"] = "zone/imagefile17.pak"
        with self.assertRaisesRegex(ValueError, "ordered scope"):
            b.stock_budget(self.plan["StockInputs"][:72], extras, b.COMPLETE_PROFILE)

    def test_complete_profile_cannot_accept_failed_f_or_unclosed_original_job(self):
        self.overlay_fixture(complete=True)
        self.state["Failure"] = "Could not find asset file assetfile101.pak"
        self.save_state()
        with self.assertRaisesRegex(ValueError, "cleanup/lease/failure"):
            b.bind_run(self.expect)
        del self.state["Failure"]
        self.state["Phases"][0]["JobActiveAtClose"] = 1
        self.save_state()
        with self.assertRaisesRegex(ValueError, "JobActiveAtClose"):
            b.bind_run(self.expect)

    def test_complete_profile_requires_recovery_and_absence_of_last_pak(self):
        self.overlay_fixture(complete=True)
        target = self.work / "zone/assetfile244.pak"
        self.write(target, b"synthetic stale link")
        with self.assertRaisesRegex(ValueError, "still exists"):
            b.bind_run(self.expect)
        target.unlink()
        self.state["Transaction"]["Files"] = [x for x in self.state["Transaction"]["Files"] if x["Path"] != "zone/assetfile244.pak"]
        self.run_pins["backup/recovery.local.json"] = self.json(self.root / "backup/recovery.local.json", self.state["Transaction"])
        self.save_state()
        with self.assertRaisesRegex(ValueError, "restoration entries"):
            b.bind_run(self.expect)

    def test_complete_inventory_limit_applies_before_initial_and_repeated_reads(self):
        self.overlay_fixture(complete=True)
        path = Path(self.original_spec["RecipientCompleteInventoryReceipt"])
        original = path.read_bytes()
        path.write_bytes(original + b" " * (b.INVENTORY_LIMIT + 1 - len(original)))
        with self.assertRaisesRegex(ValueError, "byte bound"):
            b.bind_run(self.expect)
        path.write_bytes(original)
        reader = b.Reader()
        reader.read(path, limit=b.INVENTORY_LIMIT)
        path.write_bytes(original + b" " * (b.INVENTORY_LIMIT + 1 - len(original)))
        with self.assertRaisesRegex(ValueError, "byte bound"):
            reader.read(path, limit=64 * 1024**2)


if __name__ == "__main__":
    unittest.main()
