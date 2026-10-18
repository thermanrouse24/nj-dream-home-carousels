#!/usr/bin/env python3
"""Turn a carousel's 4:5 slides into 9:16 Instagram Story frames (1080x1920).
Usage: python3 make_stories.py posts/YYYY-MM-DD/<id>
Writes posts/YYYY-MM-DD/<id>_story_<n>of<N>.jpg
The slide sits centered on the NJ Dream Home background, with room above and below
for Instagram's story UI.
"""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SW, SH = 1080, 1920

def story_bg():
    bg = Image.open(os.path.join(HERE, "background.png")).convert("RGB")
    # top: stretch the sky/forest gradient; bottom: keep mountains at natural scale
    top = bg.crop((0, 0, 1080, 1000)).resize((1080, 1570))
    bottom = bg.crop((0, 1000, 1080, 1350))
    out = Image.new("RGB", (SW, SH))
    out.paste(top, (0, 0)); out.paste(bottom, (0, 1570))
    return out

prefix = sys.argv[1]
files = sorted(glob.glob(prefix + "_[0-9]*of*.jpg"), key=lambda f: int(f.rsplit("_", 1)[1].split("of")[0]))
n = len(files)
sw, sh_ = 920, 1150  # slide size inside the frame
x, y = (SW - sw) // 2, 330
for k, f in enumerate(files, 1):
    frame = story_bg()
    slide = Image.open(f).convert("RGB").resize((sw, sh_), Image.LANCZOS)
    shadow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x + 8, y + 18, x + sw + 8, y + sh_ + 18), 28, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    frame.paste(shadow, (0, 0), shadow)
    mask = Image.new("L", (sw, sh_), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh_), 28, fill=255)
    frame.paste(slide, (x, y), mask)
    out = f"{prefix}_story_{k}of{n}.jpg"
    frame.save(out, quality=90)
    print(out)
