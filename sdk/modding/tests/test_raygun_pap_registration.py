"""Source safety fixtures only; these do not execute GSC or simulate the engine."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = "sdk/modding/examples/raygun-pap-registration/"


def source_code(text):
    return re.sub(r"//[^\n]*", "", text)


def body(text, name):
    match = re.search(r"^" + name + r"\([^\n]*\)\n\{\n(.*?)^\}",
                      source_code(text), re.M | re.S)
    if not match:
        raise ValueError("Missing module function: " + name)
    return match.group(1)


def require_gates(text):
    activation = body(text, "activate").split("level.sdk_raygun_pap_registration = state;", 1)[0]
    for guard in ("!isdefined(assets_observed)", "assets_observed != true",
                  "!isdefined(scenario_reviewed)", "scenario_reviewed != true",
                  "!private_context(approved_fs_game)", "!isplayer(self)", "!isalive(self)",
                  "level.players.size != 1", "level.players[0] != self",
                  "isdefined(level.max_pap_func)", "level.pap_max != 2",
                  "isdefined(level.pap[base])", "isdefined(level.pap[upgraded])",
                  "isdefined(level.pap[upgraded_fallback])",
                  "isdefined(level.attachmentmap_basetounique[base])",
                  "isdefined(level.attachmentmap_uniquetobase[pap])",
                  "isdefined(self.pap[upgraded])", "before_base.lvl != 1"):
        if guard not in activation:
            raise ValueError("Missing pre-write refusal: " + guard)
    context = body(text, "private_context")
    for guard in ('getdvarint("sdk_raygun_pap_enable") == 1', '!getdvarint("sdk_raygun_pap_stop")',
                  'getdvar("mapname") == "cp_zmb"', 'getdvar("g_gametype") == "zombie"',
                  'getdvar("fs_game") == approved_fs_game', 'getdvarint("net_port") == 27116',
                  'getdvarint("sv_maxclients") == 1', 'getdvarint("sv_lanOnly") == 1',
                  'getdvar("g_password") != ""', 'getdvarint("sv_cheats") == 0',
                  'getdvarint("g_inactivity") == 0'):
        if guard not in context:
            raise ValueError("Missing private context: " + guard)


def require_mutation_boundary(text):
    # Separate assignments from comparisons. Inspect every retail-global/player
    # write, not a hash of the whole implementation or a Python GSC interpreter.
    code = source_code(text)
    writes = re.findall(r"\b((?:level|self|state\.owner)\.[\w]+(?:\[[^\]\n]+\])?)\s*=(?!=)\s*([^;]+);", code)
    allowed = {
        ("level.sdk_raygun_pap_registration", "state"),
        ("level.sdk_raygun_pap_registration", "undefined"),
        ("level.pap[base]", "base"), ("level.pap[state.base]", "undefined"),
        ("level.attachmentmap_basetounique[base]", "state.map"),
        ("level.attachmentmap_basetounique[state.base]", "undefined"),
        ("level.attachmentmap_uniquetobase[pap]", '"pap1"'),
        ("level.attachmentmap_uniquetobase[state.pap]", "undefined"),
        ("self.pap[base]", "state.record"), ("self.pap[upgraded]", "state.record"),
        ("state.owner.pap[state.base]", "state.before_base"),
        ("state.owner.pap[state.upgraded]", "undefined"),
    }
    if set(writes) != allowed:
        raise ValueError("Retail mutation set differs: " + repr(set(writes) ^ allowed))
    if re.search(r"\b(?:giveweapon|_giveweapon|takeweapon|givemaxammo|setweaponammostock|"
                 r"setweaponammoclip|setdvar|setdvarint|executecommand|setmoney|"
                 r"set_score|flag_set|flag_clear)\s*\(", code):
        raise ValueError("Transaction, prerequisite or server mutation forbidden")
    if re.search(r"\.(?:lvl|score|money|points)\s*(?:\+\+|--|[+\-*/]=)", code):
        raise ValueError("Retail level/currency adjustment forbidden")


def require_cleanup_order(text):
    cleanup = body(text, "stop")
    deferred = cleanup.index('return false;')
    stopped = cleanup.index('state.stopped = true;')
    ownership = cleanup.index('if (!owned_bindings(state))')
    first_revert = cleanup.index('level.pap[state.base] = undefined;')
    clear = cleanup.index('level.sdk_raygun_pap_registration = undefined;')
    notification = cleanup.rindex('level notify("sdk_raygun_pap_stopped");')
    if not deferred < stopped < ownership < first_revert < clear < notification:
        raise ValueError("Deferral, ownership or pre-endon cleanup order differs")
    pending = cleanup[ownership:first_revert]
    if 'RESTORE_PENDING' not in pending or 'return true;' not in pending:
        raise ValueError("External ownership loss must preserve bindings")


class RayGunPapSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / EXAMPLE / "sdk_raygun_pap_registration.gsc").read_text()

    def test_exported_source_doc_and_fixtures_only(self):
        product = ROOT / "product.json"
        if product.is_file():
            exports = json.loads(product.read_text())["exports"]
        else:
            # CI executes the exact composed source package, which intentionally
            # has a composition receipt rather than canonical product metadata.
            receipt = json.loads((ROOT / "source-workspace.json").read_text())
            exports = [entry["path"] for entry in receipt["files"]
                       if entry["owner"] == "iw7-creator-sdk"]
        self.assertIn(EXAMPLE + "sdk_raygun_pap_registration.gsc", exports)
        self.assertIn(EXAMPLE + "README.md", exports)
        self.assertIn("sdk/modding/tests/test_raygun_pap_registration.py", exports)
        self.assertEqual({p.name for p in (ROOT / EXAMPLE).iterdir()},
                         {"README.md", "sdk_raygun_pap_registration.gsc"})

    def test_default_init_cannot_publish_state_or_call_activation(self):
        init = body(self.text, "init")
        self.assertNotIn("activate(", init)
        self.assertNotRegex(init, r"\b(?:level|self)\.[\w]+\s*=(?!=)")
        self.assertIn("explicit_caller_attestations_required", init)

    def test_prewrite_guards_and_negative_weakened_attestations(self):
        require_gates(self.text)
        for old, new in (("assets_observed != true", "assets_observed == true"),
                         ("scenario_reviewed != true", "scenario_reviewed == true"),
                         ('getdvarint("sdk_raygun_pap_enable") == 1', 'true'),
                         ('getdvarint("net_port") == 27116', 'true'),
                         ("isdefined(level.max_pap_func)", "false"),
                         ("before_base.lvl != 1", "false")):
            with self.subTest(guard=old), self.assertRaises(ValueError):
                require_gates(self.text.replace(old, new, 1))

    def test_only_owned_dictionary_mutations_and_negative_global_overrides(self):
        require_mutation_boundary(self.text)
        for forbidden in ("level.max_pap_func = ::activate;", "level.pap_max = 3;",
                          "level.pap[upgraded] = base;", 'setdvar("sv_cheats", 1);',
                          'self giveweapon(upgraded);', 'self.pap[base].lvl++;'):
            with self.subTest(write=forbidden), self.assertRaises(ValueError):
                require_mutation_boundary(self.text + "\n" + forbidden)

    def test_shared_record_without_fabricated_upgrade(self):
        activation = body(self.text, "activate")
        self.assertIn('state.record = before_base;', activation)
        self.assertIn('state.record.lvl = 1;', activation)
        self.assertIn('self.pap[base] = state.record;', activation)
        self.assertIn('self.pap[upgraded] = state.record;', activation)
        self.assertIn('state.map["pap1"] = pap;', activation)
        self.assertIn('base = "sdk_raygun_zm";', activation)
        self.assertIn('pap = "sdk_raygun_pap_zm";', activation)
        self.assertIn('upgraded = "sdk_raygun_zm+sdk_raygun_pap_zm";', activation)
        self.assertNotRegex(activation, r'\.lvl\s*=\s*2|\.lvl\+\+')

    def test_second_upgrade_shortened_family_bypass_is_refused(self):
        require_gates(self.text)
        with self.assertRaises(ValueError):
            require_gates(self.text.replace('isdefined(level.pap[upgraded_fallback])', 'false', 1))
        self.assertIn('upgraded_fallback = getsubstr(upgraded, 0, upgraded.size - 1);',
                      body(self.text, "activate"))
        watcher = body(self.text, "watch_context")
        self.assertIn('isdefined(level.pap[state.upgraded])', watcher)
        self.assertIn('isdefined(level.pap[state.upgraded_fallback])', watcher)

    def test_real_donor_prerequisite_is_read_only_before_publication(self):
        activation = body(self.text, "activate")
        before = activation.split('level.sdk_raygun_pap_registration = state;', 1)[0]
        self.assertIn('!scripts\\engine\\utility::flag("fuses_inserted") &&', before)
        self.assertIn('!scripts\\cp\\zombies\\directors_cut::directors_cut_is_activated()) return false;', before)
        self.assertNotRegex(source_code(self.text), r'::(?:flag_set|directors_cut_activate)\(')

    def test_every_added_binding_is_owned_before_any_revert(self):
        require_cleanup_order(self.text)
        owned = body(self.text, "owned_bindings")
        for key in ('level.pap[state.base]', 'level.attachmentmap_basetounique[state.base]',
                    'level.attachmentmap_uniquetobase[state.pap]', 'state.owner.pap[state.base]',
                    'state.owner.pap[state.upgraded]'):
            self.assertIn(key, owned)
        self.assertIn('state.owner.pap[state.base] = state.before_base;', body(self.text, "stop"))

    def test_notification_before_clear_is_causal_negative_control(self):
        require_cleanup_order(self.text)
        clear = '        level.sdk_raygun_pap_registration = undefined;'
        changed = self.text.replace(clear, '        level notify("sdk_raygun_pap_stopped");\n' + clear, 1)
        changed = changed.rsplit('    level notify("sdk_raygun_pap_stopped");', 1)[0] + '\n    return true;\n}\n'
        with self.assertRaises(ValueError):
            require_cleanup_order(changed)

    def test_inflight_machine_defers_context_cleanup_and_watchdog_retries(self):
        cleanup = body(self.text, "stop")
        self.assertIn('reason != "game_ended" && reason != "owner_disconnect"', cleanup)
        self.assertIn('isdefined(state.owner.paping_weapon)', cleanup)
        self.assertIn('if (stop(state, "context_changed")) return;', body(self.text, "watch_context"))
        self.assertIn('level waittill("game_ended");', body(self.text, "game_end"))
        self.assertIn('self waittill("disconnect");', body(self.text, "departed"))

    def test_registration_has_no_yield_and_no_accepted_runtime_marker(self):
        activation = body(self.text, "activate")
        writes = activation.split('level.sdk_raygun_pap_registration = state;', 1)[1].split('level thread watch_context', 1)[0]
        self.assertNotRegex(writes, r'\b(?:wait|waittill|thread)\b')
        markers = [line for line in self.text.splitlines() if 'print(' in line]
        self.assertTrue(markers)
        self.assertTrue(all('runtime_ready=0' in line for line in markers))
        self.assertNotIn('runtime_ready=1', self.text)


if __name__ == "__main__":
    unittest.main()
