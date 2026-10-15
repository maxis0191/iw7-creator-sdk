"""Bind editable original project inputs; no opaque asset read, writer or build.

This is the ModelLabV2 author-input seam, not a second serializer or package
format. Existing producer modules own geometry, DDS, material and FF validation.
"""
import importlib.util
import math
import os
import re
import sys
from pathlib import Path

API = "creator-original-authoring/1"
TEMPLATE_REQUIRED = {"material", "statebits", "statebitsmap"}
TEMPLATE_OPTIONAL = {"stateinfo", "cbi", "cbt"}
FIELDS = {"schema", "namespace", "zone", "model_name", "mesh_name", "material_name",
          "image_name", "geometry_source", "script_source", "texture", "material_template", "placement"}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def _select(project, tools_root, *, manifest):
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
    rgba8 = None
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
        rgba8 = pixels
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
    geometry_validated = False
    geometry_producer = Path(tools_root) / "ops/model-lab/geometry.py"
    if geometry_producer.is_file():
        inputs.read(Path(tools_root), "ops/model-lab/geometry.py", "producer/geometry", 128 * 1024)
        verifier = module(geometry_producer, "creator_original_geometry")
        if hasattr(verifier, "validate_authored"):
            verifier.validate_authored(geometry, model_name=names["model_name"], material_reference=names["material_name"])
            geometry_validated = True
    inputs.recheck()
    report = {"api": API, "source_contract_valid": True, "descriptor": descriptor, "inputs": inputs.records,
            "geometry_source_bound": True, "geometry_source_validated": geometry_validated,
            "geometry_verified": False, "texture": texture_summary,
            "source_scene": {"model_name": names["model_name"], "placement": placement,
                             "transform_verified": False, "physics_serialized": False},
            "opaque_inputs_read": False, "build_executed": False, "package_ready": False,
            "runtime_ready": False, "owner_accepted": False,
            "pending": ["The existing generic rigid producer must validate the authored geometry and prepare writer inputs.",
                        "The existing DDS/material producer must validate the actual texture and explicit template/sidecars.",
                        "A newly measured build/readback, complete closure and unchanged-runtime creator trial remain required."]}
    return report, {"shared": f, "root": root, "inputs": inputs, "geometry": geometry, "rgba8": rgba8}


def select(project, tools_root, *, manifest):
    return _select(project, tools_root, manifest=manifest)[0]


def _model_producer(tools_root):
    """Load only the existing reviewed producer, never an arbitrary JSON command."""
    directory = Path(tools_root) / "ops/model-lab"
    for name in ("geometry", "prepare_writer"):
        cached = sys.modules.get(name)
        if cached is not None and Path(cached.__file__).resolve() != (directory / (name + ".py")).resolve():
            raise ValueError("Conflicting producer already loaded; use a fresh Python process")
    previous = sys.path[:]
    try:
        sys.path.insert(0, str(directory))
        producer = module(directory / "prepare_writer.py", "creator_original_writer")
        if not hasattr(producer, "prepare_authored"):
            raise ValueError("Prepared tools predate the reviewed original geometry producer")
        return producer
    finally:
        sys.path[:] = previous


def prepare_writer_inputs(project, output, tools_root, native_source_root, *, manifest):
    """Prepare source/header/writer inputs through the existing producer only.

    No compiler, native binary, stock, FF, reservation or gameplay is invoked.
    Caller-supplied native_source_root is the pinned serializer SOURCE checkout.
    """
    report, context = _select(project, tools_root, manifest=manifest)
    f, root, inputs = context["shared"], context["root"], context["inputs"]
    destination = Path(os.path.abspath(output))
    f.safe_existing(destination.parent)
    native = f.safe_existing(native_source_root).resolve(strict=True)
    f.require(not os.path.lexists(destination) and not destination.is_relative_to(root) and
              not root.is_relative_to(destination) and not destination.is_relative_to(native) and
              not native.is_relative_to(destination), "Fresh nonoverlapping author writer destination required")
    data = report["descriptor"]
    producer = _model_producer(tools_root)
    inputs.recheck()
    result = producer.prepare_authored(destination, native, root / data["geometry_source"],
        namespace=data["namespace"], zone=data["zone"], mesh_name=data["mesh_name"],
        material_reference=data["material_name"])
    f.require(result["model_name"] == data["model_name"] and
              result["geometry_input_sha256"] == report["inputs"]["geometry"]["sha256"],
              "Writer consumed different author geometry; preserve the fresh output for diagnosis")
    checked = producer.verify_authored_preparation(destination)
    f.require(f.encoded(checked) == f.encoded(result) and
              all(result[key] is False for key in ("compiled", "ff_built", "ready")),
              "Written source recipe differs or incorrectly claims a compiled result")
    inputs.recheck()
    return {"api": API, "writer_source_prepared": True, "writer_source": result,
            "author_inputs": report["inputs"], "source_root": str(destination),
            "native_compiled": False, "ff_built": False, "build_verified": False,
            "runtime_ready": False, "owner_accepted": False}


