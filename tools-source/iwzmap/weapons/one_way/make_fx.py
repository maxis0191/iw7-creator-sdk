"""ONE WAY's own effects (DESIGN.md section 7), built as IW7 particle systems from stock emitters.

Every system here is ours: its emitters are cloned from stock cp_zmb systems (the only way this engine's particle
format is authored today: iw7_vfx.py decodes and re-encodes ZoneTool's stream byte-identically) and rewritten:
life, counts, sizes, velocities, colours, materials. No stock system is referenced at run time; the materials,
models and light definitions they link are stock assets of cp_zmb.

    python -B make_fx.py --dump <IW7-Runtime>/iwz-map-ref-a/dump --vfx-tool <x64-zt-extensions>/tools-source/asset-bridge/t7-weapons --out <fx dir>

Writes <out>/particlesystem/vfx/iwz/oneway/*.iw7VFX, <out>/tracer/szoneway_ticket.json,
<out>/vfxpkg/iw7_szoneway_zm_vfxpackage.json and <out>/fx.json (zone rows, what each effect is made of).

| effect | where it plays | look |
|---|---|---|
| ow_issue_v, ow_issue_v_ads, ow_issue_w | tag_flash (the weapon's flash slots) | card dust puff, three to six card chips, a press spark and a short warm light; no flame |
| szoneway_ticket (tracer) | every shot | a short pale card streak that wobbles as it flies |
| ow_ticket_2 / ow_ticket_1 / ow_ticket_r | on the booked zombie (script, playfxontag) | a card stuck to the chest: buff, buff with red (first class), pale green (upgraded) |
| ow_door | at the bell, at each zombie taken, carried or put back (script, playfx) | two leaves of warm carriage light 76 high opening and closing in 1.0 s, a warm light on the floor and bodies |
| ow_door_full | the full train | the same, whiter and brighter |
| ow_taken | the zombie taken through its door | two or three cards left turning in the air |
"""
import argparse
import copy
import json
import os
import sys

PREFIX = "vfx/iwz/oneway/"
SRC = {
    "atom_v": "vfx/iw7/core/muzflash/atomizer/vfx_muz_atom_v_a",
    "atom_w": "vfx/iw7/core/muzflash/atomizer/vfx_muz_atom_w_a",
    "kickup": "vfx/iw7/_requests/coop/vfx_trp_escvel_dust_kickup",
    "spark": "vfx/core/expl/spark_death",
}
DUST_UNLIT = "eq/vfx_vol_smk_wispy_swirl_lg_unlit"      # unlit: lit particles read black in a dark map
PAPER = "eq/vfx_debris_paper_torn_a_atl"
GLOW = "eq/vfx_vol_light_glow_abstract_03"
CARD = (1.0, 0.95, 0.84)            # ticket card, buff
CARD_RED = (0.95, 0.32, 0.25)
CARD_GREEN = (0.72, 0.95, 0.74)
WARM = (1.0, 0.78, 0.48)           # lit carriage, 1986 tungsten
WHITE = (1.0, 0.95, 0.88)

vfx = None


def load(dump, name):
    p = os.path.join(dump, "cp_zmb", "particlesystem", *name.split("/")) + ".iw7VFX"
    with open(p, "rb") as f:
        return vfx.decode(f.read())


def emitter(model, index):
    return copy.deepcopy(model["system"]["emitterDefs"][index])


def modules(e):
    for g in e["stateDefs"][0]["moduleGroupDefs"]:
        for m in g.get("moduleDefs") or []:
            yield g, m


def mod(e, kind):
    for _, m in modules(e):
        if m["moduleType"] == "PARTICLE_MODULE_" + kind:
            return vfx.module_data(m)
    return None


def drop(e, *kinds):
    names = {"PARTICLE_MODULE_" + k for k in kinds}
    for g in e["stateDefs"][0]["moduleGroupDefs"]:
        if g.get("moduleDefs"):
            g["moduleDefs"] = [m for m in g["moduleDefs"] if m["moduleType"] not in names]
            g["numModules"] = len(g["moduleDefs"])


