from modules import oyin_xona as o

def test_qulf_va_kunlik_ochilish():
    h = {}
    h, x = o.otdi(h, 116, 1, 3, False, "2026-11-07"); assert x is None and h["116"]["1"]["yulduz"] == 3
    h2, x = o.otdi(h, 116, 2, 3, True, "2026-11-07"); assert x == "ertaga" and h2 == h     # o'sha kuni ochilmaydi
    h3, x = o.otdi(h, 116, 2, 2, False, "2026-11-08"); assert x == "obuna"                  # obunasiz — yo'q
    h4, x = o.otdi(h, 116, 2, 2, True, "2026-11-08"); assert x is None and "2" in h4["116"]
    _, x = o.otdi(h4, 116, 4, 3, True, "2026-11-09"); assert x == "qulf"                    # sakrab bo'lmaydi
    _, x = o.otdi(h4, 116, 3, 0, True, "2026-11-09"); assert x == "otmadi"
    h5, x = o.otdi(h4, 116, 1, 1, True, "2026-11-09"); assert x is None and h5["116"]["1"]["yulduz"] == 3 and h5["116"]["1"]["sana"] == "2026-11-07"
    _, x = o.otdi({}, 999, 1, 3, True, "2026-11-09"); assert x == "nomalum"
    _, x = o.otdi({}, 152, 1, 3, True, "2026-11-09"); assert x is None   # REV379: yangi o'yinlar ham
