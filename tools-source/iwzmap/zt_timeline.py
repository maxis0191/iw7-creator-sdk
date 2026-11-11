"""Where does a ZoneTool run spend its time? Follow its log while it runs and stamp every new line.

  python -I zt_timeline.py follow <zt-*.out.log> <timeline.tsv> --pid <zonetool pid>   (zt.ps1 starts this itself)
  python -I zt_timeline.py report <timeline.tsv> [--top 12]

ZoneTool prints no times. The follower reads the log every 0.25 s while the process lives and writes
"<seconds since start>\t<line>" for each new line, so a line's time is when it appeared (within 0.25 s, and
within the buffering of the log: zt.ps1 runs ZoneTool with -unbuffered-io). The report names the phases
(the line that opened each phase and how long until the next phase) and the longest gaps between lines.
"""
import argparse, ctypes, os, re, sys, time

def alive(pid):
    if not pid:
        return False
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259  # STILL_ACTIVE


def follow(log, out, pid, limit):
    t0 = time.monotonic()
    pos, carry = 0, b''
    with open(out, 'w', encoding='utf-8', newline='\n') as w:
        w.write('# zt_timeline/1 %s\n' % log)
        while True:
            running = alive(pid)
            if os.path.exists(log):
                with open(log, 'rb') as f:
                    f.seek(pos)
                    data = f.read()
                pos += len(data)
                parts = (carry + data).split(b'\n')
                carry = parts.pop()
                now = time.monotonic() - t0
                for p in parts:
                    w.write('%.2f\t%s\n' % (now, p.decode('utf-8', 'replace').rstrip('\r')))
                w.flush()
            if not running and pid:
                break
            if time.monotonic() - t0 > limit:
                break
            time.sleep(0.25)
        if carry:
            w.write('%.2f\t%s\n' % (time.monotonic() - t0, carry.decode('utf-8', 'replace').rstrip('\r')))
        w.write('%.2f\t# end\n' % (time.monotonic() - t0))


def read(path):
    rows = []
    for ln in open(path, encoding='utf-8', errors='replace'):
        if ln.startswith('# zt_timeline'):
            continue
        t, _, text = ln.rstrip('\n').partition('\t')
        try:
            rows.append((float(t), text))
        except ValueError:
            pass
    return rows


def report(path, top):
    rows = read(path)
    if not rows:
        print('empty timeline'); return 1
    total = rows[-1][0]
    print('total %.1f s, %d lines' % (total, len(rows)))
    # gaps: the time before a line appeared, charged to the line before it (the work that line announced)
    gaps = []
    for i in range(1, len(rows)):
        gaps.append((rows[i][0] - rows[i - 1][0], rows[i - 1][0], rows[i - 1][1][:150]))
    gaps.sort(reverse=True)
    print('longest gaps (seconds after the line, at time, line):')
    for g, at, text in gaps[:top]:
        print('  %7.1f  @%7.1f  %s' % (g, at, text))
    # message families: the leading [ LEVEL ][ function ] tag
    fam = {}
    for i in range(1, len(rows)):
        m = re.match(r'\[\s*\w+\s*\]\[\s*([^\]]+?)\s*\]', rows[i - 1][1])
        key = m.group(1) if m else rows[i - 1][1][:40]
        fam[key] = fam.get(key, 0.0) + rows[i][0] - rows[i - 1][0]
    print('time charged per message source:')
    for k, v in sorted(fam.items(), key=lambda kv: -kv[1])[:top]:
        print('  %7.1f  %s' % (v, k))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('follow'); f.add_argument('log'); f.add_argument('out'); f.add_argument('--pid', type=int, default=0)
    f.add_argument('--limit', type=float, default=7200)
    r = sub.add_parser('report'); r.add_argument('timeline'); r.add_argument('--top', type=int, default=12)
    a = ap.parse_args()
    if a.cmd == 'follow':
        follow(a.log, a.out, a.pid, a.limit); return 0
    return report(a.timeline, a.top)


if __name__ == '__main__':
    sys.exit(main())
