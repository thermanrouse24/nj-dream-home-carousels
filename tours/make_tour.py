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
import re
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


PHONE_TEXT = "Call/Text 917.843.5290 Therm The Realtor"   # Therm, Oct 28 2026: his name and number on every post


def find_phone_box(src, dur, scan_s=10.0):
    """Find the edit's own black 'Call/Text <number> <name>' bar near the end (e.g. 'Call/Text 347-988-8291 Vinny').
    Returns (x, y, w, h, t_start, t_end) in 1080x1920 coords, or None."""
    import numpy as np
    tmp = tempfile.mkdtemp()
    start = max(0.0, dur - scan_s)
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", src,
         "-vf", f"fps=10,scale={W}:{H}", os.path.join(tmp, "f_%04d.png")])
    hits = []
    for f in sorted(os.listdir(tmp)):
        a = np.asarray(Image.open(os.path.join(tmp, f)).convert("L")) < 30
        rows = np.where(a.sum(1) > 350)[0]
        if not len(rows):
            continue
        runs = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
        for r in runs:
            if not (80 <= len(r) <= 220) or r[0] < H * 0.45:     # a solid bar 80-220 px tall, lower half
                continue
            band = a[r[0]:r[-1] + 1]
            cols = np.where(band.mean(0) > 0.6)[0]
            if len(cols) < 500 or band[:, cols.min():cols.max() + 1].mean() < 0.75:
                continue
            t = start + (int(f[2:6]) - 1) / 10.0
            hits.append((int(cols.min()), int(r[0]), int(cols.max() - cols.min() + 1), int(len(r)), t))
    if len(hits) < 5:
        return None
    x = min(h[0] for h in hits); y = min(h[1] for h in hits)
    x2 = max(h[0] + h[2] for h in hits); y2 = max(h[1] + h[3] for h in hits)
    return x, y, x2 - x, y2 - y, min(h[4] for h in hits), max(h[4] for h in hits) + 0.1


def phone_patch_png(w, h, out_png):
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    size = int(h * 0.48)
    while size > 20:
        f = font("InstrumentSerif-Regular.ttf", size)
        if d.textlength(PHONE_TEXT, font=f) <= w - 60:
            break
        size -= 2
    bb = d.textbbox((0, 0), PHONE_TEXT, font=f)
    d.text(((w + 8 - (bb[2] - bb[0])) / 2 - bb[0], (h + 8 - (bb[3] - bb[1])) / 2 - bb[1]), PHONE_TEXT,
           font=f, fill=(255, 255, 255, 255))
    img.save(out_png)


def replace_phone_box(src, dur):
    """If the edit shows someone else's Call/Text bar, cover it with Therm's. Returns (path, info)."""
    box = find_phone_box(src, dur)
    if not box:
        return src, None
    x, y, w, h, t0, t1 = box
    tmp = tempfile.mkdtemp()
    png = os.path.join(tmp, "phone.png"); out = os.path.join(tmp, "patched.mp4")
    phone_patch_png(w, h, png)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", png, "-filter_complex",
         f"[0:v]scale={W}:{H},setsar=1[b];[b][1:v]overlay={x - 4}:{y - 4}:enable='between(t,{max(0, t0 - 0.15):.2f},{t1 + 0.2:.2f})'[v]",
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "copy", out])
    return out, {"phone_box": [x, y, w, h], "phone_box_s": [round(t0, 1), round(t1, 1)], "phone_text": PHONE_TEXT}


def mean_volume_db(path):
    """Mean loudness of the source's audio in dB (None if no audio). Under -50 dB counts as silent."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", p.stderr)
    if not m:
        return None
    return -999.0 if m.group(1) == "-inf" else float(m.group(1))


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


def price_block(img, price, facts, top, price_note=None):
    """Under the town/county: the facts line (thin spaced sans), the price in the town's tall serif,
    a thin bronze rule, and NJ DREAM HOME in the county's thin spaced sans."""
    y = top
    if facts:
        img = tracked_text(img, facts.upper(), vfont(COUNTY_FONT, 36, 500), y, 6)
        y += 70
    if price:   # clean sans so the number reads instantly (Therm, Oct 24 2026: the serif price wasn't legible)
        # Playfair Display: an elegant high-contrast serif with clear, open numerals (Therm, Oct 24 2026:
        # "a bit more luxurious" but still easy to read)
        img = tracked_text(img, price, vfont(PRICE_FONT, 118, 700), y - 14, 3, fill=TOWN_COLOR + (255,))
        y += 152
        if price_note:   # says what the number is, e.g. "3.5% DOWN PAYMENT"
            img = tracked_text(img, price_note.upper(), vfont(COUNTY_FONT, 34, 600), y, 8, fill=(225, 183, 133, 255))
            y += 62
        else:
            y += 28
    d = ImageDraw.Draw(img)
    d.line([((W - 300) / 2, y), ((W + 300) / 2, y)], fill=(225, 183, 133, 255), width=3)
    return tracked_text(img, "NJ DREAM HOME", vfont(COUNTY_FONT, 52, 400), y + 26, 18)


