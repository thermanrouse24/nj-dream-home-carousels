#!/usr/bin/env python3
"""Instagram music for home tours (Therm, Oct 28 2026: every tour gets a song; it posts without
his approval as long as the music is attached).

Run by the "Render home tour" workflow (it has the Meta secrets). For every tours/specs/*_T.json
that is "rendered" and has no "audio_candidates" yet, it saves Instagram's current trending MUSIC
(Instagram Audio API, clean titles only, 30 s or longer) into the spec, plus the search results for
the Brain's pick (spec["music"]["ig_audio"]) if there is one. The daily build then picks one and
sets "ig_audio_id" + "ig_audio" ("Title - Artist") in the spec. If nobody picked, the publisher
uses the first clean trending track at post time. Never posts anything.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "publisher"))
import ig_audio

tok, ig = os.environ.get("META_PAGE_TOKEN", "").strip(), os.environ.get("IG_USER_ID", "").strip()
if not tok or not ig:
    sys.exit("no Meta secrets: skipping audio candidates")
here = os.path.dirname(os.path.abspath(__file__))
for p in sorted(glob.glob(os.path.join(here, "specs", "*_T.json"))):
    s = json.load(open(p))
    if s.get("status") != "rendered" or s.get("audio_candidates") or s.get("ig_audio_id"):
        continue
    cands = ig_audio.trending(tok, ig)[:20]
    want = (s.get("music") or {}).get("ig_audio")
    if want:
        res, _, _ = ig_audio.search(tok, ig, want.split(" - ")[0])
        cands = [r for r in res if ig_audio.clean(r)][:10] + cands
    s["audio_candidates"] = cands
    json.dump(s, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"{os.path.basename(p)}: {len(cands)} audio candidates")
