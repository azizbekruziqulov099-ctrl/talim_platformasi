"""REV99: 2–3 yosh til kitobi — 3–4 yosh ingliz kitobidan, juda sodda va iliq («sen», robot Kabu).

[en]…[/en] bo'laklar 3–4 yosh kitobidagi bilan AYNAN bir xil qoldirilgan — shuning uchun 9 tildagi tayyor tarjimalar
o'zgarishsiz ishlaydi. Faqat o'zbekcha gaplar qisqartirilgan va bolaga «sen» deb murojaat qilinadi.

Ishlatish: python tools/bogcha_23.py   → tools/bogcha_content/en_23.json
"""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "bogcha_content"

# kalit: "bo'lim.dars" (0 dan). I — kirish, A — har so'z harakati, E — qo'shimcha topshiriq matni, T — test (savol, izoh).
UZ = {
    "0.0": {"I": "Salom, do'stim! Men — robot Kabu. Bip-bip! Uzoq yurtdan uchib keldim. U yerda bolalar qanday salomlashadi? Qani, bilib olamiz!",
            "A": ["Qo'lingni silkit!", "Qo'lingni baland ko'tar!"],
            "E": [("🎵 Salom qo'shig'i", "Qani, qo'shiq aytamiz! [en]Hello, hello, hello![/en] Qo'l silkitamiz. [en]Hi, hi, hi![/en] Qo'l ko'taramiz. Yana bir marta!")],
            "T": [("Robot Kabu keldi. Unga nima deymiz?", "Barakalla! Do'stimizni ko'rsak [en]Hello![/en] deymiz.")]},
    "0.1": {"I": "Bip-bip! Mehmon ketayotganda nima deymiz? Sovg'a olganda-chi? Ikkita sehrli so'z!",
            "A": ["Qo'l silkitib xayrlash!", "Qo'lingni ko'ksingga qo'y!"],
            "E": [("🎭 Sovg'a o'yini", "Ayiqcha senga olma berdi. Nima deysan? [en]Thank you![/en] Ayiqcha uyiga ketyapti. Qo'l silkit: [en]Bye![/en]")],
            "T": [("Senga sovg'a berishdi. Nima deysan?", "Ofarin! Sovg'a olganda [en]Thank you![/en] — rahmat deymiz.")]},
    "0.2": {"I": "Ertalab quyosh chiqadi, kechasi oy chiqadi. Bolalar ertalab va kechasi nima deydi? Tingla!",
            "A": ["Kerishib, uyg'ongandek qil!", "Qo'lingni yostiq qilib, uxlagandek qil!"],
            "E": [("🏃 Tong-tun o'yini", "Men [en]Good morning![/en] desam — sakra! Men [en]Good night![/en] desam — ko'zingni yum. Tayyormisan? [en]Good morning![/en] … [en]Good night![/en]")],
            "T": [("Kechasi oy chiqdi. Nima deymiz?", "To'g'ri! Kechasi [en]Good night![/en] deymiz.")]},
    "0.3": {"I": "Bip-bip! Men so'rayman, sen javob berasan. «Ha» va «yo'q» uchun ham so'z bor!",
            "A": ["Boshingni irg'at!", "Boshingni chayqa!"],
            "E": [("🎲 Ha-yo'q o'yini", "Robot Kabu mushukmi? Yo'q! [en]No![/en] Sen bolamisan? Ha! [en]Yes![/en] Muzqaymoq yaxshi ko'rasanmi? [en]Yes![/en]")],
            "T": [("Robot Kabu — mushukmi?", "Barakalla! Yo'q — [en]No![/en] Kabu mushuk emas.")]},
    "1.0": {"I": "Bog'chada o'g'il bolalar ham, qiz bolalar ham bor. Sen kimsan? Qani, bilib olamiz!",
            "E": [("🙋 Men kimman?", "O'g'il bolalar, ayting: [en]Boy![/en] Qiz bolalar, ayting: [en]Girl![/en] Endi hammamiz birga: [en]Boy and girl![/en]")],
            "T": [(None, "Ofarin! [en]Girl[/en] — qiz bola.")]},
    "1.1": {"I": "Uyda seni kim eng ko'p yaxshi ko'radi? Onang va dadang! Ularni qanday chaqiramiz?",
            "E": [("🎵 Oila barmoqchalari", "Barmog'ingni ko'rsat. Bu — [en]Mum[/en]! Bu — [en]Dad[/en]! [en]Hello, Mum! Hello, Dad![/en] Barmoqlar ta'zim qiladi!")],
            "T": [(None, "Barakalla! [en]Dad[/en] — dadam.")]},
    "1.2": {"I": "Sss… jim! Beshikda kichkintoy uxlayapti. Yonida mehribon buvijon o'tiribdi.",
            "A": ["Qo'lingda chaqaloqni allala!", ""],
            "E": [("🎭 Allalash o'yini", "Qo'g'irchoqni qo'lingga ol. Bu — [en]baby[/en]. Sekin allala va shivirla: [en]Good night, baby![/en]")],
            "T": [(None, "To'g'ri! [en]Baby[/en] — chaqaloq.")]},
    "1.3": {"I": "Bugun katta oilani yig'amiz! Bobojon ham keldi. Hammamiz birga — bu oila!",
            "E": [("🤗 Oila quchog'i", "Qo'llaringni keng och va hammani quchoqla: [en]Mum, dad, baby, granny, grandpa[/en] — bu [en]family[/en]!")],
            "T": [(None, "Ofarin! [en]Grandpa[/en] — bobojon.")]},
    "2.0": {"I": "Bip-bip! Sehrli bo'yoq qutisini topdim! Birinchi bo'yoqlar — qizil va ko'k. Qani, ochamiz!",
            "E": [("👀 Rang ovi", "Atrofingga qara! Qizil narsa topsang — ayt: [en]Red![/en] Ko'k narsa topsang — ayt: [en]Blue![/en]")],
            "T": [(None, "Barakalla! [en]Red[/en] — qizil.")]},
    "2.1": {"I": "Quyosh qanday rangda? Maysa-chi? Qutidan yana ikki rang chiqdi!",
            "E": [("🚦 Svetofor o'yini", "[en]Green![/en] — joyingda yugur! [en]Red![/en] — to'xta! [en]Yellow![/en] — chapak chal! Boshladik!")],
            "T": [(None, "To'g'ri! Quyosh — [en]yellow[/en], sariq.")]},
    "2.2": {"I": "Gulcha pushti, apelsin esa to'q sariq. Qani, ikkita chiroyli rang!",
            "T": [(None, "Ofarin! [en]Pink[/en] — pushti.")]},
    "2.3": {"I": "Qor qanday rangda? Tun-chi? Bugun oq va qora rang!",
            "E": [("🎵 Ranglar qo'shig'i", "Qani, kuylaymiz: [en]Red and blue, yellow, green[/en]! [en]Pink, orange, white and black[/en]! Barakalla, hamma rangni bilasan!")],
            "T": [(None, "To'g'ri! Qor — [en]white[/en], oq.")]},
    "3.0": {"I": "Hovlida kim «miyov» deyapti? Kim «vov-vov» deyapti? Yangi do'stlar bilan tanishamiz!",
            "A": ["Mushukdek «miyov» de!", "Kuchukdek «vov-vov» de!"],
            "E": [("🐾 Ovozni top", "Men ovoz chiqaraman, sen nomini ayt! «Miyov!» — [en]Cat![/en] «Vov-vov!» — [en]Dog![/en] Barakalla!")],
            "T": [(None, "Barakalla! [en]Cat[/en] — mushuk «miyov» deydi.")]},
    "3.1": {"I": "Bip-bip! Fermaga boramiz! Kim sut beradi? Kim tez chopadi? Ketdik!",
            "A": ["Sigirdek «mu-u» de!", "Otdek chopib, «du-dup» qil!"],
            "E": [("🏇 Ot minish", "Joyingda otdek chopamiz: du-dup, du-dup! [en]Horse, horse![/en] Endi to'xta, sigirdek: «mu-u!» [en]Cow![/en]")],
            "T": [(None, "Ofarin! [en]Cow[/en] — sigir sut beradi.")]},
    "3.2": {"I": "Kim «qo-qo» deyapti, kim «ga-ga» deyapti? Bular — qanotli do'stlarim!",
            "A": ["Tovuqdek «qo-qo» de!", "O'rdakdek lapanglab yur!"],
            "E": [("🦆 O'rdakcha yurishi", "Qo'llaringni qanot qil va o'rdakdek yur: [en]Duck, duck, duck![/en] Endi tovuqdek don cho'qi: [en]Hen, hen![/en]")],
            "T": [(None, "To'g'ri! [en]Duck[/en] — o'rdak suvda suzadi.")]},
    "3.3": {"I": "Kimning juni paxtadek yumshoq? Kim sakrab-sakrab sabzi yeydi? Topdingmi?",
            "A": ["Qo'ydek «ba-a» de!", "Quyondek sakra!"],
            "E": [("🐰 Quyon sakrashi", "Qo'llaring quloq bo'lsin. Sakraymiz: bir, ikki, uch! [en]Rabbit, rabbit, hop![/en] Barakalla!")],
            "T": [(None, "Ofarin! [en]Rabbit[/en] — quyon sakraydi.")]},
    "4.0": {"I": "Bip-bip! Uchta don topdim! Qani, sanaymiz! Barmoqchalaringni tayyorla!",
            "A": ["Bitta barmoq ko'rsat!", "Ikkita barmoq ko'rsat!", "Uchta barmoq ko'rsat!"],
            "E": [("👏 Chapak sanash", "Men bilan chapak chal va sana: [en]One[/en] — chap! [en]Two[/en] — chap, chap! [en]Three[/en] — chap, chap, chap!")],
            "T": [(None, "Barakalla! [en]One, two[/en] — ikkita olma.")]},
    "4.1": {"I": "Qo'lingga qara. Nechta barmoq bor? Besh! Qani, beshgacha sanaymiz!",
            "A": ["To'rtta barmoq ko'rsat!", "Kaftingni och!"],
            "E": [("🎵 Barmoq qo'shig'i", "Barmoqlarni bittadan och: [en]One, two, three, four, five![/en] Endi yum: [en]Five, four, three, two, one![/en] Ofarin!")],
            "T": [("Qo'limda nechta barmoq bor? 🖐", "To'g'ri! [en]Five[/en] — beshta barmoq.")]},
    "4.2": {"I": "Fil juda katta, sichqoncha esa kichkina! Robot Kabu-chi? Qani, ko'ramiz!",
            "A": ["Qo'llaringni keng yoy!", "Kichkina bo'lib, cho'nqayib o'tir!"],
            "E": [("🏃 Katta-kichik o'yini", "[en]Big![/en] desam — qo'lingni keng yoyib, baland tur! [en]Small![/en] desam — cho'nqayib, kichkina bo'l! [en]Big![/en] … [en]Small![/en]")],
            "T": [(None, "Ofarin! Fil — [en]big[/en], katta.")]},
    "5.0": {"I": "O'yinchoq sandiqchasini topdim! Ichida nima bor ekan? Sekin ochamiz…",
            "A": ["Koptokni otgandek qil!", ""],
            "E": [("⚽ Koptok o'yini", "Koptokni dumalat. Olganingda ayt: [en]Ball![/en] Qo'g'irchoqni quchoqla: [en]Doll![/en]")],
            "T": [(None, "Barakalla! [en]Ball[/en] — koptok.")]},
    "5.1": {"I": "Bip-bip! Kim keldi? Mashina! Ichida yumshoq ayiqcha o'tiribdi!",
            "A": ["Rul bura: bip-bip!", ""],
            "E": [("🚗 Mashina haydaymiz", "Rulni ushla va yur: bip-bip! [en]Car, car![/en] To'xta! Ayiqchani mashinaga o'tqaz: [en]Teddy, hello![/en]")],
            "T": [("«Bip-bip» qiladigan o'yinchoq qaysi?", "To'g'ri! [en]Car[/en] — mashina.")]},
    "5.2": {"I": "Bugun bayram! Havoda shar uchyapti, baraban «bum-bum» chalyapti!",
            "A": ["", "Baraban chal: bum-bum!"],
            "E": [("🥁 Baraban sanash", "Tizzangga baraban chal va sana: [en]One, two, three![/en] Bum-bum-bum! [en]Drum![/en] Endi shardek yengil uch: [en]Balloon![/en]")],
            "T": [(None, "Ofarin! [en]Balloon[/en] — havo shari.")]},
    "5.3": {"I": "Chu-chu! Poyezd keldi! Vagonlarida rang-barang kubiklar bor!",
            "A": ["Poyezddek «chu-chu» de!", "Kubiklarni ustma-ust qo'ygandek qil!"],
            "E": [("🚂 Poyezd o'yini", "Poyezd bo'lamiz: chu-chu! [en]Train, train![/en] Birinchi bekat — o'yinchoqlar: [en]ball, doll, car, teddy![/en]")],
            "T": [(None, "Barakalla! [en]Train[/en] — poyezd.")]},
    "6.0": {"I": "Mening boshim va munchoqdek ko'zlarim bor. Seniki-chi? Qani, ko'rsat!",
            "A": ["Boshingni ushla!", "Ko'zingni pirpiratib ko'rsat!"],
            "E": [("🙈 Berkinmachoq", "Ko'zingni qo'ling bilan yop… [en]Eyes![/en] Endi och — ku-ku! Boshingni sila: [en]Head![/en]")],
            "T": [(None, "Ofarin! [en]Eyes[/en] — ko'zlar bilan ko'ramiz.")]},
    "6.1": {"I": "Tss… eshityapsanmi? Qush sayrayapti! Hidlayapsanmi? Gul hidi!",
            "A": ["Quloqlaringni ushla!", "Burningga teg!"],
            "E": [("👃 Hidla-chi", "Gulni hidlagandek qil: mmm! [en]Nose![/en] Endi qulog'ingni kafting bilan tut va tingla: [en]Ears![/en]")],
            "T": [(None, "Barakalla! [en]Nose[/en] — burun bilan hidlaymiz.")]},
    "6.2": {"I": "Qarsakni kim chaladi? Qo'llarimiz! Kim jilmayadi? Og'zimiz! Qani, jilmay!",
            "A": ["Og'zingni ko'rsat!", "Qo'llaringni ko'tar!"],
            "E": [("👏 Qarsak qo'shig'i", "Chapak chal: [en]Hands, hands![/en] Endi og'zingni katta och: «a-a-a!» [en]Mouth![/en]")],
            "T": [(None, "To'g'ri! [en]Hands[/en] — qo'llar bilan.")]},
    "6.3": {"I": "Men uchaman, sen esa yurasan va sakraysan! Nima bilan? Oyoqlaring bilan! Tur!",
            "A": ["Oyog'ingni ko'tar!", "Oyog'ingni tapillat!"],
            "E": [("🎵 Bosh, ko'z, quloq", "Men aytaman, sen ushlaysan: [en]Head![/en] [en]Eyes![/en] [en]Ears![/en] [en]Nose![/en] [en]Mouth![/en] [en]Hands![/en] [en]Feet![/en] Barakalla!")],
            "T": [(None, "Ofarin! [en]Legs[/en] — oyoqlar bilan yuramiz.")]},
    "7.0": {"I": "Savatcha olib keldim! Ichida qizil meva va sariq meva bor. Topdingmi?",
            "E": [("🧺 Savatcha o'yini", "Savatchadan olma olgandek qil: [en]Apple![/en] Endi bananni artgandek qil: [en]Banana![/en] Qizil — [en]apple[/en], sariq — [en]banana[/en]!")],
            "T": [(None, "Barakalla! [en]Banana[/en] — banan.")]},
    "7.1": {"I": "Chanqadingmi? Menda oq ichimlik va tiniq ichimlik bor. Qaysi birini ichasan?",
            "E": [("🎭 Choyxona o'yini", "Ayiqchaga ichimlik ber: [en]Milk?[/en] Ayiqcha: [en]Yes![/en] Unga nima deymiz? [en]Thank you![/en] Barakalla!")],
            "T": [(None, "To'g'ri! Sigir — [en]milk[/en], sut beradi.")]},
    "7.2": {"I": "Bugun tug'ilgan kun! Dasturxonda non ham, shamli tort ham bor. Puflaymizmi?",
            "A": ["", "Shamni pufla: puf-f!"],
            "E": [("🎂 Tug'ilgan kun", "Shamlarni sana: [en]One, two, three![/en] Endi pufla: puf-f! [en]Cake, cake![/en] Hammaga ayt: [en]Thank you![/en]")],
            "T": [(None, "Ofarin! [en]Cake[/en] — tortdagi shamni puflaymiz.")]},
    "7.3": {"I": "Olmadan shirin sharbat qildik! Juda mazali bo'lsa, bir qiziq so'z aytamiz!",
            "A": ["", "Qorningni sila!"],
            "E": [("😋 Mazali o'yini", "Men ovqat aytaman: yoqsa — [en]Yummy![/en] deb qorningni sila, yoqmasa — [en]No![/en] de. [en]Cake?[/en] … [en]Apple?[/en] … [en]Juice?[/en]")],
            "T": [(None, "Barakalla! Mazali bo'lsa — [en]Yummy![/en]")]},
}

