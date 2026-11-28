"""Assemble the ZoneTool mod-zone source of the original wonder weapon ONE WAY (offline, stdlib only).

    python -B make_zone.py --fragment <r14>/zonetool --dump <IW7-Runtime>/iwz-map-ref-a/dump --out <dir> [--sounds <dir>]

Writes
    <out>/zonetool/mod/...             the view-model fragment as built, plus weapons/<weapon>.json and
                                       animpkg/<weapon>_package.json (both made from the stock template weapon)
    <out>/zone_source/mod.csv          zone `mod`: ignore/require rows, then the assets the mod embeds
    <out>/zone_source/<stock>.csv      copies of the stock zone lists the `ignore` rows read (preflight needs them
                                       beside mod.csv; ZoneTool reads them from its own zone_source)
    <out>/make_zone_report.json        every field set, every stand-in, the reload timers, the rows

--sounds <dir> (made by x64-zt-extensions tools-source/asset-bridge/iw7-audio/foley/foley_bank.py bank) adds the weapon's own
sounds: sound/, soundbank/, sound_assets/ and sfxpkg/ go under zonetool/mod, the weapon's sfxPackage and notetrack sound map are
set, and `soundbank,<bank>` and `sfxpkg,<name>` rows join mod.csv.

Everything the weapon points at that is not ours (world model, hand and anim packages, effect and sound packages,
tracer, icons) stays the template's and is a reference to the stock zones, not an embedded asset.
"""
import argparse
import csv
import json
import os
import shutil
import sys

# ---- this weapon (the only weapon named in this tool) ------------------------------------------------------
WEAPON = "iw7_szoneway_zm"
PACKAGE = WEAPON + "_package"               # own anim package: the stock one with this weapon's reload timers
ZONE = "mod"                                # the sound bank / mod.ff convention: the zone is named `mod`
CLIP = 12                                   # DESIGN.md section 3: "12 in the stack"
RESERVE = 60                                # "60 in reserve"
FIRE_TIME_MS = 400                          # one shot every 0.4 s
RELOAD_MS = 2400                            # 2.4 s
RELOAD_EMPTY_MS = 2800                      # 2.8 s from empty
REACH_UNITS = 1500.0                        # instant hit reaches 1,500 units

# ---- defaults of this machine and of the stock template (overridable) ---------------------------------------
DEFAULT_TEMPLATE = "iw7_atomizer_mp"        # stock weapon the definition is cloned from
DEFAULT_TEMPLATE_ZONE = "cp_zmb"            # stock zone holding the template weapon, its package and its models
# Stock zones whose lists the csv ignores: every asset of them is a reference, never embedded.
STOCK_ZONES = ("common_cp", "global_cp", "cp_zmb", "patch_cp_zmb", "techsets_common", "techsets_global",
               "techsets_common_core_mp", "techsets_global_core_mp", "techsets_common_mp", "techsets_global_mp",
               "techsets_common_cp", "techsets_global_cp", "techsets_cp_zmb")
# Zones ZoneTool loads for the techsets of the materials (same list as the map builds, tools-source/iwzmap/build-sz2.ps1).
REQUIRE_ZONES = ("techsets_common", "techsets_global", "techsets_common_core_mp", "techsets_global_core_mp",
                 "techsets_common_mp", "techsets_global_mp", "techsets_common_cp", "techsets_global_cp",
                 "techsets_cp_zmb")
# Stock reload shape (tools-source/asset-bridge/t7-weapons/iw7_weapon_author.py): the perk plays it 35% faster,
# a reload can be cut at 84% of it.
INTERRUPT_FRACTION = 0.84
FAST_RELOAD_FRACTION = 0.65
VIEW_MODEL_FIELDS = ("gunXModel", "defaultViewModel")
FRAGMENT_SKIP = ("rows.csv",)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)


def find_stock(dump, zone, folder, name):
    path = os.path.join(dump, zone, folder, name + ".json")
    if not os.path.isfile(path):
        sys.exit("stock %s/%s/%s.json not found under %s" % (zone, folder, name, dump))
    return path


def read_rows(fragment):
    path = os.path.join(fragment, "rows.csv")
    if not os.path.isfile(path):
        sys.exit("no rows.csv in " + fragment)
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("//"):
                kind, _, name = line.partition(",")
                rows.append((kind.strip(), name.strip()))
    return rows


SOURCE_OF = {"material": ("materials", ".json"), "xmodel": ("xmodel", ".xmb"), "xanim": ("xanim", ".xab"),
             "image": ("images", ".dds")}


def check_rows(fragment, rows):
    missing = []
    for kind, name in rows:
        folder, ext = SOURCE_OF.get(kind, (None, None))
        if folder and not os.path.isfile(os.path.join(fragment, folder, *name.split("/")) + ext):
            missing.append("%s,%s" % (kind, name))
    if missing:
        sys.exit("rows.csv names assets the fragment does not hold: " + ", ".join(missing))


