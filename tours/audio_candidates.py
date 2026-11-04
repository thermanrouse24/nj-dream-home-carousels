#!/usr/bin/env python3
"""Instagram music for home tours (Therm, Nov 4 2026: trending HIP HOP, R&B or POP that clients enjoy).

Run by the "Render home tour" workflow (it has the Meta secrets). Instagram's trending list has no genre
and is full of film scores, covers and sound-alikes, so it is NOT used. The daily build writes
"ig_song_wants" (["Title - Artist", ...] from this week's hip hop, R&B and pop charts) in the spec. For
every rendered tours/specs/*_T.json with wants and no "audio_candidates" yet, this looks up each song and
keeps only clean results whose title AND artist match. The pick goes in the approval email. Never posts.
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
    wants, cands = s.get("ig_song_wants") or [], []
    for want in wants:
        title, _, artist = want.partition(" - ")
        res, _, _ = ig_audio.search(tok, ig, want.replace(" - ", " "))
        first = (artist.split(",")[0].split("&")[0].strip() or title).lower()
        cands += [r for r in res if ig_audio.clean(r) and title.strip().lower() in (r.get("title") or "").lower()
                  and first in (r.get("artist") or "").lower()][:1]
    if not cands:
        print(f"{os.path.basename(p)}: no wanted song found on Instagram"); continue
    s["audio_candidates"] = cands
    json.dump(s, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"{os.path.basename(p)}: {len(cands)} audio candidates")
