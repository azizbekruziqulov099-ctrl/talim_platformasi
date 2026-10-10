"""REV86: Shaxmat maktabi — bolalar va boshlovchilar uchun bosqichma-bosqich o'rgatish tizimi.

Darslar ketma-ket ochiladi (oldingisini tugatgan keyingisiga o'tadi). Har bir dars — qisqa tushuntirish
va taxtada bajariladigan mashqlar. Mashq turlari:
  • katak   — taxtadagi katak yoki figurani topish (a–h, 1–8 nomlari);
  • yulduz  — bitta figura bilan hamma ⭐ ni yig'ish (figuraning yurishini o'rganish); qora figuralar
              yurmaydi, ularni urib olish ham yulduz. Eng kam yurishlar soni (par) avtomatik hisoblanadi;
  • shax    — shaxdan qutulish: qochish / to'sish / urish usullaridan so'ralgani bilan;
  • mat     — N yurishda mat. Bir nechta to'g'ri yo'l bo'lsa hammasi qabul qilinadi (tekshiruvchi qidiruv),
              raqib eng qattiq himoyani o'ynaydi;
  • yechim  — aniq yurishlar ketma-ketligi (vilka, rokirovka, o'tib urish): raqib javobi tayyor.
Barcha mashqlar tests/test_shaxmat_maktab_rev86.py da tekshiriladi (FEN to'g'ri, mat haqiqatan mat,
yechim qonuniy, yulduzlar yetib boriladigan).
"""
from collections import deque
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from . import shaxmat_engine as eng
except ImportError:  # pragma: no cover
    from modules import shaxmat_engine as eng

START = eng.START_FEN

