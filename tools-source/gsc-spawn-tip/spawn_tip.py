"""One exact source-only plan and admitted child phase; not a generic compiler SDK."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys

HERE = Path(__file__).resolve().parent
MIB = 1024**2
SOURCE_SHA = "eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23"
COMPILER_SHA = "1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb"
BUILD_SHA = "7279357cf636295561ff66dd1e085372d93841147859073349868f89a7dcb6e7"
SUPERVISION_SHA = "f1a1f3e42d3b3c10efca4cab804df91a756f8dac11bbb97f95289e8b29538575"
PINS = {
    "decoder": {
        "tool_sha256": "fbaeff90961d1c5c3aec5f293c6dcb7b9dd92ab049e6aebe3ea399b47a007211",
        "source_revision": "03d3956d648b7aa4637fe1007f9d69ea463631e9",
        "source_sha256": "bd53e01813dd80d44c871108fa1a3730db1b03e89b084e818098f49f12352d51",
        "tables_sha256": "6e3ed82737908b5c7be76290a178a66b5c63456a12097e964139154f4b46de4b"},
    "profile_sha256": "e87230812b01059ece4327d9d465b8b20e5e1162d3cd698492aed70405bbf360",
    "reference_validator_sha256": "fdb52f27225c61b563a09cd710cfeca769a9d01a8c971b882edeb277efe98a7c",
    "consumption_validator_sha256": "42dd0dcb01c014cfbfbabb18d404d4c6ccd1b6d04ed27a5b16e63dde54e72d07",
}
BINARY_PINS = {
    "Compiler": (23029248, COMPILER_SHA),
    "Auditor": (1248768, PINS["decoder"]["tool_sha256"]),
    "Python": (104952, "4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a"),
    "Host": (301368, "362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139"),
    "JobAssembly": (13312, "5f613ebb83019dbf4bfa4f6a93c5329098343729b70acc2cfa70aa8b64f195f8"),
}
SOURCES = {
    "Runner": "tools-source/gsc-spawn-tip/Run-SpawnTip.ps1",
    "Profile": "tools-source/gsc-spawn-tip/SpawnTip.Profile.ps1",
    "Phase": "tools-source/gsc-spawn-tip/spawn_tip.py",
    "Core": "tools-source/asset-bridge/h1-fixture/H1Native.Core.ps1",
    "Scheduler": "ops/Resource-Scheduler.Core.ps1",
    "Memory": "ops/Resource-Memory.ps1",
    "Recorder": "ops/Resource-RecorderOwnedProcess.Core.ps1",
    "MemoryNative": "ops/native/ResourceMemory.cs",
    "JobSource": "tools-source/asset-bridge/animation/Probe-NativeJob.cs",
    "Consumption": "sdk/modding/audit_gsc_consumption.py",
    "Source": "sdk/modding/examples/server-spawn-tip/sdk_spawn_tip.gsc",
}
FALSE_GATES = {key: False for key in ("asset_dependency_closure_verified",
    "native_builtin_semantics_verified", "runtime_validation_passed", "owner_acceptance", "package_ready")}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key.casefold() not in {x.casefold() for x in result}, "Duplicate JSON property")
        result[key] = value
    return result


def path_ok(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts and '"' not in str(path)
            and not any(x in str(path) for x in "\r\n"), "Canonical absolute path required")
    for part in (*reversed(path.parents), path):
        if part.exists() or part.is_symlink():
            m = part.lstat()
            require(not stat.S_ISLNK(m.st_mode) and not getattr(m, "st_file_attributes", 0) & 0x400,
                    "Redirected path refused")
    return path


def read(path, limit):
    path = path_ok(path)
    require(path.is_file() and path.stat().st_size <= limit, "Bounded regular file required")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "File grew beyond bound")
    return raw


def load(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def text_pin(role, path, expected=None):
    require(Path(path).suffix in (".py", ".ps1", ".cs", ".cpp", ".hpp", ".json", ".gsc"),
            "Planning reads source/text only")
    raw = read(path, 2 * MIB)
    require(expected is None or sha(raw) == expected, "Source/physical table pin differs: " + role)
    return {"Role": role, "Path": str(path_ok(path)), "Bytes": len(raw), "SHA256": sha(raw), "IsText": True}


def make_plan(repo, audit_source, compiler, python, host, job, run):
    repo, audit_source, run = map(path_ok, (repo, audit_source, run))
    require(run.parent == repo / "runtime" and not run.exists(), "Fresh immediate runtime child required")
    audit_run = audit_source / "build/native-reference-qualification-20261012-v8"
    bindings = [text_pin(role, repo / rel,
                 SOURCE_SHA if role == "Source" else PINS["consumption_validator_sha256"] if role == "Consumption" else None)
                for role, rel in SOURCES.items()]
    bindings += [text_pin("References", audit_source / "audit/references.py", PINS["reference_validator_sha256"]),
                 text_pin("ReferenceProfile", audit_source / "audit/reference-profile.json", PINS["profile_sha256"]),
                 text_pin("V8Build", audit_run / "build-receipt.json", BUILD_SHA),
                 text_pin("V8Supervision", audit_run / "supervision.json", SUPERVISION_SHA)]
    profile = load(read(audit_source / "audit/reference-profile.json", 64 * 1024))
    require(len(profile["table_files"]) == 8 and profile["tables_sha256"] == PINS["decoder"]["tables_sha256"],
            "Exact V8 physical table inventory required")
    for index, row in enumerate(profile["table_files"]):
        bindings.append(text_pin("Table" + str(index), audit_source / row["path"], row["sha256"]))
    paths = {"Compiler": compiler, "Python": python, "Host": host, "JobAssembly": job,
             "Auditor": audit_run / "native/Release/iw7-gsc-audit.exe"}
    # Expected values from retained qualified receipts. No binary open/hash/stat.
    for role, path in paths.items():
        size, digest = BINARY_PINS[role]
        bindings.append({"Role": role, "Path": str(path_ok(path)), "Bytes": size,
                         "SHA256": digest, "IsText": False})
    return {"Schema": "iw7.spawn-tip-plan/1", "Repo": str(repo), "AuditSource": str(audit_source),
            "RunRoot": str(run), "Bindings": bindings, "ReferencePins": PINS,
            "PhysicalBytes": 4 * 1024**3, "CommitBytes": 6 * 1024**3,
            "DeadlineSeconds": 180, "CompileSeconds": 20, "AuditSeconds": 60,
            "OutputLimitBytes": 64 * MIB, "MetadataReserveBytes": MIB,
            "CompilerLogBytes": 64 * 1024, "AuditLogBytes": 4 * MIB,
            "BinaryLimitBytes": 64 * 1024, "StackLimitBytes": 128 * 1024,
            "EstimatesAreMeasured": False, "BinaryInputsVerified": False,
            "Payload": "iw7-mod/custom_scripts/cp/sdk_spawn_tip.gsc"}


def pins_by_role(plan):
    pins = {p["Role"]: p for p in plan["Bindings"]}
    require(len(pins) == len(plan["Bindings"]), "Repeated binding role")
    return pins


def verify_pin(pin):
    raw = read(pin["Path"], max(pin["Bytes"], 1))
    require(len(raw) == pin["Bytes"] and sha(raw) == pin["SHA256"], "Input pin differs: " + pin["Role"])
    return raw


def module(pin, name):
    verify_pin(pin)
    spec = importlib.util.spec_from_file_location(name, pin["Path"])
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write_new(path, raw, limit):
    path = Path(path).absolute()
    require(len(raw) <= limit, "Output exceeds per-file bound")
    path_ok(path)
    with Path(path).open("xb") as stream:
        stream.write(raw)


def write_json(path, value, limit=MIB):
    write_new(path, (json.dumps(value, indent=2, allow_nan=False) + "\n").encode(), limit)


def compile_ok(result):
    text = (result.stdout + result.stderr).decode("utf-8", errors="strict")
    require(result.returncode == 0 and not re.search(r"\[ERROR\]|failed|exception", text, re.I),
            "Compiler reported failure (including exit-zero diagnostics)")
    require(sum(line.startswith("compiled iw7/") for line in text.splitlines()) == 1,
            "Exactly one compilation marker required")


def execute(plan, plan_sha, lease_token, run_id):
    """Internal child. Only its external H1 original-job receipt proves closure."""
    require(re.fullmatch(r"[0-9a-f]{32}", lease_token) and re.fullmatch(r"[0-9a-f]{32}", run_id),
            "Admitted supervisor token/run identity required")
    pins = pins_by_role(plan)
    require(plan["ReferencePins"] == PINS, "Independent reference pins differ")
    root = path_ok(plan["RunRoot"])
    require(Path.cwd() == root / "phase", "Supervisor-owned phase directory required")
    source = verify_pin(pins["Source"])
    require(sha(source) == SOURCE_SHA, "Only the original spawn-tip source is admitted")
    for pin in plan["Bindings"]:
        verify_pin(pin)
    consumption = module(pins["Consumption"], "spawn_tip_consumption")
    references = module(pins["References"], "spawn_tip_references")
    compiler = pins["Compiler"]["Path"]
    command = [compiler, "-m", "comp", "-g", "iw7", "-s", "pc", pins["Source"]["Path"]]
    result = consumption.run_bounded(command, b"", limit=plan["CompilerLogBytes"], timeout=plan["CompileSeconds"])
    write_new("compile.stdout.log", result.stdout, plan["CompilerLogBytes"])
    write_new("compile.stderr.log", result.stderr, plan["CompilerLogBytes"])
    write_json(Path.cwd() / "compile.command.json", {"argv": command, "exit_code": result.returncode})
    compile_ok(result)
    binary = Path.cwd() / "compiled/iw7/sdk_spawn_tip.gscbin"
    raw = read(binary, plan["BinaryLimitBytes"])
    require(len(raw) >= 16 and struct.unpack_from("<I", raw, 8)[0] <= plan["StackLimitBytes"],
            "Small-profile declared stack bound exceeded before inflation")
    _, stack = references.unpack(raw)
    require(len(stack) <= plan["StackLimitBytes"], "Small-profile decompressed stack bound exceeded")
    auditor = pins["Auditor"]["Path"]
    result = consumption.run_bounded([auditor, "--stdin-gscbin-references"], raw,
                                     limit=plan["AuditLogBytes"], timeout=plan["AuditSeconds"])
    write_new("audit.stdout.json", result.stdout, plan["AuditLogBytes"])
    write_new("audit.stderr.log", result.stderr, plan["AuditLogBytes"])
    require(result.returncode == 0 and not result.stderr, "Strict native audit refused input")
    native = load(result.stdout)
    assembly = consumption.validate_witness(raw, native["consumption"], PINS["decoder"])
    bound = references.validate(raw, native, PINS, plan["AuditSource"], consumption)
    write_new("disassembly.gscasm", assembly, MIB)
    write_json(Path.cwd() / "references.bound.json", bound)
    for pin in plan["Bindings"]:
        verify_pin(pin)
    require(read(binary, plan["BinaryLimitBytes"]) == raw, "Compiled input changed during audit")
    status = bool(bound["complete_instruction_coverage_verified"] and
                  bound["encoded_external_script_reference_absence"] and not bound["blockers"])
    artifacts = []
    for name in ("compiled/iw7/sdk_spawn_tip.gscbin", "compile.command.json", "compile.stdout.log",
                 "compile.stderr.log", "audit.stdout.json", "audit.stderr.log", "disassembly.gscasm",
                 "references.bound.json"):
        data = read(Path.cwd() / name, 4 * MIB)
        artifacts.append({"Path": str(Path.cwd() / name), "Bytes": len(data), "SHA256": sha(data)})
    report = {"Schema": "iw7.spawn-tip-child/1", "PlanSHA256": plan_sha, "LeaseToken": lease_token,
              "RunId": run_id, "SourceSHA256": sha(source), "InputSHA256": sha(raw),
              "EncodedReferenceAbsence": status, "InputsReverified": True, "Artifacts": artifacts,
              "ChildOnly": True, "JobClosureProven": False, "Limits": FALSE_GATES}
    write_json(Path.cwd() / "child.json", report)
    require(status, "Measured reference blockers remain; preserved evidence is not qualified absence")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("plan")
    for name in ("repo", "audit-source", "compiler", "python", "host", "job", "run", "output"):
        prep.add_argument("--" + name, type=Path, required=True)
    child = sub.add_parser("child")
    for name in ("plan", "plan-sha256", "lease-token", "run-id"):
        child.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if args.action == "plan":
        plan = make_plan(args.repo, args.audit_source, args.compiler, args.python, args.host, args.job, args.run)
        write_json(path_ok(args.output), plan, 128 * 1024)
        print(json.dumps({"plan": str(args.output), "sha256": sha(read(args.output, 128 * 1024)),
                          "binary_inputs_read": False, "runtime_ready": False}))
    else:
        raw = read(args.plan, 128 * 1024)
        require(sha(raw) == args.plan_sha256, "Reviewed plan changed")
        execute(load(raw), args.plan_sha256, args.lease_token, args.run_id)


if __name__ == "__main__":
    main()
