"""Synthetic /3 linkage fixtures. Decoder double is explicit, never native proof.

The SDK tests the actual independently pinned operand parser. These tests exercise
Creator's receipt/source/controls binding and mandatory delegation to that parser.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SDK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reference_fixture_base", SDK / "tests/test_creator_gsc_audit.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
a = fixtures.a


class ReferenceFixture(fixtures.AuditFixture):
    def __init__(self, base):
        super().__init__(base)
        self.pins["source_revision"] = a.V3_SOURCE_REVISION
        self.plan.update(schema="iw7.gsc-audit-build-plan/2", source_revision=a.V3_SOURCE_REVISION,
                         tool_source_sha256=a.V3_TOOL_SOURCE, reference_contract="iw7.gsc-reference-native/1")
        self.build["schema"] = "iw7.gsc-audit-build-run/3"
        self.build["build_source_manifest"].update(source_revision=a.V3_SOURCE_REVISION, tool_source_sha256=a.V3_TOOL_SOURCE)
        self.bound["pins"] = copy.deepcopy(self.pins)
        self.bound["native"]["source_revision"] = a.V3_SOURCE_REVISION
        for role, relative in a.REFERENCE_FILES.items():
            self.paths[role] = self.run / relative
        self.paths["original_input"] = self.base / "original.gscbin"
        self.raw["original_input"] = self.raw["input"]  # Explicitly tiny synthetic consumption container.
        self.plan["inputs"][1].update(path=str(self.paths["original_input"]), bytes=len(self.raw["input"]), sha256=a.sha(self.raw["input"]))
        self.source_root = self.base / "reader-source"
        (self.source_root / "audit").mkdir(parents=True)
        profile = {"table_files": []}
        for i in range(8):
            path = self.source_root / ("table-" + str(i))
            path.write_bytes(b"synthetic table")
            profile["table_files"].append({"path": path.name, "sha256": a.sha(path.read_bytes())})
        reader = b'''# Explicit test double; not a native decoder or production policy.
def validate(raw, native, pins, source_root, consumption_validator):
    consumption_validator.validate_witness(raw, native['consumption'], pins['decoder'])
    if native['functions'] != []:
        raise ValueError('Synthetic decoder refuses inconsistent function coverage')
    return native['synthetic_result']
'''
        content = {"reference_reader": reader, "reference_profile": json.dumps(profile).encode(),
                   "reference_tests": b"# Synthetic harness, never invoked\n"}
        self.source_pins = {}
        for key, (relative, _) in a.REFERENCE_SOURCES.items():
            path = self.source_root / relative
            path.write_bytes(content[key])
            self.source_pins[key] = (relative, a.sha(content[key]))
            self.plan.update({key: str(path), key + "_sha256": self.source_pins[key][1]})
        self.plan["tool_root"] = str(self.source_root)
        self.reference_pins = {"decoder": self.pins, "profile_sha256": self.source_pins["reference_profile"][1],
            "reference_validator_sha256": self.source_pins["reference_reader"][1], "consumption_validator_sha256": a.WRAPPER_SHA256}
        self.build["reference_pins"] = self.reference_pins
        self.extra = {"original_consumption": copy.deepcopy(self.bound), "reference_pins": self.reference_pins,
            "reference_controls": {"schema": "iw7.gsc-reference-controls/1", "pins": self.reference_pins,
                "opcode_cases": 153, "unsupported_refusals": 2, "unresolved_controls": 4, "native_invocations": 159,
                "beacon_roles": ["variant", "original"], "tests_run": 3, "failures": 0, "errors": 0, "skipped": 0, "successful": True}}
        for role, count, absent in (("variant", 570, True), ("original", 560, False)):
            result = {"schema": "iw7.gsc-reference-bound/1", "pins": self.reference_pins,
                "input_sha256": a.sha(self.raw["input"]), "instruction_count": count,
                "complete_instruction_coverage_verified": True, "encoded_external_script_reference_absence": absent,
                "blockers": [] if absent else [{"bytecode_offset": 212, "stack_offset": 318, "detail": {"target": "flag_exist"}},
                                                {"bytecode_offset": 226, "stack_offset": 345, "detail": {"target": "flag"}}],
                "native_execution_authenticated": False, "native_builtin_semantics_verified": False,
                "asset_dependency_closure_verified": False, "retail_runtime_compatibility_verified": False,
                "runtime_validation_passed": False, "owner_acceptance": False, "package_ready": False}
            self.extra[role + "_bound"] = result
            self.extra[role + "_native"] = {"schema": "iw7.gsc-reference-native/1", "profile_sha256": self.reference_pins["profile_sha256"],
                "consumption": copy.deepcopy(self.bound["native"]), "functions": [], "synthetic_result": copy.deepcopy(result)}
        for step in self.build["steps"]:
            if step["name"] == "witness-variant":
                step["command"][step["command"].index("--source-revision") + 1] = a.V3_SOURCE_REVISION
        self.build["steps"].append({"name": "native-reference-tests", "exit_code": 0, "wrapper_exit_code": 0, "failure": None,
            "storage_limit_exceeded": False, "command": [self.plan["python"], "-B", self.plan["reference_tests"], "--tool",
                str(self.run / "native/Release/iw7-gsc-audit.exe"), "--pins", str(self.run / "reference-pins.json"),
                "--source-root", str(self.source_root), "--consumption-validator", self.plan["wrapper"],
                "--variant", str(self.paths["input"]), "--original", str(self.paths["original_input"]), "--output", str(self.run / "references")]})
        self.supervision["CompletionEvidence"]["ReferenceContractVerified"] = True
        self.ready = True
        self.save()

    def save(self):
        if not getattr(self, "ready", False):
            return super().save()
        for role, value in self.extra.items():
            self.write(role, value)
        self.build.pop("completion_artifacts", None)
        super().save()
        links = {"input-original": "original_input", "witness-original": "original_consumption",
                 "reference-pins": "reference_pins", "reference-controls": "reference_controls"}
        links.update({"reference-" + r.replace("_", "-"): r for r in ("variant_native", "variant_bound", "original_native", "original_bound")})
        artifacts = {x["role"]: x for x in self.build["completion_artifacts"]}
        for role, key in links.items():
            raw = self.paths[key].read_bytes()
            artifacts[role] = {"role": role, "path": str(self.paths[key]), "bytes": len(raw), "sha256": a.sha(raw)}
        for key, (relative, _) in self.source_pins.items():
            path, role = self.source_root / relative, key.replace("_", "-")
            artifacts[role] = {"role": role, "path": str(path), "bytes": path.stat().st_size, "sha256": a.sha(path.read_bytes())}
        self.build["completion_artifacts"] = list(artifacts.values())
        super().save()
        self.evidence.update(schema="iw7.creator-gsc-audit-input/2", references={"source_root": str(self.source_root), "pins": self.reference_pins})

    def inspect(self):
        with mock.patch.object(a, "REFERENCE_SOURCES", self.source_pins), mock.patch.object(a, "REFERENCE_INPUTS",
                {role: a.sha(self.raw["input"]) for role in ("variant", "original")}):
            return super().inspect()


class CreatorReferenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="creator-reference-fixture-")
        self.addCleanup(temporary.cleanup)
        self.f = ReferenceFixture(Path(temporary.name))

    def test_synthetic_v3_clears_only_encoded_reference_question(self):
        result = self.f.inspect()
        self.assertTrue(result["global_completion_record_linked"])
        self.assertTrue(result["encoded_external_script_reference_absence"])
        for key in ("external_gsc_dependency_absence_verified", "recipient_closure_complete", "package_ready", "runtime_ready",
                    "owner_accepted", "native_execution_authenticated", "global_build_revalidated"):
            self.assertFalse(result[key])

    def test_missing_reference_phase_cannot_qualify(self):
        self.f.build["steps"].pop()
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Ordered completion steps"):
            self.f.inspect()

    def test_unverified_global_reference_completion_is_refused(self):
        self.f.supervision["CompletionEvidence"]["ReferenceContractVerified"] = False
        self.f.save()
        with self.assertRaisesRegex(ValueError, "completion was not verified"):
            self.f.inspect()

    def test_successful_reference_witnesses_cannot_override_failed_global_supervision(self):
        self.f.supervision.update(Success=False, Failure="completion collector rejected null source SHA", CompletionEvidence=None)
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Global audit supervision failed"):
            self.f.inspect()

    def test_each_control_count_and_skips_are_bound(self):
        for field in ("native_invocations", "opcode_cases", "unsupported_refusals", "unresolved_controls", "skipped"):
            with self.subTest(field=field):
                value = self.f.extra["reference_controls"][field]
                self.f.extra["reference_controls"][field] += 1
                self.f.save()
                with self.assertRaisesRegex(ValueError, "Exact native reference controls"):
                    self.f.inspect()
                self.f.extra["reference_controls"][field] = value

    def test_new_input_protocol_never_accepts_historical_v6_receipts(self):
        self.f.plan["schema"] = "iw7.gsc-audit-build-plan/1"
        self.f.build["schema"] = "iw7.gsc-audit-build-run/2"
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Unsupported global audit protocol"):
            self.f.inspect()

    def test_consistent_previous_producer_records_are_no_longer_accepted(self):
        previous = "42e6c403a789b38ede39fd58ff0cb5f77da7d002"
        old_digest = "68ba75b9ee7a6b3cb6e5812c55581291ed8344dd37ee90ba6a56d0dbd58eede6"
        self.f.pins["source_revision"] = previous
        self.f.plan.update(source_revision=previous, tool_source_sha256=old_digest)
        self.f.build["build_source_manifest"].update(source_revision=previous, tool_source_sha256=old_digest)
        for witness in (self.f.bound, self.f.extra["original_consumption"]):
            witness["pins"]["source_revision"] = previous
            witness["native"]["source_revision"] = previous
        for role in ("variant", "original"):
            self.f.extra[role + "_native"]["consumption"]["source_revision"] = previous
            self.f.extra[role + "_native"]["synthetic_result"]["pins"]["decoder"]["source_revision"] = previous
        step = next(x for x in self.f.build["steps"] if x["name"] == "witness-variant")
        step["command"][step["command"].index("--source-revision") + 1] = previous
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Unreviewed completion producer"):
            self.f.inspect()

    def test_new_revision_cannot_keep_previous_tool_source_digest(self):
        old_digest = "68ba75b9ee7a6b3cb6e5812c55581291ed8344dd37ee90ba6a56d0dbd58eede6"
        self.f.plan["tool_source_sha256"] = old_digest
        self.f.build["build_source_manifest"]["tool_source_sha256"] = old_digest
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Unreviewed completion producer"):
            self.f.inspect()

    def test_previous_native_witness_cannot_be_mixed_into_new_run(self):
        self.f.extra["variant_native"]["consumption"]["source_revision"] = "42e6c403a789b38ede39fd58ff0cb5f77da7d002"
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Same-Run reference and consumption"):
            self.f.inspect()

    def test_even_identical_reference_file_from_another_run_is_refused(self):
        self.f.paths["variant_native"] = self.f.base / "previous-run/references/variant-native.json"
        self.f.save()
        with self.assertRaisesRegex(ValueError, "variant_native path differs"):
            self.f.inspect()

    def test_native_consumption_must_match_companion_from_same_run(self):
        self.f.extra["variant_native"]["consumption"]["stack_consumed"] = 0
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Same-Run reference and consumption"):
            self.f.inspect()

    def test_native_report_is_submitted_to_independent_reader(self):
        self.f.extra["variant_native"]["functions"] = [{"untrusted": True}]
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Synthetic decoder refuses"):
            self.f.inspect()

    def test_recomputed_bound_report_cannot_be_replaced_by_claimed_boolean(self):
        self.f.extra["variant_bound"]["package_ready"] = True
        self.f.save()
        with self.assertRaisesRegex(ValueError, "Recomputed bound reference report"):
            self.f.inspect()

    def test_source_table_and_reader_drift_are_refused(self):
        for path in (self.f.source_root / "table-0", self.f.source_root / "audit/references.py"):
            with self.subTest(path=path):
                raw = path.read_bytes()
                path.write_bytes(raw + b"changed")
                with self.assertRaisesRegex(ValueError, "source changed|table changed"):
                    self.f.inspect()
                path.write_bytes(raw)

    def test_reader_path_replacement_never_executes_unverified_python(self):
        original_module = a.module
        replaced = False
        def instrument(path, name):
            nonlocal replaced
            loaded = original_module(path, name)
            if Path(path).name == "creator_self_contained.py":
                snapshot = loaded.snapshot
                def replace_after_read(source, packager, limit):
                    nonlocal replaced
                    raw = snapshot(source, packager, limit)
                    if Path(source) == self.f.source_root / "audit/references.py" and not replaced:
                        replaced = True
                        Path(source).write_bytes(b"raise AssertionError('UNVERIFIED READER EXECUTED')\n")
                    return raw
                loaded.snapshot = replace_after_read
            return loaded
        with mock.patch.object(a, "module", side_effect=instrument):
            with self.assertRaisesRegex(ValueError, "Reference source changed during inspection"):
                self.f.inspect()


if __name__ == "__main__":
    unittest.main()