TAG = re.compile(r"\[en\].*?\[/en\]", re.S)


def build():
    src = json.loads((ROOT / "en_34.json").read_text(encoding="utf-8"))
    cur = copy.deepcopy(src)
    cur.update(age="2-3 yosh", book_title="Hello, friend! 2–3 yosh")
    for ui, unit in enumerate(cur["units"]):
        unit.pop("scenarios", None)   # 2–3 yoshga dialog/rol o'yini og'ir
        for li, les in enumerate(unit["lessons"]):
            o = UZ[f"{ui}.{li}"]
            les["intro"] = o["I"]
            for it, act in zip(les["items"], o.get("A") or [None] * len(les["items"])):
                if act is not None:
                    it["action"] = act
            for row, (title, text) in zip(les.get("extra") or [], o.get("E") or []):
                # inglizcha bo'laklar o'zgarmasin — tarjimalar shunga bog'langan
                assert TAG.findall(row["matn"]) == TAG.findall(text), (ui, li, row["matn"], text)
                row["matn"] = text   # sarlavha o'zgarmaydi (9 tilda tarjimasi tayyor)
            for t, (q, why) in zip(les.get("tests") or [], o.get("T") or []):
                if q:
                    assert TAG.findall(t["q"]) == TAG.findall(q), (ui, li)
                    t["q"] = q
                assert TAG.findall(t.get("why") or "") == TAG.findall(why), (ui, li, t.get("why"), why)
                t["why"] = why
    (ROOT / "en_23.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return cur


if __name__ == "__main__":
    b = build()
    print("en_23:", sum(len(u["lessons"]) for u in b["units"]), "dars")
