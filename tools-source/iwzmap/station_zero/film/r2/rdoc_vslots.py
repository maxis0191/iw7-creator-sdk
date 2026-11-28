"""qrenderdoc --python: draws of a capture that bind more than one vertex buffer (the layer stream of a layered world surface is slot 1). env STUDIO_EXTRACT={Capture,Out,Target}"""
import json, os, traceback
import renderdoc as rd
req = json.loads(open(os.environ["STUDIO_EXTRACT"], encoding="utf-8-sig").read())
log = {"multi": [], "n": 0}
try:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])
    cap = rd.OpenCaptureFile(); assert cap.OpenFile(req["Capture"], "", None) == rd.ResultCode.Succeeded
    st, ctl = cap.OpenCapture(rd.ReplayOptions(), None)
    acts = []
    def walk(a):
        for x in a:
            acts.append(x); walk(x.children)
    walk(ctl.GetRootActions())
    for a in acts:
        if not (a.flags & rd.ActionFlags.Drawcall) or int(req["Target"]) not in [int(o) for o in a.outputs]:
            continue
        ctl.SetFrameEvent(int(a.eventId), True)
        s = ctl.GetPipelineState()
        vb = [(i, int(v.resourceId), int(v.byteStride)) for i, v in enumerate(s.GetVBuffers()) if int(v.resourceId)]
        log["n"] += 1
        if len(vb) > 1:
            ps = s.GetShaderReflection(rd.ShaderStage.Pixel)
            log["multi"].append({"event": int(a.eventId), "indices": a.numIndices, "vb": vb, "inputs": [(x.name, int(x.vertexBuffer)) for x in s.GetVertexInputs()],
                                 "ps_ro": len(ps.readOnlyResources) if ps else None})
    ctl.Shutdown(); cap.Shutdown(); rd.ShutdownReplay()
except Exception:
    log["error"] = traceback.format_exc()
json.dump(log, open(os.path.join(req["Out"], "vslots.json"), "w"), indent=1)
os._exit(0)
