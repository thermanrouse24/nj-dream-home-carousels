#!/usr/bin/env python3
"""Notebook-paper style (Therm's reference: the handwritten "hooks" pages).

Lined paper, red margin line, three punched holes, blue handwriting, circled numbers and
yellow highlighter. Used two ways:

1. Carousels: put "style": "notebook" in a spec; render_carousel.py hands it to render() here.
   Slide types: cover, list, text, stat, point (same fields as the brand template).
   Wrap words in [[double brackets]] to highlight them, e.g. "You don't need [[20% down]]."
   The last slide is still Therm's business card (added by render_carousel.py).
2. Quote stories: python3 notebook.py quote "Quote with [[highlight]]" OUT_PREFIX
   writes OUT_PREFIX_story.jpg (1080x1920) and OUT_PREFIX_square.jpg (1080x1080).

Fonts: Kalam (Indian Type Foundry) and Patrick Hand, both SIL Open Font License, free for
commercial use.
"""
import os, random, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = (240, 236, 226)
RULE = (150, 182, 222)
MARGIN = (226, 120, 130)
INK = (28, 30, 128)
INK_SOFT = (70, 74, 150)
HL = (255, 238, 70)
LINE_GAP = 66


def F(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


TITLE = lambda s: F("Kalam-Bold.ttf", s)
HAND = lambda s: F("Kalam-Regular.ttf", s)
SMALL = lambda s: F("PatrickHand-Regular.ttf", s)


def paper(W, H, seed=1):
    rnd = random.Random(seed)
    im = Image.new("RGB", (W, H), PAPER)
    # faint paper grain
    noise = Image.effect_noise((W, H), 9).convert("L").point(lambda v: 128 + (v - 128) // 3)
    im = Image.blend(im, Image.merge("RGB", (noise, noise, noise)), 0.05)
    d = ImageDraw.Draw(im)
    for y in range(150, H, LINE_GAP):
        d.line([(0, y + rnd.randint(-1, 1)), (W, y + rnd.randint(-1, 1))], fill=RULE, width=2)
    d.line([(122, 0), (122, H)], fill=MARGIN, width=3)
    # punched holes: dark hole with a lighter rim
    for frac in (0.12, 0.5, 0.88):
        cy = int(H * frac)
        d.ellipse((30, cy - 26, 82, cy + 26), fill=(205, 198, 184))
        d.ellipse((34, cy - 22, 78, cy + 22), fill=(66, 56, 44))
        d.ellipse((40, cy - 16, 72, cy + 12), fill=(92, 80, 64))
    return im


def tokens(text):
    """Split into (word, highlighted) pairs. [[...]] marks a highlighted run."""
    out = []
    for part in re.split(r"(\[\[.*?\]\])", text):
        hl = part.startswith("[[")
        body = part[2:-2] if hl else part
        # punctuation right after a highlight ("[[budget]].") sticks to that word, no space
        if not hl and out and body and not body[0].isspace():
            first, _, rest = body.partition(" ")
            out[-1] = (out[-1][0] + first, out[-1][1]); body = rest
        for w in body.split():
            out.append((w, hl))
    return out


def wrap_tokens(d, toks, font, maxw):
    lines, cur = [], []
    for t in toks:
        trial = " ".join(w for w, _ in cur + [t])
        if cur and d.textlength(trial, font=font) > maxw:
            lines.append(cur); cur = [t]
        else:
            cur.append(t)
    if cur:
        lines.append(cur)
    return lines


def draw_line(d, x, y, toks, font, fill=INK, hl_layer=None):
    sp = d.textlength(" ", font=font)
    for i, (w, hl) in enumerate(toks):
        tw = d.textlength(w, font=font)
        if hl and hl_layer is not None:
            asc, desc = font.getmetrics()
            nxt_hl = i + 1 < len(toks) and toks[i + 1][1]
            hl_layer.rounded_rectangle((x - 6, y + asc * 0.28, x + tw + (sp if nxt_hl else 6), y + asc + desc * 0.15),
                                       radius=8, fill=HL + (150,))
        d.text((x, y), w, font=font, fill=fill)
        x += tw + sp
    return x


def para(img, x, y, text, font, maxw, line_h, fill=INK):
    """Draw text with highlights; highlights go UNDER the ink."""
    hl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    ink = Image.new("RGBA", img.size, (0, 0, 0, 0))
    idr = ImageDraw.Draw(ink)
    lines = wrap_tokens(idr, tokens(text), font, maxw)
    for ln in lines:
        draw_line(idr, x, y, ln, font, fill, hd)
        y += line_h
    hl = hl.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(hl)
    img.alpha_composite(ink)
    return y


def circled(d, cx, cy, r, num):
    """Hand-drawn double circle with a number inside."""
    for k, (dx, dy, rr) in enumerate(((0, 0, r), (2, -1, r - 3))):
        d.ellipse((cx - rr + dx, cy - rr + dy, cx + rr + dx, cy + rr + dy), outline=INK, width=3)
    f = HAND(int(r * 1.15))
    tw = d.textlength(num, font=f)
    d.text((cx - tw / 2, cy - r * 0.78), num, font=f, fill=INK)


def title(img, d, text, y, W, size=96):
    f = TITLE(size)
    while d.textlength(text, font=f) > W - 260 and size > 56:
        size -= 4; f = TITLE(size)
    x = 190
    # sketchy bold: draw a few offset passes
    for dx, dy in ((0, 0), (2, 1), (-1, 2)):
        d.text((x + dx, y + dy), text, font=f, fill=INK)
    tw = d.textlength(text, font=f)
    uy = y + int(size * 1.25)
    d.line([(x - 10, uy + 4), (x + tw * 0.5, uy), (x + tw + 10, uy - 3)], fill=INK, width=4, joint="curve")
    return uy + 40


def brand(d, W):
    f = SMALL(30)
    d.line([(W - 170, 92), (W - 128, 66), (W - 86, 92)], fill=INK, width=3)
    for i, w in enumerate(["NJ", "DREAM", "HOME"]):
        tw = d.textlength(w, font=f)
        d.text((W - 128 - tw / 2, 92 + i * 28), w, font=f, fill=INK)


def footer(d, W, H, page, total, source=None):
    f = SMALL(28)
    y = H - 96
    if source:
        d.text((150, y - 34), ("Source: " + source)[:95], font=SMALL(24), fill=INK_SOFT)
    d.text((150, y), "Therm The Realtor | eXp Realty", font=f, fill=INK_SOFT)
    t = f"{page}/{total}"
    d.text((W - 80 - d.textlength(t, font=f), y), t, font=f, fill=INK_SOFT)


def slide(s, i, n, src, seed):
    W, H = 1080, 1350
    img = paper(W, H, seed).convert("RGBA")
    d = ImageDraw.Draw(img)
    brand(d, W)
    t = s["type"]
    if t == "cover":
        y = 300
        if s.get("eyebrow"):
            y = para(img, 190, y, s["eyebrow"], HAND(46), W - 280, LINE_GAP, INK_SOFT) + 10
        for ln in s["lines"]:
            txt = ln.lstrip("~")
            if ln.startswith("~"):
                txt = f"[[{txt}]]"
            y = para(img, 190, y, txt, TITLE(92), W - 260, 104)
        if s.get("sub"):
            para(img, 190, y + 40, s["sub"], HAND(46), W - 280, LINE_GAP)
        d = ImageDraw.Draw(img)
        d.text((W - 300, H - 160), "Swipe  ->", font=SMALL(40), fill=INK)
        footer(d, W, H, i, n, None)
    elif t == "list":
        y = title(img, d, s["title"], 210, W)
        f = HAND(50)
        for k, item in enumerate(s["items"], 1):
            circled(ImageDraw.Draw(img), 168 + 40, y + 34, 34, str(k))
            y = para(img, 270, y, item, f, W - 340, 62) + 42
        footer(ImageDraw.Draw(img), W, H, i, n, s.get("source", src))
    else:  # text, stat, point
        top = 230
        if t == "point" and s.get("num"):
            circled(d, 230, 228, 44, str(s["num"]))
            top = 300
        y = title(img, d, s.get("title") or s.get("label", ""), top, W)
        if t == "stat":
            y = para(img, 190, y + 10, f"[[{s['value']}]]", TITLE(120), W - 260, 140) + 20
        body = s.get("body", "")
        if body:
            para(img, 190, y + 10, body, HAND(50), W - 270, LINE_GAP)
        footer(ImageDraw.Draw(img), W, H, i, n, s.get("source", src))
    return img.convert("RGB")


def render(spec, slides, out_dir, card_fn):
    """Called by render_carousel.render for "style": "notebook"."""
    n = len(slides); paths = []
    for i, s in enumerate(slides, 1):
        if s["type"] == "card":
            img = card_fn()
        else:
            img = slide(s, i, n, spec.get("source"), seed=i)
        p = os.path.join(out_dir, f"{spec['id']}_{i}of{n}.jpg")
        img.save(p, "JPEG", quality=95, subsampling=0, optimize=True); paths.append(p)
    return paths


def quote(text, out_prefix):
    outs = []
    for kind, (W, H) in (("story", (1080, 1920)), ("square", (1080, 1080))):
        img = paper(W, H, seed=len(text)).convert("RGBA")
        d = ImageDraw.Draw(img)
        brand(d, W)
        size = 72 if kind == "story" else 60
        f = HAND(size)
        probe = wrap_tokens(d, tokens(text), f, W - 290)
        block = len(probe) * int(size * 1.3)
        y = max(250, (H - block) // 2 - 40)
        y = para(img, 190, y, text, f, W - 290, int(size * 1.3))
        d = ImageDraw.Draw(img)
        d.text((190, y + 40), "- Therm The Realtor", font=SMALL(44), fill=INK)
        d.text((190, y + 96), "@therm.realtor", font=SMALL(34), fill=INK_SOFT)
        out = f"{out_prefix}_{kind}.jpg"
        img.convert("RGB").save(out, "JPEG", quality=95, subsampling=0)
        outs.append(out)
    return outs


if __name__ == "__main__":
    if sys.argv[1] == "quote":
        for p in quote(sys.argv[2], sys.argv[3]):
            print(p)
