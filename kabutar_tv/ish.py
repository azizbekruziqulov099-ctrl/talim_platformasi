"""Tungi ish: python -m modules.kabutar_tv.ish --sana 2026-10-28 [--tillar en,de] [--darajalar 1-sinf,2-sinf] [--majburiy]"""
import argparse
import datetime as dt

from .kanal import kun_ishi

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sana", default=dt.date.today().isoformat())
    p.add_argument("--tillar", default="")
    p.add_argument("--darajalar", default="")
    p.add_argument("--majburiy", action="store_true")
    a = p.parse_args()
    kun_ishi(dt.date.fromisoformat(a.sana), [x for x in a.tillar.split(",") if x] or None,
             [x for x in a.darajalar.split(",") if x] or None, a.majburiy, log=lambda m: print(m, flush=True))
