"""Where does a running Windows program spend its processor time? A sampling profiler that needs no install.

  python -I proc_sample.py <pid> [--seconds 30] [--interval-ms 10] [--depth 24] [--top 25] [--json out.json]
         [--symbols <folder with the program's .pdb>]

Every interval it suspends each thread of the process for a moment, walks its stack (dbghelp StackWalk64, the
Windows debug help library that ships with Windows) and resumes it. Frames are named with the program's own symbols
when its .pdb is beside the .exe or in --symbols, else as module+offset. It prints the functions where the samples
landed (self) and the functions on the stacks (inclusive), each as a share of the samples of busy threads.
A thread that was waiting (in a wait or sleep function at the top) is counted apart, so the shares are of real work.
Only reads the process; the pauses are microseconds. Run it on your own processes only.
"""
import argparse, collections, ctypes, ctypes.wintypes as wt, json, os, sys, time

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
dbg = ctypes.WinDLL('dbghelp', use_last_error=True)

PROCESS_ALL = 0x0010 | 0x0400 | 0x0008  # VM_READ | QUERY_INFORMATION | VM_OPERATION
THREAD_ALL = 0x0002 | 0x0008 | 0x0010 | 0x0040  # SUSPEND_RESUME | GET_CONTEXT | QUERY_INFORMATION | QUERY_LIMITED
TH32CS_SNAPTHREAD = 0x4
CONTEXT_FULL = 0x10000B
IMAGE_FILE_MACHINE_AMD64 = 0x8664


class M128A(ctypes.Structure):
    _fields_ = [('Low', ctypes.c_uint64), ('High', ctypes.c_int64)]


class CONTEXT(ctypes.Structure):
    _pack_ = 16
    _fields_ = [(n, ctypes.c_uint64) for n in ('P1Home', 'P2Home', 'P3Home', 'P4Home', 'P5Home', 'P6Home')] + [
        ('ContextFlags', wt.DWORD), ('MxCsr', wt.DWORD),
        ('SegCs', wt.WORD), ('SegDs', wt.WORD), ('SegEs', wt.WORD), ('SegFs', wt.WORD), ('SegGs', wt.WORD), ('SegSs', wt.WORD),
        ('EFlags', wt.DWORD)] + [(n, ctypes.c_uint64) for n in (
        'Dr0', 'Dr1', 'Dr2', 'Dr3', 'Dr6', 'Dr7', 'Rax', 'Rcx', 'Rdx', 'Rbx', 'Rsp', 'Rbp', 'Rsi', 'Rdi',
        'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15', 'Rip')] + [
        ('FltSave', ctypes.c_byte * 512), ('VectorRegister', M128A * 26), ('VectorControl', ctypes.c_uint64),
        ('DebugControl', ctypes.c_uint64), ('LastBranchToRip', ctypes.c_uint64), ('LastBranchFromRip', ctypes.c_uint64),
        ('LastExceptionToRip', ctypes.c_uint64), ('LastExceptionFromRip', ctypes.c_uint64)]


class ADDRESS64(ctypes.Structure):
    _fields_ = [('Offset', ctypes.c_uint64), ('Segment', wt.WORD), ('Mode', ctypes.c_int)]


class KDHELP64(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ('Thread', 'ThCallbackStack', 'ThCallbackBStore', 'NextCallback',
                                                'FramePointer', 'KiCallUserMode', 'KeUserCallbackDispatcher',
                                                'SystemRangeStart', 'KiUserExceptionDispatcher', 'StackBase',
                                                'StackLimit', 'BuildVersion', 'RetpolineStubFunctionTableSize',
                                                'RetpolineStubFunctionTable', 'RetpolineStubOffset',
                                                'RetpolineStubSize', 'Reserved0', 'Reserved1')]


