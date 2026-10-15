"""Bind editable original project inputs; no opaque asset read, writer or build.

This is the ModelLabV2 author-input seam, not a second serializer or package
format. Existing producer modules own geometry, DDS, material and FF validation.
"""
import importlib.util
import math
import re
from pathlib import Path

API = "creator-original-authoring/1"
TEMPLATE_REQUIRED = {"material", "statebits", "statebitsmap"}
TEMPLATE_OPTIONAL = {"stateinfo", "cbi", "cbt"}
FIELDS = {"schema", "namespace", "zone", "model_name", "mesh_name", "material_name",
          "image_name", "geometry_source", "script_source", "texture", "material_template", "placement"}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def select(project, tools_root, *, manifest):
    """Inspect source texts only, preserving pending template/runtime inputs.

    DDS and material sidecars are never opened by Plan. The hashes here bind
    author input snapshots; they are not compiler, asset or runtime evidence.
    """
    f = module(Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py", "author_source_inputs")
    require = f.require
    root = f.safe_existing(project).resolve(strict=True)
    require(root.is_dir(), "Author Project must be a directory")
    inputs = f.Inputs()
    current_manifest = f.decoded(inputs.read(root, "manifest.json", "manifest", 1024 * 1024))
    require(f.encoded(current_manifest) == f.encoded(manifest), "Author manifest changed after contract selection")
    descriptor = f.decoded(inputs.read(root, "authoring.json", "authoring", 65536))
    require(isinstance(descriptor, dict) and set(descriptor) == FIELDS and
            descriptor["schema"] == "iw7.creator-authoring/1", "Exact original authoring input fields required")
    namespace = manifest["namespace"]
    require(descriptor["namespace"] == namespace and descriptor["zone"] == namespace,
            "Author namespace and zone must match the existing community package")
    names = {key: descriptor[key] for key in ("model_name", "mesh_name", "material_name", "image_name")}
    require(all(isinstance(name, str) for name in names.values()), "Original asset names must be strings")
    require(len(set(names.values())) == len(names), "Distinct original asset names required")
    for key, name in names.items():
        require(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9_]{1,62}", name) and
                name.startswith(namespace + "_"), "Namespaced original asset name required: " + key)

    def relative(value):
        require(isinstance(value, str) and f.sdk.transport.safe_path(value), "Safe relative author path required")
        require(not any(part.endswith((".", " ")) or ":" in part for part in value.replace("\\", "/").split("/")),
                "Ordinary author source path required")
        return value

    def text_json(path, label, limit=1024 * 1024):
        require(isinstance(path, str) and path.endswith(".json"), "Explicit source JSON path required")
        return f.decoded(inputs.read(root, relative(path), label, limit))

    script = relative(descriptor["script_source"])
    require(script == namespace + ".gsc", "Author script must use the community namespace entrypoint")
    script_raw = inputs.read(root, script, "script", 65536)
    require(script_raw and b"\x00" not in script_raw, "Nonempty source GSC text required")
    script_raw.decode("utf-8-sig")
    geometry = text_json(descriptor["geometry_source"], "geometry")
    require(isinstance(geometry, dict) and geometry.get("schema") == "iw7.original-mesh-source/1" and
            geometry.get("name") == names["model_name"] and geometry.get("iw7_serialized") is False and
            geometry.get("ready") is False, "Original source mesh identity required; no serialized/readiness claim")
    require(type(geometry.get("surfaces")) is list and len(geometry["surfaces"]) == 1 and
            isinstance(geometry["surfaces"][0], dict) and
            geometry["surfaces"][0].get("material_reference") == names["material_name"],
            "The original surface must bind the declared authored material")
    texture = descriptor["texture"]
    require(isinstance(texture, dict) and set(texture) == {"kind", "source", "slot"} and
            texture["kind"] in ("rgba8", "dds-dx10") and type(texture["slot"]) is int and
            0 <= texture["slot"] < 256, "Explicit texture kind, source and integer slot required")
    relative(texture["source"])
    texture_summary = {"kind": texture["kind"], "source": texture["source"], "slot": texture["slot"],
                       "dds_verified": False}
    if texture["kind"] == "rgba8":
        pixels = text_json(texture["source"], "rgba8")
        require(isinstance(pixels, dict) and set(pixels) == {"width", "height", "pixels"} and
                type(pixels["width"]) is int and type(pixels["height"]) is int and
                1 <= pixels["width"] <= 1024 and 1 <= pixels["height"] <= 1024,
                "Explicit bounded original RGBA8 source required")
        values = pixels["pixels"]
        require(type(values) is list and len(values) == pixels["width"] * pixels["height"] * 4 and
                all(type(value) is int and 0 <= value <= 255 for value in values),
                "RGBA8 source requires exactly four integer bytes per pixel")
        texture_summary.update(width=pixels["width"], height=pixels["height"], source_pixels_bound=True)
    templates = descriptor["material_template"]
    require(isinstance(templates, dict) and TEMPLATE_REQUIRED <= set(templates) <= TEMPLATE_REQUIRED | TEMPLATE_OPTIONAL,
            "Existing material template roles must be explicit")
    for path in templates.values():
        relative(path)
    placement = descriptor["placement"]
    require(isinstance(placement, dict) and set(placement) == {"offset_forward_right_up", "angles", "scale"},
            "Explicit source placement fields required")
    for key in ("offset_forward_right_up", "angles"):
        vector = placement[key]
        require(type(vector) is list and len(vector) == 3 and
                all(type(value) in (int, float) and math.isfinite(value) and abs(value) <= 32768 for value in vector),
                "Finite bounded source placement vector required: " + key)
    require(type(placement["scale"]) in (int, float) and placement["scale"] == 1,
            "Initial rigid author route requires explicit scale 1")
    nodes = {node["id"]: node for node in manifest["package"]["closure"]["nodes"]}
    model, mesh = "xmodel:" + names["model_name"], "xsurface:" + names["mesh_name"]
    material, image = "material:" + names["material_name"], "image:" + names["image_name"]
    ncs = "netconststrings:ncs_mdl_" + namespace
    rawfile = "rawfile:" + namespace
    gsc = "scriptfile:custom_scripts/cp/" + script
    require({model, mesh, material, image, ncs, rawfile, gsc} <= set(nodes),
            "Author graph must declare the actual model, mesh, material, image, NCS, rawfile and GSC")
    require({mesh, material, ncs, rawfile} <= set(nodes[model]["requires"]) and
            image in nodes[material]["requires"] and model in nodes[gsc]["requires"],
            "Author graph must preserve the model/material/image and script dependency edges")
    require(all(nodes[key]["scope"] == "client" for key in (model, mesh, material, image, ncs, rawfile)) and
            nodes[gsc]["scope"] == "server", "Original content belongs to the declared client/server sides")
    require("original-rigid-authoring/1" in manifest["requires"]["client"],
            "Original authoring must retain its unqualified capability, not inherit the cube witness")
    inputs.recheck()
    return {"api": API, "source_contract_valid": True, "descriptor": descriptor, "inputs": inputs.records,
            "geometry_source_bound": True, "geometry_verified": False, "texture": texture_summary,
            "source_scene": {"model_name": names["model_name"], "placement": placement,
                             "transform_verified": False, "physics_serialized": False},
            "opaque_inputs_read": False, "build_executed": False, "package_ready": False,
            "runtime_ready": False, "owner_accepted": False,
            "pending": ["The existing generic rigid producer must validate the authored geometry and prepare writer inputs.",
                        "The existing DDS/material producer must validate the actual texture and explicit template/sidecars.",
                        "A newly measured build/readback, complete closure and unchanged-runtime creator trial remain required."]}
