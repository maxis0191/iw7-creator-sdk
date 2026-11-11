import json, math, statistics, collections
from q import q
from zones import zones, inside
Z=[z for z in zones]
playable=[z for z in Z if z['name']!='hidden_room']
def vol(z): return 8*z['half'][0]*z['half'][1]*z['half'][2]
def area(z): return 4*z['half'][0]*z['half'][1]
def zone_of(x,y,zc):
    c=[z for z in zc if inside(z,x,y,z_c)] if False else None
def assign(x,y,zv,zs):
    c=[z for z in zs if inside(z,x,y,zv)]
    if not c: return None
    return min(c,key=vol)['name']
def assign_all(x,y,zv,zs):
    return [z['name'] for z in zs if inside(z,x,y,zv)]
out={}
# props
props=q("select x,y,z from smodels")
lights=q("select x,y,z from lights")
pc=collections.Counter(); pci=collections.Counter(); lc=collections.Counter(); lci=collections.Counter()
none_p=0
for x,y,zv in props:
    a=assign(x,y,zv,Z)
    if a: pc[a]+=1
    else: none_p+=1
    for n in assign_all(x,y,zv,Z): pci[n]+=1
none_l=0
for x,y,zv in lights:
    a=assign(x,y,zv,Z)
    if a: lc[a]+=1
    else: none_l+=1
    for n in assign_all(x,y,zv,Z): lci[n]+=1
# spawner counts by target
sp={}
for z in Z:
    if z['target']:
        n=q("select count(*) from ents where targetname=? ",(z['target'],))[0][0]
        sp[z['name']]=n
# dog_spawner (goon/clown/brute locations) by volume
dogs=q("select origin_x,origin_y,origin_z from ents where targetname='dog_spawner'")
dc=collections.Counter(); dnone=0
for x,y,zv in dogs:
    a=assign(x,y,zv,Z)
    if a: dc[a]+=1
    else: dnone+=1
# windows
wins=q("select origin_x,origin_y,origin_z from ents where targetname='window_entrance'")
wc=collections.Counter()
for x,y,zv in wins:
    a=assign(x,y,zv,Z); wc[a]+=1
# player_respawn_loc
rs=q("select origin_x,origin_y,origin_z from ents where targetname='player_respawn_loc'")
rc=collections.Counter()
for x,y,zv in rs:
    rc[assign(x,y,zv,Z)]+=1
idle=q("select origin_x,origin_y,origin_z from ents where targetname='zombie_idle_spot'")
ic=collections.Counter()
for x,y,zv in idle: ic[assign(x,y,zv,Z)]+=1
res=[]
for z in Z:
    n=z['name']
    res.append(dict(zone=n,center=z['center'],size_x=2*z['half'][0],size_y=2*z['half'][1],size_z=2*z['half'][2],
        area_sqin=area(z),area_m2=area(z)*0.0254**2,props_excl=pc[n],props_incl=pci[n],lights_excl=lc[n],lights_incl=lci[n],
        spawners=sp.get(n,0),goon_locs=dc[n],windows=wc[n],respawn=rc[n],idle=ic[n]))
print('unassigned props',none_p,'lights',none_l,'goon none',dnone,'windows none',wc[None],'respawn none',rc[None])
for r in res:
    print(r['zone'], int(r['size_x']),int(r['size_y']),int(r['size_z']), round(r['area_m2']), r['props_excl'],r['props_incl'],r['lights_excl'],r['lights_incl'],r['spawners'],r['goon_locs'],r['windows'],r['respawn'],r['idle'])
json.dump(res,open('<temp>/wk/zoneres.json','w'),indent=1)
