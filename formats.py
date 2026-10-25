#!/usr/bin/env python3
"""Three carousel JOBS, three looks (Therm's rule, Oct 25 2026; learned from the Brian Mark
"carousels" short in videos/2026-10-25_brianmark_carousels.mp4, structure only).

  "style": "story"  CONNECTION. Full-bleed photo of Therm, one subtitle line per slide, like a
                    paused video. Story-bank facts only. Builds trust ("this guy has been there").
  "style": "bold"   WARM-UP / VALUE. Photo cover with a huge condensed headline (white + yellow
                    highlight line) and "Swipe to learn how ->". Inside: one step per slide with an
                    orange step label, and when it helps a REAL screenshot of the official page on a
                    white card with a red hand-drawn circle on the exact thing to click.
  "style": "proof"  BUY. White testimonial-style card and a big-number slide, with a results
                    disclaimer. Only Therm's verified story bank wins (no invented clients, no client
                    photos, no names).

render_carousel.py calls render(spec, slides, out_dir, card_fn) for these styles. The business card
is still always the last slide.

Slide types:
  story style:  {"type": "cover"|"story", "text": "Subtitle sentence.", "eyebrow": "optional small caps",
                 "photo": "therm_waterfront.jpg" (quote_photos/ name or repo path), "focus": [x, y],
                 "zoom": 1.0 to 1.6, "source": "..."}
  bold style:   cover: {"type": "cover", "lines": ["WHITE LINE", "~YELLOW LINE"], "badge": "optional pill",
                        "photo", "focus", "zoom", "sub": "optional one line"}
                step:  {"type": "step", "label": "STEP 1:", "title": "Look up the address",
                        "shot": "shots/<file>.png" (made by tools/shoot.py), "circle": [x, y, w, h] fractions of
                        the shot, "body": "One short line.", "source": "..."}
                stat/point/text/list slides render in the brand look.
  proof style:  card:  {"type": "proof_card", "kicker": "ONE OF MY BUYERS...", "lead": "small line",
                        "scene": "keys|savings|home|documents" (illustration, never a client photo),
                        "punch": "Big closing line.", "source": "..."}
                big:   {"type": "proof_big", "lines": ["$1,800 back", "at closing."], "body": "...",
                        "disclaimer": "Results vary..." (default added), "photo": optional Therm photo}
"""
import io, json, math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
M = 80
YELLOW = (255, 212, 59)
ORANGE = (255, 138, 31)
RED = (226, 38, 38)
WHITE = (255, 255, 255)
INK = (18, 18, 18)


def F(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)

ANTON = lambda s: F("Anton-Regular.ttf", s)
SEMI = lambda s: F("Inter-SemiBold.otf", s)
BODY = lambda s: F("Inter-Regular.otf", s)
MED = lambda s: F("Inter-Medium.otf", s)
MBOLD = lambda s: F("Montserrat-ExtraBold.ttf", s)


# ---------- helpers ----------
def photo_path(p):
    if not p:
        return os.path.join(HERE, "quote_photos", "therm_waterfront.jpg")
    for c in (p, os.path.join(HERE, p), os.path.join(HERE, "quote_photos", p)):
        if os.path.exists(c):
            return c
    raise SystemExit(f"photo not found: {p} (use Therm's own photos only, see quote_photos/photos.json)")


def default_focus(p):
    try:
        meta = json.load(open(os.path.join(HERE, "quote_photos", "photos.json")))
        for ph in meta["photos"]:
            if os.path.basename(p) == ph["file"]:
                return ph["focus"]
    except Exception:
        pass
    return [0.5, 0.3]


