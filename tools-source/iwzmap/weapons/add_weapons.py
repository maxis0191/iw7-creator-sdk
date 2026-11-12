"""Weapons and camos module of a map build: one recipe puts original weapons, their Pack-a-Punch route, the map's
camos and their game script into an assembled usermap zone (after assemble.py / sz2_assemble.py, like the audio,
kit and darkness modules of build-sz2.ps1).

usage: add_weapons.py <work dir> <map> <recipe.json> [--var NAME=path ...] [--report <json>] [--check]

The recipe is data (see station_zero_weapons.json); ${NAME} in any string is replaced by --var values or by the
environment variable IWZ_<NAME>. What it does, all of it from the recipe:
- fragments: zone tree fragments made by the weapon model chain (x64-zt-extensions t7-weapons/authored:
  xmodel, xsurface, materials with their techset state and constant buffer sidecars, images) are copied into
  zonetool/<map>/, and their rows.csv lines are added to zone_source/<map>.csv;
- camos: a camo material (the stock camo_NN donor shape: layer-1 images + the motion constants of the weapon vertex
  shader, see engine-camo-shading.md) is written under the name the map's camo index resolves to (e.g. camo_01 for
  "camo01"), with the stock donor's sidecars renamed, and its DDS images;
- weapons: a weapon definition derived from a stock donor definition (dump JSON): models, camo override lists,
  fields set by the recipe, attachments; written to weapons/<name>.json with a weapon row;
- stringtables: a stock table copied with rows appended (the map's own weapon table: wheel and upgrade tags);
- gsc: game script modules copied to scripts/cp/maps/<map>/<map>_<module>.gsc (rawfile rows after the level script
  row) and a call to each module's entry inserted into the level script's main() after an anchor line.
Stock files in zonetool/<map>/ are hardlinks into the stock dumps: they are never written through; a file of
the same name is removed first and written new.
--check validates the recipe and every input path without writing (exit 1 with the list of problems).
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

SECTIONS = ("fragments", "camos", "weapons", "stringtables", "gsc")


def expand(value, env):
    if isinstance(value, str):
        def rep(m):
            k = m.group(1)
            if k in env:
                return env[k]
            if ("IWZ_" + k) in os.environ:
                return os.environ["IWZ_" + k]
            raise KeyError("recipe variable ${%s} has no --var or IWZ_%s" % (k, k))
        return re.sub(r"\$\{([A-Za-z0-9_]+)\}", rep, value)
    if isinstance(value, list):
        return [expand(v, env) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, env) for k, v in value.items()}
    return value


def fresh_write(path, data, mode="w"):
    """Write a new file; never through a hardlink into a stock dump."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.lexists(path):
        os.remove(path)
    if mode == "w":
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
    else:
        with open(path, "wb") as f:
            f.write(data)


def fresh_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    shutil.copyfile(src, dst)


