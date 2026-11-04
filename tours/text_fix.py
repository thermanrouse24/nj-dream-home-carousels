#!/usr/bin/env python3
"""Fix the burned-in text in Therm's tour edits (Therm, Oct 29 2026).

His edit template has text overlays that are wrong for some platforms or break our ad rules:
  - "CLICK THE LINK IN BIO" / "JUST CLICK THE LINK IN BIO!": TikTok has no bio link, so on the TikTok
    copy every one of these is covered with a box saying DM ME "HOME" (Instagram/Facebook keep it).
  - "IT ONLY TAKES 30 SECONDS TO SAVE THOUSAND(S)": a money promise. Covered on every copy with
    "TAKES 30 SECONDS. NO OBLIGATION."
  - "WE HAVE HELPED HUNDREDS OF CLIENTS. WORK WITH THE BEST IN BUSINESS.": unverified count + "best"
    superlative. Covered on every copy with "LET'S MAKE YOUR PLAN."

How: OCR (tesseract) on 4 frames a second finds those lines and where/when they show; the boxes are
merged over time. Only that spot is softly blurred, with the new wording on top in the edit's own look
(tall yellow letters, dark outline), and only while the original text is on screen. No solid boxes
(Therm, Nov 4 2026: the black boxes sat on top of his edit). The rest of his edit is untouched.

Usage (testing): python3 tours/text_fix.py IN.mp4 OUT_ig.mp4 OUT_tiktok.mp4
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1080, 1920
FPS = 4

RULES = {
    # kind: (regex on the OCR'd line, replacement text, platforms it applies to)
    "cta": (r"LINK|L1NK|IN.?BIO|INIB|CLICK|CLIGK|GLICK", 'DM ME "HOME"', {"tiktok"}),
    "save": (r"SECOND|SECO|THOUSAND|SAVE", "TAKES 30 SECONDS. NO OBLIGATION.", {"ig", "tiktok"}),
    "best": (r"HUNDRED|CLIENT|BUSINESS|USINESS|BEST IN|HELPED", "LET'S MAKE YOUR PLAN.", {"ig", "tiktok"}),
}
KEEP = r"PRE.?APPROVAL|SCHEDULE|SHOWING|NEED|INFORMATION|DREAM HOME|WHY RENT|OWN"   # fine everywhere


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ffmpeg failed: " + p.stderr[-800:])
    return p.stdout


def ocr_lines(img):
    """Text lines [(text, x0, y0, x1, y1)] from normal + inverted OCR (white text with dark outlines)."""
    import pytesseract
    out = []
    g = img.convert("L")
    for v in (g, ImageOps.invert(g)):
        d = pytesseract.image_to_data(v, config="--psm 11", output_type=pytesseract.Output.DICT)
        words = [(d["text"][i].strip().upper(), d["left"][i], d["top"][i], d["width"][i], d["height"][i])
                 for i in range(len(d["text"])) if d["text"][i].strip() and float(d["conf"][i]) > 20
                 and d["height"][i] >= 18]
        words.sort(key=lambda w: (w[2] + w[4] / 2, w[1]))
        lines = []
        for t, x, y, w, h in words:      # join words whose vertical centres are close and that sit side by side
            cy = y + h / 2
            for L in lines:
                if abs(L["cy"] - cy) < max(14, h * 0.45) and x - L["x1"] < h * 2.2:
                    L["t"] += " " + t; L["x1"] = max(L["x1"], x + w); L["y0"] = min(L["y0"], y)
                    L["y1"] = max(L["y1"], y + h); L["x0"] = min(L["x0"], x)
                    break
            else:
                lines.append({"t": t, "x0": x, "y0": y, "x1": x + w, "y1": y + h, "cy": cy})
        out += [(L["t"], L["x0"], L["y0"], L["x1"], L["y1"]) for L in lines]
    return out


def scan(src):
    """Events [{kind, box:[x0,y0,x1,y1], t0, t1}] found in the video."""
    tmp = tempfile.mkdtemp()
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", f"fps={FPS},scale={W}:{H}", os.path.join(tmp, "f%05d.png")])
    hits = []
    for f in sorted(os.listdir(tmp)):
        t = (int(f[1:6]) - 1) / FPS
        for text, x0, y0, x1, y1 in ocr_lines(Image.open(os.path.join(tmp, f))):
            letters = re.sub(r"[^A-Z0-9]", "", text)
            if len(letters) < 4:
                continue
            for kind, (pat, _, _) in RULES.items():
                if re.search(pat, text) and not (kind == "cta" and re.search(r"PRE.?APPROVAL|SCHEDULE|SHOWING", text)
                                                 and not re.search(r"LINK|BIO", text)):
                    hits.append((kind, t, x0, y0, x1, y1))
                    break
    events = []
    for kind in RULES:
        hs = sorted([h for h in hits if h[0] == kind], key=lambda h: h[1])
        for h in hs:
            for e in events:   # same kind, close in time and overlapping vertically -> same overlay
                if e["kind"] == kind and h[1] - e["t1"] <= 0.75 and abs((h[3] + h[5]) / 2 - e["cy"]) < 120:
                    e["t1"] = h[1]; e["boxes"].append(h[2:]); break
            else:
                events.append({"kind": kind, "t0": h[1], "t1": h[1], "cy": (h[3] + h[5]) / 2, "boxes": [h[2:]]})
    # a one-frame OCR blip is noise; real overlays stay on screen
    events = [e for e in events if len(e["boxes"]) >= 2]

    def pct(v, q):
        v = sorted(v); return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]
    for e in events:
        bx = e.pop("boxes")
        x0, y0 = pct([b[0] for b in bx], 0.1), pct([b[1] for b in bx], 0.2)
        x1, y1 = pct([b[2] for b in bx], 0.9), pct([b[3] for b in bx], 0.8)
        padx, pady = 55, 16
        x0, x1, y0, y1 = max(0, x0 - padx), min(W, x1 + padx), max(0, y0 - pady), min(H, y1 + pady)
        if e["kind"] == "cta":          # keep the replacement no bigger than one line of text
            y1 = min(H, min(y1, y0 + 120) + 26)
        else:                           # 2-line claim boxes: cover the whole box and the header above it
            x0, x1 = 120, W - 120          # his claim overlays are centred boxes; never paint edge to edge
            y0 = max(0, y0 - (160 if e["kind"] == "save" else 30)); y1 = min(H, y1 + (75 if e["kind"] == "save" else 30))
            if e["kind"] == "save": x0 = max(0, x0 - 70)   # also covers the house emoji above-left of the line (Nov 3 2026)
            if y1 - y0 > 360:              # OCR noise can stretch it; keep it to the overlay's real size
                c = (y0 + y1) / 2; y0, y1 = c - 180, c + 180
            if e["kind"] == "best" and y1 - y0 < 240:   # 2-line claim; OCR sometimes reads only line 1
                y1 = min(H, y0 + 240)      # (Nov 1 2026: "Work with the best in business." showed under the IG box)
        e["box"] = [int(x0), int(y0), int(x1), int(y1)]
        e["t0"] = max(0.0, e["t0"] - 0.25); e["t1"] = e["t1"] + 0.25   # OCR samples every 0.25 s
    return events


FEATHER = 26       # px the blur fades out around the box, so there is no hard edge on his footage


def patch_png(texts, w, h, out):
    """Transparent picture with only the new words, in the style of the edit's own text."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    n = len(texts)
    size = min(92, int(h * 0.8 / n))
    while True:
        f = ImageFont.truetype(os.path.join(ROOT, "fonts", "Anton-Regular.ttf"), size)
        sw = max(3, size // 13)
        bbs = [d.textbbox((0, 0), t, font=f, stroke_width=sw) for t in texts]
        if size <= 20 or (max(b[2] - b[0] for b in bbs) <= w - 30 and sum(b[3] - b[1] for b in bbs) + 14 * (n - 1) <= h - 12):
            break
        size -= 2
    total = sum(b[3] - b[1] for b in bbs) + 14 * (n - 1)
    y = (h - total) / 2
    for t, b in zip(texts, bbs):
        d.text(((w - (b[2] - b[0])) / 2 - b[0], y - b[1]), t, font=f, fill=(255, 244, 150, 255),
               stroke_width=sw, stroke_fill=(15, 15, 15, 255))
        y += b[3] - b[1] + 14
    img.save(out)


def feather_png(w, h, out):
    """White box with soft edges: where the blur shows."""
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rectangle((FEATHER, FEATHER, w - 1 - FEATHER, h - 1 - FEATHER), fill=255)
    m.filter(ImageFilter.GaussianBlur(FEATHER / 2)).save(out)


def merge(events):
    """Overlays that overlap in time AND on screen become one box (no stacked, half-hidden patches)."""
    ev = [dict(e, texts=[RULES[e["kind"]][1]]) for e in events]
    changed = True
    while changed:
        changed = False
        for i in range(len(ev)):
            for j in range(i + 1, len(ev)):
                a, b = ev[i], ev[j]
                if a["t0"] > b["t1"] or b["t0"] > a["t1"]:
                    continue
                A, B = a["box"], b["box"]
                if A[0] > B[2] or B[0] > A[2] or A[1] > B[3] + 30 or B[1] > A[3] + 30:
                    continue
                top, bot = (a, b) if A[1] <= B[1] else (b, a)
                texts = [t for t in top["texts"] + bot["texts"]]
                a.update(box=[min(A[0], B[0]), min(A[1], B[1]), max(A[2], B[2]), max(A[3], B[3])],
                         t0=min(a["t0"], b["t0"]), t1=max(a["t1"], b["t1"]),
                         texts=list(dict.fromkeys(texts)), kind=a["kind"] + "+" + b["kind"])
                ev.pop(j); changed = True
                break
            if changed:
                break
    return ev


def apply(src, events, platform, out):
    """Overlay the replacement boxes that apply to this platform. Returns the list applied."""
    keep = [e for e in events if platform not in RULES[e["kind"]][2]]     # lines that stay (e.g. link in bio on IG)
    use = [dict(e, box=list(e["box"])) for e in events if platform in RULES[e["kind"]][2]]
    for e in use:   # never cut into a line that stays: stop the patch just above or below it
        for k in keep:
            if e["t0"] > k["t1"] or k["t0"] > e["t1"]:
                continue
            b, kb = e["box"], k["box"]
            if e["kind"] == "best" and kb[1] < b[1] + 240:   # OCR misread line 2 of the claim as a CTA:
                continue                                       # it is part of the claim, so cover it too
            if b[1] < kb[1] < b[3]:
                b[3] = kb[1] - 4
            elif b[1] < kb[3] < b[3]:
                b[1] = kb[3] + 4
    use = merge([e for e in use if e["box"][3] - e["box"][1] > 40])
    if not use:
        return src, []
    tmp = tempfile.mkdtemp()
    inputs, fc, prev, n = [], f"[0:v]scale={W}:{H},setsar=1[b0];", "b0", 1
    for i, e in enumerate(use):
        x0, y0, x1, y1 = e["box"]
        # the blur reaches FEATHER px past the box, so nothing of the old graphic peeks out at its edges
        bx0, by0, bx1, by1 = max(0, x0 - FEATHER), max(0, y0 - FEATHER), min(W, x1 + FEATHER), min(H, y1 + FEATHER)
        bw, bh = (bx1 - bx0) & ~1, (by1 - by0) & ~1
        mask, words = os.path.join(tmp, f"m{i}.png"), os.path.join(tmp, f"p{i}.png")
        feather_png(bw, bh, mask)
        patch_png(e["texts"], x1 - x0, y1 - y0, words)
        inputs += ["-loop", "1", "-i", mask, "-i", words]
        on = f"enable='between(t,{e['t0']:.2f},{e['t1']:.2f})'"
        fc += (f"[{prev}]split[k{i}][c{i}];[c{i}]crop={bw}:{bh}:{bx0}:{by0},boxblur=34:3,format=yuva420p[g{i}];"
               f"[{n}:v]format=gray[a{i}];[g{i}][a{i}]alphamerge[s{i}];"
               f"[k{i}][s{i}]overlay={bx0}:{by0}:shortest=1:{on}[h{i}];"
               f"[h{i}][{n + 1}:v]overlay={x0}:{y0}:{on}[b{i + 1}];")
        prev, n = f"b{i + 1}", n + 2
    fc = fc[:-(len(prev) + 3)] + "[v]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", out])
    return out, [{"kind": e["kind"], "box": e["box"], "t": [round(e["t0"], 1), round(e["t1"], 1)],
                  "text": " / ".join(e["texts"])} for e in use]


def fix(src):
    """Returns (ig_src, tiktok_src, info)."""
    try:
        import pytesseract  # noqa
    except ImportError:
        return src, src, {"error": "pytesseract not installed: text not fixed"}
    events = scan(src)
    tmp = tempfile.mkdtemp()
    ig, ig_info = apply(src, events, "ig", os.path.join(tmp, "ig.mp4"))
    tk, tk_info = apply(src, events, "tiktok", os.path.join(tmp, "tk.mp4"))
    return ig, tk, {"ig": ig_info, "tiktok": tk_info}


if __name__ == "__main__":
    ig, tk, info = fix(sys.argv[1])
    import shutil
    shutil.copy(ig, sys.argv[2]); shutil.copy(tk, sys.argv[3])
    print(json.dumps(info, indent=1))
