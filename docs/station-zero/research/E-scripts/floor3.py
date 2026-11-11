import sys, math, json, sqlite3, collections
sys.path.insert(0,'<temp>/wk')
import numpy as np
import iw7_world
from zones import zones
dbp='<runtime>/worldkit/cp_zmb.sqlite'
w=iw7_world.World.__new__(iw7_world.World); w.path=dbp
w.con=sqlite3.connect('file:'+dbp+'?mode=ro',uri=True)
w.meta={k:json.loads(v) for k,v in w.con.execute('select key,value from meta')}
Z=[z for z in zones if z['name']!='hidden_room']
centers=np.array([z['center'] for z in Z]); halves=np.array([z['half'] for z in Z]); vols=np.array([8*z['half'][0]*z['half'][1]*z['half'][2] for z in Z])
CELL=32.0
mats=[r[1] for r in w.con.execute('select i,material from surfaces')]
skip=('caulk','nodraw','clip','sky','trigger','shadow')
rng=np.random.default_rng(1)
samples=[]  # (zone, cx, cy, z)
for i,mat in enumerate(mats):
    if any(s in mat for s in skip): continue
    m=w.surface_mesh(i)
    if not m['tris']: continue
    P=np.array(m['positions'],float); T=np.array(m['tris']); vn=np.array(m['normals'],float)
    a=P[T[:,0]];b=P[T[:,1]];c=P[T[:,2]]
    n=np.cross(b-a,c-a); ar=np.linalg.norm(n,axis=1)/2
    upn=(vn[T[:,0],2]+vn[T[:,1],2]+vn[T[:,2],2])/3
    cen=(a+b+c)/3
    d=(np.abs(cen[:,None,:]-centers[None,:,:])<=halves[None,:,:]).all(axis=2)
    sel=(upn>0.7)&(ar>1e-3)&d.any(axis=1)
    for k in np.nonzero(sel)[0]:
        cand=np.nonzero(d[k])[0]; j=cand[np.argmin(vols[cand])]
        ns=int(min(max(1,ar[k]/(CELL*CELL/2)),4000))
        if ns==1:
            pts=cen[k][None,:]
        else:
            r1=rng.random(ns); r2=rng.random(ns); s=np.sqrt(r1)
            pts=(1-s)[:,None]*a[k]+(s*(1-r2))[:,None]*b[k]+(s*r2)[:,None]*c[k]
        for p in pts: samples.append((j,p[0],p[1],p[2]))
print('samples',len(samples))
S=np.array(samples)
res={}
for j,z in enumerate(Z):
    s=S[S[:,0]==j]
    cells=collections.defaultdict(list)
    for _,x,y,zz in s:
        cells[(int(x//CELL),int(y//CELL))].append(zz)
    lv=0
    for k,zs in cells.items():
        zs=sorted(zs); n=1
        for t in range(1,len(zs)):
            if zs[t]-zs[t-1]>96: n+=1
        lv+=n
    res[z['name']]=dict(cells_xy=len(cells),cell_levels=lv,area_xy_m2=len(cells)*CELL*CELL*0.0254**2,area_levels_m2=lv*CELL*CELL*0.0254**2)
    print(z['name'],res[z['name']])
tot_xy=sum(v['area_xy_m2'] for v in res.values()); tot_l=sum(v['area_levels_m2'] for v in res.values())
print('TOTAL xy',tot_xy,'levels',tot_l)
json.dump(dict(per_zone=res,total_xy_m2=tot_xy,total_levels_m2=tot_l,cell=CELL),open('<temp>/wk/floor3.json','w'),indent=1)
