from q import q
import collections
def kvs(i):
    return {b:c for a,b,c in q("select key,key_name,value from ent_kv where i=?",(i,))}
rows=q("""select e.i,e.origin_x,e.origin_y,e.origin_z from ents e join ent_kv k on k.i=e.i and k.key_name='script_noteworthy'
 where e.targetname='interaction' and (k.value like 'debris_%' or k.value='team_door_switch') order by k.value,e.i""")
for r in rows:
    d=kvs(r[0]); print(r[0],[round(x) for x in r[1:]],d)
