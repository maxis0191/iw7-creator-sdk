import json, math, statistics, collections, re
from q import q
vol=json.load(open('<temp>/wk/vol.json'))
vb={r['model']:r['bounds'] for r in vol['rows'] if r.get('bounds')}
sv=q("select i,origin_x,origin_y,origin_z,model,angles from ents where classname='info_volume' and targetname='spawn_volume' order by i")
zones=[]
for i,x,y,z,model,ang in sv:
    kv={b:c for a,b,c in q("select key,key_name,value from ent_kv where i=?",(i,))}
    name=kv['636'].replace('pf7_','')
    b=vb[model]
    yaw=0.0
    if ang:
        p=[float(t) for t in ang.split()]; yaw=p[1]
    zones.append(dict(i=i,name=name,center=(x,y,z),yaw=yaw,ang=ang,half=((b[1][0]-b[0][0])/2,(b[1][1]-b[0][1])/2,(b[1][2]-b[0][2])/2),bmin=b[0],bmax=b[1],target=kv.get('target'),model=model))
def inside(z,px,py,pz,pad=0.0):
    dx,dy,dz=px-z['center'][0],py-z['center'][1],pz-z['center'][2]
    c,s=math.cos(math.radians(-z['yaw'])),math.sin(math.radians(-z['yaw']))
    lx,ly=dx*c-dy*s,dx*s+dy*c
    hx,hy,hz=z['half']
    return abs(lx)<=hx+pad and abs(ly)<=hy+pad and abs(dz)<=hz+pad
if __name__=="__main__":
    for z in zones: print(z['name'],z['center'],z['yaw'],z['ang'],[round(2*h) for h in z['half']])
