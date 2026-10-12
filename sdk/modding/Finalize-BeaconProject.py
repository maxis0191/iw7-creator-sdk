"""Materialize the fixed BeaconV1 candidate from existing bounded build evidence.

No compiler, extractor, game, ZIP writer or network. Exit 0 means a measured
candidate was written, including when recipient closure still blocks packaging.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
API = "beacon-finalize/1"
LIMIT = 2 * 1024 * 1024
MATERIAL = "mopw/character_park_clown_zombie_shoes"
UTILITY = "scriptfile:scripts/engine/utility.gsc"
BUILD_SOURCES = ("xmodel/paris_model_probe.xmb", "xsurface/paris_model_probe_lod0.xsb",
                 "zone_source/sdk_beacon.csv", "zone_source/paris_model_probe_recipient.csv",
                 "netconststrings/ncs_mdl_paris_model_probe.json")
PROJECT_FILES = {*BUILD_SOURCES, "beacon-preparation.json", "manifest.json", "model-ff-plan.json",
                 "sdk_beacon.gsc", "zone_source/paris_model_probe.csv"}
INVENTORY = ("material,," + MATERIAL, "xmodelsurfs,paris_model_probe_lod0", "xmodel,paris_model_probe",
             "netconststrings,ncs_mdl_paris_model_probe", "rawfile,sdk_beacon")
NODE_FILES = {"xmodel:paris_model_probe": BUILD_SOURCES[0],
              "xsurface:paris_model_probe_lod0": BUILD_SOURCES[1],
              "netconststrings:ncs_mdl_paris_model_probe": BUILD_SOURCES[4], "rawfile:sdk_beacon": "sdk_beacon"}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sdk = module(HERE / "manifest.py", "beacon_finalization_sdk")
compat = module(REPO / "ops/modding/Distribution-Compat.py", "beacon_finalization_compat")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-fA-F0-9]{64}", value))


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def decoded(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Invalid JSON number: " + value)
    def finite(value):
        result = float(value)
        return result if math.isfinite(result) else invalid(value)
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique, parse_constant=invalid, parse_float=finite)


def safe_existing(path):
    path = Path(os.path.abspath(path))
    for item in (*reversed(path.parents), path):
        meta = item.lstat()
        require(not stat.S_ISLNK(meta.st_mode) and not getattr(meta, "st_file_attributes", 0) & 0x400,
                "Redirected input/output path refused")
    return path


def identity(meta):
    return meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns


class Inputs:
    def __init__(self):
        self.reads = {}
        self.records = {}

    def read(self, root, name, label, limit=65536):
        require(sdk.transport.safe_path(name), "Unsafe input path")
        path = safe_existing(root / name)
        require(path.is_relative_to(root), "Input escapes its explicit root")
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit, "Bounded regular input required: " + label)
        with path.open("rb") as stream:
            require(identity(os.fstat(stream.fileno())) == identity(before), "Input changed before read")
            raw = stream.read(limit + 1)
            require(identity(os.fstat(stream.fileno())) == identity(before), "Input changed during read")
        require(len(raw) == before.st_size and identity(path.stat()) == identity(before), "Input changed after read")
        self.reads[path] = (identity(before), sha(raw))
        self.records[label] = {"bytes": len(raw), "sha256": sha(raw)}
        return raw

    def json(self, root, name, label, limit=65536):
        value = decoded(self.read(root, name, label, limit))
        require(isinstance(value, dict), "JSON object required: " + label)
        return value

    def recheck(self):
        for path, (expected, digest) in self.reads.items():
            safe_existing(path)
            require(identity(path.stat()) == expected, "Input changed before materialization")
            with path.open("rb") as stream:
                require(sha(stream.read(expected[2] + 1)) == digest, "Input bytes changed before materialization")
                require(identity(os.fstat(stream.fileno())) == expected, "Input changed during final recheck")
            require(identity(path.stat()) == expected, "Input changed after final recheck")


def check_geometry(value):
    exact = {"schema": "iw7.model-roundtrip/1", "vertices": 24, "triangles": 12, "bones": 1,
             "surfaces": 1, "lods": 1, "shadow_cutoff_lod": 6, "collision_lod": 255,
             "lod0_dist": 1000000, "has_lods": True, "geometry_roundtrip_verified": True,
             "read_existing_supported": True, "material_reference": MATERIAL, "ready": False,
             "normal_encoding": "H1-1010102-candidate", "iw7_normal_encoding_verified": False,
             "ff_built": False, "pixels_verified": False}
    require(isinstance(value, dict), "Geometry receipt must be an object")
    for key, expected in exact.items():
        require(type(value.get(key)) is type(expected) and value[key] == expected, "Original beacon geometry receipt differs: " + key)


def check_project(inputs, project):
    template = inputs.json(HERE, "examples/beacon/manifest.json", "template/manifest.json")
    gsc_template = inputs.read(HERE, "examples/beacon/sdk_beacon.gsc", "template/sdk_beacon.gsc")
    recipe = inputs.read(HERE, "examples/beacon/zone.csv", "template/zone.csv")
    receipt = inputs.json(project, "source-receipt.local.json", "project/source-receipt.local.json")
    require(receipt.get("schema") == "iw7.beacon-source-receipt/1" and receipt.get("zone") == "sdk_beacon"
            and receipt.get("ff_built") is False and Path(receipt["output"]).absolute() == project,
            "Exact unbuilt beacon source receipt/root required")
    entries = receipt.get("files")
    require(isinstance(entries, list) and len(entries) == len(PROJECT_FILES)
            and all(isinstance(entry, dict) and isinstance(entry.get("path"), str) for entry in entries)
            and {entry.get("path") for entry in entries} == PROJECT_FILES, "Exact ten-file beacon source inventory required")
    files = {}
    for entry in entries:
        raw = inputs.read(project, entry["path"], "project/" + entry["path"])
        require(type(entry.get("bytes")) is int and entry["bytes"] == len(raw)
                and pin(entry.get("sha256")) and sha(raw) == entry["sha256"].lower(), "Source receipt size/hash mismatch")
        files[entry["path"]] = raw
    require(files["sdk_beacon.gsc"] == gsc_template, "Only the exact shipped beacon GSC template is supported")
    require(files["zone_source/sdk_beacon.csv"].decode().splitlines() == recipe.decode().splitlines(), "Beacon zone recipe differs")
    require(files["zone_source/paris_model_probe_recipient.csv"].decode().splitlines() == ["material," + MATERIAL], "Recipient recipe differs")
    expected_ncs = {"stringType": 0, "sourceType": 2, "stringList": ["paris_model_probe"]}
    require(encoded(decoded(files[BUILD_SOURCES[4]])) == encoded(expected_ncs), "NCS source differs")
    preparation = decoded(files["beacon-preparation.json"])
    require(isinstance(preparation, dict) and preparation.get("schema") == "iw7.beacon-preparation/1" and preparation.get("zone") == "sdk_beacon"
            and preparation.get("gsc_sha256") == sha(gsc_template) and preparation.get("ff_built") is False
            and preparation.get("runtime_ready") is False and preparation.get("writer_plan") == "iw7.model-ff-plan/1",
            "Beacon preparation identity differs")
    source_manifest = decoded(files["manifest.json"])
    # Only the already measured GSC fields added by prepare_beacon are mutable.
    expected = copy.deepcopy(template)
    expected["package"]["files"][1].update(bytes=len(gsc_template), sha256=sha(gsc_template))
    expected["package"]["closure"]["nodes"][0]["sha256"] = sha(gsc_template)
    require(encoded(source_manifest) in (encoded(template), encoded(expected)), "Only the fixed beacon manifest/preparation is supported")
    return copy.deepcopy(template), gsc_template, expected_ncs


def check_build(inputs, project, build):
    state = inputs.json(build, "state.local.json", "build/state.local.json", 1024 * 1024)
    require(state.get("Schema") == "iw7.beacon-ff-build/1" and state.get("Status") == "BootstrapInventoryAndGeometryVerified",
            "Successful final beacon build state required")
    for flag in ("Restored", "StockPreserved", "InventoryVerified", "GeometryRoundtripVerified"):
        require(state.get(flag) is True, "Build gate not established: " + flag)
    require(state.get("Ready") is False and state.get("RestorationStatus") == "Confirmed"
            and state.get("RetainedLeaseToken") is None and state.get("CleanupError") is None
            and not state.get("Failure"), "Closed/restored build without a retained lease/failure required")
    plan = state["Plan"]
    require(Path(plan["SourceRoot"]).absolute() == project and plan["SourceFiles"] == list(BUILD_SOURCES)
            and Path(state["Work"]).absolute() == build / "work", "Build is bound to a different source/work root")
    require(pin(plan["Candidate"]["SHA256"]) and pin(plan["Candidate"]["ArtifactSHA256"]), "Pinned candidate identity missing")
    phases = state["Phases"]
    require(isinstance(phases, list) and len(phases) == 4 and all(isinstance(phase, dict) for phase in phases)
            and [phase.get("Phase") for phase in phases] == ["build", "verify", "dump", "read"], "Exact ordered four-phase completion required")
    for phase in phases:
        require(type(phase.get("ExitCode")) is int and phase["ExitCode"] == 0
                and type(phase.get("JobActiveAtClose")) is int and phase["JobActiveAtClose"] == 0,
                "Build phase failed or job remains active")
        detail = inputs.json(build, phase["Phase"] + "/phase.json", "build/" + phase["Phase"] + "/phase.json")
        require(detail.get("schema") == "iw7.beacon-tool-phase/1" and detail.get("phase") == phase["Phase"]
                and type(detail.get("exit_code")) is int and detail["exit_code"] == 0 and detail.get("failure") is None,
                "Native phase receipt disagrees with final state")
    ff = inputs.read(build, "mod.ff", "build/mod.ff", 1024 * 1024)
    require(state["FF"]["Path"] == "mod.ff" and type(state["FF"]["Bytes"]) is int and state["FF"]["Bytes"] == len(ff)
            and pin(state["FF"]["SHA256"]) and state["FF"]["SHA256"].lower() == sha(ff), "FF differs from measured build")
    require(ff.startswith(b"IWffu100"), "Expected IW7 FF envelope missing (not a full parser)")
    rows = inputs.read(build, "assets.csv", "build/assets.csv").decode("utf-8-sig").splitlines()
    dumped = inputs.read(build, "work/dump/sdk_beacon/sdk_beacon.csv", "build/dump-inventory.csv").decode("utf-8-sig").splitlines()
    require(len(rows) == len(dumped) == 5 and set(rows) == set(dumped) == set(INVENTORY), "Exact five-asset inventories required")
    log = inputs.read(build, "verify/stdout.log", "build/verify/stdout.log", LIMIT).decode("utf-8-sig")
    require('Loading zone "sdk_beacon"' in log and not re.search(r'could not be found|Could not find referenced|\[ ERROR \]|\[ FATAL \]', log), "Verification log missing or failed")
    matches = re.findall(r'Loading asset "([^"\r\n]+)" of type ([a-z0-9]+)\.', log)
    require(len(matches) == 5 and {kind + "," + name for name, kind in matches} == set(INVENTORY), "Verification log inventory differs")
    geometry = inputs.json(build, "read/stdout.log", "build/read/stdout.log")
    require(encoded(geometry) == encoded(state["Geometry"]), "Reader output differs from final state")
    check_geometry(geometry)
    nodes = {}
    for ident, relative in NODE_FILES.items():
        raw = inputs.read(build, "work/dump/sdk_beacon/" + relative, "build/dump/" + relative, 8192)
        if relative in BUILD_SOURCES[:2]:
            require(raw == inputs.read(build, "roundtrip/" + relative, "build/roundtrip/" + relative, 8192), "Reader input differs from FF dump")
        nodes[ident] = raw
    require(nodes["rawfile:sdk_beacon"] == b"Compiled using x64 ZoneTool.", "Unexpected generated beacon rawfile")
    return state, ff, nodes


def recipient_snapshot(inputs, proof, root):
    require((proof is None) == (root is None), "Recipient proof and root must be supplied together")
    if proof is None:
        return None
    proof = safe_existing(proof)
    root = safe_existing(root)
    declared = inputs.json(proof.parent, proof.name, "recipient/proof.json")
    expected = inputs.json(REPO, "ops/model-lab/recipient.evidence.json", "contract/recipient.evidence.json")
    require(encoded(declared) == encoded(expected), "Only the reviewed snapshot-only recipient evidence is supported; no fresh-resolution adapter exists")
    for label, record in expected["material_snapshot"].items():
        raw = inputs.read(root, record["path"], "recipient/" + label, 65536)
        require(len(raw) == record["bytes"] and sha(raw) == record["sha256"], "Recipient snapshot changed")
    return expected["material_snapshot"]["material_json"]["sha256"]


class OutputFiles:
    """Exclusive fixed files, with identity-checked, nonrecursive error cleanup."""
    def __init__(self, root):
        self.root = root
        self.files = {}
        self.directories = {}
        self.bytes = 0

    def mkdir(self, path):
        path.mkdir()
        meta = safe_existing(path).stat()
        self.directories[path] = (meta.st_dev, meta.st_ino)

    def write(self, name, raw):
        require(sdk.transport.safe_path(name), "Unsafe output path")
        require(self.bytes + len(raw) <= LIMIT, "Materialization exceeds 2 MiB byte budget")
        path = self.root / name
        for directory in (*reversed(path.parent.parents), path.parent):
            if directory.is_relative_to(self.root) and not directory.exists():
                self.mkdir(directory)
        safe_existing(path.parent)
        with path.open("xb") as stream:
            try:
                require(stream.write(raw) == len(raw), "Incomplete candidate write")
                stream.flush()
            finally:
                self.files[path] = identity(os.fstat(stream.fileno()))
        require(identity(path.stat()) == self.files[path], "Output changed during write")
        self.bytes += len(raw)

    def cleanup(self):
        for path, expected in reversed(self.files.items()):
            try:
                safe_existing(path)
                if identity(path.stat()) == expected:
                    path.unlink()
            except (OSError, ValueError):
                pass  # Preserve replacements, redirects and concurrent content.
        for path, expected in sorted(self.directories.items(), key=lambda item: len(item[0].parts), reverse=True):
            try:
                meta = safe_existing(path).stat()
                if (meta.st_dev, meta.st_ino) == expected:
                    path.rmdir()
            except (OSError, ValueError):
                pass


def finalize(project, build_root, output_root, *, client_source=None, server_source=None,
             recipient_proof=None, recipient_root=None):
    project, build = safe_existing(project), safe_existing(build_root)
    output = Path(os.path.abspath(output_root))
    safe_existing(output.parent)
    require(not output.exists() and not output.is_symlink(), "Fresh output root required")
    require(all(not root.is_relative_to(output) and not output.is_relative_to(root) for root in (project, build)),
            "Output overlaps input roots")
    for value in (client_source, server_source):
        require(value is None or isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value), "Source identity must be an exact lowercase commit")
    inputs = Inputs()
    manifest, gsc, ncs = check_project(inputs, project)
    state, ff, nodes = check_build(inputs, project, build)
    source_bound = "SourceReceiptSHA256" in state["Plan"]
    if source_bound:
        digest = state["Plan"]["SourceReceiptSHA256"]
        require(pin(digest) and digest.lower() == inputs.records["project/source-receipt.local.json"]["sha256"],
                "Build SourceReceiptSHA256 differs from the current source receipt")
    require(encoded(decoded(nodes["netconststrings:ncs_mdl_paris_model_probe"])) == encoded(ncs), "Dumped NCS differs from original source")
    material_sha = recipient_snapshot(inputs, recipient_proof, recipient_root)
    closure = manifest["package"]["closure"]
    representations = []
    outputs = {"mod.ff": ff, "sdk_beacon.gsc": gsc}
    for node in closure["nodes"]:
        if node["id"] in nodes:
            raw = nodes[node["id"]]
            node["sha256"] = sha(raw)
            path = "evidence/serialized-nodes/" + NODE_FILES[node["id"]]
            outputs[path] = raw
            representations.append({"id": node["id"], "path": path, "bytes": len(raw), "sha256": sha(raw), "representation": "Exact retained FF dump bytes"})
        elif node["scope"] == "server":
            node["sha256"] = sha(gsc)
            node["requires"].append(UTILITY)
        elif material_sha:
            node["sha256"] = material_sha
    closure["nodes"].append({"id": UTILITY, "kind": "scriptfile", "scope": "recipient", "sha256": None, "requires": []})
    closure["status"] = "incomplete"
    closure["evidence_ref"] = "finalization.json#node_representations"
    for entry in manifest["package"]["files"]:
        path = "mod.ff" if entry["role"] == "client" else "sdk_beacon.gsc"
        entry.update(source=path, bytes=len(outputs[path]), sha256=sha(outputs[path]))
    validation = sdk.validate(manifest, stage="plan", client_source=client_source, server_source=server_source)
    require(validation["valid"], "Generated SDK plan invalid: " + "; ".join(validation["errors"]))
    compatibility = compat.check_environment([manifest], client_source=client_source, server_source=server_source, protocol=2, mode="cp")
    blockers = ["Recipient material resolution and transitive image/technique closure remain unqualified.",
                "Current compiled scripts/engine/utility (native lookup without .gsc) and its imports remain unqualified."] + compatibility
    if not source_bound:
        blockers.append("Historical build state lacks Plan.SourceReceiptSHA256; source-to-build receipt binding remains unverified.")
    # Snapshot hashes are useful provenance, never a shortcut to complete closure.
    evidence = {"api": API, "adapter": "BeaconV1", "inputs": inputs.records, "node_representations": representations,
                "recipient_snapshot_measured": material_sha is not None, "recipient_current_resolution_verified": False,
                "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
                "blockers": blockers, "build_candidate_sha256": state["Plan"]["Candidate"]["SHA256"].lower(),
                "target_source_assertions": {"client": client_source, "server": server_source},
                "source_receipt_bound": source_bound,
                "source_receipt_binding_limit": ("Plan.SourceReceiptSHA256 matches the remeasured source receipt."
                    if source_bound else "Historical final state lacks Plan.SourceReceiptSHA256; source root/GSC/template are checked but historical receipt binding is unverified.")
                    + " Receipt statements and source pins are not publisher authentication or runtime proof.",
                "validation_limit": "Rechecks existing source/build records and retained bytes. Does not parse arbitrary FF assets, execute a reader, prove a retail recipient or promote runtime evidence."}
    outputs.update({"manifest.json": encoded(manifest), "finalization.json": encoded(evidence), "validation-plan.json": encoded(validation)})
    require(sum(map(len, outputs.values())) <= LIMIT, "Materialization exceeds 2 MiB byte budget")
    inputs.recheck()
    # Exclusive root and fixed output allowlist; invalid inputs never create it.
    writer = OutputFiles(output)
    writer.mkdir(output)
    try:
        for name, raw in sorted(outputs.items(), key=lambda item: (item[0] == "manifest.json", item[0])):
            writer.write(name, raw)
        package = sdk.validate(manifest, root=output, stage="package", client_source=client_source, server_source=server_source)
        require(package["checked"] == ["client_fastfile", "server_gameplay"], "Materialized payload verification failed")
        require(not package["ready"] and any("closure incomplete" in error for error in package["errors"]), "Incomplete recipient gate unexpectedly changed")
        writer.write("validation-package.json", encoded(package))
    except Exception:
        writer.cleanup()
        raise
    return {"api": API, "materialized": True, "candidate_root": str(output), "manifest_path": str(output / "manifest.json"),
            "closure_complete": False, "package_ready": False, "runtime_ready": False, "source_receipt_bound": source_bound,
            "blockers": blockers,
            "exact_hashes": {"ff": sha(ff), "gsc": sha(gsc), "manifest": sha(outputs["manifest.json"]),
                             "source_receipt": inputs.records["project/source-receipt.local.json"]["sha256"],
                             "build_receipt": inputs.records["build/state.local.json"]["sha256"]},
            "bytes_written": writer.bytes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--client-source")
    parser.add_argument("--server-source")
    parser.add_argument("--recipient-proof", type=Path)
    parser.add_argument("--recipient-root", type=Path)
    args = parser.parse_args()
    try:
        result = finalize(args.project, args.build_root, args.output_root, client_source=args.client_source,
                          server_source=args.server_source, recipient_proof=args.recipient_proof, recipient_root=args.recipient_root)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        print(json.dumps({"api": API, "materialized": False, "closure_complete": False, "package_ready": False, "runtime_ready": False,
                          "errors": [str(error)]}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