def material_of(e):
    d = mod(e, "INIT_MATERIAL")
    if not d:
        return None
    return [a.get("material") for a in d["m_linkedAssetList"]["assetList"]]


def find_by_material(model, name, element=None):
    for i, e in enumerate(model["system"]["emitterDefs"]):
        if name in (material_of(e) or []) and (element is None or e["stateDefs"][0]["elementType"].endswith(element)):
            return i
    raise SystemExit("no emitter with material %s in %s" % (name, model["system"]["name"]))


def find_by_element(model, element):
    for i, e in enumerate(model["system"]["emitterDefs"]):
        if e["stateDefs"][0]["elementType"].endswith(element):
            return i
    raise SystemExit("no %s emitter in %s" % (element, model["system"]["name"]))


def set_material(e, name):
    d = mod(e, "INIT_MATERIAL")
    d["m_linkedAssetList"]["assetList"] = [vfx.new_linked_asset("PARTICLE_MODULE_INIT_MATERIAL", material=name)]
    d["m_linkedAssetList"]["numAssets"] = 1


def one_shot(e, burst, life, delay=(0.0, 0.0)):
    """A burst at the start: no emitter life, `burst` particles, each living `life` seconds."""
    e["emitterLife"] = {"min": 0.0, "max": 0.0}
    e["emitterDelay"] = {"min": 0.0, "max": 0.0}
    e["particleSpawnRate"] = {"min": 1.0, "max": 1.0}
    e["particleBurstCount"] = {"min": int(burst[0]), "max": int(burst[1])}
    e["particleLife"] = {"min": float(life[0]), "max": float(life[1])}
    e["particleDelay"] = {"min": float(delay[0]), "max": float(delay[1])}
    e["particleCountMax"] = max(int(burst[1]), 1)
    sp = mod(e, "INIT_SPAWN")
    if sp:   # spawn curve flat at 1 (the stock kickup fades its emission out)
        sp["m_curves"][0]["controlPoints"] = vfx.new_curve_points([(0.0, 1.0), (1.0, 1.0)])
        sp["m_curves"][0]["numControlPoints"] = 2


def nominal_size(e):
    a = mod(e, "INIT_ATTRIBUTES")
    if a is None:       # size carried by the graph alone (stock spark_death)
        return mod(e, "SIZE_GRAPH")["m_curves"][0]["scale"]
    s = max(a["m_sizeMax"][0], a["m_sizeMin"][0]) or 1.0
    lerp = mod(e, "SIZE_LERP")
    if lerp:
        return max(lerp["m_sizeEnd"][0], lerp["m_sizeBegin"][0])
    g = mod(e, "SIZE_GRAPH")
    if g:
        return s * (g["m_curves"][0]["scale"] or 1.0)
    return s


def resize(e, target):
    """Scale every size of the emitter so its nominal size becomes `target` units."""
    k = target / nominal_size(e)
    a = mod(e, "INIT_ATTRIBUTES")
    if a is None:
        for c in mod(e, "SIZE_GRAPH")["m_curves"]:
            c["scale"] = c["scale"] * k
    else:   # the graph multiplies the attributes: scaling the attributes is enough
        a["m_sizeMin"] = [x * k for x in a["m_sizeMin"]]
        a["m_sizeMax"] = [x * k for x in a["m_sizeMax"]]
    lerp = mod(e, "SIZE_LERP")
    if lerp:
        lerp["m_sizeBegin"] = [x * k for x in lerp["m_sizeBegin"]]
        lerp["m_sizeEnd"] = [x * k for x in lerp["m_sizeEnd"]]
    box = mod(e, "INIT_SPAWN_SHAPE_BOX")
    if box:
        box["m_dimensionsMin"] = [x * k for x in box["m_dimensionsMin"]]
        box["m_dimensionsMax"] = [x * k for x in box["m_dimensionsMax"]]
    return k


