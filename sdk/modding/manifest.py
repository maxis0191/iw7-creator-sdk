"""Community mod contract v1. Read-only, standard-library API; never installs.

The embedded package is validated by the existing reviewed transport validator.
Dependencies and executable capabilities must additionally be resolved by the
distribution caller against its actual target; this module is not a loader.
"""
import argparse
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "iw7.community-mod/1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
spec = importlib.util.spec_from_file_location("iw7_transport_contract", REPO / "ops/Validate-ModPackage.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


def load_manifest(path):
    """Reject duplicate keys, nonfinite numbers and oversized manifest documents."""
    def pairs(values):
        out = {}
        for key, value in values:
            if key in out:
                raise ValueError("Duplicate JSON key: " + key)
            out[key] = value
        return out
    def invalid(value):
        raise ValueError("Nonfinite JSON number: " + value)
    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            invalid(value)
        return number
    with Path(path).open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("Manifest exceeds 1 MiB")
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=invalid, parse_float=finite)


def _shape(value, schema, path, errors):
    """Evaluate only the JSON Schema keywords used by our fixed bundled schema.

    This is deliberately not a general JSON Schema implementation. The embedded
    transport object is delegated to transport.validate, including strict fields.
    """
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            branch = []
            _shape(value, option, path, branch)
            if not branch:
                return
        errors.append(path + ": no allowed type/value matches")
        return
    kinds = {"object": dict, "array": list, "string": str, "integer": int,
             "boolean": bool, "null": type(None)}
    kind = schema.get("type")
    if kind and type(value) is not kinds[kind]:
        errors.append(path + ": expected " + kind)
        return
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        errors.append(path + ": unsupported constant")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(path + ": unsupported value")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                errors.append(path + ": unknown fields " + str(sorted(unknown)))
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            errors.append(path + ": missing fields " + str(sorted(missing)))
        for key, item in value.items():
            if key in properties:
                _shape(item, properties[key], path + "." + key, errors)
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 4096):
            errors.append(path + ": invalid item count")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            errors.append(path + ": duplicate items")
        for index, item in enumerate(value):
            _shape(item, schema.get("items", {}), f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 4096):
            errors.append(path + ": invalid string length")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(path + ": invalid string format")
    elif type(value) is int:
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            errors.append(path + ": integer outside range")


