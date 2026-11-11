import math
def hp(w):
    if w==1: return 150
    if w<=9: return 150+(w-1)*100
    return int(950*1.1**(w-9))
def total(w,p):
    arr=[0,0.25,0.3,0.5,0.7,0.9]
    a=1;b=1
    if w<6: a=arr[w]
    elif w<10: b=w/5
    else: b=w*w*0.03
    e=p-1
    if e<1: e=0.5
    return int((24+e*6*b)*a)
def delay(w):
    if w==1: return 2.0
    return max(2*0.95**(w-1),0.08)
def mm(w):
    if w==1: return (1,0,0,0)
    lo=4*w; vals=list(range(lo,lo+35))  # randomintrange(lo,lo+35) -> lo..lo+34
    c=[0,0,0,0]
    for v in vals:
        c[0 if v<=32 else 1 if v<=55 else 2 if v<=78 else 3]+=1
    return tuple(x/35 for x in c)
print('wave hp  zombies(1p 2p 3p 4p) delay  slow/walk/run/sprint')
for w in [1,2,3,4,5,6,8,10,12,14,15,16,18,20,25,30,35,40,50]:
    m=mm(w)
    print(w,hp(w),[total(w,p) for p in (1,2,3,4)],round(delay(w),2),[round(x*100) for x in m])
# brute hp
for w in [10,12,14,15,20,30]:
    print('brute',w,[min(2000+int(hp(w)*2*m),5000) for m in (1,1.5,2,2.5)])
# hp cap wave
w=9
while hp(w)<6100000: w+=1
print('cap 6.1M at wave',w, hp(w-1),hp(w))
# delay floor wave
w=1
while delay(w)>0.08+1e-9: w+=1
print('delay floor at wave',w)
# clown counts
for n,(mult,d) in enumerate([(6,2),(9,2),(12,2),(12,3),(15,3)]):
    print('event#',n,'players->',[p*mult*d for p in (1,2,3,4)])
