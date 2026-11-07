from modules import xalqaro_baholash as xb

def _s(i, foiz, rasm=False):
    return {"id": f"S{i:02d}", "xalqaro_ortacha": foiz, "variantlar": [{"rasm": "<svg/>" if rasm else None}]}

def test_toplamlar_osondan_qiyinga_va_rasmlar_taqsimlanadi():
    qs = [_s(i, 90 - i * 3, rasm=i in (20, 21)) for i in range(22)]
    tl = xb.mavzu_toplamlari(qs)
    assert [len(t) for t in tl] == [8, 7, 7]
    assert sum(len(t) for t in tl) == 22 and len({s["id"] for t in tl for s in t}) == 22
    # oson to'plamdagi savollar oxirgisidan osonroq
    assert max(xb.savol_qiyinligi(s) for s in tl[0]) < min(xb.savol_qiyinligi(s) for s in tl[2])   # oson < imtihon
    assert sum(1 for t in tl if any(v.get("rasm") for s in t for v in s["variantlar"])) >= 2    # rasm qo'shni to'plamga ham o'tdi
    assert [xb.toplam_darajasi(i, 3) for i in (1, 2, 3)] == ["oson", "orta", "imtihon"]
    assert xb.toplam_darajasi(3, 4) == "qiyin"
    assert xb.mavzu_toplamlari([]) == []
