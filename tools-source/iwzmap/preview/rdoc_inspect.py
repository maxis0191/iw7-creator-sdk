"""Run through qrenderdoc --python (offline replay of an existing .rdc, no game): dump what chosen events used.

Request (IWZ_RDOC_INSPECT env, path of a JSON file):
  Capture, Out (JSON), Work (folder), Events: [ids] (draws or dispatches),
  List: true -> every draw and dispatch (event, shader hashes, targets) in Out.list,
  Dispatches: [ids] the events of Events that are compute dispatches (a draw keeps a stale cs bound),
  Shaders: true -> DXBC disassembly of every shader of the events (deduped by SHA-256 of the bytecode, written to
           Work/shader_<sha12>_<stage>.txt),
  Dump: [[event, resource id], ...] -> raw bytes of mip 0 of that resource as it is at that event
           (Work/res_<id>_ev<event>.bin; format and size in Out),
  DumpBuffers: [[event, resource id, size], ...] raw buffer bytes.
Out lists per event: the shaders, every constant buffer (all float4 rows), SRV and UAV bindings (resource, size, format),
samplers, render targets, blend state. The reader of these files is the analysis scripts of the preview (see README).
"""
import hashlib
import json
import os
import struct
import sys
import traceback

import renderdoc as rd

try:
    req = json.loads(open(os.environ["IWZ_RDOC_INSPECT"], encoding="utf-8-sig").read())
except Exception:
    open(os.environ.get("IWZ_RDOC_INSPECT", "rdoc_inspect_error") + ".err", "w").write(traceback.format_exc())
    sys.exit(1)
