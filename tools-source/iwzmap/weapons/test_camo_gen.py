"""Tests for camo_gen.py:  python -B -m unittest test_camo_gen  (from this folder)."""
import json
import os
import shutil
import tempfile
import unittest

import numpy as np

import camo_gen as cg

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "camos.json"), encoding="utf-8") as _f:
    SPEC = json.load(_f)
TEXCONV = os.environ.get("IWZ_TEXCONV") or os.path.join(
    os.path.expanduser("~"), "Documents", "IW7-Tools", "texconv-may2026", "texconv.exe")
STOCK_CAMO = os.environ.get("IWZ_STOCK_CAMO01") or os.path.join(
    os.path.expanduser("~"), "Documents", "IW7-Runtime", "iwz-map-ref-a", "dump", "techsets_global_mp",
    "materials", "camo_01.json")

_CACHE = {}


def full(key):
    """The camo at the spec's size (the size the bands are tuned for), generated once per test run."""
    if key not in _CACHE:
        _CACHE[key] = cg.generate(SPEC, key)
    return _CACHE[key]


class Determinism(unittest.TestCase):
    def test_same_seed_same_texels(self):
        for key in SPEC["camos"]:
            _, a, pa = cg.generate(SPEC, key, size=256)
            _, b, pb = cg.generate(SPEC, key, size=256)
            for k in ("c", "n", "sg", "e", "o"):
                np.testing.assert_array_equal(cg.to_u8(pa[k]), cg.to_u8(pb[k]), err_msg="%s %s" % (key, k))
            for k in a["motion"]:
                np.testing.assert_array_equal(a["motion"][k], b["motion"][k])

    def test_other_seed_other_texels(self):
        for key in SPEC["camos"]:
            _, _, pa = cg.generate(SPEC, key, size=256, seed=1)
            _, _, pb = cg.generate(SPEC, key, size=256, seed=2)
            self.assertFalse(np.array_equal(cg.to_u8(pa["c"]), cg.to_u8(pb["c"])), key)


class Tiling(unittest.TestCase):
    def test_every_image_wraps_without_a_seam(self):
        limit = SPEC.get("seam_ratio_max", 1.05)
        for key in SPEC["camos"]:
            _, L, p = full(key)
            images = {k: v for k, v in p.items() if not k.startswith("_")}
            images.update(L["motion"])
            for k, v in images.items():
                edge, ratio = cg.seam_metric(v)
                self.assertLessEqual(ratio, limit, "%s %s: wrap step %.4f, ratio %.3f" % (key, k, edge, ratio))

    def test_metric_catches_a_real_seam(self):
        rng = np.random.default_rng(0)
        ramp = np.tile(np.linspace(0, 1, 256, dtype=np.float32), (256, 1))
        self.assertGreater(cg.seam_metric(ramp)[1], 5.0)
        noise = rng.standard_normal((260, 260)).astype(np.float32)
        smooth = np.cumsum(np.cumsum(noise, 0), 1)[:256, :256]       # smooth and not periodic
        self.assertGreater(cg.seam_metric(smooth)[1], 1.05)
        periodic = cg.fft_noise(rng, 256, 5.0, 20.0, 256 / 180.0)
        self.assertLessEqual(cg.seam_metric(periodic)[1], 1.05)


class Coverage(unittest.TestCase):
    def test_role_shares_inside_their_bands(self):
        for key in SPEC["camos"]:
            cfg, L, _ = full(key)
            _, checks = cg.measure(L, cfg)
            self.assertTrue(checks, key)
            for nm, c in checks.items():
                self.assertTrue(c["ok"], "%s %s share %.4f outside %s" % (key, nm, c["share"], c["band"]))

    def test_carrier_keeps_plain_enamel_majority(self):
        _, L, _ = full("carrier")
        plain = float(np.isin(L["roles"], [0, 1]).mean())             # enamel + worn enamel
        self.assertGreaterEqual(plain, 0.60)

    def test_mercury_arc_restraint(self):
        cfg, L, _ = full("mercury")
        shares, _ = cg.measure(L, cfg)
        arc = shares["core"] + shares["body"] + shares["teal"]
        self.assertLessEqual(arc, cfg["arc_max_share"])
        # the scrolled arc (layer M) stays restrained at every sampled moment of 20 s
        for t in np.linspace(0, 20, 21):
            m = cg.motion_frames(L, cfg, SPEC, float(t))
            self.assertLessEqual(float((m.max(-1) > 0.15).mean()), cfg["arc_max_share"])

    def test_no_amber_in_mercury_emissive(self):
        _, L, _ = full("mercury")
        e = L["emissive"].reshape(-1, 3)
        lit = e[e.max(1) > 0.05]
        # amber has red > blue; every arc texel is violet, white or teal (blue >= red)
        self.assertTrue(np.all(lit[:, 2] + 1e-3 >= lit[:, 0]))

    def test_no_blue_in_carrier(self):
        _, L, _ = full("carrier")
        a = L["albedo"].reshape(-1, 3)
        self.assertTrue(np.all(a[:, 2] <= np.maximum(a[:, 0], a[:, 1]) + 0.03))


