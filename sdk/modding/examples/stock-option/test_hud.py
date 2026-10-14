"""Bounded HUD source/clock checks; no HUD or engine emulator."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
FROZEN = (HERE / "sdk_stock_option_v1.gsc").read_bytes()
SOURCE = (HERE / "sdk_stock_option_hud_v1.gsc").read_text(encoding="utf-8")
DISASSEMBLY = None


def function(text, name):
    match = re.search(r"(?m)^" + re.escape(name) + r"\(([^)]*)\)\s*\{", text)
    if match is None:
        raise ValueError("Production function missing: " + name)
    cursor = match.end()
    depth = 1
    while depth:
        if text[cursor] == "{": depth += 1
        if text[cursor] == "}": depth -= 1
        cursor += 1
    return match.group(1), text[match.end():cursor - 1]


def actual_clock_helper():
    args, body = function(SOURCE, "hud_seconds_remaining")
    lines = []
    for statement in body.split(";"):
        statement = " ".join(statement.split())
        if not statement:
            continue
        conditional = re.fullmatch(r"if \((remaining [<>=!]+ \d+)\) return (\d+)", statement)
        if conditional:
            lines.append("if " + conditional[1] + ": return " + conditional[2])
        elif re.fullmatch(r"remaining = deadline - now", statement):
            lines.append(statement)
        elif re.fullmatch(r"return int\(\(remaining \+ \d+\) / \d+\)", statement):
            lines.append(statement)
        else:
            raise ValueError("Unexpected non-pure clock helper statement")
    namespace = {}
    exec("def actual(" + args + "):\n" + "\n".join("    " + line for line in lines),
         {"__builtins__": {}, "int": int}, namespace)
    return namespace["actual"]


class StockOptionHudTests(unittest.TestCase):
    def test_frozen_source_and_entire_ammo_handlers_are_byte_unchanged(self):
        self.assertEqual(len(FROZEN), 11035)
        self.assertEqual(hashlib.sha256(FROZEN).hexdigest(),
                         "5a28e5a220aedfaed4481bdbd5440aec8c14bf90b5840ae62122d05a86575fba")
        for name in ("private_context", "eligible", "one_round_transfer", "shots", "transfer",
                     "trace_value", "transfer_trace", "expires", "context_guard", "life_end", "shutdown"):
            self.assertEqual(function(SOURCE, name), function(FROZEN.decode(), name), name)
        _, activation = function(SOURCE, "activate")
        self.assertIn("seconds = 10;", activation)
        self.assertIn("if (seconds < 1 || seconds > 30) return;", activation)
        self.assertIn("state.deadline = gettime() + seconds * 1000;", activation)

    def test_production_clock_rounds_up_and_never_extends_deadline(self):
        actual = actual_clock_helper()
        for milliseconds, expected in ((30000, 30), (10001, 11), (10000, 10), (9999, 10),
                                       (1001, 2), (1000, 1), (999, 1), (1, 1), (0, 0), (-1, 0)):
            self.assertEqual(actual(1_000_000_000 + milliseconds, 1_000_000_000), expected)
        self.assertEqual([actual(10000, now) for now in (0, 1, 999, 1000, 9000, 9999, 10000)],
                         [10, 10, 10, 9, 1, 1, 0])
        _, countdown = function(SOURCE, "hud_countdown")
        self.assertIn("hud_seconds_remaining(state.deadline, gettime())", countdown)
        self.assertNotIn("state.deadline =", countdown)
        self.assertNotIn("getweaponammo", countdown)

    def test_one_owner_hud_is_destroyed_before_any_stop_notification(self):
        _, show = function(SOURCE, "show_hud")
        _, stop = function(SOURCE, "stop")
        _, cleanup = function(SOURCE, "destroy_hud")
        _, activation = function(SOURCE, "activate")
        self.assertEqual(SOURCE.count("newclienthudelem(self)"), 1)
        self.assertIn("state.hud = hud;", show)
        self.assertIn("if (!isdefined(hud)) return false;", show)
        self.assertIn('self stop(shared, state, "hud_unavailable");', activation)
        self.assertLess(activation.index("self show_hud(state)"), activation.index("self thread shots"))
        self.assertLess(stop.index("state.stopped = true"), stop.index("destroy_hud(state)"))
        self.assertLess(stop.index("destroy_hud(state)"), stop.index("shared.owner = undefined"))
        self.assertLess(stop.index("destroy_hud(state)"), stop.index("self notify"))
        self.assertEqual(cleanup.strip(), "if (!isdefined(state.hud)) return;\n    state.hud destroy();\n    state.hud = undefined;")
        self.assertNotIn("sdk_soulbox", SOURCE)
        for event in ("death", "disconnect", "weapon_change", "reload_start", "faux_spawn"):
            self.assertIn('self thread life_end(shared, state, "' + event + '")', activation)
        self.assertIn('"game_ended"', function(SOURCE, "shutdown")[1])

    def test_display_persists_with_bounded_updates_and_expires_without_another_entity(self):
        _, countdown = function(SOURCE, "hud_countdown")
        self.assertIn('self endon("sdk_stock_option_stopped");', countdown)
        self.assertIn('level endon("game_ended");', countdown)
        self.assertIn("while (!state.stopped && isdefined(state.hud))", countdown)
        self.assertRegex(countdown, r"if \(remaining == 0\)\s*\{\s*destroy_hud\(state\);\s*return;")
        self.assertIn("wait 0.05;", countdown)
        self.assertIn("previous != remaining", countdown)
        self.assertIn('state.hud settext("Stock Option active | " + remaining + "s");', countdown)
        self.assertNotIn("newclienthudelem", countdown)

    def test_new_manifest_is_exact_but_runtime_and_package_stay_unqualified(self):
        spec = importlib.util.spec_from_file_location("stock_option_hud_manifest", HERE.parents[1] / "manifest.py")
        sdk = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sdk)
        manifest = sdk.load_manifest(HERE / "hud-manifest.json")
        entry = manifest["package"]["files"][0]
        raw = (HERE / entry["source"]).read_bytes()
        self.assertEqual(entry["bytes"], len(raw))
        self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn("hud", manifest["lifecycle"]["cleanup"])
        self.assertIn("sdk_stock_option_v1", [row["id"] for row in manifest["conflicts"]])
        self.assertTrue(sdk.validate(manifest, stage="plan")["valid"])
        self.assertFalse(sdk.validate(manifest, root=HERE, stage="package")["ready"])
        contract = json.loads((HERE / "hud-contract.json").read_text())
        self.assertTrue(all(value is False for value in contract["qualification"].values()))
        self.assertEqual(contract["hud"]["entities_per_activation"], 1)

    def test_actual_compiled_hud_calls_and_cleanup_order(self):
        if DISASSEMBLY is None:
            self.skipTest("Supply --disassembly for existing offline compiler evidence")
        validation = json.loads((HERE / "hud-source-validation.json").read_text())
        evidence = next(row for row in validation["offline_phases"] if row["mode"] == "disasm")
        assembly = DISASSEMBLY.read_bytes()
        self.assertEqual(len(assembly), evidence["output_bytes"])
        self.assertEqual(hashlib.sha256(assembly).hexdigest(), evidence["output_sha256"])
        text = assembly.decode()
        _, stop = function(SOURCE, "stop")
        self.assertIn("destroy_hud(state)", stop)
        compiled_stop = re.search(r"(?ms)^sub:stop\r?$\n(.*?)^end:stop\r?$", text)[1]
        self.assertLess(compiled_stop.index("OP_ScriptLocalFunctionCall destroy_hud"),
                        compiled_stop.index("OP_notify"))
        self.assertEqual(len(re.findall(r"OP_CallBuiltin\d newclienthudelem\b", text)), 1)
        self.assertIn("OP_CallBuiltinMethod0 destroy", text)
        self.assertIn("Stock Option active | ", text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--disassembly", type=Path)
    args, remaining = parser.parse_known_args()
    DISASSEMBLY = args.disassembly
    unittest.main(argv=[sys.argv[0]] + remaining)
