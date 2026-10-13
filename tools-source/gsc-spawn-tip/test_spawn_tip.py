"""Synthetic source/receipt tests. Never executes or opens a native executable."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("spawn_tip", Path(__file__).with_name("spawn_tip.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class ProfileTests(unittest.TestCase):
    def test_plan_never_reads_binary_and_preserves_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []
            def pin(role, path, expected=None):
                calls.append(Path(path))
                self.assertNotIn(Path(path).suffix, (".exe", ".dll"))
                return {"Role": role, "Path": str(path), "Bytes": 1, "SHA256": expected or "a" * 64, "IsText": True}
            profile = {"table_files": [{"path": f"table{i}.cpp", "sha256": "b" * 64} for i in range(8)],
                       "tables_sha256": s.PINS["decoder"]["tables_sha256"]}
            with patch.object(s, "text_pin", pin), patch.object(s, "read", return_value=b"{}"), patch.object(s, "load", return_value=profile):
                plan = s.make_plan(root, root / "audit", root / "compiler.exe", root / "python.exe",
                                   root / "host.exe", root / "job.dll", root / "runtime/run")
            self.assertEqual(len(calls), 23)
            self.assertEqual(len(plan["Bindings"]), 28)
            self.assertEqual((plan["PhysicalBytes"], plan["CommitBytes"]), (4 * 1024**3, 6 * 1024**3))
            self.assertFalse(plan["BinaryInputsVerified"])
            self.assertFalse(plan["EstimatesAreMeasured"])
            self.assertEqual(plan["Payload"], "iw7-mod/custom_scripts/cp/sdk_spawn_tip.gsc")
            for role, (size, digest) in s.BINARY_PINS.items():
                self.assertEqual(s.pins_by_role(plan)[role]["SHA256"], digest)
                self.assertEqual(s.pins_by_role(plan)[role]["Bytes"], size)

    def test_plan_refuses_existing_or_outside_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for run in (root, root / "elsewhere/run", root / "runtime/../escape"):
                with self.subTest(run=run), self.assertRaises(ValueError):
                    s.make_plan(root, root, root, root, root, root, run)

    def test_text_plan_does_not_open_executable_suffix(self):
        with patch.object(Path, "open", side_effect=AssertionError("Unexpected open")):
            with self.assertRaises(ValueError):
                s.text_pin("Source", Path.cwd() / "fake.exe")

    def test_duplicate_and_nonfinite_json_refused(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":1,"A":2}', b'{"a":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                s.load(raw)

    def test_compiler_exit_zero_error_or_missing_marker_refused(self):
        for code, out, err in ((0, b"[ERROR] failed\n", b""), (0, b"", b""),
                               (0, b"compiled iw7/a\ncompiled iw7/b\n", b""),
                               (1, b"compiled iw7/a\n", b""), (0, b"compiled iw7/a\n", b"exception")):
            with self.subTest(code=code, out=out), self.assertRaises(ValueError):
                s.compile_ok(subprocess.CompletedProcess([], code, out, err))
        s.compile_ok(subprocess.CompletedProcess([], 0, b"compiled iw7/sdk_spawn_tip.gscbin\n", b""))

    def test_bounded_read_and_create_new_preserve_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "file.json"
            s.write_new(path, b"original", 8)
            with self.assertRaises(ValueError):
                s.read(path, 7)
            with self.assertRaises(FileExistsError):
                s.write_new(path, b"changed", 8)
            self.assertEqual(path.read_bytes(), b"original")
            with self.assertRaises(ValueError):
                s.write_new(Path(temp) / "big.json", b"123", 2)

    def fixture(self, temp):
        root = Path(temp)
        phase = root / "phase"
        phase.mkdir()
        source = (s.HERE.parents[1] / s.SOURCES["Source"]).read_bytes()
        bindings = [{"Role": role, "Path": str(root / (role + ".data")), "Bytes": 1, "SHA256": "a" * 64,
                     "IsText": role not in s.BINARY_PINS}
                    for role in ("Source", "Consumption", "References", "Compiler", "Auditor")]
        return source, {"RunRoot": str(root), "Bindings": bindings, "ReferencePins": copy.deepcopy(s.PINS),
            "AuditSource": str(root / "source"), "CompilerLogBytes": 65536, "CompileSeconds": 20,
            "BinaryLimitBytes": 65536, "StackLimitBytes": 131072, "AuditLogBytes": 4*s.MIB, "AuditSeconds": 60}

    def exercise(self, temp, *, blocked=False, mismatch=False, native_exit=0, stack_size=0):
        source, plan = self.fixture(temp)
        raw = b"GSC\0" + s.struct.pack("<III", 1, 0, 1) + b"xx"
        invocations, validations = [], []
        def run(argv, payload, **kwargs):
            invocations.append((argv, payload, kwargs))
            if "-m" in argv:
                binary = Path.cwd() / "compiled/iw7/sdk_spawn_tip.gscbin"
                binary.parent.mkdir(parents=True)
                binary.write_bytes(raw)
                return subprocess.CompletedProcess(argv, 0, b"compiled iw7/sdk_spawn_tip.gscbin\n", b"")
            return subprocess.CompletedProcess(argv, native_exit, b'{"consumption":{"synthetic":true}}', b"")
        def witness(received, native, pins):
            validations.append(("consumption", received, native, pins))
            if mismatch:
                raise ValueError("synthetic witness mismatch")
            return b"synthetic assembly"
        def refs(received, native, pins, source_root, validator):
            validations.append(("references", received, native, pins))
            return {"complete_instruction_coverage_verified": True,
                    "encoded_external_script_reference_absence": not blocked,
                    "blockers": ["synthetic external call"] if blocked else []}
        consumption = types.SimpleNamespace(run_bounded=run, validate_witness=witness)
        references = types.SimpleNamespace(unpack=lambda raw: (b"", b"x"*stack_size), validate=refs)
        prior = Path.cwd()
        os.chdir(Path(temp) / "phase")
        try:
            with patch.object(s, "verify_pin", side_effect=lambda p: source if p["Role"] == "Source" else b"x"), \
                 patch.object(s, "module", side_effect=lambda p, n: consumption if p["Role"] == "Consumption" else references):
                if blocked or mismatch or native_exit or stack_size > plan["StackLimitBytes"]:
                    with self.assertRaises(ValueError):
                        s.execute(plan, "c"*64, "d"*32, "e"*32)
                else:
                    report = s.execute(plan, "c"*64, "d"*32, "e"*32)
                    self.assertTrue(report["EncodedReferenceAbsence"])
                    self.assertFalse(report["JobClosureProven"])
                    self.assertTrue(all(value is False for value in report["Limits"].values()))
        finally:
            os.chdir(prior)
        return invocations, validations

    def test_two_calls_same_input_and_both_existing_validators(self):
        with tempfile.TemporaryDirectory() as temp:
            calls, validations = self.exercise(temp)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][2], {"limit": 65536, "timeout": 20})
            self.assertEqual(calls[1][2], {"limit": 4*s.MIB, "timeout": 60})
            self.assertEqual(calls[1][0][-1], "--stdin-gscbin-references")
            self.assertEqual([v[0] for v in validations], ["consumption", "references"])
            self.assertTrue(all(v[1] == calls[1][1] for v in validations))

    def test_blocked_reference_preserves_false_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            self.exercise(temp, blocked=True)
            report = json.loads((Path(temp)/"phase/child.json").read_bytes())
            self.assertFalse(report["EncodedReferenceAbsence"])
            self.assertFalse(report["Limits"]["package_ready"])

    def test_native_failure_mismatch_or_stack_bound_cannot_emit_child_success(self):
        for scenario in ({"native_exit": 9}, {"mismatch": True}, {"stack_size": 131073}):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temp:
                calls, _ = self.exercise(temp, **scenario)
                self.assertFalse((Path(temp)/"phase/child.json").exists())
                self.assertEqual(len(calls), 1 if "stack_size" in scenario else 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
