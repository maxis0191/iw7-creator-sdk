"""Create and check a local BeaconV1 candidate from retained build evidence."""
import importlib.util
from pathlib import Path


def materialize(project, build_root, output_root, tools_root, *, client_source=None, server_source=None,
                recipient_proof=None, recipient_root=None):
    path = Path(tools_root) / "sdk/modding/Finalize-BeaconProject.py"
    spec = importlib.util.spec_from_file_location("creator_local_finalizer", path)
    finalizer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(finalizer)
    result = finalizer.finalize(project, build_root, output_root, client_source=client_source,
        server_source=server_source, recipient_proof=recipient_proof, recipient_root=recipient_root)
    require = finalizer.require
    require(result["api"] == "beacon-finalize/1" and result["materialized"] is True and
            all(result[key] is False for key in ("closure_complete", "package_ready", "runtime_ready")),
            "Materialize finalizer returned an unexpected candidate contract")
    output = finalizer.safe_existing(output_root)
    require(output.is_dir() and Path(result["candidate_root"]) == output and Path(result["manifest_path"]) == output / "manifest.json",
            "Materialize finalizer returned unexpected candidate paths")
    require(isinstance(result["blockers"], list) and result["blockers"] and
            all(isinstance(item, str) and item for item in result["blockers"]), "Materialize requires explicit remaining blockers")
    # Success needs actual bounded files, not just a positive finalizer boolean.
    # This does not repeat native work or invoke the package writer.
    names = {"mod.ff", "sdk_beacon.gsc", "manifest.json", "finalization.json", "validation-plan.json", "validation-package.json"}
    names.update("evidence/serialized-nodes/" + name for name in finalizer.NODE_FILES.values())
    inputs, files, measured = finalizer.Inputs(), {}, 0
    for name in sorted(names):
        files[name] = inputs.read(output, name, name, finalizer.LIMIT)
        measured += len(files[name])
        require(measured <= finalizer.LIMIT, "Materialized candidate exceeds the byte budget")
    require(type(result["bytes_written"]) is int and 0 < measured == result["bytes_written"] <= finalizer.LIMIT,
            "Materialized candidate byte count differs")
    for role, name in (("ff", "mod.ff"), ("gsc", "sdk_beacon.gsc"), ("manifest", "manifest.json")):
        require(finalizer.sha(files[name]) == result["exact_hashes"][role], "Materialized candidate hash differs: " + role)
    evidence = finalizer.decoded(files["finalization.json"])
    require(evidence["api"] == "beacon-finalize/1" and evidence["blockers"] == result["blockers"] and
            all(evidence[key] is False for key in ("closure_complete", "package_ready", "runtime_ready", "owner_accepted")),
            "Materialized candidate evidence differs")
    manifest = finalizer.decoded(files["manifest.json"])
    representations = evidence["node_representations"]
    require(isinstance(representations, list) and len(representations) == len(finalizer.NODE_FILES) and
            all(isinstance(item, dict) for item in representations) and
            {item["id"] for item in representations} == set(finalizer.NODE_FILES),
            "Materialized candidate node representation identities differ")
    for ident, relative in finalizer.NODE_FILES.items():
        name = "evidence/serialized-nodes/" + relative
        raw = files[name]
        expected = {"id": ident, "path": name, "bytes": len(raw), "sha256": finalizer.sha(raw),
                    "representation": "Exact retained FF dump bytes"}
        actual = next(item for item in representations if item["id"] == ident)
        require(finalizer.encoded(actual) == finalizer.encoded(expected),
                "Materialized candidate node representation differs: " + ident)
        nodes = [node for node in manifest["package"]["closure"]["nodes"] if node["id"] == ident]
        require(len(nodes) == 1 and nodes[0]["sha256"] == expected["sha256"],
                "Materialized candidate node closure hash differs: " + ident)
    # Recompute these pure reports; a stored success/failure summary is not proof.
    for stage in ("plan", "package"):
        report = finalizer.sdk.validate(manifest, root=output if stage == "package" else None,
            stage=stage, client_source=client_source, server_source=server_source)
        require(files["validation-" + stage + ".json"] == finalizer.encoded(report),
                "Materialized candidate validation report differs: " + stage)
    inputs.recheck()
    return {**result, "creator_output_verified": True, "candidate_files_verified": inputs.records}
