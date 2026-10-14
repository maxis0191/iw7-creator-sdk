"""Check actual GSC phase captures and optional pinned compiler disassembly."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("stock_option_source_helpers", HERE / "test_source.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
DISASSEMBLY = None


class StockOptionTraceTests(unittest.TestCase):
    def test_accounting_helper_is_byte_unchanged_and_no_setter_added(self):
        args, body = source.function("one_round_transfer")
        self.assertEqual(hashlib.sha256((args + "\0" + body).encode()).hexdigest(),
                         "3d684d59138c0955c345ee777630b7c17e113d1338f0506117fbc7432b821d45")
        _, transfer = source.function("transfer")
        self.assertEqual(transfer.count("self setweaponammostock"), 1)
        self.assertEqual(transfer.count("self setweaponammoclip"), 1)
        self.assertNotRegex(transfer, r"\bwait\b|\bthread\b|\bnotify\b|\bprint\s*\(")
        self.assertNotIn('notify("weapon_fired"', source.SOURCE)

    def test_real_getters_keep_short_circuit_and_trace_after_last_path_write(self):
        _, body = source.function("transfer")
        reserve = body.index("self setweaponammostock")
        clip = body.index("self setweaponammoclip")
        self.assertLess(body.index("clip = self getweaponammoclip"), reserve)
        self.assertLess(body.index("stock = self getweaponammostock"), reserve)
        for prefix, target in (("debit", "clip"), ("restored", "transaction[0]")):
            guard = prefix + "_eligible"
            self.assertIn(guard + " = self eligible(state.weapon);", body)
            self.assertIn("if (" + guard + ") " + prefix + "_stock = self getweaponammostock(state.weapon);", body)
            self.assertIn("if (" + guard + " && " + prefix + "_stock == transaction[1]) " + prefix + "_clip = self getweaponammoclip(state.weapon);", body)
            self.assertIn(prefix + "_clip != " + target, body)
        between = body[reserve:clip]
        self.assertEqual(between.count("transfer_trace("), 1)
        self.assertRegex(between, r'transfer_trace\([^;]+"reserve_write_unconfirmed"\);\s*self stop\([^;]+\);\s*return;\s*}')
        self.assertLess(body.index("state.shots++;"), body.index('"confirmed"'))
        self.assertGreater(body.index('"confirmed"'), clip)

    def test_one_line_maps_raw_samples_and_explicit_unknowns(self):
        _, trace = source.function("transfer_trace")
        self.assertEqual(trace.count("print("), 1)
        self.assertNotIn("getweaponammo", trace)
        for key, variable in (("fired_weapon", "fired_weapon"), ("entry_clip", "entry_clip"),
                              ("entry_reserve", "entry_stock"), ("after_debit_clip", "debit_clip"),
                              ("after_debit_reserve", "debit_stock"), ("after_restore_clip", "restored_clip"),
                              ("after_restore_reserve", "restored_stock")):
            self.assertIn('"; ' + key + '=" + trace_value(' + variable + ')', trace)
        self.assertIn('if (outcome == "confirmed") marker = "SHOT";', trace)
        self.assertIn("observed_handler_order_only=1; engine_atomicity=unknown", trace)
        _, formatting = source.function("trace_value")
        self.assertIn('if (!isdefined(value)) return "unobserved";', formatting)

    def test_actual_pinned_disassembly_preserves_write_and_failure_branch_order(self):
        if DISASSEMBLY is None:
            self.skipTest("Supply --disassembly for existing offline compiler evidence; no compiler runs from tests")
        validation = json.loads((HERE / "source-validation.json").read_text())
        evidence = next(x for x in validation["offline_phases"] if x["mode"] == "disasm")
        assembly = DISASSEMBLY.read_bytes()
        self.assertEqual(len(assembly), evidence["output_bytes"])
        self.assertEqual(hashlib.sha256(assembly).hexdigest(), evidence["output_sha256"])
        binary = DISASSEMBLY.parents[2] / "compiled/iw7/sdk_stock_option_v1.gscbin"
        self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(), evidence["input_sha256"])
        text = assembly.decode()
        match = re.search(r"(?ms)^sub:transfer\r?$\n(.*?)^end:transfer\r?$", text)
        self.assertIsNotNone(match)
        transfer = match[1]
        reserve = transfer.index("OP_CallBuiltinMethod2 setweaponammostock")
        clip = transfer.index("OP_CallBuiltinMethod2 setweaponammoclip")
        self.assertLess(reserve, clip)
        self.assertEqual(transfer.count("OP_CallBuiltinMethod2 setweaponammostock"), 1)
        self.assertEqual(transfer.count("OP_CallBuiltinMethod2 setweaponammoclip"), 1)
        middle = transfer[reserve:clip]
        self.assertLess(middle.index("getweaponammostock"), middle.index("getweaponammoclip"))
        self.assertEqual(middle.count("OP_ScriptLocalFunctionCall transfer_trace"), 1)
        trace = middle.index("OP_ScriptLocalFunctionCall transfer_trace")
        jumps = re.findall(r"OP_JumpOnFalse (loc_[A-Fa-f0-9]+)", middle[:trace])
        self.assertTrue(jumps)
        target = jumps[-1]
        self.assertIn("OP_End", middle[trace:])
        self.assertLess(middle[trace:].index("OP_End"), middle[trace:].index(target))
        self.assertNotRegex(middle, r"OP_wait|OP_notify|OP_.*ThreadCall|OP_CallBuiltin\d print")
        emitter = re.search(r"(?ms)^sub:transfer_trace\r?$\n(.*?)^end:transfer_trace\r?$", text)[1]
        self.assertEqual(len(re.findall(r"OP_CallBuiltin\d print\b", emitter)), 1)
        self.assertIn("observed_handler_order_only=1; engine_atomicity=unknown", emitter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--disassembly", type=Path)
    args, remaining = parser.parse_known_args()
    DISASSEMBLY = args.disassembly
    unittest.main(argv=[sys.argv[0]] + remaining)
