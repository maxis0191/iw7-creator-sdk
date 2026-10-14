"""Bounded reader/stager for the existing community ZIP, never a ZIP writer.

Inspect writes nothing. Stage uses a fresh private directory and the real SDK
package/delivery gates before the PowerShell installer can touch its targets.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
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


def checked_entries(archive, maximum):
    """The existing operator and closed player layouts share the ZIP guards."""
    infos = archive.infolist()
    if not 1 <= len(infos) <= 4096 or sum(i.file_size for i in infos) > maximum:
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
    return infos


def source_json(path):
    path = pack.no_redirects(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 128 * 1024:
        raise ValueError("Bounded canonical source witness required")
    with path.open("rb") as stream:
        held = os.fstat(stream.fileno())
        raw = stream.read(128 * 1024 + 1)
        after = os.fstat(stream.fileno())
    if (pack.fingerprint(before) != pack.fingerprint(held) or pack.fingerprint(held) != pack.fingerprint(after) or
            pack.fingerprint(after) != pack.fingerprint(path.stat()) or len(raw) != before.st_size):
        raise ValueError("Canonical source witness changed during its bounded snapshot")
    return strict_json(raw), {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def file_identity(meta):
    # Python 3.12 Windows inodes can be 128-bit. Decimal strings preserve them
    # through JSON consumers; this portable identity is not a native index64.
    return dict(kind="python-os-stat/1", device=str(meta.st_dev), inode=str(meta.st_ino),
                bytes=meta.st_size, mtime_ns=meta.st_mtime_ns)


def stage_player(args):
    """Inspect/stage only the retained private BO3 player packet; never install."""
    if (type(args.max_bytes) is not int or not 0 < args.max_bytes <= 64 * 1024 * 1024 or
            type(args.protocol) is not int or args.protocol != 2 or args.target != "native"):
        raise ValueError("Player witness requires a typed bounded budget, native target and protocol 2")
    profile = sdk.HERE / "examples/private-bo3-prop"
    manifest, manifest_ref = source_json(profile / "manifest.json")
    validation, validation_ref = source_json(profile / "physical-validation.json")
    if validation.get("schema") != "iw7.private-bo3-packet-validation/1" or validation["physical"]["verified"] is not True:
        raise ValueError("Canonical physical packet witness required")
    report = sdk.validate(manifest, stage="plan", target=args.target,
                          client_source=args.client_source, server_source=args.server_source)
    if not report["valid"] or manifest["namespace"] != "paris_bo3_static_probe":
        raise ValueError("SDK player witness plan gate: " + "; ".join(report["errors"]))
    errors = pack.compat.check_environment([manifest], client_source=args.client_source,
                                           server_source=args.server_source, protocol=args.protocol, mode="cp")
    if errors:
        raise ValueError("Compatibility gate: " + "; ".join(errors))
    client = [row for row in manifest["package"]["files"] if row["role"] == "client"]
    expected = validation["physical"]["player_archive"]
    relative = "mods/paris_bo3_static_probe/mod.ff"
    if (len(client) != 1 or client[0]["destination"] != relative or
            set(expected["members"]) != {"PLAY.txt", relative} or
            expected["members"][relative] != {"bytes": client[0]["bytes"], "sha256": client[0]["sha256"]} or
            validation["physical"]["ff"] != expected["members"][relative] or
            type(expected["bytes"]) is not int or not 0 < expected["bytes"] <= min(args.max_bytes, 128 * 1024) or
            not isinstance(args.sha256, str) or args.sha256.lower() != expected["sha256"]):
        raise ValueError("Exact private player archive and client witness required")
    for record in expected["members"].values():
        if (type(record["bytes"]) is not int or not 0 < record["bytes"] <= args.max_bytes or
                not isinstance(record["sha256"], str) or len(record["sha256"]) != 64 or
                any(c not in "0123456789abcdef" for c in record["sha256"])):
            raise ValueError("Typed source member binding required")
    root = None
    owner = None
    if args.stage_root:
        owner_arg = getattr(args, "stage_owner_root", None)
        if not owner_arg or not Path(owner_arg).is_absolute() or not Path(args.stage_root).is_absolute():
            raise ValueError("Explicit absolute player stage and owned operation roots required")
        owner = pack.no_redirects(Path(owner_arg))
        root = Path(os.path.abspath(args.stage_root))
        if not owner.is_dir() or root == owner or not root.is_relative_to(owner):
            raise ValueError("Player stage must be a fresh child of its owned operation root")
        pack.no_redirects(root.parent)
        if root.exists() or root.is_symlink():
            raise ValueError("Fresh player staging root required")
    elif getattr(args, "stage_owner_root", None):
        raise ValueError("Player stage owner requires a stage root")
    path = pack.no_redirects(Path(args.archive))
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != expected["bytes"]:
        raise ValueError("Exact bounded player archive size required")
    with path.open("rb") as source:
        held = os.fstat(source.fileno())
        raw = source.read(expected["bytes"] + 1)
        after = os.fstat(source.fileno())
        if (pack.fingerprint(before) != pack.fingerprint(held) or pack.fingerprint(held) != pack.fingerprint(after)
                or pack.fingerprint(after) != pack.fingerprint(path.stat()) or len(raw) != expected["bytes"]):
            raise ValueError("Player archive identity changed during its bounded snapshot")
    if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError("Player archive SHA-256 differs")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = checked_entries(archive, args.max_bytes)
        if {info.filename for info in infos} != set(expected["members"]) or len(infos) != 2:
            raise ValueError("Player ZIP must contain exactly its two pinned members")
        payloads = {}
        for info in infos:
            binding = expected["members"][info.filename]
            if info.file_size != binding["bytes"]:
                raise ValueError("Player member size differs: " + info.filename)
            payload = archive.read(info)  # CRC checked on the same hashed BytesIO snapshot.
            if hashlib.sha256(payload).hexdigest() != binding["sha256"]:
                raise ValueError("Player member SHA-256 differs: " + info.filename)
            payloads[info.filename] = payload
    row = dict(Area="client", Relative=relative, Entry=relative,
               Bytes=client[0]["bytes"], SHA256=client[0]["sha256"])
    result = dict(Schema="iw7.private-bo3-player-stage/1", PackageId=manifest["package"]["id"],
                  Version=manifest["package"]["version"], ArchiveLayout="player", Rows=[row],
                  ArchiveSHA256=expected["sha256"], ArchiveBytes=len(raw), ArchiveIdentity=file_identity(held),
                  SnapshotMode="single-bounded-bytesio", PlayerPayloadVerified=True, PlayerStageVerified=False,
                  StageRoot=None, StageOwnerRoot=None, StageIdentity=None, StageModRoot=None, StageModIdentity=None,
                  SourceReferences={"manifest": manifest_ref, "physical_validation": validation_ref,
                  "archive_producer_source": validation["sdk"]["source"], "archive_producer_merge": validation["sdk"]["merge"]},
                  PackageGatePending=True, DeliveryGate=None, installed=False, runtime_ready=False,
                  owner_accepted=False, public_deployment=False, NativePrerequisiteMeasured=False,
                  ValidationLimit="Client payload integrity only; no full GSC package, installation, binary, load or game acceptance")
    if root is not None:
        root.mkdir()
        target = root / relative
        target.parent.mkdir(parents=True)
        pack.no_redirects(target.parent)
        with target.open("xb") as outgoing:
            outgoing.write(payloads[relative])
        pack.no_redirects(target)
        if target.stat().st_size != row["Bytes"] or hashlib.sha256(target.read_bytes()).hexdigest() != row["SHA256"]:
            raise ValueError("Player staging payload differs")
        result.update(PlayerStageVerified=True, StageRoot=str(root), StageIdentity=file_identity(target.stat()),
                      StageOwnerRoot=str(owner), StageModRoot=str(target.parent),
                      StageModIdentity=file_identity(target.parent.stat()))
    return result


def inspect(args):
    layout = getattr(args, "layout", "staging")
    if layout == "player":
        return stage_player(args)
    if layout != "staging" or getattr(args, "stage_owner_root", None):
        raise ValueError("Unsupported layout or player-only staging option")
    path = pack.no_redirects(Path(args.archive))
    if not path.is_file() or not 0 < path.stat().st_size <= args.max_bytes:
        raise ValueError("Archive must be a bounded regular file")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != args.sha256.lower():
            raise ValueError("Archive SHA-256 differs")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            infos = checked_entries(archive, args.max_bytes)
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
    parser.add_argument("--layout", choices=("staging", "player"), default="staging",
                        help="Operator staging, or only the retained private BO3 player packet")
    parser.add_argument("--stage-owner-root", help="Existing owned operation root containing a fresh player stage")
    args = parser.parse_args()
    try:
        if not 0 < args.max_bytes <= 64 * 1024 * 1024:
            raise ValueError("Budget must be in 1..64 MiB")
        print(json.dumps(inspect(args), allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"error": str(error), "public_deployment": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
