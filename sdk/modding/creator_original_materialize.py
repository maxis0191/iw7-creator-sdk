"""Consume authored plan/3 writer/FF receipts through the existing Creator route.

No compiler, process, stock path, binary/tool discovery or package writer. Real
serialized inputs retain their separate admission; Source tests use stand-ins.
"""
import copy
import os
from pathlib import Path
import sys

PROFILE = "iw7-authored-rigid-v1"
API = "creator-model-materialize/1"
ASSET_FIELDS = {"source_root", "source_plan_sha256", "derived_receipt_sha256",
                "build_receipt_sha256", "roundtrip_sha256", "surface_roundtrip_sha256", "ff_bytes", "ff_sha256"}


def _author(tools_root):
    import importlib.util
    spec = importlib.util.spec_from_file_location("original_materialize_author", Path(tools_root) / "sdk/modding/creator_authoring.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def _checked(project, source_root, build_root, tools_root, manifest):
    author = _author(tools_root)
    selection, context = author._select(project, tools_root, manifest=manifest)
    f, inputs, project = context["shared"], context["inputs"], context["root"]
    require = f.require
    require(f.sdk.validate(manifest, stage="plan")["valid"], "Valid authored community contract required")
    require(manifest["package"]["maps"] == ["cp_zmb"] and manifest["package"]["delivery"] == "mod" and
            manifest["package"]["closure"]["status"] == "incomplete" and
            manifest["compatibility"]["network_protocol"] == 2 and
            all(item["status"] == "pending" and item["reference"] is None and not item["maps"]
                for item in manifest["package"]["evidence"]), "Authored cp_zmb mod qualification must remain pending")
    source, build = (f.safe_existing(path).resolve(strict=True) for path in (source_root, build_root))
    roots = (project, source, build)
    require(all(path.is_dir() for path in roots) and all(not a.is_relative_to(b) and not b.is_relative_to(a)
            for i, a in enumerate(roots) for b in roots[i+1:]), "Separate project/source/build directories required")
    project_identity = f.identity(project.stat())[:2]

    def read(root, name, label, limit=1024 * 1024):
        require(sum(item["bytes"] for item in inputs.records.values()) + limit <= 128 * 1024 * 1024,
                "Authored input working envelope exceeded")
        first = inputs.reads.copy()
        raw = inputs.read(root, name, label, limit)
        require(all(inputs.reads[path] == snapshot for path, snapshot in first.items()),
                "First authored input snapshot changed during repeated read")
        return raw

    plan_raw = read(source, "model-ff-plan.json", "source/plan")
    plan = f.decoded(plan_raw)
    data = selection["descriptor"]
    require(plan["schema"] == "iw7.model-ff-plan/3" and plan["geometry_profile"] == PROFILE and
            all(plan[key] == data[key] for key in ("namespace", "zone", "model_name", "mesh_name")) and
            plan["material_reference"] == data["material_name"] and plan["image"]["name"] == data["image_name"],
            "Authored FF plan must use the actual current project names")
    require(all(plan[key] is False for key in ("ff_built", "pixels_verified", "ready", "physics_serialized")),
            "Source plan cannot promote execution or physics")
    recipe_raw = read(source, "evidence/writer/writer-source.json", "source/writer-recipe")
    recipe = f.decoded(recipe_raw)
    require(recipe["geometry_input_sha256"] == selection["inputs"]["geometry"]["sha256"],
            "Writer belongs to different current authored geometry")
    derivation = read(source, "evidence/material-inputs.json", "source/derivation")
    # Reuse the material producer against the first current author snapshots.
    # A valid old FF stage alone must not approve changed pixels/templates.
    first = inputs.reads.copy()
    current_material = author._material_inputs(selection, context, tools_root)
    require(all(inputs.reads[path] == snapshot for path, snapshot in first.items()),
            "First author snapshot changed during material preparation")
    material_metadata = {key: value for key, value in current_material.items() if key != "files"}
    material_metadata["files"] = {name: f.sha(raw) for name, raw in current_material["files"].items()}
    require(f.encoded(f.decoded(derivation)) == f.encoded(material_metadata),
            "Staged material differs from current author pixels/template/slot")
    # Enroll every fixed/evidence input the existing verifier may consult before
    # invoking it; do not replace the initial snapshot after a reader returns.
    require(type(recipe["source_files"]) is dict and 1 <= len(recipe["source_files"]) <= 16 and
            type(plan["source_files"]) is dict and 1 <= len(plan["source_files"]) <= 32 and
            type(plan["dump_files"]) is list and 1 <= len(plan["dump_files"]) <= 32 and
            len(set(plan["dump_files"])) == len(plan["dump_files"]), "Bounded distinct authored inventories required")
    for name in ("writer-provenance.json", *recipe["source_files"]):
        read(source, "evidence/writer/" + name, "source/writer/" + name, 512 * 1024)
    source_data = {name: read(source, name, "source/file/" + name, 20 * 1024 * 1024)
                   for name in plan["source_files"]}
    state_raw = read(build, "state.local.json", "build/state")
    state = f.decoded(state_raw)
    geometry_raw = read(build, "geometry-roundtrip.json", "build/geometry")
    surface_raw = read(build, "surface-roundtrip.json", "build/surface")
    geometry, surface = f.decoded(geometry_raw), f.decoded(surface_raw)
    require(state["Schema"] == "iw7.model-ff-build/1" and state["Status"] == "BootstrapInventoryVerified" and
            all(state.get(key) is True for key in ("Restored", "StockPreserved", "InventoryVerified", "GeometryRoundtripVerified",
                                                 "MaterialFieldsVerified", "SerializedImageBytesVerified")) and
            state["RestorationStatus"] == "Confirmed" and state.get("RetainedLeaseToken") is None and
            state.get("Failure") is None and state.get("CleanupError") is None and state.get("Ready") is False,
            "Restored successful authored FF build required; pending/failed states refuse")
    for phase in ("Build", "Offline", "Dump", "GeometryReader", "SurfaceReader"):
        require(type(state[phase]["ExitCode"]) is int and state[phase]["ExitCode"] == 0,
                "All actual authored FF phases require integer exit zero")
    require(f.encoded(state["SourcePlan"]) == f.encoded(plan) and state["SourcePlanSHA256"].lower() == f.sha(plan_raw) and
            state["GeometryEvidenceSHA256"].lower() == f.sha(geometry_raw) and
            state["SurfaceEvidenceSHA256"].lower() == f.sha(surface_raw), "Actual FF/geometry/surface receipt binding differs")
    ff = read(build, "mod.ff", "build/ff", 32 * 1024 * 1024)
    require(state["FF"]["Path"] == "mod.ff" and type(state["FF"]["Bytes"]) is int and
            state["FF"]["Bytes"] == len(ff) and state["FF"]["SHA256"].lower() == f.sha(ff), "Actual FF tuple differs")
    ff_tuple = {"bytes": len(ff), "sha256": f.sha(ff)}
    for receipt in (geometry, surface):
        require(type(receipt["ff"]["bytes"]) is int and receipt["ff"]["bytes"] == len(ff) and receipt["ff"]["sha256"].lower() == f.sha(ff) and
                receipt["source_plan_sha256"].lower() == f.sha(plan_raw), "Roundtrip belongs to another FF/source plan")
    require(geometry["schema"] == "iw7.model-roundtrip/1" and geometry["geometry_profile"] == PROFILE and
            geometry["geometry_roundtrip_verified"] is True and geometry["ready"] is False and
            geometry["physics_serialized"] is False and geometry["iw7_normal_encoding_verified"] is False and
            all(geometry[key] == plan[key] for key in ("namespace", "zone", "model_name", "mesh_name", "material_reference")) and
            all(type(geometry[key]) is int and type(plan["selected_counts"][key]) is int and
                geometry[key] == plan["selected_counts"][key] for key in ("vertices", "triangles")),
            "Native geometry receipt identity/counts differ")
    geometry_stdout = Path(state["GeometryReader"]["Stdout"])
    surface_stdout = Path(state["SurfaceReader"]["Stdout"])
    require(all(path.is_absolute() for path in (geometry_stdout, surface_stdout)), "Absolute reader outputs required")
    geometry_stdout, surface_stdout = (f.safe_existing(path).resolve(strict=True) for path in (geometry_stdout, surface_stdout))
    require(all(path.parent == build for path in (geometry_stdout, surface_stdout)),
            "Reader outputs must be directly under the retained build")
    raw_geometry = f.decoded(read(build, geometry_stdout.name, "build/native-geometry-stdout"))
    require(f.encoded(raw_geometry) == f.encoded({key: value for key, value in geometry.items()
                            if key not in ("ff", "source_plan_sha256", "dumped_artifacts")}),
            "Enriched geometry receipt differs from its actual native output")
    require(read(build, surface_stdout.name, "build/surface-stdout") == surface_raw,
            "Retained surface receipt differs from actual reader output")
    artifacts = geometry["dumped_artifacts"]
    require(type(artifacts) is list and len(artifacts) == 2 and
            {item["path"] for item in artifacts} == set(plan["artifact_paths"]), "Exact two geometry dump bindings required")
    dumps = {}
    for item in artifacts:
        raw = read(build, "roundtrip/" + item["path"], "build/dump/" + item["path"])
        require(type(item["bytes"]) is int and item["bytes"] == len(raw) and item["sha256"].lower() == f.sha(raw),
                "Geometry dump differs from the native readback binding")
        dumps[item["path"]] = raw
    for name in plan["dump_files"]:
        if name not in dumps:
            dumps[name] = read(build, "roundtrip/" + name, "build/dump/" + name, 20 * 1024 * 1024)
    # Delegate source/material/image parsing to the existing independent producer.
    author._model_producer(tools_root)
    previous = sys.path[:]
    try:
        sys.path.insert(0, str(Path(tools_root) / "ops/model-lab"))
        verifier = author.module(Path(tools_root) / "ops/model-lab/prepare_ff.py", "creator_authored_readback")
        require(f.encoded(verifier.verify_authored_stage(source)) == f.encoded(plan), "Authored stage verification differs")
        measured = verifier.verify_authored_dump(source, build / "roundtrip", build / "mod.ff")
        require(f.encoded(measured) == f.encoded(surface), "Actual image/material readback differs from supplied receipt")
    finally:
        sys.path[:] = previous
    inputs.recheck()
    require(f.identity(f.safe_existing(project).stat())[:2] == project_identity, "Author directory changed")
    return {"f": f, "inputs": inputs, "project": project, "source": source, "build": build,
            "selection": selection, "plan": plan, "plan_raw": plan_raw, "recipe": recipe,
            "derivation": derivation, "state_raw": state_raw, "geometry_raw": geometry_raw,
            "surface_raw": surface_raw, "ff": ff, "ff_tuple": ff_tuple, "dumps": dumps,
            "source_data": source_data, "gsc": context["script"], "project_identity": project_identity}


def bind(project, source_root, build_root, tools_root, *, manifest, review_reference):
    checked = _checked(project, source_root, build_root, tools_root, manifest)
    f, inputs, root = checked["f"], checked["inputs"], checked["project"]
    f.require(isinstance(review_reference, str) and 0 < len(review_reference.strip()) <= 1024,
              "Explicit GSC/closure review declaration required")
    destination = root / "composition.json"
    f.require(not os.path.lexists(destination), "Existing author composition must be preserved")
    script = checked["selection"]["descriptor"]["script_source"]
    gsc = checked["gsc"]
    descriptor = {"schema": "iw7.creator-model-composition/1", "assets": {
        "source_root": str(checked["source"]), "source_plan_sha256": f.sha(checked["plan_raw"]),
        "derived_receipt_sha256": f.sha(checked["derivation"]), "build_receipt_sha256": f.sha(checked["state_raw"]),
        "roundtrip_sha256": f.sha(checked["geometry_raw"]), "surface_roundtrip_sha256": f.sha(checked["surface_raw"]),
        "ff_bytes": len(checked["ff"]), "ff_sha256": f.sha(checked["ff"])}, "script": {
        "path": script, "bytes": len(gsc), "sha256": f.sha(gsc), "review_reference": review_reference,
        "closure_sha256": f.sha(f.encoded(manifest["package"]["closure"]))}}
    raw = f.encoded(descriptor)
    inputs.recheck()
    f.require(f.identity(f.safe_existing(root).stat())[:2] == checked["project_identity"], "Author directory changed")
    with destination.open("xb") as stream:
        stream.write(raw)
    verified = f.Inputs()
    f.require(verified.read(root, "composition.json", "composition", 65536) == raw, "New composition changed")
    inputs.recheck()
    verified.recheck()
    f.require(f.identity(f.safe_existing(root).stat())[:2] == checked["project_identity"], "Author directory changed")
    return {"bindings_written": True, "composition_path": str(destination), "composition": descriptor,
            "build_verified": False, "materialized": False, "package_ready": False,
            "runtime_ready": False, "owner_accepted": False,
            "pending": ["Source/FF/reader bindings are local declarations; runtime and package capability remain unqualified."]}


def materialize(project, build_root, output_root, tools_root, *, manifest, client_source, server_source):
    author = _author(tools_root)
    f = author.module(Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py", "authored_binding_inputs")
    project = f.safe_existing(project).resolve(strict=True)
    binding_inputs = f.Inputs()
    binding_raw = binding_inputs.read(project, "composition.json", "project/composition", 65536)
    descriptor = f.decoded(binding_raw)
    f.require(type(descriptor) is dict and set(descriptor) == {"schema", "assets", "script"} and
              descriptor["schema"] == "iw7.creator-model-composition/1", "Existing model composition envelope required")
    assets, script = descriptor["assets"], descriptor["script"]
    f.require(type(assets) is dict and set(assets) == ASSET_FIELDS and type(script) is dict and
              set(script) == {"path", "bytes", "sha256", "review_reference", "closure_sha256"},
              "Explicit authored geometry/surface/GSC bindings required")
    f.require(isinstance(assets["source_root"], str) and Path(assets["source_root"]).is_absolute(),
              "Explicit retained authored source root required")
    checked = _checked(project, assets["source_root"], build_root, tools_root, manifest)
    f, inputs = checked["f"], checked["inputs"]
    inputs.reads.update(binding_inputs.reads)
    inputs.records.update(binding_inputs.records)
    plan, data = checked["plan"], checked["selection"]["descriptor"]
    for key, raw in (("source_plan_sha256", checked["plan_raw"]), ("derived_receipt_sha256", checked["derivation"]),
                     ("build_receipt_sha256", checked["state_raw"]), ("roundtrip_sha256", checked["geometry_raw"]),
                     ("surface_roundtrip_sha256", checked["surface_raw"]), ("ff_sha256", checked["ff"])):
        f.require(f.pin(assets[key]) and assets[key].lower() == f.sha(raw), "Authored composition input changed: " + key)
    gsc = checked["gsc"]
    f.require(type(assets["ff_bytes"]) is int and assets["ff_bytes"] == len(checked["ff"]) and
              script["path"] == data["script_source"] and type(script["bytes"]) is int and script["bytes"] == len(gsc) and
              f.pin(script["sha256"]) and script["sha256"].lower() == f.sha(gsc) and
              isinstance(script["review_reference"], str) and 0 < len(script["review_reference"].strip()) <= 1024 and
              f.pin(script["closure_sha256"]) and script["closure_sha256"].lower() == f.sha(f.encoded(manifest["package"]["closure"])),
              "Reviewed author GSC/closure or measured payload differs")
    output = Path(os.path.abspath(output_root))
    output = f.safe_existing(output.parent).resolve(strict=True) / output.name
    f.require(not os.path.lexists(output) and all(not output.is_relative_to(root) and not root.is_relative_to(output)
              for root in (checked["project"], checked["source"], checked["build"])), "Fresh nonoverlapping author candidate required")
    result = copy.deepcopy(manifest)
    f.require(result["package"]["closure"]["status"] == "incomplete" and
              all(item["status"] == "pending" and item["reference"] is None and not item["maps"]
                  for item in result["package"]["evidence"]), "Authored qualification must remain explicitly pending")
    result["package"]["closure"].update(status="incomplete", evidence_ref="finalization.json#node_representations")
    nodes = {node["id"]: node for node in result["package"]["closure"]["nodes"]}
    representations = []
    model, mesh = "xmodel:" + data["model_name"], "xsurface:" + data["mesh_name"]
    material, image = "material:" + data["material_name"], "image:" + data["image_name"]
    script_id = "scriptfile:custom_scripts/cp/" + data["script_source"]
    ncs_id = "netconststrings:" + plan["ncs_name"]
    bound = {model: checked["dumps"]["xmodel/" + data["model_name"] + ".xmb"],
             mesh: checked["dumps"]["xsurface/" + data["mesh_name"] + ".xsb"],
             material: checked["dumps"]["materials/" + data["material_name"] + ".json"],
             image: checked["dumps"]["images/" + data["image_name"] + ".iw7Image"],
             script_id: gsc, ncs_id: checked["source_data"]["netconststrings/" + plan["ncs_name"] + ".json"]}
    for node_id, raw in bound.items():
        f.require(nodes[node_id]["sha256"] in (None, f.sha(raw)), "Declared author node changed: " + node_id)
        nodes[node_id]["sha256"] = f.sha(raw)
        representations.append({"id": node_id, "bytes": len(raw), "sha256": f.sha(raw),
                                "representation": "Verified source NCS" if node_id == ncs_id else
                                    "Reviewed GSC source" if node_id == script_id else "Retained authored FF dump"})
    # Dependencies come from the existing material producer, not guessed shader
    # names. Missing recipient/CBT qualification remains explicit and blocking.
    references = plan["recipient_references"]
    for kind, name in [("techset", references["techset"]), *[("image", name) for name in references["images"]]]:
        ident = kind + ":" + name
        if ident not in nodes:
            node = {"id": ident, "kind": "other" if kind == "techset" else "image", "scope": "recipient",
                    "sha256": None, "requires": []}
            result["package"]["closure"]["nodes"].append(node)
            nodes[ident] = node
        f.require(nodes[ident]["scope"] == "recipient", "Recipient/local asset collision in authored graph")
        if ident not in nodes[material]["requires"]:
            nodes[material]["requires"].append(ident)
    files = result["package"]["files"]
    f.require(len(files) == 2 and sorted(entry["role"] for entry in files) == ["client", "server"],
              "One authored FF and standalone GSC payload required")
    outputs = {"mod.ff": checked["ff"], data["script_source"]: gsc}
    for entry in files:
        client = entry["role"] == "client"
        name = "mod.ff" if client else data["script_source"]
        destination = "mods/" + data["namespace"] + "/mod.ff" if client else "iw7-mod/custom_scripts/cp/" + name
        f.require(entry["destination"] == destination and entry["closure_roots"] == [model if client else script_id] and
                  entry["bytes"] in (None, len(outputs[name])) and entry["sha256"] in (None, f.sha(outputs[name])),
                  "Authored payload destination/identity differs")
        entry.update(source=name, bytes=len(outputs[name]), sha256=f.sha(outputs[name]))
    blockers = ["Original author runtime capability remains blocked pending a measured independent creator loop.",
                "Recipient technique/other image resolution, native CBT semantics and zone rawfile representation remain unqualified.",
                "GSC import/linking, rendered pixels, real input, multiplayer and owner acceptance remain unqualified."]
    evidence = {"api": API, "adapter": "ModelLabV2", "geometry_profile": PROFILE, "composition": descriptor,
                "inputs": inputs.records, "node_representations": representations, "build_executed": False,
                "geometry_roundtrip_rechecked": True, "surface_roundtrip_rechecked": True,
                "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
                "native_provenance_verified": False, "recipient_closure_complete": False, "blockers": blockers}
    plan_check = f.sdk.validate(result, stage="plan", client_source=client_source, server_source=server_source)
    f.require(plan_check["valid"], "Materialized authored contract invalid: " + "; ".join(plan_check["errors"]))
    outputs.update({"manifest.json": f.encoded(result), "finalization.json": f.encoded(evidence),
                    "validation-plan.json": f.encoded(plan_check)})
    inputs.recheck()
    output.mkdir()
    directory_identity = f.identity(output.stat())[:2]
    for name, raw in outputs.items():
        f.require(f.identity(f.safe_existing(output).stat())[:2] == directory_identity, "Candidate directory changed")
        with (output / name).open("xb") as stream:
            stream.write(raw)
    package_check = f.sdk.validate(result, root=output, stage="package", client_source=client_source, server_source=server_source)
    f.require(package_check["ready"] is False and set(package_check["checked"]) == {entry["id"] for entry in files},
              "Unqualified authored package gate or payload checking changed")
    outputs["validation-package.json"] = f.encoded(package_check)
    f.require(f.identity(f.safe_existing(output).stat())[:2] == directory_identity, "Candidate directory changed")
    with (output / "validation-package.json").open("xb") as stream:
        stream.write(outputs["validation-package.json"])
    verified = f.Inputs()
    for name, raw in outputs.items():
        f.require(verified.read(output, name, name, len(raw)) == raw, "Materialized authored output changed")
    inputs.recheck()
    verified.recheck()
    f.require(f.identity(f.safe_existing(output).stat())[:2] == directory_identity, "Candidate directory changed")
    return {"api": API, "materialized": True, "candidate_root": str(output), "manifest_path": str(output / "manifest.json"),
            "creator_output_verified": True, "candidate_files_verified": verified.records,
            "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
            "blockers": blockers, "bytes_written": sum(map(len, outputs.values())),
            "exact_hashes": {"ff": f.sha(checked["ff"]), "gsc": f.sha(gsc), "manifest": f.sha(outputs["manifest.json"]),
                             "finalization": f.sha(outputs["finalization.json"])}}
