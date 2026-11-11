"""Synthetic tests of add_weapons.py: a fake assembled zone tree, a fake donor dump, one recipe of every section."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_weapons  # noqa: E402

TECH = "l_sm_replace_x_2uvt_bafsp_vm"


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class AddWeaponsTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        T = self.t
        self.work = os.path.join(T, "work")
        root = os.path.join(self.work, "zonetool", "cp_x")
        w(os.path.join(root, "scripts", "cp", "maps", "cp_x", "cp_x.gsc"),
          "main()\n{\n    level.pap_1_camo = \"camo01\";\n    level.no_pap_camos = [];\n    other();\n}\n")
        w(os.path.join(self.work, "zone_source", "cp_x.csv"),
          "// cp_x\nrawfile,scripts/cp/maps/cp_x/cp_x.gsc\nmaterial,stock_a\ncom_map,maps/cp/cp_x.d3dbsp\n")
        frag = os.path.join(T, "frag")
        w(os.path.join(frag, "xmodel", "gun_vm.xmb"), "x")
        w(os.path.join(frag, "rows.csv"), "material,m2o/gun_camo\nxmodel,gun_vm\n")
        dump = os.path.join(T, "dump")
        w(os.path.join(dump, "weapons", "donor.json"), json.dumps({
            "szInternalName": "donor", "szDisplayName": "D", "iClipSize": 6, "attachments": ["x"],
            "weapDef": {"gunXModel": "d_vm", "worldModel": "d_wm", "worldXModelLeftHand": "d_wm",
                        "worldXModelRightHand": "d_wm", "gunXModelLeftHand": "l", "gunXModelRightHand": "r",
                        "complexGunXModel": ["a", "b"], "camoViewModelMaterialOverride": ["c1", "c2", "", ""],
                        "camoWorldModelMaterialOverride": ["", ""], "shotCount": 8}}))
        for kind, exts in (("constantbuffer", (".cbi", ".cbt")), ("state", (".statebits", ".statebitsmap", ".stateinfo"))):
            for ext in exts:
                w(os.path.join(dump, "tsets", "techsets", kind, TECH, "camo_01" + ext), "s")
        camos = os.path.join(T, "camos")
        w(os.path.join(camos, "m.json"), json.dumps({
            "techniqueSet->name": TECH,
            "textureTable": [{"image": "zz_c", "lastCharacter": 49, "typeHash": 1}],
            "constantTable": [{"name": "secondarySam", "nameHash": 4044143062, "literal": [1, 1, 0.1, 0]}]}))
        for s in ("c", "n", "sg", "e", "o"):
            w(os.path.join(camos, "img", "zz_%s.dds" % s), "d")
        w(os.path.join(T, "table.csv"), "0,a_zm,wall,X,\n1,b_zm,magic,Y,\n")
        w(os.path.join(T, "mod.gsc"), "init()\n{\n    scripts\\cp\\maps\\cp_iwz\\cp_iwz_wonder::x();\n}\n")
        self.recipe = {
            "fragments": [{"root": frag}],
            "camos": [{"material": "camo_01", "json": os.path.join(camos, "m.json"), "images": os.path.join(camos, "img"),
                       "prefix": "zz", "donor_techsets": os.path.join(dump, "tsets")}],
            "weapons": [{"name": "iw7_new_zm", "donor": os.path.join(dump, "weapons", "donor.json"),
                         "view_model": "gun_vm", "world_model": "gun_wm", "camo_vm": ["m2o/gun_camo"],
                         "weapdef": {"shotCount": 1}, "top": {"iClipSize": 12, "attachments": ["p1"]}}],
            "stringtables": [{"name": "cp/cp_x_table.csv", "base": os.path.join(T, "table.csv"),
                              "append": [["iw7_new_zm", "magic upgrade", "Wheel", ""]]}],
            "gsc": [{"module": "wonder", "src": os.path.join(T, "mod.gsc")}],
        }

    def run_module(self, check=False):
        m = add_weapons.Module(self.work, "cp_x", self.recipe, check=check)
        return m, m.run()

    def test_check_writes_nothing(self):
        before = open(os.path.join(self.work, "zone_source", "cp_x.csv")).read()
        m, ok = self.run_module(check=True)
        self.assertTrue(ok, m.problems)
        self.assertEqual(before, open(os.path.join(self.work, "zone_source", "cp_x.csv")).read())
        self.assertFalse(os.path.exists(os.path.join(self.work, "zonetool", "cp_x", "weapons")))

    def test_full_run(self):
        m, ok = self.run_module()
        self.assertTrue(ok, m.problems)
        root = os.path.join(self.work, "zonetool", "cp_x")
        csv = open(os.path.join(self.work, "zone_source", "cp_x.csv")).read().splitlines()
        # script row right after the level script; asset rows before com_map
        lvl = csv.index("rawfile,scripts/cp/maps/cp_x/cp_x.gsc")
        self.assertEqual(csv[lvl + 1], "rawfile,scripts/cp/maps/cp_x/cp_x_wonder.gsc")
        com = csv.index("com_map,maps/cp/cp_x.d3dbsp")
        for row in ("material,m2o/gun_camo", "xmodel,gun_vm", "material,camo_01", "weapon,iw7_new_zm",
                    "stringtable,cp/cp_x_table.csv"):
            self.assertLess(csv.index(row), com, row)
        wd = json.load(open(os.path.join(root, "weapons", "iw7_new_zm.json")))
        self.assertEqual(wd["szInternalName"], "iw7_new_zm")
        self.assertEqual(wd["iClipSize"], 12)
        self.assertEqual(wd["weapDef"]["shotCount"], 1)
        self.assertEqual(wd["weapDef"]["gunXModel"], "gun_vm")
        self.assertEqual(wd["weapDef"]["complexGunXModel"], ["", ""])
        self.assertEqual(wd["weapDef"]["camoViewModelMaterialOverride"], ["m2o/gun_camo", "", "", ""])
        table = open(os.path.join(root, "cp", "cp_x_table.csv")).read().splitlines()
        self.assertEqual(table[-1], "2,iw7_new_zm,magic upgrade,Wheel,")
        self.assertTrue(os.path.exists(os.path.join(root, "materials", "camo_01.json")))
        self.assertTrue(os.path.exists(os.path.join(root, "techsets", "constantbuffer", TECH, "camo_01.cbt")))
        self.assertTrue(os.path.exists(os.path.join(root, "images", "zz_sg.dds")))
        gsc = open(os.path.join(root, "scripts", "cp", "maps", "cp_x", "cp_x.gsc")).read().splitlines()
        at = next(i for i, l in enumerate(gsc) if "level.no_pap_camos" in l)
        self.assertIn("cp_x_wonder::init();", gsc[at + 1])
        mod = open(os.path.join(root, "scripts", "cp", "maps", "cp_x", "cp_x_wonder.gsc")).read()
        self.assertIn("scripts\\cp\\maps\\cp_x\\cp_x_wonder::x", mod)
        # a second run (incremental assembly) adds no row twice and no second call
        m2, ok2 = self.run_module()
        self.assertTrue(ok2, m2.problems)
        csv2 = open(os.path.join(self.work, "zone_source", "cp_x.csv")).read().splitlines()
        self.assertEqual(len(csv), len(csv2))
        gsc2 = open(os.path.join(root, "scripts", "cp", "maps", "cp_x", "cp_x.gsc")).read()
        self.assertEqual(gsc2.count("cp_x_wonder::init();"), 1)

    def test_unknown_field_and_missing_input(self):
        self.recipe["weapons"][0]["weapdef"]["noSuchField"] = 1
        self.recipe["camos"][0]["prefix"] = "absent"
        m, ok = self.run_module(check=True)
        self.assertFalse(ok)
        self.assertTrue(any("noSuchField" in p for p in m.problems))
        self.assertTrue(any("camo image missing" in p for p in m.problems))

    def test_hardlinked_stock_is_not_written_through(self):
        root = os.path.join(self.work, "zonetool", "cp_x")
        stock = os.path.join(self.t, "stock_level.gsc")
        lvl = os.path.join(root, "scripts", "cp", "maps", "cp_x", "cp_x.gsc")
        os.replace(lvl, stock)
        os.link(stock, lvl)
        before = open(stock).read()
        m, ok = self.run_module()
        self.assertTrue(ok, m.problems)
        self.assertEqual(before, open(stock).read())

    def test_vars(self):
        self.assertEqual(add_weapons.expand({"a": ["${X}/y"]}, {"X": "q"}), {"a": ["q/y"]})
        with self.assertRaises(KeyError):
            add_weapons.expand("${NOPE_NOT_SET_ANYWHERE}", {})


if __name__ == "__main__":
    unittest.main()
