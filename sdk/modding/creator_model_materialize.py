"""Select/bind/materialize explicit ModelLab inputs; no compiler/runner/ZIP writer.

Reuse resident or original-arena readback and SDK contracts. Review references are
explicit operator declarations, not authenticated GSC or native execution proof.
"""
import copy
import importlib.util
import os
from pathlib import Path
import re
import sys

API = "creator-model-materialize/1"
PROFILE = "t7-iw7-resident-static-v2"
ARENA_PROFILE = "iw7-original-arena-rigid-v1"
ARENA_COUNTS = {"bones": 1, "roots": 1, "surfaces": 1, "vertices": 168, "triangles": 84}
ARENA_WRITER = "evidence/arena-writer-source.json"
ARENA_GEOMETRY = "evidence/geometry.source.json"
MATERIAL = "mopw/character_park_clown_zombie_shoes"
METADATA = 1024 * 1024
INPUT_LIMIT = 96 * METADATA
OUTPUT_LIMIT = 36 * METADATA


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def source_profile(plan, adapter, manifest, require):
    require(adapter in ("ModelLabV2", "OriginalArenaV1"), "Explicit supported model adapter required")
    arena = adapter == "OriginalArenaV1"
    require(plan["schema"] == ("iw7.model-ff-plan/1" if arena else "iw7.model-ff-plan/2") and
            plan["geometry_profile"] == (ARENA_PROFILE if arena else PROFILE),
            "Explicit " + ("original arena" if arena else "resident v2") + " source plan required")
    if arena:
        require(plan["origin"] == "authored-arena" and plan["zone"] == "paris_model_probe" and
                plan["model_name"] == "paris_original_arena" and plan["mesh_name"] == "paris_original_arena_lod0" and
                plan["material_reference"] == MATERIAL and plan["selected_counts"] == ARENA_COUNTS and
                all(type(n) is int for n in plan["selected_counts"].values()), "Explicit original arena identity/counts required")
        require("original-arena-display/1" in manifest["requires"]["client"] and
                not {"xmodel-rigid/1", "skeletal-animation-import/1"}.intersection(manifest["requires"]["client"]) and
                "model-netconststrings/1" in manifest["requires"]["engine"],
                "Original arena requires its blocked capability and NCS; no historical cube or rig qualification")
        require(all(plan[key] is False for key in ("material_payload_copied", "native_provenance_verified",
                "physics_serialized", "ff_built", "pixels_verified", "ready")), "Source plan cannot promote arena qualification")
        require(plan["lod0_dist"] == 1000000 and plan["has_lods"] is True and
                plan["shadow_cutoff_lod"] == 6 and plan["collision_lod"] == 255, "Explicit arena LOD policy required")
        model, mesh = "xmodel:" + plan["model_name"], "xsurface:" + plan["mesh_name"]
        nodes = {n["id"]: n for n in manifest["package"]["closure"]["nodes"]}
        require({n["id"] for n in nodes.values() if n["scope"] == "client"} ==
                {model, mesh, "netconststrings:ncs_mdl_paris_model_probe", "rawfile:paris_model_probe"} and
                set(nodes[model]["requires"]) == {mesh, "netconststrings:ncs_mdl_paris_model_probe",
                    "rawfile:paris_model_probe", "material:" + MATERIAL} and
                nodes["material:" + MATERIAL]["scope"] == "recipient", "Author closure must bind the real original arena names")
    return arena


def arena_inputs(source, plan, read, require):
    """Retain the first snapshot of every file the World reader can consult."""
    sources = {"xmodel/paris_original_arena.xmb", "xsurface/paris_original_arena_lod0.xsb",
               "netconststrings/ncs_mdl_paris_model_probe.json", "zone_source/paris_model_probe.csv",
               "zone_source/paris_model_probe_recipient.csv"}
    names = [*sources, ARENA_GEOMETRY, ARENA_WRITER, "model-ff-plan.json"]
    require(set(plan["source_files"]) == sources and isinstance(plan["validation_files"], list) and
            len(plan["validation_files"]) == len(names) and set(plan["validation_files"]) == set(names),
            "Exact eight original arena validation inputs required")
    # The plan and writer already have their first snapshots under fixed labels.
    snapshots = {}
    for name in sorted(set(names) - {"model-ff-plan.json", ARENA_WRITER}):
        limit = 128 * 1024 if name == ARENA_GEOMETRY else 8192
        snapshots[name] = read(source, name, "source/" + name, limit)
    return snapshots


