"""Read-only recipient evidence primitives; no engine, subprocess or ZIP writer.

These checks establish local representation integrity and declared graph gaps.
They do not authenticate a producer, bind an outer run or authorize packaging.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import zlib

LIMIT = 2 * 1024 * 1024
NATIVE_BUFFER_LIMIT = 64 * 1024 * 1024
EXE_SHA = "e7c956fd713f5d1b1b16cd55ef162aa487031430690ab1394ee60d3d02a13d04"
MODULE = "scripts/engine/utility"
PACK = "paris_enemy_cp_zmb_sdk_beacon_recipient_scripts"
SCRIPT_PATH = f"dump/{PACK}/{MODULE}.gscbin"
REFERENCES = (("material", "mopw/character_park_clown_zombie_shoes"),
              ("techset", "mopw_l_sm_replace_i0c0s0o0n0p0"),
              ("image", "park_clown_zombie_shoes_n_3e46d100_packed_nog"),
              ("image", "park_clown_zombie_shoes_pink_c_park_clown_zombie_shoes_g_packed_cs"))


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value), "Invalid SHA-256")
    return value.lower()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def json_bytes(raw):
    require(len(raw) <= LIMIT, "JSON exceeds analysis bound")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def number(value):
        result = float(value)
        require(math.isfinite(result), "Nonfinite JSON number")
        return result
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs, parse_float=number, parse_constant=number)


def safe_name(value):
    return isinstance(value, str) and len(value) <= 240 and bool(re.fullmatch(r"[a-z0-9_]+(?:/[a-z0-9_]+)*", value))


def safe_path(value):
    require(isinstance(value, str) and 0 < len(value) <= 512 and re.fullmatch(r"[A-Za-z0-9_./-]+", value)
            and not value.startswith("/"), "Unsafe relative evidence path")
    parts = value.split("/")
    require(all(part not in ("", ".", "..") and part == part.rstrip(" .") for part in parts), "Unsafe evidence path component")
    require(not any(re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) for part in parts), "Reserved path component")
    return PurePosixPath(value)


def no_redirects(path):
    path = Path(os.path.abspath(path))
    for item in (*reversed(path.parents), path):
        meta = item.lstat()
        require(not stat.S_ISLNK(meta.st_mode) and not getattr(meta, "st_file_attributes", 0) & 0x400, "Redirected evidence path")
    return path


def identity(meta):
    return meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns


class Files:
    """Fixed local bounds, stable files and streamed hashes; never writes."""
    def __init__(self, root):
        self.root = no_redirects(root)
        require(self.root.is_dir(), "Evidence root must be a directory")
        self.total = 0
        self.records = {}

    def measure(self, name, *, limit=LIMIT, retain=False):
        relative = safe_path(name)
        path = no_redirects(self.root.joinpath(*relative.parts))
        require(path.is_relative_to(self.root), "Evidence path escapes root")
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, "Evidence file exceeds bound or is not regular")
        require(len(self.records) < 64 and self.total + before.st_size <= 8 * LIMIT, "Evidence group exceeds analysis bound")
        checksum, chunks, count = hashlib.sha256(), [], 0
        with path.open("rb") as stream:
            require(identity(os.fstat(stream.fileno())) == identity(before), "Evidence changed before read")
            while block := stream.read(min(65536, before.st_size - count + 1)):
                count += len(block)
                require(count <= before.st_size, "Evidence grew during read")
                checksum.update(block)
                if retain:
                    chunks.append(block)
            require(identity(os.fstat(stream.fileno())) == identity(before), "Evidence changed during read")
        require(count == before.st_size and identity(path.stat()) == identity(before), "Evidence changed after read")
        record = {"path": name, "bytes": count, "sha256": checksum.hexdigest()}
        self.records[name] = record
        self.total += count
        return record, b"".join(chunks) if retain else None

    def read(self, name, limit=LIMIT):
        return self.measure(name, limit=limit, retain=True)[1]


def rows(raw, header, maximum=512):
    require(len(raw) <= 65536, "CSV exceeds analysis bound")
    result = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True))
    require(result and result[0] == header and 0 < len(result) - 1 <= maximum
            and all(len(row) == len(header) for row in result[1:]), "CSV header, row count or columns differ")
    return [dict(zip(header, row)) for row in result[1:]]


def reference_manifest(raw):
    result = rows(raw, ["type", "name", "status"], 4)
    require([(row["type"], row["name"], row["status"]) for row in result]
            == [(kind, name, "verified") for kind, name in REFERENCES], "Four exact verified references required")
    return {"verified_references": 4, "serialized_content_observed": False, "manifest_sha256": sha(raw)}


def gscbin(raw, module=MODULE):
    """Parse actual export bytes; source_len describes the uncompressed stack."""
    require(safe_name(module) and len(raw) <= LIMIT, "Unsupported module or script analysis bound")
    prefix = module.encode("ascii") + b"\0"
    offset = len(prefix)
    require(raw.startswith(prefix) and len(raw) >= offset + 12, "Script content name or length header differs")
    compressed, source, bytecode = struct.unpack_from("<iii", raw, offset)
    require(all(0 <= n <= NATIVE_BUFFER_LIMIT for n in (compressed, source, bytecode)), "Invalid native ScriptFile length")
    require(source <= LIMIT, "Expanded stack exceeds analysis bound")
    require(len(raw) == offset + 12 + compressed + bytecode, "Script representation has extra or missing bytes")
    buffer = raw[offset + 12:offset + 12 + compressed]
    code = raw[offset + 12 + compressed:]
    if compressed:
        decompressor = zlib.decompressobj()
        try:
            expanded = decompressor.decompress(buffer, source + 1)
        except zlib.error as error:
            raise ValueError("Invalid compressed ScriptFile stack") from error
        require(len(expanded) == source and decompressor.eof and not decompressor.unused_data
                and not decompressor.unconsumed_tail, "Stack length, zlib end or trailing data differs")
    else:
        require(source == 0, "Missing compressed stack")
        expanded = b""
    return {"module": module, "bytes": len(raw), "sha256": sha(raw), "compressed_len": compressed,
            "source_len": source, "bytecode_len": bytecode, "payload_sha256_without_name": sha(raw[offset:]),
            "compressed_sha256": sha(buffer), "bytecode_sha256": sha(code), "stack_sha256": sha(expanded),
            "stack_integrity_verified": True, "imports_analyzed": False}


def script_manifest(files, raw):
    result = rows(raw, ["donor_map", "pack_name", "module", "status", "path", "size_bytes", "sha256"], 1)[0]
    require(result["donor_map"] == "cp_zmb" and result["pack_name"] == PACK and result["module"] == MODULE
            and result["status"] == "dumped" and result["path"] == SCRIPT_PATH, "Exact successful utility export required")
    record, payload = files.measure(SCRIPT_PATH, retain=True)
    require(result["size_bytes"] == str(record["bytes"]) and digest(result["sha256"]) == record["sha256"], "Script manifest size/hash differs")
    parsed = gscbin(payload)
    observation = {key: parsed[key] for key in ("module", "bytes", "sha256", "compressed_len", "source_len", "bytecode_len")}
    observation.update(path=SCRIPT_PATH, decompressed=False, transitive_imports_verified=False, manifest_sha256=sha(raw))
    return observation, parsed


def verify_phase(work, receipt_path):
    """Consume H1's agreed phase-result/1. Outer run context remains separate."""
    receipt_path = no_redirects(receipt_path)
    receipt_bytes = Files(receipt_path.parent).read(receipt_path.name, 65536)
    receipt = json_bytes(receipt_bytes)
    fields = {"schema", "phase", "pid", "exit_code", "failure", "executable_sha256", "ownership", "log_limit_each", "observation"}
    require(isinstance(receipt, dict) and set(receipt) in (fields, fields | {"capture"}), "Unexpected phase receipt fields")
    require(receipt["schema"] == "iw7.recipient-phase-result/1" and receipt["phase"] in ("references", "script"), "Unknown recipient phase")
    require(type(receipt["pid"]) is int and receipt["pid"] > 0 and type(receipt["exit_code"]) is int
            and receipt["exit_code"] == 0 and receipt["failure"] is None, "Phase failed or native process identity missing")
    require(receipt["executable_sha256"] == EXE_SHA and receipt["ownership"] == "outer original Windows job"
            and type(receipt["log_limit_each"]) is int and receipt["log_limit_each"] == LIMIT, "Phase tool/ownership/bounds differ")
    if "capture" in receipt:
        # Producer 4867081 adds diagnostics, not an original-job closure proof.
        capture = receipt["capture"]
        require(isinstance(capture, dict) and set(capture) == {"pipe_buffer_size", "drain_threads_closed",
                "stdout_bytes_at_receipt", "stderr_bytes_at_receipt", "tree_closure_verified"}, "Unexpected capture fields")
        require(type(capture["pipe_buffer_size"]) is int and capture["pipe_buffer_size"] == 0
                and capture["drain_threads_closed"] is True and capture["tree_closure_verified"] is False,
                "Capture declaration does not match the successful raw-pipe producer contract")
        require(all(type(capture[key]) is int and 0 <= capture[key] <= LIMIT
                    for key in ("stdout_bytes_at_receipt", "stderr_bytes_at_receipt")), "Capture byte counts exceed declared bounds")
    files = Files(work)
    if receipt["phase"] == "references":
        manifest_path = "enemy-catalog/sdk_beacon_recipient_a.csv"
        observed = reference_manifest(files.read(manifest_path, 65536))
        analysis = {"content_identity_measured": False, "dependency_inventory_measured": False}
    else:
        manifest_path = f"dump/{PACK}/scriptfile-manifest.csv"
        observed, analysis = script_manifest(files, files.read(manifest_path, 65536))
    observed.update(manifest_path=manifest_path, closure_complete=False, package_ready=False)
    require(canonical(receipt["observation"]) == canonical(observed), "Phase observation differs from remeasured files")
    return {"phase": receipt["phase"], "phase_bytes_verified": True, "receipt_sha256": sha(receipt_bytes),
            "observation": observed, "analysis": analysis, "files": list(files.records.values()),
            "scope": "Local exported bytes and receipt consistency only; outer run, stock and load order are not verified here."}


