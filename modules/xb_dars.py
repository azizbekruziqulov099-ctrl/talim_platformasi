"""Fakt banklari va o'qish matnlaridan chuqur dars qadamlarini yig'ish (4–7 qadam)."""

def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}


def _qadamlar_fakt(nom, banki):
    q = []
    parcha = [banki[i:i + 3] for i in range(0, len(banki), 3)]
    for k, p in enumerate(parcha[:3], 1):
        doska = "\n".join(f"• {x[0]}\n   ✅ {x[1]}" for x in p)
        ovoz = f"{k}-qism. " + " ".join(f"{x[0]} Javob: {x[1]}. {x[3]}" for x in p)
        q.append(_d(f"{k}-qism: asosiy bilimlar", doska, ovoz))
    x = banki[0]
    q.append(_d("Hayotiy holat", f"Vaziyat: {x[0]}\n1. Savolni o‘qi\n2. Muhim so‘zni top\n3. Sababini o‘yla\n4. Javob: {x[1]}",
                f"Hayotda shunday holat uchrasa, avval savolni diqqat bilan o‘qing, kalit so‘zni toping va sababini o‘ylang. Masalan: {x[0]} To‘g‘ri javob: {x[1]}."))
    y = banki[1]
    q.append(_d("Ko‘p uchraydigan xato", f"❌ {y[2][0]}\n✅ {y[1]}\nNima uchun? {y[3]}",
                f"Ko‘pchilik bu yerda {y[2][0]} deb xato qiladi. To‘g‘ri javob: {y[1]}. {y[3]}"))
    return q


def _qadamlar_matn(matnlar):
    q = []
    for k, (matn, qs) in enumerate(matnlar[:3], 1):
        s, tj, no = qs[0]
        q.append(_d(f"Matn {k}: o‘qiymiz va javob topamiz", f"{matn}\n\nSavol: {s}\n✅ {tj}",
                    f"Matnni o‘qing: {matn} Savol: {s} Javob: {tj}. Javob matnda yoki undan kelib chiqadigan mantiqda bor."))
    s, tj, no = matnlar[0][1][0]
    q.append(_d("Xato javobdan qanday qochamiz", f"❌ {no[0]}\n✅ {tj}\nMatndan dalil top!", f"Chalg‘ituvchi javob: {no[0]}. U matnda tasdiqlanmaydi. To‘g‘ri javob: {tj}."))
    return q


def _matem_qadamlar(kod):
    """Matematika mavzusi uchun: hayotiy PISA holat va xato-tuzatish (generatordan, har safar bir xil)."""
    import random
    from modules import pisa_mat_g as G
    out = []
    shab = G.SH.get(kod, [])
    och = [f for f, t in shab if t == "ochiq"]
    yop = [f for f, t in shab if t == "yopiq"]
    if och:
        q = och[0](random.Random(21))
        qism = "\n".join(x["savol"] for x in q["qismlar"])
        out.append(_d("Hayotiy PISA holat", f"{q['savol']}\n{qism}\n\nYechim:\n{q['yechim']}", f"Hayotiy holat. {q['savol']} {qism.replace(chr(10), ' ')} Yechim. {q['yechim'].replace(chr(10), ' ')}"))
    if yop:
        q = yop[-1](random.Random(33))
        v = q["variantlar"]; j = "ABCD".index(q["javob"]) if isinstance(q["javob"], str) and q["javob"] in "ABCD" else 0
        xato = next((x for i, x in enumerate(v) if i != j), "")
        out.append(_d("Ko‘p uchraydigan xato", f"{q['savol']}\n❌ {xato}\n✅ {v[j]}\n{q['yechim']}", f"Ko‘p o‘quvchilar bu yerda {xato.replace('$', '')} deb xato qiladi. {q['yechim'].replace(chr(10), ' ')} To‘g‘ri javob: {v[j].replace('$', '')}."))
    return out


def boyit(M):
    try:
        from modules import xb_ps
    except Exception:
        return
    for kod, t in list(M.items()):
        try:
            if kod[:2] in ("M4", "M8", "PF") and not t.get("_boy"):
                t["dars"] = list(t["dars"]) + _matem_qadamlar(kod); t["_boy"] = 1
                continue
            if len(t.get("dars", [])) >= 4:
                continue
            if kod in xb_ps.BANK:
                t["dars"] = list(t["dars"]) + _qadamlar_fakt(t["nom"], xb_ps.BANK[kod])
            elif kod in xb_ps._matnlar:
                t["dars"] = list(t["dars"]) + _qadamlar_matn(xb_ps._matnlar[kod])
        except Exception:
            pass
