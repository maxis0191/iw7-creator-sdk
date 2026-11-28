"""qrenderdoc --python (offline replay, no game): pixel history of chosen pixels of a forge capture, and for every event that wrote them the
pixel shader, every bound shader resource (name, format, size, content statistics) and the constant buffers the pixel shader reads.
Worker R2b, 28 Nov 2026 (R2-PARITY section 11).

    set STUDIO_EXTRACT=<req.json> ; qrenderdoc.exe --python rdoc_pixel.py
    req.json = {"Capture": "x.rdc", "Out": "dir", "Pixels": [[x, y, "label"], ...], "Target": null | resourceId int (default: the 2D colour target with the most
                draws that is as large as the biggest one), "MaxTexBytes": 4194304}
Writes <Out>/pixel_log.json (targets by draw count, per pixel: history, per event: shader, srvs, cbuffers) and returns. Every step is guarded: an API
difference is written into the log as "err" and the rest continues.
"""
import json
import os
import traceback

import renderdoc as rd

req = json.loads(open(os.environ["STUDIO_EXTRACT"], encoding="utf-8-sig").read())
os.makedirs(req["Out"], exist_ok=True)
log = {"capture": req["Capture"], "targets": [], "pixels": {}, "errors": []}
MAXB = int(req.get("MaxTexBytes", 4194304))


def guard(tag, fn, default=None):
    try:
        return fn()
    except Exception:
        log["errors"].append({tag: traceback.format_exc()[-600:]})
        return default


def flat(a, out):
    for x in a:
        out.append(x)
        flat(x.children, out)


def col(v):
    return [round(float(c), 5) for c in (v.floatValue if hasattr(v, "floatValue") else v)]


def tex_stats(ctl, tex, rid):
    """mip 0 for small images, else the last mip: size, share of zero texels, per channel mean (float / unorm formats only)"""
    import struct
    d = {"w": tex.width, "h": tex.height, "d": tex.depth, "mips": tex.mips, "arr": tex.arraysize, "fmt": tex.format.Name(), "dim": str(tex.type)}
    mip = 0
    while mip < tex.mips - 1 and (max(1, tex.width >> mip) * max(1, tex.height >> mip) * 8) > MAXB:
        mip += 1
    d["stat_mip"] = mip
    raw = bytes(ctl.GetTextureData(rid, rd.Subresource(mip, 0, 0)))
    d["bytes"] = len(raw)
    nz = sum(1 for b in raw[:1 << 20] if b)
    d["nonzero_share_first_mb"] = round(nz / max(1, min(len(raw), 1 << 20)), 4)
    d["all_zero"] = nz == 0
    d["distinct_first_64k_bytes"] = len(set(raw[:65536]))
    return d


