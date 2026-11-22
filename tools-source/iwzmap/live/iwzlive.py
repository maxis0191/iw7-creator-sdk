"""iwzlive: the running game as the viewport of a map tool (client library and CLI over `forge live`).

    from iwzlive import Session
    s = Session.start(usermap=r"C:\\...\\um_final2\\cp_iwz", models=["com_debris_paper_iw6_02", "trashbin_01_iw6"])
    s.prop("a", "trashbin_01_iw6", (244, 200, 0), (0, 90, 0))        # visible in the game within a second
    png = s.shot("view1", cam=(100, 100, 60, 45, 0))                 # a frame back as a PNG path
    s.sync({"a": {...}, "b": {...}})                                 # only the difference to what the game has is sent
    for edit in s.watch_edits(): ...                                 # what a person placed or turned with the keys in the game
    s.save_section("section.json")                                   # in-game edits written back into a section's props

The transport is the `forge live` command (C:\\forge, one daemon that owns the game); tests give `Session` a fake runner. See docs/LIVE-LINK.md.
"""
import json
import os
import subprocess
import sys
import time

FORGE = os.environ.get("IWZ_FORGE") or r"C:\forge\forge.py"
EPS = 1e-3


class LiveError(RuntimeError):
    pass


def forge_runner(args, stdin=None, timeout=900):
    """Run `forge live <args>`; returns (exit code, stdout text). A runner is any callable with this shape."""
    r = subprocess.run([sys.executable, "-B", FORGE, "live"] + list(args), input=stdin, capture_output=True, text=True, timeout=timeout)
    if not r.stdout.strip() and r.returncode not in (0, 1):
        raise LiveError("forge live %s: exit %d: %s" % (" ".join(args[:2]), r.returncode, (r.stderr or "").strip()[-400:]))
    return r.returncode, r.stdout


def _fmt(x):
    x = float(x)
    return ("%.4f" % x).rstrip("0").rstrip(".") if x != int(x) else str(int(x))


def prop_op(pid, model, origin, angles=(0, 0, 0), scale=1.0):
    op = "prop %s %s %s %s" % (pid, model, " ".join(_fmt(v) for v in origin), " ".join(_fmt(v) for v in angles))
    if abs(float(scale) - 1.0) > EPS:
        op += " " + _fmt(scale)
    return op


def same(a, b):
    return all(abs(float(x) - float(y)) <= EPS for x, y in zip(a, b)) and len(a) == len(b)


def row_to_prop(row, index):
    """A section's props row -> (id, desc). Rows made by the game carry an `id`; others get p<index>."""
    pid = str(row.get("id") or "p%d" % index)
    ang = row.get("angles")
    if ang is None:
        ang = [row.get("pitch", 0), row.get("yaw", 0), row.get("roll", 0)]
    return pid, {"model": row["model"], "origin": [float(v) for v in row["origin"]], "angles": [float(v) for v in ang], "scale": float(row.get("scale") or 1.0)}


