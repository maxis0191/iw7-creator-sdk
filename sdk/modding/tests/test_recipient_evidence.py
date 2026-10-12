"""Synthetic, asset-free recipient analysis tests; no native process or stock."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zlib

VERIFY = Path(__file__).resolve().parents[1] / "recipient/verify.py"
SPEC = importlib.util.spec_from_file_location("recipient_evidence_test", VERIFY)
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def csv_bytes(header, entries):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(entries)
    return stream.getvalue().encode()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="recipient-evidence-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.work = self.root / "work"
        self.work.mkdir()
        self.receipt_path = self.root / "phase.json"
        self.stack = b"synthetic stack containing scripts/common/flags, not decoded imports"
        self.code = b"\x00\x01\x02synthetic instruction bytes"
        self.compressed = zlib.compress(self.stack)
        self.script = v.MODULE.encode() + b"\0" + struct.pack("<iii", len(self.compressed), len(self.stack), len(self.code)) + self.compressed + self.code

    def write(self, name, raw):
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def phase(self, kind):
        if kind == "references":
            path = "enemy-catalog/sdk_beacon_recipient_a.csv"
            raw = csv_bytes(["type", "name", "status"], [[*row, "verified"] for row in v.REFERENCES])
            observation = {"verified_references": 4, "serialized_content_observed": False}
        else:
            path = f"dump/{v.PACK}/scriptfile-manifest.csv"
            raw = csv_bytes(["donor_map", "pack_name", "module", "status", "path", "size_bytes", "sha256"],
                [["cp_zmb", v.PACK, v.MODULE, "dumped", v.SCRIPT_PATH, len(self.script), v.sha(self.script)]])
            self.write(v.SCRIPT_PATH, self.script)
            observation = {"module": v.MODULE, "path": v.SCRIPT_PATH, "bytes": len(self.script), "sha256": v.sha(self.script),
                "compressed_len": len(self.compressed), "source_len": len(self.stack), "bytecode_len": len(self.code),
                "decompressed": False, "transitive_imports_verified": False}
        self.write(path, raw)
        observation.update(manifest_path=path, manifest_sha256=v.sha(raw), closure_complete=False, package_ready=False)
        receipt = {"schema": "iw7.recipient-phase-result/1", "phase": kind, "pid": 123, "exit_code": 0, "failure": None,
            "executable_sha256": v.EXE_SHA, "ownership": "outer original Windows job", "log_limit_each": 2097152,
            "observation": observation}
        self.save_receipt(receipt)
        return receipt

    def save_receipt(self, receipt):
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    def image_fixture(self, cumulative=(3, 7, 0, 0)):
        name = "original_synthetic_image"
        data = bytearray(112)
        struct.pack_into("<I", data, 24, 71)  # DXGI BC1_UNORM; no render claim.
        struct.pack_into("<4H", data, 48, 8, 8, 1, 1)
        data[56:58] = b"\x02\x01"
        for i, size in enumerate(cumulative):
            struct.pack_into("<HHI", data, 72 + 8 * i, 8, 8, size | (1 << 26))
        header = b"\x08\x01\x01\0\0\0" + data + b"\x06\x01" + name.encode() + b"\0"
        base = "dump/original_test/streamed_images/" + name
        components = {base + ".iw7Image": header}
        previous = 0
        for i, total in enumerate(cumulative):
            if total > previous:
                components[base + f"_stream{i}.pixels"] = bytes([i + 1]) * (total - previous)
            previous = total
        for path, raw in components.items():
            self.write(path, raw)
        entries = [["cp_zmb", name, "dumped", path, len(raw), v.sha(raw)] for path, raw in components.items()]
        manifest = csv_bytes(["donor_map", "image", "status", "path", "size_bytes", "sha256"], entries)
        return name, header, components, entries, manifest

    def test_references_rehash_csv_without_inventing_content(self):
        self.phase("references")
        report = v.verify_phase(self.work, self.receipt_path)
        self.assertTrue(report["phase_bytes_verified"])
        self.assertFalse(report["observation"]["serialized_content_observed"])
        self.assertFalse(report["analysis"]["content_identity_measured"])
        self.assertFalse(report["analysis"]["dependency_inventory_measured"])
        self.assertNotIn("sha256", report["observation"])

    def test_script_hashes_serialized_compiled_and_expanded_bytes_separately(self):
        report = v.gscbin(self.script)
        self.assertEqual(report["sha256"], v.sha(self.script))
        self.assertEqual(report["payload_sha256_without_name"], v.sha(self.script[len(v.MODULE) + 1:]))
        self.assertEqual(report["compressed_sha256"], v.sha(self.compressed))
        self.assertEqual(report["bytecode_sha256"], v.sha(self.code))
        self.assertEqual(report["stack_sha256"], v.sha(self.stack))
        self.assertTrue(report["stack_integrity_verified"])
        self.assertFalse(report["imports_analyzed"], "A string resembling an import is not disassembly")

    def test_real_phase_contract_comparison_keeps_producer_decompression_claim(self):
        self.phase("script")
        report = v.verify_phase(self.work, self.receipt_path)
        self.assertTrue(report["phase_bytes_verified"])
        self.assertFalse(report["observation"]["decompressed"])
        self.assertTrue(report["analysis"]["stack_integrity_verified"])
        self.assertFalse(report["analysis"]["imports_analyzed"])

    def test_script_truncation_extra_bytes_name_and_length_bounds(self):
        offset = len(v.MODULE) + 1
        bad = [self.script[:-1], self.script + b"x", b"X" + self.script[1:], self.script[:offset + 11]]
        for field, value in ((0, -1), (1, 64 * 1024 * 1024 + 1), (2, -1), (1, v.LIMIT + 1)):
            raw = bytearray(self.script)
            struct.pack_into("<i", raw, offset + 4 * field, value)
            bad.append(bytes(raw))
        for raw in bad:
            with self.subTest(bytes=len(raw)), self.assertRaises(ValueError):
                v.gscbin(raw)

    def test_zlib_length_trailing_stream_and_corruption_are_rejected(self):
        for compressed, expanded_len in ((self.compressed[:-1], len(self.stack)), (self.compressed + b"x", len(self.stack)),
            (self.compressed + zlib.compress(b"extra"), len(self.stack)), (b"invalid", len(self.stack)),
            (self.compressed, len(self.stack) - 1), (self.compressed, len(self.stack) + 1), (b"", 1)):
            raw = v.MODULE.encode() + b"\0" + struct.pack("<iii", len(compressed), expanded_len, len(self.code)) + compressed + self.code
            with self.subTest(compressed=len(compressed), expected=expanded_len), self.assertRaises(ValueError):
                v.gscbin(raw)

    def test_empty_compiled_envelope_is_structural_only(self):
        raw = v.MODULE.encode() + b"\0" + struct.pack("<iii", 0, 0, 0)
        result = v.gscbin(raw)
        self.assertEqual(result["stack_sha256"], v.sha(b""))
        self.assertFalse(result["imports_analyzed"])

    def test_reference_csv_missing_default_duplicate_or_wrong_order_refused(self):
        good = [[*row, "verified"] for row in v.REFERENCES]
        variants = [good[:3], [good[0]] * 4, list(reversed(good)), [good[0][:-1] + ["default"], *good[1:]]]
        for entries in variants:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                v.reference_manifest(csv_bytes(["type", "name", "status"], entries))

    def test_phase_exit_pid_schema_and_boolean_claims_refused(self):
        original = self.phase("script")
        for key, value in (("exit_code", 1), ("exit_code", False), ("failure", "timeout"), ("pid", 0),
                           ("pid", True), ("schema", "future"), ("log_limit_each", True), ("executable_sha256", "0" * 64)):
            with self.subTest(key=key):
                receipt = copy.deepcopy(original)
                receipt[key] = value
                self.save_receipt(receipt)
                with self.assertRaises(ValueError):
                    v.verify_phase(self.work, self.receipt_path)
        for key, value in (("transitive_imports_verified", True), ("closure_complete", True),
                           ("package_ready", 0), ("sha256", "0" * 64), ("manifest_path", "../outside.csv")):
            with self.subTest(key=key):
                receipt = copy.deepcopy(original)
                receipt["observation"][key] = value
                self.save_receipt(receipt)
                with self.assertRaisesRegex(ValueError, "observation differs"):
                    v.verify_phase(self.work, self.receipt_path)

    def test_phase_rehash_catches_payload_change_and_manifest_alias(self):
        receipt = self.phase("script")
        self.write(v.SCRIPT_PATH, self.script + b"changed")
        with self.assertRaisesRegex(ValueError, "size/hash"):
            v.verify_phase(self.work, self.receipt_path)
        self.write(v.SCRIPT_PATH, self.script)
        manifest_path = receipt["observation"]["manifest_path"]
        raw = (self.work / manifest_path).read_bytes()
        self.write(manifest_path, raw.replace(v.SCRIPT_PATH.encode(), b"../outside.gscbin"))
        with self.assertRaisesRegex(ValueError, "Exact successful"):
            v.verify_phase(self.work, self.receipt_path)

    def test_streamed_image_requires_header_and_all_pixels(self):
        name, header, components, _, manifest = self.image_fixture()
        result = v.image_manifest(v.Files(self.work), manifest, name)
        self.assertTrue(result["component_set_verified"])
        self.assertIsNone(result["single_asset_sha256"])
        self.assertEqual(result["header"]["header_sha256"], v.sha(header))
        self.assertEqual(result["header"]["streams"], [{"index": 0, "bytes": 3}, {"index": 1, "bytes": 4}])
        self.assertEqual({r["path"]: r["sha256"] for r in result["components"]}, {p: v.sha(raw) for p, raw in components.items()})

    def test_header_only_and_missing_or_extra_manifest_streams_refused(self):
        name, _, _, entries, _ = self.image_fixture()
        variants = [entries[:1], entries[:2], entries + [entries[1]],
                    entries + [["cp_zmb", name, "dumped", "dump/extra.pixels", 3, "0" * 64]]]
        for rows in variants:
            manifest = csv_bytes(["donor_map", "image", "status", "path", "size_bytes", "sha256"], rows)
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                v.image_manifest(v.Files(self.work), manifest, name)

    def test_pixel_hash_and_declared_size_checked(self):
        name, _, components, _, manifest = self.image_fixture()
        path = next(p for p in components if p.endswith("stream0.pixels"))
        for raw in (b"bad", b"larger"):
            self.write(path, raw)
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "size/hash differs"):
                v.image_manifest(v.Files(self.work), manifest, name)

    def test_image_holes_descending_and_wrong_framing_refused(self):
        name, header, _, _, _ = self.image_fixture()
        for cumulative in ((3, 0, 9, 0), (7, 3, 0, 0)):
            _, altered, _, _, _ = self.image_fixture(cumulative)
            with self.assertRaisesRegex(ValueError, "holes or descending"):
                v.streamed_image_header(altered, name)
        for altered in (header[:-1], header + b"x", b"\x09" + header[1:], header.replace(name.encode(), b"wrong")):
            with self.assertRaises(ValueError):
                v.streamed_image_header(altered, name)

    def test_unused_tail_streams_allowed_but_resident_profile_is_not_guessed(self):
        name, header, _, _, _ = self.image_fixture((3, 0, 0, 0))
        self.assertEqual(v.streamed_image_header(header, name)["streams"], [{"index": 0, "bytes": 3}])
        resident = bytearray(header)
        resident[6 + 57] = 0
        with self.assertRaisesRegex(ValueError, "streamed IW7"):
            v.streamed_image_header(bytes(resident), name)

    def test_material_edges_use_actual_json_names_with_sidecars_pending(self):
        raw = b'{"techniqueSet->name":"original_techset","textureTable":[{"image":"original_image"},{"image":"original_image"}],"subMaterials":[123]}'
        result = v.material_dependencies(raw)
        self.assertEqual(result["requires"], ["image:original_image", "techset:original_techset"])
        self.assertEqual(result["representation_sha256"], v.sha(raw))
        self.assertTrue(result["submaterials_present"])
        self.assertTrue(result["remaining"])
        for bad in (b'{}', b'{"techniqueSet->name":"x","textureTable":[{"image":""}]}',
                    b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'):
            with self.assertRaises(ValueError):
                v.material_dependencies(bad)

    def test_structural_graph_can_close_but_is_not_a_proof_gate(self):
        graph = {"scriptfile:a.gsc": ["scriptfile:b.gsc", "image:c"], "scriptfile:b.gsc": ["scriptfile:a.gsc"], "image:c": []}
        report = v.audit_graph(["scriptfile:a.gsc"], graph)
        self.assertTrue(report["structural_graph_closed"])
        self.assertEqual(report["reachable"], sorted(graph))
        self.assertNotIn("package_ready", report)
        self.assertNotIn("closure_complete", report)

    def test_graph_tracks_missing_and_unparsed_dependencies_through_cycles(self):
        graph = {"scriptfile:a.gsc": ["scriptfile:b.gsc", "image:missing"], "scriptfile:b.gsc": None}
        result = v.audit_graph(["scriptfile:a.gsc"], graph)
        self.assertFalse(result["structural_graph_closed"])
        self.assertEqual(result["missing_nodes"], ["image:missing"])
        self.assertEqual(result["unknown_dependency_nodes"], ["scriptfile:b.gsc"])

    def test_graph_duplicates_bad_types_and_bounds_rejected(self):
        for graph in ({"image:a": ["image:b", "image:b"]}, {"image:a": True}, {"bad": []}, {"image:../a": []},
                      {"image:a": [f"image:x{i}" for i in range(513)]}):
            with self.subTest(graph_type=str(type(graph))), self.assertRaises(ValueError):
                v.audit_graph(["image:a"], graph)
        with self.assertRaises(ValueError):
            v.audit_graph(["image:a", "image:a"], {"image:a": []})

    def test_files_reject_escape_aliases_and_reparse_attributes(self):
        self.write("input.bin", b"payload")
        for path in ("../input.bin", "/input.bin", "C:/input.bin", "input.bin:stream", "a//b", "a/./b", "nul.txt", "a./b", "a\\b", "*.bin"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.Files(self.work).measure(path)
        original = Path.lstat
        def reparse(path, *args, **kwargs):
            if path == self.work / "input.bin":
                return SimpleNamespace(st_mode=0o100644, st_file_attributes=0x400)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "lstat", reparse), self.assertRaisesRegex(ValueError, "Redirected"):
            v.Files(self.work).measure("input.bin")

    def test_cli_is_read_only_and_refuses_nonobject_receipts(self):
        self.phase("script")
        def snapshot():
            return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        before = snapshot()
        command = [sys.executable, "-B", str(VERIFY), "--work", str(self.work), "--phase-receipt", str(self.receipt_path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)["phase_bytes_verified"])
        self.assertEqual(snapshot(), before)
        self.receipt_path.write_text("[]")
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertFalse(json.loads(result.stdout)["phase_bytes_verified"])
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
