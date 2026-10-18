#!/usr/bin/env python3
"""NJ Dream Home carousel renderer.

Usage: python3 render_carousel.py spec.json OUT_DIR
Renders 1080x1350 slides in the NJ Dream Home brand template.

Spec format:
{
  "id": "2026-10-18_fact",            # used in file names
  "tag": "REAL ESTATE 101",           # pill text; a word wrapped in *stars* is bolded, e.g. "LOCAL *SPOTS*"
  "source": "optional default source line for every slide",
  "slides": [
    {"type": "cover", "eyebrow": "FOR FIRST-TIME BUYERS",
     "lines": ["WHERE YOU", "CAN", "~AFFORD MORRIS", "~COUNTY"],   # ~ = bronze line
     "sub": "One or two sentences."},
    {"type": "stat", "label": "MEDIAN PRICE", "value": "$592,500", "body": "...", "source": "..."},
    {"type": "point", "num": "1", "title": "Short title", "body": "Body text", "meta": "optional small bronze line", "source": "...",
     "icon": "coffee|utensils|tree|pizza|bakery|market|book|train|calendar|pin",   # local slides
     "photo": "optional path to Therm's OWN photo of the place (never a downloaded photo)"},
    {"type": "text", "title": "Heading", "body": "Paragraph", "source": "..."},
    {"type": "list", "title": "Heading", "items": ["a", "b", "c"]},
    {"type": "cta", "title": ["WANT MY FREE", "~FIRST-TIME BUYER", "~GUIDE?"],
     "steps": ["Tap the link in my bio", "Fill out the quick form", "My team responds within 24 hours"]}
  ]
}
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
CREAM = (245, 236, 215)
BRONZE = (225, 183, 133)
MUTED = (170, 178, 168)
DARK = (22, 30, 24)
M = 80  # side margin

def F(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)

HEAD = lambda s: F("Montserrat-ExtraBold.ttf", s)
BOLD = lambda s: F("Montserrat-Bold.ttf", s)
SEMI = lambda s: F("Montserrat-SemiBold.ttf", s)
BODY = lambda s: F("Inter-Regular.otf", s)
BODYM = lambda s: F("Inter-Medium.otf", s)

def tracked(draw, xy, text, font, fill, track=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track
    return x

def tracked_len(draw, text, font, track):
    return sum(draw.textlength(c, font=font) + track for c in text) - (track if text else 0)

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines

def para(draw, x, y, text, font, fill, maxw, lh):
    for ln in wrap(draw, text, font, maxw):
        draw.text((x, y), ln, font=font, fill=fill); y += lh
    return y

def base():
    return Image.open(os.path.join(HERE, "background.png")).convert("RGB").copy()

def header(img, d, tag):
    # pill, top-left
    parts = tag.split("*")
    f_reg, f_b = SEMI(28), HEAD(28)
    tr = 3.2
    widths = [tracked_len(d, p, f_b if i % 2 else f_reg, tr) for i, p in enumerate(parts)]
    pw = int(sum(widths) + 26 * 2 + 4 * (len([p for p in parts if p]) - 1))
    d.rounded_rectangle((M, 80, M + pw, 136), radius=6, fill=BRONZE)
    x = M + 26
    for i, p in enumerate(parts):
        if not p: continue
        x = tracked(d, (x, 91), p, f_b if i % 2 else f_reg, DARK, tr) + 4
    # mini logo, top-right
    cx = W - 133
    d.line([(cx - 38, 102), (cx, 82), (cx + 38, 102)], fill=BRONZE, width=4, joint="curve")
    f = HEAD(26)
    for i, word in enumerate(["NJ", "DREAM", "HOME"]):
        tw = d.textlength(word, font=f)
        d.text((cx - tw / 2, 106 + i * 23), word, font=f, fill=CREAM)

def footer(d, page, total, source=None, swipe=False):
    f = BODY(24)
    y = 1260
    if source:
        lines = wrap(d, "Source: " + source, BODY(22), 760)[:3]
        y = 1260 - 28 * len(lines) + 10
    x = tracked(d, (M, y - 30 if source else y), "Therm The Realtor", f, MUTED)
    d.line([(x + 14, (y - 30 if source else y) + 4), (x + 14, (y - 30 if source else y) + 26)], fill=MUTED, width=2)
    d.text((x + 30, y - 30 if source else y), "eXp Realty", font=f, fill=MUTED)
    if source:
        yy = y
        for ln in lines:
            d.text((M, yy), ln, font=BODY(22), fill=MUTED); yy += 28
    if swipe:
        fs = BOLD(26)
        tracked(d, (W - M - 150, 1262), "Swipe", fs, CREAM, 2)
        d.line([(W - M - 50, 1279), (W - M, 1279)], fill=CREAM, width=3)
        d.line([(W - M - 14, 1268), (W - M, 1279), (W - M - 14, 1290)], fill=CREAM, width=3)
    else:
        t = f"{page}/{total}"
        fs = BOLD(26)
        d.text((W - M - d.textlength(t, font=fs), 1262), t, font=fs, fill=CREAM)

def headline_block(d, lines, y, max_size=118, maxw=W - 2 * M, gap=0.98):
    # pick the largest size that fits every line
    size = max_size
    clean = [l.lstrip("~") for l in lines]
    while size > 54 and max(d.textlength(c, font=HEAD(size)) for c in clean) > maxw:
        size -= 2
    f = HEAD(size)
    for raw in lines:
        col = BRONZE if raw.startswith("~") else CREAM
        d.text((M - 4, y), raw.lstrip("~"), font=f, fill=col)
        y += int(size * gap)
    return y

def eyebrow(d, y, text):
    tracked(d, (M, y), text.upper(), BOLD(30), BRONZE, 4)

def s_cover(img, d, s, i, n, src):
    lines = s["lines"]
    # vertical layout centered in the open area
    y = 290 if len(lines) <= 4 else 250
    if s.get("eyebrow"):
        eyebrow(d, y, s["eyebrow"]); y += 70
    y = headline_block(d, lines, y)
    if s.get("sub"):
        y = para(d, M, y + 70, s["sub"], BODY(42), CREAM, W - 2 * M, 56)
    if s.get("chips"):
        # preview of what's inside, e.g. the three place names
        y += 40; x = M
        for k, c in enumerate(s["chips"]):
            label = f"{k + 1:02d}  {c}"
            w_ = tracked_len(d, label.upper(), BOLD(26), 2.5) + 44
            if x + w_ > W - M: x = M; y += 68
            x = _chip(d, x, y, label, filled=False)
    footer(d, i, n, None, swipe=True)

def s_stat(img, d, s, i, n, src):
    y = 450
    eyebrow(d, y, s["label"])
    val = s["value"].upper()
    size = 190
    while size > 80 and d.textlength(val, font=HEAD(size)) > W - 2 * M: size -= 4
    d.text((M - 6, y + 50), val, font=HEAD(size), fill=CREAM)
    y2 = d.textbbox((M - 6, y + 50), val, font=HEAD(size))[3] + 40
    d.line([(M, y2), (M + 120, y2)], fill=BRONZE, width=4)
    para(d, M, y2 + 36, s.get("body", ""), BODY(42), CREAM, W - 2 * M, 56)
    footer(d, i, n, s.get("source", src))

# ---------- line icons for local slides (drawn, no outside images) ----------
def _icon(name, size=150, color=BRONZE):
    S = 512; st = 26
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    c = color + (255,)
    if name == "coffee":
        g.rounded_rectangle((110, 210, 350, 430), radius=40, outline=c, width=st)
        g.arc((300, 250, 430, 380), -90, 90, fill=c, width=st)
        for x in (170, 230, 290):
            g.arc((x - 30, 70, x + 30, 130), 90, 270, fill=c, width=st - 6)
            g.arc((x - 30, 125, x + 30, 185), -90, 90, fill=c, width=st - 6)
        g.line((80, 460, 380, 460), fill=c, width=st)
    elif name == "utensils":
        g.line((180, 70, 180, 450), fill=c, width=st)
        for x in (130, 180, 230): g.line((x, 70, x, 190), fill=c, width=st - 8)
        g.arc((130, 140, 230, 240), 0, 180, fill=c, width=st - 8)
        g.line((340, 250, 340, 450), fill=c, width=st)
        g.chord((300, 60, 400, 300), 90, 270, outline=c, width=st)
    elif name == "tree":
        g.ellipse((120, 50, 390, 320), outline=c, width=st)
        g.line((255, 250, 255, 460), fill=c, width=st)
        g.line((255, 340, 330, 270), fill=c, width=st - 6)
        g.line((140, 460, 370, 460), fill=c, width=st)
    elif name == "pizza":
        g.polygon([(256, 470), (80, 110), (432, 110)], outline=c, width=st)
        g.arc((60, 40, 452, 200), 180, 360, fill=c, width=st)
        for (x, y) in ((220, 190), (300, 230), (250, 320)): g.ellipse((x - 26, y - 26, x + 26, y + 26), outline=c, width=st - 10)
    elif name == "bakery":
        g.rounded_rectangle((70, 230, 442, 420), radius=50, outline=c, width=st)
        g.arc((70, 120, 442, 340), 180, 360, fill=c, width=st)
        for x in (170, 256, 342): g.line((x - 30, 200, x + 20, 260), fill=c, width=st - 8)
    elif name == "market":
        g.polygon([(70, 220), (442, 220), (390, 450), (122, 450)], outline=c, width=st)
        g.arc((150, 70, 362, 330), 180, 360, fill=c, width=st)
        for x in (190, 256, 322): g.line((x, 270, x, 400), fill=c, width=st - 10)
    elif name == "book":
        g.polygon([(256, 140), (60, 100), (60, 400), (256, 440)], outline=c, width=st)
        g.polygon([(256, 140), (452, 100), (452, 400), (256, 440)], outline=c, width=st)
    elif name == "train":
        g.rounded_rectangle((120, 60, 392, 390), radius=50, outline=c, width=st)
        g.rectangle((160, 120, 352, 230), outline=c, width=st - 8)
        for x in (190, 322): g.ellipse((x - 26, 300, x + 26, 352), outline=c, width=st - 10)
        g.line((170, 390, 110, 470), fill=c, width=st); g.line((342, 390, 402, 470), fill=c, width=st)
    elif name == "calendar":
        g.rounded_rectangle((70, 110, 442, 450), radius=30, outline=c, width=st)
        g.line((70, 200, 442, 200), fill=c, width=st)
        for x in (170, 342): g.line((x, 60, x, 150), fill=c, width=st)
        for yy in (270, 360):
            for x in (150, 256, 362): g.ellipse((x - 16, yy - 16, x + 16, yy + 16), fill=c)
    else:  # "pin" default
        g.ellipse((136, 50, 376, 290), outline=c, width=st)
        g.polygon([(150, 230), (362, 230), (256, 460)], outline=c, width=st)
        g.ellipse((216, 130, 296, 210), outline=c, width=st - 6)
    return im.resize((size, size), Image.LANCZOS)

ICONS = {"coffee", "utensils", "tree", "pizza", "bakery", "market", "book", "train", "calendar", "pin"}

def _photo_block(img, path, x, y, w, h):
    ph = Image.open(path).convert("RGB")
    r = max(w / ph.width, h / ph.height)
    ph = ph.resize((int(ph.width * r) + 1, int(ph.height * r) + 1), Image.LANCZOS)
    left, top = (ph.width - w) // 2, (ph.height - h) // 2
    ph = ph.crop((left, top, left + w, top + h))
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), 24, fill=255)
    img.paste(ph, (x, y), mask)

def s_point(img, d, s, i, n, src):
    y = 330
    photo = s.get("photo")
    if photo:
        # Only Therm's own photos of the place (see PLAYBOOK). Credit line optional via "photo_credit".
        _photo_block(img, photo, M, y, W - 2 * M, 430)
        y += 430 + 40
    # number badge
    r = 52
    d.ellipse((M, y, M + 2 * r, y + 2 * r), fill=BRONZE)
    num = str(s.get("num", i - 1)); fn = HEAD(54)
    d.text((M + r - d.textlength(num, font=fn) / 2, y + r - 36), num, font=fn, fill=DARK)
    if s.get("icon") and not photo:
        ic = _icon(s["icon"] if s["icon"] in ICONS else "pin", 180)
        img.paste(ic, (W - M - 180, y - 40), ic)
    y += 2 * r + 50
    y = headline_block(d, [l for l in wrap(d, s["title"].upper(), HEAD(78), W - 2 * M)], y, max_size=78 if not photo else 64, gap=1.08)
    if s.get("meta"):
        y += 14; tracked(d, (M, y), s["meta"].upper(), BOLD(28), BRONZE, 3); y += 50
    else:
        y += 20
    d.line([(M, y), (M + 120, y)], fill=BRONZE, width=4)
    para(d, M, y + 36, s.get("body", ""), BODY(40 if not photo else 36), CREAM, W - 2 * M, 54 if not photo else 48)
    footer(d, i, n, s.get("source", src))

def s_text(img, d, s, i, n, src):
    y = 330
    if s.get("eyebrow"): eyebrow(d, y, s["eyebrow"]); y += 70
    y = headline_block(d, wrap(d, s["title"].upper(), HEAD(80), W - 2 * M), y, max_size=80, gap=1.08)
    d.line([(M, y + 24), (M + 120, y + 24)], fill=BRONZE, width=4)
    para(d, M, y + 60, s.get("body", ""), BODY(40), CREAM, W - 2 * M, 54)
    footer(d, i, n, s.get("source", src))

def s_list(img, d, s, i, n, src):
    y = 300
    if s.get("eyebrow"): eyebrow(d, y, s["eyebrow"]); y += 70
    y = headline_block(d, wrap(d, s["title"].upper(), HEAD(72), W - 2 * M), y, max_size=72, gap=1.08) + 40
    for k, it in enumerate(s["items"], 1):
        r = 30
        d.ellipse((M, y, M + 2 * r, y + 2 * r), fill=BRONZE)
        fn = HEAD(32); t = str(k)
        d.text((M + r - d.textlength(t, font=fn) / 2, y + 9), t, font=fn, fill=DARK)
        ly = y + 8
        for ln in wrap(d, it, BODYM(38), W - 2 * M - 100):
            d.text((M + 2 * r + 30, ly), ln, font=BODYM(38), fill=CREAM); ly += 50
        y = max(y + 2 * r, ly) + 34
    footer(d, i, n, s.get("source", src))

def s_cta(img, d, s, i, n, src):
    logo = Image.open(os.path.join(HERE, "logo_photo.png")).convert("RGBA")
    lw = 616; lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh))
    mask = Image.new("L", (lw, lh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, lw, lh), 18, fill=255)
    lx, ly = (W - lw) // 2, 80
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((lx + 6, ly + 14, lx + lw + 6, ly + lh + 14), 18, fill=(0, 0, 0, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    img.paste(Image.open(os.path.join(HERE, "background.png")).convert("RGB"), (0, 0))
    img.paste(sh, (0, 0), sh)
    img.paste(logo, (lx, ly), mask)
    d = ImageDraw.Draw(img)
    y = headline_block(d, s["title"], ly + lh + 70, max_size=62, gap=1.12) + 40
    # The only call to action Therm uses. Fixed text on purpose; specs cannot change it.
    cta = "CLICK THE LINK IN MY BIO"
    fb = HEAD(40)
    tw = tracked_len(d, cta, fb, 2)
    bw, bh = int(tw + 2 * 44), 96
    d.rounded_rectangle((M, y, M + bw, y + bh), radius=48, fill=BRONZE)
    tracked(d, (M + 44, y + 26), cta, fb, DARK, 2)
    footer(d, i, n, None)
    return img

# ---------- local "place card" and "route" slides ----------
GLOW = (225, 183, 133)

def _chip(d, x, y, text, filled=False):
    f = BOLD(26); tw = tracked_len(d, text.upper(), f, 2.5)
    w, h = int(tw + 44), 54
    if filled:
        d.rounded_rectangle((x, y, x + w, y + h), radius=27, fill=BRONZE)
        tracked(d, (x + 22, y + 13), text.upper(), f, DARK, 2.5)
    else:
        d.rounded_rectangle((x, y, x + w, y + h), radius=27, outline=BRONZE, width=3)
        tracked(d, (x + 22, y + 13), text.upper(), f, BRONZE, 2.5)
    return x + w + 14

def _pin_glyph(d, x, y, s, col):
    d.ellipse((x, y, x + s, y + s), fill=col)
    d.polygon([(x + s * 0.12, y + s * 0.62), (x + s * 0.88, y + s * 0.62), (x + s / 2, y + s * 1.35)], fill=col)
    d.ellipse((x + s * 0.32, y + s * 0.32, x + s * 0.68, y + s * 0.68), fill=DARK)

def s_place(img, d, s, i, n, src):
    """Place card: illustrated scene (or Therm's own photo) on top, then name, address, fact chips, body."""
    import scenes
    num = str(s.get("num", i - 1))
    x0, y0, iw, ih = M, 205, W - 2 * M, 440
    photo = s.get("photo")
    if photo:
        _photo_block(img, photo, x0, y0, iw, ih)
    else:
        tmp = f"/tmp/_scene_{os.getpid()}_{i}.png"
        scenes.render_scene(s.get("scene", "default"), int(s.get("variant", i)), tmp, w=iw, h=ih)
        _photo_block(img, tmp, x0, y0, iw, ih)
    d = ImageDraw.Draw(img)
    # tag: ILLUSTRATION (drawn scenes) or photo credit
    tag = "ILLUSTRATION" if not photo else ("PHOTO: " + s.get("photo_credit", "THERM THE REALTOR")).upper()
    f = BOLD(20); tw = tracked_len(d, tag, f, 2)
    d.rounded_rectangle((x0 + iw - tw - 40, y0 + 18, x0 + iw - 16, y0 + 52), radius=8, fill=(22, 32, 26))
    tracked(d, (x0 + iw - tw - 28, y0 + 24), tag, f, MUTED, 2)
    # number badge overlapping the image
    r = 50; by = y0 + ih - r
    d.ellipse((x0 + 28, by, x0 + 28 + 2 * r, by + 2 * r), fill=BRONZE, outline=(16, 28, 21), width=6)
    fn = HEAD(52)
    d.text((x0 + 28 + r - d.textlength(num, font=fn) / 2, by + r - 35), num, font=fn, fill=DARK)
    kind = s.get("kind", "").upper()
    if kind:
        kw = tracked_len(d, kind, BOLD(26), 4)
        tracked(d, (W - M - kw, y0 + ih + 26), kind, BOLD(26), BRONZE, 4)
    y = y0 + ih + 74
    tsz = 74
    lines = wrap(d, s["title"].upper(), HEAD(tsz), W - 2 * M)
    while tsz > 52 and (len(lines) > 2 or (len(lines) > 1 and len(lines[-1]) < 7)):
        tsz -= 4; lines = wrap(d, s["title"].upper(), HEAD(tsz), W - 2 * M)
    y = headline_block(d, lines, y, max_size=tsz, gap=1.04) + 12
    if s.get("meta"):
        _pin_glyph(d, M, y + 4, 30, BRONZE)
        tracked(d, (M + 46, y), s["meta"].upper(), BOLD(32), CREAM, 2.5)
        y += 62
    x = M
    for k, c in enumerate(s.get("chips", [])[:3]):
        f2 = BOLD(26); w_ = tracked_len(d, c.upper(), f2, 2.5) + 44
        if x + w_ > W - M: x = M; y += 66
        x = _chip(d, x, y, c, filled=(k == 0))
    if s.get("chips"): y += 76
    if s.get("body"):
        para(d, M, y, s["body"], BODY(34), CREAM, W - 2 * M, 46)
    footer(d, i, n, s.get("source", src))
    return img

def s_route(img, d, s, i, n, src):
    """The stops on one card: numbered nodes on a dotted route line."""
    y = 250
    if s.get("eyebrow"): eyebrow(d, y, s["eyebrow"]); y += 66
    y = headline_block(d, wrap(d, s["title"].upper(), HEAD(76), W - 2 * M), y, max_size=76, gap=1.06) + 50
    stops = s["stops"]; step = 150
    x0 = M + 38
    # dotted line
    yy = y + 38
    while yy < y + 38 + step * (len(stops) - 1):
        d.ellipse((x0 - 4, yy - 4, x0 + 4, yy + 4), fill=BRONZE); yy += 22
    for k, st in enumerate(stops):
        cy = y + k * step
        d.ellipse((x0 - 38, cy, x0 + 38, cy + 76), fill=BRONZE)
        t = str(k + 1); fn = HEAD(40)
        d.text((x0 - d.textlength(t, font=fn) / 2, cy + 13), t, font=fn, fill=DARK)
        d.text((x0 + 70, cy + 2), st["name"].upper(), font=HEAD(44), fill=CREAM)
        tracked(d, (x0 + 72, cy + 56), st["where"].upper(), BOLD(26), BRONZE, 2.5)
    y = y + step * len(stops) + 10
    if s.get("tip"):
        d.rounded_rectangle((M, y, W - M, y + 170), radius=18, fill=(15, 30, 22))
        d.rounded_rectangle((M, y, W - M, y + 170), radius=18, outline=(70, 90, 70), width=2)
        tracked(d, (M + 32, y + 26), "BUYER TIP", BOLD(26), BRONZE, 4)
        para(d, M + 32, y + 66, s["tip"], BODY(34), CREAM, W - 2 * M - 64, 46)
    footer(d, i, n, s.get("source", src))

RENDER = {"cover": s_cover, "stat": s_stat, "point": s_point, "text": s_text, "list": s_list, "cta": s_cta, "place": s_place, "route": s_route}

def render(spec, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    n = len(spec["slides"]); paths = []
    for i, s in enumerate(spec["slides"], 1):
        img = base(); d = ImageDraw.Draw(img)
        t = s["type"]
        if t != "cta":
            header(img, d, spec.get("tag", "NJ DREAM HOME"))
        if t in ("stat", "point", "text", "list"):
            # draw body content on a layer, then center it vertically in the open area
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            RENDER[t](layer, ld, s, i, n, spec.get("source"))
            content = layer.crop((0, 0, W, 1150))
            bb = content.getbbox()
            if bb:
                top, bot = bb[1], bb[3]
                target = 190 + (1130 - 190 - (bot - top)) // 2
                img.paste(content, (0, target - top), content)
            foot = layer.crop((0, 1150, W, H)); img.paste(foot, (0, 1150), foot)
        else:
            res = RENDER[t](img, d, s, i, n, spec.get("source"))
            img = res or img
        p = os.path.join(out_dir, f"{spec['id']}_{i}of{n}.jpg")
        img.save(p, "JPEG", quality=92, optimize=True); paths.append(p)
    return paths

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for p in render(spec, sys.argv[2]): print(p)
