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


# Therm's edit template puts "SINGLE FAMILY / HOME" here (x, y, w, h on the 1080x1920 frame).
# Therm (Oct 24 2026): remove that label and put the TOWN / COUNTY title in its place.
LABEL_BOX = (0, 954, 1080, 346)   # label sits about y 990 to 1260; the extra rows are the soft edges
# Therm (Oct 24 2026): restyle the edit's price and "NJ DREAM HOME" to match the town/county title.
# One band covers the edit's whole cover block (label, facts line, price, NJ DREAM HOME) and all of it
# is redrawn in one style, so nothing from the old fonts peeks through.
BLOCK_BOX = (0, 954, 1080, 790)


def tracked_text(img, text, font_obj, cy, track, fill=(255, 255, 255, 255)):
    """Centered, letter-spaced text with a soft shadow. Returns the composited image."""
    d = ImageDraw.Draw(img)
    widths = [d.textlength(c, font=font_obj) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    while total > W - 120 and track > 4:
        track -= 2
        total = sum(widths) + track * (len(text) - 1)
    cx = (W - total) / 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    xx = cx
    for c, wdt in zip(text, widths):
        sd.text((xx + 2, cy + 3), c, font=font_obj, fill=(0, 0, 0, 150)); xx += wdt + track
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(img)
    xx = cx
    for c, wdt in zip(text, widths):
        d.text((xx, cy), c, font=font_obj, fill=fill); xx += wdt + track
    return img


def price_block(img, price, facts, top):
    """Under the town/county: the facts line (thin spaced sans), the price in the town's tall serif,
    a thin bronze rule, and NJ DREAM HOME in the county's thin spaced sans."""
    y = top
    if facts:
        img = tracked_text(img, facts.upper(), vfont(COUNTY_FONT, 36, 500), y, 6)
        y += 70
    if price:   # clean sans so the number reads instantly (Therm, Oct 24 2026: the serif price wasn't legible)
        img = tracked_text(img, price, vfont(COUNTY_FONT, 112, 600), y - 6, 4, fill=TOWN_COLOR + (255,))
        y += 168
    d = ImageDraw.Draw(img)
    d.line([((W - 300) / 2, y), ((W + 300) / 2, y)], fill=(225, 183, 133, 255), width=3)
    return tracked_text(img, "NJ DREAM HOME", vfont(COUNTY_FONT, 52, 400), y + 26, 18)


def title_overlay(town, county, out_png, box=None, price=None, facts=None):
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
        mask = town_layer(town_txt, W - 100, (box[3] - 95) if box else 330)
    if box and mask.height > box[3] - 70:   # two-line names: shrink to fit the label box
        r = (box[3] - 70) / mask.height
        mask = mask.resize((int(mask.width * r), int(mask.height * r)), Image.LANCZOS)
    if box:
        x, y = (W - mask.width) // 2, box[1] + 20
    else:
        x, y = (W - mask.width) // 2, 130   # top of the frame: Therm's edits put their own text in the lower half
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 175), (x + 4, y + 8), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
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
    if box:
        img = price_block(img, price, facts, int(cy + 85))
    img.save(out_png)


def label_end(src, box, max_s=6.0):
    """Seconds until the edit's own label leaves the box: the box's share of near-black / near-white
    pixels (the label's text and outline) drops below half of what it was at the start."""
    tmp = tempfile.mkdtemp()
    x, y, w, h = box
    run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(max_s), "-i", src, "-vf",
         f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,crop={w}:{h}:{x}:{y},fps=10,scale=255:-2",
         os.path.join(tmp, "c%03d.png")])
    files = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    def score(f):
        im = Image.open(os.path.join(tmp, f)).convert("L")
        hist = im.histogram()
        return (sum(hist[:25]) + sum(hist[236:])) / max(1, sum(hist))
    if not files:
        return TITLE_SECONDS
    base = max(score(f) for f in files[:4])
    if base < 0.08:          # no label in this edit
        return None
    for i, f in enumerate(files):
        if i >= 5 and score(f) < base * 0.5:
            return round(i / 10 + 0.1, 2)
    return min(max_s, TITLE_SECONDS)


