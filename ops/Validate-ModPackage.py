"""Read-only IW7 package gate. No game assets, build, upload or game launch.

Plan validation permits explicitly unknown payloads. Package/delivery validation
hashes real local files and never upgrades static evidence to gameplay acceptance.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

SCHEMA = "iw7.mod-package/1"
SHA = re.compile(r"^[0-9a-fA-F]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
IDENT = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
MAPS = {"cp_zmb", "cp_rave", "cp_disco", "cp_town", "cp_final"}
KINDS = {"scriptfile", "luafile", "xmodel", "image", "material", "sound", "weapon", "anim", "bt", "asm", "other"}
EVIDENCE = {"source-check", "offline-load", "runtime-link", "render", "gameplay"}
# Independently reviewed source capability, not arbitrary manifest assertions.
# PR #697 implements this loader; local merge-base confirmed the project pin,
# and the dated official develop source contains the implementation.
CAPABILITY_SOURCES = {
    "lua-fastfile": {
        "7c8fe47d3fa09e093d779e84bf958e9427b49a0f": "https://github.com/auroramod/iw7-mod/pull/697/files",
        "77e6d4d24e918ee363b3feee3735c3b889dff7d7": "docs/UPSTREAM-2026-10-06.md#lua-assets-and-downloader",
        "c0a1c6dacd33c86320b308656d9ba895291c2198": "https://github.com/auroramod/iw7-mod/blob/c0a1c6dacd33c86320b308656d9ba895291c2198/src/client/component/ui_scripting.cpp",
    }
}
RESERVED = {"CON", "PRN", "AUX", "NUL", "CLOCK$", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10)),
            *(f"{prefix}{i}" for prefix in ("COM", "LPT") for i in "\u00b9\u00b2\u00b3")}


def safe_path(value):
    if not isinstance(value, str) or not value or len(value) > 240:
        return False
    if "\\" in value or value.startswith("/") or any(ord(c) < 32 for c in value):
        return False
    for part in value.split("/"):
        if part in ("", ".", "..") or part.endswith((".", " ")):
            return False
        if any(c in part for c in '<>:"|?*') or part.split(".")[0].upper() in RESERVED:
            return False
    return True


def load_manifest(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def _validate(data, root=None, stage="plan", target="stock", client_source=None, server_source=None):
    errors, pending, checked = [], [], []
    def fail(message):
        errors.append(message)
    def fields(obj, names, label):
        if not isinstance(obj, dict):
            fail(label + " must be an object")
            return False
        extra, missing = set(obj) - set(names), set(names) - set(obj)
        if extra or missing:
            fail(f"{label} fields mismatch: extra={sorted(extra)} missing={sorted(missing)}")
        return not extra and not missing
    def items(value, label):
        if not isinstance(value, list):
            fail(label + " must be an array")
            return []
        return value
    def strings(value, label):
        values = items(value, label)
        if any(not isinstance(v, str) or not v.strip() for v in values):
            fail(label + " must contain nonempty strings")
            return []
        if len({v.casefold() for v in values}) != len(values):
            fail(label + " contains duplicate or Windows case-colliding values")
        return values
    def sha(value):
        return isinstance(value, str) and bool(SHA.fullmatch(value))
    def pin(value):
        return isinstance(value, str) and bool(COMMIT.fullmatch(value))

    if stage not in {"plan", "package", "delivery"} or target not in {"stock", "native"}:
        raise ValueError("Unsupported stage/target")
    if not fields(data, {"schema", "id", "version", "maps", "delivery", "native_requirements", "files", "closure", "evidence"}, "manifest"):
        return {"schema": SCHEMA, "valid": False, "ready": False, "errors": errors, "pending": pending, "checked": checked}
    if data["schema"] != SCHEMA:
        fail("Unsupported schema")
    module = data["id"]
    if not isinstance(module, str) or not IDENT.fullmatch(module):
        fail("id must be a lowercase safe module identifier")
    if not isinstance(data["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", data["version"]):
        fail("version must be numeric major.minor.patch")
    maps = strings(data["maps"], "maps")
    if not maps or set(maps) - MAPS:
        fail("maps must identify supported retail recipients")
    delivery = data["delivery"]
    if delivery not in {"server-only", "mod", "usermap"}:
        fail("delivery must be server-only, mod or usermap")

    requirements = data["native_requirements"]
    if fields(requirements, {"server_source", "client_source", "client_capabilities", "compatible_client_sources"}, "native_requirements"):
        for side, observed in (("server", server_source), ("client", client_source)):
            required = requirements[side + "_source"]
            if required is not None and not pin(required):
                fail(side + "_source must be null or an exact source commit")
            if required is not None:
                if side == "client" and target == "stock":
                    fail("Custom native client requirement cannot be delivered to a stock client by assets")
                if observed != required:
                    (pending if stage == "plan" else errors).append(side + " native source pin not established")
        capabilities = strings(requirements["client_capabilities"], "client_capabilities")
        if set(capabilities) - set(CAPABILITY_SOURCES):
            fail("Unknown client capability; extend reviewed contract before use")
        compatible = strings(requirements["compatible_client_sources"], "compatible_client_sources")
        if any(not pin(v) for v in compatible):
            fail("compatible_client_sources requires exact commits")
        for capability in capabilities:
            known = CAPABILITY_SOURCES.get(capability, {})
            if any(source not in known for source in compatible):
                fail("Client capability source lacks independently reviewed proof: " + capability)
        if capabilities and (not compatible or client_source not in compatible):
            (pending if stage == "plan" else errors).append("Client capability source pin not established")
    else:
        capabilities = []

    closure = data["closure"]
    nodes, roots, unresolved = {}, [], []
    if fields(closure, {"status", "roots", "nodes", "unresolved", "evidence_ref"}, "closure"):
        roots = strings(closure["roots"], "closure.roots")
        unresolved = strings(closure["unresolved"], "closure.unresolved")
        if closure["status"] not in {"incomplete", "complete"}:
            fail("closure status must be incomplete or complete")
        for node in items(closure["nodes"], "closure.nodes"):
            if not fields(node, {"id", "kind", "scope", "sha256", "requires"}, "closure node"):
                continue
            name = node["id"]
            if not isinstance(name, str) or not name.strip() or any(ord(c) < 32 for c in name):
                fail("Invalid closure node id")
                continue
            key = name.casefold()
            if key in nodes:
                fail("Duplicate or case-colliding closure node: " + name)
            node = dict(node)
            node["requires"] = strings(node["requires"], "node requires")
            nodes[key] = node
            if node["kind"] not in KINDS or node["scope"] not in {"client", "server", "recipient"}:
                fail("Invalid closure node kind/scope: " + name)
            if node["sha256"] is not None and not sha(node["sha256"]):
                fail("Invalid closure node SHA-256: " + name)
        for name in roots:
            if name.casefold() not in nodes:
                fail("Closure root has no node: " + name)
        unresolved_set = {s.casefold() for s in unresolved}
        if unresolved_set & set(nodes):
            fail("Dependency cannot be both resolved and unresolved")
        for node in nodes.values():
            for name in node["requires"] if isinstance(node["requires"], list) else []:
                if isinstance(name, str) and name.casefold() not in nodes and name.casefold() not in unresolved_set:
                    fail("Dependency not inventoried: " + name)
        if closure["status"] == "complete":
            if unresolved or not roots or not isinstance(closure["evidence_ref"], str) or not closure["evidence_ref"].strip():
                fail("Complete closure requires roots, evidence reference and no unresolved dependency")
            if any(not sha(node["sha256"]) for node in nodes.values()):
                fail("Complete closure requires inventory SHA-256 for every node, including recipient dependencies")
        else:
            (pending if stage == "plan" else errors).append("Dependency closure incomplete")
    reachable = set()
    queue = [s.casefold() for s in roots]
    while queue:
        key = queue.pop()
        if key in reachable or key not in nodes:
            continue
        reachable.add(key)
        queue.extend(s.casefold() for s in nodes[key]["requires"] if isinstance(s, str))
    if set(nodes) - reachable:
        fail("Closure includes nodes not reachable from declared roots")
    if any(node["kind"] == "luafile" and node["scope"] == "client" for node in nodes.values()) and "lua-fastfile" not in capabilities:
        fail("Client LuaFile requires declared lua-fastfile capability")

    destinations, sources, file_ids = set(), set(), set()
    bound_roots = {"client": set(), "server": set()}
    payload_bindings = []
    files = items(data["files"], "files")
    if not files:
        fail("At least one package file must be declared")
    base = Path(root).absolute() if root else None
    if stage != "plan" and base is None:
        fail("Package/delivery stage requires an explicit payload root")
    for entry in files:
        if not fields(entry, {"id", "role", "source", "destination", "bytes", "sha256", "closure_roots"}, "file"):
            continue
        fid = entry["id"]
        if not isinstance(fid, str) or not IDENT.fullmatch(fid):
            fail("Invalid file id")
        elif fid.casefold() in file_ids:
            fail("Duplicate file id: " + fid)
        else:
            file_ids.add(fid.casefold())
        source, dest = entry["source"], entry["destination"]
        if not safe_path(dest):
            fail("Unsafe destination path")
            continue
        if dest.casefold() in destinations:
            fail("Duplicate or Windows case-colliding destination: " + dest)
        destinations.add(dest.casefold())
        role = entry["role"]
        if role not in {"client", "server"}:
            fail("File role must be client or server")
        if role == "server":
            if not (dest.startswith("iw7-mod/custom_scripts/cp/") and dest.endswith(".gsc")) and not (dest.startswith("zone/") and dest.endswith(".ff")):
                fail("Server file outside supported GSC/fastfile locations")
        elif delivery == "mod":
            if dest not in {f"mods/{module}/mod.{ext}" for ext in ("ff", "sabl", "sabs")}:
                fail("Mod downloader supports only mod.ff/mod.sabl/mod.sabs under this module")
        elif delivery == "usermap":
            if dest not in {f"usermaps/{module}/{module}{suffix}" for suffix in (".ff", "_load.ff", "_art.ff", ".pak", ".sabl", ".sabs")}:
                fail("Usermap file outside reviewed downloader layout")
        else:
            fail("server-only delivery cannot contain client files")
        bindings = strings(entry["closure_roots"], "file closure_roots")
        if not bindings or any(s.casefold() not in {r.casefold() for r in roots} for s in bindings):
            fail("Each file must bind declared dependency roots")
        if any(nodes.get(s.casefold(), {}).get("scope") != role for s in bindings):
            fail("File root scope must match its client/server role")
        if role in bound_roots:
            bound_roots[role].update(s.casefold() for s in bindings)
            suffix = Path(dest).suffix
            kinds = {"scriptfile"} if suffix == ".gsc" else {"sound"} if suffix in {".sabl", ".sabs"} else {"image"} if suffix == ".pak" else KINDS
            if suffix == ".gsc" and len(bindings) != 1:
                fail("Standalone GSC payload must bind exactly one ScriptFile root")
            if any(nodes.get(s.casefold(), {}).get("kind") not in kinds for s in bindings):
                fail("Payload format cannot contain its declared root asset kind")
            payload_bindings.append((role, bindings, kinds, suffix == ".gsc"))
        if source is None or entry["bytes"] is None or entry["sha256"] is None:
            (pending if stage == "plan" else errors).append("Payload not established: " + str(fid))
        if source is not None:
            if not safe_path(source):
                fail("Unsafe payload source path")
                continue
            if source.casefold() in sources:
                fail("Duplicate or Windows case-colliding payload source: " + source)
            sources.add(source.casefold())
        if entry["bytes"] is not None and (type(entry["bytes"]) is not int or entry["bytes"] <= 0):
            fail("Payload size must be a positive integer")
        if entry["sha256"] is not None and not sha(entry["sha256"]):
            fail("Invalid payload SHA-256")
        if stage == "plan" or source is None or base is None:
            continue
        path = base / source
        try:
            # Resolve every ancestor and reject links/reparse points before opening.
            current = base
            for ancestor in (base, *base.parents):
                meta = ancestor.lstat()
                if stat.S_ISLNK(meta.st_mode) or getattr(meta, "st_file_attributes", 0) & 0x400:
                    raise ValueError("Redirected payload root")
            for part in source.split("/"):
                current /= part
                meta = current.lstat()
                if stat.S_ISLNK(meta.st_mode) or getattr(meta, "st_file_attributes", 0) & 0x400:
                    raise ValueError("Redirected payload path")
            if not path.resolve().is_relative_to(base.resolve()) or not path.is_file():
                raise ValueError("Payload is not a regular contained file")
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as stream:
                before = stream.fileno()
                before = os.fstat(before)
                if not stat.S_ISREG(before.st_mode):
                    raise ValueError("Nonregular payload")
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(block)
                    digest.update(block)
                after = os.fstat(stream.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                    raise ValueError("Payload changed during integrity check")
            if size != entry["bytes"] or digest.hexdigest() != str(entry["sha256"]).lower():
                fail("Payload size/hash mismatch: " + source)
            else:
                checked.append(fid)
        except (OSError, ValueError) as error:
            fail("Cannot verify payload " + source + ": " + str(error))

    # Following a server root into a client dependency does not ship that asset.
    # Each deliverable root must bind a file of its own role. Each deliverable
    # node must then be reachable from such a file without crossing the other
    # role; recipient nodes are reviewed pre-existing dependencies, not payloads.
    for name in roots:
        key = name.casefold()
        scope = nodes.get(key, {}).get("scope")
        if scope in bound_roots and key not in bound_roots[scope]:
            fail("Deliverable closure root has no matching-role file: " + name)
    covered = {"client": set(), "server": set()}
    for role, bindings, kinds, standalone in payload_bindings:
        seen, queue = set(), [s.casefold() for s in bindings]
        while queue:
            key = queue.pop()
            if key in seen or key not in nodes:
                continue
            seen.add(key)
            node = nodes[key]
            if node["scope"] not in {role, "recipient"}:
                continue
            if node["scope"] == role:
                if node["kind"] not in kinds:
                    continue
                covered[role].add(key)
            if not standalone:
                queue.extend(s.casefold() for s in node["requires"])
    for key, node in nodes.items():
        scope = node["scope"]
        if scope in covered and key not in covered[scope]:
            fail("Deliverable dependency has no matching-role payload coverage: " + node["id"])
    if delivery == "mod" and f"mods/{module}/mod.ff" not in destinations:
        fail("Mod requires mandatory mod.ff; optional audio cannot replace it")
    if delivery == "usermap" and f"usermaps/{module}/{module}.ff" not in destinations:
        fail("Usermap requires mandatory main fastfile")

    evidence = {}
    for record in items(data["evidence"], "evidence"):
        if not fields(record, {"kind", "status", "reference", "authority", "maps"}, "evidence record"):
            continue
        kind = record["kind"]
        if not isinstance(kind, str) or kind not in EVIDENCE or kind in evidence:
            fail("Invalid or duplicate evidence kind")
            continue
        evidence[kind] = record
        if record["status"] not in {"pending", "pass", "fail"}:
            fail("Invalid evidence status")
        if record["authority"] not in {"agent", "owner"}:
            fail("Evidence authority must be agent or owner")
        coverage = strings(record["maps"], "evidence.maps")
        if set(coverage) - set(maps):
            fail("Evidence coverage outside module maps")
        if record["status"] == "pass" and (not coverage or not isinstance(record["reference"], str) or not record["reference"].strip()):
            fail("Passing evidence requires coverage and a traceable reference")
        if record["status"] == "fail":
            (pending if stage != "delivery" else errors).append("Failed evidence: " + kind)
    if stage == "delivery":
        required_evidence = {"source-check", "runtime-link"}
        if any(f.get("role") == "client" for f in files if isinstance(f, dict)):
            required_evidence.add("offline-load")
        for kind in required_evidence:
            record = evidence.get(kind, {})
            if record.get("status") != "pass" or set(record.get("maps", [])) != set(maps):
                fail("Delivery requires passed " + kind + " evidence for every declared map")
    owner = evidence.get("gameplay", {})
    accepted = owner.get("status") == "pass" and owner.get("authority") == "owner" and set(owner.get("maps", [])) == set(maps)
    return {"schema": SCHEMA, "valid": not errors, "ready": stage != "plan" and not errors and not pending,
            "stage": stage, "target": target, "errors": errors, "pending": pending, "checked": checked,
            "declared_owner_gameplay_accepted": bool(accepted and not errors),
            "readiness_scope": "Declared transport contract and local file integrity only; not executable/version or game acceptance.",
            "validation_limit": "Node hashes, dependency closure and evidence references are manifest assertions. Supplied source pins are not measured executable provenance. No runtime, rendering or gameplay test was executed."}


def validate(data, root=None, stage="plan", target="stock", client_source=None, server_source=None):
    try:
        return _validate(data, root, stage, target, client_source, server_source)
    except (TypeError, ValueError, KeyError, AttributeError) as error:
        return {"schema": SCHEMA, "valid": False, "ready": False,
                "errors": ["Malformed manifest: " + str(error)], "pending": [], "checked": [],
                "declared_owner_gameplay_accepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--root")
    parser.add_argument("--stage", choices=("plan", "package", "delivery"), default="plan")
    parser.add_argument("--target", choices=("stock", "native"), default="stock")
    parser.add_argument("--client-source")
    parser.add_argument("--server-source")
    args = parser.parse_args()
    try:
        result = validate(load_manifest(args.manifest), args.root, args.stage, args.target, args.client_source, args.server_source)
    except (OSError, ValueError, TypeError) as error:
        result = {"schema": SCHEMA, "valid": False, "ready": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["valid"] and (args.stage == "plan" or result["ready"]) else 1


if __name__ == "__main__":
    sys.exit(main())
