"""Bounded output adapter INSIDE the coordinator's existing Windows job.

This is not an ownership/admission API. Build-BeaconFF.ps1 owns the whole tree.
It starts only a pinned ZoneTool phase or the pinned original geometry reader.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time

LIMIT = 2 * 1024 * 1024


def copy_bounded(source, destination, exceeded, limit=LIMIT):
    written = 0
    try:
        while True:
            block = source.read(4096)
            if not block:
                break
            keep = block[:max(0, limit - written)]
            if keep:
                destination.write(keep)
                destination.flush()
                written += len(keep)
            if len(keep) != len(block):
                exceeded.set()
    except OSError:
        # Includes disk/pipe errors: never silently accept a dead drain thread.
        exceeded.set()
    return written


def command(phase, executable, work, roundtrip):
    if phase == "read":
        return [executable, "--verify-existing", roundtrip]
    verbs = {"build": "-buildzone", "verify": "-verifyzone", "dump": "-dumpzone"}
    return [executable, "-headless", "-unbuffered-io", "-strict-content-sources", verbs[phase], "sdk_beacon"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("build", "verify", "dump", "read"), required=True)
    parser.add_argument("--exe", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--logs", required=True)
    parser.add_argument("--roundtrip", required=True)
    args = parser.parse_args()
    exe = Path(args.exe)
    if hashlib.sha256(exe.read_bytes()).hexdigest() != args.sha256.lower():
        raise ValueError("Pinned executable changed before phase")
    out = Path(args.logs)
    if out.exists():
        raise ValueError("Fresh phase log directory required")
    out.mkdir()
    exceeded = threading.Event()
    workers = []
    failure = None
    # Native descendants inherit the outer non-breakaway job; never use shell.
    process = subprocess.Popen(command(args.phase, str(exe), args.work, args.roundtrip),
                               cwd=args.work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=0x08000000 if os.name == "nt" else 0)
    handles = []
    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        target = (out / (name + ".log")).open("xb")
        handles.append(target)
        thread = threading.Thread(target=copy_bounded, args=(stream, target, exceeded), daemon=True)
        thread.start()
        workers.append(thread)
    deadline = time.monotonic() + (30 if args.phase == "read" else 240)
    while process.poll() is None:
        if exceeded.is_set() or time.monotonic() >= deadline:
            failure = "log bound or output error" if exceeded.is_set() else "phase timeout"
            break
        time.sleep(0.05)
    if failure is None:
        for thread in workers:
            thread.join(2)
        if exceeded.is_set():
            failure = "log bound or output error"
        elif any(t.is_alive() for t in workers):
            failure = "inherited output pipe remains open"
    result = {"schema": "iw7.beacon-tool-phase/1", "phase": args.phase,
              "pid": process.pid, "exit_code": process.poll(), "failure": failure,
              "log_limit_each": LIMIT, "ownership": "outer Windows job"}
    (out / "phase.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failure:
        # Do not kill by PID or declare closure. Parent observes our nonzero
        # exit, stops its original job and requires zero active members.
        os._exit(2)
    for handle in handles:
        handle.close()
    return 0 if process.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
