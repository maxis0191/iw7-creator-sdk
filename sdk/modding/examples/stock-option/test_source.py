"""Execute the production pure GSC arithmetic; no engine/native/retail inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
SOURCE = (HERE / "sdk_stock_option_v1.gsc").read_text(encoding="utf-8")


def function(name):
    match = re.search(r"(?m)^" + re.escape(name) + r"\(([^)]*)\)\s*\{", SOURCE)
    if match is None:
        raise ValueError("Production GSC function missing: " + name)
    start = match.end(); depth = 1; cursor = start
    while depth:
        char = SOURCE[cursor]
        if char == "{": depth += 1
        if char == "}": depth -= 1
        cursor += 1
    return match.group(1), SOURCE[start:cursor-1]


def production_accounting():
    args, body = function("one_round_transfer")
    # Tiny translation of this actual pure helper, not an engine/GSC emulator.
    lines = []
    for statement in body.split(";"):
        statement = " ".join(statement.split())
        if not statement: continue
        if statement.startswith("if "):
            condition = re.fullmatch(r"if \((.*)\) return undefined", statement)
            if condition is None: raise ValueError("Unexpected pure helper control flow")
            expression = condition[1].replace("||", " or ").replace("&&", " and ")
            lines.append("if " + expression + ": return None")
        elif statement == "transaction = []":
            lines.append("transaction = {}")  # GSC arrays extend on indexed assignment.
        elif re.fullmatch(r"transaction\[[01]\] = [a-z_]+(?: - 1)?", statement) or statement == "return transaction":
            lines.append(statement)
        else: raise ValueError("Unexpected non-pure helper statement")
    namespace = {}
    exec("def actual(" + args + "):\n" + "\n".join("    " + line for line in lines), {"__builtins__": {}}, namespace)
    return namespace["actual"]


class StockOptionSourceTests(unittest.TestCase):
    def test_confirmed_shots_keep_clip_and_pay_one_reserve_round(self):
        actual = production_accounting()
        for clip in range(2, 65):
            for stock in range(1, 129):
                result = actual(clip, stock, clip-1, stock)
                self.assertEqual(result, {0: clip, 1: stock-1})
                self.assertEqual(sum(result.values()), clip+stock-1)

    def test_zero_negative_excess_clip_reserve_and_non_single_debits_refused(self):
        actual = production_accounting()
        for before in (-1, 0, 1, 513):
            self.assertIsNone(actual(before, 10, before-1, 10))
        for stock in (-1, 0, 65536):
            self.assertIsNone(actual(12, stock, 11, stock))
        for after in (-1, 0, 9, 10, 12, 13):
            self.assertIsNone(actual(12, 10, after, 10))
        for stock_after in (0, 9, 11, 100):
            self.assertIsNone(actual(12, 10, 11, stock_after))

    def test_last_reserve_round_is_paid_and_no_next_transfer_is_allowed(self):
        actual = production_accounting()
        result = actual(12, 1, 11, 1)
        self.assertEqual(result, {0: 12, 1: 0})
        self.assertIsNone(actual(12, 0, 11, 0))

    def test_partial_write_paths_do_not_restore_unpaid_clip_or_rollback_reserve(self):
        _, body = function("transfer")
        debit = body.index("self setweaponammostock")
        restore = body.index("self setweaponammoclip")
        self.assertLess(debit, restore)
        middle = body[debit:restore]
        self.assertIn('"reserve_write_unconfirmed"', middle)
        self.assertIn("return;", middle)
        self.assertEqual(body.count("self setweaponammostock"), 1)
        self.assertEqual(body.count("self setweaponammoclip"), 1)
        self.assertNotRegex(body, r"\bwait\b|\bthread\b|\bnotify\b")
        _, stopped = function("stop")
        self.assertNotIn("setweaponammo", stopped)
        self.assertLess(stopped.index("state.stopped = true"), stopped.index("self notify"))
        self.assertLess(stopped.index("shared.owner = undefined"), stopped.index("self notify"))

    def test_reload_switch_dual_wield_and_lifecycle_guards_are_real_builtin_names(self):
        _, body = function("eligible")
        for name in ("isreloading", "isswitchingweapon", "isdualwielding", "hasweapon", "getcurrentweapon"):
            self.assertIn(name, body)
        self.assertNotIn("isweaponswitching", SOURCE)
        for event in ("death", "disconnect", "weapon_change", "reload_start", "faux_spawn"):
            self.assertIn('life_end(shared, state, "' + event + '")', SOURCE)
        self.assertIn('self waittill("weapon_fired", fired_weapon)', SOURCE)
        self.assertNotIn('notify("weapon_fired"', SOURCE)
        _, shutdown = function("shutdown")
        self.assertIn("player.sdk_stock_option_listener = undefined", shutdown)
        self.assertIn("player.sdk_stock_option_active = undefined", shutdown)

    def test_contract_stays_explicit_bounded_and_unqualified(self):
        contract = json.loads((HERE / "contract.json").read_text())
        self.assertFalse(contract["activation"]["default_enabled"])
        self.assertEqual(contract["activation"]["maximum_seconds"], 30)
        self.assertEqual(contract["activation"]["maximum_active_players"], 1)
        self.assertEqual(contract["activation"]["maximum_shots"], 64)
        self.assertTrue(all(value is False for value in contract["qualification"].values()))
        self.assertEqual(contract["scope"]["new_client_files"], [])

    def test_manifest_exact_source_passes_plan_but_cannot_be_packaged(self):
        spec = importlib.util.spec_from_file_location("stock_option_sdk", SDK / "manifest.py")
        sdk = importlib.util.module_from_spec(spec); spec.loader.exec_module(sdk)
        manifest = sdk.load_manifest(HERE / "manifest.json")
        entry = manifest["package"]["files"][0]
        raw = (HERE / entry["source"]).read_bytes()
        self.assertEqual(entry["bytes"], len(raw))
        self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
        plan = sdk.validate(manifest, stage="plan")
        self.assertTrue(plan["valid"], plan["errors"])
        package = sdk.validate(manifest, root=HERE, stage="package")
        self.assertFalse(package["ready"])
        self.assertIn("package: Dependency closure incomplete", package["errors"])
        self.assertTrue(all(e["status"] == "pending" for e in manifest["package"]["evidence"] if e["kind"] != "source-check"))


if __name__ == "__main__":
    unittest.main()
