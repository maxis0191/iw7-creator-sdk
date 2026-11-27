"""Run several image generations in parallel (one background command, one wait).

usage: python gen.py <batch.json> [--workers 6]
batch.json: [{"name": "logo_needle_drop", "transparent": true, "images": [...], "edit": false}, ...]
The prompt is read from ../prompts/<prompt or name>.prompt.txt; the raw output goes to
C:/studio-data/sz/film/art/_raw/<name>.png (the generator never overwrites: -v2, -v3 ...).
A summary line per job is printed and written next to the batch file as <batch>.result.json.
"""
import json, subprocess, sys, time, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
PROMPTS = HERE.parent / "prompts"
RAW = pathlib.Path("C:/studio-data/sz/film/art/_raw")
GEN = pathlib.Path.home() / ".claude/skills/imagegen/scripts/codex_imagegen.py"


def run(job):
    name = job["name"]
    pf = PROMPTS / f"{job.get('prompt', name)}.prompt.txt"
    cmd = [sys.executable, str(GEN), "--prompt-file", str(pf), "--out", str(RAW / f"{name}.png")]
    for im in job.get("images", []):
        cmd += ["-i", im]
    if job.get("edit"):
        cmd.append("--edit")
    if job.get("n"):
        cmd += ["-n", str(job["n"])]
    if job.get("transparent"):
        cmd.append("--transparent")
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {}
    except Exception:
        try:
            res = json.loads(p.stdout)
        except Exception:
            res = {"ok": False, "error": p.stdout[-400:] + p.stderr[-400:]}
    out = {"name": name, "ok": res.get("ok"), "images": res.get("images"), "s": round(time.time() - t),
           "error": (res.get("error") or "") + (": " + res["codex_errors"][0] if res.get("codex_errors") else "")
           or None}
    print(json.dumps(out), flush=True)
    return out


def main():
    batch = pathlib.Path(sys.argv[1])
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    jobs = json.loads(batch.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(run, jobs))
    batch.with_suffix(".result.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
