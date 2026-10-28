#!/usr/bin/env python3
"""Put APPROVED posts into queue/ for the free publisher (publisher/publish.py).

Only the approval agent runs this, and only for posts Therm approved.

  Carousel (all networks at the slot time; Reel 1 hour later only with --reel):
    python3 publisher/enqueue.py carousel specs/2026-10-24_A.json --time 04:45 [--date 2026-10-24] [--reel] [--manual-ig]
  Quote story (IG Story + Threads + TikTok):
    python3 publisher/enqueue.py quote Q2610-03 --date 2026-10-24 --time 09:15 --text "The quote"
  Home Tour Reel (after the tour-render workflow set the spec to "rendered"):
    python3 publisher/enqueue.py tour tours/specs/2026-10-25_T.json [--time 09:45]
  Business card story (pre-approved, Mon/Wed/Fri 7:15 AM):
    python3 publisher/enqueue.py card --date 2026-10-26 --time 07:15

Options: --platforms instagram,facebook,threads,tiktok (default: all four), --replace to rewrite
items that are still queued (published items are never touched).
Then commit and push queue/ ; GitHub Actions posts each item at its time.
"""
import argparse, datetime as dt, glob, json, os, re, sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = "https://raw.githubusercontent.com/thermanrouse24/nj-dream-home-carousels/main/"
NY = ZoneInfo("America/New_York")
CTA = "Click the link in my bio."
TIKTOK_CTA = 'DM me "HOME" to get started.'
FOOTER = "Therm The Realtor | eXp Realty"
ALL = ["instagram", "facebook", "threads", "tiktok"]