def cover_fit(path, focus=None, zoom=1.0, w=W, h=H):
    im = Image.open(path).convert("RGB")
    fx, fy = focus or default_focus(path)
    sc = max(w / im.width, h / im.height) * zoom
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x = int(min(max(fx * im.width - w / 2, 0), im.width - w))
    y = int(min(max(fy * im.height - h * 0.32, 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def shade(img, top=0.35, bottom=0.88, overall=0.0, start=0.35):
    """Darken: a top band (for the header), a bottom gradient (for text) and an optional overall dim."""
    g = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        a = overall
        if t < 0.18:
            a = max(a, top * (1 - t / 0.18))
        if t > start:
            a = max(a, bottom * min(1, (t - start) / (1 - start)) ** 1.2)
        g.putpixel((0, y), int(255 * min(a, 0.95)))
    mask = g.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, mask)


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def shadow_text(img, xy, text, font, fill, blur=6, off=(0, 3), alpha=200, anchor="la"):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0] + off[0], xy[1] + off[1]), text, font=font, fill=(0, 0, 0, alpha), anchor=anchor)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.paste(lay, (0, 0), lay)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor=anchor)


def fit_font(d, lines, maker, maxw, start, minimum=40):
    size = start
    while size > minimum and max(d.textlength(l, font=maker(size)) for l in lines) > maxw:
        size -= 2
    return maker(size)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), m)
    return out


