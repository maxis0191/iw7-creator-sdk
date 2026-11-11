import json, statistics
z=json.load(open('zoneres.json')); f=json.load(open('floor3.json'))['per_zone']; tr=json.load(open('tricnt.json'))
adj={
'front_gate':[('moon',750)],
'moon':[('front_gate',750),('moon_outside_begin','team 1000xP (moon door)'),('mars','team 1000xP (kepler door)'),('europa_tunnel','team 1000xP (triton door)')],
'moon_outside_begin':[('moon','team 1000xP'),('underground_route',1000),('arcade',1250),('moon_rocket_space',1500)],
'moon_rocket_space':[('moon_bumpercars',1250),('moon_outside_begin',1500)],
'moon_bumpercars':[('moon_rocket_space',1250),('arcade',1250),('underground_route',1250)],
'arcade':[('moon_outside_begin',1250),('moon_bumpercars',1250),('arcade_back',1500)],
'arcade_back':[('arcade',1500),('europa_2',1500)],
'europa_2':[('arcade_back',1500),('europa_tunnel',1250)],
'europa_tunnel':[('europa_2',1250),('swamp_stage',1500),('moon','team 1000xP')],
'swamp_stage':[('underground_route',1250),('europa_tunnel',1500),('mars_3',1500)],
'underground_route':[('moon_outside_begin',1000),('moon_bumpercars',1250),('swamp_stage',1250)],
'mars':[('mars_3',1250),('moon','team 1000xP')],
'mars_3':[('mars',1250),('swamp_stage',1500)],
'hidden_room':[('PAP portal only',0)]}
rows=[]
print('| zone | box W x D x H (units) | box W x D (m) | footprint m2 | props | lights | tris | spawners | goon locs | windows | respawn locs |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for r in z:
    print('| %s | %d x %d x %d | %.1f x %.1f | %.0f | %d | %d | %d | %d | %d | %d | %d |'%(r['zone'],r['size_x'],r['size_y'],r['size_z'],r['size_x']*0.0254,r['size_y']*0.0254,r['area_m2'],r['props_excl'],r['lights_excl'],tr[r['zone']],r['spawners'],r['goon_locs'],r['windows'],r['respawn']))
P=[r for r in z if r['zone']!='hidden_room']
def st(name,vals,fmt='%.1f'):
    print('%s: min %s, median %s, max %s'%(name,fmt%min(vals),fmt%statistics.median(vals),fmt%max(vals)))
st('box footprint m2',[r['area_m2'] for r in P],'%.0f')
st('box footprint sq units',[r['area_sqin'] for r in P],'%.0f')
st('box long side m',[max(r['size_x'],r['size_y'])*0.0254 for r in P])
st('props',[r['props_excl'] for r in P],'%.0f')
st('lights',[r['lights_excl'] for r in P],'%.0f')
st('spawners',[r['spawners'] for r in P],'%.0f')
st('props/1000 sq units',[r['props_excl']/r['area_sqin']*1000 for r in P],'%.3f')
st('props/100 m2',[r['props_excl']/r['area_m2']*100 for r in P],'%.1f')
st('lights/100 m2',[r['lights_excl']/r['area_m2']*100 for r in P],'%.2f')
st('lights/1000 sq units',[r['lights_excl']/r['area_sqin']*1000 for r in P],'%.4f')
print()
print('| zone | props/1000 sq u | props/100 m2 (box) | lights/100 m2 (box) | surface-covered floor XY m2 | multi-level floor m2 | props per 100 m2 of floor XY |')
print('|---|---|---|---|---|---|---|')
for r in P:
    fz=f[r['zone']]
    print('| %s | %.3f | %.1f | %.2f | %.0f | %.0f | %.1f |'%(r['zone'],r['props_excl']/r['area_sqin']*1000,r['props_excl']/r['area_m2']*100,r['lights_excl']/r['area_m2']*100,fz['area_xy_m2'],fz['area_levels_m2'],r['props_excl']/fz['area_xy_m2']*100))
st('props/100m2 floorXY',[r['props_excl']/f[r['zone']]['area_xy_m2']*100 for r in P],'%.1f')
st('floor XY m2',[f[r['zone']]['area_xy_m2'] for r in P],'%.0f')
st('lights/100m2 floorXY',[r['lights_excl']/f[r['zone']]['area_xy_m2']*100 for r in P],'%.2f')
print('totals playable: props',sum(r['props_excl'] for r in P),'lights',sum(r['lights_excl'] for r in P),'tris',sum(tr[r['zone']] for r in P),'spawners',sum(r['spawners'] for r in P))
