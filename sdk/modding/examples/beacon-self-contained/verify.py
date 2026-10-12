"""Offline source/bytecode witness only; never a Creator adapter or package gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sdk_beacon_self_contained.gsc"
COMPILER_SHA256 = "1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb"
RETAIL_SHA256 = "007f026cb956a4c256977d60c2691cc554e0cc78a13dfd1694469acf707bbdf7"
LOCAL_SCRIPT_OPS = {
    "OP_ScriptLocalFunctionCall2", "OP_ScriptLocalMethodCall", "OP_ScriptLocalMethodThreadCall"
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def function_body(source, name):
    match = re.search(r"^" + re.escape(name) + r"\s*\([^\n]*\)\s*\{", source, re.M)
    if not match:
        raise ValueError("Missing function: " + name)
    start = source.index("{", match.start())
    depth = 0
    for token in re.finditer(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/|[{}]', source[start:]):
        if token.group() == "{":
            depth += 1
        elif token.group() == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1:start + token.start()]
    raise ValueError("Unclosed function: " + name)


def inspect_binary(raw):
    if len(raw) < 16 or len(raw) > 65536 or raw[:4] != b"GSC\0":
        raise ValueError("Expected bounded gsc-tool IW7 GSC container")
    compressed_len, stack_len, code_len = struct.unpack_from("<III", raw, 4)
    if not 0 < stack_len <= 65536 or not 0 < code_len <= 65536 or len(raw) != 16 + compressed_len + code_len:
        raise ValueError("Invalid GSC container lengths")
    inflater = zlib.decompressobj()
    stack = inflater.decompress(raw[16:16 + compressed_len], stack_len + 1)
    if len(stack) != stack_len or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError("Invalid compressed symbol stack")
    if any(value in stack.lower() for value in (b"scripts/", b"scripts\\", b"utility", b"::")):
        raise ValueError("External script namespace present in compiled symbol stack")
    return {"bytes": len(raw), "sha256": sha(raw), "compressed_stack_bytes": compressed_len,
            "stack_bytes": stack_len, "bytecode_bytes": code_len, "literal_external_namespace_strings": 0}


def inspect_assembly(text):
    functions, calls, opcodes = [], [], []
    opened = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("sub:"):
            if opened:
                raise ValueError("Nested assembly function")
            opened = line[4:]
            if opened in functions:
                raise ValueError("Duplicate assembly function")
            functions.append(opened)
            continue
        if line.startswith("end:"):
            if line[4:] != opened:
                raise ValueError("Mismatched assembly function")
            opened = None
            continue
        if not opened:
            raise ValueError("Instruction outside assembly function")
        if re.fullmatch(r"loc_[0-9A-F]+", line):
            continue
        match = re.fullmatch(r"(OP_\w+)(?:\s+(.*))?", line)
        if not match:
            raise ValueError("Unrecognized assembly line")
        opcode, operand = match.groups()
        opcodes.append(opcode)
        if "Far" in opcode or "Pointer" in opcode:
            raise ValueError("External or dynamic call/reference opcode: " + opcode)
        if opcode.startswith("OP_Script"):
            if opcode not in LOCAL_SCRIPT_OPS:
                raise ValueError("Unqualified script opcode: " + opcode)
            calls.append((opcode, (operand or "").split(" ")[0]))
    if opened or not opcodes or "intro_flag_ready" not in functions:
        raise ValueError("Incomplete assembly witness")
    if any(target not in functions for _, target in calls):
        raise ValueError("Local script call has no local definition")
    return {"functions": functions, "instructions": len(opcodes), "script_calls": len(calls),
            "script_call_opcodes": sorted({op for op, _ in calls}), "external_script_calls": 0,
            "dynamic_script_references": 0}


def run(compiler, retail_reference, output):
    compiler, retail_reference = Path(compiler).resolve(strict=True), Path(retail_reference).resolve(strict=True)
    output = Path(output).absolute()
    if output.exists() or not output.parent.is_dir() or output.resolve().is_relative_to(HERE):
        raise ValueError("Use a fresh output directory outside the tracked example")
    compiler_hash = sha(compiler.read_bytes())
    if compiler_hash != COMPILER_SHA256:
        raise ValueError("Pinned existing gsc-tool 1.5.1.359 required")
    retail = retail_reference.read_bytes()
    if sha(retail) != RETAIL_SHA256:
        raise ValueError("Inspected historical utility source differs")
    source = SOURCE.read_bytes()
    if len(source) > 65536 or b"::" in source or b"#include" in source.lower():
        raise ValueError("Bounded source without external script declarations required")
    output.mkdir()
    phases = []
    for mode, path, marker in (("parse", SOURCE, "parsed iw7/"), ("comp", SOURCE, "compiled iw7/"),
                              ("disasm", output / "compiled/iw7/sdk_beacon_self_contained.gscbin", "disassembled iw7/")):
        command = [str(compiler), "-m", mode, "-g", "iw7", "-s", "pc"]
        if mode == "parse":
            command += ["-y"]
        command += [str(path)]
        result = subprocess.run(command, cwd=output, capture_output=True, text=True, timeout=20)
        (output / (mode + ".stdout.log")).write_text(result.stdout)
        (output / (mode + ".stderr.log")).write_text(result.stderr)
        if (result.returncode or re.search(r"\[ERROR\]|failed|exception", result.stdout + result.stderr, re.I)
                or sum(line.startswith(marker) for line in result.stdout.splitlines()) != 1):
            raise ValueError("Offline compiler phase refused: " + mode)
        phases.append({"name": mode, "exit_code": result.returncode})
    binary = (output / "compiled/iw7/sdk_beacon_self_contained.gscbin").read_bytes()
    assembly = (output / "disassembled/iw7/sdk_beacon_self_contained.gscasm").read_bytes()
    binary_result, assembly_result = inspect_binary(binary), inspect_assembly(assembly.decode())
    if sha(SOURCE.read_bytes()) != sha(source) or sha(compiler.read_bytes()) != compiler_hash or sha(retail_reference.read_bytes()) != RETAIL_SHA256:
        raise ValueError("Source, compiler or inspected reference changed during validation")
    result = {"schema": "iw7.beacon-self-contained-offline/1", "source_bytes": len(source), "source_sha256": sha(source),
              "compiler_sha256": compiler_hash, "retail_reference_sha256": RETAIL_SHA256, "phases": phases,
              "binary": binary_result, "assembly": dict(assembly_result, bytes=len(assembly), sha256=sha(assembly)),
              "external_gsc_dependency_absent_in_this_compilation": True,
              "current_retail_scriptfile_binding_measured": False, "creator_adapter_supported": False,
              "asset_closure_complete": False, "runtime_ready": False, "owner_accepted": False}
    (output / "validation.local.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    parser.add_argument("--retail-reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.compiler, args.retail_reference, args.output), indent=2))
