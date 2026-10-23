#!/usr/bin/env python3
"""Make a one-image preview (3x2 grid) of a carousel's six slides.
Usage: python3 make_sheet.py posts/YYYY-MM-DD/<id>   (prefix without _1of6.jpg)
Writes posts/YYYY-MM-DD/<id>_preview.jpg
"""
import glob, sys
from PIL import Image

prefix = sys.argv[1]
files = sorted([f for f in glob.glob(prefix + "_[0-9]*of*.jpg") if f.rsplit("_", 1)[1].split("of")[0].isdigit() and f.endswith("of6.jpg")], key=lambda f: int(f.rsplit("_", 1)[1].split("of")[0]))
w, h, gap = 540, 675, 12
cols = 3
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), (15, 28, 21))
for k, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS)
    sheet.paste(im, (gap + (k % cols) * (w + gap), gap + (k // cols) * (h + gap)))
out = prefix + "_preview.jpg"
sheet.save(out, quality=85)
print(out)