class STACKFRAME64(ctypes.Structure):
    _fields_ = [('AddrPC', ADDRESS64), ('AddrReturn', ADDRESS64), ('AddrFrame', ADDRESS64), ('AddrStack', ADDRESS64),
                ('FuncTableEntry', ctypes.c_void_p), ('Params', ctypes.c_uint64 * 4), ('Far', wt.BOOL),
                ('Virtual', wt.BOOL), ('Reserved', ctypes.c_uint64 * 3), ('KdHelp', KDHELP64)]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ThreadID', wt.DWORD),
                ('th32OwnerProcessID', wt.DWORD), ('tpBasePri', wt.LONG), ('tpDeltaPri', wt.LONG), ('dwFlags', wt.DWORD)]


class SYMBOL_INFO(ctypes.Structure):
    _fields_ = [('SizeOfStruct', wt.ULONG), ('TypeIndex', wt.ULONG), ('Reserved', ctypes.c_uint64 * 2),
                ('Index', wt.ULONG), ('Size', wt.ULONG), ('ModBase', ctypes.c_uint64), ('Flags', wt.ULONG),
                ('Value', ctypes.c_uint64), ('Address', ctypes.c_uint64), ('Register', wt.ULONG), ('Scope', wt.ULONG),
                ('Tag', wt.ULONG), ('NameLen', wt.ULONG), ('MaxNameLen', wt.ULONG), ('Name', ctypes.c_char * 512)]


FUNC_TABLE = ctypes.WINFUNCTYPE(ctypes.c_void_p, wt.HANDLE, ctypes.c_uint64)
GET_MODBASE = ctypes.WINFUNCTYPE(ctypes.c_uint64, wt.HANDLE, ctypes.c_uint64)
dbg.StackWalk64.argtypes = [wt.DWORD, wt.HANDLE, wt.HANDLE, ctypes.POINTER(STACKFRAME64), ctypes.c_void_p,
                            ctypes.c_void_p, FUNC_TABLE, GET_MODBASE, ctypes.c_void_p]
dbg.SymFunctionTableAccess64.restype = ctypes.c_void_p
dbg.SymFunctionTableAccess64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbg.SymGetModuleBase64.restype = ctypes.c_uint64
dbg.SymGetModuleBase64.argtypes = [wt.HANDLE, ctypes.c_uint64]
dbg.SymFromAddr.argtypes = [wt.HANDLE, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(SYMBOL_INFO)]
dbg.SymInitializeW.argtypes = [wt.HANDLE, wt.LPCWSTR, wt.BOOL]
k32.OpenThread.restype = wt.HANDLE
k32.OpenProcess.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.POINTER(CONTEXT)]
k32.SuspendThread.argtypes = [wt.HANDLE]
k32.ResumeThread.argtypes = [wt.HANDLE]
k32.CloseHandle.argtypes = [wt.HANDLE]

WAITS = ('NtWaitFor', 'NtDelayExecution', 'NtRemoveIoCompletion', 'ZwWaitFor', 'NtWaitForAlertByThreadId',
         'NtUserMsgWaitForMultipleObjectsEx', 'ZwRemoveIoCompletion', 'NtSignalAndWaitForSingleObject')