def reload_timers(old, total, empty):
    """Timers of the package for reloads of `total` / `empty` ms; the ammo goes in at the template's share of the animation."""
    new = dict(old)
    for prefix, length in (("", total), ("Empty", empty)):
        base = old.get("iReload%sTime" % prefix) or old["iReloadTime"]
        add_old = old.get("iReload%sAddTime" % prefix) or old["iReloadAddTime"]
        add = round(length * add_old / base)
        interrupt = max(add, round(length * INTERRUPT_FRACTION))
        new["iReload%sTime" % prefix] = length
        new["iReload%sAddTime" % prefix] = add
        new["iReload%sInterruptTime" % prefix] = interrupt
        new["iFastReload%sTime" % prefix] = round(length * FAST_RELOAD_FRACTION)
        new["iFastReload%sAddTime" % prefix] = round(add * FAST_RELOAD_FRACTION)
        new["iFastReload%sInterruptTime" % prefix] = round(interrupt * FAST_RELOAD_FRACTION)
    return new


SOUND_DIRS = ("sound", "soundbank", "sound_assets", "sfxpkg")


def read_sounds(path):
    """The sounds report of foley_bank.py: bank, sfx package name, csv rows, notetrack map."""
    report_path = os.path.join(path, "sounds_report.json")
    if not os.path.isfile(report_path):
        sys.exit("no sounds_report.json in %s (run foley_bank.py bank first)" % path)
    rep = load(report_path)
    for d in SOUND_DIRS:
        if not os.path.isdir(os.path.join(path, d)):
            sys.exit("%s holds no %s/ folder" % (path, d))
    return rep


def apply_sounds(weapon, rep, changes):
    """The weapon's own sound package and its notetrack-to-alias map (the counted key/value arrays of the weapon)."""
    d = weapon["weapDef"]
    changes.append(("sfxPackage", d.get("sfxPackage"), rep["sfxpackage"]))
    d["sfxPackage"] = rep["sfxpackage"]
    keys, values = rep["notetrack_keys"], rep["notetrack_values"]
    changes.append(("notetrackSoundMapKeys", weapon.get("notetrackSoundMapKeys"), keys))
    changes.append(("notetrackSoundMapValues", weapon.get("notetrackSoundMapValues"), values))
    weapon["notetrackSoundMapKeys"] = list(keys)
    weapon["notetrackSoundMapValues"] = list(values)


def author(template, pkg_template, view_model):
    """(weapon json, package json, [(field, before, after)])."""
    w = json.loads(json.dumps(template))
    d = w["weapDef"]
    changes = []

    def put(holder, key, value, label=None):
        before = holder.get(key)
        holder[key] = value
        if before != value:
            changes.append((label or key, before, value))

    put(w, "szInternalName", WEAPON)
    put(w, "iClipSize", CLIP)
    put(d, "iMaxAmmo", RESERVE)
    put(d, "iStartAmmo", RESERVE)
    put(d, "iFireTime", FIRE_TIME_MS)
    for field in VIEW_MODEL_FIELDS:
        put(d, field, view_model)
    put(d, "reloadDisabled", False)                 # the template pistol cannot reload at all
    put(d, "suppressAmmoReserveDisplay", False)     # the template hides the reserve count; this weapon has 60
    # instant hit to REACH_UNITS: full damage out to the reach, no fall-off before it (the script sets the real damage)
    put(d, "maxDamageRange", REACH_UNITS)
    put(d, "minDamageRange", REACH_UNITS)
    put(d, "minDamage", d["damage"])
    put(d, "minPlayerDamage", d["playerDamage"])
    for key in [k for k in w if k.startswith("attachments") and isinstance(w[k], list)]:
        put(w, key, ["" for _ in w[key]])             # the template's scope attachment belongs to its own model
    for key in ("complexGunXModel", "complexWorldModel", "camoViewModelMaterialOverride",
                "camoWorldModelMaterialOverride"):
        if isinstance(d.get(key), list):
            d[key] = ["" for _ in d[key]]
    put(d, "szXAnims", PACKAGE)

    pkg = json.loads(json.dumps(pkg_template))
    pkg["timers"] = reload_timers(pkg_template["timers"], RELOAD_MS, RELOAD_EMPTY_MS)
    for key, value in pkg["timers"].items():
        if pkg_template["timers"].get(key) != value:
            changes.append(("package.timers." + key, pkg_template["timers"].get(key), value))
    return w, pkg, changes


def stand_ins(template_name, weapon, sounds_own=False):
    d = weapon["weapDef"]
    fields = ("worldModel", "defaultWorldModel", "szXAnimsRightHanded", "szXAnimsLeftHanded", "handXModel",
              "vfxPackage", "sfxPackage", "tracerType", "hudIcon", "pickupIcon", "ammoCounterIcon", "fireRumble",
              "meleeImpactRumble", "stowTag", "stowOffsetModel", "szLUICrosshairWidget", "killIcon")
    out = {f: d.get(f) for f in fields if d.get(f) and not (f == "sfxPackage" and sounds_own)}
    out["szDisplayName"] = weapon.get("szDisplayName")
    out["package animations (every slot of %s)" % PACKAGE] = "stock FTL pistol animations, the template's own package"
    out["feel (spread, kick, sway, ADS, melee, aim assist, accuracy graph, damage values)"] = \
        "template %s values, untouched" % template_name
    return out