def arena_reader(tools_root):
    return module(Path(tools_root) / "tools-source/asset-bridge/world/original-arena/model_lab.py",
                  "creator_original_arena_verifier")


def select_arena(source_root, tools_root, *, manifest):
    """Read only the staged original geometry, never stock, a tool or a FF."""
    f = module(Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py", "model_shared_checks")
    source = f.safe_existing(source_root).resolve(strict=True)
    f.require(source.is_dir(), "Original arena ModelSourceRoot must be a directory")
    inputs = f.Inputs()
    raw = inputs.read(source, "model-ff-plan.json", "source/plan", 65536)
    plan = f.decoded(raw)
    source_profile(plan, "OriginalArenaV1", manifest, f.require)
    inputs.read(source, ARENA_WRITER, "source/derivation", 65536)
    arena_inputs(source, plan, inputs.read, f.require)
    reader = arena_reader(tools_root)
    checked = reader.verify_stage(source)[0]
    f.require(f.encoded(plan) == f.encoded(checked), "Original arena source verification differs")
    inputs.recheck()
    return {"geometry_profile": ARENA_PROFILE, "origin": "authored-arena", "source_root": str(source),
            "source_plan_sha256": f.sha(raw), "model_name": plan["model_name"], "mesh_name": plan["mesh_name"],
            "selected_counts": plan["selected_counts"], "material_reference": plan["material_reference"],
            "inputs": inputs.records, "build_executed": False, "package_ready": False,
            "runtime_ready": False, "owner_accepted": False,
            "pending": ["Original arena runtime linking and visible pixels remain unqualified.",
                        "No solid collision, physics or gameplay qualification is supplied."]}


def bind(project, source_root, build_root, tools_root, *, manifest, review_reference, adapter="ModelLabV2"):
    """Write the existing composition descriptor from stable authored inputs.

    This binds bytes and declarations only. Materialize remains responsible for
    independent geometry/build validation; no qualification is added here.
    """
    f = module(Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py", "model_shared_checks")
    require = f.require
    roots = [f.safe_existing(p).resolve(strict=True) for p in (project, source_root, build_root)]
    project, source, build = roots
    require(all(p.is_dir() for p in roots), "Project/source/build roots must be directories")
    root_id = f.identity(project.stat())[:2]
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots) for b in roots[i + 1:]),
            "Project/source/build roots must be separate")
    destination = project / "composition.json"
    require(not os.path.lexists(destination), "Bind requires absent composition.json; existing author input is preserved")
    require(isinstance(review_reference, str) and 0 < len(review_reference.strip()) <= 1024,
            "Bind requires an explicit GSC/closure review reference")
    inputs = f.Inputs()
    original = f.decoded(inputs.read(project, "manifest.json", "project/manifest", METADATA))
    require(f.encoded(original) == f.encoded(manifest), "Project manifest changed after Creator compatibility checks")
    ident = original["namespace"]
    gsc_name = ident + ".gsc"
    require(f.sdk.transport.safe_path(gsc_name), "Existing <namespace>.gsc source required")
    gsc = inputs.read(project, gsc_name, "project/gsc", 65536)
    plan_raw = inputs.read(source, "model-ff-plan.json", "source/plan", METADATA)
    plan = f.decoded(plan_raw)
    if adapter == "ModelLabV2" and plan.get("geometry_profile") == "iw7-authored-rigid-v1":
        authored = module(Path(tools_root) / "sdk/modding/creator_original_materialize.py", "creator_original_materialize")
        return authored.bind(project, source, build, tools_root, manifest=original, review_reference=review_reference)
    arena = source_profile(plan, adapter, original, require)
    model_id, mesh_id = "xmodel:" + plan["model_name"], "xsurface:" + plan["mesh_name"]
    declared = {node["id"] for node in original["package"]["closure"]["nodes"]}
    require({model_id, mesh_id}.issubset(declared),
            "Author closure must use the source plan's model and mesh names: " + model_id + ", " + mesh_id)
    derived = inputs.read(source, ARENA_WRITER if arena else "derived-export.json", "source/derivation", METADATA)
    if arena:
        arena_inputs(source, plan, inputs.read, require)
        require(f.encoded(arena_reader(tools_root).verify_stage(source)[0]) == f.encoded(plan),
                "Original arena source verification differs")
    state_raw = inputs.read(build, "state.local.json", "build/state", METADATA)
    state = f.decoded(state_raw)
    roundtrip = inputs.read(build, "geometry-roundtrip.json", "build/roundtrip", METADATA)
    ff = inputs.read(build, "mod.ff", "build/ff", 32 * METADATA)
    require(state["SourcePlanSHA256"].lower() == f.sha(plan_raw) and
            f.encoded(state["SourcePlan"]) == f.encoded(plan), "Retained build/source plan differs")
    require(state["FF"]["Path"] == "mod.ff" and type(state["FF"]["Bytes"]) is int and
            state["FF"]["Bytes"] == len(ff) and state["FF"]["SHA256"].lower() == f.sha(ff),
            "Retained build FF tuple differs")
    require(state["GeometryEvidenceSHA256"].lower() == f.sha(roundtrip),
            "Retained build/roundtrip differs")
    descriptor = {"schema": "iw7.creator-model-composition/1", "assets": {
        "source_root": str(source), "source_plan_sha256": f.sha(plan_raw),
        "derived_receipt_sha256": f.sha(derived), "build_receipt_sha256": f.sha(state_raw),
        "roundtrip_sha256": f.sha(roundtrip), "ff_bytes": len(ff), "ff_sha256": f.sha(ff)}, "script": {
        "path": gsc_name, "bytes": len(gsc), "sha256": f.sha(gsc),
        "review_reference": review_reference, "closure_sha256": f.sha(f.encoded(original["package"]["closure"]))}}
    raw = f.encoded(descriptor)
    require(len(raw) <= 65536, "Composition descriptor exceeds existing input bound")
    inputs.recheck()
    require(f.identity(f.safe_existing(project).stat())[:2] == root_id, "Author directory identity changed")
    with destination.open("xb") as stream:
        stream.write(raw)
    # Retain a failed/partial descriptor for diagnosis; never replace author data.
    verified = f.Inputs()
    require(verified.read(project, "composition.json", "composition", len(raw)) == raw,
            "Written composition changed")
    inputs.recheck()
    verified.recheck()
    require(f.identity(f.safe_existing(project).stat())[:2] == root_id, "Author directory identity changed")
    return {"bindings_written": True, "composition_path": str(destination), "composition": descriptor,
            "build_verified": False, "materialized": False, "package_ready": False,
            "runtime_ready": False, "owner_accepted": False,
            "pending": ["Run Materialize to independently validate the retained geometry and build.",
                        "The GSC/closure review reference is an author declaration, not authenticated qualification."]}