def velocity(e, vmin, vmax, turbulence=None):
    a = mod(e, "INIT_ATTRIBUTES")
    if a is None:
        return
    a["m_velocityMin"] = [float(vmin[0]), float(vmin[1]), float(vmin[2]), 0.0]
    a["m_velocityMax"] = [float(vmax[0]), float(vmax[1]), float(vmax[2]), 0.0]
    vg = mod(e, "VELOCITY_GRAPH")
    if vg is not None:
        if turbulence is None:
            drop(e, "VELOCITY_GRAPH")
        else:
            for c in vg["m_curves"]:
                if c["scale"]:
                    c["scale"] = float(turbulence)


def colour(e, cmin, cmax, alpha=(1.0, 1.0)):
    a = mod(e, "INIT_ATTRIBUTES")
    if a is None:       # colour carried by the graph alone: rgb of both sets made constant, alpha curves kept
        g = mod(e, "COLOR_GRAPH")
        for i, c in enumerate(g["m_curves"]):
            if i % 4 < 3:
                c["controlPoints"] = vfx.new_curve_points([(0.0, (cmin, cmax)[i // 4][i % 4]), (1.0, (cmin, cmax)[i // 4][i % 4])])
                c["numControlPoints"] = 2
                c["scale"] = 1.0
        return
    a["m_colorMin"] = [cmin[0], cmin[1], cmin[2], alpha[0]]
    a["m_colorMax"] = [cmax[0], cmax[1], cmax[2], alpha[1]]
    drop(e, "COLOR_GRAPH", "COLOR_LERP")    # the stock curves would retint our card colour


def light(e, rgb, radius, intensity, life):
    a = mod(e, "INIT_ATTRIBUTES")
    # light emitters keep their radius in size x and their intensity in size y (stock atomizer: 130 / 5.92)
    a["m_sizeMin"][0], a["m_sizeMax"][0] = radius * 0.85, radius
    a["m_sizeMin"][1], a["m_sizeMax"][1] = intensity * 0.85, intensity
    a["m_colorMin"] = [rgb[0], rgb[1], rgb[2], 1.0]
    a["m_colorMax"] = [rgb[0], rgb[1], rgb[2], 1.0]
    drop(e, "COLOR_GRAPH", "COLOR_LERP")
    e["particleLife"] = {"min": float(life[0]), "max": float(life[1])}
    e["particleBurstCount"] = {"min": 1, "max": 1}
    e["particleSpawnRate"] = {"min": 1.0, "max": 1.0}
    e["emitterLife"] = {"min": 0.0, "max": 0.0}


def graph(e, kind, pairs, scale=1.0, curves=None):
    """Replace every curve of a SIZE_GRAPH / INTENSITY_GRAPH with `pairs` (time, value)."""
    g = mod(e, kind)
    if g is None:
        return False
    for i, c in enumerate(g["m_curves"]):
        if curves is not None and i not in curves:
            continue
        c["controlPoints"] = vfx.new_curve_points(pairs)
        c["numControlPoints"] = len(pairs)
        c["scale"] = float(scale)
    return True


def system(name, template, emitters):
    m = copy.deepcopy(template)
    m["system"]["name"] = PREFIX + name
    m["system"]["emitterDefs"] = emitters
    m["system"]["numEmitters"] = len(emitters)
    m["system"]["flags"] = vfx.system_flags(m)
    m["system"]["preRollMSec"] = 0
    return m


# ---- the effects --------------------------------------------------------------------------------------------

def issue(S, scale, world):
    """The press: card dust, card chips, a spark, a short warm light. `scale` 1 = first person (inches at tag_flash)."""
    kick, spark, atom = S["kickup"], S["spark"], S["atom_w" if world else "atom_v"]
    out = []
    # card dust: two soft unlit puffs drifting forward and up, pale card colour, half transparent
    d = emitter(kick, find_by_material(kick, "eq/vfx_vol_smk_wispy_swirl_lg"))
    set_material(d, DUST_UNLIT)
    one_shot(d, (2, 3), (0.35, 0.6))
    resize(d, 4.5 * scale)
    lerp = mod(d, "SIZE_LERP")
    if lerp:
        lerp["m_sizeBegin"] = [x * 0.45 for x in lerp["m_sizeEnd"]]
    velocity(d, (25 * scale, -6 * scale, 3 * scale), (55 * scale, 6 * scale, 12 * scale), turbulence=8 * scale)
    colour(d, CARD, (0.86, 0.80, 0.70), alpha=(0.5, 0.32))
    box = mod(d, "INIT_SPAWN_SHAPE_BOX")
    if box:
        box["m_dimensionsMin"] = [0.0, 0.0, 0.0, 0.0]
        box["m_dimensionsMax"] = [0.5 * scale, 0.5 * scale, 0.5 * scale, 0.0]
    out.append(d)
    # card chips: tumbling oriented paper bits flicked out of the slot
    c = emitter(kick, find_by_material(kick, PAPER, "ORIENTED_SPRITE"))
    one_shot(c, (3, 6), (0.45, 0.75))
    resize(c, 0.9 * scale)
    velocity(c, (60 * scale, -30 * scale, 8 * scale), (130 * scale, 30 * scale, 45 * scale), turbulence=25 * scale)
    colour(c, CARD, (0.88, 0.83, 0.72))
    out.append(c)
    # press spark: one bright flash sprite, very short
    s = emitter(spark, 0)
    one_shot(s, (1, 1), (0.05, 0.08))
    resize(s, 2.2 * scale)
    velocity(s, (0, 0, 0), (0, 0, 0))
    colour(s, (1.0, 0.86, 0.55), (1.0, 0.78, 0.42))
    out.append(s)
    # a warm light for 30 ms: the slot lit by the press, never a muzzle flame
    li = emitter(atom, find_by_element(atom, "LIGHT_OMNI"))
    light(li, (1.0, 0.80, 0.52), radius=(55 if not world else 90), intensity=(3.0 if not world else 6.0), life=(0.025, 0.04))
    out.append(li)
    return system("ow_issue_" + ("w" if world else "v"), S["atom_w" if world else "atom_v"], out)


def ticket(S, name, rgb, band=None):
    """A card stuck to the booked zombie's chest, held for the rest of the departure (up to 6.5 s)."""
    kick = S["kickup"]
    c = emitter(kick, find_by_material(kick, PAPER, "ORIENTED_SPRITE"))
    one_shot(c, (1, 1), (6.5, 6.5))
    resize(c, 3.5)
    velocity(c, (0, 0, 0), (0, 0, 0))
    drop(c, "INIT_ROTATION")
    colour(c, rgb, rgb)
    graph(c, "SIZE_GRAPH", [(0.0, 0.0), (0.02, 1.15), (0.04, 1.0), (0.97, 1.0), (1.0, 0.0)])
    box = mod(c, "INIT_SPAWN_SHAPE_BOX")
    if box:
        box["m_dimensionsMin"] = [0.0, 0.0, 0.0, 0.0]
        box["m_dimensionsMax"] = [0.0, 0.0, 0.0, 0.0]
    out = [c]
    if band:
        b = copy.deepcopy(c)
        resize(b, 2.2)
        colour(b, band, band)
        out.append(b)
    return system(name, kick, out)


def door(S, name, rgb, brightness):
    """Two leaves of carriage light 76 high, opening for 1.0 s and shutting, and the light they throw."""
    atom = S["atom_w"]
    out = []
    for side in (-1, 1):
        leaf = emitter(atom, find_by_material(atom, GLOW))
        one_shot(leaf, (1, 1), (1.0, 1.0))
        velocity(leaf, (0, 0, 0), (0, 0, 0))
        drop(leaf, "INIT_ROTATION", "INIT_MIRROR_TEXTURE", "INIT_ATLAS", "SIZE_LERP")
        a = mod(leaf, "INIT_ATTRIBUTES")
        a["m_sizeMin"] = [40.0, 76.0, 40.0, 0.0]
        a["m_sizeMax"] = [40.0, 76.0, 40.0, 0.0]
        a["m_useNonUniformInterpolationForSize"] = True
        # width opens in 0.25 s, holds, shuts in the last 0.25 s; height stays
        graph(leaf, "SIZE_GRAPH", [(0.0, 0.05), (0.25, 1.0), (0.75, 1.0), (1.0, 0.05)], curves={0})
        graph(leaf, "SIZE_GRAPH", [(0.0, 1.0), (1.0, 1.0)], curves={1, 2, 3, 4, 5})
        graph(leaf, "INTENSITY_GRAPH", [(0.0, 0.2), (0.2, 1.0), (0.8, 1.0), (1.0, 0.0)], scale=brightness)
        colour(leaf, rgb, rgb, alpha=(0.85, 0.85))
        box = mod(leaf, "INIT_SPAWN_SHAPE_BOX")
        if box is None:
            raise SystemExit("door leaf template has no spawn box")
        box["m_dimensionsMin"] = [0.0, side * 21.0, 38.0, 0.0]
        box["m_dimensionsMax"] = [0.0, side * 21.0, 38.0, 0.0]
        out.append(leaf)
    li = emitter(atom, find_by_element(atom, "LIGHT_OMNI"))
    light(li, rgb, radius=190.0, intensity=4.0 * brightness, life=(1.0, 1.0))
    graph(li, "INTENSITY_GRAPH", [(0.0, 0.0), (0.2, 1.0), (0.8, 1.0), (1.0, 0.0)])
    box = mod(li, "INIT_SPAWN_SHAPE_BOX")
    if box:
        box["m_dimensionsMin"] = [0.0, 0.0, 40.0, 0.0]
        box["m_dimensionsMax"] = [0.0, 0.0, 40.0, 0.0]
    out.append(li)
    return system(name, atom, out)


def probes(S):
    """Door parts alone, for the in-game A/B (plans/sz-oneway-fxprobe.json): the stock glow with only its life
    changed, the light alone, one leaf alone."""
    atom = S["atom_w"]
    g = emitter(atom, find_by_material(atom, GLOW))
    one_shot(g, (1, 1), (1.5, 1.5))
    li = emitter(atom, find_by_element(atom, "LIGHT_OMNI"))
    light(li, WARM, radius=190.0, intensity=14.0, life=(1.5, 1.5))
    leaf = door(S, "x", WARM, 1.0)["system"]["emitterDefs"][0]
    leaf["particleLife"] = {"min": 1.5, "max": 1.5}
    return [system("ow_probe_glow", atom, [g]), system("ow_probe_light", atom, [li]), system("ow_probe_leaf", atom, [leaf])]


def taken(S):
    kick = S["kickup"]
    c = emitter(kick, find_by_material(kick, PAPER, "ORIENTED_SPRITE"))
    one_shot(c, (2, 3), (1.4, 2.0))
    resize(c, 4.5)
    velocity(c, (-20, -20, 30), (20, 20, 70), turbulence=60)
    colour(c, CARD, (0.9, 0.85, 0.74))
    box = mod(c, "INIT_SPAWN_SHAPE_BOX")
    if box:
        box["m_dimensionsMin"] = [-8.0, -8.0, 30.0, 0.0]
        box["m_dimensionsMax"] = [8.0, 8.0, 60.0, 0.0]
    return system("ow_taken", kick, [c])


def tracer():
    # gfx_tracer_new, the stock rifles' tracer material, tinted by the colour stops; slower and wider than a bullet's
    # streak, with a screw wobble so it reads as a card turning in flight
    c = list(CARD)
    return {"material": "gfx_tracer_new", "fadeOverTime": True, "fadeTime": 0.06, "speed": 2600.0,
            "beamLength": 22.0, "beamWidth": 2.4, "screwRadius": 0.9, "screwDist": 26.0,
            "colors": [c + [0.0], c + [0.95], c + [1.0], c + [0.8], c + [0.0]]}


def main():
    global vfx
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--vfx-tool", required=True, help="folder of iw7_vfx.py (x64-zt-extensions t7-weapons)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--probe", action="store_true", help="also build the door-part probes (ow_probe_*)")
    a = ap.parse_args()
    sys.path.insert(0, a.vfx_tool)
    import iw7_vfx
    vfx = iw7_vfx
    S = {k: load(a.dump, v) for k, v in SRC.items()}
    systems = [
        issue(S, 1.0, world=False),
        issue(S, 1.0, world=True),
        ticket(S, "ow_ticket_2", CARD),
        ticket(S, "ow_ticket_1", CARD, band=CARD_RED),
        ticket(S, "ow_ticket_r", CARD_GREEN),
        door(S, "ow_door", WARM, 1.0),
        door(S, "ow_door_full", WHITE, 1.6),
        taken(S),
    ]
    if a.probe:
        systems += probes(S)
    v_ads = copy.deepcopy(systems[0])
    v_ads["system"]["name"] = PREFIX + "ow_issue_v_ads"
    systems.insert(1, v_ads)
    rows, report = [], []
    for m in systems:
        name = m["system"]["name"]
        data = vfx.encode(m)
        back = vfx.decode(data)        # the written stream must read back
        if back["system"]["numEmitters"] != len(m["system"]["emitterDefs"]):
            raise SystemExit("%s: read back %d emitters" % (name, back["system"]["numEmitters"]))
        p = os.path.join(a.out, "particlesystem", *name.split("/")) + ".iw7VFX"
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        rows.append("vfx," + name)
        report.append({"name": name, "bytes": len(data), "summary": vfx.summary(back)})
    os.makedirs(os.path.join(a.out, "tracer"), exist_ok=True)
    with open(os.path.join(a.out, "tracer", "szoneway_ticket.json"), "w") as f:
        json.dump(tracer(), f, indent=4)
    rows.append("tracer,szoneway_ticket")
    fx = lambda n: {"type": 1, "fx": PREFIX + n}   # noqa: E731
    pkg = {"vfx": {"viewFlashEffect": fx("ow_issue_v"), "worldFlashEffect": fx("ow_issue_w"),
                   "viewFlashADSEffect": fx("ow_issue_v_ads")}}
    for k in ("viewFlashOverchargeEffect", "viewFlashOverchargeADSEffect", "worldFlashOverchargeEffect",
              "viewShellEjectEffect", "worldShellEjectEffect", "viewLastShotEjectEffect", "worldLastShotEjectEffect",
              "viewMagEjectEffect"):
        pkg["vfx"][k] = None
    os.makedirs(os.path.join(a.out, "vfxpkg"), exist_ok=True)
    with open(os.path.join(a.out, "vfxpkg", "iw7_szoneway_zm_vfxpackage.json"), "w") as f:
        json.dump(pkg, f, indent=4)
    rows.append("vfxpkg,iw7_szoneway_zm_vfxpackage")
    with open(os.path.join(a.out, "fx.json"), "w") as f:
        json.dump({"rows": rows, "vfxPackage": "iw7_szoneway_zm_vfxpackage", "tracerType": "szoneway_ticket",
                   "systems": report}, f, indent=1)
    for r in report:
        print("%-36s %6d B  %s" % (r["name"], r["bytes"], r["summary"].get("elements")))
    print("rows:", len(rows))


if __name__ == "__main__":
    main()
