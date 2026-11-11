import json, collections
from q import q
from zones import zones, inside
Z=zones
def vol(z): return 8*z['half'][0]*z['half'][1]*z['half'][2]
def zone_at(x,y,z):
    c=[v for v in Z if inside(v,x,y,z)]
    return min(c,key=vol)['name'] if c else None
rows=q("""select e.i,e.classname,e.origin_x,e.origin_y,e.origin_z,k.value from ents e join ent_kv k on k.i=e.i and k.key_name='script_noteworthy' where e.targetname='interaction' order by k.value,e.i""")
def area_of(i):
    r=q("select value from ent_kv where i=? and key_name='area'",(i,))
    return r[0][0] if r else None
by=collections.defaultdict(list)
for i,cl,x,y,z,v in rows:
    by[v].append((i,cl,round(x),round(y),round(z),area_of(i),zone_at(x,y,z)))
import sys
def show(prefix=None,names=None):
    for k in sorted(by):
        if (names and k in names) or (prefix and k.startswith(prefix)):
            print(k,len(by[k]),[(a[2],a[3],a[4],a[5] or a[6]) for a in by[k]])
if __name__=="__main__":
    show(prefix='perk_machine')
    print('--- weapons')
    for k in sorted(by):
        if k.startswith('iw7_') or k.startswith('zfreeze') or k.startswith('power_'):
            print(k,len(by[k]),[(a[5] or a[6]) for a in by[k]])
    print('--- others')
    for k in ['weapon_upgrade','pap_upgrade','fast_travel','generator','rockettrap','beamtrap','interaction_discoballtrap','scrambler','blackhole_trap','crafting_station','lost_and_found','jaroslav_machine','atm_deposit','atm_withdrawal','ark_quest_station','coaster','laughingclown','bowling_for_planets','clown_tooth_game','basketball_game','game_race','shooting_gallery','neil_head','neil_repair','wor_standee','gold_teeth','arcade_counter_ammo','arcade_counter_grenade','dj_quest_door','dj_quest_speaker','neil_battery','neil_firmware','dj_quest_part_1','secure_window']:
        if k in by: print(k,len(by[k]),collections.Counter([(a[5] or a[6]) for a in by[k]]))
    wf=q("select origin_x,origin_y,origin_z from ents where targetname='wheel_fx_spot'")
    print('wheels',[(round(x),round(y),round(z),zone_at(x,y,z)) for x,y,z in wf])