def threads(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    e = THREADENTRY32(); e.dwSize = ctypes.sizeof(e)
    out = []
    ok = k32.Thread32First(snap, ctypes.byref(e))
    while ok:
        if e.th32OwnerProcessID == pid:
            out.append(e.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return out


class Sampler:
    def __init__(self, pid, symbols=None, depth=24):
        self.pid, self.depth = pid, depth
        self.h = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not self.h:
            raise OSError('cannot open process %d (error %d)' % (pid, ctypes.get_last_error()))
        dbg.SymSetOptions(0x2 | 0x4 | 0x10 | 0x200)  # UNDNAME | DEFERRED_LOADS | LOAD_LINES | FAIL_CRITICAL_ERRORS
        if not dbg.SymInitializeW(self.h, symbols, True):
            raise OSError('SymInitialize failed (%d)' % ctypes.get_last_error())
        self.ft = FUNC_TABLE(lambda hp, a: dbg.SymFunctionTableAccess64(hp, a))
        self.mb = GET_MODBASE(lambda hp, a: dbg.SymGetModuleBase64(hp, a))
        self.names = {}
        self.th = {}

    def name(self, addr):
        n = self.names.get(addr)
        if n is None:
            si = SYMBOL_INFO(); si.SizeOfStruct = ctypes.sizeof(SYMBOL_INFO) - 512; si.MaxNameLen = 511
            disp = ctypes.c_uint64()
            if dbg.SymFromAddr(self.h, addr, ctypes.byref(disp), ctypes.byref(si)):
                n = si.Name.decode('utf-8', 'replace')
            else:
                base = dbg.SymGetModuleBase64(self.h, addr)
                n = ('mod_%x+%x' % (base, addr - base)) if base else ('0x%x' % addr)
            self.names[addr] = n
        return n

    def stack(self, tid):
        th = self.th.get(tid)
        if th is None:
            th = k32.OpenThread(THREAD_ALL, False, tid)
            self.th[tid] = th
        if not th:
            return None
        if k32.SuspendThread(th) == 0xFFFFFFFF:
            return None
        try:
            ctx = CONTEXT(); ctx.ContextFlags = CONTEXT_FULL
            if not k32.GetThreadContext(th, ctypes.byref(ctx)):
                return None
            sf = STACKFRAME64()
            sf.AddrPC.Offset, sf.AddrPC.Mode = ctx.Rip, 3
            sf.AddrFrame.Offset, sf.AddrFrame.Mode = ctx.Rbp, 3
            sf.AddrStack.Offset, sf.AddrStack.Mode = ctx.Rsp, 3
            pcs = []
            for _ in range(self.depth):
                if not dbg.StackWalk64(IMAGE_FILE_MACHINE_AMD64, self.h, th, ctypes.byref(sf), ctypes.byref(ctx), None,
                                       self.ft, self.mb, None):
                    break
                if not sf.AddrPC.Offset:
                    break
                pcs.append(sf.AddrPC.Offset)
            return pcs
        finally:
            k32.ResumeThread(th)


def run(pid, seconds, interval, depth, symbols):
    s = Sampler(pid, symbols, depth)
    raw = []
    end = time.monotonic() + seconds
    rounds = 0
    while time.monotonic() < end:
        for tid in threads(pid):
            pcs = s.stack(tid)
            if pcs:
                raw.append((tid, pcs))
        rounds += 1
        time.sleep(interval / 1000.0)
    selfc, incl, waits, busy = collections.Counter(), collections.Counter(), 0, 0
    per_thread = collections.Counter()
    for tid, pcs in raw:
        names = [s.name(a) for a in pcs]
        if any(w in names[0] for w in WAITS) or names[0].startswith(('NtWait', 'ZwWait')):
            waits += 1
            continue
        busy += 1
        per_thread[tid] += 1
        selfc[names[0]] += 1
        for n in set(names):
            incl[n] += 1
    return {'schema': 'iw7.proc-sample/1', 'pid': pid, 'seconds': seconds, 'rounds': rounds, 'samples': len(raw),
            'busy': busy, 'waiting': waits, 'busy_threads': dict(per_thread.most_common(8)),
            'self': selfc.most_common(60), 'inclusive': incl.most_common(80)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('pid', type=int); ap.add_argument('--seconds', type=float, default=30)
    ap.add_argument('--interval-ms', type=float, default=10); ap.add_argument('--depth', type=int, default=24)
    ap.add_argument('--top', type=int, default=25); ap.add_argument('--json'); ap.add_argument('--symbols')
    a = ap.parse_args()
    r = run(a.pid, a.seconds, a.interval_ms, a.depth, a.symbols)
    if a.json:
        json.dump(r, open(a.json, 'w'), indent=1)
    b = max(1, r['busy'])
    print('%d samples in %d rounds over %.0f s: %d busy, %d waiting; busy threads %s' % (
        r['samples'], r['rounds'], r['seconds'], r['busy'], r['waiting'], r['busy_threads']))
    print('self (where the busy samples landed):')
    for n, c in r['self'][:a.top]:
        print('  %5.1f %%  %s' % (100.0 * c / b, n[:150]))
    print('inclusive (on the stack):')
    for n, c in r['inclusive'][:a.top]:
        print('  %5.1f %%  %s' % (100.0 * c / b, n[:150]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
