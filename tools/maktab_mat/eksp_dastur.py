import json, re, sys
sys.path.insert(0,'/tmp/m1')
import m34, m56, m711
KURSLAR=[]
def bolib(darslar, kurs, nom, gen):
    # darslar: [(nom, tur)] — 20 bosqichga teng bo'lamiz
    n=len(darslar); L=[]
    for b in range(20):
        a, z = round(b*n/20), round((b+1)*n/20)
        bo = darslar[a:max(z,a+1)] if a < n else darslar[-1:]
        turlar=[]
        for _, t in bo:
            if t not in turlar: turlar.append(t)
        L.append({"mavzu": " · ".join(dict.fromkeys(x[0] for x in bo))[:140], "turlar": turlar})
    KURSLAR.append({"kalit": kurs, "nom": nom, "gen": gen, "bosqichlar": L})
for g in ("3","4"):
    ds=[]
    for nom, asl, x in m34.darslar34(g):
        n=asl.lower(); mid,o,t=next(((m,o,t) for k,m,o,t in m34.TUR if any(y in n for y in k)), ("N056",None,"aralash"))
        if t!="aralash": ds.append((asl,t))
    bolib(ds, f"mat{g}", f"Matematika · {g}-sinf", "34")
for g in ("5","6"):
    ds=[]
    for kalit, asl, bob, x in m56.darslar56(g):
        mid,o,t=m56.tanla(asl,bob)
        if t!="aralash": ds.append((asl,t))
    bolib(ds, f"mat{g}", f"Matematika · {g}-sinf", "56")
for g in ("7","8","9","10","11"):
    for fan in ("Algebra","Geometriya"):
        ds=[]
        for kalit, asl, bob, x in m711.darslar711(g, fan):
            mid,o,t=m711.tanla711(asl,fan,bob); ds.append((asl,t))
        bolib(ds, f"{'alg' if fan=='Algebra' else 'geo'}{g}", f"{fan} · {g}-sinf", "711")
json.dump(KURSLAR, open('/tmp/m1/ekspeditsiya_dastur.json','w'), ensure_ascii=False, indent=0)
print(len(KURSLAR), [ (k['kalit'], sum(len(b['turlar']) for b in k['bosqichlar'])) for k in KURSLAR])
