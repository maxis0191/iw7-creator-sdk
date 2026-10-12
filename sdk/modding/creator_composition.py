"""Compose reviewed script sources with retained assets; no build or execution.

Policies are registered here, never imported from a project. The versioned input
separates script, asset and evidence policies so new reviewed authorship routes
can be added without pretending that an old FF was built from a new script.
"""
import copy
import os
from pathlib import Path

API = "creator-composition/1"
SCRIPT_POLICY = "beacon-self-contained-source/1"
ASSET_POLICY = "beacon-retained-build/1"


def exact(value, fields, label, require):
    require(isinstance(value, dict) and set(value) == set(fields), "Unexpected composition " + label + " fields")


def plan_contract(data):
    """Keep the actual retained FF rawfile identity, not the prospective rename."""
    manifest = copy.deepcopy(data)
    old, actual = "rawfile:sdk_beacon_self_contained", "rawfile:sdk_beacon"
    for node in manifest["package"]["closure"]["nodes"]:
        if node["id"] == old:
            node["id"] = actual
        node["requires"] = [actual if ref == old else ref for ref in node["requires"]]
    return manifest


def recipient_observation(f, inputs, spec, output):
    if spec is None:
        return None
    exact(spec, ("run_root", "phase_sha256", "csv_sha256"), "recipient evidence", f.require)
    root = f.safe_existing(spec["run_root"])
    f.require(Path(spec["run_root"]).is_absolute() and not output.is_relative_to(root) and
              not root.is_relative_to(output), "Composition output overlaps recipient evidence")
    paths = (("references/phase.json", "phase_sha256"),
             ("work/enemy-catalog/sdk_beacon_recipient_a.csv", "csv_sha256"))
    for name, key in paths:
        raw = inputs.read(root, name, "composition/recipient/" + name, 65536)
        f.require(f.pin(spec[key]) and f.sha(raw) == spec[key], "Composition recipient evidence pin differs")
    verifier = f.module(f.HERE / "recipient/verify.py", "composition_recipient")
    report = verifier.verify_phase(root / "work", root / "references/phase.json")
    f.require(report["phase"] == "references" and report["receipt_sha256"] == spec["phase_sha256"] and
              report["observation"]["manifest_sha256"] == spec["csv_sha256"], "Composition recipient observation differs")
    return {**report, "run_bound": False, "stock_identity_verified": False}