UNITS = [
    {"nomi": "Taxta bilan tanishuv", "emoji": "🏁", "darslar": [
        {"kod": "taxta", "nomi": "Taxta va kataklar", "emoji": "🔤",
         "matn": ["Shaxmat taxtasi 64 ta katakdan iborat: 32 ta oq va 32 ta qora.",
                  "Tik qatorlar a, b, c, d, e, f, g, h harflari bilan, yotiq qatorlar 1 dan 8 gacha raqamlar bilan belgilanadi.",
                  "Har bir katakning o'z nomi bor: avval harf, keyin raqam. Masalan: e4, a1, h8."],
         "mashqlar": [
             {"tur": "katak", "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "vazifa": "e4 katakni bosing", "javob": ["e4"]},
             {"tur": "katak", "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "vazifa": "a1 katakni bosing", "javob": ["a1"]},
             {"tur": "katak", "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "vazifa": "h8 katakni bosing", "javob": ["h8"]},
             {"tur": "katak", "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "vazifa": "d5 katakni bosing", "javob": ["d5"]},
             {"tur": "katak", "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "vazifa": "c7 katakni bosing", "javob": ["c7"]},
         ]},
        {"kod": "joylar", "nomi": "Figuralar joyi", "emoji": "♟",
         "matn": ["O'yin boshida oq figuralar 1- va 2-qatorlarda, qora figuralar 7- va 8-qatorlarda turadi.",
                  "Oldinda — 8 ta piyoda. Orqada chetdan: ruh, ot, fil, o'rtada farzin va shoh.",
                  "Eslab qoling: oq farzin oq katakda, qora farzin qora katakda turadi."],
         "mashqlar": [
             {"tur": "katak", "fen": START, "vazifa": "Oq shohni toping", "javob": ["e1"]},
             {"tur": "katak", "fen": START, "vazifa": "Qora farzinni toping", "javob": ["d8"]},
             {"tur": "katak", "fen": START, "vazifa": "Oq otlardan birini toping", "javob": ["b1", "g1"]},
             {"tur": "katak", "fen": START, "vazifa": "Qora fillardan birini toping", "javob": ["c8", "f8"]},
             {"tur": "katak", "fen": START, "vazifa": "Oq ruhlardan birini toping", "javob": ["a1", "h1"]},
         ]},
    ]},
    {"nomi": "Figuralar qanday yuradi", "emoji": "🚶", "darslar": [
        {"kod": "ruh", "nomi": "Ruh", "emoji": "♜",
         "matn": ["Ruh to'g'ri chiziq bo'ylab yuradi: oldinga, orqaga, o'ngga va chapga — istalgancha katak.",
                  "Lekin boshqa figuralar ustidan sakray olmaydi.",
                  "Vazifa: ruh bilan hamma ⭐ yulduzlarni yig'ing. Kam yurish — ko'p yulduz!"],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/R7 w - - 0 1", "yulduzlar": ["a5", "e5"]},
             {"tur": "yulduz", "fen": "8/8/8/8/3R4/8/8/8 w - - 0 1", "yulduzlar": ["d8", "h8", "h1"]},
             {"tur": "yulduz", "fen": "8/2p5/8/8/8/2R5/8/8 w - - 0 1", "yulduzlar": ["c7", "g7", "g2"]},
         ]},
        {"kod": "fil", "nomi": "Fil", "emoji": "♝",
         "matn": ["Fil qiyshiq — diagonal bo'ylab istalgancha katak yuradi.",
                  "Qiziq sir: fil doim bir xil rangdagi kataklarda qoladi. Oq katakdagi fil hech qachon qora katakka o'tmaydi!"],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/2B5 w - - 0 1", "yulduzlar": ["e3", "g5"]},
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/5B2 w - - 0 1", "yulduzlar": ["b5", "e8", "h5"]},
             {"tur": "yulduz", "fen": "8/8/8/8/3B4/8/8/8 w - - 0 1", "yulduzlar": ["a1", "h8", "a7"]},
         ]},
        {"kod": "farzin", "nomi": "Farzin", "emoji": "♛",
         "matn": ["Farzin — eng kuchli figura! U ruh kabi to'g'ri chiziq bo'ylab ham, fil kabi diagonal bo'ylab ham yuradi.",
                  "Farzinni ehtiyot qiling — uni yo'qotish juda og'ir."],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/3Q4 w - - 0 1", "yulduzlar": ["d7", "h3"]},
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/Q7 w - - 0 1", "yulduzlar": ["h8", "a8", "e4", "h1"]},
             {"tur": "yulduz", "fen": "8/1p2p3/6p1/8/4Q3/8/8/8 w - - 0 1", "yulduzlar": ["b7", "g6", "e7"]},
         ]},
        {"kod": "shoh", "nomi": "Shoh", "emoji": "♚",
         "matn": ["Shoh — eng muhim figura. U har tomonga faqat 1 katak yuradi.",
                  "Shohni asrash kerak: agar shoh qutula olmasa — o'yin tugaydi (bu MAT deyiladi)."],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/4K3 w - - 0 1", "yulduzlar": ["e3"]},
             {"tur": "yulduz", "fen": "8/8/8/8/3K4/8/8/8 w - - 0 1", "yulduzlar": ["f6", "b5"]},
         ]},
        {"kod": "ot", "nomi": "Ot", "emoji": "♞",
         "matn": ["Ot «G» harfi shaklida sakraydi: bir tomonga 2 katak va yon tomonga 1 katak.",
                  "Ot — yagona figura, u boshqa figuralar ustidan sakrab o'ta oladi!",
                  "Har sakrashda ot katak rangini almashtiradi: oqdan qoraga, qoradan oqqa."],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/1N6 w - - 0 1", "yulduzlar": ["c3", "e4"]},
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/6N1 w - - 0 1", "yulduzlar": ["f3", "g5", "e6"]},
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/8/N7 w - - 0 1", "yulduzlar": ["h8"]},
         ]},
        {"kod": "piyoda", "nomi": "Piyoda", "emoji": "♟",
         "matn": ["Piyoda faqat oldinga yuradi — 1 katak. Birinchi yurishida 2 katak ham yura oladi.",
                  "Lekin piyoda qiyshiq uradi: oldinga-yonga bir katakdagi raqib figurasini.",
                  "Piyoda oxirgi qatorga yetsa — sehr! U farzin (yoki ruh, fil, ot)ga aylanadi."],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/8/8/8/8/4P3/8 w - - 0 1", "yulduzlar": ["e4", "e5"]},
             {"tur": "yulduz", "fen": "8/8/1p6/2p5/3P4/8/8/8 w - - 0 1", "yulduzlar": ["c5", "b6"]},
             {"tur": "yulduz", "fen": "8/6P1/8/8/8/8/8/8 w - - 0 1", "yulduzlar": ["g8"]},
         ]},
    ]},
    {"nomi": "Urish, shax va mat", "emoji": "⚔️", "darslar": [
        {"kod": "urish", "nomi": "Urib olish", "emoji": "🎯",
         "matn": ["Figura raqib figurasi turgan katakka yursa — uni urib oladi, raqib figurasi taxtadan chiqadi.",
                  "Vazifa: hamma qora figuralarni urib oling. Ular joyidan qimirlamaydi."],
         "mashqlar": [
             {"tur": "yulduz", "fen": "8/8/p2p4/8/8/8/3p4/R7 w - - 0 1", "yulduzlar": ["a6", "d6", "d2"]},
             {"tur": "yulduz", "fen": "8/8/2p3p1/4p3/3N4/8/8/8 w - - 0 1", "yulduzlar": ["c6", "e5", "g6"]},
             {"tur": "yulduz", "fen": "7p/8/8/8/p6p/8/8/3Q4 w - - 0 1", "yulduzlar": ["a4", "h4", "h8"]},
         ]},
        {"kod": "shax", "nomi": "Shax va undan qutulish", "emoji": "⚠️",
         "matn": ["Shohga hujum qilinsa — bu SHAX. Shaxni e'tiborsiz qoldirib bo'lmaydi!",
                  "Shaxdan 3 xil qutulish mumkin: 1) shoh qochadi, 2) orasiga figura qo'yib to'siladi, 3) hujum qilayotgan figura urib olinadi."],
         "mashqlar": [
             {"tur": "shax", "usul": "qoch", "fen": "4k3/8/8/8/8/8/8/r3K3 w - - 0 1", "vazifa": "Shohni xavfsiz joyga qochiring"},
             {"tur": "shax", "usul": "tos", "fen": "4k3/8/8/8/8/8/3B4/r3K3 w - - 0 1", "vazifa": "Shaxni fil bilan to'sing"},
             {"tur": "shax", "usul": "ur", "fen": "4k3/8/8/8/1B6/8/3q4/4K3 w - - 0 1", "vazifa": "Shax berayotgan farzinni urib oling"},
         ]},
        {"kod": "mat1", "nomi": "Mat 1 yurishda", "emoji": "🏆",
         "matn": ["MAT — shohga shax berildi va u hech qanday usulda qutula olmaydi. Mat qilgan o'yinchi yutadi!",
                  "Vazifa: bitta yurish bilan mat qiling. Shohning qochadigan joylarini sanang!"],
         "mashqlar": [
             {"tur": "mat", "n": 1, "fen": "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "vazifa": "Oxirgi qatorda mat qiling"},
             {"tur": "mat", "n": 1, "fen": "k7/8/1K6/8/8/8/8/6Q1 w - - 0 1", "vazifa": "Farzin bilan mat qiling"},
             {"tur": "mat", "n": 1, "fen": "6k1/1R6/8/8/8/8/8/R5K1 w - - 0 1", "vazifa": "Ikki ruh bilan mat qiling"},
             {"tur": "mat", "n": 1, "fen": "r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1", "vazifa": "«Bolalar mati»ni toping"},
             {"tur": "mat", "n": 1, "fen": "6rk/6pp/8/6N1/8/8/8/6K1 w - - 0 1", "vazifa": "Ot bilan «bo'g'ilgan mat» qiling"},
             {"tur": "mat", "n": 1, "fen": "5rk1/5ppp/8/8/8/8/1B6/6QK w - - 0 1", "vazifa": "Farzin va fil birgalikda mat qiladi"},
         ]},
        {"kod": "mat2", "nomi": "Mat 2 yurishda", "emoji": "🧠",
         "matn": ["Endi qiyinroq: mat 2 yurishda. Birinchi yurish tayyorlaydi, ikkinchisi mat qiladi.",
                  "Raqib eng yaxshi himoyani o'ynaydi — shoshilmang, o'ylab yuring!"],
         "mashqlar": [
             {"tur": "mat", "n": 2, "fen": "7k/8/8/8/8/8/1R6/R6K w - - 0 1", "vazifa": "Ikki ruh «narvon» bo'lib mat qiladi"},
             {"tur": "mat", "n": 2, "fen": "7k/8/5K2/8/8/8/8/Q7 w - - 0 1", "vazifa": "Farzin va shoh birgalikda"},
             {"tur": "mat", "n": 2, "fen": "k7/8/2K5/8/8/8/8/7R w - - 0 1", "vazifa": "Ruh va shoh bilan mat"},
         ]},
    ]},
    {"nomi": "Taktika va maxsus yurishlar", "emoji": "✨", "darslar": [
        {"kod": "vilka", "nomi": "Vilka (ikki tomonlama hujum)", "emoji": "🍴",
         "matn": ["Vilka — bitta figura bir vaqtda ikkita raqib figurasiga hujum qiladi. Raqib faqat bittasini qutqara oladi!",
                  "Ot vilkalari ayniqsa xavfli. Shoh va boshqa figurani birga «sanchqiga ilish»ga harakat qiling."],
         "mashqlar": [
             {"tur": "yechim", "fen": "r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "vazifa": "Ot bilan shoh va ruhga vilka qiling va ruhni yuting",
              "yechim": ["b5c7", "e8d7", "c7a8"]},
             {"tur": "yechim", "fen": "4k3/8/8/8/7r/8/8/3QK3 w - - 0 1", "vazifa": "Farzin bilan shax bering va ruhni yuting",
              "yechim": ["d1a4", "e8f7", "a4h4"]},
             {"tur": "yechim", "fen": "4k3/8/8/2n1b3/8/3P4/8/4K3 w - - 0 1", "vazifa": "Piyoda bilan ikki figuraga vilka qiling",
              "yechim": ["d3d4", "e5f6", "d4c5"]},
         ]},
        {"kod": "rokirovka", "nomi": "Rokirovka", "emoji": "🏰",
         "matn": ["Rokirovka — bir yurishda shoh va ruh birga yuradi: shoh ruh tomonga 2 katak o'tadi, ruh shohning yoniga sakraydi.",
                  "Shart: shoh ham, ruh ham hali yurmagan, oralarida figura yo'q, shoh shax ostida emas va urilayotgan katakdan o'tmaydi.",
                  "Rokirovka shohni xavfsiz joyga yashiradi. Shohni bosing va 2 katak yon tomonga yuring."],
         "mashqlar": [
             {"tur": "yechim", "fen": "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "vazifa": "Qisqa rokirovka qiling (h1 tomonga)",
              "yechim": ["e1g1"]},
             {"tur": "yechim", "fen": "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "vazifa": "Uzun rokirovka qiling (a1 tomonga)",
              "yechim": ["e1c1"]},
         ]},
        {"kod": "otib_urish", "nomi": "O'tib urish", "emoji": "💨",
         "matn": ["Qiziq qoida: raqib piyodasi birinchi yurishida 2 katak yurib, sizning piyodangiz yoniga kelsa —",
                  "siz uni xuddi 1 katak yurgandek qiyshiq yurib urishingiz mumkin. Faqat darhol, keyingi yurishda!"],
         "mashqlar": [
             {"tur": "yechim", "fen": "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "vazifa": "d5 dagi piyodani o'tib urish bilan oling",
              "yechim": ["e5d6"]},
             {"tur": "yechim", "fen": "4k3/8/8/5Pp1/8/8/8/4K3 w - g6 0 1", "vazifa": "g5 dagi piyodani o'tib urib oling",
              "yechim": ["f5g6"]},
         ]},
    ]},
]

