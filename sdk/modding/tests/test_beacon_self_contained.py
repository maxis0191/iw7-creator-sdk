"""Source/control-flow and offline-audit tests; no IW7 runtime or retail assets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import unittest
import zlib

SDK = Path(__file__).resolve().parents[1]
EXAMPLE = SDK / "examples/beacon-self-contained"
spec = importlib.util.spec_from_file_location("beacon_self_contained_verify", EXAMPLE / "verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
SOURCE = verify.SOURCE.read_text()


class SelfContainedBeaconTests(unittest.TestCase):
    def test_original_template_unchanged_and_variant_not_an_existing_adapter(self):
        self.assertEqual(hashlib.sha256((SDK / "examples/beacon/sdk_beacon.gsc").read_bytes()).hexdigest(),
                         "8ba85b3f5b3014d0c4d02b0e71f49bf617959b486502e4c63243b065abc2a0b6")
        self.assertNotIn("::", SOURCE)
        self.assertNotIn("#include", SOURCE.lower())
        self.assertIn('"mods/sdk_beacon_self_contained"', SOURCE)
        self.assertIn('"sdk_beacon_self_contained_enable"', SOURCE)
        self.assertNotIn('"mods/sdk_beacon"', SOURCE)
        self.assertFalse((EXAMPLE / "manifest.json").exists(), "This source variant must not imply an accepted package contract")

    @unittest.skipUnless(shutil.which("node"), "Node is required for the source-body host model")
    def test_actual_guard_body_and_wait_condition_with_undefined_and_false_flags(self):
        # Both snippets are valid JavaScript without translation. This exercises
        # the actual GSC source body in a host model, not an IW7 interpreter.
        body = verify.function_body(SOURCE, "intro_flag_ready")
        joined = verify.function_body(SOURCE, "joined")
        condition = re.search(r"while \((.*?)\) wait 0\.1;", joined, re.S).group(1)
        javascript = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const body = process.argv[1], condition = process.argv[2];
const values = [undefined, 0, false, 1, true, 2, -1];
let cases = 0;
for (const present of [false, true]) {
  for (const flag of values) {
    for (const frozen of [undefined, false, 0, true, 1]) {
      let flagReads = 0, frozenReads = 0;
      const flags = present ? new Proxy(Object.freeze({ intro_gesture_done: flag }), {
        get(object, key) { assert.equal(key, 'intro_gesture_done'); flagReads++; return object[key]; },
        set() { throw new Error('Retail flags must not be modified'); }
      }) : undefined;
      const level = Object.freeze({ flag: flags });
      const self = Object.freeze({ get controlsfrozen() { frozenReads++; return frozen; } });
      const context = { level, self, isdefined: value => value !== undefined };
      const script = 'function intro_flag_ready() {' + body + '}\nBoolean(' + condition + ')';
      const actualWait = vm.runInNewContext(script, context, { timeout: 100 });
      // Reference meaning: retail flag_exist guards the raw flag() result.
      const flagExists = present && flag !== undefined;
      const expectedWait = !flagExists || !flag || (frozen !== undefined && Boolean(frozen));
      assert.equal(actualWait, expectedWait);
      assert.equal(flagReads, !present ? 0 : flag === undefined ? 1 : 2);
      assert.equal(frozenReads, !flagExists || !flag ? 0 : frozen === undefined ? 1 : 2);
      cases++;
    }
  }
}
console.log(JSON.stringify({ cases, host_model_only: true }));
'''
        result = subprocess.run([shutil.which("node"), "-e", javascript, body, condition],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"cases": 70, "host_model_only": True})

    def test_assembly_rejects_external_calls_and_function_references(self):
        for opcode in ("OP_ScriptFarFunctionCall", "OP_ScriptFarFunctionCall2", "OP_ScriptFarMethodThreadCall",
                       "OP_GetFarFunction", "OP_ScriptFunctionCallPointer", "OP_CallBuiltinPointer"):
            with self.subTest(opcode=opcode), self.assertRaisesRegex(ValueError, "External or dynamic"):
                verify.inspect_assembly("sub:intro_flag_ready\n" + opcode + " utility flag\nend:intro_flag_ready\n")

    def test_assembly_requires_local_definitions_and_closed_text_functions(self):
        with self.assertRaisesRegex(ValueError, "no local definition"):
            verify.inspect_assembly("sub:intro_flag_ready\nOP_ScriptLocalFunctionCall2 absent\nend:intro_flag_ready\n")
        with self.assertRaisesRegex(ValueError, "Unclosed"):
            verify.inspect_assembly("sub:intro_flag_ready\nOP_GetZero\n")
        with self.assertRaisesRegex(ValueError, "outside"):
            verify.inspect_assembly("OP_GetZero\n")

    def test_binary_container_checks_exact_lengths_and_symbol_stack(self):
        stack = b"local_symbols\0intro_gesture_done\0"
        compressed = zlib.compress(stack)
        raw = b"GSC\0" + struct.pack("<III", len(compressed), len(stack), 1) + compressed + b"\0"
        self.assertEqual(verify.inspect_binary(raw)["stack_bytes"], len(stack))
        for invalid in (raw[:-1], raw + b"\0", b"BAD!" + raw[4:]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                verify.inspect_binary(invalid)
        external = b"scripts\\engine\\utility\0flag\0"
        compressed = zlib.compress(external)
        raw = b"GSC\0" + struct.pack("<III", len(compressed), len(external), 1) + compressed + b"\0"
        with self.assertRaisesRegex(ValueError, "External script namespace"):
            verify.inspect_binary(raw)

    def test_closed_local_assembly_cannot_prove_full_binary_consumption(self):
        # These are framing fixtures, not valid IW7 bytecode. Both buffers can
        # contain arbitrary suffixes while the supplied text stays well formed.
        assembly = (b"sub:intro_flag_ready\nOP_ScriptLocalFunctionCall2 local\nend:intro_flag_ready\n"
                    b"sub:local\nOP_GetZero\nOP_Return\nend:local\n")
        for stack_suffix, code_suffix in ((b"", b""), (b"unread_symbols\0", b""),
                                           (b"", b"\xff\xfe"), (b"unread_symbols\0", b"\xff\xfe")):
            with self.subTest(stack_suffix=stack_suffix, code_suffix=code_suffix):
                stack = b"intro_flag_ready\0local\0" + stack_suffix
                compressed = zlib.compress(stack)
                code = b"\0" + code_suffix
                binary = b"GSC\0" + struct.pack("<III", len(compressed), len(stack), len(code)) + compressed + code
                result = verify.inspect_artifacts(binary, assembly)
                self.assertTrue(result["binary"]["container_length_verified"])
                self.assertTrue(result["binary"]["symbol_stack_decompression_complete"])
                self.assertEqual(result["assembly"]["observed_script_calls"], 1)
                self.assertEqual(result["assembly"]["observed_external_script_calls"], 0)
                self.assertEqual(result["evidence_scope"], "observed_disassembly_only")
                self.assertFalse(result["external_gsc_dependency_absence_verified"])
                consumption = result["disassembly_consumption"]
                self.assertFalse(consumption["attestation_available"])
                for buffer in ("bytecode", "stack"):
                    self.assertIsNone(consumption[buffer + "_consumed_bytes"])
                    self.assertFalse(consumption[buffer + "_fully_consumed_verified"])
                self.assertNotIn("external_gsc_dependency_absent_in_this_compilation", result)


if __name__ == "__main__":
    unittest.main()
