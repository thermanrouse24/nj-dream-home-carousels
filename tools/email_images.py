#!/usr/bin/env python3
"""Make approval-email preview images that actually show up in Gmail.

Gmail's send tool STRIPS <img src="https://..."> links. Images only show when they are attached
inline: attachments[i] = {"content": <base64>, "filename": ..., "mimeType": "image/jpeg",
"inline": true} and the HTML uses <img src="cid:att<i>"> (i = zero-based position in attachments).

Usage: python3 tools/email_images.py OUT_DIR IMAGE [IMAGE ...]
Writes OUT_DIR/att<i>.b64 (small JPEG, max 560 px wide, under ~45 KB) and prints one line per image:
  att<i>  <file>  <bytes>  ->  use <img src="cid:att<i>">
Paste each .b64 file's content (cat it) as that attachment's "content", in the same order.
"""
import base64, io, os, sys
from PIL import Image

out, files = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    w = 560 if im.width >= im.height else 300          # wide sheets 560 px, tall story cards 300 px
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    q = 72
    while True:
        b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
        if b.tell() < 45_000 or q <= 40: break
        q -= 8
    data = base64.b64encode(b.getvalue()).decode()
    open(os.path.join(out, f"att{i}.b64"), "w").write(data)
    print(f"att{i}  {f}  {b.tell()} bytes  ->  <img src=\"cid:att{i}\">")