def _material_producer(tools_root):
    directory = Path(tools_root) / "tools-source/asset-bridge/surfaces"
    cached = sys.modules.get("inspect_content")
    if cached is not None and Path(cached.__file__).resolve() != (directory / "inspect_content.py").resolve():
        raise ValueError("Conflicting material producer already loaded; use a fresh Python process")
    previous = sys.path[:]
    try:
        # The reviewed module imports its inspect_content sibling before adding
        # the image bridge. A spec loader alone does not add this directory.
        sys.path.insert(0, str(directory))
        return module(directory / "authored_dds_material.py", "creator_original_material")
    finally:
        sys.path[:] = previous


def material_inputs(project, tools_root, *, manifest):
    """Return existing DDS/material producer payloads from explicit author inputs.

    This operation DOES read supplied template/sidecar bytes and a DDS if chosen.
    It is separate from read-only Plan and never writes an output or starts a tool.
    """
    report, context = _select(project, tools_root, manifest=manifest)
    return _material_inputs(report, context, tools_root)


def _material_inputs(report, context, tools_root):
    f, root, inputs = context["shared"], context["root"], context["inputs"]
    data = report["descriptor"]
    producer = _material_producer(tools_root)
    texture = data["texture"]
    if texture["kind"] == "rgba8":
        # Use the first validated in-memory snapshot, never a reread that could
        # replace/bless a change-read-restore race in the author pixel input.
        pixels = context["rgba8"]
        dds = producer.rgba8_dds(pixels["width"], pixels["height"], bytes(pixels["pixels"]))
    else:
        dds = inputs.read(root, texture["source"], "dds", 17 * 1024 * 1024)
    template = {role: inputs.read(root, path, "template/" + role, 256 * 1024)
                for role, path in data["material_template"].items()}
    inputs.recheck()
    result = producer.prepare_material(zone=data["zone"], image_name=data["image_name"],
        material_name=data["material_name"], texture_slot=texture["slot"], dds=dds, template=template)
    inputs.recheck()
    return result


def stage_ff_inputs(project, writer_run, output, tools_root, *, manifest):
    """Join measured writer inputs and the existing material producer's payloads.

    This DOES read the supplied model artifacts/templates. It never compiles a
    native tool, creates a FF, touches stock or starts a game. The existing stage
    verifier remains the only authority for its artifact/recipe checks.
    """
    report, context = _select(project, tools_root, manifest=manifest)
    f, inputs = context["shared"], context["inputs"]
    writer_root = f.safe_existing(writer_run).resolve(strict=True)
    destination = Path(os.path.abspath(output))
    f.safe_existing(destination.parent)
    project_root = context["root"]
    f.require(not os.path.lexists(destination) and all(
        not destination.is_relative_to(root) and not root.is_relative_to(destination)
        for root in (project_root, writer_root)), "Fresh nonoverlapping authored FF input destination required")
    recipe = f.decoded(inputs.read(writer_root, "writer-source.json", "writer/recipe", 512 * 1024))
    descriptor = report["descriptor"]
    f.require(recipe["namespace"] == descriptor["namespace"] and recipe["zone"] == descriptor["zone"] and
              recipe["model_name"] == descriptor["model_name"] and recipe["mesh_name"] == descriptor["mesh_name"] and
              recipe["material_reference"] == descriptor["material_name"] and
              recipe["geometry_input_sha256"] == report["inputs"]["geometry"]["sha256"],
              "Measured writer belongs to different current author inputs")
    # Reuse the SAME validated project/pixel snapshots; a second selection could
    # otherwise bind a different texture between the writer check and staging.
    material = _material_inputs(report, context, tools_root)
    directory = Path(tools_root) / "ops/model-lab"
    _model_producer(tools_root)
    previous = sys.path[:]
    try:
        sys.path.insert(0, str(directory))
        stage = module(directory / "prepare_ff.py", "creator_original_ff_stage")
        f.require(hasattr(stage, "stage_authored"), "Prepared tools predate the reviewed authored FF stage")
        inputs.recheck()
        result = stage.stage_authored(writer_root, destination, material_inputs=material)
        f.require(all(result[key] is False for key in ("ff_built", "pixels_verified", "ready")),
                  "FF input preparation cannot claim build or runtime qualification")
        inputs.recheck()
    finally:
        sys.path[:] = previous
    return {"api": API, "ff_inputs_staged": True, "source_plan": result,
            "opaque_inputs_read": True, "native_compiled": False, "ff_built": False,
            "build_verified": False, "runtime_ready": False, "owner_accepted": False}
