#!/usr/bin/env python3
"""TikTok version of the business card story (Therm's rule, Oct 23 2026).
TikTok has no clickable bio link for this account yet, so the button reads DM ME "HOME"
instead of CLICK THE LINK IN MY BIO. Built from business_card_story.jpg:
the area under the card is redrawn from the story background, then the new button is drawn.
Usage: python3 make_card_tiktok.py   -> writes business_card_story_tiktok.jpg
       python3 make_card_tiktok.py posts/YYYY-MM-DD/<id>   -> writes <id>_6of6_tiktok.jpg
       (TikTok copy of a carousel's last slide, same card, DM ME "HOME" button)
"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
from render_carousel import HEAD, tracked, tracked_len, DARK, W, H
CTA = 'DM ME "HOME"'

def button(img, y_center_top, size):
    d = ImageDraw.Draw(img)
    fb = HEAD(size)
    tw = tracked_len(d, CTA, fb, 2)
    pad = 44 if size <= 40 else 56
    bw, bh = int(tw + 2 * pad), (96 if size <= 40 else 110)
    x = (img.width - bw) // 2
    y = y_center_top(bh)
    d.rounded_rectangle((x, y, x + bw, y + bh), radius=bh // 2, fill=(225, 183, 133))
    tracked(d, (x + pad, y + (bh - size) // 2 - 2), CTA, fb, DARK, 2)

if ARGS:
    prefix = ARGS[0]
    slide = Image.open(prefix + "_6of6.jpg").convert("RGB")
    bg = Image.open(os.path.join(HERE, "background.png")).convert("RGB")
    slide.paste(bg.crop((0, W, W, H)), (0, W))
    button(slide, lambda bh: W + (H - W - bh) // 2, 40)
    out = prefix + "_6of6_tiktok.jpg"
    slide.save(out, quality=95, subsampling=0); print(out); sys.exit(0)

def story_bg():
    bg = Image.open(os.path.join(HERE, "background.png")).convert("RGB")
    top = bg.crop((0, 0, 1080, 1000)).resize((1080, 1570))
    bottom = bg.crop((0, 1000, 1080, 1350))
    out = Image.new("RGB", (1080, 1920)); out.paste(top, (0, 0)); out.paste(bottom, (0, 1570))
    return out

img = Image.open(os.path.join(HERE, "business_card_story.jpg")).convert("RGB")
CARD_BOTTOM = 1442
img.paste(story_bg().crop((0, CARD_BOTTOM, 1080, 1920)), (0, CARD_BOTTOM))
button(img, lambda bh: 1530, 48)
img.save(os.path.join(HERE, "business_card_story_tiktok.jpg"), quality=95, subsampling=0)
print("business_card_story_tiktok.jpg")