PRICE_FONT = "PlayfairDisplay.ttf"
PANEL_COLOR = (16, 34, 24)   # NJ Dream Home forest green


def brand_panel(box):
    """A clean forest-green panel over the (blurred) old cover block, fading softly at top and bottom."""
    x, y, w, h = box
    edge = 60
    a = Image.new("L", (w, h + 2 * edge), 0)
    ImageDraw.Draw(a).rectangle((-10, edge + 20, w + 10, h + edge - 20), fill=232)
    a = a.filter(ImageFilter.GaussianBlur(18)).crop((0, edge, w, h + edge))
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    panel.paste(Image.new("RGBA", (w, h), PANEL_COLOR + (255,)), (x, y), a)
    return panel


def title_overlay(town, county, out_png, box=None, price=None, facts=None, price_note=None, panel_box=None):
    """Transparent 1080x1920 PNG in Therm's reference style: the TOWN huge (tall condensed serif),
    the COUNTY small and widely spaced underneath. A soft shadow keeps it readable on any footage."""
    img = brand_panel(panel_box) if panel_box else Image.new("RGBA", (W, H), (0, 0, 0, 0))
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
        img = price_block(img, price, facts, int(cy + 85), price_note)
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


TEXT_SECONDS = 1.5   # Therm, Oct 24 2026: the 5 lines of text show for 1.5 s at the front of the video only


def build(src, card_jpg, overlay_png, out_mp4, has_audio, dur, box=None, until=TITLE_SECONDS, boxes=None,
          text_until=None):
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
               f"[1:v]format=rgba[ov];[base][ov]overlay=0:0:shortest=1:enable='lt(t,{text_until or until})'[v0];"
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
    ap.add_argument("--facts", default="", help="the edit's facts line, e.g. '5 Beds | 5 Baths'")
    ap.add_argument("--price-note", default="", help="what the price is, e.g. 'down payment'")
    ap.add_argument("--panel", action="store_true", help="solid forest-green panel instead of the blurred band")
    a = ap.parse_args()
    dur, has_audio = probe(a.src)
    if dur <= 1:
        sys.exit("video too short or unreadable")
    os.makedirs(os.path.dirname(os.path.abspath(a.out_prefix)), exist_ok=True)
    a.src, phone_info = replace_phone_box(a.src, dur)
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, "title.png")
    box = None if a.keep_label else LABEL_BOX
    until = label_end(a.src, box) if box else None
    # the blur stays until the edit's own label is gone (so it never peeks through); the new text
    # itself shows only for TEXT_SECONDS
    text_until = TEXT_SECONDS
    if until is None:        # no SINGLE FAMILY / HOME label found: title at the top, nothing blurred
        box, until = None, TITLE_SECONDS
    title_overlay(a.town, a.county, ov, box, a.price.strip() or None, a.facts.strip() or None,
                  a.price_note.strip() or None, BLOCK_BOX if (box and a.panel) else None)
    boxes = [BLOCK_BOX] if box else []
    build(a.src, os.path.join(ROOT, "business_card_story.jpg"), ov, a.out_prefix + "_ig.mp4", has_audio, dur, until=until, boxes=boxes, text_until=text_until)
    build(a.src, os.path.join(ROOT, "business_card_story_tiktok.jpg"), ov, a.out_prefix + "_tiktok.mp4", has_audio, dur, until=until, boxes=boxes, text_until=text_until)
    vol = mean_volume_db(a.src) if has_audio else None
    total = dur + CARD_SECONDS
    times = [0.8, dur * 0.25, dur * 0.5, dur * 0.75, max(dur - 0.5, 0), total - 1.0]
    frames(a.out_prefix + "_ig.mp4", times, a.out_prefix + "_preview.jpg", a.out_prefix + "_cover.jpg")
    info = {"text_until_s": text_until, "blur_until_s": until, "duration_s": round(total, 1), "source_duration_s": round(dur, 1), "source_has_audio": has_audio,
            "source_mean_volume_db": vol, "has_music": bool(has_audio and vol is not None and vol > -50),
            "ig_mb": round(os.path.getsize(a.out_prefix + "_ig.mp4") / 1e6, 1),
            "tiktok_mb": round(os.path.getsize(a.out_prefix + "_tiktok.mp4") / 1e6, 1),
            "phone_replaced": phone_info}
    print(json.dumps(info))


if __name__ == "__main__":
    main()
