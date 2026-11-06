import sys,os,struct; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from hkpack import Packfile
pf=Packfile(open(sys.argv[1],'rb').read()); b=pf.data_sec.body
d=[a for a,n,_ in pf.objects if n=='hknpCompressedMeshShapeData'][0]
dmn=struct.unpack_from('<3f',b,d+0x20); dmx=struct.unpack_from('<3f',b,d+0x30); span=[dmx[k]-dmn[k] for k in range(3)]
sec_p,NSEC,_=pf.array(d+0x50); prim_p,_,_=pf.array(d+0x60); svi_p,_,_=pf.array(d+0x70); sv_p,_,_=pf.array(d+0x90)
def shared(i):
    v=struct.unpack_from('<Q',b,sv_p+8*i)[0]; q=(v&0x1FFFFF,(v>>21)&0x1FFFFF,(v>>42)&0x3FFFFF)
    return [dmn[k]+q[k]*span[k]/(0x1FFFFF if k<2 else 0x3FFFFF) for k in range(3)]
def tri(key):
    s=key>>8; pi=(key&0xFF)>>1; t=key&1
    so=sec_p+96*s; shv,prims=struct.unpack_from('<II',b,so+76); page=b[so+92]
    if pi>=(prims&0xFF): return None
    idx=b[prim_p+4*((prims>>8)+pi):prim_p+4*((prims>>8)+pi)+4]
    vs=[shared((page<<16)|struct.unpack_from('<H',b,svi_p+2*((shv>>8)+k))[0]) for k in idx]
    return [vs[0],vs[1],vs[2]] if t==0 else [vs[0],vs[2],vs[3]]
p,n,_=pf.array(d+0xB8)
import collections
res=collections.Counter(); vals=collections.Counter()
for i in range(1,min(n,20000)):
    o=p+112*i; f=struct.unpack_from('<24f',b,o); data=struct.unpack_from('<4I',b,o+96)
    for j in range(4):
        lo=(f[j],f[8+j],f[16+j]); hi=(f[4+j],f[12+j],f[20+j])
        if lo[0]>hi[0]: res['empty']+=1; continue
        v=data[j]
        if v < n: res['internal?']+=1; vals['int_odd' if v&1 else 'int_even']+=1; continue
        for name,key in (('raw',v),('shr1',v>>1)):
            t=tri(key) if (key>>8)<NSEC else None
            ok = t is not None and all(lo[a]-0.6<=x[a]<=hi[a]+0.6 for x in t for a in range(3))
            res[name+('_ok' if ok else '_bad')]+=1
print(n, res, vals)
# hypothesis B: even -> internal node (v>>1), odd -> leaf key (v>>1); walk from root 1
res=collections.Counter(); seen=set(); stack=[1]; leaves=0
while stack:
    i=stack.pop()
    if i in seen: res['revisit']+=1; continue
    seen.add(i); o=p+112*i; f=struct.unpack_from('<24f',b,o); data=struct.unpack_from('<4I',b,o+96)
    for j in range(4):
        lo=(f[j],f[8+j],f[16+j]); hi=(f[4+j],f[12+j],f[20+j])
        if lo[0]>hi[0]: res['empty']+=1; continue
        v=data[j]
        if v&1:
            t=tri(v>>1); leaves+=1
            ok=t is not None and all(lo[a]-0.6<=x[a]<=hi[a]+0.6 for x in t for a in range(3))
            res['leaf_ok' if ok else 'leaf_bad']+=1
        else:
            c=v>>1; stack.append(c)
            cf=struct.unpack_from('<24f',b,p+112*c)
            inside=all(cf[k]>=lo[0]-0.6 or cf[k]>3e38 for k in range(4))
            res['child_inside' if inside else 'child_out']+=1
print('B', res, 'visited', len(seen), 'leaves', leaves)
