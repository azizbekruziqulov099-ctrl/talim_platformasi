"""REV202: LAB-SINXRON — og'iz ovozga millisoniyagacha mos bo'lsin.

Rhubarb Lip Sync (bepul, MIT litsenziya) ovozni tinglab, qaysi paytda qaysi og'iz shakli (A–H, X) kerakligini aytadi.
Serverda birinchi marta ishlatilganda GitHub'dan o'zi yuklab olinadi (KABUTAR_TV_DIR/tools). Yuklanmasa yoki xato
bersa — oldingi usul (so'z va harflar bo'yicha) ishlaydi, ko'rsatuv to'xtamaydi.
"""
import bisect
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import wave

URL = "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.13.0/Rhubarb-Lip-Sync-1.13.0-Linux.zip"
_qulf = threading.Lock()
_holat = {"yol": None, "urindi": False}


def _papka():
    return os.path.join(os.environ.get("KABUTAR_TV_DIR") or os.path.join(os.getcwd(), "kabutar_tv_data"), "tools")


def rhubarb():
    """Rhubarb dasturining yo'li (kerak bo'lsa yuklab oladi). Bo'lmasa — None."""
    if _holat["yol"]:
        return _holat["yol"]
    env = os.environ.get("RHUBARB_PATH")
    if env and os.path.exists(env):
        _holat["yol"] = env
        return env
    with _qulf:
        if _holat["yol"] or _holat["urindi"]:
            return _holat["yol"]
        _holat["urindi"] = True
        tayyor = os.path.join(_papka(), "Rhubarb-Lip-Sync-1.13.0-Linux", "rhubarb")
        if not os.path.exists(tayyor):
            try:
                import urllib.request
                import zipfile
                os.makedirs(_papka(), exist_ok=True)
                zp = os.path.join(_papka(), "rhubarb.zip")
                urllib.request.urlretrieve(URL, zp)
                with zipfile.ZipFile(zp) as z:
                    for n in z.namelist():   # faqat kerakli qismlar (dastur, res, lib)
                        if n.endswith("/rhubarb") or "/res/" in n or "/lib/" in n:
                            z.extract(n, _papka())
                os.remove(zp)
                os.chmod(tayyor, 0o755)
            except Exception as exc:
                print(f"[labsinx] Rhubarb yuklanmadi: {exc}", flush=True)
                return None
        _holat["yol"] = tayyor if os.path.exists(tayyor) else None
        return _holat["yol"]


def belgilar(pcm, sr, matn="", til="en", kesh=None):
    """PCM (s16 mono) → [(boshlanish, shakl)] yoki None. Natija keshlanadi."""
    yol = rhubarb()
    if not yol or not pcm:
        return None
    kalit = hashlib.sha1(pcm[:200000] + str(len(pcm)).encode() + matn.encode()).hexdigest()
    kp = os.path.join(kesh, f"lab_{kalit}.json") if kesh else None
    if kp and os.path.exists(kp):
        try:
            return [tuple(x) for x in json.load(open(kp))]
        except Exception:
            pass
    ish = tempfile.mkdtemp(prefix="lab_")
    try:
        wav = os.path.join(ish, "o.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm)
        cmd = [yol, "-f", "json", "--quiet", "--extendedShapes", "GHX"]
        if til == "en" and matn:
            dlg = os.path.join(ish, "d.txt")
            with open(dlg, "w", encoding="utf-8") as f:
                f.write(matn)
            cmd += ["-r", "pocketSphinx", "-d", dlg]
        else:
            cmd += ["-r", "phonetic"]   # boshqa tillar uchun — tildan qat'i nazar ishlaydi
        r = subprocess.run(cmd + [wav], capture_output=True, timeout=120)
        if r.returncode != 0:
            return None
        d = json.loads(r.stdout.decode("utf-8"))
        out = [(float(c["start"]), c["value"]) for c in d.get("mouthCues", [])]
        if kp:
            json.dump(out, open(kp, "w"))
        return out
    except Exception:
        return None
    finally:
        shutil.rmtree(ish, ignore_errors=True)


def shakl(cues, t):
    """t paytdagi og'iz shakli."""
    if not cues:
        return "X"
    i = bisect.bisect_right([c[0] for c in cues], t) - 1
    return cues[i][1] if i >= 0 else "X"
