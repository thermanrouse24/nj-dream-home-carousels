#!/usr/bin/env python3
"""Put the next approved home tour caption (tours/captions.json, rotating 1, 2, 3) into a tour spec.

Usage: python3 tours/set_caption.py tours/specs/<date>_T.json
Therm's rule (Oct 25 2026): only these 3 captions, word for word; no town/county/price/beds/baths,
no listing broker or agent. The next option follows the last spec (by date) that has caption_option.
"""
import glob, json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
caps = json.load(open(os.path.join(here, "captions.json")))["captions"]
path = sys.argv[1]
spec = json.load(open(path))
last = 0
for f in sorted(glob.glob(os.path.join(here, "specs", "*_T.json"))):
    if os.path.abspath(f) == os.path.abspath(path):
        continue
    d = json.load(open(f))
    if d.get("caption_option") and d.get("date", "") < spec.get("date", "9999"):
        last = d["caption_option"]
opt = spec.get("caption_option") or (last % len(caps)) + 1
c = next(x for x in caps if x["option"] == opt)
spec.update(caption_option=opt, caption=c["caption"], tiktok_caption=c["tiktok_caption"])
json.dump(spec, open(path, "w"), ensure_ascii=False, indent=1)
print(f"{path}: caption option {opt}")
