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


if __name__ == "__main__":
    unittest.main()
