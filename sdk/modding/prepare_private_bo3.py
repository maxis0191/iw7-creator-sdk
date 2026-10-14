"""Prepare the fixed private FF-B project from explicit, retained inputs.

No extraction, compiler, native executable, stock discovery, installer or ZIP.
Static package readiness does not establish native provenance or game acceptance.
"""
import argparse
import copy
import importlib.util
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TEMPLATE_ROOT = HERE
UPSTREAM = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"
API = "iw7.private-bo3-project/1"
MODEL = "p7_fre_platform_cap_02"
MESH = "p7_fre_platform_cap_02_lod0ca80354f"
MATERIAL = "mopw/character_park_clown_zombie_shoes"
GSC = "paris_bo3_static_probe.gsc"
EXPECTED_INPUTS = {
    "fastfile": {"bytes": 9904, "sha256": "50ca9124d35f4ea5e9f017adafcf012df01b9991d1fcde2597c8f0f58aabcd0c"},
    "server-script": {"bytes": 8607, "sha256": "a8b8d07e7d3bad415b1bb69d09954b21342ba54c9d4b4d7137321f9e3f8e637a"},
    "readback": {"bytes": 2274, "sha256": "7f8b628fd3dd8250c24c959017be139b81f6aad92ebe5e1e885d42c98dd6351f"},
}
REFERENCE_INPUTS = {
    "material:" + MATERIAL: {"path": "zone_source/paris_model_probe_recipient.csv", "bytes": 48,
                              "sha256": "e230b6beb069ba65654f919f9b2a75f907b8956c08b557244604918c5a78e2f2"},
    "rawfile:paris_model_probe": {"path": "zone_source/paris_model_probe.csv", "bytes": 107,
                                 "sha256": "085ef65ab49a576c7332e29509d0a85417f3fb5e1fe31419e5d1865880f5eef3"},
    "netconststrings:ncs_mdl_paris_model_probe": {"path": "netconststrings/ncs_mdl_paris_model_probe.json", "bytes": 93,
                                               "sha256": "c10fc3b61cc0cc6df433a08eb0c2ae8a7a83145e7f47573681bab9b97c9be7c4"},
}
READER_DECLARATIONS = [
    {"relative_path": "roundtrip/xmodel/" + MODEL + ".xmb", "bytes": 1089,
     "sha256": "af4cb78463b466fe9cb92f1d24b1dfb706664d255d3aa1d939af0e1e6a68b583"},
    {"relative_path": "roundtrip/xsurface/" + MESH + ".xsb", "bytes": 22456,
     "sha256": "5c93d1769b4fcf500729fbba49474e97dff471962797741a4bceae50a755fd4d"},
]