report = {"capture": req["Capture"], "success": False, "events": {}}
STAGES = {"vs": rd.ShaderStage.Vertex, "ps": rd.ShaderStage.Pixel, "cs": rd.ShaderStage.Compute}
work = req["Work"]
os.makedirs(work, exist_ok=True)
try:
    rd.InitialiseReplay(rd.GlobalEnvironment(), [])
    cap = rd.OpenCaptureFile()
    assert cap.OpenFile(req["Capture"], "", None) == rd.ResultCode.Succeeded
    status, ctl = cap.OpenCapture(rd.ReplayOptions(), None)
    assert status == rd.ResultCode.Succeeded, status
    texinfo = {int(t.resourceId): t for t in ctl.GetTextures()}
    bufinfo = {int(b.resourceId): b for b in ctl.GetBuffers()}
    targets = ctl.GetDisassemblyTargets(True)
    report["disasm_targets"] = list(targets)
    target = next((t for t in targets if "DXBC" in t), targets[0])
    done = set()
    events = [int(e) for e in req.get("Events", [])]
    if req.get("List"):
        acts = []

        def walk(items):
            for a in items:
                if a.children:
                    walk(a.children)
                elif a.flags & (rd.ActionFlags.Drawcall | rd.ActionFlags.Dispatch):
                    acts.append(a)
        walk(ctl.GetRootActions())
        listing = []
        for a in acts:
            ctl.SetFrameEvent(a.eventId, False)
            st = ctl.GetPipelineState()
            row = {"e": a.eventId, "disp": bool(a.flags & rd.ActionFlags.Dispatch), "n": a.numIndices, "inst": a.numInstances}
            for label, stage in STAGES.items():
                if label == "cs" and not row["disp"]:
                    continue
                sid = st.GetShader(stage)
                if sid != rd.ResourceId.Null():
                    refl = st.GetShaderReflection(stage)
                    row[label] = hashlib.sha256(bytes(refl.rawBytes)).hexdigest()[:12]
            row["rt"] = [int(o.resource) for o in st.GetOutputTargets() if o.resource != rd.ResourceId.Null()]
            listing.append(row)
        report["list"] = listing
    dispatches = set(int(e) for e in req.get("Dispatches", []))
    dump = {}
    for e, rid in req.get("Dump", []):
        dump.setdefault(int(e), []).append(int(rid))
    dumpb = {}
    for e, rid, sz in req.get("DumpBuffers", []):
        dumpb.setdefault(int(e), []).append((int(rid), int(sz)))
    for ev in sorted(set(events) | set(dump) | set(dumpb)):
        ctl.SetFrameEvent(ev, True)
        st = ctl.GetPipelineState()
        item = {"shaders": {}, "cb": {}, "srv": {}, "uav": {}, "samplers": {}, "targets": [], "dumps": []}
        for label, stage in STAGES.items():
            sid = st.GetShader(stage)
            if sid == rd.ResourceId.Null():
                continue
            refl = st.GetShaderReflection(stage)
            sha = hashlib.sha256(bytes(refl.rawBytes)).hexdigest()
            item["shaders"][label] = sha
            if ev in events and req.get("Shaders") and (sha, label) not in done:
                done.add((sha, label))
                pipe = st.GetComputePipelineObject() if label == "cs" else st.GetGraphicsPipelineObject()
                txt = ctl.DisassembleShader(pipe, refl, target)
                open(os.path.join(work, "shader_%s_%s.txt" % (sha[:12], label)), "w", encoding="utf-8").write(txt)
            if ev not in events:
                continue
            if label == "cs" and ev not in dispatches:
                continue
            for used in st.GetConstantBlocks(stage):
                if used.access.index >= len(refl.constantBlocks):
                    continue
                cb = refl.constantBlocks[used.access.index]
                d = used.descriptor
                size = d.byteSize or 4096
                data = bytes(ctl.GetBufferData(d.resource, d.byteOffset, size))
                rows = [list(struct.unpack_from("<4f", data, 16 * i)) for i in range(len(data) // 16)]
                item["cb"]["%s:cb%d" % (label, cb.fixedBindNumber)] = {"id": int(d.resource), "rows": rows}
            for used in st.GetReadOnlyResources(stage):
                if used.access.index >= len(refl.readOnlyResources):
                    continue
                r = refl.readOnlyResources[used.access.index]
                rid = int(used.descriptor.resource)
                t = texinfo.get(rid)
                item["srv"]["%s:t%d" % (label, r.fixedBindNumber)] = (
                    {"id": rid, "w": t.width, "h": t.height, "format": t.format.Name(), "mips": t.mips,
                     "first_mip": used.descriptor.firstMip} if t else {"id": rid, "kind": "buffer"})
            for used in st.GetReadWriteResources(stage):
                if used.access.index >= len(refl.readWriteResources):
                    continue
                r = refl.readWriteResources[used.access.index]
                rid = int(used.descriptor.resource)
                t = texinfo.get(rid)
                item["uav"]["%s:u%d" % (label, r.fixedBindNumber)] = (
                    {"id": rid, "w": t.width, "h": t.height, "format": t.format.Name()} if t else
                    {"id": rid, "kind": "buffer"})
            for i, used in enumerate(st.GetSamplers(stage)):
                if used.access.index >= len(refl.samplers):
                    continue
                try:
                    s = used.sampler
                    val = {"filter": str(s.filter), "addr": [str(s.addressU), str(s.addressV)],
                           "mipbias": s.mipBias, "compare": str(s.compareFunction)}
                except Exception as ex:
                    val = {"error": str(ex)}
                item["samplers"]["%s:s%d" % (label, refl.samplers[used.access.index].fixedBindNumber)] = val
        for o in st.GetOutputTargets():
            if o.resource != rd.ResourceId.Null():
                t = texinfo.get(int(o.resource))
                item["targets"].append({"id": int(o.resource), "w": t.width, "h": t.height, "format": t.format.Name()})
        for rid in dump.get(ev, []):
            t = texinfo[rid]
            res = [r for r in ctl.GetResources() if int(r.resourceId) == rid][0]
            raw = bytes(ctl.GetTextureData(res.resourceId, rd.Subresource(0, 0, 0)))
            p = os.path.join(work, "res_%d_ev%d.bin" % (rid, ev))
            open(p, "wb").write(raw)
            item["dumps"].append({"id": rid, "path": p, "bytes": len(raw), "w": t.width, "h": t.height,
                                  "format": t.format.Name()})
        for rid, sz in dumpb.get(ev, []):
            res = [r for r in ctl.GetResources() if int(r.resourceId) == rid][0]
            raw = bytes(ctl.GetBufferData(res.resourceId, 0, sz))
            p = os.path.join(work, "buf_%d_ev%d.bin" % (rid, ev))
            open(p, "wb").write(raw)
            item["dumps"].append({"id": rid, "path": p, "bytes": len(raw), "kind": "buffer"})
        report["events"][str(ev)] = item
    ctl.Shutdown()
    cap.Shutdown()
    rd.ShutdownReplay()
    report["success"] = True
except Exception:
    report["error"] = traceback.format_exc()
json.dump(report, open(req["Out"], "w", encoding="utf-8"))
sys.exit(0)