def finalize(project, build_root, output_root, tools_root, *, client_source=None, server_source=None):
    f = _finalizer(tools_root)
    require, inputs = f.require, f.Inputs()
    project, build = f.safe_existing(project), f.safe_existing(build_root)
    output = Path(os.path.abspath(output_root))
    f.safe_existing(output.parent)
    require(not os.path.lexists(output), "Fresh composition output required")
    descriptor = inputs.json(project, "composition.json", "composition/descriptor", 65536)
    exact(descriptor, ("schema", "script", "assets", "evidence"), "descriptor", require)
    require(descriptor["schema"] == "iw7.creator-composition/1", "Unsupported composition contract")
    script, assets, evidence_spec = (descriptor[key] for key in ("script", "assets", "evidence"))
    exact(script, ("policy", "path", "bytes", "sha256"), "script", require)
    exact(assets, ("policy", "project", "build_root", "source_receipt_sha256", "build_receipt_sha256", "ff_sha256"), "assets", require)
    exact(evidence_spec, ("gsc", "recipient"), "evidence", require)
    require(script["policy"] == SCRIPT_POLICY and assets["policy"] == ASSET_POLICY,
            "Unreviewed composition policy; arbitrary scripts/assets cannot be materialized")
    selector = f.module(f.HERE / "creator_self_contained.py", "composition_selector")
    packager = f.module(f.REPO / "ops/modding/Package-CommunityMod.py", "composition_packager")
    data, selected = selector.select(project, tools_root, packager)
    require(script == {"policy": SCRIPT_POLICY, "path": selector.SOURCE_NAME, "bytes": selector.SOURCE_BYTES,
                       "sha256": selector.SOURCE_SHA256} and type(script["bytes"]) is int,
            "Composition script must match the reviewed source policy")
    gsc = inputs.read(project, script["path"], "composition/script", 65536)
    require(len(gsc) == script["bytes"] and f.sha(gsc) == script["sha256"], "Composition script bytes differ")
    # Also keep the selector's optional manifest and reviewed policy bytes stable.
    for path, label in ((f.HERE / selector.MANIFEST_NAME, "composition/policy-manifest"),
                        (f.HERE / "examples/beacon-self-contained" / script["path"], "composition/policy-source")):
        inputs.read(path.parent, path.name, label, 131072)
    if selected["project_manifest_present"]:
        inputs.read(project, "manifest.json", "composition/project-manifest", 131072)
    require(Path(assets["project"]).is_absolute() and Path(assets["build_root"]).is_absolute(),
            "Composition asset roots must be explicit absolute paths")
    asset_project = f.safe_existing(assets["project"])
    require(f.safe_existing(assets["build_root"]) == build, "Composition BuildRoot differs from the asset descriptor")
    require(all(not output.is_relative_to(root) and not root.is_relative_to(output)
                for root in (project, asset_project, build)), "Composition output overlaps inputs")
    require(not project.is_relative_to(asset_project) and not asset_project.is_relative_to(project) and
            not project.is_relative_to(build) and not build.is_relative_to(project),
            "Composition project must be separate from retained asset source/build")
    _, _, state, ff, nodes, source_bound = f.retained_beacon(inputs, asset_project, build)
    require(source_bound, "Composition requires the original source-bound asset build")
    for field, label in (("source_receipt_sha256", "project/source-receipt.local.json"),
                         ("build_receipt_sha256", "build/state.local.json"), ("ff_sha256", "build/mod.ff")):
        require(f.pin(assets[field]) and assets[field] == inputs.records[label]["sha256"], "Composition asset pin differs: " + field)
    gsc_report = None
    if evidence_spec["gsc"] is not None:
        pin = evidence_spec["gsc"]
        exact(pin, ("path", "sha256"), "GSC evidence", require)
        path = f.safe_existing(pin["path"])
        require(Path(pin["path"]).is_absolute() and not path.is_relative_to(output), "Explicit separate GSC evidence required")
        raw = inputs.read(path.parent, path.name, "composition/gsc-expectations", 1024 * 1024)
        require(f.pin(pin["sha256"]) and f.sha(raw) == pin["sha256"], "Composition GSC evidence pin differs")
        audit = f.module(f.HERE / "creator_gsc_audit.py", "composition_gsc_audit")
        gsc_report = audit.inspect(project, tools_root, f.decoded(raw), packager)
        # Enroll the measured audit inputs in the writer's final identity/hash
        # recheck too; an earlier attached observation alone is not sufficient.
        for group in ("files", "reference_source_files"):
            for role, record in gsc_report[group].items():
                path = f.safe_existing(record["path"])
                require(not path.is_relative_to(output), "Composition output overlaps GSC evidence")
                measured = inputs.read(path.parent, path.name, "composition/gsc/" + group + "/" + role, 4 * 1024 * 1024)
                require(len(measured) == record["bytes"] and f.sha(measured) == record["sha256"], "GSC evidence changed after inspection")
    recipient = recipient_observation(f, inputs, evidence_spec["recipient"], output)
    encoded_absence = gsc_report is not None and gsc_report.get("encoded_external_script_reference_absence") is True
    blockers = ["Recipient serialized material, technique-set, image contents and transitive dependencies remain unqualified.",
                "Native builtin/loader semantics and runtime behavior of this composition remain unqualified."]
    if not encoded_absence:
        blockers.insert(0, "Complete source-bound encoded GSC reference qualification remains pending; no utility dependency is asserted.")
    if recipient is None:
        blockers.append("No checked recipient reference-phase observation is attached.")
    else:
        blockers.append("Recipient phase bytes agree, but the outer Run and stock identity are not revalidated by this composition.")
    manifest = plan_contract(data)
    compatibility = f.compat.check_environment([manifest], client_source=client_source, server_source=server_source, protocol=2, mode="cp")
    require(not compatibility, "Composition target compatibility failed: " + "; ".join(compatibility))
    outputs = {"mod.ff": ff, script["path"]: gsc}
    representations = []
    closure = manifest["package"]["closure"]
    for node in closure["nodes"]:
        if node["id"] in nodes:
            raw = nodes[node["id"]]
            node["sha256"] = f.sha(raw)
            name = "evidence/serialized-nodes/" + f.NODE_FILES[node["id"]]
            outputs[name] = raw
            representations.append({"id": node["id"], "path": name, "bytes": len(raw), "sha256": f.sha(raw),
                                    "representation": "Exact retained FF dump bytes"})
        elif node["scope"] == "server":
            node["sha256"] = f.sha(gsc)
    closure["evidence_ref"] = "finalization.json#node_representations"
    for entry in manifest["package"]["files"]:
        name = "mod.ff" if entry["role"] == "client" else script["path"]
        entry.update(source=name, bytes=len(outputs[name]), sha256=f.sha(outputs[name]))
    receipt = {"api": API, "schema": "iw7.creator-composition-receipt/1", "adapter": "BeaconSelfContainedV1",
        "composition": descriptor, "inputs": inputs.records, "node_representations": representations,
        "asset_build_reused": True, "asset_source_receipt_bound": True, "variant_ff_built": False,
        "source_receipt_scope": "Original asset build only; separate variant source is composed, never relabeled as build input.",
        "gsc_observation": gsc_report, "recipient_observation": recipient,
        "encoded_external_script_reference_absence": encoded_absence,
        "unresolved_qualifications": [] if encoded_absence else [{"id": "compiled-gsc-import-absence", "status": "unresolvedQualification",
            "dependency_edge_asserted": False, "subject": "External/dynamic references in the exact compiled variant"}],
        "closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
        "blockers": blockers, "build_candidate_sha256": state["Plan"]["Candidate"]["SHA256"].lower(),
        "target_source_assertions": {"client": client_source, "server": server_source}}
    selector.select(project, tools_root, packager)
    written = f.write_candidate(output, inputs, manifest, receipt, outputs, client_source=client_source, server_source=server_source)
    return {"api": API, "materialized": True, "candidate_root": str(output), "manifest_path": str(output / "manifest.json"),
        "asset_build_reused": True, "asset_source_receipt_bound": True, "variant_ff_built": False,
        "closure_complete": False, "package_ready": False, "runtime_ready": False, "blockers": blockers,
        "exact_hashes": {"ff": f.sha(ff), "gsc": f.sha(gsc), "manifest": f.sha(outputs["manifest.json"]),
                         "finalization": f.sha(outputs["finalization.json"]), "composition": inputs.records["composition/descriptor"]["sha256"],
                         "source_receipt": assets["source_receipt_sha256"], "build_receipt": assets["build_receipt_sha256"]},
        "bytes_written": written}


def _finalizer(tools_root):
    import importlib.util
    spec = importlib.util.spec_from_file_location("composition_finalizer", Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def materialize(project, build_root, output_root, tools_root, *, client_source=None, server_source=None):
    f = _finalizer(tools_root)
    result = finalize(project, build_root, output_root, tools_root, client_source=client_source, server_source=server_source)
    verifier = f.module(f.HERE / "creator_materialize.py", "composition_verifier")
    return verifier.verify_candidate(f, result, output_root, api=API, gsc_name="sdk_beacon_self_contained.gsc",
                                    verify_evidence_hash=True, client_source=client_source, server_source=server_source)