LESSONS = [dict(les, bolim=ui) for ui, unit in enumerate(UNITS) for les in unit["darslar"]]
for _i, _les in enumerate(LESSONS):
    _les["tartib"] = _i
BY_CODE = {les["kod"]: les for les in LESSONS}


# ── Yordamchilar ──
def keep_white(fen):
    """Yulduz mashqida navbat doim oqda qoladi (qora figuralar yurmaydi)."""
    parts = fen.split()
    parts[1], parts[3] = "w", "-"
    return " ".join(parts)


def uci(m):
    return eng.sq_name(m["from"]) + eng.sq_name(m["to"]) + (m.get("promo") or "")


def mumkin(fen):
    return [eng.move_names(m) for m in eng.legal_moves(fen)]


def star_par(fen, stars):
    """Hamma yulduzni yig'ish uchun eng kam yurish (BFS)."""
    goal = frozenset(stars)
    start = (keep_white(fen), frozenset())
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (pos, got), d = queue.popleft()
        if got == goal:
            return d
        if d > 12:
            continue
        for m in eng.legal_moves(pos):
            if m.get("promo") and m["promo"] != "q":
                continue
            nxt = keep_white(eng.apply_move(pos, m))
            ngot = got | ({eng.sq_name(m["to"])} & goal)
            state = (nxt, frozenset(ngot))
            if state not in seen:
                seen.add(state)
                queue.append((state, d + 1))
    return None


