"""prove_live.py end to end against a fake game behind `forge live`: the table, the verdict rule, a model the level did not load."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import iwzlive  # noqa: E402
import prove_live  # noqa: E402
from test_iwzlive import FakeForge  # noqa: E402


class GameForge(FakeForge):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.n = 0
        self.keep_on_reload = True

    def __call__(self, args, stdin=None, timeout=0):
        if args[0] == "shot":
            self.n += 1
            png = os.path.join(tempfile.mkdtemp(), "s%d.png" % self.n)
            with open(png, "wb") as f:
                f.write(os.urandom(8000))
            name = args[args.index("--name") + 1] if "--name" in args else "x"
            return 0, json.dumps({"ok": True, "path": png, "name": name, "ms_total": 700.0}) + "\n"
        if args[0] == "reload" and not self.keep_on_reload:
            self.props.clear()
        return super().__call__(args, stdin, timeout)


class Prove(unittest.TestCase):
    def run_prove(self, fake, extra=()):
        old = iwzlive.forge_runner
        iwzlive.forge_runner = fake
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = prove_live.main(list(extra))
            return code, out.getvalue()
        finally:
            iwzlive.forge_runner = old

    def test_passes_when_everything_answers(self):
        code, text = self.run_prove(GameForge())
        self.assertEqual(code, 0, text)
        self.assertIn("T1 PASS", text)
        self.assertIn("props back True", text)

    def test_fails_when_the_props_do_not_come_back(self):
        f = GameForge()
        f.keep_on_reload = False
        code, text = self.run_prove(f)
        self.assertEqual(code, 1, text)
        self.assertIn("T1 FAIL", text)

    def test_an_unloaded_model_stops_before_the_table(self):
        code, text = self.run_prove(GameForge(refuse_models={"trashbin_01_iw6"}))
        self.assertEqual(code, 2)
        self.assertIn("models the level did not load", text)


if __name__ == "__main__":
    unittest.main()
