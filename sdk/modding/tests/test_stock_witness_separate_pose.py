"""Frozen-source relation and nominal math only; no engine, compilation or game."""
import hashlib
import math
from pathlib import Path
import unittest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
STOCK = EXAMPLES / "original-rig-stock-witness"
BASELINE_SHA = "649b7497af5e2f11c7ca5a959f5e0cabfa0e42fc4939675578ffc8bfe3275a7e"
SCALE_AFTER_SHA = "40e8990cb27f49244499c57ae9f19b635f0515c5c35442919af0b90c8a377ed0"
CORE_SHA = "49f7e1aa336bb2fdb73e5c36be03c213311ead4555fc9bca0d7b4e69ccdc219b"
GUARD = b'    if (!getdvarint("dedicated") || !getdvarint("sdk_original_rig_stock_witness_enable") ||\n'
OPT_IN = b'        !getdvarint("sdk_original_rig_stock_witness_separated_pose_enable") ||\n'
BEFORE = (b'    anchor = level.sdk_original_rig_probe.actors[1];\n'
          b'    origin = anchor.origin;\n'
          b'    angles = anchor.angles;\n'
          b'    anchor_entity = anchor getentitynumber();\n')
AFTER = (b'    anchor = level.sdk_original_rig_probe.actors[1];\n'
         b'    anchor_origin = anchor.origin;\n'
         b'    angles = anchor.angles;\n'
         b'    right_basis = anglestoright(angles);\n'
         b'    origin = anchor_origin + right_basis * 32 + (0, 0, 48);\n'
         b'    anchor_entity = anchor getentitynumber();\n'
         b'    print("[SDK rig stock witness] PLACEMENT_SELECTED; variant=SeparatePose; anchor_entity=" + anchor_entity + "; anchor_origin=" + anchor_origin + "; anchor_angles=" + angles + "; right_basis=" + right_basis + "; offset_right=32; offset_up=48; offset_forward=0; origin=" + origin + "; angles=" + angles + "; server_scale=3; time_ms=" + gettime() + "; pixels_pending=1.");\n')


def require_only_pose_variant(baseline, variant):
    if hashlib.sha256(baseline).hexdigest() != BASELINE_SHA:
        raise ValueError("Frozen Original source differs")
    if baseline.count(GUARD) != 1 or baseline.count(BEFORE) != 1:
        raise ValueError("Unique guard and central placement required")
    expected = baseline.replace(GUARD, GUARD + OPT_IN, 1).replace(BEFORE, AFTER, 1)
    if variant != expected:
        raise ValueError("Only the explicit pose/opt-in/journal changes are permitted")


def nominal_origin(anchor, yaw):
    # The yaw-only basis is corroborated by frozen core49f and V2's three poses.
    # This is a source/math example, never client refdef or engine observation.
    angle = math.radians(yaw)
    right = (math.sin(angle), -math.cos(angle), 0.0)
    return tuple(anchor[i] + right[i] * 32 + (48 if i == 2 else 0) for i in range(3))


class StockWitnessSeparatePoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = (STOCK / "sdk_original_rig_stock_witness.gsc").read_bytes()
        cls.variant = (STOCK / "sdk_original_rig_stock_witness_separated_pose.gsc").read_bytes()

    def test_actual_source_is_only_pose_plus_opt_in_and_journal(self):
        require_only_pose_variant(self.baseline, self.variant)

    def test_all_three_frozen_sources_keep_their_identities(self):
        self.assertEqual(hashlib.sha256(self.baseline).hexdigest(), BASELINE_SHA)
        self.assertEqual(hashlib.sha256((STOCK / "sdk_original_rig_stock_witness_scale_after.gsc").read_bytes()).hexdigest(), SCALE_AFTER_SHA)
        self.assertEqual(hashlib.sha256((EXAMPLES / "original-rig-probe/sdk_original_rig_probe.gsc").read_bytes()).hexdigest(), CORE_SHA)

    def test_original_timing_input_lifetime_cleanup_and_creation_marker_are_exact(self):
        self.assertIn(b'    actor.scale = 3;\n    actor setmodel("zmb_coin_alien");\n', self.variant)
        self.assertEqual(self.variant[self.variant.index(b'expiry(state)\n{'):],
                         self.baseline[self.baseline.index(b'expiry(state)\n{'):])
        self.assertEqual(self.variant[self.variant.index(b'watch_use(state)\n{'):self.variant.index(b'create_witness(state)\n{')],
                         self.baseline[self.baseline.index(b'watch_use(state)\n{'):self.baseline.index(b'create_witness(state)\n{')])
        marker = next(line for line in self.baseline.splitlines() if b'print("[SDK rig stock witness] WITNESS_CREATED;' in line)
        self.assertIn(marker, self.variant.splitlines())
        self.assertEqual(self.variant.count(OPT_IN), 1)

    def test_old_colocation_and_scale_after_are_causal_negative_controls(self):
        for candidate in (self.baseline, (STOCK / "sdk_original_rig_stock_witness_scale_after.gsc").read_bytes()):
            with self.subTest(candidate=hashlib.sha256(candidate).hexdigest()), self.assertRaises(ValueError):
                require_only_pose_variant(self.baseline, candidate)

    def test_changed_basis_offset_angle_anchor_scale_ttl_or_absolute_pose_is_refused(self):
        changes = ((b'right_basis * 32', b'right_basis * 64'), (b'(0, 0, 48)', b'(0, 0, 24)'),
                   (b'anglestoright(angles)', b'anglestoforward(angles)'), (b'actors[1]', b'actors[0]'),
                   (b'actor.angles = angles;', b'actor.angles = (0, 90, 0);'), (b'actor.scale = 3;', b'actor.scale = 1;'),
                   (b'    wait 10;', b'    wait 11;'),
                   (b'origin = anchor_origin + right_basis * 32 + (0, 0, 48);', b'origin = (435.546, 3517.47, 96.0679);'))
        for before, after in changes:
            with self.subTest(change=before), self.assertRaises(ValueError):
                require_only_pose_variant(self.baseline, self.variant.replace(before, after, 1))

    def test_placement_journal_is_single_explicit_and_precedes_spawn(self):
        body = self.variant[self.variant.index(b'create_witness(state)\n{'):]
        self.assertEqual(body.count(b'PLACEMENT_SELECTED;'), 1)
        self.assertLess(body.index(b'PLACEMENT_SELECTED;'), body.index(b'actor = spawn('))
        for field in (b'variant=SeparatePose', b'anchor_entity=', b'anchor_origin=', b'anchor_angles=',
                      b'right_basis=', b'offset_right=32', b'offset_up=48', b'offset_forward=0',
                      b'origin=', b'angles=', b'server_scale=3', b'time_ms=', b'pixels_pending=1'):
            self.assertIn(field, AFTER)

    def test_nominal_v2_pose_is_derived_and_not_an_absolute_gsc_coordinate(self):
        origin = nominal_origin((467.546, 3517.47, 48.0679), -90)
        for actual, expected in zip(origin, (435.546, 3517.47, 96.0679)):
            self.assertAlmostEqual(actual, expected, places=8)
        self.assertGreater(math.dist(origin, (467.546, 3517.47, 48.0679)), 0)
        for coordinate in (b'435.546', b'3517.47', b'96.0679'):
            self.assertNotIn(coordinate, self.variant)

    def test_translating_anchor_and_rotating_yaw_keep_relative_right_and_world_up(self):
        base = (10.0, 20.0, 30.0)
        self.assertEqual(nominal_origin(base, 0), (10.0, -12.0, 78.0))
        for actual, expected in zip(nominal_origin(base, 90), (42.0, 20.0, 78.0)):
            self.assertAlmostEqual(actual, expected, places=8)
        shifted = nominal_origin((110.0, 220.0, 330.0), -90)
        unshifted = nominal_origin(base, -90)
        self.assertEqual(tuple(shifted[i] - unshifted[i] for i in range(3)), (100.0, 200.0, 300.0))


if __name__ == "__main__":
    unittest.main()