_PAR = {}


def par_of(les_code, i):
    key = (les_code, i)
    if key not in _PAR:
        ex = BY_CODE[les_code]["mashqlar"][i]
        _PAR[key] = star_par(ex["fen"], ex["yulduzlar"])
    return _PAR[key]


def is_mate(b):
    return b.in_check() and not b.legal()


def forced_mate(b, n):
    """Navbatdagi tomon (hujumchi) n yurishda majburan mat qila oladimi."""
    for m in b.legal():
        u = b.make(m)
        ok = is_mate(b) or (n > 1 and bool(b.legal()) and all_replies_mate(b, n - 1))
        b.unmake(u)
        if ok:
            return True
    return False


def all_replies_mate(b, n):
    for r in b.legal():
        u = b.make(r)
        ok = forced_mate(b, n)
        b.unmake(u)
        if not ok:
            return False
    return True


def best_defence(b, n):
    """Mat mashqida raqib javobi: iloji bo'lsa matni kechiktiradigan (yoki eng uzoq chidaydigan) yurish."""
    replies = b.legal()
    for r in replies:
        u = b.make(r)
        escapes = not forced_mate(b, n)
        b.unmake(u)
        if escapes:
            return r
    return replies[0] if replies else None


def method_of(b, m):
    """Shaxdan qutulish usuli: qoch | tos | ur."""
    if b.sq[m[1]] != ".":
        return "ur"
    if b.sq[m[0]].lower() == "k":
        return "qoch"
    return "tos"