def at(date, hhmm, plus_min=0):
    d = dt.datetime.strptime(f"{date} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=NY)
    return (d + dt.timedelta(minutes=plus_min)).isoformat()


def need(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        sys.exit(f"missing file: {path} (render it and push it first)")
    return RAW + path


def write(items, replace):
    out = []
    for it in items:
        it.setdefault("status", "queued")
        it["approved_by"] = "Therm"
        it["queued_at"] = dt.datetime.now(NY).isoformat(timespec="seconds")
        folder = os.path.join(ROOT, "queue", it["publish_at"][:10])
        os.makedirs(folder, exist_ok=True)
        f = os.path.join(folder, it["id"] + ".json")
        if os.path.exists(f):
            old = json.load(open(f))
            if old.get("status") not in ("queued", "retry", "invalid") or not replace:
                print(f"skip {it['id']} (already in queue: {old.get('status')})")
                continue
        with open(f, "w") as fh:
            json.dump(it, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        out.append(os.path.relpath(f, ROOT))
        print("queued", it["id"], it["publish_at"])
    return out


def carousel(a):
    spec = json.load(open(os.path.join(ROOT, a.spec)))
    sid = spec["id"]                          # e.g. 2026-10-24_A_flood
    date = a.date or sid[:10]
    slot = sid.split("_")[1]
    base = f"posts/{sid[:10]}/{sid}"     # files live under the spec's own date
    jpgs = [need(f"{base}_{n}of6.jpg") for n in range(1, 7)]
    ig_media = []
    for n in range(1, 7):                     # motion MP4 replaces a stat slide on Instagram only
        mp4 = f"{base}_{n}of6.mp4"
        ig_media.append(RAW + mp4 if os.path.exists(os.path.join(ROOT, mp4)) else jpgs[n - 1])
    plan = (spec.get("story_plan") or {}).get("frames") or [1]
    stories = [need(f"{base}_story_{n}of6.jpg") for n in plan]
    tiktok_last = f"{base}_6of6_tiktok.jpg"
    tiktok_media = jpgs[:5] + [need(tiktok_last)]
    caption = spec["caption"]
    short = spec.get("threads_caption") or ""
    if not short or sum(len(c.encode()) if ord(c) > 0xFFFF else 1 for c in short) > 500:
        sys.exit("spec needs a threads_caption of 500 characters or fewer")
    tk_caption = caption.replace(CTA, TIKTOK_CTA)
    if TIKTOK_CTA not in tk_caption:      # Therm's rule: every TikTok post says DM me "HOME"
        tk_caption = tk_caption.replace(FOOTER, f"{TIKTOK_CTA}\n\n{FOOTER}") if FOOTER in tk_caption else f"{tk_caption}\n\n{TIKTOK_CTA}"
    t = at(date, a.time)
    p = f"{date}_{slot}"
    items = []
    if "instagram" in a.platforms:
        if a.manual_ig:
            print("MANUAL: Instagram feed carousel left for Therm to post by hand (song: %s)" % spec.get("music", {}).get("ig_audio"))
        else:
            items.append({"id": f"{p}_ig_feed", "platform": "instagram", "type": "carousel", "publish_at": t,
                          "media": ig_media, "caption": caption})
        items.append({"id": f"{p}_ig_story", "platform": "instagram", "type": "story", "publish_at": t,
                      "media": stories, "story_plan": spec.get("story_plan")})
        if a.reel:
            reel = f"{base}_reel.mp4"
            if os.path.exists(os.path.join(ROOT, reel)):
                items.append({"id": f"{p}_ig_reel", "platform": "instagram", "type": "reel",
                              "publish_at": at(date, a.time, 60), "media": [RAW + reel], "caption": caption,
                              "note": "API cannot attach licensed music; posts with the file's own (silent) audio"})
    if "facebook" in a.platforms:
        items.append({"id": f"{p}_fb", "platform": "facebook", "type": "photos", "publish_at": t,
                      "media": jpgs, "caption": caption})
    if "threads" in a.platforms:
        items.append({"id": f"{p}_threads", "platform": "threads", "type": "carousel", "publish_at": t,
                      "media": jpgs, "caption": short})
    if "tiktok" in a.platforms:
        items.append({"id": f"{p}_tiktok", "platform": "tiktok", "type": "photos", "publish_at": t,
                      "media": tiktok_media, "caption": tk_caption})
    return items


def quote(a):
    month = a.date[:7]
    story = need(f"quotes/{month}/{a.quote_id}_story.jpg")
    square = need(f"quotes/{month}/{a.quote_id}_square.jpg")
    text = re.sub(r"\[\[|\]\]", "", a.text).strip()
    t = at(a.date, a.time)
    p = f"{a.date}_{a.quote_id}"
    items = []
    if "instagram" in a.platforms:
        items.append({"id": f"{p}_ig_story", "platform": "instagram", "type": "story", "publish_at": t, "media": [story]})
    if "threads" in a.platforms:
        items.append({"id": f"{p}_threads", "platform": "threads", "type": "image", "publish_at": t, "media": [square], "caption": text})
    if "tiktok" in a.platforms:
        items.append({"id": f"{p}_tiktok", "platform": "tiktok", "type": "photos", "publish_at": t, "media": [story],
                      "caption": f"{text}\n\n{TIKTOK_CTA}\n\n{FOOTER}"})
    return items


def card(a):
    t = at(a.date, a.time)
    p = f"{a.date}_card"
    items = []
    if "instagram" in a.platforms:
        items.append({"id": f"{p}_ig_story", "platform": "instagram", "type": "story", "publish_at": t,
                      "media": [need("business_card_story.jpg")]})
    if "threads" in a.platforms:
        items.append({"id": f"{p}_threads", "platform": "threads", "type": "image", "publish_at": t,
                      "media": [need("business_card.jpg")],
                      "caption": f"Buying your first home in New Jersey? {CTA}\n\n{FOOTER}"})
    if "tiktok" in a.platforms:
        items.append({"id": f"{p}_tiktok", "platform": "tiktok", "type": "photos", "publish_at": t,
                      "media": [need("business_card_story_tiktok.jpg")],
                      "caption": f"Buying your first home in New Jersey? {TIKTOK_CTA}\n\n{FOOTER}"})
    return items


def tour(a):
    """Home Tour Reel (Therm's rule, Oct 24 2026): IG Reel + Facebook Reel + TikTok video, 9:45 AM."""
    spec = json.load(open(os.path.join(ROOT, a.spec)))
    if spec.get("status") != "rendered":
        sys.exit(f"tour {spec.get('id')} is not rendered yet (status {spec.get('status')})")
    # Therm's rule (Oct 28 2026, evening): every tour gets a song through the Instagram Audio API and
    # posts as an Instagram Reel WITHOUT his approval, as long as the music is attached. Only the
    # Instagram Reel can carry API music, so only it is queued; Facebook and TikTok stay in his post kit.
    if spec.get("ig_audio_id") or spec.get("ig_audio"):
        date = a.date or spec["date"]
        return [{"id": f"{date}_T_ig_reel", "platform": "instagram", "type": "reel",
                 "publish_at": at(date, a.time), "media": [spec["ig_url"]], "caption": spec["caption"],
                 "tour": spec["id"], "has_music": True, "ig_audio_id": spec.get("ig_audio_id"),
                 "ig_audio": spec.get("ig_audio") or "auto",
                 "ig_audio_backup": spec.get("ig_audio_backup") or "auto",
                 "audio_volume": spec.get("audio_volume", 100),
                 "video_volume": spec.get("video_volume", 0 if not spec.get("render_info", {}).get("source_has_audio") else 30)}]
    # Older rule (Oct 28 2026 morning): no API music -> Therm posts it himself from a post kit.
    if not a.auto:
        sys.exit(f"tour {spec.get('id')}: tours are posted by Therm with trending music. "
                 "Run python3 tours/handoff.py instead (Therm, Oct 28 2026).")
    if not spec.get("render_info", {}).get("has_music"):
        sys.exit(f"tour {spec.get('id')} has NO music (silent video): not queued. Therm's rule: never post tours without music.")
    date = a.date or spec["date"]
    t = at(date, a.time)
    p = f"{date}_T"
    caption = spec["caption"]
    tk = spec.get("tiktok_caption") or caption.replace(CTA, TIKTOK_CTA)
    if TIKTOK_CTA not in tk:
        tk = tk.replace(FOOTER, f"{TIKTOK_CTA}\n\n{FOOTER}") if FOOTER in tk else f"{tk}\n\n{TIKTOK_CTA}"
    items = []
    if "instagram" in a.platforms:
        items.append({"id": f"{p}_ig_reel", "platform": "instagram", "type": "reel", "publish_at": t,
                      "media": [spec["ig_url"]], "caption": caption, "tour": spec["id"], "has_music": True})
    if "facebook" in a.platforms:
        items.append({"id": f"{p}_fb_reel", "platform": "facebook", "type": "reel", "publish_at": t,
                      "media": [spec["ig_url"]], "caption": caption, "tour": spec["id"], "has_music": True})
    if "tiktok" in a.platforms:
        items.append({"id": f"{p}_tiktok", "platform": "tiktok", "type": "video", "publish_at": t,
                      "media": [spec["tiktok_url"]], "caption": tk, "tour": spec["id"], "has_music": True})
    return items


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="kind", required=True)
    c = sub.add_parser("carousel"); c.add_argument("spec"); c.add_argument("--date"); c.add_argument("--time", required=True)
    c.add_argument("--reel", action="store_true"); c.add_argument("--manual-ig", action="store_true")
    q = sub.add_parser("quote"); q.add_argument("quote_id"); q.add_argument("--date", required=True)
    q.add_argument("--time", required=True); q.add_argument("--text", required=True)
    k = sub.add_parser("card"); k.add_argument("--date", required=True); k.add_argument("--time", default="07:15")
    tr = sub.add_parser("tour"); tr.add_argument("spec"); tr.add_argument("--date"); tr.add_argument("--time", default="09:45")
    tr.add_argument("--auto", action="store_true", help="only if Therm explicitly asks to auto-post a tour that already has music")
    for s in (c, q, k, tr):
        s.add_argument("--platforms", default=",".join(ALL)); s.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    a.platforms = [x.strip() for x in a.platforms.split(",") if x.strip()]
    if a.kind == "tour" and a.platforms == ALL:  # (music tours queue Instagram only, see tour())
        a.platforms = ["instagram", "facebook", "tiktok"]   # Therm: IG Reel + TikTok + Facebook
    items = {"carousel": carousel, "quote": quote, "card": card, "tour": tour}[a.kind](a)
    now = dt.datetime.now(NY)
    for it in items:
        if dt.datetime.fromisoformat(it["publish_at"]) < now + dt.timedelta(minutes=5):
            sys.exit(f"{it['id']} time {it['publish_at']} is in the past or too close; pick a later time")
    write(items, a.replace)


if __name__ == "__main__":
    main()
