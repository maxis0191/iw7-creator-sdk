"""Frame time with the train kit shown vs hidden, from a run's Present-sampler perf log and the fixture's markers.

usage: train_perf.py <run dir>   (reads <run dir>.perf.log, <run dir>/client.stdout.log, <run dir>/engine-errors.log)
Clock alignment: the journal's last 'connState=9 cgameInit=1' tick (ms) is taken as the fixture's CONNECTED gettime;
PERF_BEGIN/END gettimes then map onto perf-log ticks; the first and last second of each window are dropped.
Perf rows: 'tick frames p50 p95 p99 max' per second (gameplay agent's journal DLL).
"""
import os, re, statistics, sys

run = sys.argv[1].rstrip('/\\')
rows = [l.split() for l in open(run + '.perf.log') if len(l.split()) == 6]
rows = [(int(r[0]), int(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in rows]
jt = [int(m.group(1)) for m in re.finditer(r'\[(\d+)\] client active=1 keyCatchers=\d+ connState=9 cgameInit=1',
                                            open(os.path.join(run, 'engine-errors.log'), errors='replace').read())]
log = open(os.path.join(run, 'client.stdout.log'), errors='replace').read()
con = int(re.search(r'\[IWZ train\] CONNECTED t=(\d+)', log).group(1))
base = jt[-1] - con
wins = re.findall(r'PERF_BEGIN shown=(\d) t=(\d+).*?PERF_END shown=\d t=(\d+)', log, re.S)
for shown, b, e in wins:
    t0, t1 = base + int(b) + 1000, base + int(e) - 1000
    sel = [r for r in rows if t0 <= r[0] <= t1 and r[1] > 0]
    if not sel:
        print('shown=%s: no samples' % shown); continue
    med = lambda k: statistics.median(r[k] for r in sel)
    print('kit shown=%s: %d s, median p50 %.2f ms (%.0f fps), p95 %.2f ms, p99 %.2f ms, worst %.1f ms'
          % (shown, len(sel), med(2), 1000 / med(2), med(3), med(4), max(r[5] for r in sel)))
