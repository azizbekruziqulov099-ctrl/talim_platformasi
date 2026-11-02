import json, re, os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UZ = {"Singapore": "Singapur", "Chinese Taipei": "Tayvan", "Korea": "Janubiy Koreya", "Hong Kong SAR": "Gonkong", "Japan": "Yaponiya",
 "Macao SAR": "Makao", "Lithuania": "Litva", "Türkiye": "Turkiya", "England": "Angliya", "Poland": "Polsha", "Ireland": "Irlandiya",
 "Romania": "Ruminiya", "Netherlands": "Niderlandiya", "Latvia": "Latviya", "Norway": "Norvegiya", "Czech Republic": "Chexiya",
 "Sweden": "Shvetsiya", "Bulgaria": "Bolgariya", "Finland": "Finlandiya", "Australia": "Avstraliya", "Germany": "Germaniya",
 "Denmark": "Daniya", "Serbia": "Serbiya", "Belgium (Flemish)": "Belgiya (flamand)", "Hungary": "Vengriya", "Portugal": "Portugaliya",
 "United States": "AQSH", "Cyprus": "Kipr", "Slovak Republic": "Slovakiya", "Slovenia": "Sloveniya", "Italy": "Italiya", "Armenia": "Armaniston",
 "Albania": "Albaniya", "Canada": "Kanada", "Spain": "Ispaniya", "United Arab Emirates": "BAA", "Georgia": "Gruziya", "Azerbaijan": "Ozarbayjon",
 "New Zealand": "Yangi Zelandiya", "Belgium (French)": "Belgiya (fransuz)", "Kazakhstan": "Qozog‘iston", "France": "Fransiya",
 "Montenegro": "Chernogoriya", "North Macedonia": "Shimoliy Makedoniya", "Qatar": "Qatar", "Bahrain": "Bahrayn", "Kosovo": "Kosovo",
 "Bosnia and Herzegovina": "Bosniya va Gersegovina", "Chile": "Chili", "Uzbekistan": "O‘zbekiston", "Jordan": "Iordaniya", "Oman": "Ummon",
 "Iran": "Eron", "Saudi Arabia": "Saudiya Arabistoni", "Brazil": "Braziliya", "Morocco": "Marokash", "Kuwait": "Quvayt", "South Africa": "JAR",
 "Austria": "Avstriya", "Malta": "Malta", "Israel": "Isroil", "Malaysia": "Malayziya", "Palestine": "Falastin", "Russian Federation": "Rossiya",
 "Northern Ireland": "Shimoliy Irlandiya", "Croatia": "Xorvatiya", "Pakistan": "Pokiston", "Philippines": "Filippin", "Lebanon": "Livan",
 "Egypt": "Misr", "Viet Nam": "Vyetnam", "Estonia": "Estoniya", "Switzerland": "Shveytsariya", "Kyrgyzstan": "Qirg‘iziston", "Tajikistan": "Tojikiston",
 "Mongolia": "Mongoliya", "Indonesia": "Indoneziya", "Thailand": "Tailand", "Greece": "Gretsiya", "Mexico": "Meksika", "Moldova": "Moldova",
 "Ukraine": "Ukraina", "Tunisia": "Tunis", "Ghana": "Gana", "Syrian Arab Republic": "Suriya", "Macedonia, Rep. of": "Makedoniya",
 "Iran, Islamic Rep. of": "Eron", "Korea, Rep. of": "Janubiy Koreya", "Palestinian Nat'l Auth.": "Falastin", "Turkey": "Turkiya",
 "Hong Kong (China)": "Gonkong", "Macao (China)": "Makao", "United Kingdom": "Buyuk Britaniya", "OECD average": "OECD o‘rtachasi",
 "Botswana": "Botsvana", "Honduras": "Gonduras", "Yemen": "Yaman", "Qatar ": "Qatar", "Bahrain ": "Bahrayn", "Colombia": "Kolumbiya",
 "Argentina": "Argentina", "Iceland": "Islandiya", "Peru": "Peru", "Uruguay": "Urugvay", "Cambodia": "Kambodja", "Baku (Azerbaijan)": "Boku (Ozarbayjon)"}
