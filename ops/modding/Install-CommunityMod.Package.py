"""Bounded reader/stager for the existing community ZIP, never a ZIP writer.

Inspect writes nothing. Stage uses a fresh private directory and the real SDK
package/delivery gates before the PowerShell installer can touch its targets.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


sdk = module(REPO / "sdk/modding/manifest.py", "install_sdk")
pack = module(Path(__file__).with_name("Package-CommunityMod.py"), "install_pack")


def strict_json(raw):
    # JSON decoding only; SDK/transport remain the sole manifest validators.
    def pairs(values):
        out = {}
        for key, value in values:
            if key in out:
                raise ValueError("Duplicate JSON key: " + key)
            out[key] = value
        return out
    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite JSON value")
        return number
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON value")))


def inspect(args):
    path = pack.no_redirects(Path(args.archive))
    if not path.is_file() or not 0 < path.stat().st_size <= args.max_bytes:
        raise ValueError("Archive must be a bounded regular file")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != args.sha256.lower():
            raise ValueError("Archive SHA-256 differs")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= 4096 or sum(i.file_size for i in infos) > args.max_bytes:
                raise ValueError("Archive entry/expanded size budget exceeded")
            names = set()
            for info in infos:
                mode = (info.external_attr >> 16) & 0xFFFF
                if (not sdk.transport.safe_path(info.filename) or info.orig_filename != info.filename
                        or info.filename.casefold() in names or info.is_dir() or info.flag_bits & 1
                        or info.compress_type != zipfile.ZIP_STORED or info.file_size != info.compress_size
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or info.external_attr & 0x410):
                    raise ValueError("Unsafe, redirected, duplicate or unsupported ZIP entry")
                names.add(info.filename.casefold())
            info = archive.getinfo("manifest.json")
            if info.file_size > 1024 * 1024:
                raise ValueError("Manifest exceeds 1 MiB")
            data = strict_json(archive.read(info))
            report = sdk.validate(data, stage="plan", target=args.target,
                                  client_source=args.client_source, server_source=args.server_source)
            if not report["valid"]:
                raise ValueError("SDK plan gate: " + "; ".join(report["errors"]))
            if data["dependencies"] or data["conflicts"]:
                raise ValueError("Installer v1 requires a standalone package without unresolved active-set declarations")
            errors = pack.compat.check_environment([data], client_source=args.client_source,
                                                   server_source=args.server_source, protocol=args.protocol, mode="cp")
            if errors:
                raise ValueError("Compatibility gate: " + "; ".join(errors))
            package = data["package"]
            expected, rows = {"manifest.json"}, []
            for entry in package["files"]:
                destination = entry["destination"]
                allowed = ({f"mods/{package['id']}/mod.{ext}" for ext in ("ff", "sabl", "sabs")}
                           if entry["role"] == "client" else {f"iw7-mod/custom_scripts/cp/{package['id']}.gsc"})
                if destination not in allowed or not entry["bytes"] or not entry["sha256"] or not entry["source"]:
                    raise ValueError("Installer supports only measured namespaced GSC and the three mod files")
                for prefix in (("server", "fastdl") if entry["role"] == "client" else ("server",)):
                    name = prefix + "/" + destination
                    expected.add(name)
                    member = archive.getinfo(name)
                    if member.file_size != entry["bytes"]:
                        raise ValueError("ZIP size mismatch: " + name)
                    with archive.open(member) as stream:
                        hashed = hashlib.file_digest(stream, "sha256").hexdigest()
                    if hashed != entry["sha256"].lower():
                        raise ValueError("ZIP payload SHA-256 mismatch: " + name)
                    rows.append(dict(Area=prefix, Relative=destination, Entry=name,
                                     Bytes=entry["bytes"], SHA256=hashed))
            if {i.filename for i in infos} != expected:
                raise ValueError("ZIP contains unexpected/missing entries")
            result = dict(PackageId=package["id"], Version=package["version"], Delivery=package["delivery"],
                          Rows=rows, ArchiveSHA256=digest, ArchiveBytes=path.stat().st_size,
                          PackageGatePending=True, PlanPending=report.get("pending", []),
                          DeliveryGate=None, runtime_ready=False, owner_accepted=False, public_deployment=False)
            if args.stage_root:
                root = Path(args.stage_root).absolute()
                pack.no_redirects(root.parent)
                root.mkdir()  # A fresh directory, never reuse an earlier failed stage.
                for entry in package["files"]:
                    target = root / entry["source"]  # Already checked by the real SDK.
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pack.no_redirects(target.parent)
                    with archive.open("server/" + entry["destination"]) as incoming, target.open("xb") as outgoing:
                        while block := incoming.read(1024 * 1024):
                            outgoing.write(block)
                gate = sdk.validate(data, root=root, stage="package", target=args.target,
                                    client_source=args.client_source, server_source=args.server_source)
                if not gate["valid"] or not gate["ready"]:
                    raise ValueError("SDK package gate: " + "; ".join(gate["errors"] + gate.get("pending", [])))
                result["PackageGatePending"] = False
                result["DeliveryGate"] = sdk.validate(data, root=root, stage="delivery", target=args.target,
                                                     client_source=args.client_source, server_source=args.server_source)
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--client-source", required=True)
    parser.add_argument("--server-source", required=True)
    parser.add_argument("--protocol", type=int, required=True)
    parser.add_argument("--target", choices=("stock", "native"), default="stock")
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--stage-root")
    args = parser.parse_args()
    try:
        if not 0 < args.max_bytes <= 64 * 1024 * 1024:
            raise ValueError("Budget must be in 1..64 MiB")
        print(json.dumps(inspect(args), allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"error": str(error), "public_deployment": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