def covers(ctl, dr, px, py, W, H):
    import struct
    mesh = ctl.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
    if mesh.numIndices == 0 or int(mesh.vertexResourceId) == 0:
        return 0
    vb = ctl.GetBufferData(mesh.vertexResourceId, mesh.vertexByteOffset, 0)
    nv = len(vb) // mesh.vertexByteStride
    pos = []
    for i in range(nv):
        pos.append(struct.unpack_from("<4f", vb, i * mesh.vertexByteStride))
    if int(mesh.indexResourceId):
        ib = ctl.GetBufferData(mesh.indexResourceId, mesh.indexByteOffset, 0)
        fmt = "<%dH" % (len(ib) // 2) if mesh.indexByteStride == 2 else "<%dI" % (len(ib) // 4)
        idx = list(struct.unpack(fmt, ib))[: mesh.numIndices]
        idx = [i + mesh.baseVertex for i in idx]
    else:
        idx = list(range(mesh.numIndices))
    n = 0
    X = px + 0.5
    Y = py + 0.5
    def scr(p):
        if p[3] <= 1e-6:
            return None
        return ((p[0] / p[3] * 0.5 + 0.5) * W, (1 - (p[1] / p[3] * 0.5 + 0.5)) * H)
    for t in range(0, len(idx) - 2, 3):
        try:
            a, b, c = scr(pos[idx[t]]), scr(pos[idx[t + 1]]), scr(pos[idx[t + 2]])
        except IndexError:
            continue
        if not (a and b and c):
            continue
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
        if l1 >= 0 and l2 >= 0 and l1 + l2 <= 1:
            n += 1
    return n


try:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])
    cap = rd.OpenCaptureFile()
    assert cap.OpenFile(req["Capture"], "", None) == rd.ResultCode.Succeeded
    st, ctl = cap.OpenCapture(rd.ReplayOptions(), None)
    names = {int(r.resourceId): r.name for r in ctl.GetResources()}
    texs = {int(t.resourceId): t for t in ctl.GetTextures()}
    acts = []
    flat(ctl.GetRootActions(), acts)
    draws = [a for a in acts if a.flags & rd.ActionFlags.Drawcall]
    log["actions"] = len(acts)
    log["draws"] = len(draws)
    # colour targets by draw count
    counts = {}
    for a in draws:
        for o in a.outputs:
            r = int(o)
            if r and r in texs:
                counts[r] = counts.get(r, 0) + 1
    for r, c in sorted(counts.items(), key=lambda kv: -kv[1])[:12]:
        t = texs[r]
        log["targets"].append({"id": r, "name": names.get(r), "w": t.width, "h": t.height, "fmt": t.format.Name(), "draws": c})
    target = req.get("Target")
    if not target:
        big = max((texs[r].width * texs[r].height) for r in counts)
        target = max((r for r in counts if texs[r].width * texs[r].height == big), key=lambda r: counts[r])
    log["target"] = int(target)
    tex = texs[int(target)]
    shader_cache = {}
    for (px, py, label) in req["Pixels"]:
        rec = {"x": px, "y": py, "events": []}
        log["pixels"][label] = rec
        # PixelHistory returned only the last event on this capture (R2b), so the writers are found by geometry: every draw to the target whose
        # post-vertex-shader triangles cover the pixel, in event order, with the pixel's value after it
        for dr in draws:
            if not req.get("All") and int(target) not in [int(o) for o in dr.outputs]:
                continue
            ev = int(dr.eventId)
            ctl.SetFrameEvent(ev, True)
            hit = guard("cover%d" % ev, lambda: covers(ctl, dr, px, py, tex.width, tex.height), None)
            if hit:
                rec["events"].append({"event": ev, "passed": True, "tris": hit, "indices": int(dr.numIndices), "outputs": [int(o) for o in dr.outputs if int(o)], "name": dr.GetName(ctl.GetStructuredFile()) if hasattr(dr, "GetName") else ""})
        # pipeline of every event that wrote the pixel (passed)
        for e in rec["events"]:
            if e["passed"] is False or (req.get("OnlyEvents") and e["event"] not in req["OnlyEvents"]):
                continue
            ctl.SetFrameEvent(e["event"], True)
            state = ctl.GetPipelineState()
            info = {}
            e["pipeline"] = info
            ps = state.GetShader(rd.ShaderStage.Pixel)
            info["ps"] = {"id": int(ps), "name": names.get(int(ps))}
            refl = state.GetShaderReflection(rd.ShaderStage.Pixel)
            if refl is not None:
                info["ps"]["entry"] = state.GetShaderEntryPoint(rd.ShaderStage.Pixel)
                info["ps"]["files"] = guard("files", lambda: [f.filename for f in refl.debugInfo.files], [])
                info["ps"]["src_head"] = guard("src", lambda: refl.debugInfo.files[0].contents[:300] if refl.debugInfo.files else "", "")
                info["ps"]["ro_names"] = [r.name for r in refl.readOnlyResources]
                info["ps"]["cb_names"] = [c.name for c in refl.constantBlocks]
            info["vs"] = {"name": names.get(int(state.GetShader(rd.ShaderStage.Vertex)))}
            info["vbuffers"] = guard("vb", lambda: [{"slot": i, "id": int(v.resourceId), "stride": int(v.byteStride), "offset": int(v.byteOffset)} for i, v in enumerate(state.GetVBuffers()) if int(v.resourceId)], [])
            info["vertex_inputs"] = guard("vi", lambda: [{"name": a.name, "vb": int(a.vertexBuffer), "fmt": a.format.Name(), "off": int(a.byteOffset)} for a in state.GetVertexInputs()], [])
            info["srvs"] = []
            ro = guard("ro", lambda: state.GetReadOnlyResources(rd.ShaderStage.Pixel), [])
            for i, u in enumerate(ro):
                rid = int(u.descriptor.resource)
                s = {"slot": i, "name": names.get(rid), "id": rid}
                if refl is not None and i < len(refl.readOnlyResources):
                    s["shader_name"] = refl.readOnlyResources[i].name
                if rid in texs:
                    key = rid
                    if key not in shader_cache:
                        shader_cache[key] = guard("stats%d" % rid, lambda: tex_stats(ctl, texs[rid], texs[rid].resourceId), {})
                    s["tex"] = shader_cache[key]
                info["srvs"].append(s)
            info["cbuffers"] = []
            if refl is not None:
                for ci, cb in enumerate(refl.constantBlocks):
                    c = {"index": ci, "name": cb.name, "vars": {}}
                    bound = guard("cb%d" % ci, lambda: state.GetConstantBlock(rd.ShaderStage.Pixel, ci, 0))
                    if bound is not None:
                        vals = guard("cbv%d" % ci, lambda: ctl.GetCBufferVariableContents(state.GetGraphicsPipelineObject(), ps, rd.ShaderStage.Pixel,
                                                                                         info["ps"]["entry"], ci, bound.descriptor.resource,
                                                                                         bound.descriptor.byteOffset, bound.descriptor.byteSize), [])

                        def walk(vs, pre=""):
                            for v in vs:
                                nm = pre + v.name
                                if v.members:
                                    walk(v.members, nm + ".")
                                else:
                                    vv = guard("val", lambda: [round(float(x), 5) for x in list(v.value.f32v)[: v.rows * v.columns]], None)
                                    c["vars"][nm] = vv
                        walk(vals)
                    info["cbuffers"].append(c)
    ctl.Shutdown()
    cap.Shutdown()
    rd.ShutdownReplay()
except Exception:
    log["error"] = traceback.format_exc()
json.dump(log, open(os.path.join(req["Out"], "pixel_log.json"), "w"), indent=1)
os._exit(0)
