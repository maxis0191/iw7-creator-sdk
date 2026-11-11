import numpy as np, json
from q import q
from zones import zones
Z=zones
T=np.array(q("select cx,cy,cz,surface from tris"))
cent=np.array([z['center'] for z in Z]); half=np.array([z['half'] for z in Z]); vols=8*half.prod(axis=1)
ins=(np.abs(T[:,None,:3]-cent[None])<=half[None]).all(axis=2)
anyin=ins.any(axis=1)
print('tris total',len(T),'in volumes',int(anyin.sum()))
j=np.where(ins,vols[None,:],1e30).argmin(axis=1)
cnt={}
for k,z in enumerate(Z):
    m=anyin&(j==k); cnt[z['name']]=int(m.sum())
print(cnt)
surf=len(set(T[anyin,3].astype(int)))
print('surfaces with >=1 tri centroid in volumes',surf)
# props inside union
P=np.array(q("select x,y,z from smodels"))
insP=(np.abs(P[:,None,:]-cent[None])<=half[None]).all(axis=2).any(axis=1)
print('props in volumes',int(insP.sum()),'bbox of those',P[insP].min(axis=0),P[insP].max(axis=0))
L=np.array(q("select x,y,z from lights"))
insL=(np.abs(L[:,None,:]-cent[None])<=half[None]).all(axis=2).any(axis=1)
print('lights in volumes',int(insL.sum()))
json.dump(cnt,open('tricnt.json','w'))
# distinct models in volumes
mods=q("select model,x,y,z from smodels")
M=np.array([[m[1],m[2],m[3]] for m in mods])
ins2=(np.abs(M[:,None,:]-cent[None])<=half[None]).all(axis=2).any(axis=1)
print('distinct models in volumes',len(set(m[0] for m,k in zip(mods,ins2) if k)))