def streamed_image_header(raw, name):
    """Pinned IW7 0x70 GfxImage + assetmanager array/string framing only."""
    require(safe_name(name) and "/" not in name, "Only flat native image names supported")
    require(raw[:6] == b"\x08\x01\x01\x00\x00\x00" and len(raw) == 121 + len(name)
            and raw[118:] == b"\x06\x01" + name.encode() + b"\0", "Unsupported IW7 image serialization framing/name")
    data = raw[6:118]
    require(data[57] == 1 and data[56] > 0 and all(struct.unpack_from("<4H", data, 48)), "Expected nonempty streamed IW7 image")
    streams, previous, unused = [], 0, False
    for index in range(4):
        cumulative = struct.unpack_from("<I", data, 76 + 8 * index)[0] & 0x3FFFFFF
        if not cumulative:
            unused = True
            continue
        require(not unused and cumulative >= previous, "Image stream descriptors have holes or descending sizes")
        if cumulative > previous:
            streams.append({"index": index, "bytes": cumulative - previous})
        previous = cumulative
    require(streams, "Streamed image has no pixel components")
    return {"name": name, "header_sha256": sha(raw), "streams": streams,
            "format": struct.unpack_from("<I", data, 24)[0], "width": struct.unpack_from("<H", data, 48)[0],
            "height": struct.unpack_from("<H", data, 50)[0]}


