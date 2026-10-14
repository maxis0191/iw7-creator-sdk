"""Guard the one-variable source experiment, not GSC execution or rendering."""
import hashlib
from pathlib import Path
import unittest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/original-rig-stock-witness"
BASELINE_SHA = "649b7497af5e2f11c7ca5a959f5e0cabfa0e42fc4939675578ffc8bfe3275a7e"
VARIANT_SHA = "40e8990cb27f49244499c57ae9f19b635f0515c5c35442919af0b90c8a377ed0"
BEFORE = b'    actor.scale = 3;\n    actor setmodel("zmb_coin_alien");\n'
AFTER = b'    actor setmodel("zmb_coin_alien");\n    actor.scale = 3;\n'


def require_single_change(baseline, variant):
    if hashlib.sha256(baseline).hexdigest() != BASELINE_SHA:
        raise ValueError("Pinned original witness source differs")
    if baseline.count(BEFORE) != 1:
        raise ValueError("Exactly one original order required")
    if variant != baseline.replace(BEFORE, AFTER, 1):
        raise ValueError("Variant must contain only the scale/setmodel permutation")


class StockWitnessScaleAfterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = (EXAMPLE / "sdk_original_rig_stock_witness.gsc").read_bytes()
        cls.variant = (EXAMPLE / "sdk_original_rig_stock_witness_scale_after.gsc").read_bytes()

    def test_actual_variant_has_only_the_order_change(self):
        require_single_change(self.baseline, self.variant)
        self.assertEqual(hashlib.sha256(self.variant).hexdigest(), VARIANT_SHA)

    def test_original_source_drift_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Pinned original"):
            require_single_change(self.baseline + b"\n", self.variant)

    def test_unchanged_order_is_refused(self):
        with self.assertRaisesRegex(ValueError, "only the"):
            require_single_change(self.baseline, self.baseline)

    def test_extra_lifetime_or_pose_change_is_refused(self):
        for original, changed in ((b"    wait 10;", b"    wait 11;"),
                                  (b"    actor.angles = angles;", b"    actor.angles = (0, 0, 0);")):
            with self.subTest(change=original), self.assertRaisesRegex(ValueError, "only the"):
                require_single_change(self.baseline, self.variant.replace(original, changed, 1))


if __name__ == "__main__":
    unittest.main()