def write_csv(path, rows, stock_present):
    lines = ["// zone %s: ONE WAY (%s), generated by make_zone.py" % (ZONE, WEAPON)]
    lines += ["ignore," + z for z in stock_present]
    lines += ["require," + z for z in REQUIRE_ZONES]
    lines += ["%s,%s" % row for row in rows]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fragment", required=True, help="built view-model fragment (the folder holding xmodel/, materials/, rows.csv)")
    ap.add_argument("--dump", required=True, help="stock dump root (one folder per zone, each with its <zone>.csv)")
    ap.add_argument("--out", required=True, help="output folder (zonetool/mod, zone_source/mod.csv)")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE, help="stock weapon the definition is cloned from")
    ap.add_argument("--template-zone", default=DEFAULT_TEMPLATE_ZONE, help="stock zone holding the template")
    ap.add_argument("--sounds", help="folder written by foley_bank.py bank: the weapon's own sound bank, sfx package and notetrack map")
    args = ap.parse_args(argv)

    sounds = read_sounds(args.sounds) if args.sounds else None
    rows = read_rows(args.fragment)
    check_rows(args.fragment, rows)
    models = [name for kind, name in rows if kind == "xmodel"]
    if len(models) != 1:
        sys.exit("rows.csv must hold exactly one xmodel row (the view model), found %d" % len(models))
    view_model = models[0]

    template = load(find_stock(args.dump, args.template_zone, "weapons", args.template))
    pkg_name = template["weapDef"]["szXAnims"]
    pkg_template = load(find_stock(args.dump, args.template_zone, "animpkg", pkg_name))
    weapon, pkg, changes = author(template, pkg_template, view_model)
    if sounds:
        apply_sounds(weapon, sounds, changes)

    mod = os.path.join(args.out, "zonetool", ZONE)
    if os.path.exists(mod):
        shutil.rmtree(mod)
    shutil.copytree(args.fragment, mod, ignore=shutil.ignore_patterns(*FRAGMENT_SKIP))
    save(os.path.join(mod, "weapons", WEAPON + ".json"), weapon)
    save(os.path.join(mod, "animpkg", PACKAGE + ".json"), pkg)
    if sounds:
        for folder in SOUND_DIRS:
            shutil.copytree(os.path.join(args.sounds, folder), os.path.join(mod, folder), dirs_exist_ok=True)

    # stock lists beside the csv (what `ignore,<zone>` reads)
    zone_source = os.path.join(args.out, "zone_source")
    present, absent = [], []
    for zone in STOCK_ZONES:
        src = os.path.join(args.dump, zone, zone + ".csv")
        if os.path.isfile(src):
            os.makedirs(zone_source, exist_ok=True)
            shutil.copyfile(src, os.path.join(zone_source, zone + ".csv"))
            present.append(zone)
        else:
            absent.append(zone)
    if args.template_zone not in present:
        sys.exit("the stock list of %s is missing under %s: the weapon's stock references cannot be ignored" %
                 (args.template_zone, args.dump))

    sound_rows = [tuple(r.split(",", 1)) for r in sounds["csv_rows"]] if sounds else []
    embedded = rows + sound_rows + [("animpkg", PACKAGE), ("weapon", WEAPON)]
    lines = write_csv(os.path.join(zone_source, ZONE + ".csv"), embedded, present)

    report = {
        "weapon": WEAPON, "zone": ZONE, "template": args.template, "template_zone": args.template_zone,
        "view_model": view_model, "csv": lines, "stock_lists_ignored": present, "stock_lists_absent": absent,
        "changed_fields": [{"field": f, "template": b, "now": a} for f, b, a in changes],
        "stand_ins": stand_ins(args.template, weapon, bool(sounds)),
        "sounds": None if not sounds else {"bank": sounds["bank"], "zone": sounds["zone"], "sfxpackage": sounds["sfxpackage"],
                                           "aliases": sounds["aliases"], "alias_rows": len(sounds["rows"]),
                                           "sfx_fields_changed": sounds["sfx_fields_changed"],
                                           "notetrack_map": dict(zip(sounds["notetrack_keys"], sounds["notetrack_values"]))},
        "reload_ms": {"full": RELOAD_MS, "empty": RELOAD_EMPTY_MS,
                      "package_timers": {k: pkg["timers"][k] for k in pkg["timers"] if "eload" in k and pkg["timers"][k]}},
        "ammo": {"clip": CLIP, "iMaxAmmo": RESERVE, "iStartAmmo": RESERVE,
                 "meaning": "ASSUMED reserve outside the clip: stock zombies weapons keep iMaxAmmo a multiple of the clip "
                            "(8/80, 14/126, 15/135, 20/160) and the mechanic's script reads getweaponammostock"},
    }
    save(os.path.join(args.out, "make_zone_report.json"), report)
    print("make_zone: %s -> %s (%d csv lines, %d fields changed)" % (WEAPON, mod, len(lines), len(changes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