def public_exercise(les_code, i, ex):
    out = {"tur": ex["tur"], "fen": ex["fen"], "vazifa": ex.get("vazifa") or "", "mumkin": mumkin(ex["fen"]) if ex["tur"] != "katak" else []}
    if ex["tur"] == "katak":
        out["javob"] = ex["javob"]     # oddiy topish mashqi — mijozda tekshiriladi
    if ex["tur"] == "yulduz":
        out["yulduzlar"] = ex["yulduzlar"]
        out["par"] = par_of(les_code, i)
        out["vazifa"] = out["vazifa"] or "Hamma ⭐ yulduzlarni yig'ing"
    if ex["tur"] == "mat":
        out["n"] = ex["n"]
    if ex["tur"] == "yechim":
        out["qadamlar"] = (len(ex["yechim"]) + 1) // 2
    if ex["tur"] == "shax":
        out["usul"] = ex["usul"]
    return out


def check_move(les_code, i, fen, path, got=(), step=0):
    """Mashqdagi bitta yurishni tekshiradi. Holatsiz: mijoz joriy FEN va yig'ilgan yulduzlarni yuboradi."""
    les = BY_CODE.get(les_code)
    if not les or not (0 <= i < len(les["mashqlar"])):
        raise HTTPException(404, "Mashq topilmadi")
    ex = les["mashqlar"][i]
    side = eng.side_to_move(fen)
    move = eng.find_move(fen, side, path)
    if ex["tur"] == "katak":
        raise HTTPException(400, "Bu mashq taxtada tekshiriladi")
    if not move:
        return {"togri": False, "xabar": "Bu figura bunday yura olmaydi. Qayta urinib ko'ring!"}
    b = eng.Board(fen)
    m = (move["from"], move["to"], move.get("promo") or "")
    if ex["tur"] == "yulduz":
        nxt = keep_white(eng.apply_move(fen, move))
        got = sorted(set(got) | ({eng.sq_name(move["to"])} & set(ex["yulduzlar"])))
        done = set(got) == set(ex["yulduzlar"])
        return {"togri": True, "fen": nxt, "yigildi": got, "tugadi": done, "mumkin": [] if done else mumkin(nxt),
                "xabar": "⭐ Barakalla!" if eng.sq_name(move["to"]) in ex["yulduzlar"] else ""}
    if ex["tur"] == "shax":
        want = ex["usul"]
        got_method = method_of(b, m)
        if got_method != want:
            hints = {"qoch": "Bu safar shohning o'zi qochishi kerak.", "tos": "Bu safar shaxni orasiga figura qo'yib to'sing.",
                     "ur": "Bu safar hujum qilayotgan figurani urib oling."}
            return {"togri": False, "xabar": "Bu ham shaxdan qutqaradi, lekin vazifa boshqacha. " + hints[want]}
        return {"togri": True, "fen": eng.apply_move(fen, move), "tugadi": True, "mumkin": [], "xabar": "✅ Shoh qutqarildi!"}
    if ex["tur"] == "mat":
        remaining = ex["n"] - step
        u = b.make(m)
        if is_mate(b):
            fen2 = b.fen()
            return {"togri": True, "fen": fen2, "tugadi": True, "mumkin": [], "xabar": "🏆 MAT! Zo'r!"}
        good = remaining > 1 and bool(b.legal()) and all_replies_mate(b, remaining - 1)
        if not good:
            b.unmake(u)
            return {"togri": False, "xabar": "Bu yurishdan keyin raqib qutulib ketadi. Boshqa yurishni qidiring!"}
        reply = best_defence(b, remaining - 1)
        reply_san = b.san(reply)
        b.make(reply)
        fen2 = b.fen()
        return {"togri": True, "fen": fen2, "tugadi": False, "mumkin": mumkin(fen2), "javob": [eng.sq_name(reply[0]), eng.sq_name(reply[1])],
                "javob_yozuv": reply_san, "xabar": "👍 To'g'ri! Raqib javob berdi — endi mat qiling."}
    if ex["tur"] == "yechim":
        sol = ex["yechim"]
        if step * 2 >= len(sol) or uci(move) != sol[step * 2]:
            return {"togri": False, "xabar": "Yaxshiroq yurish bor. Vazifani qayta o'qing va urinib ko'ring!"}
        fen2 = eng.apply_move(fen, move)
        if step * 2 + 1 >= len(sol):
            return {"togri": True, "fen": fen2, "tugadi": True, "mumkin": [], "xabar": "🎉 Ajoyib!"}
        reply = eng.find_move(fen2, eng.side_to_move(fen2), [sol[step * 2 + 1][:2], sol[step * 2 + 1][2:4]])
        san_reply = eng.san(fen2, reply)
        fen3 = eng.apply_move(fen2, reply)
        return {"togri": True, "fen": fen3, "tugadi": False, "mumkin": mumkin(fen3), "javob": eng.move_names(reply)[:2],
                "javob_yozuv": san_reply, "xabar": "👍 To'g'ri! Raqib javob berdi — davom eting."}
    raise HTTPException(400, "Noma'lum mashq turi")


