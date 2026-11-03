"""content/*.json + meta → backend modules/xalqaro_data/*.json

  python3 -I tools/build_data.py                 # o'zbekcha (asosiy) → xalqaro_data/
  python3 -I tools/build_data.py --til ru        # ruscha: content_ru/ → xalqaro_data/ru/
  python3 -I tools/build_data.py --til en        # inglizcha: content_en/ → xalqaro_data/en/

REV270: tarjima tilida faqat TO'LIQ tayyor to'plamlar chiqariladi (barcha savollari, PISA birliklari va mavzu darslari
shu tilda bo'lsa). Chala to'plam o'sha tilda umuman ko'rsatilmaydi — o'zbekcha bilan aralashib ketmasin.
"""
import glob
import json
import os
import sys

S = os.path.dirname(os.path.abspath(__file__))   # tools/xalqaro
args = sys.argv[1:]
TIL = "uz"
if "--til" in args:
    i = args.index("--til")
    TIL = args[i + 1]
    del args[i:i + 2]
BASE_OUT = args[0] if args else os.path.join(S, "..", "..", "modules", "xalqaro_data")
OUT = BASE_OUT if TIL == "uz" else os.path.join(BASE_OUT, TIL)
CONTENT = f"{S}/content" if TIL == "uz" else f"{S}/content_{TIL}"
RAMKA_DIR = S if TIL == "uz" else CONTENT
os.makedirs(OUT, exist_ok=True)


def yig(content_dir, ramka_dir):
    ramka = json.load(open(f"{ramka_dir}/ramka.json"))
    pisa_r = json.load(open(f"{ramka_dir}/ramka_pisa.json"))
    savollar, yoq = [], []
    for tk in ramka["toplamlar"]:
        meta = json.load(open(f"{S}/meta/{tk}.items.json"))
        cont = {}
        for f in sorted(glob.glob(f"{content_dir}/{tk}_p*.json")):
            for d in json.load(open(f)):
                cont[d["id"]] = d
        for m in meta:
            c = cont.get(m["id"])
            if not c:
                yoq.append((tk, m["id"]))
                continue
            savollar.append({
                "id": m["id"], "toplam": tk, "mavzu": m["mavzu"], "soha": m["soha"], "fikrlash": m["fikrlash"],
                "asl_ball": m["ball"], "blok": m.get("block_seq"), "xalqaro_ortacha": m.get("xalqaro_ortacha"),
                "davlatlar": m.get("davlatlar", {}), "kunikma": c["kunikma"], "usul": c["usul"], "variantlar": c["variantlar"]})
    # REV262: PISA birliklari (umumiy stimul + savollar)
    birliklar = []
    for f in sorted(glob.glob(f"{content_dir}/pisa/*.json")):
        for u in json.load(open(f)):
            birliklar.append({"birlik": u["birlik"], "toplam": u["toplam"], "nom": u["nom"], "asl": u.get("asl", ""),
                              "stimul": u.get("stimul", ""), "stimul_rasm": u.get("stimul_rasm")})
            soha_of = {m["kalit"]: m["soha"] for m in pisa_r["mavzular"][u["toplam"]]}
            for q in u["savollar"]:
                v = {k: q.get(k) for k in ("turi", "savol", "rasm", "javoblar", "togri", "javob", "javob_turi", "yechim", "xatolar", "maslahat")}
                savollar.append({"id": q["id"], "toplam": u["toplam"], "mavzu": q["mavzu"], "soha": soha_of.get(q["mavzu"], ""), "fikrlash": q["fikrlash"],
                                 "birlik": u["birlik"], "asl_id": q.get("asl_id", ""), "jarayon": q.get("jarayon"), "kontekst": q.get("kontekst"),
                                 "qiyinlik_ball": q.get("qiyinlik_ball"), "taxminiy": bool(q.get("taxminiy")), "oecd_foiz": q.get("oecd_foiz"),
                                 "kunikma": q.get("kunikma", ""), "usul": q.get("usul", ""), "variantlar": [v]})
    for k2 in ("toplamlar", "mavzular"):
        ramka[k2].update(pisa_r[k2])
    for k2 in ("darajalar", "jarayonlar", "kontekstlar"):
        ramka[k2] = pisa_r[k2]
    darslar = []
    for f in sorted(glob.glob(f"{content_dir}/dars_*.json")):
        darslar += json.load(open(f))
    fan_soha = {"biologiya": "Biologiya", "kimyo": "Kimyo", "fizika": "Fizika", "yer": "Geografiya"}
    for d in darslar:
        for tk, tops in ramka["mavzular"].items():
            t = next((t for t in tops if t["kalit"] == d["mavzu"]), None)
            if t:   # «fan» — o'qituvchi (ustoz) va doska turini tanlash uchun kanonik (o'zbekcha) nom, tarjima qilinmaydi
                d["fan"] = fan_soha.get(t["soha"], ramka["toplamlar"][tk]["ustoz_fan"]) if tk == "T11_G8_S" else ramka["toplamlar"][tk]["ustoz_fan"]
    return ramka, savollar, birliklar, darslar, yoq


