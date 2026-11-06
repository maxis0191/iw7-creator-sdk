"""Find RIP-relative references to target addresses in the iw7_ship code of a full minidump and print the
referencing instruction.  usage: xref.py <dump> <hex target> [...]"""
import sys
import numpy as np
from minidump.minidumpfile import MinidumpFile
import capstone

dump = MinidumpFile.parse(sys.argv[1])
reader = dump.get_reader()
BASE, SIZE = 0x140001000, 0x14A0000
code = reader.read(BASE, SIZE)
arr = np.frombuffer(code, dtype=np.uint8)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
for t in (int(x, 16) for x in sys.argv[2:]):
    found = 0
    for align in range(4):
        n = (len(arr) - align) // 4
        disp = arr[align:align + n * 4].view('<i4').astype(np.int64)
        pos = BASE + align + np.arange(n, dtype=np.int64) * 4
        idx = np.nonzero(pos + 4 + disp == t)[0]
        for k in idx:
            at = int(pos[k])
            for back in range(2, 8):
                ins = next(md.disasm(reader.read(at - back, 16), at - back), None)
                if ins and ins.address + ins.size >= at + 4 and ins.size > back:
                    print(hex(t), hex(ins.address), ins.mnemonic, ins.op_str); found += 1
                    break
    print(hex(t), 'refs', found)
