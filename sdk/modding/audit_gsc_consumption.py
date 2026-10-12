"""Bind a pinned native IW7 consumption witness to the same input bytes. No package gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zlib

INPUT_LIMIT = 8 * 1024 * 1024
STACK_LIMIT = 16 * 1024 * 1024
OUTPUT_LIMIT = 128 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path, maximum):
    with Path(path).open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('File exceeds audit limit')
    return data


def unpack(raw):
    if len(raw) < 16 or len(raw) > INPUT_LIMIT or raw[:4] != b'GSC\0':
        raise ValueError('Expected bounded GSC container')
    compressed_size, stack_size, code_size = struct.unpack_from('<III', raw, 4)
    if (not compressed_size or not code_size or code_size > INPUT_LIMIT or stack_size > STACK_LIMIT
            or compressed_size + code_size != len(raw) - 16):
        raise ValueError('Invalid container lengths or trailing data')
    inflater = zlib.decompressobj()
    try:
        stack = inflater.decompress(raw[16:16 + compressed_size], stack_size + 1)
    except zlib.error as error:
        raise ValueError('Invalid compressed stack') from error
    if (len(stack) != stack_size or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail):
        raise ValueError('Compressed stack truncated, trailing or size mismatched')
    return raw[16 + compressed_size:], stack


def validate_pins(pins):
    if set(pins) != {'tool_sha256', 'source_revision', 'source_sha256', 'tables_sha256'}:
        raise ValueError('Require explicit tool, source revision, source digest and table pins')
    for key, value in pins.items():
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}' if key == 'source_revision' else '[0-9a-f]{64}', value):
            raise ValueError('Invalid pin: ' + key)


def validate_witness(raw, witness, pins):
    validate_pins(pins)
    code, stack = unpack(raw)
    if not isinstance(witness, dict):
        raise ValueError('Native witness must be an object')
    expected = {'schema': 'iw7.gsc-consumption-native/1', 'engine': 'iw7-pc',
                'input_bytes': len(raw), 'input_sha256': sha(raw),
                'bytecode_bytes': len(code), 'bytecode_sha256': sha(code),
                'stack_bytes': len(stack), 'stack_sha256': sha(stack),
                'bytecode_consumed': len(code), 'stack_consumed': len(stack),
                'initial_op_end_verified': True, 'complete_consumption_verified': True}
    expected.update({key: value for key, value in pins.items() if key != 'tool_sha256'})
    for key, value in expected.items():
        if type(witness.get(key)) is not type(value) or witness[key] != value:
            raise ValueError('Native witness mismatch: ' + key)
    if code[0] != 0x34:
        raise ValueError('Expected IW7 initial OP_End')
    functions = witness.get('functions')
    if not isinstance(functions, list):
        raise ValueError('Missing function consumption records')
    code_pos, stack_pos = 1, 0
    fields = {'bytecode_begin', 'declared_bytes', 'bytecode_end', 'stack_begin', 'stack_end'}
    for function in functions:
        if not isinstance(function, dict) or set(function) != fields or any(type(v) is not int for v in function.values()):
            raise ValueError('Invalid function consumption record')
        if (function['bytecode_begin'] != code_pos or function['stack_begin'] != stack_pos
                or function['declared_bytes'] <= 0
                or function['bytecode_end'] != code_pos + function['declared_bytes']
                or function['bytecode_end'] > len(code)
                or not stack_pos < function['stack_end'] <= len(stack)):
            raise ValueError('Function consumption mismatch')
        code_pos, stack_pos = function['bytecode_end'], function['stack_end']
    if code_pos != len(code) or stack_pos != len(stack):
        raise ValueError('Unaccounted bytecode or stack suffix')
    encoded = witness.get('assembly_hex')
    if not isinstance(encoded, str) or len(encoded) > OUTPUT_LIMIT or not re.fullmatch('(?:[0-9a-f]{2})*', encoded):
        raise ValueError('Invalid assembly encoding')
    assembly = bytes.fromhex(encoded)
    if type(witness.get('assembly_bytes')) is not int or witness['assembly_bytes'] != len(assembly) or witness.get('assembly_sha256') != sha(assembly):
        raise ValueError('Assembly binding mismatch')
    return assembly


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate witness field')
        result[key] = value
    return result


def audit_bytes(raw, tool, pins):
    validate_pins(pins)
    unpack(raw)
    tool = Path(tool).resolve(strict=True)
    if sha(read_bounded(tool, 64 * 1024 * 1024)) != pins['tool_sha256']:
        raise ValueError('Native tool pin mismatch')
    result = subprocess.run([str(tool), '--stdin-gscbin'], input=raw, capture_output=True, timeout=60)
    if result.returncode or result.stderr or len(result.stdout) > OUTPUT_LIMIT:
        raise ValueError('Native audit failed or exceeded output limit')
    if sha(read_bounded(tool, 64 * 1024 * 1024)) != pins['tool_sha256']:
        raise ValueError('Native tool changed during audit')
    witness = json.loads(result.stdout, object_pairs_hook=unique_object)
    assembly = validate_witness(raw, witness, pins)
    receipt = {'schema': 'iw7.gsc-consumption-bound/1', 'pins': dict(pins), 'native': witness,
               'tool_rehashed_after_execution': True, 'input_transport': 'same_bytes_via_stdin',
               'complete_consumption_verified': True,
               'external_gsc_dependency_absence_verified': False,
               'asset_closure_complete': False, 'runtime_ready': False, 'owner_accepted': False}
    return receipt, assembly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', required=True, type=Path)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    for key in ('tool-sha256', 'source-revision', 'source-sha256', 'tables-sha256'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        raise ValueError('Use a fresh output directory with an existing parent')
    pins = {key: getattr(args, key) for key in ('tool_sha256', 'source_revision', 'source_sha256', 'tables_sha256')}
    receipt, assembly = audit_bytes(read_bounded(args.input, INPUT_LIMIT), args.tool, pins)
    args.output.mkdir()
    (args.output / 'disassembly.gscasm').write_bytes(assembly)
    (args.output / 'consumption.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'complete_consumption_verified': True, 'input_sha256': receipt['native']['input_sha256'],
                      'external_gsc_dependency_absence_verified': False}))


if __name__ == '__main__':
    main()
