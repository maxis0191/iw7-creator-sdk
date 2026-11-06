"""Disassemble a range of the dump.  usage: dis.py <dump> <hex start> <count>"""
import sys
from minidump.minidumpfile import MinidumpFile
import capstone

reader = MinidumpFile.parse(sys.argv[1]).get_reader()
start, count = int(sys.argv[2], 16), int(sys.argv[3])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
code = reader.read(start, count * 15)
for i, ins in enumerate(md.disasm(code, start)):
    if i >= count: break
    extra = ''
    if 'rip' in ins.op_str:
        # resolve rip-relative operand
        import re
        m = re.search(r'rip ([+-]) 0x([0-9a-f]+)', ins.op_str)
        if m:
            off = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            extra = '   ; -> ' + hex(ins.address + ins.size + off)
    print('%x  %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, extra))
