#!/usr/bin/env python3
"""Quote cards for Instagram Stories, TikTok and Threads (Therm's "post card" template).

Usage:
  python3 make_quote.py "Quote text" PHOTO OUT_PREFIX
    PHOTO = a file name in quote_photos/ (see quote_photos/photos.json) or a path
  Writes OUT_PREFIX_story.jpg (1080x1920, Instagram Story + TikTok) and
         OUT_PREFIX_square.jpg (1080x1080, Threads).

The look: Therm's own photo, washed out, with a frosted social-post card on top
(round NJ Dream Home avatar, name, @therm.realtor, the quote, comment / like / share icons).
No like or comment COUNTS are drawn: made-up numbers would be fake social proof.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "quote_photos")
INK = (20, 22, 24)
GRAY = (120, 126, 132)
BLUE = (100, 181, 246)
NAME, HANDLE = "Therman Rouse", "@therm.realtor"


def F(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


def photo_info(photo):
    meta = json.load(open(os.path.join(PH, "photos.json")))
    for p in meta["photos"]:
        if p["file"] == photo:
            return os.path.join(PH, p["file"]), p.get("focus", [0.5, 0.3]), p.get("has_logo", False)
    return photo, [0.5, 0.3], False


def cover(img, W, H, focus, face_y):
    """Crop-to-fill so the focus point (his face) lands at face_y (fraction of the output height)."""
    s = max(W / img.width, H / img.height)
    im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = min(max(int(im.width * focus[0] - W / 2), 0), im.width - W)
    y = min(max(int(im.height * focus[1] - H * face_y), 0), im.height - H)
    return im.crop((x, y, x + W, y + H))


def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                cur = t
            else:
                out.append(cur); cur = w
        out.append(cur)
    return out


def icons(d, x, y, s):
    sw = max(3, s // 9)
    # comment bubble
    d.ellipse((x, y, x + s, y + s * 0.9), outline=INK, width=sw)
    d.polygon([(x + s * 0.1, y + s * 0.62), (x, y + s), (x + s * 0.38, y + s * 0.84)], fill=INK)
    # heart
    hx = x + s * 4.2
    r = s * 0.28
    d.ellipse((hx, y + s * 0.05, hx + 2 * r, y + s * 0.05 + 2 * r), fill=INK)
    d.ellipse((hx + 2 * r - s * 0.02, y + s * 0.05, hx + 4 * r - s * 0.02, y + s * 0.05 + 2 * r), fill=INK)
    d.polygon([(hx + s * 0.02, y + s * 0.4), (hx + 4 * r - s * 0.04, y + s * 0.4), (hx + 2 * r - s * 0.01, y + s * 0.98)], fill=INK)
    # share (three dots joined)
    sx = x + s * 8.4
    pts = [(sx + s * 0.8, y + s * 0.12), (sx + s * 0.12, y + s * 0.5), (sx + s * 0.8, y + s * 0.88)]
    d.line([pts[0], pts[1], pts[2]], fill=INK, width=sw)
    for (px, py) in pts:
        d.ellipse((px - s * 0.14, py - s * 0.14, px + s * 0.14, py + s * 0.14), outline=INK, width=sw, fill=(255, 255, 255))


def card(W, quote, scale):
    """The frosted post card, as an RGBA image, sized to its text."""
    cw = int(W - 2 * 110 * scale)
    pad = int(56 * scale)
    av = int(166 * scale)
    fq = F("Inter-Regular.otf", int(40 * scale))
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = int(44 * scale)
    lines = wrap(tmp, quote, F("Inter-Regular.otf", size), cw - 2 * pad)
    while len(lines) > 7 and size > 30:
        size -= 2
        lines = wrap(tmp, quote, F("Inter-Regular.otf", size), cw - 2 * pad)
    fq = F("Inter-Regular.otf", size)
    lh = int(size * 1.36)
    ch = pad + av + int(34 * scale) + lh * len(lines) + int(90 * scale) + int(48 * scale) + pad
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=int(44 * scale), fill=(255, 255, 255, 205),
                        outline=BLUE + (255,), width=max(2, int(3 * scale)))
    a = Image.open(os.path.join(PH, "avatar.png")).convert("RGBA").resize((av, av), Image.LANCZOS)
    c.alpha_composite(a, (pad, pad))
    d.text((pad + av + int(22 * scale), pad + int(26 * scale)), NAME, font=F("Montserrat-SemiBold.ttf", int(40 * scale)), fill=INK)
    d.text((pad + av + int(22 * scale), pad + int(82 * scale)), HANDLE, font=F("Inter-Regular.otf", int(34 * scale)), fill=GRAY)
    for k in range(3):  # the three blue dots
        r = int(8 * scale)
        cx = cw - pad - k * int(30 * scale)
        d.ellipse((cx - r, pad + int(14 * scale) - r, cx + r, pad + int(14 * scale) + r), fill=BLUE)
    y = pad + av + int(34 * scale)
    for ln in lines:
        d.text((pad, y), ln, font=fq, fill=INK); y += lh
    icons(d, pad, y + int(70 * scale), int(44 * scale))
    return c


def logo(W):
    """Small NJ DREAM HOME mark, like the brand template."""
    im = Image.new("RGBA", (300, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(105, 34), (150, 6), (195, 34)], fill=(225, 183, 133), width=6, joint="curve")
    f = F("Montserrat-ExtraBold.ttf", 46)
    for i, w in enumerate(["NJ", "DREAM", "HOME"]):
        tw = d.textlength(w, font=f)
        d.text((150 - tw / 2, 34 + i * 46), w, font=f, fill=(255, 255, 255))
    return im


def render(quote, photo, out_prefix):
    if photo == "notebook":  # Quote Bank Photo column says "notebook": handwritten notebook style
        import notebook
        return notebook.quote(quote, out_prefix)
    quote = quote.replace("[[", "").replace("]]", "")  # highlights only exist in notebook style
    path, focus, has_logo = photo_info(photo)
    src = Image.open(path).convert("RGB")
    outs = []
    for kind, (W, H), cy_frac, face_y in (("story", (1080, 1920), 0.62, 0.22), ("square", (1080, 1080), 0.62, 0.15)):
        bg = cover(src, W, H, focus, face_y)
        bg = Image.blend(bg, Image.new("RGB", (W, H), (255, 255, 255)), 0.22).convert("RGBA")
        c = card(W, quote, 1.0)
        x = (W - c.width) // 2
        y = int(H * cy_frac - c.height / 2)
        if kind == "square":
            y = max(230, min(y, H - c.height - 165))
        # soft blur of the photo under the card = frosted glass
        region = bg.crop((x, y, x + c.width, y + c.height)).filter(ImageFilter.GaussianBlur(14))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, c.width - 1, c.height - 1), radius=44, fill=255)
        bg.paste(region, (x, y), mask)
        bg.alpha_composite(c, (x, y))
        if has_logo:  # the photo already carries the NJ Dream Home mark
            out = f"{out_prefix}_{kind}.jpg"
            bg.convert("RGB").save(out, "JPEG", quality=90); outs.append(out)
            continue
        lg = logo(W)
        scale = 0.62 if kind == "square" else 0.8
        lg = lg.resize((int(lg.width * scale), int(lg.height * scale)), Image.LANCZOS)
        bg.alpha_composite(lg, ((W - lg.width) // 2, H - lg.height - (34 if kind == "square" else 150)))
        out = f"{out_prefix}_{kind}.jpg"
        bg.convert("RGB").save(out, "JPEG", quality=90)
        outs.append(out)
    return outs


if __name__ == "__main__":
    for p in render(sys.argv[1], sys.argv[2], sys.argv[3]):
        print(p)
