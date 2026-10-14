"""Build an inert, deterministic ZIP from an SDK-validated community mod.

No network, extraction, installation, game launch or executable download. The
Default archive is operator staging; --layout player projects only client mod
files into a copyable game-root layout. Packaging is never gameplay acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
CHUNK = 1024 * 1024
MAX_MANIFEST = 1024 * 1024
DEFAULT_BUDGET = 64 * 1024 * 1024
LIMIT = ("Local declared contract and payload integrity only. No FF parsing, "
         "runtime, publisher authentication, installed-client provenance or gameplay acceptance.")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compat = load_module(Path(__file__).with_name("Distribution-Compat.py"), "distribution_compat")


def read_manifest(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_MANIFEST + 1)
    if len(raw) > MAX_MANIFEST:
        raise ValueError("Manifest exceeds 1 MiB")
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Invalid JSON constant: " + value)))


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def preflight_payload_budget(manifests_and_roots, max_bytes):
    """Bound reads before SDK package hashing; callers first run SDK plan shape."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("A positive byte budget is required")
    total = 0
    for manifest, directory in manifests_and_roots:
        root = no_redirects(directory)
        for entry in manifest["package"]["files"]:
            size = entry["bytes"]
            if type(size) is not int or size <= 0:
                raise ValueError("Measured payload size is required before packaging")
            total += size
            if total > max_bytes:
                raise ValueError("Payload verification exceeds preparation byte budget")
            path = payload_path(root, entry["source"])
            if path.stat().st_size != size:
                raise ValueError("Payload size mismatch before SDK hashing")


def no_redirects(path):
    path = Path(os.path.abspath(path))
    for item in (*reversed(path.parents), path):
        meta = item.lstat()
        if stat.S_ISLNK(meta.st_mode) or getattr(meta, "st_file_attributes", 0) & 0x400:
            raise ValueError("Redirected filesystem path refused: " + str(item))
    return path


def payload_path(root, relative):
    # The SDK supplies the stricter Windows path rules. Check containment again
    # at the write boundary instead of trusting a previous filesystem check.
    if not isinstance(relative, str) or "\\" in relative or any(part in ("", ".", "..") for part in relative.split("/")):
        raise ValueError("Unsafe payload path")
    path = no_redirects(root / relative)
    if not path.is_relative_to(root) or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Payload is not a regular contained file")
    return path


def fingerprint(meta):
    return meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns


def zip_info(name):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_STORED
    return info


def stream_payload(archive, name, root, entry):
    path = payload_path(root, entry["source"])
    digest, crc, total = hashlib.sha256(), 0, 0
    before_path = path.stat()
    with path.open("rb") as source, archive.open(zip_info(name), "w", force_zip64=True) as output:
        before = os.fstat(source.fileno())
        if fingerprint(before) != fingerprint(before_path) or not stat.S_ISREG(before.st_mode):
            raise ValueError("Payload changed before packaging: " + entry["source"])
        while True:
            block = source.read(min(CHUNK, entry["bytes"] + 1 - total))
            if not block:
                break
            total += len(block)
            if total > entry["bytes"]:
                raise ValueError("Payload exceeds declared size: " + entry["source"])
            digest.update(block)
            crc = zlib.crc32(block, crc)
            output.write(block)
        if fingerprint(before) != fingerprint(os.fstat(source.fileno())):
            raise ValueError("Payload changed during packaging: " + entry["source"])
    if fingerprint(before) != fingerprint(payload_path(root, entry["source"]).stat()):
        raise ValueError("Payload path changed during packaging: " + entry["source"])
    if total != entry["bytes"] or digest.hexdigest() != entry["sha256"].lower():
        raise ValueError("Payload size/SHA-256 mismatch at write: " + entry["source"])
    return {"destination": entry["destination"], "bytes": total, "sha256": digest.hexdigest(),
            # IW7 Windows x64 zlib uLong is 32 bits; dump_hex serializes its
            # in-memory little-endian bytes. It is not format(crc, '08X').
            "aurora_crc32": struct.pack("<I", crc & 0xffffffff).hex().upper()}


