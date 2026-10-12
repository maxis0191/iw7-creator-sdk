"""Pure witness/wrapper checks using synthetic framing; no native process."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

spec = importlib.util.spec_from_file_location('gsc_consumption_audit', Path(__file__).resolve().parents[1] / 'audit_gsc_consumption.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture():
    code, stack = b'\x34\x19', struct.pack('<II', 1, 0) + b'main\0'
    compressed = zlib.compress(stack)
    raw = b'GSC\0' + struct.pack('<III', len(compressed), len(stack), len(code)) + compressed + code
    assembly = b'sub:main\nOP_Return\nend:main\n'
    pins = {'tool_sha256': audit.sha(b'fake-tool'), 'source_revision': 'a' * 40,
            'source_sha256': 'b' * 64, 'tables_sha256': 'c' * 64}
    witness = {'schema': 'iw7.gsc-consumption-native/1', 'engine': 'iw7-pc',
               'input_bytes': len(raw), 'input_sha256': audit.sha(raw),
               'bytecode_bytes': len(code), 'bytecode_sha256': audit.sha(code),
               'stack_bytes': len(stack), 'stack_sha256': audit.sha(stack),
               'bytecode_consumed': len(code), 'stack_consumed': len(stack),
               'initial_op_end_verified': True, 'branch_targets_verified': True, 'complete_consumption_verified': True,
               'functions': [{'bytecode_begin': 1, 'declared_bytes': 1, 'bytecode_end': 2,
                              'stack_begin': 0, 'stack_end': len(stack)}],
               'assembly_bytes': len(assembly), 'assembly_sha256': audit.sha(assembly), 'assembly_hex': assembly.hex()}
    witness.update({k: v for k, v in pins.items() if k != 'tool_sha256'})
    return raw, assembly, pins, witness


class ConsumptionWitnessTests(unittest.TestCase):
    def test_valid_synthetic_witness(self):
        raw, assembly, pins, witness = fixture()
        self.assertEqual(audit.validate_witness(raw, witness, pins), assembly)

    def test_all_binding_fields_and_both_cursors_are_required(self):
        raw, _, pins, witness = fixture()
        for key in ('schema', 'engine', 'input_sha256', 'input_bytes', 'bytecode_sha256', 'stack_sha256',
                    'bytecode_consumed', 'stack_consumed', 'source_revision', 'source_sha256',
                    'tables_sha256', 'initial_op_end_verified', 'branch_targets_verified', 'complete_consumption_verified'):
            altered = copy.deepcopy(witness)
            altered.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit.validate_witness(raw, altered, pins)
        for key in ('bytecode_consumed', 'stack_consumed'):
            altered = copy.deepcopy(witness)
            altered[key] -= 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                audit.validate_witness(raw, altered, pins)

    def test_boolean_and_integer_fields_are_not_interchangeable(self):
        raw, _, pins, witness = fixture()
        witness['complete_consumption_verified'] = 1
        with self.assertRaises(ValueError):
            audit.validate_witness(raw, witness, pins)

    def test_function_sizes_and_partition_must_cover_both_buffers(self):
        raw, _, pins, witness = fixture()
        for field in ('bytecode_begin', 'declared_bytes', 'bytecode_end', 'stack_begin', 'stack_end'):
            altered = copy.deepcopy(witness)
            altered['functions'][0][field] += 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.validate_witness(raw, altered, pins)
        witness['functions'] = []
        with self.assertRaisesRegex(ValueError, 'suffix'):
            audit.validate_witness(raw, witness, pins)

    def test_assembly_bytes_are_bound_and_hex_must_be_canonical(self):
        raw, _, pins, witness = fixture()
        for replacement in ('ff', witness['assembly_hex'] + ' ', witness['assembly_hex'][:-1]):
            altered = dict(witness, assembly_hex=replacement)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                audit.validate_witness(raw, altered, pins)

    def test_container_and_compressed_suffixes_are_refused(self):
        raw, _, _, _ = fixture()
        for malformed in (raw[:-1], raw + b'\0', b'BAD!' + raw[4:]):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                audit.unpack(malformed)
        code, stack = audit.unpack(raw)
        for compressed in (zlib.compress(stack) + b'\0', zlib.compress(stack + b'extra'), zlib.compress(stack)[:-1]):
            malformed = b'GSC\0' + struct.pack('<III', len(compressed), len(stack), len(code)) + compressed + code
            with self.subTest(compressed=compressed), self.assertRaises(ValueError):
                audit.unpack(malformed)

    def test_wrong_or_missing_pins_and_duplicate_json_are_refused(self):
        raw, _, pins, witness = fixture()
        for replacement in ({}, dict(pins, tables_sha256='d' * 64), dict(pins, source_revision='not-a-revision')):
            with self.subTest(pins=replacement), self.assertRaises(ValueError):
                audit.validate_witness(raw, witness, replacement)
        with self.assertRaises(ValueError):
            json.loads('{"schema":1,"schema":2}', object_pairs_hook=audit.unique_object)

    def test_extra_fields_and_extra_claims_are_refused(self):
        raw, _, pins, witness = fixture()
        for field in ('unexpected', 'external_gsc_dependency_absent', 'runtime_ready'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'exactly'):
                audit.validate_witness(raw, dict(witness, **{field: True}), pins)

    def test_bounded_pipe_capture_reads_exact_input_and_output(self):
        payload = b'original input\0' * 256
        result = audit.run_bounded([sys.executable, '-c',
            'import sys; data=sys.stdin.buffer.read(); sys.stdout.buffer.write(data); sys.stderr.buffer.write(b"note")'],
            payload, limit=len(payload) + 4, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, payload)
        self.assertEqual(result.stderr, b'note')

    def test_bounded_pipe_capture_refuses_stdout_stderr_and_combined_overflow(self):
        for code in ('sys.stdout.buffer.write(b"x"*65537)', 'sys.stderr.buffer.write(b"x"*65537)',
                     'sys.stdout.buffer.write(b"x"*40000); sys.stderr.buffer.write(b"x"*40000)'):
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, 'limit'):
                audit.run_bounded([sys.executable, '-c', 'import sys; ' + code], b'', limit=65536, timeout=5)

    def test_bounded_pipe_capture_closes_timed_out_owned_process(self):
        with self.assertRaisesRegex(ValueError, 'timed out'):
            audit.run_bounded([sys.executable, '-c', 'import time; time.sleep(10)'], b'', limit=1024, timeout=0.1)

    def test_wrapper_passes_same_bytes_and_never_promotes_import_or_runtime_gates(self):
        raw, assembly, pins, witness = fixture()
        with tempfile.TemporaryDirectory() as folder:
            tool = Path(folder) / 'fake.exe'
            tool.write_bytes(b'fake-tool')
            result = subprocess.CompletedProcess([], 0, json.dumps(witness).encode(), b'')
            with patch.object(audit, 'run_bounded', return_value=result) as run:
                receipt, emitted = audit.audit_bytes(raw, tool, pins)
            self.assertEqual(run.call_args.args[1], raw)
            self.assertEqual(emitted, assembly)
            self.assertTrue(receipt['complete_consumption_verified'])
            for gate in ('external_gsc_dependency_absence_verified', 'asset_closure_complete', 'runtime_ready', 'owner_accepted'):
                self.assertFalse(receipt[gate])

    def test_wrapper_rejects_tool_replacement_and_nonzero_native_exit(self):
        raw, _, pins, witness = fixture()
        with tempfile.TemporaryDirectory() as folder:
            tool = Path(folder) / 'fake.exe'
            tool.write_bytes(b'fake-tool')
            def replaced(*args, **kwargs):
                tool.write_bytes(b'replaced')
                return subprocess.CompletedProcess([], 0, json.dumps(witness).encode(), b'')
            with patch.object(audit, 'run_bounded', side_effect=replaced), self.assertRaisesRegex(ValueError, 'changed'):
                audit.audit_bytes(raw, tool, pins)
            tool.write_bytes(b'fake-tool')
            with patch.object(audit, 'run_bounded', return_value=subprocess.CompletedProcess([], 1, b'', b'bad')), self.assertRaises(ValueError):
                audit.audit_bytes(raw, tool, pins)


if __name__ == '__main__':
    unittest.main()
