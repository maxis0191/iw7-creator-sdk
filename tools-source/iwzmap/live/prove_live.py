"""Proof of line T1 (docs/MAP-BUILDER-FINAL.md): live edits in a running game.

    python -B prove_live.py [--usermap <folder>] [--models a,b,c,d,e] [--center x,y,z] [--json out.json]

Starts a live session on a usermap, places 50 props of 5 stock models one by one (send to ack), moves 10, deletes 10, takes 5 frames from 5 cameras (send to
PNG file), reloads the map, and checks that the 40 remaining props are back (`list`). Prints a table and exits 0 only if every ack came, the median
ack is under 1000 ms and the median frame under 2000 ms. A model the level did not load is reported first and stops the run (change --models).

The times are wall times of the whole call a map tool makes (this process, `forge live`, the daemon, the game and back), the daemon's own measure (console write
to ack seen) is printed beside them. Needs the game: run it from the lead's session, never from a worker."""
import argparse
import hashlib
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import iwzlive  # noqa: E402

USERMAP = r"C:\Users\ezvalo\Documents\IW7-Runtime\iwz-blend\testmap1\um_final2\cp_iwz"
# stock models of the cp_zmb zone that are also static models of the template map cp_zmb (tools-source/iwzmap/scenes/station_zero_kits.json: zones has cp_zmb, template_donor,
# dump_checked), so a usermap built on that template has them loaded; sizes 15 to 42 units. Not seen in the game: the first run says which the level refuses.
MODELS = ["p7_box_cardboard_a_closed", "com_trashbag2_black", "com_restaurantchair_1", "chair_folding_iw6", "fac_trash_bin"]
CENTER = (244.0, 200.0, 0.0)          # the middle of room_a of the Blender test map (box 0..488 x 0..400, floor -16, ceiling 132)


def median(xs):
    return statistics.median(xs) if xs else float("inf")


def timed(fn):
    t = time.perf_counter()
    r = fn()
    return r, (time.perf_counter() - t) * 1000.0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--usermap", default=USERMAP)
    p.add_argument("--models", default=",".join(MODELS))
    p.add_argument("--center", default=",".join("%g" % v for v in CENTER))
    p.add_argument("--json")
    a = p.parse_args(argv)
    models = [m for m in a.models.split(",") if m]
    cx, cy, cz = (float(v) for v in a.center.split(","))
    rows = []              # (phase, what, ok, wall_ms, daemon_ms)

    def record(phase, what, ok, wall, daemon=None):
        rows.append((phase, what, bool(ok), round(wall, 1), None if daemon is None else round(daemon, 1)))

    t0 = time.perf_counter()
    s = iwzlive.Session.start(usermap=a.usermap, models=models, fresh=True)
    start_s = time.perf_counter() - t0
    print("session up in %.1f s: %s" % (start_s, json.dumps({k: s.info.get(k) for k in ("cell", "booted", "ready_s", "ping_ms")})))

    # 0. every model must be loadable
    bad = []
    for m in models:
        r = s.prop("probe_" + m[:20], m, (cx, cy, cz + 400), (0, 0, 0))
        if not r["ok"]:
            bad.append((m, r.get("why")))
    s.clear()
    if bad:
        print("models the level did not load: %s" % bad)
        return 2

    # 1. fifty props, one by one
    want = {}
    for i in range(50):
        pid = "p%02d" % i
        origin = (cx - 100 + (i % 10) * 22.0, cy - 60 + (i // 10) * 30.0, cz)
        angles = (0, (i * 37) % 360, 0)
        model = models[i % len(models)]
        r, wall = timed(lambda: s.prop(pid, model, origin, angles))
        record("place", pid, r["ok"], wall, r.get("ms"))
        if r["ok"]:
            want[pid] = {"model": model, "origin": list(origin), "angles": list(angles), "scale": 1.0}
    # 2. move ten
    for i in range(10):
        pid = "p%02d" % i
        d = want[pid]
        d["origin"] = [d["origin"][0], d["origin"][1] + 24.0, d["origin"][2]]
        r, wall = timed(lambda: s.prop(pid, d["model"], d["origin"], d["angles"]))
        record("move", pid, r["ok"], wall, r.get("ms"))
    # 3. delete ten
    for i in range(40, 50):
        pid = "p%02d" % i
        r, wall = timed(lambda: s.delete(pid))
        record("delete", pid, r["ok"], wall, r.get("ms"))
        want.pop(pid, None)
    # 4. five frames from five cameras around the props
    import math
    shas = set()
    frames = []
    for k in range(5):
        ang = k * 72.0
        x, y = cx + 170.0 * math.cos(math.radians(ang)), cy + 170.0 * math.sin(math.radians(ang))
        yaw = (ang + 180.0) % 360.0
        try:
            path, wall = timed(lambda: s.shot("prove_c%d" % k, cam=(x, y, cz + 60.0, yaw, 10.0)))
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                shas.add(hashlib.sha256(f.read()).hexdigest())
            ok = size > 5000
            frames.append(path)
            record("frame", "cam%d (%d bytes)" % (k, size), ok, wall, (s.last_shot or {}).get("ms_total"))
        except iwzlive.LiveError as e:
            record("frame", "cam%d: %s" % (k, e), False, 0.0)
    different = len(shas) >= 2
    # 5. reload, and the remaining props are back
    r, reload_wall = timed(s.reload)
    back = s.known
    missing = [pid for pid in want if pid not in back]
    off = [pid for pid in want if pid in back and not iwzlive.same(want[pid]["origin"], back[pid]["origin"]) and max(abs(x - y) for x, y in zip(want[pid]["origin"], back[pid]["origin"])) > 0.1]
    extra = [pid for pid in back if pid not in want]
    restored_ok = not missing and not off and not extra and len(back) == 40
    record("reload", "map again, %d props back (missing %d, moved %d, extra %d)" % (len(back), len(missing), len(off), len(extra)), restored_ok, reload_wall)
    path, wall = timed(lambda: s.shot("prove_after_reload"))
    record("frame", "after reload", os.path.getsize(path) > 5000, wall)

    # table
    print("\n%-8s %-46s %-4s %9s %9s" % ("phase", "what", "ok", "wall ms", "daemon ms"))
    for ph, what, ok, wall, dm in rows:
        print("%-8s %-46s %-4s %9.1f %9s" % (ph, what[:46], "yes" if ok else "NO", wall, "" if dm is None else "%.1f" % dm))
    ack_rows = [r for r in rows if r[0] in ("place", "move", "delete")]
    frame_rows = [r for r in rows if r[0] == "frame" and r[1].startswith("cam")]
    med_ack, med_frame = median([r[3] for r in ack_rows]), median([r[3] for r in frame_rows])
    all_ok = all(r[2] for r in rows)
    verdict = all_ok and med_ack < 1000 and med_frame < 2000 and different and restored_ok
    print("\nacks %d, all ok: %s, median ack %.1f ms (daemon: %.1f), max %.1f" % (len(ack_rows), all(r[2] for r in ack_rows), med_ack, median([r[4] for r in ack_rows if r[4] is not None]), max([r[3] for r in ack_rows] or [0])))
    print("frames %d, median %.1f ms, distinct frames %s; reload %.1f s, props back %s" % (len(frame_rows), med_frame, different, reload_wall / 1000.0, restored_ok))
    print("T1 %s" % ("PASS" if verdict else "FAIL"))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"rows": rows, "median_ack_ms": med_ack, "median_frame_ms": med_frame, "start_s": start_s, "reload_s": reload_wall / 1000.0, "pass": verdict}, f, indent=1)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
