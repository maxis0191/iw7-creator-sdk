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
from datetime import datetime

WRAPPER_SHA256 = "42dd0dcb01c014cfbfbabb18d404d4c6ccd1b6d04ed27a5b16e63dde54e72d07"
ROLES = {"compilation", "plan", "build", "supervision", "input", "consumption", "assembly"}
V2_SOURCE_REVISION = "eabe74ab65d8ce2a943b54d24b15a60749a0cf2a"
V2_TOOL_SOURCE = "e762caa7429679946ea5804a0fe3b678d1ab97db5ed3ff063d028327f554a9cf"


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
    require(build["schema"] == "iw7.gsc-audit-build-run/2" and pins["source_revision"] == V2_SOURCE_REVISION and
            plan["tool_source_sha256"] == V2_TOOL_SOURCE and plan["residual_closure_policy"] == "original-job-pinned-vctip/1",
            "Unreviewed completion producer or policy")
    require(supervision["Success"] is True and not supervision.get("Failure"), "Global /2 supervision failed")
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
    if steps and steps[0]["name"] == "zlib-clone":
        expected_steps = ["zlib-clone", "zlib-checkout"] + expected_steps
    same([s["name"] for s in steps], expected_steps, "Ordered completion steps")
    expected_roles = {"source-manifest", "tool", "wrapper", "compiler-config-0", "input-variant", "input-original",
                      "witness-variant", "witness-original", "assembly-variant", "assembly-original"} | {"result-" + name for name in expected_steps}
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
    same_path(by_role["tool"]["path"], run / "native/Release/iw7-gsc-audit.exe", "Recorded native tool")
    require(by_role["tool"]["sha256"] == pins["tool_sha256"] and by_role["wrapper"]["sha256"] == WRAPPER_SHA256, "Completion tool/wrapper pins differ")
    same_path(by_role["wrapper"]["path"], plan["wrapper"], "Recorded wrapper")
    for step in steps:
        integer(step["exit_code"], 0, 0, "Native step exit")
        integer(step["wrapper_exit_code"], 0, 0, "Wrapper step exit")
        require(step["failure"] is None and step["storage_limit_exceeded"] is False, "Completion step failed")
    return True


def inspect(project, tools_root, evidence, packager):
    """Consume independently pinned existing files; no audit_bytes/native call."""
    selector = module(Path(tools_root) / "sdk/modding/creator_self_contained.py", "creator_audit_selector")
    _, selected = selector.select(project, tools_root, packager)
    require(isinstance(evidence, dict) and set(evidence) == {"schema", "run_root", "source_sha256", "pins", "files"}, "Unexpected Creator audit input fields")
    require(evidence["schema"] == "iw7.creator-gsc-audit-input/1" and evidence["source_sha256"] == selected["source"]["sha256"], "Selected source audit binding differs")
    files = evidence["files"]
    require(isinstance(files, dict) and set(files) == ROLES, "Exact audit artifact roles required")
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
    parsed = {role: selector.json_snapshot(raw[role]) for role in ROLES - {"input", "assembly"}}
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
    require(plan["schema"] == "iw7.gsc-audit-build-plan/1" and build["schema"] in ("iw7.gsc-audit-build-run/1", "iw7.gsc-audit-build-run/2") and
            supervision["Schema"] == "iw7.gsc-audit-build-supervision/1", "Unsupported global audit protocol; separate review required")
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
    opcodes = re.findall(r"^\s*(OP_\w+)\b", assembly.decode("utf-8"), re.M)
    require(opcodes, "Witness assembly has no observed instructions")
    # Re-read only the bounded selected files, never executables, stock or logs.
    for role, record in records.items():
        require(sha(selector.snapshot(Path(record["path"]), packager, 2 * 1024**2)) == record["sha256"], "Audit artifact changed across read group")
    require(sha(selector.snapshot(wrapper_path, packager, 262144)) == WRAPPER_SHA256, "Witness validator changed during inspection")
    selector.select(project, tools_root, packager)
    blockers = ["historical source/compilation records are bound but compilation provenance is not authenticated or re-executed",
                "complete structural consumption and observed opcode counts are not complete semantic import-absence proof",
                "variant builder/finalizer and independent recipient asset-content closure remain unqualified"]
    if not completion_linked:
        blockers.insert(0, "build-run/1 has no accepted completion record; successful native substeps are not global build qualification")
    if supervision["Success"] is False:
        blockers.insert(0, "supervision recorded failure: " + str(supervision.get("Failure", "unspecified")))
    return {"schema": "iw7.creator-gsc-audit-observation/1", "source_sha256": selected["source"]["sha256"],
        "artifact_records_bound": True, "native_witness_bytes_bound": True, "historical_compilation_record_bound": True,
        "bytecode_consumed": bound["native"]["bytecode_consumed"], "stack_consumed": bound["native"]["stack_consumed"],
        "structural_consumption_measured": True, "observed_far_opcodes": sum("Far" in x for x in opcodes),
        "observed_pointer_opcodes": sum("Pointer" in x for x in opcodes), "opcode_count_scope": "bound emitted assembly text only",
        "build_substeps_success_reported": build["success"], "supervision_success_reported": supervision["Success"],
        "global_completion_record_linked": completion_linked, "global_build_revalidated": False,
        "completion_scope": "Pinned historical report linkage only; compiler/tool/result/original-control files and job guards are not remeasured by Creator",
        "compilation_provenance_authenticated": False, "native_execution_authenticated": False,
        "external_gsc_dependency_absence_verified": False, "recipient_closure_complete": False, "finalization_allowed": False,
        "package_ready": False, "runtime_ready": False, "owner_accepted": False, "files": records, "pins": pins,
        "unresolved_qualifications": blockers}


def require_finalization(project, tools_root, evidence, packager):
    """Finalizers must re-read evidence, never trust an attached report boolean."""
    report = inspect(project, tools_root, evidence, packager)
    raise ValueError("Creator audit finalization refused: " + "; ".join(report["unresolved_qualifications"]))
