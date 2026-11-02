"""content/*.json + meta → backend modules/xalqaro_data/*.json"""
import glob, json, os, sys
S = os.path.dirname(os.path.abspath(__file__))   # tools/xalqaro
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, "..", "..", "modules", "xalqaro_data")
os.makedirs(OUT, exist_ok=True)
ramka = json.load(open(f"{S}/ramka.json"))
savollar, yoq = [], []
for tk in ramka["toplamlar"]:
    meta = json.load(open(f"{S}/meta/{tk}.items.json"))
    cont = {}
    for f in sorted(glob.glob(f"{S}/content/{tk}_p*.json")):
        for d in json.load(open(f)):
            cont[d["id"]] = d
    for m in meta:
        c = cont.get(m["id"])
        if not c:
            yoq.append(m["id"]); continue
        savollar.append({
            "id": m["id"], "toplam": tk, "mavzu": m["mavzu"], "soha": m["soha"], "fikrlash": m["fikrlash"],
            "asl_ball": m["ball"], "blok": m.get("block_seq"), "xalqaro_ortacha": m.get("xalqaro_ortacha"),
            "davlatlar": m.get("davlatlar", {}), "kunikma": c["kunikma"], "usul": c["usul"], "variantlar": c["variantlar"]})
darslar = []
for f in sorted(glob.glob(f"{S}/content/dars_*.json")):
    darslar += json.load(open(f))
fan_soha = {"biologiya": "Biologiya", "kimyo": "Kimyo", "fizika": "Fizika", "yer": "Geografiya"}
for d in darslar:
    for tk, tops in ramka["mavzular"].items():
        t = next((t for t in tops if t["kalit"] == d["mavzu"]), None)
        if t:
            d["fan"] = fan_soha.get(t["soha"], ramka["toplamlar"][tk]["ustoz_fan"]) if tk == "T11_G8_S" else ramka["toplamlar"][tk]["ustoz_fan"]
json.dump(savollar, open(f"{OUT}/savollar.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(darslar, open(f"{OUT}/darslar.json", "w"), ensure_ascii=False, separators=(",", ":"))
r2 = {"fikrlash": ramka["fikrlash"], "toplamlar": ramka["toplamlar"], "mavzular": ramka["mavzular"]}
json.dump(r2, open(f"{OUT}/ramka.json", "w"), ensure_ascii=False, indent=1)
json.dump(json.load(open(os.path.join(OUT, "natijalar.json"))), open(f"{OUT}/natijalar.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("savollar:", len(savollar), "variant:", sum(len(s["variantlar"]) for s in savollar), "darslar:", len(darslar), "yo'q:", len(yoq))
for f in os.listdir(OUT):
    print(f, os.path.getsize(f"{OUT}/{f}") // 1024, "KB")