def image_manifest(files, raw, name):
    """Verify selected image header AND every positive-size declared pixel stream."""
    entries = rows(raw, ["donor_map", "image", "status", "path", "size_bytes", "sha256"])
    selected = [entry for entry in entries if entry["image"] == name]
    require(selected and all(e["donor_map"] == "cp_zmb" and e["status"] == "dumped" for e in selected), "Selected image export incomplete")
    paths = [entry["path"] for entry in selected]
    require(len(set(path.casefold() for path in paths)) == len(paths), "Duplicate image components")
    for path in paths:
        safe_path(path)
    headers = [entry for entry in selected if PurePosixPath(entry["path"]).name == name + ".iw7Image"]
    require(len(headers) == 1, "Exactly one image header required")
    header = headers[0]
    header_record, payload = files.measure(header["path"], limit=1024, retain=True)
    parsed = streamed_image_header(payload, name)
    parent = PurePosixPath(header["path"]).parent
    expected = {header["path"]: header_record["bytes"]}
    expected.update({str(parent / f"{name}_stream{item['index']}.pixels"): item["bytes"] for item in parsed["streams"]})
    require(set(paths) == set(expected), "Image manifest omits declared streams or contains extra components")
    components = []
    for entry in sorted(selected, key=lambda entry: entry["path"]):
        record = header_record if entry is header else files.measure(entry["path"])[0]
        require(record["bytes"] == expected[entry["path"]] and str(record["bytes"]) == entry["size_bytes"]
                and record["sha256"] == digest(entry["sha256"]), "Image component size/hash differs")
        components.append(record)
    return {"name": name, "component_set_verified": True, "manifest_sha256": sha(raw), "components": components,
            "header": parsed, "single_asset_sha256": None,
            "scope": "Exact selected serialized header and pixels only; no current DB binding or agreed composite node hash."}


