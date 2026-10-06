"""Asset-free adversarial checks for package planning and integrity gates."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("mod_package", ROOT / "ops/Validate-ModPackage.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = b"synthetic non-game fixture\n"
        (self.root / "fixture.ff").write_bytes(self.payload)
        self.data = mod.load_manifest(ROOT / "ops/mod-packages/hud-lua-plan.json")
        self.data["files"][0].update(source="fixture.ff", bytes=len(self.payload), sha256=hashlib.sha256(self.payload).hexdigest())
        self.data["closure"].update(status="complete", evidence_ref="synthetic fixture dependency report")
        self.data["closure"]["nodes"][0]["sha256"] = hashlib.sha256(b"synthetic Lua source").hexdigest()

    def check(self, data=None, stage="package", **kwargs):
        return mod.validate(data or self.data, self.root, stage, client_source=PIN, **kwargs)

    def denied(self, data=None, stage="package", fragment=None, **kwargs):
        report = self.check(data, stage, **kwargs)
        self.assertFalse(report["valid"], report)
        self.assertFalse(report["ready"])
        if fragment:
            self.assertIn(fragment, " ".join(report["errors"]))
        return report

    def test_inert_plan_is_valid_but_not_ready(self):
        data = mod.load_manifest(ROOT / "ops/mod-packages/hud-lua-plan.json")
        report = mod.validate(data)
        self.assertTrue(report["valid"], report)
        self.assertFalse(report["ready"])
        self.assertEqual(report["checked"], [])
        self.assertGreaterEqual(len(report["pending"]), 3)
        self.denied(data)

    def test_local_hash_success_is_not_gameplay(self):
        report = self.check()
        self.assertTrue(report["valid"], report)
        self.assertTrue(report["ready"])
        self.assertEqual(report["checked"], ["client_fastfile"])
        self.assertFalse(report["declared_owner_gameplay_accepted"])
        self.denied(stage="delivery", fragment="Delivery requires")

    def test_supported_technical_delivery_does_not_claim_owner_acceptance(self):
        for record in self.data["evidence"]:
            if record["kind"] in {"source-check", "offline-load", "runtime-link"}:
                record.update(status="pass", reference="synthetic test witness", maps=["cp_zmb"])
        report = self.check(stage="delivery")
        self.assertTrue(report["ready"], report)
        self.assertFalse(report["declared_owner_gameplay_accepted"])

    def test_bad_sha_size_missing_payload(self):
        for field, value in (("sha256", "f" * 64), ("bytes", 1), ("bytes", True), ("sha256", "abc"), ("source", "absent.ff"), ("bytes", None)):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["files"][0][field] = value
                self.denied(data)

    def test_unsafe_windows_paths(self):
        for path in ("../fixture.ff", "a/../fixture.ff", "C:/fixture.ff", "//host/share", "a\\b", "a//b", "./b", "NUL.ff", "a/COM1.txt", "a/COM\u00b9.ff", "a/LPT\u00b2.txt", "a:stream", "a/b.", "a/b ", "a/?b", "a/\x00b"):
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                data["files"][0]["source"] = path
                self.denied(data, fragment="Unsafe payload")

    def test_case_collisions_for_sources_destinations_and_nodes(self):
        data = copy.deepcopy(self.data)
        second = dict(data["files"][0], id="second", source="FIXTURE.ff")
        data["files"].append(second)
        self.denied(data, fragment="case-colliding")
        data = copy.deepcopy(self.data)
        node = copy.deepcopy(data["closure"]["nodes"][0])
        node["id"] = node["id"].upper()
        data["closure"]["nodes"].append(node)
        self.denied(data, fragment="case-colliding")

    def test_complete_closure_rejects_unresolved_unknown_edges_and_unreachable(self):
        data = copy.deepcopy(self.data)
        data["closure"]["unresolved"] = ["xmodel:missing"]
        self.denied(data, fragment="no unresolved")
        data = copy.deepcopy(self.data)
        data["closure"]["nodes"][0]["requires"] = ["xmodel:not-inventoried"]
        self.denied(data, fragment="not inventoried")
        data = copy.deepcopy(self.data)
        node = dict(data["closure"]["nodes"][0], id="image:unused", kind="image")
        data["closure"]["nodes"].append(node)
        self.denied(data, fragment="not reachable")

    def test_dependency_cycle_is_bounded_and_inventory_required(self):
        node = self.data["closure"]["nodes"][0]
        node["requires"] = ["material:fixture"]
        self.data["closure"]["nodes"].append(dict(node, id="material:fixture", kind="material", requires=[node["id"]]))
        self.assertTrue(self.check()["valid"])
        self.data["closure"]["nodes"][1]["sha256"] = None
        self.denied(fragment="every node")

    def test_lua_requires_capability_and_compatible_exact_source(self):
        report = mod.validate(self.data, self.root, "package", client_source="1b76f04e55b7e01ffb9d5a6fd9053585beb5ba27")
        self.assertFalse(report["valid"])
        self.data["native_requirements"]["client_capabilities"] = []
        self.denied(fragment="LuaFile requires")

    def test_native_client_cannot_arrive_via_stock_assets(self):
        self.data["native_requirements"]["client_source"] = PIN
        self.denied(fragment="stock client")
        self.assertTrue(self.check(target="native")["valid"])
        self.data["native_requirements"]["server_source"] = PIN
        self.denied(target="native", fragment="server native source")
        self.assertTrue(self.check(target="native", server_source=PIN)["valid"])

    def test_manifest_cannot_self_declare_new_capability_revision(self):
        invented = "a" * 40
        self.data["native_requirements"]["compatible_client_sources"] = [invented]
        report = mod.validate(self.data, self.root, "delivery", client_source=invented)
        self.assertFalse(report["ready"])
        self.assertIn("independently reviewed proof", " ".join(report["errors"]))
        self.assertFalse(mod.validate(self.data, stage="plan", client_source=invented)["valid"])

    def server_plan_with_client_dependency(self):
        payload = b"synthetic fixture\n"
        (self.root / "probe.gsc").write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        data = copy.deepcopy(self.data)
        data["delivery"] = "server-only"
        data["native_requirements"].update(client_capabilities=[], compatible_client_sources=[])
        data["files"][0].update(role="server", source="probe.gsc", destination="iw7-mod/custom_scripts/cp/probe.gsc",
                                bytes=len(payload), sha256=digest, closure_roots=["scriptfile:probe"])
        data["closure"].update(roots=["scriptfile:probe"], nodes=[
            {"id": "scriptfile:probe", "kind": "scriptfile", "scope": "server", "sha256": digest, "requires": ["xmodel:custom_missing"]},
            {"id": "xmodel:custom_missing", "kind": "xmodel", "scope": "client", "sha256": digest, "requires": []},
        ])
        for record in data["evidence"]:
            if record["kind"] in {"source-check", "runtime-link", "offline-load"}:
                record.update(status="pass", reference="declared synthetic evidence", maps=["cp_zmb"])
        return data

    def test_server_dependency_cannot_silently_ship_custom_client_asset(self):
        data = self.server_plan_with_client_dependency()
        self.denied(data, stage="delivery", fragment="matching-role payload coverage")
        self.denied(data, stage="package", fragment="matching-role payload coverage")
        data["closure"]["nodes"][1]["scope"] = "recipient"
        # A declared pre-existing recipient dependency does not need a payload;
        # its real provenance remains the supervising engine verifier's job.
        report = self.check(data, stage="delivery")
        self.assertTrue(report["ready"], report)
        self.assertIn("manifest assertions", report["validation_limit"])

    def test_declared_deliverable_root_requires_matching_file_binding(self):
        data = self.server_plan_with_client_dependency()
        data["closure"]["nodes"][0]["requires"] = []
        data["closure"]["roots"].append("xmodel:custom_missing")
        self.denied(data, stage="delivery", fragment="root has no matching-role file")
        data["files"][0]["closure_roots"].append("xmodel:custom_missing")
        self.denied(data, stage="delivery", fragment="root scope")

    def test_cross_scope_assets_delivered_by_own_role_files(self):
        data = self.server_plan_with_client_dependency()
        data["delivery"] = "mod"
        data["closure"]["roots"].append("xmodel:custom_missing")
        data["files"].append({"id": "client_model", "role": "client", "source": "fixture.ff",
                              "destination": "mods/paris_hud_probe/mod.ff", "bytes": len(self.payload),
                              "sha256": hashlib.sha256(self.payload).hexdigest(), "closure_roots": ["xmodel:custom_missing"]})
        self.assertTrue(self.check(data, stage="delivery")["ready"])
        # A client root cannot cover another server dependency unless that node
        # is independently reachable from a server payload binding.
        data["closure"]["nodes"].append({"id": "scriptfile:server_missing", "kind": "scriptfile", "scope": "server",
                                         "sha256": hashlib.sha256(b"fixture server").hexdigest(), "requires": []})
        data["closure"]["nodes"][1]["requires"] = ["scriptfile:server_missing"]
        self.denied(data, stage="delivery", fragment="matching-role payload coverage")

    def test_cross_scope_cannot_be_hidden_behind_recipient_node(self):
        data = self.server_plan_with_client_dependency()
        data["closure"]["nodes"][0]["requires"] = ["stock:bridge"]
        data["closure"]["nodes"].append({"id": "stock:bridge", "kind": "other", "scope": "recipient",
                                         "sha256": hashlib.sha256(b"recipient bridge").hexdigest(), "requires": ["xmodel:custom_missing"]})
        self.denied(data, stage="delivery", fragment="matching-role payload coverage")

    def test_single_gsc_does_not_cover_missing_import_payload(self):
        data = self.server_plan_with_client_dependency()
        data["closure"]["nodes"][1].update(id="scriptfile:custom_missing", kind="scriptfile", scope="server")
        data["closure"]["nodes"][0]["requires"] = ["scriptfile:custom_missing"]
        self.denied(data, stage="delivery", fragment="matching-role payload coverage")
        # A real server FF is a declared multi-asset container; exact content
        # inclusion still needs the independent ZoneTool inventory witness.
        data["files"][0]["destination"] = "zone/server_scripts.ff"
        self.assertTrue(self.check(data, stage="delivery")["ready"])

    def test_audio_container_cannot_cover_model_assets(self):
        data = self.server_plan_with_client_dependency()
        data["delivery"] = "mod"
        data["closure"]["roots"].append("sound:fixture")
        data["closure"]["nodes"].append({"id": "sound:fixture", "kind": "sound", "scope": "client",
                                         "sha256": hashlib.sha256(b"fixture audio").hexdigest(), "requires": ["xmodel:custom_missing"]})
        # Mandatory mod.ff is declared to hold only the audio root too; its
        # general asset coverage would conceal the deliberately bad SABL case.
        # Use an unrelated client FF root to isolate the audio dependency path.
        data["closure"]["roots"].append("image:resident")
        data["closure"]["nodes"].append({"id": "image:resident", "kind": "image", "scope": "client",
                                         "sha256": hashlib.sha256(b"fixture image").hexdigest(), "requires": []})
        for fid, src, suffix, binding in (("resident", "fixture.ff", "ff", "image:resident"),
                                          ("audio", "fixture.sabl", "sabl", "sound:fixture")):
            (self.root / src).write_bytes(self.payload)
            data["files"].append({"id": fid, "role": "client", "source": src,
                                  "destination": "mods/paris_hud_probe/mod." + suffix,
                                  "bytes": len(self.payload), "sha256": hashlib.sha256(self.payload).hexdigest(),
                                  "closure_roots": [binding]})
        self.denied(data, stage="delivery", fragment="matching-role payload coverage")

    def test_mod_pak_exe_and_missing_ff_are_rejected(self):
        for ext in ("pak", "exe", "dll", "zip", "lua"):
            data = copy.deepcopy(self.data)
            data["files"][0]["destination"] = "mods/paris_hud_probe/mod." + ext
            self.denied(data, fragment="downloader supports")
        data = copy.deepcopy(self.data)
        data["files"][0]["destination"] = "mods/paris_hud_probe/mod.sabs"
        self.denied(data, fragment="mandatory mod.ff")

    def test_usermap_supports_pak_with_required_main_ff(self):
        self.data["delivery"] = "usermap"
        self.data["files"][0]["destination"] = "usermaps/paris_hud_probe/paris_hud_probe.ff"
        self.assertTrue(self.check()["valid"])
        (self.root / "fixture.pak").write_bytes(self.payload)
        self.data["closure"]["roots"].append("image:stream")
        self.data["closure"]["nodes"].append({"id": "image:stream", "kind": "image", "scope": "client",
                                              "sha256": hashlib.sha256(b"fixture texture").hexdigest(), "requires": []})
        self.data["files"].append(dict(self.data["files"][0], id="textures", source="fixture.pak", destination="usermaps/paris_hud_probe/paris_hud_probe.pak", closure_roots=["image:stream"]))
        self.assertTrue(self.check()["valid"])
        self.data["files"].pop(0)
        self.denied(fragment="mandatory main fastfile")

    def test_server_only_script_no_client_download(self):
        self.data["delivery"] = "server-only"
        self.data["native_requirements"]["client_capabilities"] = []
        node = self.data["closure"]["nodes"][0]
        node.update(kind="scriptfile", scope="server")
        self.data["files"][0].update(role="server", destination="iw7-mod/custom_scripts/cp/probe.gsc")
        self.assertTrue(self.check()["valid"])
        self.data["files"][0]["role"] = "client"
        self.denied(fragment="cannot contain client")

    def test_pass_without_reference_and_wrong_scope_rejected(self):
        self.data["evidence"][0].update(status="pass", maps=["cp_zmb"])
        self.denied(fragment="traceable reference")
        self.data["evidence"][0].update(status="pending")
        self.data["closure"]["nodes"][0]["scope"] = "server"
        self.denied(fragment="root scope")

    def test_agent_gameplay_and_partial_maps_are_not_owner_acceptance(self):
        self.data["evidence"][-1].update(status="pass", authority="agent", maps=["cp_zmb"], reference="synthetic agent observation")
        self.assertFalse(self.check()["declared_owner_gameplay_accepted"])
        self.data["evidence"][-1]["authority"] = "owner"
        self.assertTrue(self.check()["declared_owner_gameplay_accepted"])
        self.data["maps"].append("cp_rave")
        self.assertFalse(self.check()["declared_owner_gameplay_accepted"])

    def test_symlink_payload_and_root_rejected(self):
        path = self.root / "linked.ff"
        try:
            path.symlink_to(self.root / "fixture.ff")
        except OSError as error:
            self.skipTest("symlink permission unavailable: " + str(error))
        self.data["files"][0]["source"] = "linked.ff"
        self.denied(fragment="Redirected")
        self.data["files"][0]["source"] = "fixture.ff"
        linkroot = self.root / "linked-root"
        linkroot.symlink_to(self.root, target_is_directory=True)
        report = mod.validate(self.data, linkroot, "package", client_source=PIN)
        self.assertFalse(report["valid"])

    @unittest.skipUnless(os.name == "nt", "Windows reparse-point regression")
    def test_windows_junction_ancestor_rejected_without_symlink_privilege(self):
        link = self.root / "junction"
        run = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.root)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        try:
            self.data["files"][0]["source"] = "junction/fixture.ff"
            self.denied(fragment="Redirected payload path")
            self.data["files"][0]["source"] = "fixture.ff"
            report = mod.validate(self.data, link, "package", client_source=PIN)
            self.assertFalse(report["valid"])
            self.assertIn("Redirected payload root", " ".join(report["errors"]))
        finally:
            link.rmdir()  # Remove only the junction; preserve its target.

    def test_malformed_shape_and_unknown_fields_fail_closed(self):
        for value in (None, [], {"schema": mod.SCHEMA}):
            self.assertFalse(mod.validate(value)["valid"])
        for section, field, value in (("closure", "nodes", {}), ("closure", "roots", [5]), ("native_requirements", "client_capabilities", [None])):
            data = copy.deepcopy(self.data)
            data[section][field] = value
            self.denied(data)
        data = copy.deepcopy(self.data)
        data["silent_install"] = True
        self.denied(data, fragment="fields mismatch")

    def test_duplicate_json_keys_and_cli_exit(self):
        path = self.root / "duplicate.json"
        path.write_text('{"schema": "one", "schema": "two"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            mod.load_manifest(path)
        run = subprocess.run([sys.executable, str(ROOT / "ops/Validate-ModPackage.py"), str(path)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
