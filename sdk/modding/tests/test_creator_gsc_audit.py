"""Synthetic retained records only; the native audit is never executed."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import zlib

SDK = Path(__file__).resolve().parents[1]
REPO = SDK.parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


a = module(SDK / "creator_gsc_audit.py", "creator_gsc_audit_test")
p = module(REPO / "ops/modding/Package-CommunityMod.py", "creator_gsc_packager_test")


class AuditFixture:
    def __init__(self, base, version=2):
        self.base, self.version = Path(base).resolve(), version
        self.project, self.run = self.base / "project", self.base / "run"
        self.project.mkdir(parents=True)
        source = (SDK / "examples/beacon-self-contained/sdk_beacon_self_contained.gsc").read_bytes()
        (self.project / "sdk_beacon_self_contained.gsc").write_bytes(source)
        self.paths = {"compilation": self.base / "compilation.json", "plan": self.base / "plan.json",
                      "build": self.run / "build-receipt.json", "supervision": self.run / "supervision.json",
                      "input": self.base / "variant.gscbin", "consumption": self.run / "witness-variant/consumption.json",
                      "assembly": self.run / "witness-variant/disassembly.gscasm"}
        self.pins = {"tool_sha256": "a" * 64, "source_revision": a.V2_SOURCE_REVISION if version == 2 else "b" * 40,
                     "source_sha256": "c" * 64, "tables_sha256": "d" * 64}
        code, stack, asm = b"\x34\x34", b"x", b"OP_End\n"
        compressed = zlib.compress(stack)
        raw = b"GSC\0" + struct.pack("<III", len(compressed), len(stack), len(code)) + compressed + code
        self.raw = {"input": raw, "assembly": asm}
        native = {"schema": "iw7.gsc-consumption-native/1", "engine": "iw7-pc", "input_bytes": len(raw), "input_sha256": a.sha(raw),
                  "bytecode_bytes": len(code), "bytecode_sha256": a.sha(code), "stack_bytes": len(stack), "stack_sha256": a.sha(stack),
                  "bytecode_consumed": len(code), "stack_consumed": len(stack), "initial_op_end_verified": True,
                  "branch_targets_verified": True, "complete_consumption_verified": True,
                  **{k: v for k, v in self.pins.items() if k != "tool_sha256"},
                  "functions": [{"bytecode_begin": 1, "declared_bytes": 1, "bytecode_end": 2, "stack_begin": 0, "stack_end": 1}],
                  "assembly_bytes": len(asm), "assembly_sha256": a.sha(asm), "assembly_hex": asm.hex()}
        self.bound = {"schema": "iw7.gsc-consumption-bound/1", "pins": copy.deepcopy(self.pins), "native": native,
                      "tool_rehashed_after_execution": True, "input_transport": "same_bytes_via_stdin", "complete_consumption_verified": True,
                      "external_gsc_dependency_absence_verified": False, "asset_closure_complete": False, "runtime_ready": False, "owner_accepted": False}
        self.compilation = json.loads((SDK / "examples/beacon-self-contained/validation-2026-10-12.json").read_bytes())
        self.compilation["binary"].update(bytes=len(raw), sha256=a.sha(raw), bytecode_bytes=len(code), stack_bytes=len(stack))
        self.compilation["assembly"].update(bytes=len(asm), sha256=a.sha(asm))
        self.plan = {"schema": "iw7.gsc-audit-build-plan/1", "output": str(self.run), "python": str(self.base / "python.exe"),
                     "wrapper": str(SDK / "audit_gsc_consumption.py"), "wrapper_sha256": a.WRAPPER_SHA256,
                     "source_revision": self.pins["source_revision"], "tables_sha256": self.pins["tables_sha256"],
                     "tool_source_sha256": a.V2_TOOL_SOURCE if version == 2 else "e" * 64,
                     "residual_closure_policy": "original-job-pinned-vctip/1", "job_source_sha256": "f" * 64,
                     "members_source_sha256": "1" * 64, "output_limit_bytes": 2 * 1024**3, "output_stop_threshold_bytes": 1800 * 1024**2,
                     "inputs": [{"role": "variant", "path": str(self.paths["input"]), "bytes": len(raw), "sha256": a.sha(raw)},
                                {"role": "original", "path": str(self.base / "unread-control.gscbin"), "bytes": 17, "sha256": "2" * 64}]}
        self.build = {"schema": "iw7.gsc-audit-build-run/" + str(version), "plan": self.plan, "lease_token": "synthetic-lease",
                      "success": True, "storage_limit_exceeded": False, "tool_sha256": self.pins["tool_sha256"],
                      "build_source_manifest": {"schema": "iw7.gsc-audit-build-source/2", **{k: v for k, v in self.pins.items() if k != "tool_sha256"},
                                                "tool_source_sha256": self.plan["tool_source_sha256"]},
                      "root_pid": 123, "lease_owner_pid": 456, "run_id": "3" * 32, "peak_observed_output_bytes": 1000,
                      "started_utc": "2026-10-12T07:00:00.200000+00:00", "finished_utc": "2026-10-12T07:00:01.000000+00:00", "steps": []}
        command = [self.plan["python"], "-B", self.plan["wrapper"], "--tool", str(self.run / "native/Release/iw7-gsc-audit.exe"),
                   "--tool-sha256", self.pins["tool_sha256"], "--source-revision", self.pins["source_revision"],
                   "--source-sha256", self.pins["source_sha256"], "--tables-sha256", self.pins["tables_sha256"],
                   "--input", str(self.paths["input"]), "--output", str(self.run / "witness-variant")]
        for name in ["cmake-version", "configure", "build", "reader-tests", "native-negative-tests", "witness-variant", "witness-original"]:
            self.build["steps"].append({"name": name, "exit_code": 0, "wrapper_exit_code": 0, "failure": None,
                                        "storage_limit_exceeded": False, "command": command if name == "witness-variant" else ["synthetic-unexecuted"]})
        sample = {"ElapsedMs": 1100, "CompletedMs": 1100, "RootExited": True, "Active": 0, "RootExitCode": 0}
        self.supervision = {"Schema": "iw7.gsc-audit-build-supervision/1", "LeaseToken": self.build["lease_token"], "Success": version == 2,
                            "TreeClosed": True, "LeaseReleased": True, "RootExitCode": 0, "JobActiveAtClose": 0,
                            "RootPID": 123, "RootImage": self.plan["python"], "RootCreatedUtc": "2026-10-12T07:00:00.1000000Z",
                            "OriginalIdentity": {"PID": 123, "Source": "OriginalProcessHandle", "Image": self.plan["python"],
                                                 "CreatedUtc": "2026-10-12T07:00:00.1000000Z", "Priority": 16384},
                            "RunID": self.build["run_id"], "StartedUtc": "2026-10-12T07:00:00.0000000Z",
                            "FinishedUtc": "2026-10-12T07:00:01.2000000Z", "OriginalJobSourceSHA256": self.plan["job_source_sha256"],
                            "MemberObserverSHA256": self.plan["members_source_sha256"], "DeadlineSeconds": 3600,
                            "DrainDeadlineMilliseconds": 2000, "StopThresholdBytes": 1800 * 1024**2, "OutputLimitBytes": 2 * 1024**3,
                            "PeakObservedOutputBytes": 1000, "RootExitObservedMs": 1000, "ObservationCheckedMs": 1120,
                            "LastObservation": copy.deepcopy(sample),
                            "QualifiedClosure": {"Mode": "OriginalJobNaturalClosure", "Residual": False, "CompletionVerified": True,
                                                  "ClosureVerified": True, "AcceptanceGranted": True, "Error": None, "StopRequested": False,
                                                  "Identity": None, "First": None, "Final": None, "CloseObservation": copy.deepcopy(sample)},
                            "CompletionEvidence": {"Verified": True, "RunID": self.build["run_id"], "ToolSHA256": self.pins["tool_sha256"],
                                                   "SourceSHA256": self.pins["source_sha256"]}}
        if version == 1:
            self.supervision["Failure"] = "Unqualified residual descendants; drain deadline reached"
        self.save()

    def write(self, role, value):
        raw = value if isinstance(value, bytes) else json.dumps(value, indent=2).encode()
        self.paths[role].parent.mkdir(parents=True, exist_ok=True)
        self.paths[role].write_bytes(raw)
        return a.sha(raw)

    def save(self):
        for role, value in self.raw.items():
            self.write(role, value)
        self.write("compilation", self.compilation)
        self.write("consumption", self.bound)
        self.build["plan_sha256"] = self.supervision["PlanSHA256"] = self.write("plan", self.plan)
        roles = ["source-manifest", "tool", "wrapper", "compiler-config-0", "input-variant", "input-original",
                 "witness-variant", "witness-original", "assembly-variant", "assembly-original"] + ["result-" + x["name"] for x in self.build["steps"]]
        if "completion_artifacts" not in self.build:
            self.build["completion_artifacts"] = [{"role": role, "path": str(self.run / (role + ".synthetic")), "bytes": 1, "sha256": "4" * 64} for role in roles]
            for artifact in self.build["completion_artifacts"]:
                role = artifact["role"]
                record_role = {"input-variant": "input", "witness-variant": "consumption", "assembly-variant": "assembly"}.get(role)
                if record_role:
                    raw = self.paths[record_role].read_bytes()
                    artifact.update(path=str(self.paths[record_role]), bytes=len(raw), sha256=a.sha(raw))
                elif role == "tool":
                    artifact.update(path=str(self.run / "native/Release/iw7-gsc-audit.exe"), sha256=self.pins["tool_sha256"])
                elif role == "wrapper":
                    artifact.update(path=self.plan["wrapper"], sha256=a.WRAPPER_SHA256)
        self.supervision["QualifiedClosure"]["ReceiptSHA256"] = self.write("build", self.build)
        self.write("supervision", self.supervision)
        self.evidence = {"schema": "iw7.creator-gsc-audit-input/1", "run_root": str(self.run), "source_sha256": self.compilation["source_sha256"],
                         "pins": copy.deepcopy(self.pins), "files": {role: {"path": str(path), "sha256": a.sha(path.read_bytes())} for role, path in self.paths.items()}}

    def inspect(self):
        # Any accidental new invocation is a failure, not a mock native success.
        with mock.patch("subprocess.Popen", side_effect=AssertionError("Native execution prohibited")):
            return a.inspect(self.project, REPO, self.evidence, p)


class CreatorGscAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="creator-gsc-records-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.f = AuditFixture(self.base)

    def test_v2_links_records_and_measures_structure_without_finalization(self):
        before = {x: x.read_bytes() for x in self.base.rglob("*") if x.is_file()}
        report = self.f.inspect()
        self.assertTrue(report["global_completion_record_linked"])
        self.assertTrue(report["supervision_success_reported"])
        self.assertEqual((report["bytecode_consumed"], report["stack_consumed"]), (2, 1))
        self.assertEqual((report["observed_far_opcodes"], report["observed_pointer_opcodes"]), (0, 0))
        for key in ("global_build_revalidated", "compilation_provenance_authenticated", "native_execution_authenticated",
                    "external_gsc_dependency_absence_verified", "recipient_closure_complete", "finalization_allowed",
                    "package_ready", "runtime_ready", "owner_accepted"):
            self.assertIs(report[key], False)
        self.assertEqual(before, {x: x.read_bytes() for x in self.base.rglob("*") if x.is_file()})

    def test_v1_failure_stays_failure_after_successful_cleanup(self):
        f = AuditFixture(self.base / "v1", version=1)
        report = f.inspect()
        self.assertTrue(report["structural_consumption_measured"])
        self.assertFalse(report["global_completion_record_linked"])
        self.assertFalse(report["supervision_success_reported"])
        self.assertIn("supervision recorded failure", report["unresolved_qualifications"][0])

    def test_v1_success_boolean_cannot_upgrade_protocol(self):
        f = AuditFixture(self.base / "v1", version=1)
        f.supervision["Success"] = True
        del f.supervision["Failure"]
        f.save()
        self.assertFalse(f.inspect()["global_completion_record_linked"])

    def test_finalization_entrypoint_always_rechecks_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "finalization refused"):
            a.require_finalization(self.f.project, REPO, self.f.evidence, p)
        self.f.paths["input"].write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            a.require_finalization(self.f.project, REPO, self.f.evidence, p)

    def test_independent_pins_are_not_taken_from_bound_receipt(self):
        self.f.evidence["pins"]["tool_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Independent native audit pins"):
            self.f.inspect()

    def test_all_selected_artifacts_require_independent_byte_pins(self):
        for role, path in self.f.paths.items():
            raw = path.read_bytes()
            path.write_bytes(raw + b" ")
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "hash differs"):
                self.f.inspect()
            path.write_bytes(raw)

    def test_project_source_cannot_be_replaced_by_summary_pin(self):
        (self.f.project / "sdk_beacon_self_contained.gsc").write_bytes(b"modified source")
        with self.assertRaisesRegex(ValueError, "exact separate reviewed source"):
            self.f.inspect()

    def test_compilation_record_must_bind_source_container_assembly_and_phases(self):
        original = copy.deepcopy(self.f.compilation)
        for key, value in (("source_sha256", "0" * 64), ("source_bytes", True), ("phases", []),
                           ("binary", {**original["binary"], "sha256": "0" * 64}),
                           ("assembly", {**original["assembly"], "bytes": 0})):
            self.f.compilation = {**copy.deepcopy(original), key: value}
            self.f.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.inspect()

    def test_consumption_cursors_and_emitted_assembly_are_remeasured(self):
        original = copy.deepcopy(self.f.bound)
        for key, value in (("bytecode_consumed", 1), ("stack_consumed", 0), ("functions", []),
                           ("assembly_hex", b"different".hex()), ("bytecode_bytes", True)):
            self.f.bound = copy.deepcopy(original)
            self.f.bound["native"][key] = value
            self.f.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.inspect()

    def test_bound_receipt_cannot_claim_dependency_or_owner_acceptance(self):
        for key in ("external_gsc_dependency_absence_verified", "asset_closure_complete", "runtime_ready", "owner_accepted"):
            self.f.bound[key] = True
            self.f.save()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "cannot promote"):
                self.f.inspect()
            self.f.bound[key] = False

    def test_cross_run_paths_and_nonce_cannot_be_rebound(self):
        self.f.supervision["RunID"] = "9" * 32
        self.f.save()
        with self.assertRaisesRegex(ValueError, "nonce"):
            self.f.inspect()
        self.f.supervision["RunID"] = self.f.build["run_id"]
        self.f.plan["output"] = str(self.base / "different")
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Plan output"):
            self.f.inspect()

    def test_v2_requires_successful_global_closure_and_release(self):
        original = copy.deepcopy(self.f.supervision)
        for key, value in (("Success", False), ("TreeClosed", False), ("LeaseReleased", False),
                           ("RootExitCode", 1), ("JobActiveAtClose", 1), ("RootPID", True), ("LeaseToken", "other")):
            self.f.supervision = {**copy.deepcopy(original), key: value}
            self.f.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.inspect()

    def test_v2_completion_flags_without_exact_receipt_and_pins_refused(self):
        original = copy.deepcopy(self.f.supervision)
        for field in ("CompletionVerified", "ClosureVerified", "AcceptanceGranted"):
            self.f.supervision = copy.deepcopy(original)
            self.f.supervision["QualifiedClosure"][field] = False
            self.f.save()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "closure receipt"):
                self.f.inspect()
        self.f.supervision = original
        self.f.supervision["CompletionEvidence"]["ToolSHA256"] = "0" * 64
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Completion evidence pins"):
            self.f.inspect()

    def test_v2_deadline_and_step_completion_are_not_boolean_shortcuts(self):
        self.f.supervision["ObservationCheckedMs"] = 3000
        self.f.save()
        with self.assertRaisesRegex(ValueError, "closure time"):
            self.f.inspect()
        self.f.supervision["ObservationCheckedMs"] = 1120
        self.f.build["steps"][0]["wrapper_exit_code"] = 1
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Wrapper step exit"):
            self.f.inspect()

    def test_v2_artifact_selection_is_exact_and_links_measured_bytes(self):
        self.f.build["completion_artifacts"][-1]["role"] = "unknown"
        self.f.save()
        with self.assertRaisesRegex(ValueError, "artifact roles"):
            self.f.inspect()
        self.f.build.pop("completion_artifacts")
        self.f.save()
        next(x for x in self.f.build["completion_artifacts"] if x["role"] == "input-variant")["sha256"] = "0" * 64
        self.f.save()
        with self.assertRaisesRegex(ValueError, "artifact bytes"):
            self.f.inspect()

    def test_unknown_producer_revision_or_protocol_is_not_implicitly_supported(self):
        self.f.plan["tool_source_sha256"] = self.f.build["build_source_manifest"]["tool_source_sha256"] = "0" * 64
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Unreviewed completion producer"):
            self.f.inspect()
        self.f.build["schema"] = "iw7.gsc-audit-build-run/3"
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Unsupported global audit protocol"):
            self.f.inspect()

    def test_duplicate_json_fields_and_artifact_replacement_are_rejected(self):
        raw = self.f.paths["consumption"].read_bytes()
        self.f.paths["consumption"].write_bytes(b'{"schema":"duplicate",' + raw[1:])
        self.f.evidence["files"]["consumption"]["sha256"] = a.sha(self.f.paths["consumption"].read_bytes())
        with self.assertRaisesRegex(ValueError, "Duplicate Creator"):
            self.f.inspect()

    def test_file_change_between_validation_and_final_read_is_refused(self):
        actual = a.link_completion
        def change_after_link(*args):
            result = actual(*args)
            path = self.f.paths["assembly"]
            path.write_bytes(b"OP_Bad\n")
            return result
        with mock.patch.object(a, "link_completion", change_after_link), self.assertRaisesRegex(ValueError, "changed across read group"):
            self.f.inspect()

    def test_artifact_paths_cannot_select_another_run_or_duplicate_role(self):
        self.f.evidence["run_root"] = str(self.base)
        with self.assertRaisesRegex(ValueError, "build path differs"):
            self.f.inspect()
        self.f.evidence["run_root"] = str(self.f.run)
        self.f.evidence["files"]["unknown"] = self.f.evidence["files"]["assembly"]
        with self.assertRaisesRegex(ValueError, "Exact audit artifact roles"):
            self.f.inspect()


if __name__ == "__main__":
    unittest.main()
