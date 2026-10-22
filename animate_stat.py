#!/usr/bin/env python3
"""Animate a "stat" slide as an MP4 (1080x1350, 30 fps).

Usage: python3 animate_stat.py spec.json SLIDE_NUMBER OUT.mp4
Motion: label slides in, the number counts up, the underline draws, the body fades in, hold.
Uses the same template, fonts and colors as render_carousel.py, so the last frame matches
the still slide.
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw
import render_carousel as rc

FPS, SECONDS = 30, 4.5


def ease(t):  # ease-out cubic, clamped
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def window(t, a, b):
    return ease((t - a) / (b - a))


def count_text(value, p):
    """Count every number in the value up from 0, keeping its decimals, e.g. '3.5% down'."""
    def rep(m):
        num = float(m.group(0).replace(",", ""))
        dec = len(m.group(0).split(".")[1]) if "." in m.group(0) else 0
        v = num * p
        s = f"{v:,.{dec}f}" if "," in m.group(0) else f"{v:.{dec}f}"
        return s
    return re.sub(r"\d[\d,]*(?:\.\d+)?", rep, value)


def draw_stat(layer, s, t):
    d = ImageDraw.Draw(layer)
    M, W = rc.M, rc.W
    y = 450
    # 1) label slides in from the left and fades in (0.0 - 0.4 s)
    a = window(t, 0.0, 0.4)
    lab = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    rc.eyebrow(ImageDraw.Draw(lab), y, s["label"])
    lab = lab.transform(lab.size, Image.AFFINE, (1, 0, int(40 * (1 - a)), 0, 1, 0))
    lab.putalpha(lab.getchannel("A").point(lambda v: int(v * a)))
    layer.alpha_composite(lab)
    # 2) number counts up (0.3 - 1.5 s); size fixed from the final value so nothing jumps
    val = s["value"].upper()
    size = 190
    while size > 80 and d.textlength(val, font=rc.HEAD(size)) > W - 2 * M:
        size -= 4
    f = rc.HEAD(size)
    if t >= 0.3:
        shown = count_text(val, window(t, 0.3, 1.5))
        pop = 1 + 0.06 * max(0.0, 1 - abs(t - 1.55) / 0.15)  # small pop when it lands
        txt = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((M - 6, y + 50), shown, font=f, fill=rc.CREAM)
        if pop > 1.001:
            bb = txt.getbbox()
            if bb:
                crop = txt.crop(bb)
                crop = crop.resize((int(crop.width * pop), int(crop.height * pop)), Image.LANCZOS)
                txt = Image.new("RGBA", layer.size, (0, 0, 0, 0))
                txt.paste(crop, (bb[0], bb[1] - (crop.height - (bb[3] - bb[1])) // 2), crop)
        layer.alpha_composite(txt)
    y2 = d.textbbox((M - 6, y + 50), val, font=f)[3] + 40
    # 3) underline draws (1.4 - 2.0 s)
    u = window(t, 1.4, 2.0)
    if u > 0:
        d.line([(M, y2), (M + int(120 * u), y2)], fill=rc.BRONZE, width=4)
    # 4) body fades in, one line after another (1.9 - 2.9 s)
    lines = rc.wrap(d, s.get("body", ""), rc.BODY(42), W - 2 * M)
    for k, ln in enumerate(lines):
        a = window(t, 1.9 + 0.25 * k, 2.4 + 0.25 * k)
        if a <= 0:
            continue
        ll = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(ll).text((M, y2 + 36 + 56 * k + int(16 * (1 - a))), ln, font=rc.BODY(42), fill=rc.CREAM)
        ll.putalpha(ll.getchannel("A").point(lambda v: int(v * a)))
        layer.alpha_composite(ll)


def main(spec_path, slide_no, out):
    spec = json.load(open(spec_path))
    rc.set_style(spec.get("style"))
    slides = [s for s in spec["slides"] if s["type"] not in ("cta", "card", "logo_cta")] + [{"type": "card"}]
    n, s = len(slides), slides[slide_no - 1]
    assert s["type"] == "stat", "animate_stat.py only animates stat slides"
    # background with header and footer, same as the still
    bg = rc.base()
    bd = ImageDraw.Draw(bg)
    rc.header(bg, bd, spec.get("tag", "NJ DREAM HOME"))
    rc.footer(bd, slide_no, n, s.get("source", spec.get("source")))
    bg = bg.convert("RGBA")
    # vertical offset: center the FINAL content exactly like render_carousel does
    final = Image.new("RGBA", (rc.W, rc.H), (0, 0, 0, 0))
    draw_stat(final, s, 99)
    bb = final.crop((0, 0, rc.W, 1150)).getbbox()
    dy = (190 + (1130 - 190 - (bb[3] - bb[1])) // 2) - bb[1]
    tmp = tempfile.mkdtemp()
    for i in range(int(FPS * SECONDS)):
        layer = Image.new("RGBA", (rc.W, rc.H), (0, 0, 0, 0))
        draw_stat(layer, s, i / FPS)
        content = layer.crop((0, 0, rc.W, 1150))
        frame = bg.copy()
        frame.alpha_composite(content, (0, dy))
        frame.convert("RGB").save(os.path.join(tmp, f"f{i:04d}.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", out], check=True)
    print(out)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
