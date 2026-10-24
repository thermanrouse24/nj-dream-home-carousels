#!/usr/bin/env python3
"""Home Tour Reel maker (Therm's rule, Oct 24 2026: one home tour Reel a day, 9:45 AM).

Takes one of Therm's already-edited tour videos and adds only:
  1. the "front of the home" title for the first 2.5 seconds: the TOWN in big letters and the
     COUNTY in small letters (Therm's spec), on a soft dark band so it reads on any footage;
  2. Therm's business card as the last 3 seconds (Instagram/Facebook version says CLICK THE LINK
     IN MY BIO; the TikTok version says DM ME "HOME").
Everything else in his edit is untouched. Output is 1080x1920, H.264 + AAC, 30 fps.

Usage:
  python3 tours/make_tour.py INPUT.mp4 OUT_PREFIX --town "Union" --county "Union"
Makes OUT_PREFIX_ig.mp4, OUT_PREFIX_tiktok.mp4, OUT_PREFIX_cover.jpg, OUT_PREFIX_preview.jpg
"""
import argparse, json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1080, 1920
TITLE_SECONDS = 2.5
CARD_SECONDS = 3.0
CREAM = (245, 236, 215)
BRONZE = (225, 183, 133)


def font(name, size):
    return ImageFont.truetype(os.path.join(ROOT, "fonts", name), size)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ffmpeg failed: " + " ".join(cmd[:6]) + "\n" + p.stderr[-1500:])
    return p.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
               "-of", "json", path])
    d = json.loads(out)
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    dur = float(d.get("format", {}).get("duration", 0) or 0)
    return dur, has_audio


TOWN_FONT = "BodoniModa.ttf"      # tall, high-contrast serif (free Google Font), squeezed to a condensed look
COUNTY_FONT = "Raleway.ttf"       # thin, widely spaced sans (free Google Font)
TOWN_COLOR = (232, 246, 236)      # soft mint white, like Therm's reference reel
SQUEEZE = 0.66                    # horizontal squeeze of the town name


def vfont(name, size, weight, opsz=None):
    f = font(name, size)
    try:
        axes = [a["name"] for a in f.get_variation_axes()]
        vals = []
        for a in axes:
            vals.append(weight if a in (b"Weight", "Weight") else (opsz or 28))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def town_layer(text, max_w, max_h=330):
    """Render the town big, then squeeze it horizontally (tall condensed look). Returns RGBA."""
    size = 420
    while True:
        f = vfont(TOWN_FONT, size, 900, 28)
        tmp = Image.new("L", (10, 10))
        bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if (w * SQUEEZE <= max_w and h <= max_h) or size <= 60:
            break
        size -= 10
    pad = 40
    layer = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(layer).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255)
    layer = layer.resize((int(layer.width * SQUEEZE), layer.height), Image.LANCZOS)
    return layer