def drop_shadow(img, box, r=28, blur=24, alpha=150):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(lay).rounded_rectangle((x0, y0 + 10, x1, y1 + 10), radius=r, fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.paste(lay, (0, 0), lay)


def hand_ellipse(d, box, color=RED, width=7, seed=3):
    """A marker-style circle: two slightly different loops, like a hand-drawn annotation."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    for k in range(2):
        pts = []
        a0 = rnd.uniform(-0.6, -0.2)
        for i in range(0, 76):
            a = a0 + i / 70 * 2 * math.pi
            j = 1 + 0.03 * math.sin(a * 3 + k) + rnd.uniform(-0.01, 0.01)
            pts.append((cx + rx * j * math.cos(a) + k * 3, cy + ry * j * math.sin(a) - k * 2))
        d.line(pts, fill=color, width=width - 2 * k, joint="curve")


def curved_arrow(d, start, end, color=WHITE, width=5):
    (x0, y0), (x1, y1) = start, end
    cx, cy = (x0 + x1) / 2 + (y1 - y0) * 0.35, (y0 + y1) / 2 - (x1 - x0) * 0.15
    pts = []
    for i in range(31):
        t = i / 30
        pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    d.line(pts, fill=color, width=width, joint="curve")
    ang = math.atan2(y1 - pts[-3][1], x1 - pts[-3][0])
    for s in (2.5, -2.5):
        d.line([(x1, y1), (x1 - 26 * math.cos(ang + s / 6), y1 - 26 * math.sin(ang + s / 6))], fill=color, width=width)


def scene_png(kind, w, h, variant=0):
    import cairosvg, home_scenes
    svg = home_scenes.home_svg(kind, variant, w, h)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h))).convert("RGBA")


# ---------- brand pieces reused from render_carousel ----------
def _rc():
    import render_carousel as rc
    rc.set_style("brand")
    return rc


def chrome(img, spec, s, i, n, swipe=False):
    rc = _rc()
    d = ImageDraw.Draw(img)
    rc.header(img, d, spec.get("tag", "NJ DREAM HOME"))
    rc.footer(d, i, n, s.get("source", spec.get("source")) if i > 1 else None, swipe=swipe)


def brand_slide(spec, s, i, n):
    """stat / point / text / list inside a bold or proof carousel: render in the brand look."""
    rc = _rc()
    img = rc.base(); d = ImageDraw.Draw(img)
    rc.header(img, d, spec.get("tag", "NJ DREAM HOME"))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    rc.RENDER[s["type"]](layer, ld, s, i, n, spec.get("source"))
    content = layer.crop((0, 0, W, 1150)); bb = content.getbbox()
    if bb:
        target = 190 + (1130 - 190 - (bb[3] - bb[1])) // 2
        img.paste(content, (0, target - bb[1]), content)
    foot = layer.crop((0, 1150, W, H)); img.paste(foot, (0, 1150), foot)
    return img


# ---------- STORY (connection) ----------
def story_slide(spec, s, i, n):
    img = cover_fit(photo_path(s.get("photo")), s.get("focus"), s.get("zoom", 1.0))
    img = shade(img, top=0.45, bottom=0.9, start=0.42)
    d = ImageDraw.Draw(img)
    y = 1150
    font = SEMI(62 if i == 1 else 56)
    lines = wrap(d, s["text"], font, W - 2 * M - 20)[:4]
    lh = int(font.size * 1.2)
    y = 1120 - lh * len(lines)
    if s.get("eyebrow"):
        f = MBOLD(28)
        t = s["eyebrow"].upper()
        shadow_text(img, (W // 2, y - 64), t, f, YELLOW, anchor="ma")
    for ln in lines:
        shadow_text(img, (W // 2, y), ln, font, WHITE, anchor="ma")
        y += lh
    chrome(img, spec, s, i, n, swipe=(i == 1))
    return img


# ---------- BOLD (value / how-to) ----------
def bold_cover(spec, s, i, n):
    img = cover_fit(photo_path(s.get("photo")), s.get("focus"), s.get("zoom", 1.1))
    img = shade(img, top=0.5, bottom=0.92, overall=0.25, start=0.3)
    d = ImageDraw.Draw(img)
    raw = s["lines"]; lines = [l.lstrip("~") for l in raw]
    font = fit_font(d, lines, ANTON, W - 2 * M, 150)
    lh = int(font.size * 1.06)
    y = 1130 - lh * len(lines) - (110 if s.get("sub") else 0)
    if s.get("badge"):
        fb = MBOLD(30); t = s["badge"].upper()
        bw = d.textlength(t, font=fb) + 52
        d.rounded_rectangle(((W - bw) / 2, y - 92, (W + bw) / 2, y - 34), radius=29, fill=RED)
        d.text((W / 2, y - 63), t, font=fb, fill=WHITE, anchor="mm")
    for r, ln in zip(raw, lines):
        shadow_text(img, (W // 2, y), ln.upper(), font, YELLOW if r.startswith("~") else WHITE, blur=8, anchor="ma")
        y += lh
    if s.get("sub"):
        f = MED(36); y += 34
        for ln in wrap(d, s["sub"], f, W - 2 * M)[:2]:
            shadow_text(img, (W // 2, y), ln, f, WHITE, anchor="ma"); y += 48
    # swipe cue, centered like the format it came from
    d = ImageDraw.Draw(img)
    f = MED(34); t = "Swipe to learn how"
    tw = d.textlength(t, font=f); x = (W - tw - 80) / 2
    d.text((x, 1196), t, font=f, fill=WHITE)
    ax = x + tw + 22
    d.line([(ax, 1218), (ax + 58, 1218)], fill=WHITE, width=3)
    d.line([(ax + 44, 1206), (ax + 58, 1218), (ax + 44, 1230)], fill=WHITE, width=3)
    rc = _rc(); rc.header(img, ImageDraw.Draw(img), spec.get("tag", "NJ DREAM HOME"))
    # brokerage line, bottom-left (NJREC: on every slide)
    ImageDraw.Draw(img).text((M, 1290), "Therm The Realtor  |  eXp Realty", font=BODY(22), fill=(210, 210, 210))
    return img


def bold_step(spec, s, i, n):
    rc = _rc()
    img = Image.new("RGB", (W, H), (16, 18, 17))
    # soft vignette from the brand background so it still feels like NJ Dream Home
    bg = rc.base().filter(ImageFilter.GaussianBlur(2))
    img = Image.blend(img, bg, 0.55)
    rc.header(img, ImageDraw.Draw(img), spec.get("tag", "NJ DREAM HOME"))
    final = img
    if not s.get("shot"):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 210
    if s.get("label"):
        f = ANTON(64); d.text((M, y), s["label"].upper(), font=f, fill=ORANGE); y += 86
    tf = ANTON(84)
    tl = wrap(d, s["title"].upper(), tf, W - 2 * M)
    if len(tl) > 2:
        tf = ANTON(70); tl = wrap(d, s["title"].upper(), tf, W - 2 * M)
    title_bottom = y
    for ln in tl:
        d.text((M, y), ln, font=tf, fill=WHITE); y += int(tf.size * 1.08)
    title_bottom = y
    y += 40
    if s.get("shot"):
        shot = Image.open(photo_path(s["shot"]) if not os.path.exists(os.path.join(HERE, s["shot"])) else os.path.join(HERE, s["shot"])).convert("RGB")
        maxw, maxh = W - 2 * M, 1150 - y - (120 if s.get("body") else 40)
        sc = min(maxw / shot.width, maxh / shot.height)
        sw, sh = int(shot.width * sc), int(shot.height * sc)
        shot = shot.resize((sw, sh), Image.LANCZOS)
        pad = 18
        cx0 = (W - sw) // 2 - pad; cy0 = y
        box = (cx0, cy0, cx0 + sw + 2 * pad, cy0 + sh + 2 * pad)
        drop_shadow(img, box)
        card = Image.new("RGB", (sw + 2 * pad, sh + 2 * pad), WHITE)
        card.paste(shot, (pad, pad))
        card = rounded(card, 26)
        img.paste(card, (box[0], box[1]), card)
        d = ImageDraw.Draw(img)
        if s.get("circle"):
            cx, cy, cw, ch = s["circle"]
            ex0 = box[0] + pad + cx * sw - 14; ey0 = box[1] + pad + cy * sh - 12
            ex1 = ex0 + cw * sw + 28; ey1 = ey0 + ch * sh + 24
            hand_ellipse(d, (ex0, ey0, ex1, ey1), seed=i)
            if s.get("arrow", False):
                curved_arrow(d, (W - M - 40, title_bottom - 30), (min(ex1 + 10, W - M - 10), ey0 - 10))
        y = box[3] + 34
    if s.get("body"):
        f = SEMI(40 if s.get("shot") else 50)
        for ln in wrap(d, s["body"], f, W - 2 * M)[:5]:
            d.text((M, y), ln, font=f, fill=WHITE); y += int(f.size * 1.3)
    if not s.get("shot"):
        bb = img.getbbox()
        if bb:
            target = 190 + (1130 - 190 - (bb[3] - bb[1])) // 2
            final.paste(img, (0, target - bb[1]), img)
        img = final
    rc.footer(ImageDraw.Draw(img), i, n, s.get("source", spec.get("source")))
    return img


# ---------- PROOF (buy) ----------
DISCLAIMER = "Results vary. Every buyer's situation is different."


def proof_card(spec, s, i, n):
    rc = _rc()
    img = rc.base(); d = ImageDraw.Draw(img)
    rc.header(img, d, spec.get("tag", "NJ DREAM HOME"))
    cx0, cy0, cx1, cy1 = 110, 200, W - 110, 1120
    base_img = img
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    iw = cx1 - cx0 - 120
    y = cy0 + 70
    f = MBOLD(50)
    for ln in wrap(d, s.get("kicker", "").upper(), f, iw)[:2]:
        d.text((W // 2, y), ln, font=f, fill=INK, anchor="ma"); y += 62
    if s.get("lead"):
        f = MED(36)
        for ln in wrap(d, s["lead"], f, iw)[:2]:
            d.text((W // 2, y + 6), ln, font=f, fill=(60, 60, 60), anchor="ma"); y += 48
    y += 30
    pw, ph = 420, 300
    pic = scene_png(s.get("scene", "keys"), pw, ph, s.get("variant", 0)).convert("RGB")
    pic = rounded(pic, 24)
    px = (W - pw) // 2
    drop_shadow(img, (px, y, px + pw, y + ph), r=24, blur=14, alpha=90)
    img.paste(pic, (px, y), pic)
    d = ImageDraw.Draw(img)
    d.text((px + pw - 12, y + ph - 12), "ILLUSTRATION", font=BODY(16), fill=(255, 255, 255), anchor="rd")
    y += ph + 50
    d.line([(cx0 + 60, y - 18), (cx1 - 60, y - 18)], fill=(225, 225, 225), width=2)
    f = MBOLD(54)
    pl = wrap(d, s.get("punch", ""), f, iw)
    if len(pl) > 3:
        f = MBOLD(46); pl = wrap(d, s.get("punch", ""), f, iw)
    for ln in pl[:4]:
        d.text((W // 2, y), ln, font=f, fill=INK, anchor="ma"); y += int(f.size * 1.15)
    # size the white card to its content and center it in the open area
    ch = (y + 60) - cy0
    top = 190 + (1130 - 190 - ch) // 2
    box = (cx0, top, cx1, top + ch)
    drop_shadow(base_img, box, r=40, alpha=170)
    ImageDraw.Draw(base_img).rounded_rectangle(box, radius=40, fill=(250, 250, 248))
    base_img.paste(img, (0, top - cy0), img)
    img = base_img
    rc.footer(ImageDraw.Draw(img), i, n, s.get("source", spec.get("source")))
    return img


def proof_big(spec, s, i, n):
    rc = _rc()
    if s.get("photo"):
        img = cover_fit(photo_path(s["photo"]), s.get("focus"), s.get("zoom", 1.0))
        img = shade(img, top=0.5, bottom=0.92, overall=0.6, start=0.25)
    else:
        img = rc.base()
    d = ImageDraw.Draw(img)
    rc.header(img, d, spec.get("tag", "NJ DREAM HOME"))
    font = fit_font(d, s["lines"], lambda z: F("Inter-SemiBold.otf", z), W - 2 * M, 88, 50)
    lh = int(font.size * 1.18)
    y = 330
    for ln in s["lines"]:
        hi = ln.startswith("~"); t = ln.lstrip("~")
        shadow_text(img, (M, y), t, font, YELLOW if hi else WHITE)
        y += lh
    d = ImageDraw.Draw(img)
    if s.get("body"):
        y += 30
        f = BODY(40)
        for ln in wrap(d, s["body"], f, W - 2 * M)[:5]:
            shadow_text(img, (M, y), ln, f, (235, 235, 235), blur=4); y += 54
    disc = s.get("disclaimer", DISCLAIMER)
    f = MED(26)
    yy = 1150 - 34 * len(wrap(d, disc, f, W - 2 * M))
    for ln in wrap(d, disc, f, W - 2 * M):
        shadow_text(img, (W // 2, yy), ln, f, WHITE, blur=3, anchor="ma"); yy += 34
    rc.footer(ImageDraw.Draw(img), i, n, s.get("source", spec.get("source")))
    return img


def render(spec, slides, out_dir, card_fn):
    style = spec["style"]
    n = len(slides); paths = []
    for i, s in enumerate(slides, 1):
        t = s["type"]
        if t == "card":
            img = card_fn()
        elif style == "story" and t in ("cover", "story"):
            img = story_slide(spec, s, i, n)
        elif style == "bold" and t == "cover":
            img = bold_cover(spec, s, i, n)
        elif t == "step":
            img = bold_step(spec, s, i, n)
        elif t == "proof_card":
            img = proof_card(spec, s, i, n)
        elif t == "proof_big":
            img = proof_big(spec, s, i, n)
        elif t == "story":
            img = story_slide(spec, s, i, n)
        elif t == "cover" and style == "proof":
            img = bold_cover(spec, s, i, n)
        else:
            img = brand_slide(spec, s, i, n)
        p = os.path.join(out_dir, f"{spec['id']}_{i}of{n}.jpg")
        img.convert("RGB").save(p, "JPEG", quality=95, subsampling=0, optimize=True); paths.append(p)
    return paths
