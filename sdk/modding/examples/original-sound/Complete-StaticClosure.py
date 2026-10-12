"""Original-sound closure adapter; never reads FF/SAB or starts the engine."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOUND = ROOT / "tools-source/asset-bridge/surfaces/sound"
sys.path.insert(0, str(SOUND))

spec = importlib.util.spec_from_file_location("original_sound_closure_reader", SOUND / "read_sab.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

IDENT = "sdk_original_sound_v1"
SERVER_SOURCE = "server/" + IDENT + ".gsc"
SERVER_DESTINATION = "iw7-mod/custom_scripts/cp/" + IDENT + ".gsc"
SCRIPT_NODE = "scriptfile:custom_scripts/cp/" + IDENT + ".gsc"
BANK_NODE = "soundbank:community_original_sound_v1.all"
RAWFILE_NODE = "rawfile:mod"


def read_server_source(package_root, entry):
    """Measure the exact package file; no claim that its behavior was tested."""
    root = Path(package_root)
    reader.require(root.is_absolute(), "absolute package root required")
    reader.require(entry["role"] == "server" and entry["source"] == SERVER_SOURCE
                   and entry["destination"] == SERVER_DESTINATION
                   and entry["closure_roots"] == [SCRIPT_NODE],
                   "canonical delivered server source binding required")
    path = root / SERVER_SOURCE
    inputs = reader.Inputs()
    raw = inputs.read(path, 16384)
    reader.require(0 < len(raw) <= 16384, "nonempty bounded server GSC required")
    # Same bounded snapshot twice. The later package gate must remeasure it.
    inputs.read(path, 16384)
    return {"source": SERVER_SOURCE, "destination": SERVER_DESTINATION,
            "bytes": len(raw), "sha256": reader.sha(raw)}


def complete(request, package_root):
    """Called after the pinned producer gate; embedded bytes alone are not provenance."""
    reader.require(type(request) is dict and set(request) == {
        "manifest", "reader", "producer_state_path", "producer_state_sha256"}, "closure adapter request differs")
    state_pin, state_path = request["producer_state_sha256"], request["producer_state_path"]
    reader.require(type(state_pin) is str and re.fullmatch(r"[a-fA-F0-9]{64}", state_pin), "producer state pin required")
    reader.require(type(state_path) is str and Path(state_path).is_absolute(), "absolute producer state path required")
    validate = getattr(reader, "validate_closure_evidence", None)
    reader.require(callable(validate), "reviewed static-closure reader dependency required")
    # Revalidate the exact embedded dump bytes; this never calls inspect/read_bank.
    evidence = validate(request["reader"])
    manifest = copy.deepcopy(request["manifest"])
    package = manifest["package"]
    reader.require(manifest["namespace"] == IDENT and package["id"] == IDENT,
                   "original-sound namespace required")
    clients = [entry for entry in package["files"] if entry["role"] == "client"]
    servers = [entry for entry in package["files"] if entry["role"] == "server"]
    reader.require(len(clients) == 3 and len(servers) == 1, "exact original-sound file set required")
    for entry, filename in zip(clients, ("mod.ff", "mod.sabl", "mod.sabs")):
        reader.require(entry["source"] == "client/" + filename
                       and entry["destination"] == "mods/" + IDENT + "/" + filename
                       and {"bytes": entry["bytes"], "sha256": entry["sha256"].lower()} == evidence["artifacts"][filename],
                       "closure artifact differs from delivered client declaration: " + filename)
    closure = package["closure"]
    nodes = {node["id"]: node for node in closure["nodes"]}
    reader.require(len(closure["nodes"]) == 3 and set(nodes) == {BANK_NODE, RAWFILE_NODE, SCRIPT_NODE}
                   and set(closure["roots"]) == set(nodes) and not closure["unresolved"]
                   and all(node["requires"] == [] for node in nodes.values()),
                   "exact closed original-sound nodes required")
    server = read_server_source(package_root, servers[0])
    servers[0].update(bytes=server["bytes"], sha256=server["sha256"])
    nodes[BANK_NODE]["sha256"] = evidence["representations"]["soundbank"]["sha256"]
    nodes[RAWFILE_NODE]["sha256"] = evidence["representations"]["rawfile"]["sha256"]
    nodes[SCRIPT_NODE]["sha256"] = server["sha256"]
    closure.update(status="complete", evidence_ref=(
        state_path + "#sha256=" + state_pin.lower() + ";Reader.closure_evidence;"
        + SERVER_SOURCE + "#sha256=" + server["sha256"]))
    # Protocol, source declarations and every runtime/evidence field stay untouched.
    return {"manifest": manifest, "server_source": server,
            "representations_revalidated": True, "static_closure_complete": True,
            "client_payload_measured": False, "runtime_ready": False, "owner_accepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    args = parser.parse_args()
    try:
        request = reader.strict_json(sys.stdin.buffer.read(262145), limit=262144)
        result = complete(request, args.package_root)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        print(json.dumps({"valid": False, "errors": [str(error)]}))
        return 1
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
