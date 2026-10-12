"""Read-only linkage of retained recipient bytes to an independently pinned Run.

This binds consistent local records, not authenticated execution or retail stock.
No subprocess, engine, network, file writer, package gate or GSC disassembler.
"""
import argparse
import copy
from datetime import datetime
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
        self.absent = []
        self.total = 0

    def read(self, path, expected=None, limit=v.LIMIT, retain=True):
        path = v.no_redirects(absolute(str(path)))
        key = path_key(path)
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
            self.read(path, record["sha256"], limit=64 * 1024**2, retain=False)
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
    stock_receipts = {}
    for field in ("StockReceipt", "StockBindingReceipt", "ReviewedStockManifest", "PythonExe"):
        key = path_key(original_spec[field])
        v.require(pins.get(key) == v.digest(original_spec[field + "SHA256"]), "Original spec input pin absent: " + field)
        if field != "PythonExe":
            stock_receipts[field] = key
    candidate_root = absolute(original_spec["CandidateRoot"])
    request_root = absolute(original_spec["RequestRoot"])
    candidate_records = [candidate_root / name for name in ("build-artifact.local.json", "preparation.local.json", "result.local.json")]
    allowed_sources = {path_key(adapter.parent / name) for name in PRODUCERS}
    allowed_sources.update(path_key(path) for path in (*candidate_records, python, spec_path))
    allowed_sources.update(stock_receipts.values())
    allowed_sources.update(path_key(request_root / name) for name in ("recipient-material-requests.csv", "recipient-script-requests.txt"))
    optional_light = path_key(adapter.parent / "Recipient.Light.ps1")
    if optional_light in pins:
        allowed_sources.add(optional_light)
    same(sorted(pins), sorted(allowed_sources), "Exact source pin roles")
    for path, checksum in pins.items():
        reader.read(path, checksum, limit=64 * 1024**2 if path == path_key(python) else v.LIMIT, retain=False)
    for name, binding in providers.items():
        exact_keys(binding, ("Path", "SHA256"), "Provider")
        reader.read(binding["Path"], binding["SHA256"], retain=False)
    declared_providers = v.json_bytes(reader.read(adapter.parent / "provider-pins.json"))
    same({k: v.digest(x) for k, x in declared_providers.items()}, {k: v.digest(x["SHA256"]) for k, x in providers.items()}, "Producer provider manifest")
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
