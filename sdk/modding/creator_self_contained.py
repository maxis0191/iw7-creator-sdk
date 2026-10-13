"""Explicit source-only Creator selection. No compiler, audit runner or writer."""
import hashlib
import json
import os
from pathlib import Path
import stat

ADAPTER = "BeaconSelfContainedV1"
SOURCE_NAME = "sdk_beacon_self_contained.gsc"
SOURCE_BYTES = 5535
SOURCE_SHA256 = "9de9b76dc25293146999c71653bd407d8cb639e107293f6de87084fed90eee1c"
MANIFEST_NAME = "creator_beacon_self_contained.manifest.json"
MANIFEST_SHA256 = "1102a8d411c4bf105a07749ed4c4b779c042af1e680b1e99c5efd20b577e92af"
PENDING = [
    "Variant Build is not connected: a separate source receipt, zone recipe, FF/rawfile identity and finalization path are required.",
    "A source-bound compiled import audit must attest complete bytecode AND stack consumption and qualify all external/dynamic targets; zero observed Far calls is insufficient.",
    "Utility is an unresolved qualification question, not an asserted dependency of the variant; a complete bound import audit is still required to qualify dependency absence.",
    "Recipient material, technique-set, image and transitive dependencies still require exact closed-Run content evidence; presence checks alone do not close the graph.",
]


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(meta):
    return meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns


def snapshot(path, packager, limit):
    path = packager.no_redirects(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, "Bounded regular Creator input required")
    with path.open("rb") as stream:
        require(identity(os.fstat(stream.fileno())) == identity(before), "Creator input changed before read")
        raw = stream.read(limit + 1)
        require(identity(os.fstat(stream.fileno())) == identity(before), "Creator input changed during read")
    require(len(raw) == before.st_size and identity(packager.no_redirects(path).stat()) == identity(before), "Creator input changed after read")
    return raw


def json_snapshot(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate Creator manifest key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Invalid Creator manifest constant: " + value)
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs, parse_constant=constant)


def select(project, root, packager):
    """Return a proposed in-memory contract, never a prepared build project."""
    sdk = Path(root) / "sdk/modding"
    template = snapshot(sdk / "examples/beacon-self-contained" / SOURCE_NAME, packager, 65536)
    source_path = Path(project) / SOURCE_NAME
    source = snapshot(source_path, packager, 65536)
    require(len(template) == SOURCE_BYTES and hashlib.sha256(template).hexdigest() == SOURCE_SHA256,
            "Reviewed self-contained source pin changed in ToolsRoot")
    require(source == template, "BeaconSelfContainedV1 requires the exact separate reviewed source; no original-template substitution")
    manifest_path = sdk / MANIFEST_NAME
    raw_manifest = snapshot(manifest_path, packager, 131072)
    require(hashlib.sha256(raw_manifest).hexdigest() == MANIFEST_SHA256, "Reviewed self-contained planning contract pin changed in ToolsRoot")
    manifest = json_snapshot(raw_manifest)
    supplied = Path(project) / "manifest.json"
    present = os.path.lexists(supplied)
    if present:
        actual = json_snapshot(snapshot(supplied, packager, 131072))
        require(json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(manifest, sort_keys=True, allow_nan=False),
                "Project manifest must equal the reviewed self-contained planning contract")
    selection = {"schema": "iw7.creator-source-selection/1", "adapter": ADAPTER,
        "scope": "Exact source selection and proposed contract only; no compiled artifact or native execution was checked.",
        "source": {"path": str(source_path), "bytes": len(source), "sha256": hashlib.sha256(source).hexdigest()},
        "contract_template": {"path": str(manifest_path), "sha256": hashlib.sha256(raw_manifest).hexdigest()},
        "project_manifest_present": present, "contract_written": False, "source_bytes_verified": True,
        "build_adapter_qualified": False, "compiled_input_bound": False, "bytecode_fully_consumed_verified": False,
        "stack_fully_consumed_verified": False, "external_gsc_dependency_absence_verified": False,
        "recipient_closure_complete": False, "package_ready": False, "runtime_ready": False, "owner_accepted": False,
        "unresolved_qualifications": [{"id": "compiled-gsc-import-absence", "status": "unresolvedQualification",
            "subject": "scripts/engine/utility and any other external/dynamic GSC targets",
            "dependency_edge_asserted": False, "reason": "No complete source-bound import qualification has been accepted by this selector."}],
        "proposed_contract": manifest, "pending": list(PENDING)}
    return manifest, selection