ramka, savollar, birliklar, darslar, yoq = yig(CONTENT, RAMKA_DIR)
chiqarildi = []
if TIL != "uz":
    # to'liqlik: o'zbekcha asl bilan solishtiriladi
    _r, uz_sav, uz_bir, uz_dars, _y = yig(f"{S}/content", S)
    sav_ids = {s["id"] for s in savollar}
    bir_ids = {b["birlik"] for b in birliklar}
    dars_kod = {d["kod"] for d in darslar}
    tayyor = []
    for tk in list(ramka["toplamlar"]):
        kerak_sav = {s["id"] for s in uz_sav if s["toplam"] == tk}
        kerak_bir = {b["birlik"] for b in uz_bir if b["toplam"] == tk}
        kerak_dars = {"XB-" + t["kalit"] for t in ramka["mavzular"].get(tk, [])}
        yetmaydi = (kerak_sav - sav_ids, kerak_bir - bir_ids, kerak_dars - dars_kod)
        if any(yetmaydi) or not kerak_sav:
            chiqarildi.append((tk, [len(x) for x in yetmaydi]))
            ramka["toplamlar"].pop(tk)
            ramka["mavzular"].pop(tk, None)
        else:
            tayyor.append(tk)
    savollar = [s for s in savollar if s["toplam"] in ramka["toplamlar"]]
    birliklar = [b for b in birliklar if b["toplam"] in ramka["toplamlar"]]
    mv = {t["kalit"] for tops in ramka["mavzular"].values() for t in tops}
    darslar = [d for d in darslar if d["mavzu"] in mv]
    yoq = []

json.dump(savollar, open(f"{OUT}/savollar.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(darslar, open(f"{OUT}/darslar.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(birliklar, open(f"{OUT}/birliklar.json", "w"), ensure_ascii=False, separators=(",", ":"))
r2 = {k2: ramka[k2] for k2 in ("fikrlash", "toplamlar", "mavzular", "darajalar", "jarayonlar", "kontekstlar")}
json.dump(r2, open(f"{OUT}/ramka.json", "w"), ensure_ascii=False, indent=1)
if TIL == "uz":
    nat = os.path.join(OUT, "natijalar.json")   # natijalar.json — tools/xalqaro/build_natija.py yangilaydi
    if os.path.exists(nat):
        json.dump(json.load(open(nat)), open(f"{OUT}/natijalar.json", "w"), ensure_ascii=False, separators=(",", ":"))
    dv = f"{S}/davlatlar.json"
    if os.path.exists(dv):
        json.dump(json.load(open(dv)), open(f"{OUT}/davlatlar.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(f"[{TIL}] to'plamlar:", list(ramka["toplamlar"]), "| chiqarilmadi (savol, birlik, dars yetishmaydi):", chiqarildi)
print("PISA birliklar:", len(birliklar), "PISA savollar:", sum(1 for x in savollar if x.get("birlik")))
print("savollar:", len(savollar), "variant:", sum(len(s["variantlar"]) for s in savollar), "darslar:", len(darslar), "yo'q:", len(yoq))
