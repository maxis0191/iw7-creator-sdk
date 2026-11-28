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
        if not (a.flags & rd.ActionFlags.Drawcall) or (int(req["Target"]) and int(req["Target"]) not in [int(o) for o in a.outputs]):
            continue
        ctl.SetFrameEvent(int(a.eventId), True)
        s = ctl.GetPipelineState()
        vb = [(i, int(v.resourceId), int(v.byteStride)) for i, v in enumerate(s.GetVBuffers()) if int(v.resourceId)]
        log["n"] += 1
        if len(vb) > 1:
            ps = s.GetShaderReflection(rd.ShaderStage.Pixel)
            px = None
            try:
                import struct
                mesh = ctl.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
                vbd = ctl.GetBufferData(mesh.vertexResourceId, mesh.vertexByteOffset, 0)
                ibd = ctl.GetBufferData(mesh.indexResourceId, mesh.indexByteOffset, 0)
                fmt = "<%dH" % (len(ibd) // 2) if mesh.indexByteStride == 2 else "<%dI" % (len(ibd) // 4)
                idx = [i + mesh.baseVertex for i in struct.unpack(fmt, ibd)[: mesh.numIndices]]
                W, H = req.get("W", 1280), req.get("H", 720)
                for t in range(0, len(idx) - 2, 3):
                    ps3 = [struct.unpack_from("<4f", vbd, idx[t + k] * mesh.vertexByteStride) for k in range(3)]
                    if all(p[3] > 1e-3 for p in ps3):
                        sx = [(p[0] / p[3] * 0.5 + 0.5) * W for p in ps3]
                        sy = [(1 - (p[1] / p[3] * 0.5 + 0.5)) * H for p in ps3]
                        cx, cy = sum(sx) / 3, sum(sy) / 3
                        if 0 <= cx < W and 0 <= cy < H:
                            px = [round(cx), round(cy)]
                            break
            except Exception:
                px = None
            log["multi"].append({"px": px, "event": int(a.eventId), "indices": a.numIndices, "vb": vb, "inputs": [(x.name, int(x.vertexBuffer)) for x in s.GetVertexInputs()],
                                 "ps_ro": len(ps.readOnlyResources) if ps else None})
    ctl.Shutdown(); cap.Shutdown(); rd.ShutdownReplay()
except Exception:
    log["error"] = traceback.format_exc()
json.dump(log, open(os.path.join(req["Out"], "vslots.json"), "w"), indent=1)
os._exit(0)
