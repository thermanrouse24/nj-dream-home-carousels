#!/usr/bin/env python3
"""Instagram Audio API helper: find a licensed song / original sound and attach it to a Reel.

Meta opened part of the Instagram audio library to third-party publishing in May 2026
(Metricool: "Reels with audio" since May 18 2026). Accounts connected through Facebook Login
(our META_PAGE_TOKEN on graph.facebook.com) can:
  1. search:  GET  {GRAPH}/ig_audio?user_id=<IG_USER_ID>&audio_type=music&search_query=<song>
              (no search_query = Meta's trending list for that type)
  2. attach:  POST {GRAPH}/<IG_USER_ID>/media  media_type=REELS ... audio_configuration=
              {"audio_id": "<id>", "audio_volume": <0-100>, "video_volume": <0-100>}
Reels only (not feed photos, carousels or Stories). The third-party catalog is smaller than the
in-app one, so a trending song may be missing: then pick another from the trending list.
The exact request shape is new and thinly documented, so search() tries the known variants and
reports which one worked. Nothing here publishes anything.

CLI (read-only): python3 publisher/ig_audio.py ["song or artist"] [--type music|original_sound]
"""
import argparse, json, os, sys
import requests

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")


def _get(url, token, params):
    r = requests.get(url, params={**params, "access_token": token}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"error": {"message": r.text[:300]}}


def search(token, ig_user_id, query=None, audio_type="music", limit=25):
    """Return (results, variant, errors). results: list of dicts with at least audio_id/title."""
    base = {"audio_type": audio_type, "limit": limit}
    if query:
        base["search_query"] = query
    variants = [
        ("ig_audio?user_id", f"{GRAPH}/ig_audio", {**base, "user_id": ig_user_id}),
        ("<ig>/ig_audio", f"{GRAPH}/{ig_user_id}/ig_audio", base),
        ("<ig>/audio", f"{GRAPH}/{ig_user_id}/audio", base),
    ]
    errors = []
    for name, url, params in variants:
        code, d = _get(url, token, params)
        if code < 400 and "error" not in d:
            if os.environ.get("AUDIO_DEBUG"):
                print(f"[{name}] raw: {json.dumps(d)[:1500]}")
            rows = d.get("data", d if isinstance(d, list) else [])
            if isinstance(rows, dict):          # some responses nest the list one level down
                rows = next((v for v in rows.values() if isinstance(v, list)), [])
            out = []
            for x in rows:
                out.append({
                    "audio_id": str(x.get("audio_id") or x.get("id") or ""),
                    "title": x.get("title") or x.get("name") or "",
                    "artist": x.get("display_artist") or x.get("artist") or x.get("ig_username") or "",
                    "type": x.get("audio_type") or audio_type,
                    "duration_ms": x.get("duration_in_ms") or x.get("duration_ms"),
                })
            return out, name, errors
        errors.append(f"{name}: {code} {d.get('error', {}).get('message', '')[:200]}")
    return [], None, errors


def pick(results, wanted):
    """Best match for 'Title - Artist' (or just a title)."""
    if not results:
        return None
    w = wanted.lower()
    title = w.split(" - ")[0].strip()
    artist = w.split(" - ")[1].strip() if " - " in w else ""
    for r in results:
        if r["title"].lower() == title and (not artist or artist in r["artist"].lower()):
            return r
    for r in results:
        if title in r["title"].lower():
            return r
    return None


def resolve(token, ig_user_id, wanted, backup=None):
    """audio_id for the wanted song, else the backup, else None. Raises nothing."""
    for song in [s for s in (wanted, backup) if s]:
        res, _, _ = search(token, ig_user_id, song.split(" - ")[0])
        hit = pick(res, song)
        if hit and hit["audio_id"]:
            return hit
    return None


def audio_configuration(audio_id, audio_volume=None, video_volume=None):
    cfg = {"audio_id": str(audio_id)}
    if audio_volume is not None:
        cfg["audio_volume"] = int(audio_volume)
    if video_volume is not None:
        cfg["video_volume"] = int(video_volume)
    return json.dumps(cfg)          # Meta's examples form-encode it as a JSON string


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--type", default="music", choices=["music", "original_sound"])
    a = ap.parse_args()
    tok, ig = os.environ.get("META_PAGE_TOKEN", "").strip(), os.environ.get("IG_USER_ID", "").strip()
    if not tok or not ig:
        sys.exit("NOT READY: META_PAGE_TOKEN and IG_USER_ID secrets are needed")
    res, variant, errs = search(tok, ig, a.query, a.type)
    for e in errs:
        print("tried", e)
    if variant is None:
        print("NOT READY: Instagram audio search is not available to this account/token yet.")
        sys.exit(1)
    print(f"READY: audio search works ({variant}). {len(res)} results for "
          f"{a.query or 'TRENDING'} ({a.type}):")
    for r in res:
        print(f"  {r['audio_id']:>20}  {r['title']} - {r['artist']}  ({r['type']})")
