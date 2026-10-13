"""Read-only linkage of retained recipient bytes to an independently pinned Run.

This binds consistent local records, not authenticated execution or retail stock.
No subprocess, engine, network, file writer, package gate or GSC disassembler.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import re
import stat
import sys

_verify_spec = importlib.util.spec_from_file_location("iw7_recipient_run_verify", Path(__file__).with_name("verify.py"))
v = importlib.util.module_from_spec(_verify_spec)
_verify_spec.loader.exec_module(v)

PROVIDERS = (
    "ops/Base-Client.Core.ps1", "ops/model-lab/ModelFF.Core.ps1",
    "ops/hud-lab/HudFileIdentity.cs", "ops/Resource-Scheduler.Core.ps1",
    "ops/Resource-Memory.ps1", "ops/native/ResourceMemory.cs",
    "ops/Resource-RecorderOwnedProcess.Core.ps1", "sdk/modding/BeaconFF.Core.ps1",
    "sdk/modding/beacon_tool_phase.py", "tools-source/asset-bridge/model/BuildJob.cs",
    "tools-source/asset-bridge/common/StockBinding.Core.ps1",
    "tools-source/asset-bridge/animation/AnimationFF.Core.ps1",
)
PRODUCERS = ("recipient_phase.py", "recipient_contract.py", "Recipient.Core.ps1",
             "Run-RecipientClosure.ps1", "provider-pins.json")
OVERLAY_PRODUCERS = ("Recipient.Stock.ps1", "recipient_dialog.py", "Recipient.Light.ps1")
BASELINE_SHA = "4cf67ebe1645c6c0761b9a24cb4e4630edee9c5d737742c704d624fe60cb3850"
REVIEWED_SHA = "9116255ef148a324df15fa914795a7917615f023973111fdc39ae7329a9dcbf4"
TOOL_SOURCE = "fab935826c898806855376662a8a03317b3ad8f1"
OVERLAY_PROFILE = "observed-cp-paks-17-19-37-53"
PAKS = (("assetfile17.pak", 104595492, "6f5c0d1937b5a707d4e1fb3009f68a827714d9e4a72ff2d6570b57dbf6b0f058"),
        ("assetfile19.pak", 418201636, "064b6d23cfcec2baedf1a5589fcd602fb1cfbdbb2040d88d21cb8a8ca7779b0d"),
        ("assetfile37.pak", 53477412, "839c1da30e43b9c5c78cc457d3fa3ef61bd85ae818c81a2d2d0b30ff187fb349"),
        ("assetfile53.pak", 3817508, "b0c4ac18f4f9965a396b74ce8fbe2118d6fd6f68d92e7295ad29bc7bc2fbf773"))
FIVE_PROFILE = "observed-cp-paks-17-19-37-53-69"
FIVE_PAKS = PAKS + (("assetfile69.pak", 386465828, "042c8d62a3a24acd21a5502a5a111e6e426e870505da3cdd62ada3c3a23c496f"),)
E2_FATAL_SHA = "867e858ecd4bffde50a04e62488e42b73f528177e0e01b51a081bc030dbbb280"
COMPLETE_PROFILE = "doom-reviewed-all-asset-paks-20261012"
F_FATAL_SHA = "67995123ab95d54de3ddb9ffb0f52015daa0978f3c782c977a7c9a3a3c9f58f3"
INVENTORY_SHA = "683c8a39b6bd289a2acc0a27129a038361d5a217d6ef129d07da739feb6f76bf"
INVENTORY_LIMIT = 128 * 1024
BASE_PAK = ("assetfile1.pak", 10469412, "2c9ee05175e04f14644687de63212cdd1d2b332bd7ca9c423ebd4d28595740a9")
# Immutable reviewed names/bytes/hashes from f57b530; never scan a stock root.
COMPLETE_PAKS = (
    ("assetfile17.pak", 104595492, "6f5c0d1937b5a707d4e1fb3009f68a827714d9e4a72ff2d6570b57dbf6b0f058"),
    ("assetfile19.pak", 418201636, "064b6d23cfcec2baedf1a5589fcd602fb1cfbdbb2040d88d21cb8a8ca7779b0d"),
    ("assetfile21.pak", 944406564, "5db444e20c87a85fa896778fb5e650a6b532e192ed2d28bcdec909c2416498b3"),
    ("assetfile25.pak", 87621668, "8d2232f08d2690914682d3f094055ce04283bd67053a5a6773cced101a9a19b6"),
    ("assetfile26.pak", 403406884, "d19de294a551e84a6ef14bd5d045e3315a25d4a454d0e0e4ad35f33807320ea5"),
    ("assetfile36.pak", 61964324, "6835e02f5a1a8e99edb97b43e51c27d2603f2903a3d2687e2185168c37608fb9"),
    ("assetfile37.pak", 53477412, "839c1da30e43b9c5c78cc457d3fa3ef61bd85ae818c81a2d2d0b30ff187fb349"),
    ("assetfile52.pak", 42762276, "e377d1eea6b9f84689146ab3eb930de4ff020151242bc6d6b217b3637bb3f522"),
    ("assetfile53.pak", 3817508, "b0c4ac18f4f9965a396b74ce8fbe2118d6fd6f68d92e7295ad29bc7bc2fbf773"),
    ("assetfile68.pak", 26148900, "e35faa16d54246d545181967a08c5739066f88470e16874812cf8384102d3f15"),
    ("assetfile69.pak", 386465828, "042c8d62a3a24acd21a5502a5a111e6e426e870505da3cdd62ada3c3a23c496f"),
    ("assetfile84.pak", 311001124, "ff5edecc4b9c59542418573e952ce97d380bb4bdd51233d179a63ccb5d662864"),
    ("assetfile85.pak", 325582884, "335685b9eef52b686a19122e1004503c6ae7d0fad62bfc4577dbb9d4218ddf65"),
    ("assetfile100.pak", 240828452, "87fdac4e56255896c27cbd1722711b3e03cb76871cc46d6acdd0ed6fef7a27d3"),
    ("assetfile101.pak", 395509796, "919308f769389718621883149ec9801eafab8895e3a9e74ae73e1d702aa30b38"),
    ("assetfile116.pak", 321585188, "5619c4fc9e5e5de9fce26385b8265e292dddabfc5619772ebb332a90ce6c0998"),
    ("assetfile117.pak", 17383460, "ab9b6e1d626f29393c99370ec107192776f89e7b88e01219191473fe58f37e7b"),
    ("assetfile132.pak", 15335460, "5c13268f235a78ea682c528974206b38aa9bc705412eb9239ffa09a67a979c27"),
    ("assetfile133.pak", 6619172, "3258818e9d584301e6cd081029cef67376f422a3cb77955d7adb3cd44c419af6"),
    ("assetfile148.pak", 9650212, "b86aa968ea633983f61266ed945554d1a2f7f9c5ef17d11938d2516f36ab669c"),
    ("assetfile149.pak", 229867556, "5a733ff9189e8f52a1a4a999a142be0a3fb6a58d18ba6266439e7de48ff8ab02"),
    ("assetfile164.pak", 242434084, "a2ba6569d99c2af4122e47ada2200248e2359fb17dce2850eb61e3e921086b27"),
    ("assetfile165.pak", 6045732, "06418d501c15f041af0f3d52df649be8d228265a33d33bd80dc20c6596bf879d"),
    ("assetfile180.pak", 33882148, "46079f24957408d20b5ab3fe4aca99df838bf3a4e4e9dc7e93015bbe96037e00"),
    ("assetfile181.pak", 1376292, "481c3f64b6ef7f1eb2a7bd82378ccabfc9f524a6db63ecf42f8f3e9a9aeb066f"),
    ("assetfile196.pak", 229412, "ef73a72b327a1f819ead79e52c97df6502bb8efe53b384225b9bc0c32e0799c2"),
    ("assetfile197.pak", 1376292, "3bfd3de923aad62df54b78faa394198bfd083725aa46c5b3163749fcf5b4c518"),
    ("assetfile212.pak", 229412, "a09af42dbe7d0ef71bd21f402adb8e09907b3d6745dd958e08fbf3725fe87e57"),
    ("assetfile213.pak", 1376292, "032c32788051bf53d85dd3f3b98bd7319be571fba26af33de5bb03c24bf8dec5"),
    ("assetfile228.pak", 229412, "2ac06f84f11ffb56d9313e1ebf5fd920d0209e30a7d5e3e867692d5822a76e46"),
    ("assetfile229.pak", 1572900, "b29bc71373e6558ad150944cd12a0bb06e52b78c02e4135779abf5a66b5476ed"),
    ("assetfile244.pak", 524324, "56d3108877108e1c81bc7aa9a229c3f83bfc3bdd8c8f348a58aad71618ec4da2"),
)
STOCK_PROFILES = {
    OVERLAY_PROFILE: {"schema": "iw7.recipient-stock-observation/1", "paks": PAKS,
                      "bytes": 580092048, "limit": 600 * 1024**2, "additional": 0, "evidence": None},
    FIVE_PROFILE: {"schema": "iw7.recipient-stock-observation/2", "paks": FIVE_PAKS,
                   "bytes": 966557876, "limit": 966557876, "additional": 386465828, "evidence": E2_FATAL_SHA},
    COMPLETE_PROFILE: {"schema": "iw7.recipient-stock-observation/3", "paks": COMPLETE_PAKS,
                       "bytes": 4695508096, "limit": 4695508096, "additional": 4115416048, "evidence": F_FATAL_SHA},
}
DIAGNOSTIC_LIMITS = {"DiagnosticPollMilliseconds": 250, "DiagnosticTextBytes": 16384,
                     "DiagnosticControlLimit": 8, "DiagnosticMessageTimeoutMilliseconds": 200,
                     "DiagnosticRecordBytes": 65536}
REQUESTS = ("recipient-material.csv", "recipient-scripts.txt")
PROFILE = {"PhysicalBytes": 8 * 1024**3, "CommitBytes": 11 * 1024**3,
           "OutputStopBytes": 256 * 1024**2, "LogBytesPerStream": v.LIMIT,
           "PhaseSeconds": 240, "OuterPhaseSeconds": 245,
           "RootExitDrainSeconds": 5, "OverallSeconds": 600}
ERROR = re.compile(r"\[ ERROR \]|\[ FATAL \]|could not be found|Could not find referenced", re.I)


def exact_keys(value, keys, label):
    v.require(isinstance(value, dict) and set(value) == set(keys), label + " fields differ")


def same(a, b, label):
    v.require(v.canonical(a) == v.canonical(b), label + " differs")


def integer(value, low, high, label):
    v.require(type(value) is int and low <= value <= high, label + " is not a bounded integer")


def absolute(value):
    # Do not normalize traversal, ADS, device aliases or relative paths into trust.
    v.require(isinstance(value, str) and value and not value.startswith(("\\\\", "//")), "Local absolute path required")
    path = Path(value)
    v.require(path.is_absolute(), "Local absolute path required")
    for part in path.parts[1:]:
        v.require(part not in (".", "..") and part == part.rstrip(" .") and ":" not in part
                  and not re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part), "Unsafe absolute path")
    v.require(os.path.normcase(str(path)) == os.path.normcase(os.path.abspath(value)), "Noncanonical absolute path")
    return path


def path_key(value):
    return os.path.normcase(str(absolute(str(value))))


def same_path(value, expected, label):
    v.require(path_key(value) == path_key(expected), label + " path differs")


def pin_map(value):
    v.require(isinstance(value, dict) and 1 <= len(value) <= 64, "Independent source pins required")
    result = {}
    for path, checksum in value.items():
        key = path_key(path)
        v.require(key not in result, "Aliased source pin")
        result[key] = v.digest(checksum)
    return result


class Reader:
    """Bounded streams plus whole-group identity/hash recheck before returning."""
    def __init__(self):
        self.records = {}
        self.limits = {}
        self.absent = []
        self.total = 0

    def read(self, path, expected=None, limit=v.LIMIT, retain=True):
        path = v.no_redirects(absolute(str(path)))
        key = path_key(path)
        limit = min(limit, self.limits.get(key, limit))
        before = path.stat()
        v.require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "File type or byte bound differs")
        v.require(len(self.records) < 128 and self.total + before.st_size <= 256 * 1024**2, "Read group exceeds bound")
        digest, chunks, count = hashlib.sha256(), [], 0
        with path.open("rb") as stream:
            v.require(v.identity(os.fstat(stream.fileno())) == v.identity(before), "File changed before read")
            while block := stream.read(min(65536, before.st_size - count + 1)):
                count += len(block)
                v.require(count <= before.st_size, "File grew during read")
                digest.update(block)
                if retain:
                    chunks.append(block)
            v.require(v.identity(os.fstat(stream.fileno())) == v.identity(before), "File changed during read")
        v.require(count == before.st_size and v.identity(path.stat()) == v.identity(before), "File changed after read")
        checksum = digest.hexdigest()
        if expected is not None:
            v.require(checksum == v.digest(expected), "Independent file SHA-256 differs: " + str(path))
        record = {"path": key, "bytes": count, "sha256": checksum}
        if key in self.records:
            same(record, self.records[key][0], "Previously read file")
            v.require(v.identity(before) == self.records[key][1], "File replaced between reads")
        self.records[key] = record, v.identity(before)
        self.limits[key] = limit
        self.total += count
        return b"".join(chunks) if retain else record

    def absent_path(self, path):
        path = absolute(str(path))
        cursor = path
        while not os.path.lexists(cursor):
            cursor = cursor.parent
        v.no_redirects(cursor)
        v.require(not os.path.lexists(path), "Restored temporary input still exists")
        self.absent.append(path)

    def finish(self):
        # A later read cannot silently mix a replacement with earlier evidence.
        for record, identity in list(self.records.values()):
            path = v.no_redirects(Path(record["path"]))
            v.require(v.identity(path.stat()) == identity, "Evidence changed across group")
            self.read(path, record["sha256"], limit=self.limits[record["path"]], retain=False)
        for path in list(self.absent):
            self.absent_path(path)


def source_zones(inputs):
    names = {item["Relative"] for item in inputs}
    candidates = ["techsets_global_core_mp", "techsets_common_core_mp"]
    for zone in ("code_post_gfx", "global", "common", "global_mp", "global_cp", "common_mp", "common_cp", "cp_zmb"):
        candidates.extend(("techsets_" + zone, zone, "patch_" + zone))
    zones = [name for name in candidates if "main/" + name + ".ff" in names and "zone/" + name + ".ff" in names]
    v.require("cp_zmb" in zones and "techsets_cp_zmb" in zones, "Base/techset stock descriptors absent")
    return zones


def zone_log(raw, zones):
    text = raw.decode("utf-8-sig", errors="strict")
    v.require(not ERROR.search(text), "Native log reports errors")
    found = []
    for line in text.splitlines():
        match = re.search(r'(?:Loading zone|zone) "([^"\r\n]+)" (?:is already loaded)', line)
        if match is None:
            match = re.search(r'Loading zone "([^"\r\n]+)"\.\.\.', line)
        if match:
            found.append(match[1])
    same(found, zones, "Actual stdout source-zone sequence")


def closed_phase(identity, phase, python, zones):
    exact_keys(identity, ("Phase", "PID", "Image", "CreatedUtc", "Priority", "JobActiveAtClose", "ExitCode",
        "PostRootExitObservations", "PostRootExitDrainSeconds", "ResourceRegistration", "ObservedSourceZoneOrder", "Result"), "Phase identity")
    v.require(identity["Phase"] == phase, "Phase order differs")
    integer(identity["PID"], 1, 2**32 - 1, "Python PID")
    same_path(identity["Image"], python, "Original Python image")
    created = identity["CreatedUtc"]
    v.require(isinstance(created, str) and re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{7}(?:Z|\+00:00)", created), "Original creation identity absent")
    datetime.fromisoformat(created)
    for key, value in (("Priority", 16384), ("JobActiveAtClose", 0), ("ExitCode", 0), ("PostRootExitDrainSeconds", 5)):
        integer(identity[key], value, value, key)
    registration = identity["ResourceRegistration"]
    exact_keys(registration, ("Registered", "Outcome", "Attempts"), "Resource registration")
    integer(registration["Attempts"], 0, 100000, "Registration attempts")
    v.require((registration["Registered"] is True and registration["Outcome"] == "Registered" and registration["Attempts"] >= 1)
              or (registration["Registered"] is False and registration["Outcome"] == "ClosedBeforeRegistration"), "Unresolved registration")
    events = identity["PostRootExitObservations"]
    v.require(isinstance(events, list) and 1 <= len(events) <= 4096, "Original-job terminal observations required")
    previous, start = -1, None
    for index, event in enumerate(events):
        exact_keys(event, ("PhaseSeconds", "DrainSeconds", "Active", "RootExitCode"), "Original-job event")
        for key, maximum in (("PhaseSeconds", 245), ("DrainSeconds", 5)):
            v.require(type(event[key]) in (int, float) and math.isfinite(event[key]) and 0 <= event[key] <= maximum, "Job observation exceeds deadline")
        integer(event["Active"], 0 if index == len(events) - 1 else 1, 0 if index == len(events) - 1 else 2**32 - 1, "Original-job active count")
        integer(event["RootExitCode"], 0, 0, "Original root exit code")
        if start is None:
            start = event["PhaseSeconds"]
        v.require(event["PhaseSeconds"] >= previous and abs(event["DrainSeconds"] - (event["PhaseSeconds"] - start)) < 0.000001, "Inconsistent original-job timing")
        previous = event["PhaseSeconds"]
    same(identity["ObservedSourceZoneOrder"], zones, "Recorded zone order")


def utc_stamp(value):
    """Match .NET UTC roundtrip timestamps without losing the seventh digit."""
    v.require(isinstance(value, str), "Stock timestamp required")
    match = re.fullmatch(r"(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,7}))?(Z|[+-]\d\d:\d\d)", value)
    v.require(match is not None, "Stock timestamp invalid")
    parsed = datetime.fromisoformat(value).astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%dT%H:%M:%S") + "." + (match[2] or "").ljust(7, "0") + "Z"


def stock_descriptor(entry, *, supplemental=False):
    integer(entry["Bytes"], 1, 2**63 - 1, "Stock bytes")
    integer(entry["Attributes"], 0, 2**31 - 1, "Stock attributes")
    v.require(not entry["Attributes"] & (16 | 1024) and
              (not entry["Attributes"] & 1 or (not supplemental and entry["Relative"] == "main/fileSysCheck.cfg")), "Redirected/read-only stock metadata")
    v.require(isinstance(entry["SourceId"], str) and re.fullmatch(r"[A-F0-9]{8}:[A-F0-9]{16}", entry["SourceId"]), "Stock source identity invalid")
    v.digest(entry["SHA256"])
    v.require("TargetId" not in entry, "Metadata cannot claim staged target identity")
    result = {"Relative": str(v.safe_path(entry["Relative"])), "Source": str(absolute(entry["Source"])),
              "Mode": "Copy" if entry["Relative"] == "main/fileSysCheck.cfg" else "HardLink",
              "Bytes": entry["Bytes"], "ModifiedUtc": utc_stamp(entry["ModifiedUtc"]), "Attributes": entry["Attributes"],
              "ExpectedSourceId": entry["SourceId"], "ExpectedSHA256": entry["SHA256"]}
    result.update({"StockProfile": "RecipientSupplemental"} if supplemental else {"BaselineMode": entry["Mode"]})
    return result


def stock_budget(baseline, overlay, profile_id=None):
    """Recompute receipt arithmetic only; never opens a stock source."""
    v.require(profile_id is None or profile_id in STOCK_PROFILES, "Unknown named stock budget profile")
    profile = STOCK_PROFILES[profile_id or OVERLAY_PROFILE]
    same([x["Relative"] for x in overlay], ["zone/" + x[0] for x in profile["paks"]], "Named stock budget ordered scope")
    v.require(len(overlay) == len(profile["paks"]) and sum(x["Bytes"] for x in overlay) == profile["bytes"], "Named stock budget count/bytes differ")
    v.require(all(x.get("StockProfileId") == profile_id if profile_id is not None else "StockProfileId" not in x for x in overlay), "Mixed or incomplete stock profile identities")
    unique, names = {}, set()
    for entry in baseline + overlay:
        name = entry["Relative"].casefold()
        v.require(name not in names, "Duplicate stock target")
        names.add(name)
        identity = entry["ExpectedSourceId"]
        if identity in unique:
            previous = unique[identity]
            v.require(previous["Bytes"] == entry["Bytes"] and v.digest(previous["ExpectedSHA256"]) == v.digest(entry["ExpectedSHA256"]), "Aliased stock identity has inconsistent size/hash")
        else:
            unique[identity] = entry
    result = {"BaselineEntries": len(baseline), "SupplementalEntries": len(overlay),
            "SupplementalLogicalBytes": sum(x["Bytes"] for x in overlay), "SupplementalLimitBytes": profile["limit"],
            "SupplementalCopiedBytes": sum(x["Bytes"] for x in overlay if x["Mode"] == "Copy"),
            "UniqueHashReadBytes": sum(x["Bytes"] for x in unique.values()), "UniqueHashReadFiles": len(unique),
            "StockHardLinks": sum(x["Mode"] == "HardLink" for x in baseline + overlay),
            "StockCopiedBytes": sum(x["Bytes"] for x in baseline + overlay if x["Mode"] == "Copy"),
            "ContentVerified": False, "AdditionalResidentBytesMeasured": False}
    if profile_id is not None:
        result.update(SupplementalProfile=profile_id, AdditionalBytesBeyondFourPAKs=profile["additional"])
    return result


def complete_inventory(reader, spec, pins, rows, baseline, root):
    """Read/hash/parse the same bounded metadata bytes; no stock path is opened."""
    v.require(v.digest(spec["RecipientCompleteInventoryReceiptSHA256"]) == INVENTORY_SHA and
              pins.get(path_key(spec["RecipientCompleteInventoryReceipt"])) == INVENTORY_SHA,
              "Fixed independent complete inventory pin required")
    raw = reader.read(spec["RecipientCompleteInventoryReceipt"], INVENTORY_SHA, limit=INVENTORY_LIMIT)
    inventory = v.json_bytes(raw)
    exact_keys(inventory, ("Schema", "CapturedUtc", "Purpose", "StockRoot", "DirectoryScope", "ReviewedManifest",
        "ReviewedManifestSHA256", "RetailPayloadBytesRead", "InventoryElapsedSeconds", "Summary", "MissingReviewedFiles",
        "UnsafeAttributes", "ProposedAllAssetBudget", "Files"), "Complete inventory")
    v.require(inventory["Schema"] == "iw7.recipient-pak-inventory-proposal/1" and
              v.digest(inventory["ReviewedManifestSHA256"]) == REVIEWED_SHA, "Complete inventory schema/manifest differs")
    same_path(inventory["StockRoot"], root, "Complete inventory stock root")
    same_path(inventory["ReviewedManifest"], spec["ReviewedStockManifest"], "Complete inventory manifest")
    utc_stamp(inventory["CapturedUtc"])
    integer(inventory["RetailPayloadBytesRead"], 0, 0, "Inventory retail bytes read")
    integer(inventory["UnsafeAttributes"], 0, 0, "Inventory unsafe attributes")
    same(inventory["MissingReviewedFiles"], [], "Inventory missing reviewed files")
    entries = inventory["Files"]
    v.require(isinstance(entries, list) and len(entries) == 82, "Exact 82-file metadata inventory required")
    assets, names, image_count = {}, set(), 0
    for entry in entries:
        exact_keys(entry, ("Name", "Family", "Bytes", "SourceId", "ModifiedUtc", "Attributes", "ReviewedSHA256", "ContentVerified"), "Inventory file")
        v.require(entry["Family"] in ("assetfile", "imagefile") and isinstance(entry["Name"], str) and
                  re.fullmatch(entry["Family"] + r"[1-9][0-9]*\.pak", entry["Name"]) and
                  entry["Name"] not in names, "Inventory family/name/uniqueness differs")
        names.add(entry["Name"])
        integer(entry["Bytes"], 1, 2**63 - 1, "Inventory file bytes")
        integer(entry["Attributes"], 0, 2**31 - 1, "Inventory file attributes")
        v.require(not entry["Attributes"] & (1 | 16 | 1024) and entry["ContentVerified"] is False,
                  "Inventory is ordinary descriptive metadata only")
        v.require(isinstance(entry["SourceId"], str) and re.fullmatch(r"[A-F0-9]{8}:[A-F0-9]{16}", entry["SourceId"]), "Inventory source identity invalid")
        utc_stamp(entry["ModifiedUtc"])
        v.digest(entry["ReviewedSHA256"])
        if entry["Family"] == "assetfile":
            assets[entry["Name"]] = entry
        else:
            image_count += 1
    v.require(image_count == 49 and set(assets) == {x[0] for x in (BASE_PAK,) + COMPLETE_PAKS} and
              len({x["SourceId"] for x in assets.values()}) == 33 and sum(x["Bytes"] for x in assets.values()) == 4705977508,
              "Complete 33-asset inventory scope/identity/budget differs")
    for name, size, checksum in (BASE_PAK,) + COMPLETE_PAKS:
        entry, row = assets[name], rows[name.casefold()]
        v.require(entry["Bytes"] == size == row["Length"] and row["RelativePath"] == name and
                  v.digest(entry["ReviewedSHA256"]) == checksum == v.digest(row["SHA256"]), "Complete inventory differs from fixed reviewed asset")
    pak1 = [x for x in baseline if x["Relative"] == "zone/assetfile1.pak"]
    v.require(len(pak1) == 1, "Complete profile requires exactly one baseline pak1")
    inventory_match(pak1[0], assets["assetfile1.pak"])
    return assets


def inventory_match(descriptor, entry):
    v.require(descriptor["ExpectedSourceId"] == entry["SourceId"] and descriptor["Bytes"] == entry["Bytes"] and
              descriptor["Attributes"] == entry["Attributes"] and utc_stamp(descriptor["ModifiedUtc"]) == utc_stamp(entry["ModifiedUtc"]) and
              v.digest(descriptor["ExpectedSHA256"]) == v.digest(entry["ReviewedSHA256"]), "Complete profile descriptor differs from independent inventory")


def bind_stock_overlay(reader, spec, pins, plan):
    """Semantic baseline/overlay linkage using bounded JSON receipts only."""
    v.require(v.digest(spec["StockReceiptSHA256"]) == BASELINE_SHA and
              v.digest(spec["ReviewedStockManifestSHA256"]) == REVIEWED_SHA, "Reviewed baseline/manifest pins required")
    receipts = {field: v.json_bytes(reader.read(spec[field], pins[path_key(spec[field])]))
                for field in ("StockReceipt", "StockBindingReceipt", "ReviewedStockManifest", "RecipientStockBindingReceipt")}
    baseline, observation, reviewed, overlay = (receipts[field] for field in
        ("StockReceipt", "StockBindingReceipt", "ReviewedStockManifest", "RecipientStockBindingReceipt"))
    v.require(baseline["Schema"] == "iw7.model-ff-build/1" and baseline["Restored"] is True
              and baseline["StockPreserved"] is True and baseline["RetainedLeaseToken"] is None, "Closed historical baseline required")
    history = baseline["Inputs"]
    v.require(isinstance(history, list) and len(history) == 72 and sum(x["Mode"] == "HardLink" for x in history) == 63
              and sum(x["Mode"] == "Copy" for x in history) == 9, "Historical 72-entry profile differs")
    historical = {str(v.safe_path(x["Relative"])).casefold(): x for x in history}
    v.require(len(historical) == 72, "Duplicate historical stock path")
    root = absolute(spec["StockRoot"])
    v.require(observation["Schema"] == "iw7.ff-stock-observation/1" and
              v.digest(observation["BaselineReceiptSHA256"]) == BASELINE_SHA and
              v.digest(observation["ReviewedStockManifestSHA256"]) == REVIEWED_SHA, "Baseline observation binding differs")
    same_path(observation["StockRoot"], root, "Baseline observation stock root")
    utc_stamp(observation["CapturedUtc"])
    for field in ("BaselineReceipt", "ReviewedStockManifest"):
        if field in observation:
            same_path(observation[field], spec["StockReceipt" if field == "BaselineReceipt" else field], "Baseline observation " + field)
    v.require(not {"Restored", "StockPreserved", "Transaction", "RetainedLeaseToken", "Ready"} & set(observation), "Metadata observation cannot claim restoration/readiness")
    v.require(isinstance(reviewed, list) and 1 <= len(reviewed) <= 4096, "Bounded reviewed stock manifest required")
    rows = {}
    for row in reviewed:
        relative = str(v.safe_path(row["RelativePath"]))
        v.require(relative.casefold() not in rows and row["Operation"] == "NTFSHardLinkImmutableStock", "Duplicate/invalid reviewed stock row")
        integer(row["Length"], 0, 2**63 - 1, "Reviewed stock length")
        v.digest(row["SHA256"])
        rows[relative.casefold()] = row
    observed = observation["Inputs"]
    v.require(isinstance(observed, list) and len(observed) == 72, "Exact baseline observations required")
    base_inputs = []
    for entry in observed:
        relative = str(v.safe_path(entry["Relative"]))
        old = historical[relative.casefold()]
        v.require(relative == old["Relative"] and entry["Bytes"] == old["Bytes"] and entry["Mode"] == old["Mode"], "Observation differs from historical baseline")
        source = absolute(entry["Source"])
        if entry.get("ExternalToolDependency") is True:
            v.require(relative == "tlsdll.dll" and entry["Mode"] == "Copy" and entry["Bytes"] == 113152 and
                      v.digest(entry["SHA256"]) == "6e00dbe90e4ccb60283fad72a769b36542e587019a0da9fa42cb6a0fcf91207a" and
                      not entry.get("ReviewedStockRelative") and not source.is_relative_to(root), "Exact external TLS dependency required")
        else:
            v.require(entry.get("ExternalToolDependency") is None or entry.get("ExternalToolDependency") is False, "Invalid external dependency flag")
            review_relative = relative.split("/")[-1] if re.fullmatch(r"(?:main|zone)/[^/]+\.ff", relative) or relative == "zone/assetfile1.pak" else relative
            row = rows[review_relative.casefold()]
            v.require(entry["ReviewedStockRelative"] == row["RelativePath"] == review_relative and
                      row["Length"] == entry["Bytes"] and v.digest(row["SHA256"]) == v.digest(entry["SHA256"]), "Baseline content descriptor differs from reviewed row")
            same_path(source, root.joinpath(*v.safe_path(review_relative).parts), "Baseline stock source")
        base_inputs.append(stock_descriptor(entry))
    v.require(sum(x["Mode"] == "Copy" for x in base_inputs) == 1 and
              next(x["Bytes"] for x in base_inputs if x["Mode"] == "Copy") == 77, "Exact 77-byte sentinel copy required")

    profile_id = overlay["Profile"]
    v.require(isinstance(profile_id, str) and profile_id in STOCK_PROFILES, "Unknown supplemental stock profile")
    profile = STOCK_PROFILES[profile_id]
    inventory_markers = ("RecipientCompleteInventoryReceipt" in spec, "RecipientCompleteInventoryReceiptSHA256" in spec)
    is_complete = profile_id == COMPLETE_PROFILE
    v.require(all(inventory_markers) if is_complete else not any(inventory_markers), "Complete inventory spec/profile contract differs")
    overlay_keys = ("Schema", "Profile", "ToolSource", "StockRoot", "ReviewedStockManifestSHA256", "CapturedUtc", "ContentVerification", "Inputs")
    exact_keys(overlay, overlay_keys + (("AdditionalDependencyEvidenceSHA256",) if profile["evidence"] else ()) +
               (("CompleteInventoryEvidenceSHA256",) if is_complete else ()), "Recipient stock observation")
    v.require(overlay["Schema"] == profile["schema"] and
              overlay["ToolSource"] == TOOL_SOURCE and v.digest(overlay["ReviewedStockManifestSHA256"]) == REVIEWED_SHA and
              overlay["ContentVerification"] == "DeferredUntilAdmittedRun", "Exact unverified supplemental profile required")
    if profile["evidence"]:
        v.require(v.digest(overlay["AdditionalDependencyEvidenceSHA256"]) == profile["evidence"], "Reviewed fatal dependency evidence pin differs")
    assets = None
    if is_complete:
        v.require(v.digest(overlay["CompleteInventoryEvidenceSHA256"]) == INVENTORY_SHA, "Complete inventory observation pin differs")
        assets = complete_inventory(reader, spec, pins, rows, base_inputs, root)
    # The newer producer also enriches four-PAK /1 plans. Accept exactly both
    # named fields plus every per-input ID, or the historical four-PAK shape.
    named_markers = ("SupplementalProfile" in plan["StockBudget"], "AdditionalBytesBeyondFourPAKs" in plan["StockBudget"],
                     any("StockProfileId" in x for x in plan["StockInputs"]))
    named_mode = any(named_markers)
    v.require(not named_mode or all(named_markers), "Incomplete named stock profile contract")
    v.require(profile_id == OVERLAY_PROFILE or named_mode, "This stock profile requires explicit named contract")
    if named_mode:
        v.require(plan["StockBudget"]["SupplementalProfile"] == profile_id, "Named budget and observation profile differ")
    same_path(overlay["StockRoot"], root, "Supplemental stock root")
    utc_stamp(overlay["CapturedUtc"])
    v.require(isinstance(overlay["Inputs"], list) and len(overlay["Inputs"]) == len(profile["paks"]), "Exact named supplemental PAK count required")
    extra_inputs = []
    for entry, (name, size, checksum) in zip(overlay["Inputs"], profile["paks"]):
        exact_keys(entry, ("Relative", "Source", "Mode", "Bytes", "ModifiedUtc", "Attributes", "SourceId", "SHA256", "ReviewedStockRelative"), "Supplemental PAK")
        v.require(entry["Relative"] == "zone/" + name and entry["Mode"] == "HardLink" and entry["ReviewedStockRelative"] == name, "Supplemental PAK name/order/mode differs")
        integer(entry["Bytes"], size, size, "Supplemental PAK bytes")
        row = rows[name.casefold()]
        v.require(row["RelativePath"] == name and row["Length"] == size and v.digest(row["SHA256"]) == v.digest(entry["SHA256"]) == checksum, "Supplemental PAK reviewed hash/size differs")
        same_path(entry["Source"], root / name, "Supplemental PAK source")
        extra_inputs.append(stock_descriptor(entry, supplemental=True))
        if named_mode:
            extra_inputs[-1]["StockProfileId"] = profile_id
        if is_complete:
            inventory_match(extra_inputs[-1], assets[name])
    same(plan["StockInputs"], base_inputs + extra_inputs, "Baseline plus exact overlay descriptors")
    budget = stock_budget(base_inputs, extra_inputs, profile_id if named_mode else None)
    v.require(budget["SupplementalLogicalBytes"] == profile["bytes"] <= budget["SupplementalLimitBytes"] and
              budget["SupplementalCopiedBytes"] == 0 and budget["StockHardLinks"] == 71 + len(profile["paks"]), "Supplemental stock budget differs")
    same(plan["StockBudget"], budget, "Recomputed stock receipt budget")
    return {"profile": profile_id, "observation_schema": profile["schema"],
            "producer_contract": "named-profile/1" if named_mode else "legacy-four-pak/1",
            "additional_dependency_evidence_sha256": profile["evidence"],
            "complete_inventory_sha256": INVENTORY_SHA if is_complete else None,
            "complete_inventory_metadata_bound": is_complete,
            "baseline_receipt_sha256": BASELINE_SHA, "reviewed_manifest_sha256": REVIEWED_SHA,
            "baseline_observation_sha256": v.digest(spec["StockBindingReceiptSHA256"]),
            "overlay_observation_sha256": v.digest(spec["RecipientStockBindingReceiptSHA256"]),
            "supplemental_input_records": extra_inputs, "budget_from_receipts": budget, "content_remeasured": False}


def bind_run(expectations):
    """Expectations must be supplied independently, never synthesized from state."""
    exact_keys(expectations, ("schema", "run_root", "state_sha256", "plan", "spec_path", "source_pins", "provider_pins", "run_files", "observation"), "Expectations")
    v.require(expectations["schema"] == "iw7.recipient-run-expectations/1", "Unknown expectation schema")
    root = v.no_redirects(absolute(expectations["run_root"]))
    work, reader = root / "work", Reader()
    v.require(root.is_dir() and v.no_redirects(work).is_dir(), "Run/work directories required")
    for field in ("plan", "observation"):
        exact_keys(expectations[field], ("path", "sha256") if field == "plan" else ("path", "sha256", "phase"), field)
    expected_plan = v.json_bytes(reader.read(expectations["plan"]["path"], expectations["plan"]["sha256"]))
    state = v.json_bytes(reader.read(root / "state.local.json", expectations["state_sha256"]))
    v.require(state["Schema"] == "iw7.recipient-closure-run/1", "Unknown Run schema")
    plan = state["Plan"]
    normalized_plan = copy.deepcopy(plan)
    for entry in normalized_plan["StockInputs"]:
        entry.pop("SourceId", None)
        entry.pop("TargetId", None)
    same(normalized_plan, expected_plan, "Independently reviewed plan")
    v.require(plan["Schema"] == "iw7.recipient-closure-plan/1", "Unknown plan schema")
    same_path(plan["RunRoot"], root, "Plan RunRoot")
    for value in (plan["Work"], state["Work"]):
        same_path(value, work, "Run work")
    phases = plan["Phases"]
    v.require(phases in (["references"], ["references", "script"]), "Unsupported phase selection")
    selected = expectations["observation"]["phase"]
    v.require(selected in phases, "Observation phase was not run")
    for key, expected in PROFILE.items():
        integer(plan[key], expected, expected, "Plan " + key)
    for key in ("NativeExecuted", "ClosureComplete", "Ready"):
        v.require(plan[key] is False, "Plan is not a prospective unready plan")
    v.require(state["Status"] == ("ReferencesObservedScriptNotRun" if len(phases) == 1 else "ReferenceAndScriptObservationsVerified"), "Run did not finish requested observations")
    for key in ("Restored", "StockPreserved", "NativeExecuted", "ReferencesVerified"):
        v.require(state[key] is True, "Missing successful Run record: " + key)
    v.require(state["ScriptBytesVerified"] is (len(phases) == 2), "Script evidence contradicts phase selection")
    for key in ("ClosureComplete", "Ready", "RuntimeVerified"):
        v.require(state[key] is False, "Unsupported Run readiness claim")
    v.require(state["RestorationStatus"] == "Confirmed" and state["CleanupError"] is None
              and state["RetainedLeaseToken"] is None and state.get("Failure") is None and "ClosureAfterStop" not in state, "Run cleanup/lease/failure unresolved")
    for key in ("FinalObservedBytes", "MaxObservedBytes"):
        integer(state[key], 0, PROFILE["OutputStopBytes"], key)
    v.require(state["FinalObservedBytes"] <= state["MaxObservedBytes"], "Invalid declared output accounting")

    # External reads are limited to the independently supplied pin allowlist.
    pins = pin_map(expectations["source_pins"])
    same(pin_map(plan["SourceHashes"]), pins, "Independent source pins")
    providers = expectations["provider_pins"]
    exact_keys(providers, PROVIDERS, "Independent provider pins")
    same(plan["ProviderBindings"], providers, "Provider bindings")
    python = absolute(plan["PythonExe"])
    v.require(pins.get(path_key(python)) == v.digest(plan["PythonSHA256"]), "Python independent pin absent")
    adapter = absolute(plan["Adapter"])
    v.require(adapter.name == "recipient_phase.py", "Unsupported phase adapter")
    for name in PRODUCERS:
        v.require(path_key(adapter.parent / name) in pins, "Producer independent pin absent: " + name)
    spec_path = absolute(expectations["spec_path"])
    v.require(path_key(spec_path) in pins, "Original spec independent pin absent")
    original_spec = v.json_bytes(reader.read(spec_path, pins[path_key(spec_path)]))
    same_path(original_spec["RunRoot"], root, "Original spec RunRoot")
    same_path(original_spec["PythonExe"], python, "Original spec Python")
    overlay_markers = ("RecipientStockBindingReceipt" in original_spec, "RecipientStockBindingReceiptSHA256" in original_spec,
                       "StockBudget" in plan, path_key(adapter.parent / "Recipient.Stock.ps1") in pins)
    overlay_mode = any(overlay_markers)
    inventory_markers = ("RecipientCompleteInventoryReceipt" in original_spec, "RecipientCompleteInventoryReceiptSHA256" in original_spec)
    inventory_mode = any(inventory_markers)
    if inventory_mode:
        v.require(overlay_mode and all(inventory_markers), "Incomplete complete inventory source roles")
    if overlay_mode:
        v.require(all(overlay_markers), "Incomplete explicit supplemental stock contract")
        v.require(plan.get("FatalTextDiagnostic") is False and state.get("DiagnosticOnly") is False, "Diagnostic-only run cannot bind recipient observations")
        for key, value in DIAGNOSTIC_LIMITS.items():
            integer(plan[key], value, value, key)
    else:
        v.require(not any("StockProfile" in x or "StockProfileId" in x or x["Relative"] in {"zone/" + p[0] for p in COMPLETE_PAKS}
                          for x in normalized_plan["StockInputs"]), "Supplemental stock requires explicit profile")
    stock_receipts = {}
    receipt_roles = (("StockReceipt", "StockBindingReceipt", "ReviewedStockManifest", "PythonExe") +
                     (("RecipientStockBindingReceipt",) if overlay_mode else ()) +
                     (("RecipientCompleteInventoryReceipt",) if inventory_mode else ()))
    for field in receipt_roles:
        key = path_key(original_spec[field])
        v.require(pins.get(key) == v.digest(original_spec[field + "SHA256"]), "Original spec input pin absent: " + field)
        if field != "PythonExe":
            stock_receipts[field] = key
    candidate_root = absolute(original_spec["CandidateRoot"])
    request_root = absolute(original_spec["RequestRoot"])
    candidate_records = [candidate_root / name for name in ("build-artifact.local.json", "preparation.local.json", "result.local.json")]
    allowed_sources = {path_key(adapter.parent / name) for name in PRODUCERS}
    if overlay_mode:
        allowed_sources.update(path_key(adapter.parent / name) for name in OVERLAY_PRODUCERS)
    allowed_sources.update(path_key(path) for path in (*candidate_records, python, spec_path))
    allowed_sources.update(stock_receipts.values())
    allowed_sources.update(path_key(request_root / name) for name in ("recipient-material-requests.csv", "recipient-script-requests.txt"))
    optional_light = path_key(adapter.parent / "Recipient.Light.ps1")
    if optional_light in pins:
        allowed_sources.add(optional_light)
    same(sorted(pins), sorted(allowed_sources), "Exact source pin roles")
    for path, checksum in pins.items():
        limit = 64 * 1024**2 if path == path_key(python) else v.LIMIT
        if inventory_mode and path == path_key(original_spec["RecipientCompleteInventoryReceipt"]):
            limit = INVENTORY_LIMIT
        reader.read(path, checksum, limit=limit, retain=False)
    for name, binding in providers.items():
        exact_keys(binding, ("Path", "SHA256"), "Provider")
        reader.read(binding["Path"], binding["SHA256"], retain=False)
    declared_providers = v.json_bytes(reader.read(adapter.parent / "provider-pins.json"))
    same({k: v.digest(x) for k, x in declared_providers.items()}, {k: v.digest(x["SHA256"]) for k, x in providers.items()}, "Producer provider manifest")
    stock_binding = bind_stock_overlay(reader, original_spec, pins, normalized_plan) if overlay_mode else None
    candidate = plan["Candidate"]
    same_path(candidate["Path"], candidate_root / "bin/zonetool-community.exe", "Candidate source")
    v.require(v.digest(candidate["ArtifactSHA256"]) == v.digest(original_spec["CandidateArtifactSHA256"])
              == pins[path_key(candidate_records[0])], "Candidate artifact independent pin differs")
    v.require(v.digest(candidate["SHA256"]) == v.EXE_SHA, "Recipient tool must be reviewed E7")
    tool = reader.read(candidate["Path"], candidate["SHA256"], limit=64 * 1024**2, retain=False)
    requests = plan["Requests"]
    same([item["Relative"] for item in requests], list(REQUESTS), "Request set/order")
    expected_requests = ("".join(kind + "," + name + "\n" for kind, name in v.REFERENCES), v.MODULE + "\n")
    for request, expected, source_name, hash_field in zip(requests, expected_requests,
            ("recipient-material-requests.csv", "recipient-script-requests.txt"), ("MaterialRequestSHA256", "ScriptRequestSHA256")):
        exact_keys(request, ("Relative", "Source", "SHA256"), "Request")
        same_path(request["Source"], request_root / source_name, "Request source")
        v.require(v.digest(request["SHA256"]) == v.digest(original_spec[hash_field]), "Original spec request hash differs")
        v.require(pins.get(path_key(request["Source"])) == v.digest(request["SHA256"]), "Independent request pin absent")
        raw = reader.read(request["Source"], request["SHA256"], limit=4096)
        v.require(raw.decode("utf-8-sig").replace("\r\n", "\n") == expected, "Exact native request differs")

    stock = normalized_plan["StockInputs"]
    v.require(isinstance(stock, list) and 1 <= len(stock) <= 128, "Bounded stock descriptors required")
    zones = source_zones(stock)
    same(plan["SourceZoneOrder"], zones, "Stock descriptor zone order")
    inputs = state["Inputs"]
    v.require(isinstance(inputs, list) and len(inputs) == len(stock) + 3, "Staged input set differs")
    staged = [("zonetool.exe", candidate["Path"], tool["bytes"])] + [(x["Relative"], x["Source"], reader.records[path_key(x["Source"])][0]["bytes"]) for x in requests]
    names = []
    for index, item in enumerate(inputs):
        name = str(v.safe_path(item["Relative"]))
        v.require(name.casefold() not in {x.casefold() for x in names}, "Duplicate staged input")
        names.append(name)
        if index < len(stock):
            expected = stock[index]
            same({key: item[key] for key in expected}, expected, "Stock descriptor")
            v.require(set(item) == set(expected) | {"SourceId", "TargetId"}, "Unexpected staged stock fields")
            v.require(item["SourceId"] == item["ExpectedSourceId"], "Recorded stock identity changed")
            for key in ("SourceId", "TargetId"):
                if key in plan["StockInputs"][index]:
                    same(plan["StockInputs"][index][key], item[key], "Shared plan/input identity")
        else:
            relative, source, size = staged[index - len(stock)]
            v.require(name == relative and item["Bytes"] == size and item["Mode"] == "HardLink", "Tool/request staging differs")
            same_path(item["Source"], source, "Staged source")
        for key in ("SourceId", "TargetId"):
            v.require(isinstance(item[key], str) and re.fullmatch(r"[A-F0-9]{8}:[A-F0-9]{16}", item[key]), "Invalid recorded NTFS identity")
        v.require(item["Mode"] in ("HardLink", "Copy") and (item["SourceId"] == item["TargetId"]) is (item["Mode"] == "HardLink"), "Recorded staging identity mismatch")
        reader.absent_path(work.joinpath(*v.safe_path(name).parts))

    run_pins = expectations["run_files"]
    v.require(isinstance(run_pins, dict), "Independent retained file pins required")
    required = {"backup/recovery.local.json"}
    for phase in phases:
        required.update((phase + ".json", phase + "/phase.json", phase + "/stdout.log", phase + "/stderr.log"))
        required.add("work/enemy-catalog/sdk_beacon_recipient_a.csv" if phase == "references" else "work/dump/" + v.PACK + "/scriptfile-manifest.csv")
        if phase == "script":
            required.add("work/" + v.SCRIPT_PATH)
    same(sorted(run_pins), sorted(required), "Exact retained file pin set")
    raw_files = {name: reader.read(root.joinpath(*v.safe_path(name).parts), checksum) for name, checksum in run_pins.items()}
    transaction = v.json_bytes(raw_files["backup/recovery.local.json"])
    same(state["Transaction"], transaction, "Restoration transaction")
    v.require(transaction["Schema"] == "iw7.base-transaction/1" and transaction["Restored"] is True, "Restored transaction required")
    same_path(transaction["GameRoot"], work, "Transaction work")
    same_path(transaction["BackupRoot"], root / "backup", "Transaction backup")
    same(transaction["Files"], [{"Path": name, "Existed": False, "SHA256": None} for name in names], "Fresh Run restoration entries")
    for key in ("ProfileDirectories", "DirectoryBefore", "ProfileBefore", "ProtectedFiles"):
        same(transaction[key], [], "Fresh Run " + key)
    v.require(transaction["ProfileDirectory"] == "unused", "Unexpected profile transaction")

    same([entry["Phase"] for entry in state["Phases"]], phases, "Run phase order")
    analyses, actions = {}, {}
    for phase, identity in zip(phases, state["Phases"]):
        closed_phase(identity, phase, python, zones)
        spec = v.json_bytes(raw_files[phase + ".json"])
        exact_keys(spec, ("schema", "phase", "exe", "sha256", "cwd", "logs", "timeout"), "Phase spec")
        v.require(spec["schema"] == "iw7.recipient-phase/1" and spec["phase"] == phase and v.digest(spec["sha256"]) == v.EXE_SHA, "Phase spec differs")
        integer(spec["timeout"], 240, 240, "Phase deadline")
        for key, target in (("exe", work / "zonetool.exe"), ("cwd", work), ("logs", root / phase)):
            same_path(spec[key], target, "Phase spec " + key)
        receipt = v.json_bytes(raw_files[phase + "/phase.json"])
        v.require(receipt["phase"] == phase, "Receipt belongs to another phase")
        v.require(receipt["pid"] != identity["PID"], "Native receipt PID aliases original Python root")
        same(identity["Result"], receipt, "Nested phase receipt")
        stdout, stderr = raw_files[phase + "/stdout.log"], raw_files[phase + "/stderr.log"]
        zone_log(stdout, zones)
        v.require(not ERROR.search(stderr.decode("utf-8-sig")), "Native stderr reports errors")
        if "capture" in receipt:
            same(receipt["capture"]["stdout_bytes_at_receipt"], len(stdout), "Captured stdout count")
            same(receipt["capture"]["stderr_bytes_at_receipt"], len(stderr), "Captured stderr count")
        analyses[phase] = v.verify_phase(work, root / phase / "phase.json")
        for item in analyses[phase]["files"]:
            v.require(v.digest(run_pins["work/" + item["path"]]) == item["sha256"], "Analysis output differs from pinned bytes")
        v.require(analyses[phase]["receipt_sha256"] == v.digest(run_pins[phase + "/phase.json"]), "Analysis receipt changed")
        actions[phase] = [str(work / "zonetool.exe"), "-headless", "-unbuffered-io", "-strict-content-sources"] + (
            ["-enemy-reference-check", "cp_zmb", REQUESTS[0], "sdk_beacon_recipient_a"] if phase == "references" else
            ["-enemy-script-dump", "cp_zmb", REQUESTS[1], v.PACK])
    observation = v.json_bytes(reader.read(expectations["observation"]["path"], expectations["observation"]["sha256"]))
    same(observation, analyses[selected], "External observation versus remeasurement")
    reader.finish()
    return {"schema": "iw7.recipient-run-bound/1", "run_root": str(root), "phase": selected,
            "state_sha256": v.digest(expectations["state_sha256"]), "plan_sha256": v.digest(expectations["plan"]["sha256"]),
            "external_observation_sha256": v.digest(expectations["observation"]["sha256"]),
            "closed_run_record_bound": True, "observation_bytes_bound": True, "temporary_inputs_absent_now": True,
            "native_execution_authenticated": False, "stock_content_remeasured": False,
            "stock_receipt_files_rehashed": stock_receipts,
            "stock_profile_binding": stock_binding,
            "actions_reconstructed_from_pinned_contract": actions, "argv_observed": False,
            "source_zone_order": zones, "phases": analyses,
            "files": [item[0] for item in reader.records.values()],
            "imports_analyzed": False, "dependency_graph_complete": False, "closure_complete": False,
            "package_ready": False, "runtime_ready": False, "owner_accepted": False,
            "scope": "Consistent independently pinned local records and retained bytes only. Unsigned receipts do not authenticate execution, job ownership, historical staging or stock integrity."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expectations", required=True)
    args = parser.parse_args()
    try:
        raw = Reader().read(args.expectations)
        print(v.canonical(bind_run(v.json_bytes(raw))))
        return 0
    except (ValueError, OSError, KeyError, TypeError, OverflowError) as error:
        print("Recipient Run binding refused: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
