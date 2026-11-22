"""iwzlive against a fake `forge live` (no game, no Forge): the picture of what the game has, the difference sync, frames, in-game edits into a section."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import iwzlive  # noqa: E402


class FakeForge:
    """Answers the `forge live` commands from a dict of props, as the daemon and the game would."""

    def __init__(self, refuse_models=()):
        self.props = {}                   # id -> (model, origin, angles)
        self.edits = []
        self.calls = []
        self.refuse = set(refuse_models)

    def __call__(self, args, stdin=None, timeout=0):
        self.calls.append((list(args), stdin))
        cmd = args[0]
        if cmd == "start":
            return 0, json.dumps({"passed": True, "live": True, "cell": "k1"}) + "\n"
        if cmd == "status":
            return 0, json.dumps({"live": True, "props": len(self.props)}) + "\n"
        if cmd == "reload":
            return 0, json.dumps({"passed": True, "reload_s": 2.0}) + "\n"
        if cmd == "edits":
            since = int(args[args.index("--since") + 1])
            return 0, json.dumps({"edits": self.edits[since:], "next": len(self.edits), "passed": True}) + "\n"
        if cmd == "shot":
            out = args[args.index("--out") + 1] if "--out" in args else None
            png = os.path.join(tempfile.gettempdir(), "fake_shot.png")
            r = {"ok": True, "path": png, "passed": True}
            if out:
                r["copy"] = out
            return 0, json.dumps(r) + "\n"
        if cmd == "send":
            rows, bad = [], False
            for i, line in enumerate((stdin or "").splitlines()):
                t = line.split()
                r = {"seq": i + 1, "op": t[0], "ok": True, "ms": 12.5}
                if t[0] == "prop":
                    if t[2] in self.refuse:
                        r.update(ok=False, why="model_not_loaded")
                    else:
                        self.props[t[1]] = (t[2], [float(v) for v in t[3:6]], [float(v) for v in t[6:9]])
                elif t[0] == "del":
                    if t[1] in self.props:
                        del self.props[t[1]]
                    else:
                        r.update(ok=False, why="unknown_id")
                elif t[0] == "clear":
                    self.props.clear()
                elif t[0] == "list":
                    r["props"] = [{"id": k, "model": v[0], "origin": ",".join("%g" % x for x in v[1]), "angles": ",".join("%g" % x for x in v[2])} for k, v in sorted(self.props.items())]
                bad = bad or not r["ok"]
                rows.append(r)
            return (1 if bad else 0), "".join(json.dumps(r) + "\n" for r in rows)
        raise AssertionError(args)

    def sent_ops(self):
        return [ln for a, s in self.calls if a[0] == "send" for ln in (s or "").splitlines()]


class Library(unittest.TestCase):
    def setUp(self):
        self.f = FakeForge()
        self.s = iwzlive.Session.start(usermap="x", models=["m_one", "m_two"], runner=self.f)

    def test_start_passes_the_models_and_reads_the_game(self):
        args = self.f.calls[0][0]
        self.assertEqual(args[0], "start")
        self.assertIn("m_one,m_two", args)
        self.assertEqual(self.s.info["cell"], "k1")
        self.assertEqual(self.s.known, {})

    def test_prop_delete_clear(self):
        r = self.s.prop("a", "m_one", (1, 2.5, 3), (0, 90, 0))
        self.assertTrue(r["ok"])
        self.assertEqual(self.f.sent_ops()[-1], "prop a m_one 1 2.5 3 0 90 0")
        self.assertEqual(self.s.known["a"]["origin"], [1, 2.5, 3])
        self.s.prop("b", "m_two", (0, 0, 0), scale=2)
        self.assertEqual(self.f.sent_ops()[-1], "prop b m_two 0 0 0 0 0 0 2")
        self.assertTrue(self.s.delete("a")["ok"])
        self.assertNotIn("a", self.s.known)
        self.s.clear()
        self.assertEqual(self.s.known, {})

    def test_a_refused_model_is_a_result_not_an_exception_and_is_not_recorded(self):
        self.f.refuse.add("bad")
        r = self.s.prop("a", "bad", (0, 0, 0))
        self.assertEqual((r["ok"], r["why"]), (False, "model_not_loaded"))
        self.assertEqual(self.s.known, {})

    def test_sync_sends_only_the_difference(self):
        want = {"a": {"model": "m_one", "origin": [0, 0, 0], "angles": [0, 0, 0]}, "b": {"model": "m_two", "origin": [10, 0, 0], "angles": [0, 90, 0]}}
        r = self.s.sync(want)
        self.assertEqual((r["sent"], r["added"], r["changed"], r["deleted"]), (2, 2, 0, 0))
        n = len(self.f.sent_ops())
        r = self.s.sync(want)                                           # nothing changed: nothing sent
        self.assertEqual(r["sent"], 0)
        self.assertEqual(len(self.f.sent_ops()), n)
        want["b"]["origin"] = [10, 0, 5]
        want["c"] = {"model": "m_one", "origin": [1, 1, 1]}
        del want["a"]
        r = self.s.sync(want)
        self.assertEqual((r["sent"], r["added"], r["changed"], r["deleted"]), (3, 1, 1, 1))
        self.assertEqual(sorted(self.f.props), ["b", "c"])
        self.assertEqual(sorted(self.s.known), ["b", "c"])

    def test_sync_reports_failures_and_retries_them_next_time(self):
        self.f.refuse.add("bad")
        r = self.s.sync({"a": {"model": "bad", "origin": [0, 0, 0]}, "b": {"model": "m_one", "origin": [0, 0, 0]}})
        self.assertEqual(len(r["failed"]), 1)
        self.assertEqual(r["failed"][0]["why"], "model_not_loaded")
        self.assertEqual(sorted(self.s.known), ["b"])
        self.f.refuse.clear()
        self.assertEqual(self.s.sync({"a": {"model": "bad", "origin": [0, 0, 0]}, "b": {"model": "m_one", "origin": [0, 0, 0]}})["sent"], 1)

    def test_refresh_reads_what_the_game_has(self):
        self.f.props["z"] = ("m_one", [5, 6, 7], [0, 45, 0])
        self.s.refresh()
        self.assertEqual(self.s.known["z"]["origin"], [5, 6, 7])
        self.assertEqual(self.s.sync({"z": {"model": "m_one", "origin": [5, 6, 7], "angles": [0, 45, 0]}})["sent"], 0)

    def test_shot_returns_a_png_path(self):
        self.assertTrue(self.s.shot("v1", cam=(1, 2, 3, 90, -5)).endswith(".png"))
        args = self.f.calls[-1][0]
        self.assertIn("--cam=1,2,3,90,-5", args)
        self.s.shot("v3", cam=(-3400, 2730, 60.5, 0, 0))
        self.assertIn("--cam=-3400,2730,60.5,0,0", self.f.calls[-1][0])
        self.assertEqual(self.s.shot("v2", out=r"C:\x\v2.png"), r"C:\x\v2.png")

    def test_edits_update_known_and_watch_yields_them(self):
        self.f.edits += [{"op": "place", "id": "e1", "model": "m_one", "origin": "8,16,0", "angles": "0,15,0"}]
        got = list(self.s.watch_edits(poll=0, until=iter([False, True]).__next__))
        self.assertEqual([e["id"] for e in got], ["e1"])
        self.assertEqual(self.s.known["e1"]["origin"], [8, 16, 0])
        self.f.edits += [{"op": "delete", "id": "e1"}]
        self.assertEqual(len(self.s.edits()), 1)
        self.assertNotIn("e1", self.s.known)
        self.assertEqual(self.s.edits(), [])


class Sections(unittest.TestCase):
    def section(self, rows):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "section.json")
        with open(p, "w") as f:
            json.dump({"zone": "z", "props": rows}, f)
        return p

    def test_rows_to_game_ids_and_back(self):
        rows = [{"zone": "room_a", "model": "m_one", "origin": [0, 0, 0], "angles": [0, 90, 0], "scale": 1, "static": True, "clip": None},
                {"id": "named", "zone": "room_a", "model": "m_two", "origin": [5, 5, 5], "pitch": 1, "yaw": 2, "roll": 3}]
        p = self.section(rows)
        f = FakeForge()
        s = iwzlive.Session.start(runner=f)
        r = s.sync_section(p)
        self.assertEqual(r["added"], 2)
        self.assertEqual(sorted(f.props), ["named", "p0"])
        self.assertEqual(f.props["named"][2], [1, 2, 3])

    def test_in_game_edits_written_into_the_section(self):
        rows = [{"zone": "room_a", "model": "m_one", "origin": [0, 0, 0], "angles": [0, 90, 0], "scale": 1, "static": True, "clip": None},
                {"zone": "room_a", "model": "m_two", "origin": [5, 5, 5], "angles": [0, 0, 0], "scale": 1, "static": True, "clip": None}]
        p = self.section(rows)
        edits = [{"op": "place", "id": "e1", "model": "m_one", "origin": "8,16,0", "angles": "0,15,0"},
                 {"op": "turn", "id": "e1", "model": "m_one", "origin": "8,16,0", "angles": "0,30,0"},
                 {"op": "turn", "id": "p0", "model": "m_one", "origin": "0,0,0", "angles": "0,105,0"},
                 {"op": "delete", "id": "p1"},
                 {"op": "delete", "id": "nope"},
                 {"op": "refused", "why": "no_palette"}]
        r = iwzlive.apply_edits_to_section(p, edits, zone="room_b")
        self.assertEqual(r, {"placed": 1, "moved": 2, "deleted": 1, "unknown": 1})
        out = json.load(open(p))["props"]
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["angles"], [0, 105, 0])
        self.assertEqual(out[0]["id"], "p0")
        new = out[1]
        self.assertEqual((new["id"], new["zone"], new["model"], new["origin"], new["angles"]), ("e1", "room_b", "m_one", [8, 16, 0], [0, 30, 0]))
        # the document rebuilds to the same placement: what the game would be sent from it
        s = iwzlive.Session.start(runner=FakeForge())
        s.sync_section(p)
        self.assertEqual(sorted(s.known), ["e1", "p0"])
        self.assertTrue(iwzlive.same(s.known["e1"]["origin"], [8, 16, 0]))

    def test_a_bare_list_and_a_bad_document(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "s.json")
        json.dump([{"model": "m_one", "origin": [0, 0, 0], "angles": [0, 0, 0]}], open(p, "w"))
        iwzlive.apply_edits_to_section(p, [{"op": "place", "id": "e1", "model": "m_two", "origin": "1,2,3", "angles": "0,0,0"}])
        self.assertEqual(len(json.load(open(p))), 2)
        json.dump({"nope": 1}, open(p, "w"))
        with self.assertRaises(iwzlive.LiveError):
            iwzlive.apply_edits_to_section(p, [])


if __name__ == "__main__":
    unittest.main()
