import json, os, traceback
import renderdoc as rd
req = json.loads(open(os.environ["STUDIO_EXTRACT"], encoding="utf-8-sig").read())
log = {"rows": []}
try:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])
    cap = rd.OpenCaptureFile(); assert cap.OpenFile(req["Capture"], "", None) == rd.ResultCode.Succeeded
    st, ctl = cap.OpenCapture(rd.ReplayOptions(), None)
    sf = ctl.GetStructuredFile()
    acts = []
    def walk(a):
        for x in a:
            acts.append(x); walk(x.children)
    walk(ctl.GetRootActions())
    for a in acts:
        if a.flags & (rd.ActionFlags.Drawcall | rd.ActionFlags.Dispatch | rd.ActionFlags.Clear):
            log["rows"].append([int(a.eventId), a.GetName(sf)[:70], int(a.flags), a.numIndices, a.numInstances, [int(o) for o in a.outputs if int(o)][:4]])
    ctl.Shutdown(); cap.Shutdown(); rd.ShutdownReplay()
except Exception:
    log["error"] = traceback.format_exc()
json.dump(log, open(os.path.join(req["Out"], "enum.json"), "w"))
os._exit(0)
