#!/usr/bin/env python3
"""Screenshot an OFFICIAL page for a "bold" step slide (formats.py).

Usage: python3 tools/shoot.py <url> shots/<name>.png [--width 1200] [--height 900] [--selector "css"]
       [--scroll-to "text on the page"] [--find "text to circle"]

Takes a real screenshot of the page (primary sources only: nj.gov, fema.gov, njtransit.com, the
county or town site...). With --find it prints the circle fractions [x, y, w, h] of that text in the
shot, ready to paste into the spec's "circle". Never screenshot a person's profile, a private page,
a listing photo or anything behind a login.
"""
import argparse, json, os, sys
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url"); ap.add_argument("out")
ap.add_argument("--width", type=int, default=1200); ap.add_argument("--height", type=int, default=900)
ap.add_argument("--selector"); ap.add_argument("--scroll-to"); ap.add_argument("--find")
a = ap.parse_args()
with sync_playwright() as p:
    px = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    b = p.chromium.launch(proxy={"server": px} if px else None)
    # ignore_https_errors only matters behind a TLS-inspecting proxy (cloud sandbox); GitHub Actions has none
    pg = b.new_page(viewport={"width": a.width, "height": a.height}, device_scale_factor=2, ignore_https_errors=bool(px))
    pg.goto(a.url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(3000)
    if a.scroll_to:
        pg.get_by_text(a.scroll_to, exact=False).first.scroll_into_view_if_needed()
        pg.mouse.wheel(0, -120); pg.wait_for_timeout(400)
    if a.selector:
        el = pg.locator(a.selector).first; el.screenshot(path=a.out); box0 = el.bounding_box()
    else:
        pg.screenshot(path=a.out); box0 = {"x": 0, "y": 0, "width": a.width, "height": a.height}
    if a.find:
        bb = pg.get_by_text(a.find, exact=False).first.bounding_box()
        if bb:
            fr = [(bb["x"] - box0["x"]) / box0["width"], (bb["y"] - box0["y"]) / box0["height"],
                  bb["width"] / box0["width"], bb["height"] / box0["height"]]
            print(json.dumps({"circle": [round(v, 3) for v in fr]}))
        else:
            print("text not found", file=sys.stderr)
    b.close()
print(a.out)