class Session:
    def __init__(self, runner=None):
        self.run = runner or forge_runner
        self.known = {}            # id -> {model, origin, angles, scale}: what the game has, as far as this client knows
        self.edit_pos = 0
        self.edit_log = []         # every in-game edit seen
        self.info = {}
        self.last_shot = {}

    # ---- life -----------------------------------------------------------------------------------------------------------------------------
    @classmethod
    def start(cls, usermap=None, map=None, models=(), fs_game=None, mod_ff=None, conditions="quiet", script=None, idle_min=None, fresh=False, runner=None):
        args = ["start", "--conditions", conditions]
        if usermap:
            args += ["--usermap", usermap]
        if map:
            args += ["--map", map]
        if models:
            args += ["--models", ",".join(models)]
        for flag, v in (("--fs-game", fs_game), ("--mod-ff", mod_ff), ("--script", script)):
            if v:
                args += [flag, v]
        if idle_min:
            args += ["--idle-min", str(idle_min)]
        if fresh:
            args.append("--fresh")
        s = cls(runner)
        s.info = s._json(args)
        s.refresh()
        return s

    def _json(self, args, ok_codes=(0,)):
        code, out = self.run(args)
        try:
            data = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise LiveError("forge live %s: no JSON answer: %r" % (args[0], out[-300:]))
        if code not in ok_codes or data.get("error"):
            raise LiveError("forge live %s: %s" % (args[0], data.get("error") or data))
        return data

    def status(self):
        return self._json(["status"])

    def stop(self):
        return self._json(["stop"])

    def reload(self, hard=False):
        r = self._json(["reload"] + (["--hard"] if hard else []))
        self.refresh()
        return r

    # ---- ops ------------------------------------------------------------------------------------------------------------------------------
    def send(self, ops, timeout=2.0):
        """Ops (strings of the protocol, docs/LIVE-LINK.md) -> one result dict per op ({ok, ms, ...ack fields}); never raises on a refused op."""
        ops = list(ops)
        if not ops:
            return []
        code, out = self.run(["send", "--timeout", str(timeout), "--stdin"], stdin="\n".join(ops) + "\n")
        rows = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("{"):
                rows.append(json.loads(line))
        if len(rows) == 1 and rows[0].get("error") and len(ops) != 1:
            raise LiveError("forge live send: %s" % rows[0]["error"])
        if len(rows) != len(ops):
            raise LiveError("forge live send: %d ops, %d answers: %s" % (len(ops), len(rows), out[-300:]))
        return rows

    def _one(self, op):
        r = self.send([op])[0]
        if r.get("error"):
            raise LiveError(r["error"])
        return r

    def prop(self, pid, model, origin, angles=(0, 0, 0), scale=1.0):
        r = self._one(prop_op(pid, model, origin, angles, scale))
        if r["ok"]:
            self.known[str(pid)] = {"model": model, "origin": [float(v) for v in origin], "angles": [float(v) for v in angles], "scale": float(scale)}
        return r

    def delete(self, pid):
        r = self._one("del %s" % pid)
        if r["ok"]:
            self.known.pop(str(pid), None)
        return r

    def clear(self):
        r = self._one("clear")
        if r["ok"]:
            self.known = {}
        return r

    def camera(self, x, y, z, yaw, pitch):
        return self._one("cam %s %s %s %s %s" % tuple(_fmt(v) for v in (x, y, z, yaw, pitch)))

    def light(self, targetname, intensity, rgb=None, radius=None):
        op = "light %s %s" % (targetname, _fmt(intensity))
        if rgb is not None:
            op += " %s %s %s" % tuple(_fmt(v) for v in rgb)
            if radius is not None:
                op += " " + _fmt(radius)
        return self._one(op)

    def hud(self, text):
        return self._one("hud " + text)

    def edit_mode(self, on, palette=None, grid=None):
        ops = []
        if palette:
            ops.append("palette " + palette)
        if grid:
            ops.append("grid " + _fmt(grid))
        ops.append("edit %d" % (1 if on else 0))
        return self.send(ops)

    def fly(self, on):
        return self._one("fly %d" % (1 if on else 0))

    def refresh(self):
        """What the game has: the `list` answer replaces this client's picture."""
        r = self._one("list")
        known = {}
        for p in r.get("props") or []:
            o = [float(v) for v in p["origin"].split(",")]
            a = [float(v) for v in p["angles"].split(",")]
            known[p["id"]] = {"model": p["model"], "origin": o, "angles": a, "scale": self.known.get(p["id"], {}).get("scale", 1.0)}
        self.known = known
        return known

    def sync(self, props):
        """props: {id: {model, origin, angles, scale}}. Sends only what differs from what the game has: new and changed ids as `prop`, ids the game has and
        props lacks as `del`. Returns {sent, added, changed, deleted, failed: [results]}."""
        ops, added, changed, deleted = [], 0, 0, 0
        for pid, d in props.items():
            pid = str(pid)
            cur = self.known.get(pid)
            ang = d.get("angles") or [0, 0, 0]
            scale = float(d.get("scale") or 1.0)
            if cur is None:
                added += 1
            elif cur["model"] != d["model"] or not same(cur["origin"], d["origin"]) or not same(cur["angles"], ang) or abs(cur["scale"] - scale) > EPS:
                changed += 1
            else:
                continue
            ops.append(prop_op(pid, d["model"], d["origin"], ang, scale))
        for pid in sorted(set(self.known) - set(str(k) for k in props)):
            ops.append("del " + pid)
            deleted += 1
        res = self.send(ops, timeout=3.0) if ops else []
        failed = []
        for op, r in zip(ops, res):
            if not r["ok"]:
                failed.append(dict(r, op=op))
                continue
            t = op.split()
            if t[0] == "del":
                self.known.pop(t[1], None)
            else:
                self.known[t[1]] = {"model": t[2], "origin": [float(v) for v in t[3:6]], "angles": [float(v) for v in t[6:9]], "scale": float(t[9]) if len(t) > 9 else 1.0}
        return {"sent": len(ops), "added": added, "changed": changed, "deleted": deleted, "failed": failed}

    def sync_section(self, section_path):
        with open(section_path, encoding="utf-8-sig") as f:
            doc = json.load(f)
        return self.sync(dict(row_to_prop(r, i) for i, r in enumerate(_rows(doc))))

    # ---- frames ---------------------------------------------------------------------------------------------------------------------------
    def shot(self, name=None, cam=None, out=None, timeout=8.0):
        """A frame as a PNG file: optionally the camera (x, y, z, yaw, pitch) first. Returns the path (copied to `out` when given)."""
        args = ["shot", "--timeout", str(timeout)]
        if name:
            args += ["--name", name]
        if cam:
            args.append("--cam=" + ",".join(_fmt(v) for v in cam))      # the = form: a value that starts with - is not an option
        if out:
            args += ["--out", out]
        code, text = self.run(args)
        try:
            r = json.loads(text.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise LiveError("forge live shot: no JSON answer: %r" % text[-300:])
        if not r.get("ok"):
            raise LiveError("forge live shot: %s" % (r.get("error") or r.get("why") or r))
        self.last_shot = r
        return r.get("copy") or r["path"]

    # ---- in-game edits --------------------------------------------------------------------------------------------------------------------
    def edits(self, wait=0.0):
        """The in-game edits since the last call (LIVE edit lines: op place/turn/delete, id, model, origin, angles), also applied to `known`."""
        r = self._json(["edits", "--since", str(self.edit_pos), "--wait", str(wait)])
        self.edit_pos = r["next"]
        for e in r["edits"]:
            self._apply(e)
        self.edit_log += r["edits"]
        return r["edits"]

    def _apply(self, e):
        pid = e.get("id")
        if e.get("op") == "delete":
            self.known.pop(pid, None)
        elif e.get("op") in ("place", "turn", "move") and pid:
            old = self.known.get(pid, {})
            self.known[pid] = {"model": e.get("model") or old.get("model", ""), "origin": [float(v) for v in e["origin"].split(",")],
                               "angles": [float(v) for v in e["angles"].split(",")], "scale": old.get("scale", 1.0)}

    def watch_edits(self, poll=1.0, until=None):
        """Yields every in-game edit as a record, as it happens. `until`: a callable that returns True to stop (checked between polls)."""
        while not (until and until()):
            for e in self.edits(wait=poll):
                yield e

    def save_section(self, section_path, zone="live"):
        """The in-game edits seen so far written into the section file's `props` (see apply_edits_to_section)."""
        self.edits()
        return apply_edits_to_section(section_path, self.edit_log, zone=zone)


# ---- sections -------------------------------------------------------------------------------------------------------------------------------------

def _rows(doc):
    if isinstance(doc, dict) and isinstance(doc.get("props"), list):
        return doc["props"]
    if isinstance(doc, list):
        return doc
    raise LiveError("a section is a JSON object with a `props` list (or a bare list of rows)")


def apply_edits_to_section(section_json_path, edits, zone="live"):
    """In-game edits (records of `LIVE edit`: op place|turn|move|delete, id, model, origin, angles) into the section's `props` list.
    A row is {id, zone, model, origin, angles [pitch, yaw, roll], scale, static, clip}; rows that have no id are known to the game as p<index>, and an edit of
    such a row gives it that id. A placed prop is appended (zone: `zone`), a turn or move updates the row, a delete removes it. Written back atomically;
    returns {placed, moved, deleted, unknown}."""
    with open(section_json_path, encoding="utf-8-sig") as f:
        doc = json.load(f)
    rows = _rows(doc)
    ids = {}
    for i, r in enumerate(rows):
        ids[str(r.get("id") or "p%d" % i)] = r
    out = {"placed": 0, "moved": 0, "deleted": 0, "unknown": 0}
    for e in edits:
        pid, op = e.get("id"), e.get("op")
        if not pid or op not in ("place", "turn", "move", "delete"):
            continue
        if op == "delete":
            r = ids.pop(pid, None)
            if r is None:
                out["unknown"] += 1
                continue
            rows.remove(r)
            out["deleted"] += 1
            continue
        o = [round(float(v), 3) for v in e["origin"].split(",")]
        a = [round(float(v), 3) for v in e["angles"].split(",")]
        r = ids.get(pid)
        if r is None:
            r = {"id": pid, "zone": zone, "model": e["model"], "origin": o, "angles": a, "scale": 1.0, "static": True, "clip": None}
            rows.append(r)
            ids[pid] = r
            out["placed"] += 1
        else:
            r["id"] = pid
            r["origin"], r["angles"] = o, a
            for k in ("pitch", "yaw", "roll"):
                r.pop(k, None)
            out["moved"] += 1
    tmp = section_json_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, section_json_path)
    return out