def stars_for(mistakes, moves=None, par=None):
    if par:
        extra = max(0, (moves or 0) - par)
        return 3 if extra == 0 and not mistakes else 2 if extra <= 2 and mistakes <= 1 else 1
    return 3 if mistakes == 0 else 2 if mistakes <= 2 else 1


# ── API ──
class MoveIn(BaseModel):
    token: Optional[str] = None
    fen: str = Field(min_length=10, max_length=100)
    path: List[str] = Field(min_length=2, max_length=3)
    yigildi: List[str] = Field(default_factory=list, max_length=16)
    qadam: int = Field(default=0, ge=0, le=10)


class ResultIn(BaseModel):
    token: Optional[str] = None
    yulduz: int = Field(ge=1, le=3)


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shaxmat_maktab (
            user_id BIGINT NOT NULL,
            dars TEXT NOT NULL,
            yulduz INT NOT NULL DEFAULT 0,
            urinish INT NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, dars)
        )""")


def create_router(platform):
    router = APIRouter()
    ready = {"ok": False}

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def open_db():
        conn = platform._db()
        cur = conn.cursor()
        if not ready["ok"]:
            migrate(cur)
            conn.commit()
            ready["ok"] = True
        return conn, cur

    def progress(cur, user_id):
        cur.execute("SELECT dars, yulduz FROM shaxmat_maktab WHERE user_id=%s", (user_id,))
        return {r["dars"]: r["yulduz"] for r in cur.fetchall()}

    def unlocked(done, les):
        return les["tartib"] == 0 or bool(done.get(LESSONS[les["tartib"] - 1]["kod"]))

    @router.get("/api/shaxmat/maktab")
    def school(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        conn, cur = open_db()
        try:
            done = progress(cur, user_id)
            conn.commit()
        finally:
            cur.close()
            conn.close()
        units = []
        for unit in UNITS:
            units.append({"nomi": unit["nomi"], "emoji": unit["emoji"], "darslar": [
                {"kod": d["kod"], "nomi": d["nomi"], "emoji": d["emoji"], "mashqlar": len(d["mashqlar"]),
                 "yulduz": done.get(d["kod"], 0), "ochiq": unlocked(done, BY_CODE[d["kod"]])} for d in unit["darslar"]]})
        total = sum(done.get(d["kod"], 0) for d in LESSONS)
        return {"bolimlar": units, "yulduzlar": total, "jami": len(LESSONS) * 3,
                "tugatildi": sum(1 for d in LESSONS if done.get(d["kod"]))}

    @router.get("/api/shaxmat/maktab/{dars}")
    def lesson(dars: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        les = BY_CODE.get(dars)
        if not les:
            raise HTTPException(404, "Dars topilmadi")
        conn, cur = open_db()
        try:
            done = progress(cur, user_id)
            conn.commit()
        finally:
            cur.close()
            conn.close()
        if not unlocked(done, les):
            raise HTTPException(403, "Avval oldingi darsni tugating")
        nxt = LESSONS[les["tartib"] + 1]["kod"] if les["tartib"] + 1 < len(LESSONS) else None
        return {"kod": les["kod"], "nomi": les["nomi"], "emoji": les["emoji"], "matn": les["matn"],
                "mashqlar": [public_exercise(les["kod"], i, ex) for i, ex in enumerate(les["mashqlar"])],
                "yulduz": done.get(les["kod"], 0), "keyingi": nxt}

    @router.post("/api/shaxmat/maktab/{dars}/{index}/yur")
    def move(dars: str, index: int, body: MoveIn, authorization: str = Header(None)):
        uid_of(body.token, authorization)
        try:
            eng.Board(body.fen)
        except Exception:
            raise HTTPException(400, "Pozitsiya noto'g'ri")
        return check_move(dars, index, body.fen, body.path, body.yigildi, body.qadam)

    @router.post("/api/shaxmat/maktab/{dars}/natija")
    def result(dars: str, body: ResultIn, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        if dars not in BY_CODE:
            raise HTTPException(404, "Dars topilmadi")
        conn, cur = open_db()
        try:
            cur.execute("""INSERT INTO shaxmat_maktab(user_id, dars, yulduz, urinish) VALUES(%s,%s,%s,1)
                           ON CONFLICT(user_id, dars) DO UPDATE SET yulduz=GREATEST(shaxmat_maktab.yulduz, EXCLUDED.yulduz),
                             urinish=shaxmat_maktab.urinish+1, updated_at=NOW()""", (user_id, dars, body.yulduz))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return {"ok": True}

    return router