def title_overlay(town, county, out_png):
    """Transparent 1080x1920 PNG in Therm's reference style: the TOWN huge (tall condensed serif),
    the COUNTY small and widely spaced underneath. A soft shadow keeps it readable on any footage."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    town_txt = town.upper()
    county_txt = county.upper()
    if "COUNTY" not in county_txt:
        county_txt += " COUNTY"
    words = town_txt.split()
    if len(words) > 1 and len(town_txt) > 9:          # long names stack on two lines, each still big
        half = (len(words) + 1) // 2
        lines = [" ".join(words[:half]), " ".join(words[half:])]
        parts = [town_layer(l, W - 100, 250) for l in lines]
        mw = max(p.width for p in parts)
        mask = Image.new("L", (mw, sum(p.height for p in parts) - 60), 0)
        yy = 0
        for p in parts:
            mask.paste(p, ((mw - p.width) // 2, yy)); yy += p.height - 60
    else:
        mask = town_layer(town_txt, W - 100)
    x, y = (W - mask.width) // 2, 470
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), (x + 4, y + 8), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, sh)
    img.paste(TOWN_COLOR + (255,), (x, y), mask)
    # county: thin, tracked
    f = vfont(COUNTY_FONT, 52, 400)
    d = ImageDraw.Draw(img)
    track = 18
    widths = [d.textlength(c, font=f) for c in county_txt]
    total = sum(widths) + track * (len(county_txt) - 1)
    while total > W - 120 and track > 4:
        track -= 2
        total = sum(widths) + track * (len(county_txt) - 1)
    cx, cy = (W - total) / 2, y + mask.height - 10
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    xx = cx
    for c, wdt in zip(county_txt, widths):
        sd.text((xx + 2, cy + 3), c, font=f, fill=(0, 0, 0, 150)); xx += wdt + track
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(img)
    xx = cx
    for c, wdt in zip(county_txt, widths):
        d.text((xx, cy), c, font=f, fill=(255, 255, 255, 255)); xx += wdt + track
    img.save(out_png)


def build(src, card_jpg, overlay_png, out_mp4, has_audio, dur):
    """[tour scaled/padded to 9:16 + title overlay for 2.5 s] then [3 s business card], one file."""
    vf_main = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
               f"setsar=1,fps=30,format=yuv420p[base];"
               f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:shortest=1:enable='lt(t,{TITLE_SECONDS})'[v0];"
               f"[2:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p,trim=duration={CARD_SECONDS}[v1];")
    if has_audio:
        a0 = "[0:a]aresample=44100,aformat=channel_layouts=stereo[a0];"
    else:
        a0 = f"[3:a]atrim=duration={dur},asetpts=N/SR/TB[a0];"
    a1 = f"[3:a]atrim=duration={CARD_SECONDS},asetpts=N/SR/TB[a1];"
    fc = vf_main + a0 + a1 + "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-loop", "1", "-t", f"{dur:.3f}", "-i", overlay_png,
         "-loop", "1", "-t", str(CARD_SECONDS), "-i", card_jpg,
         "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
         "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(dur + CARD_SECONDS),
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M",
         "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", out_mp4])


def frames(mp4, times, out_jpg, cover_jpg):
    tmp = tempfile.mkdtemp()
    shots = []
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"f{i}.jpg")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", p])
        shots.append(Image.open(p).convert("RGB"))
    shots[0].save(cover_jpg, quality=90)
    tw, th = 270, 480
    sheet = Image.new("RGB", (tw * len(shots) + 10 * (len(shots) + 1), th + 20), (16, 22, 18))
    for i, s in enumerate(shots):
        sheet.paste(s.resize((tw, th)), (10 + i * (tw + 10), 10))
    sheet.save(out_jpg, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out_prefix")
    ap.add_argument("--town", required=True); ap.add_argument("--county", required=True)
    a = ap.parse_args()
    dur, has_audio = probe(a.src)
    if dur <= 1:
        sys.exit("video too short or unreadable")
    os.makedirs(os.path.dirname(os.path.abspath(a.out_prefix)), exist_ok=True)
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, "title.png")
    title_overlay(a.town, a.county, ov)
    build(a.src, os.path.join(ROOT, "business_card_story.jpg"), ov, a.out_prefix + "_ig.mp4", has_audio, dur)
    build(a.src, os.path.join(ROOT, "business_card_story_tiktok.jpg"), ov, a.out_prefix + "_tiktok.mp4", has_audio, dur)
    total = dur + CARD_SECONDS
    times = [0.8, dur * 0.25, dur * 0.5, dur * 0.75, max(dur - 0.5, 0), total - 1.0]
    frames(a.out_prefix + "_ig.mp4", times, a.out_prefix + "_preview.jpg", a.out_prefix + "_cover.jpg")
    info = {"duration_s": round(total, 1), "source_duration_s": round(dur, 1), "source_has_audio": has_audio,
            "ig_mb": round(os.path.getsize(a.out_prefix + "_ig.mp4") / 1e6, 1),
            "tiktok_mb": round(os.path.getsize(a.out_prefix + "_tiktok.mp4") / 1e6, 1)}
    print(json.dumps(info))


if __name__ == "__main__":
    main()
