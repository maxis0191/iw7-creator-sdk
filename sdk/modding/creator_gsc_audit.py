"""Read-only bridge from retained GSC audit artifacts to Creator observations.

This consumer links historical completion records and remeasures witness bytes.
It never re-executes native code or grants semantic/finalization qualification.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import types
from datetime import datetime

WRAPPER_SHA256 = "42dd0dcb01c014cfbfbabb18d404d4c6ccd1b6d04ed27a5b16e63dde54e72d07"
ROLES = {"compilation", "plan", "build", "supervision", "input", "consumption", "assembly"}
V2_SOURCE_REVISION = "eabe74ab65d8ce2a943b54d24b15a60749a0cf2a"
V2_TOOL_SOURCE = "e762caa7429679946ea5804a0fe3b678d1ab97db5ed3ff063d028327f554a9cf"
V3_SOURCE_REVISION = "03d3956d648b7aa4637fe1007f9d69ea463631e9"
V3_TOOL_SOURCE = "23b4de72afa23b1cefc6b03172a18ac945b60e0ab530ea4c40e0493ea34ae350"
REFERENCE_SOURCES = {"reference_reader": ("audit/references.py", "fdb52f27225c61b563a09cd710cfeca769a9d01a8c971b882edeb277efe98a7c"),
    "reference_profile": ("audit/reference-profile.json", "e87230812b01059ece4327d9d465b8b20e5e1162d3cd698492aed70405bbf360"),
    "reference_tests": ("audit/test_reference_native.py", "ea8a9ee474cc5f8425004620aa83b59d1de97f1ff45fe6406638a2a62e6a7141")}
REFERENCE_FILES = {"original_consumption": "witness-original/consumption.json", "reference_pins": "reference-pins.json",
    "reference_controls": "references/controls.json", "variant_native": "references/variant-native.json",
    "variant_bound": "references/variant-bound.json", "original_native": "references/original-native.json",
    "original_bound": "references/original-bound.json"}
REFERENCE_ROLES = set(REFERENCE_FILES) | {"original_input"}
REFERENCE_INPUTS = {"variant": "db486793b92e7e3c0a30c70b565fb432a4940e172a3f97da7e9db377f0e46d42",
                    "original": "31b55a5d58a90d6b980a91543c907d26b91a4f6767d5350e8a35ae0e19fa2cef"}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "Lowercase independent audit SHA-256 required")
    return value


def same(a, b, label):
    require(json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False), label + " differs")


def same_path(a, b, label):
    for value in (a, str(b)):
        require(isinstance(value, str) and Path(value).is_absolute() and ".." not in Path(value).parts, "Absolute audit path required")
    require(os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b)), label + " path differs")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, label + " must be a bounded integer")


def utc(value):
    require(isinstance(value, str) and re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6,7}(?:Z|\+00:00)", value), "Complete audit UTC timestamp required")
    return datetime.fromisoformat(value)


def link_completion(plan, build, supervision, records, run, pins):
    """Link the pinned /2 completion report; do not repeat the guarded validator."""
    if build["schema"] == "iw7.gsc-audit-build-run/1":
        return False
    refs = build["schema"] == "iw7.gsc-audit-build-run/3"
    require(build["schema"] in ("iw7.gsc-audit-build-run/2", "iw7.gsc-audit-build-run/3") and
            pins["source_revision"] == (V3_SOURCE_REVISION if refs else V2_SOURCE_REVISION) and
            plan["tool_source_sha256"] == (V3_TOOL_SOURCE if refs else V2_TOOL_SOURCE) and
            plan["residual_closure_policy"] == "original-job-pinned-vctip/1",
            "Unreviewed completion producer or policy")
    require(supervision["Success"] is True and not supervision.get("Failure"), "Global audit supervision failed")
    require(build["plan_sha256"] == supervision["PlanSHA256"] == records["plan"]["sha256"], "Completion plan digest differs")
    require(isinstance(build["run_id"], str) and re.fullmatch(r"[0-9a-f]{32}", build["run_id"]) and
            build["run_id"] == supervision["RunID"], "Completion run nonce differs")
    integer(build["root_pid"], 1, 2**32 - 1, "Completion root PID")
    integer(build["lease_owner_pid"], 1, 2**32 - 1, "Completion lease owner PID")
    require(build["root_pid"] == supervision["RootPID"], "Completion root identity differs")
    require(utc(supervision["StartedUtc"]) <= utc(supervision["RootCreatedUtc"]) <= utc(build["started_utc"]) <=
            utc(build["finished_utc"]) <= utc(supervision["FinishedUtc"]), "Completion time ordering differs")
    require(supervision["OriginalJobSourceSHA256"] == plan["job_source_sha256"] and
            supervision["MemberObserverSHA256"] == plan["members_source_sha256"], "Completion provider pins differ")
    for field, expected in (("DeadlineSeconds", 3600), ("DrainDeadlineMilliseconds", 2000),
                            ("StopThresholdBytes", 1800 * 1024**2), ("OutputLimitBytes", 2 * 1024**3)):
        integer(supervision[field], expected, expected, field)
    for field in ("PeakObservedOutputBytes",):
        integer(supervision[field], 0, supervision["StopThresholdBytes"] - 1, field)
    integer(build["peak_observed_output_bytes"], 0, supervision["StopThresholdBytes"] - 1, "Build peak output")
    for field in ("output_limit_bytes", "output_stop_threshold_bytes"):
        require(plan[field] == supervision["OutputLimitBytes" if field == "output_limit_bytes" else "StopThresholdBytes"], "Plan output guard differs")
    q, completion = supervision["QualifiedClosure"], supervision["CompletionEvidence"]
    require(all(q[key] is True for key in ("CompletionVerified", "ClosureVerified", "AcceptanceGranted")) and
            q["Error"] is None and q["ReceiptSHA256"] == records["build"]["sha256"], "Qualified closure receipt binding differs")
    require(completion["Verified"] is True and completion["RunID"] == build["run_id"] and
            completion["ToolSHA256"] == pins["tool_sha256"] and completion["SourceSHA256"] == pins["source_sha256"], "Completion evidence pins differ")
    require(type(q["Residual"]) is bool and q["Mode"] == ("OriginalJobPinnedResidual" if q["Residual"] else "OriginalJobNaturalClosure") and
            q["StopRequested"] is q["Residual"], "Completion closure mode differs")
    if q["Residual"]:
        require(supervision["StopOriginalJobRequested"] is True and q["First"] is not None and q["Final"] is not None and
                q["Identity"]["IdentityMatches"] is True, "Residual closure capture records absent")
    else:
        require(q["Identity"] is None and q["First"] is None and q["Final"] is None and
                not supervision.get("StopOriginalJobRequested", False), "Natural closure cannot contain residual Stop evidence")
    first_exit = supervision["RootExitObservedMs"]
    integer(first_exit, 0, 3600000 - 1, "First root exit time")
    previous = first_exit
    for sample in (q["CloseObservation"], supervision["LastObservation"]):
        for field in ("ElapsedMs", "CompletedMs"):
            integer(sample[field], previous, min(first_exit + 1999, 3599999), "Closure " + field)
        require(sample["CompletedMs"] >= sample["ElapsedMs"] and sample["RootExited"] is True, "Closure sample ordering differs")
        integer(sample["RootExitCode"], 0, 0, "Closure root exit")
        integer(sample["Active"], 0, 0, "Closure active members")
        previous = sample["CompletedMs"]
    integer(supervision["ObservationCheckedMs"], previous, min(first_exit + 1999, 3599999), "Final checked closure time")
    # Bind recorded completion artifacts to files that this consumer actually
    # read. Other artifacts remain historical declarations, never fresh hashes.
    artifacts = build["completion_artifacts"]
    require(isinstance(artifacts, list), "Completion artifact list required")
    roles = [item["role"] for item in artifacts]
    steps = build["steps"]
    expected_steps = ["cmake-version", "configure", "build", "reader-tests", "native-negative-tests", "witness-variant", "witness-original"]
    if refs:
        expected_steps.append("native-reference-tests")
        require(completion["ReferenceContractVerified"] is True, "Reference contract completion was not verified")
    if steps and steps[0]["name"] == "zlib-clone":
        expected_steps = ["zlib-clone", "zlib-checkout"] + expected_steps
    same([s["name"] for s in steps], expected_steps, "Ordered completion steps")
    expected_roles = {"source-manifest", "tool", "wrapper", "compiler-config-0", "input-variant", "input-original",
                      "witness-variant", "witness-original", "assembly-variant", "assembly-original"} | {"result-" + name for name in expected_steps}
    if refs:
        expected_roles |= {key.replace("_", "-") for key in REFERENCE_SOURCES} | {"reference-pins", "reference-controls",
            "reference-variant-native", "reference-variant-bound", "reference-original-native", "reference-original-bound"}
    require(len(roles) == len(set(roles)) and set(roles) == expected_roles, "Completion artifact roles differ")
    for item in artifacts:
        require(set(item) == {"role", "path", "bytes", "sha256"}, "Completion artifact fields differ")
        integer(item["bytes"], 1, 64 * 1024**2, "Completion artifact bytes")
        digest(item["sha256"])
        same_path(item["path"], item["path"], "Completion artifact")
    by_role = {item["role"]: item for item in artifacts}
    for role, record_role in (("input-variant", "input"), ("witness-variant", "consumption"), ("assembly-variant", "assembly")):
        item, record = by_role[role], records[record_role]
        same_path(item["path"], record["path"], "Completion " + role)
        require(item["bytes"] == record["bytes"] and item["sha256"] == record["sha256"], "Completion artifact bytes differ: " + role)
    if refs:
        links = {"input-original": "original_input", "witness-original": "original_consumption",
                 "reference-pins": "reference_pins", "reference-controls": "reference_controls"}
        links.update({"reference-" + role.replace("_", "-"): role for role in ("variant_native", "variant_bound", "original_native", "original_bound")})
        for role, record_role in links.items():
            item, record = by_role[role], records[record_role]
            same_path(item["path"], record["path"], "Completion " + role)
            require(item["bytes"] == record["bytes"] and item["sha256"] == record["sha256"], "Reference completion artifact differs: " + role)
    same_path(by_role["tool"]["path"], run / "native/Release/iw7-gsc-audit.exe", "Recorded native tool")
    require(by_role["tool"]["sha256"] == pins["tool_sha256"] and by_role["wrapper"]["sha256"] == WRAPPER_SHA256, "Completion tool/wrapper pins differ")
    same_path(by_role["wrapper"]["path"], plan["wrapper"], "Recorded wrapper")
    for step in steps:
        integer(step["exit_code"], 0, 0, "Native step exit")
        integer(step["wrapper_exit_code"], 0, 0, "Wrapper step exit")
        require(step["failure"] is None and step["storage_limit_exceeded"] is False, "Completion step failed")
    return True


def reference_qualification(evidence, raw, parsed, plan, build, audit, selector, packager):
    """Re-run the pinned pure decoder, never a native-shaped summary alone."""
    config = evidence["references"]
    require(isinstance(config, dict) and set(config) == {"source_root", "pins"}, "Reference reader configuration differs")
    root = packager.no_redirects(config["source_root"])
    same_path(config["source_root"], root, "Reference source root")
    same_path(plan["tool_root"], root, "Reference plan source root")
    pins = config["pins"]
    same(pins, {"decoder": evidence["pins"], "profile_sha256": REFERENCE_SOURCES["reference_profile"][1],
                "reference_validator_sha256": REFERENCE_SOURCES["reference_reader"][1],
                "consumption_validator_sha256": WRAPPER_SHA256}, "Independent reference pins")
    same(parsed["reference_pins"], pins, "Retained reference pins")
    same(build["reference_pins"], pins, "Build reference pins")
    sources = {}
    by_role = {item["role"]: item for item in build["completion_artifacts"]}
    for key, (relative, expected) in REFERENCE_SOURCES.items():
        path = root / relative
        content = selector.snapshot(path, packager, 1024 * 1024)
        require(sha(content) == expected == plan[key + "_sha256"], "Reviewed reference source changed: " + key)
        same_path(plan[key], path, "Reference source " + key)
        artifact = by_role[key.replace("_", "-")]
        same_path(artifact["path"], path, "Reference source artifact")
        require(artifact["sha256"] == expected and artifact["bytes"] == len(content), "Reference source artifact differs")
        sources[path] = content
    profile = selector.json_snapshot(sources[root / REFERENCE_SOURCES["reference_profile"][0]])
    require(len(profile["table_files"]) == 8, "Eight reviewed reference tables required")
    for table in profile["table_files"]:
        path = root / table["path"]
        require(path.is_relative_to(root), "Reference table escapes source root")
        content = selector.snapshot(path, packager, 4 * 1024 * 1024)
        require(sha(content) == table["sha256"], "Reference table changed")
        sources[path] = content
    controls = {"schema": "iw7.gsc-reference-controls/1", "pins": pins, "opcode_cases": 153, "unsupported_refusals": 2,
        "unresolved_controls": 4, "native_invocations": 159, "beacon_roles": ["variant", "original"],
        "tests_run": 3, "failures": 0, "errors": 0, "skipped": 0, "successful": True}
    same(parsed["reference_controls"], controls, "Exact native reference controls")
    command = [plan["python"], "-B", plan["reference_tests"], "--tool", str(Path(plan["output"]) / "native/Release/iw7-gsc-audit.exe"),
        "--pins", str(Path(plan["output"]) / "reference-pins.json"), "--source-root", plan["tool_root"],
        "--consumption-validator", plan["wrapper"], "--variant", plan["inputs"][0]["path"], "--original", plan["inputs"][1]["path"],
        "--output", str(Path(plan["output"]) / "references")]
    same(next(s for s in build["steps"] if s["name"] == "native-reference-tests")["command"], command, "Recorded reference control action")
    reader_path = root / REFERENCE_SOURCES["reference_reader"][0]
    reader = types.ModuleType("creator_reference_reader")
    reader.__file__ = str(reader_path)
    # Execute only the exact reviewed snapshot, not a second mutable path open.
    exec(compile(sources[reader_path], str(reader_path), "exec"), reader.__dict__)
    results = {}
    for role, input_role, witness_role in (("variant", "input", "consumption"), ("original", "original_input", "original_consumption")):
        require(sha(raw[input_role]) == REFERENCE_INPUTS[role], "Reviewed reference control input changed: " + role)
        native = parsed[role + "_native"]
        witness = parsed[witness_role]
        same(witness["pins"], evidence["pins"], "Reference consumption pins")
        require(witness["schema"] == "iw7.gsc-consumption-bound/1" and witness["complete_consumption_verified"] is True and
                witness["tool_rehashed_after_execution"] is True and witness["input_transport"] == "same_bytes_via_stdin" and
                all(witness[key] is False for key in ("external_gsc_dependency_absence_verified", "asset_closure_complete", "runtime_ready", "owner_accepted")),
                "Reference companion witness differs")
        same(native["consumption"], witness["native"], "Same-Run reference and consumption witness")
        result = reader.validate(raw[input_role], native, pins, root, audit)
        same(result, parsed[role + "_bound"], "Recomputed bound reference report")
        results[role] = result
    require(results["variant"]["instruction_count"] == 570 and results["variant"]["encoded_external_script_reference_absence"] is True and
            results["variant"]["blockers"] == [], "Exact variant encoded reference control failed")
    original = results["original"]
    require(original["instruction_count"] == 560 and original["encoded_external_script_reference_absence"] is False,
            "Original negative reference control failed")
    same([(x["bytecode_offset"], x["stack_offset"], x["detail"]["target"]) for x in original["blockers"]],
         [(212, 318, "flag_exist"), (226, 345, "flag")], "Original utility reference blockers")
    for path, content in sources.items():
        require(selector.snapshot(path, packager, 4 * 1024 * 1024) == content, "Reference source changed during inspection")
    return results["variant"], {str(path): {"path": str(path), "bytes": len(content), "sha256": sha(content)} for path, content in sources.items()}


def inspect(project, tools_root, evidence, packager):
    """Consume independently pinned existing files; no audit_bytes/native call."""
    selector = module(Path(tools_root) / "sdk/modding/creator_self_contained.py", "creator_audit_selector")
    _, selected = selector.select(project, tools_root, packager)
    refs = isinstance(evidence, dict) and evidence.get("schema") == "iw7.creator-gsc-audit-input/2"
    require(isinstance(evidence, dict) and set(evidence) == {"schema", "run_root", "source_sha256", "pins", "files"} | ({"references"} if refs else set()), "Unexpected Creator audit input fields")
    require(evidence["schema"] in ("iw7.creator-gsc-audit-input/1", "iw7.creator-gsc-audit-input/2") and evidence["source_sha256"] == selected["source"]["sha256"], "Selected source audit binding differs")
    files = evidence["files"]
    require(isinstance(files, dict) and set(files) == ROLES | (REFERENCE_ROLES if refs else set()), "Exact audit artifact roles required")
    run = packager.no_redirects(evidence["run_root"])
    same_path(evidence["run_root"], run, "Run root")
    records, raw, total = {}, {}, 0
    for role, pin in files.items():
        require(isinstance(pin, dict) and set(pin) == {"path", "sha256"}, "Audit artifact pin fields differ")
        same_path(pin["path"], pin["path"], "Explicit artifact")
        content = selector.snapshot(Path(pin["path"]), packager, 2 * 1024**2)
        total += len(content)
        require(total <= 16 * 1024**2, "Audit artifact group exceeds bound")
        require(sha(content) == digest(pin["sha256"]), "Independent audit artifact hash differs: " + role)
        raw[role] = content
        records[role] = {"path": pin["path"], "bytes": len(content), "sha256": sha(content)}
    for role, relative in (("build", "build-receipt.json"), ("supervision", "supervision.json"),
                           ("consumption", "witness-variant/consumption.json"), ("assembly", "witness-variant/disassembly.gscasm")):
        same_path(files[role]["path"], run / relative, role)
    if refs:
        for role, relative in REFERENCE_FILES.items():
            same_path(files[role]["path"], run / relative, role)
    parsed = {role: selector.json_snapshot(raw[role]) for role in files.keys() - {"input", "assembly", "original_input"}}
    compile_record, plan, build, supervision, bound = (parsed[role] for role in ("compilation", "plan", "build", "supervision", "consumption"))
    require(compile_record["schema"] == "iw7.beacon-self-contained-offline/2" and
            compile_record["source_sha256"] == selected["source"]["sha256"] and
            type(compile_record["source_bytes"]) is int and compile_record["source_bytes"] == selected["source"]["bytes"], "Historical compilation/source record differs")
    require(compile_record["binary"]["sha256"] == sha(raw["input"]) and
            type(compile_record["binary"]["bytes"]) is int and compile_record["binary"]["bytes"] == len(raw["input"]), "Compiled container differs from source record")
    digest(compile_record["compiler_sha256"])
    same(compile_record["phases"], [{"name": name, "exit_code": 0} for name in ("parse", "comp", "disasm")], "Historical compilation phases")
    require(compile_record["assembly"]["sha256"] == sha(raw["assembly"]) and type(compile_record["assembly"]["bytes"]) is int and
            compile_record["assembly"]["bytes"] == len(raw["assembly"]), "Historical assembly binding differs")
    require(compile_record["external_gsc_dependency_absence_verified"] is False and
            compile_record["asset_closure_complete"] is False and compile_record["runtime_ready"] is False and
            compile_record["owner_accepted"] is False, "Historical summary cannot qualify dependencies/runtime")
    require(plan["schema"] == ("iw7.gsc-audit-build-plan/2" if refs else "iw7.gsc-audit-build-plan/1") and
            build["schema"] in (("iw7.gsc-audit-build-run/3",) if refs else ("iw7.gsc-audit-build-run/1", "iw7.gsc-audit-build-run/2")) and
            supervision["Schema"] == "iw7.gsc-audit-build-supervision/1", "Unsupported global audit protocol; separate review required")
    if refs:
        require(plan["reference_contract"] == "iw7.gsc-reference-native/1", "Reference plan protocol differs")
    same(build["plan"], plan, "Build versus exact reviewed plan")
    same_path(plan["output"], run, "Plan output")
    require(supervision["PlanSHA256"].lower() == sha(raw["plan"]), "Supervision plan hash differs")
    require(build["lease_token"] == supervision["LeaseToken"] and isinstance(build["lease_token"], str) and build["lease_token"], "Audit lease records differ")
    require(type(build["success"]) is bool and type(supervision["Success"]) is bool, "Audit success fields must be booleans")
    require(build["success"] is True and not build.get("failure") and build["storage_limit_exceeded"] is False, "Native build steps did not complete")
    require(supervision["TreeClosed"] is True and supervision["LeaseReleased"] is True and
            type(supervision["RootExitCode"]) is int and supervision["RootExitCode"] == 0 and
            type(supervision["JobActiveAtClose"]) is int and supervision["JobActiveAtClose"] == 0, "Original audit tree cleanup is incomplete")
    identity = supervision["OriginalIdentity"]
    require(identity["Source"] == "OriginalProcessHandle" and type(identity["PID"]) is int and identity["PID"] > 0 and
            identity["PID"] == supervision["RootPID"] and identity["CreatedUtc"] == supervision["RootCreatedUtc"], "Original audit identity records differ")
    integer(supervision["RootPID"], 1, 2**32 - 1, "Original root PID")
    integer(identity["Priority"], 16384, 16384, "Original root priority")
    utc(identity["CreatedUtc"])
    same_path(identity["Image"], supervision["RootImage"], "Original root image")
    same_path(identity["Image"], plan["python"], "Original Python image")
    require(plan["wrapper_sha256"] == WRAPPER_SHA256, "Reviewed audit wrapper pin differs")
    wrapper_path = Path(tools_root) / "sdk/modding/audit_gsc_consumption.py"
    wrapper = selector.snapshot(wrapper_path, packager, 262144)
    require(sha(wrapper) == WRAPPER_SHA256, "Installed read-only witness validator differs")
    audit = module(wrapper_path, "creator_consumption_validator")
    audit.validate_pins(evidence["pins"])
    same(bound["pins"], evidence["pins"], "Independent native audit pins")
    exact_bound = {"schema", "pins", "native", "tool_rehashed_after_execution", "input_transport", "complete_consumption_verified",
                   "external_gsc_dependency_absence_verified", "asset_closure_complete", "runtime_ready", "owner_accepted"}
    require(set(bound) == exact_bound and bound["schema"] == "iw7.gsc-consumption-bound/1" and
            bound["tool_rehashed_after_execution"] is True and bound["input_transport"] == "same_bytes_via_stdin" and
            bound["complete_consumption_verified"] is True, "Bound witness protocol differs")
    require(all(bound[key] is False for key in ("external_gsc_dependency_absence_verified", "asset_closure_complete", "runtime_ready", "owner_accepted")), "Consumption receipt cannot promote qualification")
    pins, source = evidence["pins"], build["build_source_manifest"]
    require(source["schema"] == "iw7.gsc-audit-build-source/2" and build["tool_sha256"] == pins["tool_sha256"], "Build/tool source binding differs")
    for key in ("source_revision", "source_sha256", "tables_sha256"):
        same(source[key], pins[key], "Build source " + key)
    for key in ("source_revision", "tool_source_sha256", "tables_sha256"):
        same(source[key], plan[key], "Plan source " + key)
    inputs = plan["inputs"]
    require(isinstance(inputs, list) and [x["role"] for x in inputs] == ["variant", "original"], "Variant/original control input roles required")
    variant = inputs[0]
    same_path(variant["path"], files["input"]["path"], "Variant input")
    require(variant["sha256"] == sha(raw["input"]) and type(variant["bytes"]) is int and variant["bytes"] == len(raw["input"]), "Plan variant container differs")
    if refs:
        same_path(inputs[1]["path"], files["original_input"]["path"], "Original control input")
        require(type(inputs[1]["bytes"]) is int and inputs[1]["bytes"] == len(raw["original_input"]) and
                inputs[1]["sha256"] == sha(raw["original_input"]), "Plan original control bytes differ")
    steps = [x for x in build["steps"] if x["name"] == "witness-variant"]
    require(len(steps) == 1, "One recorded variant witness step required")
    step = steps[0]
    require(type(step["exit_code"]) is int and step["exit_code"] == 0 and step["failure"] is None and step["storage_limit_exceeded"] is False, "Variant witness step failed")
    command = [plan["python"], "-B", plan["wrapper"], "--tool", str(run / "native/Release/iw7-gsc-audit.exe"),
        "--tool-sha256", pins["tool_sha256"], "--source-revision", pins["source_revision"], "--source-sha256", pins["source_sha256"],
        "--tables-sha256", pins["tables_sha256"], "--input", variant["path"], "--output", str(run / "witness-variant")]
    same(step["command"], command, "Recorded witness action/input/pins")
    assembly = audit.validate_witness(raw["input"], bound["native"], pins)
    require(assembly == raw["assembly"], "Separate assembly differs from same-byte native witness")
    for key in ("bytecode_bytes", "stack_bytes"):
        same(compile_record["binary"][key], bound["native"][key], "Historical container " + key)
    completion_linked = link_completion(plan, build, supervision, records, run, pins)
    qualified, reference_sources = reference_qualification(evidence, raw, parsed, plan, build, audit, selector, packager) if refs else (None, {})
    opcodes = re.findall(r"^\s*(OP_\w+)\b", assembly.decode("utf-8"), re.M)
    require(opcodes, "Witness assembly has no observed instructions")
    # Re-read only the bounded selected files, never executables, stock or logs.
    for role, record in records.items():
        require(sha(selector.snapshot(Path(record["path"]), packager, 2 * 1024**2)) == record["sha256"], "Audit artifact changed across read group")
    require(sha(selector.snapshot(wrapper_path, packager, 262144)) == WRAPPER_SHA256, "Witness validator changed during inspection")
    selector.select(project, tools_root, packager)
    blockers = ["historical source/compilation records are bound but compilation provenance is not authenticated or re-executed",
                "native builtin and loader semantics are not proved by encoded reference qualification" if refs else
                "complete structural consumption and observed opcode counts are not complete semantic import-absence proof",
                "variant native builder and independent recipient asset-content closure remain unqualified"]
    if not completion_linked:
        blockers.insert(0, "build-run/1 has no accepted completion record; successful native substeps are not global build qualification")
    if supervision["Success"] is False:
        blockers.insert(0, "supervision recorded failure: " + str(supervision.get("Failure", "unspecified")))
    return {"schema": "iw7.creator-gsc-audit-observation/1", "source_sha256": selected["source"]["sha256"],
        "encoded_external_script_reference_absence": refs, "encoded_reference_report": qualified,
        "reference_source_files": reference_sources,
        "artifact_records_bound": True, "native_witness_bytes_bound": True, "historical_compilation_record_bound": True,
        "bytecode_consumed": bound["native"]["bytecode_consumed"], "stack_consumed": bound["native"]["stack_consumed"],
        "structural_consumption_measured": True, "observed_far_opcodes": sum("Far" in x for x in opcodes),
        "observed_pointer_opcodes": sum("Pointer" in x for x in opcodes), "opcode_count_scope": "bound emitted assembly text only",
        "build_substeps_success_reported": build["success"], "supervision_success_reported": supervision["Success"],
        "global_completion_record_linked": completion_linked, "global_build_revalidated": False,
        "completion_scope": "Pinned historical report linkage only; compiler/tool/result files and job guards are not remeasured by Creator. " +
            ("Both reference-control input containers are remeasured." if refs else "The original-control input is not remeasured."),
        "compilation_provenance_authenticated": False, "native_execution_authenticated": False,
        "external_gsc_dependency_absence_verified": False, "recipient_closure_complete": False, "finalization_allowed": False,
        "package_ready": False, "runtime_ready": False, "owner_accepted": False, "files": records, "pins": pins,
        "unresolved_qualifications": blockers}


def require_finalization(project, tools_root, evidence, packager):
    """Finalizers must re-read evidence, never trust an attached report boolean."""
    report = inspect(project, tools_root, evidence, packager)
    raise ValueError("Creator audit finalization refused: " + "; ".join(report["unresolved_qualifications"]))