def materialize(project, build_root, output_root, tools_root, *, manifest, client_source, server_source, adapter="ModelLabV2"):
    f = module(Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py", "model_shared_checks")
    require = f.require
    project, build = f.safe_existing(project), f.safe_existing(build_root)
    output = Path(os.path.abspath(output_root))
    f.safe_existing(output.parent)
    require(not os.path.lexists(output), "Fresh ModelLab materialization destination required")
    inputs = f.Inputs()

    def read(root, name, label, limit=METADATA):
        require(f.sdk.transport.safe_path(name), "Unsafe ModelLab input path")
        path = f.safe_existing(root / name)
        require(path.is_relative_to(root), "ModelLab input escapes its explicit root")
        used = sum(item["bytes"] for key, item in inputs.records.items() if key != label)
        require(used + path.stat().st_size <= INPUT_LIMIT, "ModelLab materialization input budget exceeded")
        raw = inputs.read(root, name, label, limit)
        require(sum(item["bytes"] for item in inputs.records.values()) <= INPUT_LIMIT,
                "ModelLab materialization input budget exceeded")
        return raw

    def document(root, name, label, limit=METADATA):
        value = f.decoded(read(root, name, label, limit))
        require(isinstance(value, dict), "ModelLab JSON object required: " + label)
        return value

    def exact(value, keys, label):
        require(isinstance(value, dict) and set(value) == set(keys), "Explicit " + label + " fields required")

    def pinned(root, name, label, pin, limit=METADATA):
        require(f.pin(pin), "Explicit SHA256 required: " + label)
        raw = read(root, name, label, limit)
        require(f.sha(raw) == pin.lower(), "Pinned input differs: " + label)
        return raw

    original = document(project, "manifest.json", "project/manifest")
    require(f.encoded(original) == f.encoded(manifest), "Project manifest changed after Creator compatibility checks")
    descriptor = document(project, "composition.json", "project/composition", 65536)
    if adapter == "ModelLabV2" and isinstance(descriptor.get("assets"), dict) and "surface_roundtrip_sha256" in descriptor["assets"]:
        authored = module(Path(tools_root) / "sdk/modding/creator_original_materialize.py", "creator_original_materialize")
        return authored.materialize(project, build, output, tools_root, manifest=original,
                                    client_source=client_source, server_source=server_source)
    exact(descriptor, ("schema", "assets", "script"), "ModelLab composition")
    require(descriptor["schema"] == "iw7.creator-model-composition/1", "ModelLab composition schema required")
    assets, script = descriptor["assets"], descriptor["script"]
    exact(assets, ("source_root", "source_plan_sha256", "derived_receipt_sha256", "build_receipt_sha256",
                   "roundtrip_sha256", "ff_bytes", "ff_sha256"), "retained ModelLab assets")
    exact(script, ("path", "bytes", "sha256", "review_reference", "closure_sha256"), "reviewed GSC and closure")
    require(isinstance(script["review_reference"], str) and 0 < len(script["review_reference"].strip()) <= 1024,
            "Explicit reviewed GSC/closure reference required; no lifecycle script is generated")
    require(isinstance(assets["source_root"], str) and Path(assets["source_root"]).is_absolute(),
            "Explicit absolute ModelLab source_root required")
    source = f.safe_existing(assets["source_root"])
    roots = (project, source, build)
    require(all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in roots),
            "ModelLab output overlaps retained inputs")
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots) for b in roots[i + 1:]), "Project/source/build roots must be separate")
    package = original["package"]
    require(f.pin(script["closure_sha256"]) and
            f.sha(f.encoded(package["closure"])) == script["closure_sha256"].lower(),
            "Reviewed GSC closure declaration differs")
    ident = original["namespace"]
    require(script["path"] == ident + ".gsc" and type(script["bytes"]) is int and 0 < script["bytes"] <= 65536,
            "Explicit existing <namespace>.gsc source required")
    require((project / script["path"]).is_file(), "Existing reviewed GSC required; no lifecycle script is generated")
    gsc = pinned(project, script["path"], "project/gsc", script["sha256"], 65536)
    require(len(gsc) == script["bytes"], "Reviewed GSC byte count differs")
    require(package["maps"] == ["cp_zmb"] and package["delivery"] == "mod" and
            original["compatibility"]["network_protocol"] == 2 and
            original["compatibility"]["coexistence"] == "exclusive-fs-game", "ModelLab cp_zmb mod contract required")
    require(package["closure"]["status"] == "incomplete" and
            all(e["status"] == "pending" and e["reference"] is None and not e["maps"] for e in package["evidence"]) and
            {e["kind"] for e in package["evidence"]} == {"source-check", "offline-load", "runtime-link", "render", "gameplay"},
            "ModelLab materialization requires explicit pending qualification, not promoted evidence")
    script_id = "scriptfile:custom_scripts/cp/" + ident + ".gsc"
    require(original["lifecycle"]["entrypoints"] == [
        {"side": "server", "path": "custom_scripts/cp/" + ident + ".gsc", "symbol": "init"}],
        "ModelLab requires the explicitly reviewed standalone GSC lifecycle")

    plan_raw = pinned(source, "model-ff-plan.json", "source/plan", assets["source_plan_sha256"])
    plan = f.decoded(plan_raw)
    arena = source_profile(plan, adapter, original, require)
    pinned(source, ARENA_WRITER if arena else "derived-export.json", "source/derivation", assets["derived_receipt_sha256"])
    state = f.decoded(pinned(build, "state.local.json", "build/state", assets["build_receipt_sha256"]))
    proof_raw = pinned(build, "geometry-roundtrip.json", "build/roundtrip", assets["roundtrip_sha256"])
    proof = f.decoded(proof_raw)
    require(state["Schema"] == "iw7.model-ff-build/1" and state["Status"] == "BootstrapInventoryVerified" and
            all(state.get(k) is True for k in ("Restored", "StockPreserved", "InventoryVerified", "GeometryRoundtripVerified")) and
            state["RestorationStatus"] == "Confirmed" and state.get("RetainedLeaseToken") is None and
            state.get("CleanupError") is None and state.get("Failure") is None and state.get("Ready") is False,
            "Restored successful ModelLab build required; failed/unclosed states are refused")
    require(all(type(state[k]["ExitCode"]) is int and state[k]["ExitCode"] == 0
                for k in ("Build", "Offline", "Dump", "GeometryReader")), "All retained build phases must have exit 0")
    require(f.encoded(state["SourcePlan"]) == f.encoded(plan) and
            state["SourcePlanSHA256"].lower() == f.sha(plan_raw) and
            state["GeometryEvidenceSHA256"].lower() == f.sha(proof_raw), "Retained source/reader bindings differ")
    require(type(assets["ff_bytes"]) is int and 0 < assets["ff_bytes"] <= 32 * METADATA,
            "Explicit FF byte count within the existing 32 MiB limit required")
    ff = pinned(build, "mod.ff", "build/ff", assets["ff_sha256"], assets["ff_bytes"])
    require(len(ff) == assets["ff_bytes"] and state["FF"]["Path"] == "mod.ff" and
            state["FF"]["Bytes"] == len(ff) and state["FF"]["SHA256"].lower() == f.sha(ff), "Retained FF tuple differs")

    # Enroll every input read by the explicit geometry verifier in our final
    # identity/hash recheck. Never inspect the state machine's stock/tool paths.
    if arena:
        arena_files = arena_inputs(source, plan, read, require)
    else:
        for name, limit in (("evidence/request.json", 4096), ("evidence/manifest.json", 256 * 1024),
                            ("evidence/source.xmb", METADATA), ("evidence/source.xsb", 16 * METADATA)):
            read(source, name, "source/" + name, limit)
    model_path, mesh_path = "xmodel/" + plan["model_name"] + ".xmb", "xsurface/" + plan["mesh_name"] + ".xsb"
    ncs_path = "netconststrings/ncs_mdl_paris_model_probe.json"
    expected_sources = {model_path, mesh_path, ncs_path, "zone_source/paris_model_probe.csv",
                        "zone_source/paris_model_probe_recipient.csv"}
    require(set(plan["source_files"]) == expected_sources, "Exact five ModelLab source inputs required")
    # Retain this first snapshot; rereading after verify_dump would replace the
    # Inputs baseline and could bless a subsequently modified NCS as verified.
    ncs = arena_files[ncs_path] if arena else read(source, ncs_path, "source/" + ncs_path)
    if not arena:
        for name in expected_sources - {ncs_path}:
            read(source, name, "source/" + name, 16 * METADATA if name == mesh_path else METADATA)
    model = read(build, "roundtrip/" + model_path, "build/model", METADATA)
    mesh = read(build, "roundtrip/" + mesh_path, "build/mesh", 16 * METADATA)
    for key in ("GeometryReader", "Offline"):
        path = Path(state[key]["Stdout"])
        require(path.is_absolute() and path.parent == build, "Retained phase stdout must be directly under BuildRoot")
        raw = read(build, path.name, "build/stdout/" + key)
        if key == "GeometryReader":
            require(raw == proof_raw, "Retained reader stdout differs from the pinned roundtrip")
        else:
            log = raw.decode("utf-8-sig")
    inventory = read(build, "assets.csv", "build/inventory", 65536).decode("utf-8-sig").splitlines()
    expected_rows = {"material,,mopw/character_park_clown_zombie_shoes", "xmodel," + plan["model_name"],
                     "xmodelsurfs," + plan["mesh_name"], "netconststrings,ncs_mdl_paris_model_probe", "rawfile,paris_model_probe"}
    require(len(inventory) == len(expected_rows) and set(inventory) == expected_rows,
            "Retained ModelLab inventory differs")
    rows = []
    for line in log.splitlines():
        if "Loading asset " in line:
            match = re.search(r'Loading asset "([^"\r\n]+)" of type ([a-z0-9]+)\.$', line)
            require(match is not None, "Malformed retained asset inventory callback")
            rows.append(match[2] + "," + match[1])
    require('Loading zone "paris_model_probe"' in log and
            not re.search(r'could not be found|Could not find referenced|\[ ERROR \]|\[ FATAL \]', log, re.I) and
            len(rows) == len(expected_rows) and set(rows) == expected_rows, "Retained bootstrap inventory not established")
    if arena:
        verifier = arena_reader(tools_root)
        measured = verifier.verify_dump(source, build / "roundtrip", build / "mod.ff")
    else:
        sys.path.insert(0, str(Path(tools_root) / "ops/model-lab"))
        try:
            verifier = module(Path(tools_root) / "ops/model-lab/rigid_export.py", "creator_resident_verifier")
            measured = verifier.verify_dump(source, build / "roundtrip", build / "mod.ff")
        finally:
            sys.path.pop(0)
    require(f.encoded(proof) == f.encoded(measured), "Retained roundtrip differs from independent " +
            ("original arena" if arena else "resident") + " revalidation")
    if not arena:
        require(proof["derived_receipt_sha256"] == assets["derived_receipt_sha256"].lower(), "Derived receipt binding differs")

    result_manifest = copy.deepcopy(original)
    closure = result_manifest["package"]["closure"]
    nodes = {node["id"]: node for node in closure["nodes"]}
    model_id, mesh_id = "xmodel:" + plan["model_name"], "xsurface:" + plan["mesh_name"]
    ncs_id, raw_id = "netconststrings:ncs_mdl_paris_model_probe", "rawfile:paris_model_probe"
    material_id = "material:" + verifier.MATERIAL
    require({n["id"] for n in nodes.values() if n["scope"] == "client"} == {model_id, mesh_id, ncs_id, raw_id} and
            {n["id"] for n in nodes.values() if n["scope"] == "server"} == {script_id} and
            material_id in nodes and nodes[material_id]["scope"] == "recipient" and
            set(nodes[model_id]["requires"]) == {mesh_id, ncs_id, raw_id, material_id} and
            model_id in nodes[script_id]["requires"] and set(closure["roots"]) == {model_id, script_id},
            "Reviewed closure must bind the real ModelLab names, placeholder material and GSC model dependency")
    representations = []
    for node_id, raw, representation in ((model_id, model, "Retained FF model dump"),
                                        (mesh_id, mesh, "Retained FF surface dump"),
                                        (ncs_id, ncs, "Verified NCS source input; not a retained dump"),
                                        (script_id, gsc, "Explicit separately reviewed GSC source; not a build input")):
        require(nodes[node_id]["sha256"] in (None, f.sha(raw)), "Declared node hash differs: " + node_id)
        nodes[node_id]["sha256"] = f.sha(raw)
        representations.append({"id": node_id, "bytes": len(raw), "sha256": f.sha(raw), "representation": representation})
    # Inventoried recipient nodes are not also "unresolved" IDs in transport v1.
    # Their missing qualification stays explicit in incomplete closure/blockers.
    closure.update(status="incomplete", evidence_ref="finalization.json#node_representations")
    files = result_manifest["package"]["files"]
    require(len(files) == 2 and sorted(e["role"] for e in files) == ["client", "server"],
            "Exactly one client FF and the reviewed server GSC required")
    outputs = {"mod.ff": ff, script["path"]: gsc}
    for entry in files:
        client = entry["role"] == "client"
        path = "mod.ff" if client else script["path"]
        destination = "mods/" + ident + "/mod.ff" if client else "iw7-mod/custom_scripts/cp/" + path
        require(entry["destination"] == destination and entry["closure_roots"] == [model_id if client else script_id] and
                entry["source"] in (None, path) and entry["bytes"] in (None, len(outputs[path])) and
                entry["sha256"] in (None, f.sha(outputs[path])), "Payload declaration differs from retained inputs")
        entry.update(source=path, bytes=len(outputs[path]), sha256=f.sha(outputs[path]))
    blockers = ["Recipient material/technique/image closure remains unqualified; every slot uses the same IW7 placeholder.",
                "Generated zone rawfile has inventory evidence only; no retained serialized representation was verified.",
                "GSC source/closure review is declared and hash-bound, not compiled-import or runtime qualification.",
                ("Original arena runtime linking, pixels, solid collision and owner gameplay remain unverified." if arena else
                 "Native T7 provenance, donor appearance, runtime linking, pixels and owner gameplay remain unverified.")]
    geometry_details = ({"geometry_profile": ARENA_PROFILE, "origin": "authored-arena", "selected_counts": plan["selected_counts"],
                         "physics_serialized": False} if arena else
                        {"surface_records": plan["surface_records"], "material_references": plan["material_references"],
                         "geometry_work_bytes_upper_bound": plan["geometry_work_bytes_upper_bound"]})
    evidence = {"api": API, "adapter": adapter, "inputs": inputs.records, "composition": descriptor,
        "node_representations": representations, "model_name": plan["model_name"], "mesh_name": plan["mesh_name"],
        **geometry_details,
        "material_policy": ("Existing IW7 recipient material reference; original authored arena geometry" if arena else
                            "IW7 recipient placeholder per slot; no T7 material or texture payload ported"),
        "reviewed_gsc_declaration_bound": True, "gsc_imports_verified": False,
        "asset_source_receipt_bound": True, "geometry_roundtrip_rechecked": True,
        "native_provenance_verified": False, "recipient_closure_complete": False, "build_executed": False,
        "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
        "target_source_assertions": {"client": client_source, "server": server_source, "protocol": 2}, "blockers": blockers}
    outputs.update({"manifest.json": f.encoded(result_manifest), "finalization.json": f.encoded(evidence)})
    plan_result = f.sdk.validate(result_manifest, stage="plan", client_source=client_source, server_source=server_source)
    require(plan_result["valid"], "Generated SDK contract invalid: " + "; ".join(plan_result["errors"]))
    outputs["validation-plan.json"] = f.encoded(plan_result)
    require(sum(map(len, outputs.values())) + METADATA <= OUTPUT_LIMIT, "ModelLab output budget exceeded")
    inputs.recheck()
    output.mkdir()
    root_id = f.identity(output.stat())[:2]
    # Exclusive fixed outputs; on an interrupted/failed write retain the partial
    # candidate for diagnosis. Never recurse-delete or overwrite input evidence.
    def write(name, raw):
        require(f.identity(f.safe_existing(output).stat())[:2] == root_id, "Candidate directory identity changed")
        with (output / name).open("xb") as stream:
            stream.write(raw)
    for name, raw in outputs.items():
        write(name, raw)
    package_result = f.sdk.validate(result_manifest, root=output, stage="package",
                                    client_source=client_source, server_source=server_source)
    require(not package_result["ready"] and set(package_result["checked"]) == {entry["id"] for entry in files} and
            package_result["errors"] == ["package: Dependency closure incomplete"], "Unqualified ModelLab package gate changed")
    outputs["validation-package.json"] = f.encoded(package_result)
    write("validation-package.json", outputs["validation-package.json"])
    require({p.name for p in output.iterdir()} == set(outputs), "Unexpected candidate contents")
    verified = f.Inputs()
    for name, expected in outputs.items():
        require(verified.read(output, name, name, len(expected)) == expected, "Materialized output changed: " + name)
    inputs.recheck()
    verified.recheck()
    return {"api": API, "materialized": True, "candidate_root": str(output), "manifest_path": str(output / "manifest.json"),
        "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
        "blockers": blockers, "creator_output_verified": True, "candidate_files_verified": verified.records,
        "bytes_written": sum(map(len, outputs.values())),
        "exact_hashes": {"ff": f.sha(ff), "gsc": f.sha(gsc), "manifest": f.sha(outputs["manifest.json"]),
                         "finalization": f.sha(outputs["finalization.json"])}}
