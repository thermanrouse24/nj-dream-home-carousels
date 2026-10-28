#!/usr/bin/env python3
"""Home tour "post kit" for Therm (Therm's rule, Oct 28 2026: tours are never posted without music,
and he wants TRENDING music, which only the Instagram / Facebook / TikTok apps can add).

So approved tours are NOT queued for the free publisher. Instead the Execution agent:
  1. runs   python3 tours/handoff.py tours/specs/<date>_T.json [--time 09:45] [--song "Title - Artist"]
  2. sends Therm the email this prints (subject + HTML; the cover picture goes INLINE via
     tools/email_images.py, <img src="cid:att0">) right away, so the kit is in his inbox;
  3. creates a Google Calendar event at the post time, "POST HOME TOUR NOW - <town>", 10 minutes long,
     pop-up alerts at 0 and 1 minute before, description = the "calendar" text this prints;
  4. sets the spec's "handoff" field (this script does it) and logs the Content Log row as
     "Sent to Therm to post <time> with trending music: IG Reel (+ share to FB), TikTok (DM HOME)".

Prints JSON: {"subject", "html", "text", "calendar", "cover", "time"}.
"""
import argparse, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--time", default="09:45"); ap.add_argument("--song", default="")
    a = ap.parse_args()
    path = os.path.join(ROOT, a.spec)
    s = json.load(open(path))
    if s.get("status") != "rendered":
        sys.exit(f"tour {s.get('id')} is not rendered yet (status {s.get('status')})")
    ri = s.get("render_info", {})
    if ri.get("phone_replaced") is None:
        print("NOTE: no Call/Text bar was replaced. Look at the preview: if it shows anyone else's name "
              "or number, do NOT send it.", file=sys.stderr)
    hh, mm = map(int, a.time.split(":"))
    t12 = f"{(hh % 12) or 12}:{mm:02d} {'AM' if hh < 12 else 'PM'}"
    town = s.get("town", "")
    song = a.song or (s.get("music") or {}).get("ig_audio", "")
    song_line = (f"Suggested trending song: {song} (or any trending sound you like)" if song
                 else "Pick any trending sound in the app.")
    steps = [
        "Instagram: download the IG video, open Instagram, New Reel, pick the video, tap the music note and "
        "add a trending song, paste the caption, turn on Share to Facebook, Share.",
        "TikTok: download the TikTok video, open TikTok, +, Upload, tap Sounds and add a trending sound, "
        "paste the TikTok caption (it says DM me \"HOME\"), Post.",
    ]
    subject = f"POST AT {t12}: home tour {town} (add a trending song)"
    h = [f"<p><b>Your approved home tour is ready to post at {t12}.</b> {html.escape(song_line)}</p>",
         '<p><img src="cid:att0" width="300" alt="cover"></p>',
         f'<p>IG / Facebook video: <a href="{s["ig_url"]}">{html.escape(s["ig_url"])}</a><br>'
         f'TikTok video: <a href="{s["tiktok_url"]}">{html.escape(s["tiktok_url"])}</a></p>',
         "<ol>" + "".join(f"<li>{html.escape(x)}</li>" for x in steps) + "</ol>",
         "<p><b>Instagram / Facebook caption</b></p><pre style=\"white-space:pre-wrap;font-family:inherit\">"
         + html.escape(s["caption"]) + "</pre>",
         "<p><b>TikTok caption</b></p><pre style=\"white-space:pre-wrap;font-family:inherit\">"
         + html.escape(s.get("tiktok_caption") or s["caption"]) + "</pre>"]
    text = "\n\n".join([f"Your approved home tour is ready to post at {t12}. {song_line}",
                        f"IG / Facebook video: {s['ig_url']}", f"TikTok video: {s['tiktok_url']}",
                        "\n".join(f"{i + 1}. {x}" for i, x in enumerate(steps)),
                        "Instagram / Facebook caption:\n" + s["caption"],
                        "TikTok caption:\n" + (s.get("tiktok_caption") or s["caption"])])
    cal = "\n".join([f"Post the {town} home tour with a trending song. {song_line}",
                     f"IG/FB video: {s['ig_url']}", f"TikTok video: {s['tiktok_url']}",
                     "Captions are in the email \"" + subject + "\"."])
    s["handoff"] = {"time": a.time, "song": song}
    json.dump(s, open(path, "w"), indent=1, ensure_ascii=False); open(path, "a").write("\n")
    print(json.dumps({"subject": subject, "html": "\n".join(h), "text": text, "calendar": cal,
                      "cover": s.get("cover"), "time": a.time}, ensure_ascii=False))


if __name__ == "__main__":
    main()