def feather_mask(w, h, out_png, edge=45):
    """White box with soft edges, so the blurred patch melts into the footage instead of a hard rectangle."""
    m = Image.new("L", (w, h + 2 * edge), 0)       # full width; only top and bottom fade
    ImageDraw.Draw(m).rectangle((-10, edge + 12, w + 10, h + edge - 12), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(edge / 3)).crop((0, edge, w, h + edge))
    m.save(out_png)


def build(src, card_jpg, overlay_png, out_mp4, has_audio, dur, box=None, until=TITLE_SECONDS, boxes=None):
    """[tour 9:16 (+ label box blurred) + title overlay] then [3 s business card], one file."""
    scale = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
             f"setsar=1,fps=30,format=yuv420p")
    boxes = boxes or ([box] if box else [])
    if boxes:
        scale += f",split={len(boxes) + 1}" + "".join(f"[s{i}]" for i in range(len(boxes) + 1)) + ";"
        prev = "s0"
        for i, (x, y, w, h) in enumerate(boxes):
            mask_png = os.path.join(tempfile.mkdtemp(), "mask.png")
            feather_mask(w, h, mask_png)
            scale += (f"[s{i + 1}]crop={w}:{h}:{x}:{y},boxblur=luma_radius=80:luma_power=3:chroma_radius=40:chroma_power=3,"
                      f"eq=brightness=-0.10,format=rgba[bl{i}];movie={mask_png},format=gray[mk{i}];[bl{i}][mk{i}]alphamerge[blur{i}];"
                      f"[{prev}][blur{i}]overlay={x}:{y}:enable='lt(t,{until})'[o{i}];")
            prev = f"o{i}"
        scale = scale[:-(len(prev) + 3)] + "[base];"
    else:
        scale += "[base];"
    vf_main = (scale +
               f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:shortest=1:enable='lt(t,{until})'[v0];"
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
    ap.add_argument("--keep-label", action="store_true", help="don't replace the edit's SINGLE FAMILY / HOME label")
    ap.add_argument("--price", default="", help="the price shown on the edit's cover, e.g. $37,625 (redrawn in the title style)")
    ap.add_argument("--facts", default="", help="the edit's facts line, e.g. '35 Mins to NYC | 5 Beds | 5 Baths'")
    a = ap.parse_args()
    dur, has_audio = probe(a.src)
    if dur <= 1:
        sys.exit("video too short or unreadable")
    os.makedirs(os.path.dirname(os.path.abspath(a.out_prefix)), exist_ok=True)
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, "title.png")
    box = None if a.keep_label else LABEL_BOX
    until = label_end(a.src, box) if box else None
    if until is None:        # no SINGLE FAMILY / HOME label found: title at the top, nothing blurred
        box, until = None, TITLE_SECONDS
    title_overlay(a.town, a.county, ov, box, a.price.strip() or None, a.facts.strip() or None)
    boxes = [BLOCK_BOX] if box else []
    build(a.src, os.path.join(ROOT, "business_card_story.jpg"), ov, a.out_prefix + "_ig.mp4", has_audio, dur, until=until, boxes=boxes)
    build(a.src, os.path.join(ROOT, "business_card_story_tiktok.jpg"), ov, a.out_prefix + "_tiktok.mp4", has_audio, dur, until=until, boxes=boxes)
    total = dur + CARD_SECONDS
    times = [0.8, dur * 0.25, dur * 0.5, dur * 0.75, max(dur - 0.5, 0), total - 1.0]
    frames(a.out_prefix + "_ig.mp4", times, a.out_prefix + "_preview.jpg", a.out_prefix + "_cover.jpg")
    info = {"title_until_s": until, "duration_s": round(total, 1), "source_duration_s": round(dur, 1), "source_has_audio": has_audio,
            "ig_mb": round(os.path.getsize(a.out_prefix + "_ig.mp4") / 1e6, 1),
            "tiktok_mb": round(os.path.getsize(a.out_prefix + "_tiktok.mp4") / 1e6, 1)}
    print(json.dumps(info))


if __name__ == "__main__":
    main()