def validate_archive_options(layout, player_language):
    if layout not in ("staging", "player"):
        raise ValueError("Archive layout must be staging or player")
    if player_language not in ("en", "fr"):
        raise ValueError("Player language must be en or fr")
    if layout != "player" and player_language != "en":
        raise ValueError("French player instructions require player layout")


def write_archive(manifest, root, output, *, max_bytes=DEFAULT_BUDGET, layout="staging", player_language="en"):
    """Write already-validated data with a second integrity check while streaming."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("A positive byte budget is required")
    validate_archive_options(layout, player_language)
    root = no_redirects(root)
    output = Path(os.path.abspath(output))
    no_redirects(output.parent)
    if output.exists() or output.is_symlink():
        raise ValueError("Output exists; use a fresh output path")
    package = manifest["package"]
    metadata_name, metadata = "manifest.json", canonical_json(manifest)
    entries = []
    if layout == "player":
        if package["delivery"] != "mod":
            raise ValueError("Player archive requires client mod assets; server-only packages have nothing to install")
        entries = [(entry["destination"], entry) for entry in package["files"] if entry["role"] == "client"]
        if not any(name == "mods/" + package["id"] + "/mod.ff" for name, _ in entries):
            raise ValueError("Player archive requires the declared mod.ff")
        metadata_name = "PLAY.txt"
        metadata = (
            package["id"] + " " + package["version"] + "\n\n"
            "1. Close the game. Move an existing mods/" + package["id"] + " outside the game folder as a backup.\n"
            "2. Copy the mods folder from this archive into your Infinite Warfare game folder.\n"
            "3. Start the compatible community client supplied for this mod and join its server.\n\n"
            "The client is supplied separately. Server scripts and creator tools are not needed here.\n"
            "To undo: close the game, remove only the installed mods/" + package["id"] + ",\n"
            "then move your original backup folder back if you had one. Do not merge folders.\n"
        ).encode("utf-8")
        if player_language == "fr":
            metadata = (
                package["id"] + " " + package["version"] + "\n\n"
                "1. Fermez le jeu. Déplacez le dossier mods/" + package["id"] + " existant hors du dossier du jeu pour le sauvegarder.\n"
                "2. Copiez le dossier mods de cette archive dans le dossier de votre jeu Infinite Warfare.\n"
                "3. Lancez le client natif compatible fourni séparément pour ce mod.\n\n"
                "Les scripts serveur et les outils créateur ne sont pas nécessaires ici.\n"
                "Pour annuler : fermez le jeu, retirez uniquement le dossier mods/" + package["id"] + " installé,\n"
                "puis remettez votre sauvegarde d'origine si vous en aviez une. Ne fusionnez pas les dossiers.\n"
            ).encode("utf-8")
    else:
        for entry in package["files"]:
            entries.append(("server/" + entry["destination"], entry))
            if entry["role"] == "client":
                entries.append(("fastdl/" + entry["destination"], entry))
    if len(entries) > 4096:
        raise ValueError("Too many archive entries")
    if len({name.casefold() for name, _ in entries}) != len(entries):
        raise ValueError("Archive path collision")
    # Conservative ZIP64/UTF-8 name overhead bound; duplicates for server/HTTP
    # are intentional and charged twice. No accidental full directory walk.
    estimate = len(metadata) + sum(entry["bytes"] for _, entry in entries)
    estimate += sum(2 * len(name.encode("utf-8")) + 256 for name, _ in entries) + 2048
    if estimate > max_bytes:
        raise ValueError("Archive exceeds preparation byte budget")
    fd, temporary = tempfile.mkstemp(prefix=".iw7-package-", suffix=".tmp", dir=output.parent)
    try:
        reports = {}
        with os.fdopen(fd, "w+b") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
                for name, entry in sorted(entries + [(metadata_name, None)], key=lambda item: item[0]):
                    if entry is None:
                        archive.writestr(zip_info(name), metadata)
                    else:
                        reports[entry["id"]] = stream_payload(archive, name, root, entry)
            stream.flush()
            os.fsync(stream.fileno())
            if stream.tell() > max_bytes:
                raise ValueError("Final archive exceeds byte budget")
            stream.seek(0)
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            size = os.fstat(stream.fileno()).st_size
        no_redirects(output.parent)
        # Same-directory hardlink publication is no-replace, unlike os.replace.
        # It leaves the final name absent after any earlier validation failure.
        os.link(temporary, output)
        return {"archive": str(output), "archive_sha256": digest, "archive_bytes": size, "archive_layout": layout,
                "files": [reports[key] for key in sorted(reports)]}
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layout", choices=("staging", "player"), default="staging",
                        help="Operator server/FastDL staging, or player-only mods folder and short instructions")
    parser.add_argument("--player-language", choices=("en", "fr"), default="en",
                        help="Language of player instructions; French requires player layout")
    parser.add_argument("--sdk-root", type=Path, default=ROOT / "sdk/modding",
                        help="Reviewed local SDK source directory; never read from a manifest")
    parser.add_argument("--active", action="append", nargs=2, default=[], metavar=("MANIFEST", "ROOT"),
                        help="Every other intended active mod and its measured payload root; repeatable")
    parser.add_argument("--client-source", required=True)
    parser.add_argument("--server-source", required=True)
    parser.add_argument("--protocol", type=int, required=True)
    parser.add_argument("--mode", choices=("cp", "mp"), default="cp")
    parser.add_argument("--target", choices=("stock", "native"), default="stock")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_BUDGET)
    args = parser.parse_args()
    try:
        validate_archive_options(args.layout, args.player_language)
        if len(args.active) > 64:
            raise ValueError("At most 64 other active manifests can be inspected per package")
        sdk = load_module(args.sdk_root / "manifest.py", "community_sdk")
        manifest = read_manifest(args.manifest)
        installed = [(read_manifest(path), root) for path, root in args.active]
        for candidate, _ in [(manifest, args.root), *installed]:
            plan = sdk.validate(candidate, stage="plan", target=args.target,
                                client_source=args.client_source, server_source=args.server_source)
            if not plan["valid"]:
                raise ValueError("SDK contract gate: " + "; ".join(plan["errors"]))
        preflight_payload_budget([(manifest, args.root), *installed], args.max_bytes)
        report = sdk.validate(manifest, root=args.root, stage="package", target=args.target,
                              client_source=args.client_source, server_source=args.server_source)
        if not report["valid"] or not report["ready"]:
            raise ValueError("SDK package gate: " + "; ".join(report["errors"] + report.get("pending", [])))
        for active, active_root in installed:
            result = sdk.validate(active, root=active_root, stage="package", target=args.target,
                                  client_source=args.client_source, server_source=args.server_source)
            if not result["valid"] or not result["ready"]:
                raise ValueError("Active manifest SDK gate: " + "; ".join(result["errors"] + result.get("pending", [])))
        errors = compat.check_environment([manifest, *(active for active, _ in installed)], client_source=args.client_source,
                                         server_source=args.server_source, protocol=args.protocol, mode=args.mode)
        if errors:
            raise ValueError("Compatibility gate: " + "; ".join(errors))
        result = write_archive(manifest, Path(args.root), Path(args.output), max_bytes=args.max_bytes,
                               layout=args.layout, player_language=args.player_language)
        result.update(valid=True, packaged=True, ready_to_deploy=False, validation_limit=LIMIT,
                      active_dependencies="Payloads checked at supplied roots; running-server state is not inspected.")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        result = {"valid": False, "packaged": False, "ready_to_deploy": False, "errors": [str(error)], "validation_limit": LIMIT}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
