"""Project content safety/geometry Source checks, never a GSC/physics simulator."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

SDK = Path(__file__).resolve().parents[1]
PROJECT = SDK / "examples/original-authoring/platform-contact"


def body(text, name):
    return re.search(r"^" + name + r"\([^\n]*\)\n\{\n(.*?)^\}", text, re.M | re.S).group(1)


class PlatformContentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (PROJECT / "sdk_author_platform.gsc").read_text()

    def test_same_author_data_contract_and_local_geometry_only(self):
        spec = importlib.util.spec_from_file_location("platform_authoring", SDK / "creator_authoring.py")
        author = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(author)
        manifest = json.loads((PROJECT / "manifest.json").read_text())
        report = author.select(PROJECT, SDK.parents[1], manifest=manifest)
        self.assertTrue(report["source_contract_valid"])
        self.assertEqual(report["source_scene"]["placement"],
                         {"offset_forward_right_up": [0, 0, 96], "angles": [0, 0, 0], "scale": 1})
        geometry = json.loads((PROJECT / "geometry.source.json").read_text())
        surface = geometry["surfaces"][0]
        self.assertEqual((len(surface["vertices"]), len(surface["triangles"])), (24, 12))
        self.assertEqual(geometry["bounds"], {"midpoint": [0, 0, 8], "half_size": [128, 128, 8]})
        self.assertFalse(report["source_scene"]["physics_serialized"])

    def test_init_cannot_spawn_and_fixture_must_pass_actual_anchor(self):
        self.assertNotIn("spawn(", body(self.source, "init"))
        create = body(self.source, "create_visual")
        for declaration in ('anchor + (0, 0, 96)', 'actor.angles = (0, 0, 0);', 'actor.scale = 1;',
                            'actor notsolid();', 'actor makeusable();', 'actor setuserange(160);', 'actor setusefov(360);'):
            self.assertIn(declaration, create)
        self.assertIn('isdefined(level.sdk_author_platform)', create)

    def test_retail_trigger_is_the_only_counter_writer_and_no_input_driver(self):
        interact = body(self.source, "interact")
        self.assertEqual(self.source.count('state.uses++;'), 1)
        self.assertLess(interact.index('self waittill("trigger", player);'), interact.index('state.uses++;'))
        for guard in ('!state.armed', 'state.uses != 0', 'player != state.owner', 'state.model != self',
                      'gettime() <= state.armed_ms', '!owned(state)'):
            self.assertIn(guard, interact)
        self.assertNotIn('usebuttonpressed(', self.source)
        self.assertNotIn('notify(', self.source)
        self.assertNotRegex(self.source, r'collision_(?:create|clear|destroy)')
        self.assertNotIn('state.uses++', body(self.source, "arm_use"))

    def test_ack_identity_and_teardown_ownership_are_explicit(self):
        owned = body(self.source, "owned")
        for guard in ('level.sdk_author_platform == state', 'sdk_author_platform_token == state.token',
                      'sdk_author_platform_instance == state.instance_id', 'getentitynumber() == state.entity'):
            self.assertIn(guard, owned)
        teardown = body(self.source, "teardown")
        self.assertLess(teardown.index('if (!owned(state))'), teardown.index('state.model delete();'))
        self.assertIn('RESTORE_PENDING', teardown)
        self.assertIn('return false;', teardown[teardown.index('if (!owned(state))'):teardown.index('state.model delete();')])
        for key in ('last_player', 'last_token', 'last_entity', 'last_use_ms'):
            self.assertIn('state.' + key + ' =', body(self.source, "interact"))

    def test_private_context_and_no_measured_readiness_claim(self):
        context = body(self.source, "context")
        for guard in ('getdvarint("sdk_author_platform_enable") == 1', 'getdvar("fs_game") == "mods/sdk_author_platform"',
                      'getdvarint("net_port") != 27016', 'getdvarint("sv_maxclients") == 1',
                      'getdvarint("sv_cheats") == 0', 'getdvarint("g_inactivity") == 0'):
            self.assertIn(guard, context)
        markers = [line for line in self.source.splitlines() if 'print(' in line]
        self.assertTrue(all('runtime_ready=0' in line for line in markers))
        self.assertNotIn('runtime_ready=1', self.source)


if __name__ == "__main__":
    unittest.main()