def validate(data, root=None, stage="plan", target="stock", client_source=None, server_source=None):
    """Same arguments as ops/Validate-ModPackage.py; no environment inference.

    valid: declared contract passes this stage. ready: package-stage static
    integrity/contract only. runtime_ready and owner_accepted are always False.
    The distribution layer resolves dependencies, conflicts, protocol and actual
    capabilities. This API does not turn those declarations into live evidence.
    """
    result = {"schema": SCHEMA, "valid": False, "ready": False, "stage": stage,
              "errors": [], "pending": [], "checked": [], "runtime_ready": False,
              "owner_accepted": False, "capability_evidence": {},
              "readiness_scope": "Static community contract and local transport integrity only; target compatibility requires distribution preflight.",
              "validation_limit": "No engine, packed inventory, dependency installation, binary provenance, runtime or gameplay acceptance is measured."}
    errors = result["errors"]
    try:
        _shape(data, load_manifest(HERE / "manifest.schema.json"), "$", errors)
        if errors:
            return result
        package = data["package"]
        report = transport.validate(package, root, stage, target, client_source, server_source)
        result["transport"] = report
        errors.extend("package: " + e for e in report["errors"])
        result["pending"].extend(report.get("pending", []))
        result["checked"] = report.get("checked", [])
        if not report["valid"]:
            return result
        identity = package["id"]
        if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", package["version"]):
            errors.append("package.version must be normalized numeric major.minor.patch")
        if data["namespace"] != identity:
            errors.append("namespace must equal package.id in v1")
        compatibility = data["compatibility"]
        expected = "server-only" if package["delivery"] == "server-only" else "exclusive-fs-game"
        if compatibility["coexistence"] != expected:
            errors.append("coexistence does not match package.delivery")
        if package["delivery"] == "usermap":
            errors.append("Community v1 does not qualify custom maps; use the separate transport plan for research")
        if compatibility["network_protocol"] is None:
            (result["pending"] if stage == "plan" else errors).append("Exact network_protocol must be measured before packaging")
        seen = set()
        for dep in data["dependencies"]:
            if dep["id"] == identity or dep["id"] in seen:
                errors.append("Self or duplicate dependency: " + dep["id"])
            seen.add(dep["id"])
        conflicts = set()
        for item in data["conflicts"]:
            if item["id"] == identity or item["id"] in conflicts or item["id"] in seen:
                errors.append("Self, duplicate or required conflict: " + item["id"])
            conflicts.add(item["id"])
        catalogue = load_manifest(HERE / "capabilities.json")["capabilities"]
        all_required = set()
        for side, requirements in data["requires"].items():
            for name in requirements:
                all_required.add(name)
                entry = catalogue.get(name)
                if entry is None or side not in entry["sides"]:
                    errors.append("Unknown capability or wrong side: " + side + "/" + name)
                    continue
                result["capability_evidence"][name] = entry["evidence_level"]
                if entry["evidence_level"] == "blocked":
                    (result["pending"] if stage == "plan" else errors).append("Capability not qualified: " + name)
        required = data["requires"]
        def need(side, name):
            if name not in required[side]:
                errors.append("Missing capability: " + side + "/" + name)
        need("engine", "iw7-cp/1")
        if package["delivery"] == "mod":
            need("client", "mod-fastfile-download/1")
            need("server", "mod-fastfile-host/1")
        for node in package["closure"]["nodes"]:
            if node["scope"] == "server" and node["kind"] == "scriptfile":
                need("server", "gsc-custom-scripts/1")
            if node["scope"] == "client" and node["kind"] == "luafile":
                need("client", "lua-fastfile/1")
                if "lua-fastfile" not in package["native_requirements"]["client_capabilities"]:
                    errors.append("Lua asset requires legacy transport lua-fastfile source gate")
            if node["scope"] == "client" and node["kind"] == "xmodel":
                need("client", "xmodel-rigid/1")
                need("engine", "model-netconststrings/1")
        nodes = {n["id"]: n for n in package["closure"]["nodes"]}
        endpoints = set()
        for entry in data["lifecycle"]["entrypoints"]:
            key = (entry["side"], entry["path"].casefold(), entry["symbol"])
            if key in endpoints or not transport.safe_path(entry["path"]):
                errors.append("Duplicate or unsafe lifecycle entrypoint")
            endpoints.add(key)
            kind = "scriptfile" if entry["side"] == "server" else "luafile"
            node = nodes.get(kind + ":" + entry["path"])
            if node is None or node["kind"] != kind or node["scope"] != entry["side"]:
                errors.append("Lifecycle entrypoint missing from matching asset closure: " + entry["path"])
            if entry["side"] == "server":
                if entry["path"] != "custom_scripts/cp/" + identity + ".gsc" or entry["symbol"] != "init":
                    errors.append("Server entrypoint must be custom_scripts/cp/<id>.gsc::init in v1")
                need("server", "gsc-custom-scripts/1")
                if not any(f["role"] == "server" and f["destination"] == "iw7-mod/custom_scripts/cp/" + identity + ".gsc"
                           and node and node["id"] in f["closure_roots"] for f in package["files"]):
                    errors.append("Server entrypoint requires exact standalone custom-script destination")
            elif entry["path"] != "ui_scripts/" + identity + "/__init__.lua" or entry["symbol"] != "module":
                errors.append("Client entrypoint must be ui_scripts/<id>/__init__.lua::module in v1")
        cleanup = set(data["lifecycle"]["cleanup"])
        if "gsc-private-hud/1" in all_required and "hud" not in cleanup:
            errors.append("HUD capability requires hud cleanup")
        if "script-model/1" in all_required and "entities" not in cleanup:
            errors.append("Model capability requires entities cleanup")
        if data["lifecycle"]["entrypoints"] and not {"threads", "player-state"} <= cleanup:
            errors.append("Entrypoints require threads and player-state cleanup")
        result["valid"] = not errors
        result["ready"] = bool(not errors and stage != "plan" and report.get("ready") and not result["pending"])
        return result
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        errors.append("Malformed contract or unavailable validator: " + str(error))
        return result


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
        data = load_manifest(args.manifest)
        result = validate(data, args.root, args.stage, args.target, args.client_source, args.server_source)
    except (OSError, ValueError, RecursionError) as error:
        result = {"schema": SCHEMA, "valid": False, "ready": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["valid"] and (args.stage == "plan" or result["ready"]) else 1


if __name__ == "__main__":
    sys.exit(main())