class Module:
    def __init__(self, work, mapname, recipe, check=False):
        self.work, self.map, self.recipe, self.check = work, mapname, recipe, check
        self.root = os.path.join(work, "zonetool", mapname)
        self.csv = os.path.join(work, "zone_source", mapname + ".csv")
        self.rows_before_world = []     # assets the world and the weapons reference
        self.rows_after_level = []      # script rawfiles, right after the level script row
        self.problems = []
        self.report = {"fragments": [], "camos": [], "weapons": [], "stringtables": [], "gsc": []}

    def need(self, path, what):
        if not os.path.exists(path):
            self.problems.append("%s missing: %s" % (what, path))
            return False
        return True

    # fragments ----------------------------------------------------------------------------------------------------
    def fragment(self, fr):
        src = fr["root"]
        rows_file = fr.get("rows", os.path.join(src, "rows.csv"))
        if not (self.need(src, "fragment root") and self.need(rows_file, "fragment rows")):
            return
        rows = [l.strip() for l in open(rows_file, encoding="utf-8") if l.strip() and not l.startswith("//")]
        files = []
        for dp, _, fns in os.walk(src):
            for fn in fns:
                if fn == "rows.csv":
                    continue
                rel = os.path.relpath(os.path.join(dp, fn), src)
                files.append(rel)
                if not self.check:
                    fresh_copy(os.path.join(src, rel), os.path.join(self.root, rel))
        self.rows_before_world += rows
        self.report["fragments"].append({"root": src, "files": len(files), "rows": rows})

    # camos --------------------------------------------------------------------------------------------------------
    def camo(self, c):
        name = c["material"]
        mat = c["json"]
        donor_root = c["donor_techsets"]        # techsets dump holding the stock donor's sidecars (camo_01's)
        donor = c.get("donor", "camo_01")
        ok = self.need(mat, "camo material") and self.need(donor_root, "donor techsets dump")
        images = []
        for suffix in c.get("image_suffixes", ["c", "n", "sg", "e", "o"]):
            p = os.path.join(c["images"], "%s_%s.dds" % (c["prefix"], suffix))
            ok = self.need(p, "camo image") and ok
            images.append(p)
        if not ok:
            return
        m = json.load(open(mat, encoding="utf-8"))
        tech = m["techniqueSet->name"]
        side = []
        for kind, exts in (("constantbuffer", (".cbi", ".cbt")), ("state", (".statebits", ".statebitsmap", ".stateinfo"))):
            for ext in exts:
                s = os.path.join(donor_root, "techsets", kind, tech, donor + ext)
                if self.need(s, "donor sidecar"):
                    side.append((s, os.path.join(self.root, "techsets", kind, tech, name + ext)))
        expected = {os.path.basename(p)[:-4] for p in images}
        used = {t["image"] for t in m["textureTable"] if t.get("lastCharacter") == 49}
        missing = sorted(i for i in used if i.startswith(c["prefix"]) and i not in expected)
        if missing:
            self.problems.append("camo %s names images the recipe does not ship: %s" % (name, missing))
        if self.check:
            self.report["camos"].append({"material": name, "images": len(images), "sidecars": len(side)})
            return
        fresh_write(os.path.join(self.root, "materials", name + ".json"), json.dumps(m, indent=4))
        for s, d in side:
            fresh_copy(s, d)
        for p in images:
            fresh_copy(p, os.path.join(self.root, "images", os.path.basename(p)))
        self.rows_before_world.append("material," + name)
        motion = {cst["nameHash"]: cst["literal"] for cst in m["constantTable"] if cst["name"] == "secondarySam"}
        self.report["camos"].append({"material": name, "from": mat, "images": [os.path.basename(p) for p in images],
                                     "uv_transform": {str(k): v for k, v in motion.items()}})

    # weapons ------------------------------------------------------------------------------------------------------
    def weapon(self, w):
        if not self.need(w["donor"], "donor weapon definition"):
            return
        d = json.load(open(w["donor"], encoding="utf-8"))
        wd = d["weapDef"]
        d["szInternalName"] = w["name"]
        if "display" in w:
            d["szDisplayName"] = w["display"]
        wd["gunXModel"] = w["view_model"]
        wd["worldModel"] = w["world_model"]
        for k in ("worldXModelLeftHand", "worldXModelRightHand"):
            wd[k] = w["world_model"]
        for k in ("gunXModelLeftHand", "gunXModelRightHand"):
            wd[k] = w.get("view_model_akimbo", "")
        for k in ("complexWorldModel", "complexWorldModelLeftHand", "complexWorldModelRightHand", "complexGunXModel",
                  "complexGunXModelLeftHand", "complexGunXModelRightHand"):
            if isinstance(wd.get(k), list):
                wd[k] = ["" for _ in wd[k]]
        for k, names in (("camoViewModelMaterialOverride", w.get("camo_vm", [])),
                         ("camoWorldModelMaterialOverride", w.get("camo_wm", []))):
            if isinstance(wd.get(k), list):
                if len(names) > len(wd[k]):
                    self.problems.append("%s: %d camo materials, the definition holds %d" % (k, len(names), len(wd[k])))
                wd[k] = list(names)[:len(wd[k])] + [""] * max(0, len(wd[k]) - len(names))
        for k, v in w.get("weapdef", {}).items():
            if k not in wd:
                self.problems.append("%s: weapDef has no field %s" % (w["name"], k))
            wd[k] = v
        for k, v in w.get("top", {}).items():
            if k not in d:
                self.problems.append("%s: weapon has no field %s" % (w["name"], k))
            d[k] = v
        if self.check:
            self.report["weapons"].append({"name": w["name"]})
            return
        fresh_write(os.path.join(self.root, "weapons", w["name"] + ".json"), json.dumps(d, indent=4))
        self.rows_before_world.append("weapon," + w["name"])
        self.report["weapons"].append({"name": w["name"], "donor": w["donor"], "view_model": w["view_model"],
                                       "set": sorted(w.get("weapdef", {})) + sorted(w.get("top", {}))})

    # stringtables -------------------------------------------------------------------------------------------------
    def stringtable(self, s):
        if not self.need(s["base"], "stock table"):
            return
        lines = [l.rstrip("\r\n") for l in open(s["base"], encoding="utf-8") if l.strip()]
        n = len(lines)
        for row in s.get("append", []):
            lines.append(",".join([str(n)] + [str(x) for x in row]))
            n += 1
        if not self.check:
            fresh_write(os.path.join(self.root, *s["name"].split("/")), "\n".join(lines) + "\n")
            self.rows_before_world.append("stringtable," + s["name"])
        self.report["stringtables"].append({"name": s["name"], "rows": n, "appended": len(s.get("append", []))})

    # gsc ----------------------------------------------------------------------------------------------------------
    def gsc(self, g):
        if not self.need(g["src"], "script module"):
            return
        mod = g["module"]
        rel = "scripts/cp/maps/%s/%s_%s.gsc" % (self.map, self.map, mod)
        call = "    scripts\\cp\\maps\\%s\\%s_%s::%s();" % (self.map, self.map, mod, g.get("entry", "init"))
        src = open(g["src"], encoding="utf-8").read()
        src = src.replace("scripts\\cp\\maps\\cp_iwz\\cp_iwz_", "scripts\\cp\\maps\\%s\\%s_" % (self.map, self.map))
        level = os.path.join(self.root, "scripts", "cp", "maps", self.map, self.map + ".gsc")
        if self.check:          # before assembly the level script is not in the tree yet: checked at the real run
            self.report["gsc"].append({"module": mod})
            return
        if not self.need(level, "level script"):
            return
        fresh_write(os.path.join(self.root, *rel.split("/")), src)
        text = open(level, encoding="utf-8").read()
        anchor = g.get("after", "level.no_pap_camos")
        if call.strip() not in text:
            lines = text.split("\n")
            at = next((i for i, l in enumerate(lines) if anchor in l), None)
            if at is None:
                self.problems.append("level script has no anchor line containing %r" % anchor)
                return
            lines.insert(at + 1, call)
            fresh_write(level, "\n".join(lines))
        self.rows_after_level.append("rawfile," + rel)
        self.report["gsc"].append({"module": mod, "file": rel, "call": call.strip(), "after": anchor})

    def write_csv(self):
        lines = open(self.csv, encoding="utf-8").read().splitlines()
        level_row = "rawfile,scripts/cp/maps/%s/%s.gsc" % (self.map, self.map)
        if self.rows_after_level:
            if level_row not in lines:
                self.problems.append("level script row %s not in %s" % (level_row, self.csv))
                return
            at = lines.index(level_row) + 1
            lines[at:at] = [r for r in self.rows_after_level if r not in lines]
        at = next((i for i, l in enumerate(lines) if l.startswith("com_map,")), len(lines))
        new = []
        for r in self.rows_before_world:
            if r not in lines and r not in new:
                new.append(r)
        lines[at:at] = new
        fresh_write(self.csv, "\n".join(lines) + "\n")
        self.report["csv_rows_added"] = len(new) + len(self.rows_after_level)

    def run(self):
        t0 = time.time()
        for fr in self.recipe.get("fragments", []):
            self.fragment(fr)
        for c in self.recipe.get("camos", []):
            self.camo(c)
        for w in self.recipe.get("weapons", []):
            self.weapon(w)
        for s in self.recipe.get("stringtables", []):
            self.stringtable(s)
        for g in self.recipe.get("gsc", []):
            self.gsc(g)
        if not self.check and not self.problems:
            self.write_csv()
        self.report["seconds"] = round(time.time() - t0, 2)
        self.report["problems"] = self.problems
        return not self.problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("work")
    ap.add_argument("map")
    ap.add_argument("recipe")
    ap.add_argument("--var", action="append", default=[], help="NAME=value for ${NAME} in the recipe")
    ap.add_argument("--report")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    env = dict(v.split("=", 1) for v in a.var)
    recipe = json.load(open(a.recipe, encoding="utf-8"))
    unknown = [k for k in recipe if k not in SECTIONS and not k.startswith("_")]
    try:
        recipe = expand({k: v for k, v in recipe.items() if k in SECTIONS}, env)
    except KeyError as e:
        print("add_weapons: %s" % e.args[0])
        return 1
    m = Module(a.work, a.map, recipe, check=a.check)
    if unknown:
        m.problems.append("unknown recipe sections: %s" % unknown)
    ok = m.run() and not unknown
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(m.report, open(a.report, "w", encoding="utf-8"), indent=2)
    r = m.report
    print("weapons module: %d fragments, %d camos, %d weapons, %d tables, %d scripts, %s rows, %.2f s%s" % (
        len(r["fragments"]), len(r["camos"]), len(r["weapons"]), len(r["stringtables"]), len(r["gsc"]),
        r.get("csv_rows_added", "no"), r["seconds"], " (check only)" if a.check else ""))
    for p in m.problems:
        print("  PROBLEM " + p)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