# ---- command line -----------------------------------------------------------------------------------------------------------------------------------

def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="the running game as the viewport of a map tool (over `forge live`)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--usermap")
    s.add_argument("--map")
    s.add_argument("--models", default="")
    s.add_argument("--fresh", action="store_true")
    s = sub.add_parser("sync", help="send a section's props (only the difference)")
    s.add_argument("section")
    s = sub.add_parser("shot")
    s.add_argument("--name")
    s.add_argument("--cam", help="x,y,z,yaw,pitch (write --cam=-10,... when the first value is negative)")
    s.add_argument("--out")
    s = sub.add_parser("save", help="write the in-game edits into a section file")
    s.add_argument("section")
    s.add_argument("--zone", default="live")
    sub.add_parser("status")
    sub.add_parser("stop")
    sub.add_parser("reload")
    a = p.parse_args(argv)
    if a.cmd == "start":
        s = Session.start(usermap=a.usermap, map=a.map, models=[m for m in a.models.split(",") if m], fresh=a.fresh)
        print(json.dumps(s.info))
        return 0
    s = Session()
    if a.cmd == "sync":
        s.refresh()
        r = s.sync_section(a.section)
        print(json.dumps(r))
        return 0 if not r["failed"] else 1
    if a.cmd == "shot":
        print(s.shot(a.name, [float(x) for x in a.cam.split(",")] if a.cam else None, a.out))
        return 0
    if a.cmd == "save":
        print(json.dumps(s.save_section(a.section, a.zone)))
        return 0
    print(json.dumps(getattr(s, a.cmd)()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