def material_dependencies(raw):
    """Inventory explicit JSON references; material sidecars stay outstanding."""
    data = json_bytes(raw)
    require(isinstance(data, dict) and safe_name(data.get("techniqueSet->name")), "Material technique-set name unavailable")
    textures = data.get("textureTable")
    require(isinstance(textures, list) and len(textures) <= 255, "Material texture table unavailable")
    images = []
    for item in textures:
        require(isinstance(item, dict) and safe_name(item.get("image")), "Material image reference unresolved")
        images.append(item["image"])
    return {"representation_sha256": sha(raw), "requires": sorted({"techset:" + data["techniqueSet->name"], *("image:" + name for name in images)}),
            "submaterials_present": bool(data.get("subMaterials")),
            "remaining": ["Material state/constant-buffer sidecars need independent inventory and hashes.",
                          "Technique-set passes, shader bytecode and vertex declarations need independent inventory and hashes."]}


def audit_graph(roots, dependencies):
    """Structural closure only. None means unparsed edges; [] is declared terminal.

    Cycles are legal finite graphs, not evidence of missing dependencies. Callers
    must bind every edge/terminal assertion to a reviewed parser or boundary.
    """
    def valid_id(value):
        if not isinstance(value, str) or len(value) > 512 or not re.fullmatch(r"[a-z][a-z0-9_-]*:[a-z0-9_/.]+", value):
            return False
        try:
            safe_path(value.split(":", 1)[1])
            return True
        except ValueError:
            return False
    require(isinstance(roots, list) and 0 < len(roots) <= 4096 and all(valid_id(root) for root in roots)
            and len(set(roots)) == len(roots), "Invalid or duplicate graph roots")
    require(isinstance(dependencies, dict) and len(dependencies) <= 4096, "Invalid graph or node bound")
    edge_count = 0
    for node, edges in dependencies.items():
        require(valid_id(node), "Invalid graph node")
        require(edges is None or isinstance(edges, list) and len(edges) <= 512 and all(valid_id(edge) for edge in edges)
                and len(set(edges)) == len(edges), "Invalid or duplicate dependency edges")
        edge_count += len(edges or [])
    require(edge_count <= 16384, "Graph edge bound exceeded")
    seen, missing, unknown = set(), set(), set()
    pending = list(roots)
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        if node not in dependencies:
            missing.add(node)
        elif dependencies[node] is None:
            unknown.add(node)
        else:
            pending.extend(dependencies[node])
    return {"structural_graph_closed": not missing and not unknown, "reachable": sorted(seen),
            "missing_nodes": sorted(missing), "unknown_dependency_nodes": sorted(unknown),
            "scope": "Declared graph structure only; content, producer provenance, resolution and runtime are separate obligations."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--phase-receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_phase(args.work, args.phase_receipt)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, csv.Error) as error:
        print(json.dumps({"phase_bytes_verified": False, "errors": [str(error)]}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
