from q import q
rows=q("select i,classname,targetname,origin_x,origin_y,origin_z from ents where targetname='door_buy' order by i")
for r in rows:
    kv=q("select key,key_name,value from ent_kv where i=?",(r[0],))
    print(r, [(a if a==b else b,c) for a,b,c in kv if b not in('classname','origin')])