class Encoding(unittest.TestCase):
    def test_gloss_curve_matches_roughness(self):
        for r in (0.2, 0.24, 0.35, 0.55):
            g = float(cg.gloss_from_roughness(r))
            power = 2 ** (20 * (1 - np.sqrt(1 - g))) + 2
            alpha = r * r
            self.assertAlmostEqual(power, 2 / alpha ** 2 - 2, delta=0.02 * (2 / alpha ** 2))

    def test_hybrid_normal_decodes_both_ways(self):
        rng = np.random.default_rng(3)
        v = rng.normal(0, 0.3, (64, 3)).astype(np.float32)
        v[:, 2] = 1.0
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        enc = cg.encode_normal(v[None], "hybrid")[0]
        g, a = enc[:, 1] * 2 - 1, enc[:, 3] * 2 - 1
        px, py = (g + a) / 2, (g - a) / 2                                 # stock packed_nog decode
        z = 1 - np.abs(px) - np.abs(py)
        dec = np.stack([px, py, z], 1)
        dec /= np.linalg.norm(dec, axis=1, keepdims=True)
        np.testing.assert_allclose(dec, v, atol=1e-5)
        np.testing.assert_allclose(enc[:, 0] * 2 - 1, v[:, 0], atol=1e-6)    # R = x for an xyz reader

    @unittest.skipUnless(os.path.isfile(TEXCONV), "texconv not found")
    def test_dds_headers(self):
        out = tempfile.mkdtemp(prefix="camo_test_")
        try:
            rc = cg.main([os.path.join(HERE, "camos.json"), "--out", out, "--texconv", TEXCONV, "--size", "256",
                          "--no-motion-preview"])
            self.assertIn(rc, (0, 2))                                     # bands are tuned at 1024, not 256
            with open(os.path.join(out, "camo_report.json"), encoding="utf-8") as f:
                rep = json.load(f)
            want = {"c": 71, "n": 98, "sg": 77, "e": 71, "o": 80, "m": 71, "m1": 71, "m2": 71}
            seen = 0
            for key, rec in rep["camos"].items():
                for name in os.listdir(os.path.join(out, "images")):
                    if not name.startswith(rec["image_prefix"] + "_"):
                        continue
                    suffix = name[len(rec["image_prefix"]) + 1:-4]
                    h = cg.read_dds_header(os.path.join(out, "images", name))
                    self.assertEqual((h["width"], h["height"], h["mips"], h["dxgi"]), (256, 256, 9, want[suffix]), name)
                    seen += 1
            self.assertEqual(seen, 6 + 7)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    @unittest.skipUnless(os.path.isfile(STOCK_CAMO), "stock camo_01.json not found")
    def test_material_clone(self):
        with open(STOCK_CAMO, encoding="utf-8") as f:
            stock = json.load(f)
        m = cg.build_material(stock, "iwz_camo_carrier", 1.2056, 6.0)
        layer1 = {t["typeHash"]: t["image"] for t in m["textureTable"] if t["lastCharacter"] == 49}
        self.assertEqual(layer1, {3054311504: "iwz_camo_carrier_c", 2486480606: "iwz_camo_carrier_n",
                                  3532022562: "iwz_camo_carrier_sg", 3230247958: "iwz_camo_carrier_e",
                                  1253113093: "iwz_camo_carrier_o"})
        base = {t["typeHash"]: t["image"] for t in stock["textureTable"] if t["lastCharacter"] != 49}
        self.assertEqual(base, {t["typeHash"]: t["image"] for t in m["textureTable"] if t["lastCharacter"] != 49})
        consts = {(c["name"], c["nameHash"]): c["literal"] for c in m["constantTable"]}
        self.assertEqual(consts[("emissivePara", 1323547990)], [6.0, 0.0, 0.0, 0.0])
        self.assertEqual(consts[("secondarySam", 4044143062)], [1.2056, 1.2056, 0.0, 0.0])
        moving = cg.build_material(stock, "iwz_camo_carrier", 2.0, 6.0, (0.5, -0.25), (0.0, 1.5))
        consts = {(c["name"], c["nameHash"]): c["literal"] for c in moving["constantTable"]}
        self.assertEqual(consts[("secondarySam", 4044143062)], [2.0, 2.0, 0.25, -0.125])  # S * V = tiles/s
        self.assertEqual(consts[("secondarySam", 28846999)][:2], [0.0, 1.5])
        self.assertEqual(m["techniqueSet->name"], stock["techniqueSet->name"])


if __name__ == "__main__":
    unittest.main()