spec = importlib.util.spec_from_file_location("private_bo3_shared", HERE / "Finalize-BeaconProject.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def check_readback(value):
    expected = {
        "schema": "iw7.model-rigid-roundtrip/2",
        "geometry_profile": "t7-iw7-selected-streamed-render-only-v2",
        "model_name": MODEL, "mesh_name": MESH,
        "selected_counts": {"bones": 1, "roots": 1, "surfaces": 5, "vertices": 560, "triangles": 490},
        "lod0_dist": 1000000.0, "ff": EXPECTED_INPUTS["fastfile"],
        "source_plan_sha256": "750d25d7d34c8c5849aa2048f1052fc1c5fd3c51cafd61e43268f4c003951686",
        "derived_receipt_sha256": "231e9fd55d19d1dd85a391d4e2b73cae2c21e39324ed6d69630f8df0240c0471",
        "inputs": READER_DECLARATIONS,
        "geometry_roundtrip_verified": True, "packed_attributes_byte_identical": True,
        "native_provenance_verified": False, "source_geometry_correspondence_verified": False,
        "dependency_payloads_verified": False, "runtime_verified": False, "pixels_verified": False, "ready": False,
        "material_references": [MATERIAL] * 5,
        "surface_records": [
            {"index": 0, "material_slot": 0, "vertices": 208, "triangles": 200},
            {"index": 1, "material_slot": 1, "vertices": 8, "triangles": 4},
            {"index": 2, "material_slot": 2, "vertices": 34, "triangles": 32},
            {"index": 3, "material_slot": 3, "vertices": 94, "triangles": 62},
            {"index": 4, "material_slot": 4, "vertices": 216, "triangles": 192},
        ],
        "geometry_work_bytes_upper_bound": 41656,
    }
    f.require(f.encoded(value) == f.encoded(expected), "Exact unpromoted FF-B readback declaration required")


def prepare(fastfile, server_script, readback, reference_root, output_root):
    output = Path(os.path.abspath(output_root))
    f.safe_existing(output.parent)
    f.require(not os.path.lexists(output), "Fresh private BO3 output root required")
    paths = {label: f.safe_existing(path) for label, path in (
        ("fastfile", fastfile), ("server-script", server_script), ("readback", readback))}
    references = f.safe_existing(reference_root)
    f.require(references.is_dir(), "Explicit reference root must be a directory")
    roots = {*(path.parent for path in paths.values()), references, f.safe_existing(TEMPLATE_ROOT)}
    f.require(all(not output.is_relative_to(root) and not root.is_relative_to(output) for root in roots),
              "Output overlaps an input root")
    inputs = f.Inputs()
    manifest = inputs.json(TEMPLATE_ROOT, "examples/private-bo3-prop/manifest.json", "template/manifest.json")

    def pinned(root, name, label, expected):
        raw = inputs.read(root, name, label, expected["bytes"])
        f.require(len(raw) == expected["bytes"] and f.sha(raw) == expected["sha256"],
                  "Pinned input size/hash mismatch: " + label)
        return raw

    payloads = {label: pinned(path.parent, path.name, label, EXPECTED_INPUTS[label])
                for label, path in paths.items()}
    reader = f.decoded(payloads["readback"])
    check_readback(reader)
    for node_id, expected in REFERENCE_INPUTS.items():
        pinned(references, expected["path"], "reference/" + node_id, expected)
    nodes = {node["id"]: node for node in manifest["package"]["closure"]["nodes"]}
    files = {entry["id"]: entry for entry in manifest["package"]["files"]}
    f.require(set(files) == {"client_fastfile", "server_display"}, "Exact two delivered files required")
    for file_id, label, name in (("client_fastfile", "fastfile", "mod.ff"), ("server_display", "server-script", GSC)):
        entry = files[file_id]
        f.require(entry["source"] == name and {key: entry[key] for key in ("bytes", "sha256")} == EXPECTED_INPUTS[label],
                  "Template delivered binding differs: " + file_id)
    representations = {
        "scriptfile:custom_scripts/cp/" + GSC: {
            "representation": "delivered-server-source", **inputs.records["server-script"], "bytes_measured_by_recipe": True},
    }
    for node_id, declared in zip(("xmodel:" + MODEL, "xsurface:" + MESH), reader["inputs"]):
        representations[node_id] = {
            "representation": "pinned-reader-declaration", **declared,
            "bytes_measured_by_recipe": False, "hash_origin": "readback declared serialized representation",
        }
    for node_id, expected in REFERENCE_INPUTS.items():
        representations[node_id] = {
            "representation": ("recipient-csv-reference-only" if node_id.startswith("material:") else
                               "zone-csv-inventory-only" if node_id.startswith("rawfile:") else "producer-ncs-source-reference"),
            "relative_path": expected["path"], **inputs.records["reference/" + node_id],
            "reference_bytes_measured_by_recipe": True, "serialized_payload_measured_by_recipe": False,
        }
    f.require(set(nodes) == set(representations) and
              all(node["sha256"] == representations[node_id]["sha256"] for node_id, node in nodes.items()),
              "Template node representations differ from pinned declarations/references")
    plan = f.sdk.validate(manifest, stage="plan", target="native", client_source=UPSTREAM, server_source=UPSTREAM)
    f.require(plan["valid"], "Private BO3 SDK plan invalid: " + "; ".join(plan["errors"]))
    evidence = {
        "schema": API, "inputs": copy.deepcopy(inputs.records), "node_representations": representations,
        "closure_scope": "Declared inventory and measured producer references; not physical recipient material/rawfile closure.",
        "reader": reader, "reader_executed_by_recipe": False,
        "native_prerequisite": {
            "upstream_source": UPSTREAM,
            "private_source_commit": "caccd6981578d96aee44a288108b80956053be48",
            "binary_sha256": "958613f3ade0347f991071a0a8a8502cfb66c816c5c084c5214f05078f7b0296",
            "build_manifest_sha256": "969f4af7b49826fdaca9c83774d39849bf0446adb311049bdc81e34a371145a8",
            "build_manifest_legacy_protocol": 1, "separately_reported_runtime_protocol": 2,
            "installed_binary_measured_by_recipe": False,
        },
        "target_assertions": {"target": "native", "client_source": UPSTREAM, "server_source": UPSTREAM, "protocol": 2},
        "installed": False, "copy_and_play_ready": False, "runtime_ready": False, "owner_accepted": False,
        "ready_to_deploy": False, "physical_dependency_payloads_verified": False,
    }
    outputs = {"manifest.json": f.encoded(manifest), "mod.ff": payloads["fastfile"], GSC: payloads["server-script"],
               "project-evidence.json": f.encoded(evidence)}
    inputs.recheck()
    writer, verified = f.OutputFiles(output), f.Inputs()
    try:
        writer.mkdir(output)

        def write(name, raw):
            f.require(f.identity(f.safe_existing(output).stat())[:2] == writer.directories[output],
                      "Candidate directory identity changed")
            writer.write(name, raw)

        for name, raw in outputs.items():
            write(name, raw)
        package = f.sdk.validate(manifest, root=output, stage="package", target="native",
                                 client_source=UPSTREAM, server_source=UPSTREAM)
        f.require(package["valid"] and package["ready"] and set(package["checked"]) == set(files),
                  "Private BO3 package gate refused: " + "; ".join(package["errors"] + package["pending"]))
        outputs["validation-package.json"] = f.encoded(package)
        write("validation-package.json", outputs["validation-package.json"])
        f.require({path.name for path in output.iterdir()} == set(outputs), "Unexpected candidate contents")
        for name, raw in outputs.items():
            f.require(verified.read(output, name, name, len(raw)) == raw, "Candidate output changed: " + name)
    except Exception:
        writer.cleanup()
        raise
    # Final source drift retains the measured candidate for diagnosis, as in
    # the shared finalizer; an exit failure never qualifies it for delivery.
    inputs.recheck()
    verified.recheck()
    return {"schema": API, "prepared": True, "project_root": str(output), "manifest_path": str(output / "manifest.json"),
            "package_ready": True, "runtime_ready": False, "owner_accepted": False, "installed": False,
            "copy_and_play_ready": False, "ready_to_deploy": False, "bytes_written": writer.bytes,
            "input_files_verified": inputs.records, "output_files_verified": verified.records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastfile", required=True)
    parser.add_argument("--server-script", required=True)
    parser.add_argument("--readback", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.fastfile, args.server_script, args.readback, args.reference_root, args.output)
        status = 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        result = {"schema": API, "prepared": False, "package_ready": False, "runtime_ready": False,
                  "owner_accepted": False, "installed": False, "copy_and_play_ready": False,
                  "ready_to_deploy": False, "errors": [str(error)]}
        status = 1
    print(f.encoded(result).decode("utf-8"), end="")
    return status


if __name__ == "__main__":
    sys.exit(main())