out = {"manbalar": {
  "TIMSS 2023": "IEA, TIMSS 2023 International Results (Singapur Ta’lim vazirligi ilovasi, 2024)",
  "TIMSS 2019": "IEA, TIMSS 2019 International Results (Singapur Ta’lim vazirligi ilovasi, 2020)",
  "PIRLS 2021": "IEA, PIRLS 2021 International Results",
  "PISA 2022": "OECD, PISA 2022 Results, Table A1",
  "PISA 2025": "OECD, PISA 2025 Results (2026-yil 8-sentabr) — Gazeta.uz sharhi"},
  "jadvallar": {}}
cur = None
for line in open(f"{S}/data/raw_natija.txt"):
    line = line.strip()
    if line.startswith("#"):
        cur = line[1:].strip(); out["jadvallar"][cur] = []; continue
    for part in line.split(";"):
        m = re.match(r"\s*(.+?)\s+(\d{3})\s*$", part)
        if m:
            out["jadvallar"][cur].append([UZ.get(m.group(1), m.group(1)), int(m.group(2))])
pisa22 = """Singapore 543 575 561;Macao (China) 510 552 543;Chinese Taipei 515 547 537;Hong Kong (China) 500 540 520;Japan 516 536 547;Korea 515 527 528;Estonia 511 510 526;Switzerland 483 508 503;Canada 507 497 515;Netherlands 459 493 488;Ireland 516 492 504;Poland 489 489 499;United Kingdom 494 489 500;Australia 498 487 507;Finland 490 484 511;Germany 480 475 492;France 474 474 487;OECD average 476 472 485;Hungary 473 473 486;Viet Nam 462 469 472;Italy 482 471 477;United States 504 465 499;Türkiye 456 453 476;Serbia 440 440 447;United Arab Emirates 417 431 432;Romania 428 428 428;Kazakhstan 386 425 423;Mongolia 378 425 412;Qatar 419 414 432;Moldova 411 414 417;Malaysia 388 409 416;Thailand 379 394 409;Georgia 374 390 384;Saudi Arabia 383 389 390;Baku (Azerbaijan) 365 397 380;Brazil 410 379 403;Indonesia 359 366 383;Morocco 339 365 365;Jordan 342 361 375;Uzbekistan 336 364 355;Philippines 347 355 356;Kosovo 342 355 357;Cambodia 329 336 347"""
for nom, o in [("PISA 2022 R", 0), ("PISA 2022 M", 1), ("PISA 2022 S", 2)]:
    rows = []
    for part in pisa22.split(";"):
        m = re.match(r"(.+?)\s+(\d+)\s+(\d+)\s+(\d+)$", part.strip())
        rows.append([UZ.get(m.group(1), m.group(1)), int(m.group(2 + o))])
    out["jadvallar"][nom] = sorted(rows, key=lambda r: -r[1])
out["jadvallar"]["PISA 2025 S"] = [["OECD o‘rtachasi", 482], ["O‘zbekiston", 438], ["Qozog‘iston", 420], ["Qirg‘iziston", 363], ["Tojikiston", 334]]
out["ozbekiston"] = {
  "TIMSS": {"M4": {"2023": 443}, "S4": {"2023": 412}, "M8": {"2023": 421}, "S8": {"2023": 396}},
  "PISA": {"M": {"2022": 364}, "R": {"2022": 336}, "S": {"2022": 355, "2025": 438}},
  "PIRLS": {"R4": {"2021": 437}},
  "izoh": "TIMSS 2023 da O‘zbekiston birinchi marta qatnashdi: 4-sinf matematika 58 davlat ichida 50-o‘rin, 8-sinf matematika 44 ichida 32-o‘rin. PISA 2025 da tabiiy fanlar bo‘yicha 91 davlat ichida 48-o‘rin (+83 ball — tadqiqotdagi eng katta o‘sish). PISA 2025 ning matematika va o‘qish natijalari O‘zbekiston bo‘yicha e’lon qilinmagan."
}
out["darajalar"] = {"TIMSS": [[625, "Ilg‘or"], [550, "Yuqori"], [475, "O‘rta"], [400, "Past"]], "markaz": 500}
out["nomlar"] = UZ
json.dump(out, open(f"{S}/data/natijalar.json", "w"), ensure_ascii=False, indent=0)
print({k: len(v) for k, v in out["jadvallar"].items()})
