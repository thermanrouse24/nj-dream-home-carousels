#!/usr/bin/env python3
"""Original illustrated scenes for local place cards (NJ Dream Home palette).

These are generic illustrations of a TYPE of place (a cafe storefront at dusk, a park path,
a train platform), drawn from scratch. They never depict or claim to be the actual business.
Every scene carries a small "ILLUSTRATION" tag.

Usage from Python:  render_scene(kind, variant, out_png, w=920, h=560)
kind:    LOCAL places only: coffee | brunch | bakery | pizza | market | library | park | train | events | default
         HOME-BUYING topics: home | savings | keys | documents | calendar | inspection | taxes (see home_scenes.py)
variant: 0, 1, 2 (changes awning/facade colors so three cards in a row look different)
"""
import io
import cairosvg
from PIL import Image

PAL = {
    "cream": "#F5ECD7", "bronze": "#E1B785", "bronze_d": "#B98B57", "forest": "#1F352D",
    "forest_d": "#13241A", "night": "#2A3549", "dusk": "#6B4F3A", "ink": "#16201A",
}
VARIANTS = [
    {"facade": "#4A3428", "trim": "#2E1F18", "aw1": "#E1B785", "aw2": "#F5ECD7"},
    {"facade": "#2F4A3C", "trim": "#1B2C23", "aw1": "#1F352D", "aw2": "#E1B785"},
    {"facade": "#5A4636", "trim": "#33261D", "aw1": "#B5533C", "aw2": "#F5ECD7"},
]
SIGN = {"coffee": "COFFEE", "brunch": "BRUNCH", "bakery": "BAKERY", "pizza": "PIZZA",
        "market": "MARKET", "library": "LIBRARY", "default": "OPEN"}


def _decal(kind, cx, cy, s, col):
    """Window decal glyph for the shop type."""
    if kind == "coffee":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linecap="round">'
                f'<path d="M{cx-s*0.45},{cy-s*0.1} h{s*0.75} v{s*0.35} a{s*0.3},{s*0.3} 0 0 1 -{s*0.3},{s*0.3} h-{s*0.15} a{s*0.3},{s*0.3} 0 0 1 -{s*0.3},-{s*0.3} z"/>'
                f'<path d="M{cx+s*0.3},{cy} a{s*0.15},{s*0.15} 0 0 1 0,{s*0.3}"/>'
                f'<path d="M{cx-s*0.2},{cy-s*0.25} q{s*0.08},-{s*0.12} 0,-{s*0.24} M{cx},{cy-s*0.25} q{s*0.08},-{s*0.12} 0,-{s*0.24}"/></g>')
    if kind == "pizza":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linejoin="round">'
                f'<path d="M{cx},{cy+s*0.5} L{cx-s*0.45},{cy-s*0.35} Q{cx},{cy-s*0.55} {cx+s*0.45},{cy-s*0.35} Z"/>'
                f'<circle cx="{cx-s*0.08}" cy="{cy-s*0.1}" r="{s*0.07}"/><circle cx="{cx+s*0.12}" cy="{cy+s*0.08}" r="{s*0.07}"/></g>')
    if kind == "bakery":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linecap="round">'
                f'<path d="M{cx-s*0.5},{cy+s*0.2} q0,-{s*0.55} {s*0.5},-{s*0.55} q{s*0.5},0 {s*0.5},{s*0.55} z"/>'
                f'<path d="M{cx-s*0.2},{cy-s*0.2} l{s*0.1},{s*0.18} M{cx},{cy-s*0.25} l{s*0.1},{s*0.2} M{cx+s*0.2},{cy-s*0.2} l{s*0.1},{s*0.18}"/></g>')
    if kind == "brunch":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linecap="round">'
                f'<circle cx="{cx}" cy="{cy}" r="{s*0.38}"/><circle cx="{cx}" cy="{cy}" r="{s*0.16}"/>'
                f'<path d="M{cx-s*0.62},{cy-s*0.35} v{s*0.7} M{cx+s*0.62},{cy-s*0.35} v{s*0.7}"/></g>')
    if kind == "library":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linejoin="round">'
                f'<path d="M{cx},{cy-s*0.3} L{cx-s*0.5},{cy-s*0.4} V{cy+s*0.35} L{cx},{cy+s*0.45} Z"/>'
                f'<path d="M{cx},{cy-s*0.3} L{cx+s*0.5},{cy-s*0.4} V{cy+s*0.35} L{cx},{cy+s*0.45} Z"/></g>')
    if kind == "market":
        return (f'<g fill="none" stroke="{col}" stroke-width="{s*0.08}" stroke-linejoin="round">'
                f'<path d="M{cx-s*0.5},{cy-s*0.1} h{s} l-{s*0.12},{s*0.5} h-{s*0.76} z"/>'
                f'<path d="M{cx-s*0.3},{cy-s*0.1} a{s*0.3},{s*0.3} 0 0 1 {s*0.6},0"/></g>')
    return ""


def storefront_svg(kind, v, w, h):
    V = VARIANTS[v % 3]
    sign = SIGN.get(kind, SIGN["default"])
    ground = h * 0.84
    fx, fw = w * 0.17, w * 0.66            # facade x and width
    ftop = h * 0.14
    aw_y = h * 0.36                        # awning top
    win_x, win_y, win_w, win_h = fx + fw * 0.07, h * 0.50, fw * 0.52, h * 0.30
    door_x, door_w = fx + fw * 0.66, fw * 0.24
    stripes = 9
    sw = (fw + 40) / stripes
    aw = ""
    for k in range(stripes):
        col = V["aw1"] if k % 2 == 0 else V["aw2"]
        x0 = fx - 20 + k * sw
        aw += (f'<path d="M{x0},{aw_y} h{sw} l{-sw*0.0},{h*0.09} q{-sw/2},{h*0.04} {-sw},0 z" fill="{col}"/>')
    # scallops
    sc = "".join(f'<path d="M{fx-20+k*sw},{aw_y+h*0.09} q{sw/2},{h*0.045} {sw},0" fill="{V["aw1"] if k%2==0 else V["aw2"]}"/>' for k in range(stripes))
    # brick lines
    bricks = "".join(f'<line x1="{fx}" y1="{ftop+12+r*18}" x2="{fx+fw}" y2="{ftop+12+r*18}" stroke="{V["trim"]}" stroke-opacity=".35" stroke-width="2"/>'
                     for r in range(int((aw_y - ftop) / 18)))
    lamps = "".join(f'<g><line x1="{win_x+win_w*p}" y1="{win_y}" x2="{win_x+win_w*p}" y2="{win_y+h*0.06}" stroke="#7A5A3A" stroke-width="3"/>'
                    f'<circle cx="{win_x+win_w*p}" cy="{win_y+h*0.075}" r="{h*0.018}" fill="#FFE7B8"/>'
                    f'<circle cx="{win_x+win_w*p}" cy="{win_y+h*0.075}" r="{h*0.05}" fill="url(#bulb)"/></g>' for p in (0.22, 0.5, 0.78))
    plants = "".join(
        f'<rect x="{px-18}" y="{ground-40}" width="36" height="40" rx="6" fill="{V["trim"]}"/>'
        f'<ellipse cx="{px}" cy="{ground-52}" rx="30" ry="26" fill="#2F5A3F"/>'
        f'<ellipse cx="{px-14}" cy="{ground-62}" rx="16" ry="18" fill="#3D7350"/>' for px in (fx - 34, fx + fw + 34))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAL['night']}"/><stop offset=".7" stop-color="{PAL['dusk']}"/><stop offset="1" stop-color="#8A6A4A"/></linearGradient>
 <linearGradient id="win" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE3AE"/><stop offset="1" stop-color="#E9A866"/></linearGradient>
 <radialGradient id="bulb"><stop offset="0" stop-color="#FFE7B8" stop-opacity=".9"/><stop offset="1" stop-color="#FFE7B8" stop-opacity="0"/></radialGradient>
 <radialGradient id="spill" cx=".5" cy="0" r="1"><stop offset="0" stop-color="#FFD9A0" stop-opacity=".55"/><stop offset="1" stop-color="#FFD9A0" stop-opacity="0"/></radialGradient>
 <radialGradient id="lampglow"><stop offset="0" stop-color="#FFE7B8" stop-opacity=".8"/><stop offset="1" stop-color="#FFE7B8" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{w}" height="{h}" fill="url(#sky)"/>
<path d="M0,{h*0.42} h{w*0.12} v-{h*0.12} h{w*0.06} v{h*0.12} h{w*0.0} V{ground} H0 Z" fill="#20302A"/>
<path d="M{w},{h*0.3} h-{w*0.13} v{h*0.1} h-{w*0.04} V{ground} H{w} Z" fill="#20302A"/>
<rect x="{w*0.02}" y="{h*0.48}" width="{w*0.05}" height="{h*0.07}" fill="#C79A5E" opacity=".55"/>
<rect x="{w*0.9}" y="{h*0.4}" width="{w*0.05}" height="{h*0.07}" fill="#C79A5E" opacity=".45"/>
<rect x="{fx}" y="{ftop}" width="{fw}" height="{ground-ftop}" fill="{V['facade']}"/>
{bricks}
<rect x="{fx-12}" y="{ftop-14}" width="{fw+24}" height="22" fill="{V['trim']}"/>
<rect x="{fx+fw*0.2}" y="{ftop+h*0.06}" width="{fw*0.6}" height="{h*0.12}" rx="8" fill="{PAL['ink']}" stroke="{PAL['bronze']}" stroke-width="3"/>
<text x="{fx+fw*0.5}" y="{ftop+h*0.145}" text-anchor="middle" font-family="Montserrat" font-weight="800" font-size="{h*0.075}" letter-spacing="{h*0.012}" fill="{PAL['bronze']}">{sign}</text>
{aw}{sc}
<rect x="{win_x-8}" y="{win_y-8}" width="{win_w+16}" height="{win_h+16}" fill="{V['trim']}"/>
<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" fill="url(#win)"/>
{lamps}
<rect x="{win_x}" y="{win_y+win_h*0.72}" width="{win_w}" height="{win_h*0.28}" fill="#7A4E2E" opacity=".55"/>
<line x1="{win_x+win_w/2}" y1="{win_y}" x2="{win_x+win_w/2}" y2="{win_y+win_h}" stroke="{V['trim']}" stroke-width="6"/>
{_decal(kind, win_x+win_w*0.25, win_y+win_h*0.4, h*0.12, PAL['ink'])}
<rect x="{door_x-8}" y="{win_y-30}" width="{door_w+16}" height="{ground-win_y+30}" fill="{V['trim']}"/>
<rect x="{door_x}" y="{win_y-22}" width="{door_w}" height="{ground-win_y+22}" fill="#3A2A20"/>
<rect x="{door_x+door_w*0.15}" y="{win_y-6}" width="{door_w*0.7}" height="{(ground-win_y)*0.55}" fill="url(#win)" opacity=".9"/>
<circle cx="{door_x+door_w*0.8}" cy="{win_y+(ground-win_y)*0.62}" r="6" fill="{PAL['bronze']}"/>
<rect x="0" y="{ground}" width="{w}" height="{h-ground}" fill="#2B2620"/>
<rect x="0" y="{ground}" width="{w}" height="6" fill="#4A4036"/>
<path d="M{win_x},{ground+6} L{win_x+win_w},{ground+6} L{win_x+win_w+40},{h} L{win_x-40},{h} Z" fill="#FFD9A0" opacity=".12"/>
{plants}
<line x1="{w*0.08}" y1="{ground}" x2="{w*0.08}" y2="{h*0.38}" stroke="#151A17" stroke-width="10"/>
<rect x="{w*0.08-16}" y="{h*0.33}" width="32" height="40" rx="6" fill="#151A17"/>
<rect x="{w*0.08-10}" y="{h*0.34}" width="20" height="26" rx="4" fill="#FFE7B8"/>
<circle cx="{w*0.08}" cy="{h*0.36}" r="{h*0.14}" fill="url(#lampglow)"/>
</svg>'''


def park_svg(v, w, h):
    """Park scene. variant 0 = midday, 1 = late afternoon (mirrored layout), 2 = night with moon and stars."""
    v = int(v) % 3
    ground = h * 0.62
    skies = (("#6F9BC4", "#CFE0E8"), ("#2A3549", "#C98B5A"), ("#0E1424", "#2A3549"))
    sun = ((w*0.22, h*0.24, h*0.1, "#FFF1C9", 1), (w*0.62, h*0.5, h*0.13, "#F5D9A8", .9), (w*0.5, h*0.2, h*0.08, "#E9ECF2", 1))[v]
    stars = ""
    if v == 2:
        for i, (sx, sy) in enumerate(((0.12,0.1),(0.3,0.18),(0.42,0.08),(0.66,0.14),(0.8,0.07),(0.9,0.2),(0.2,0.3),(0.72,0.32))):
            stars += f'<circle cx="{w*sx}" cy="{h*sy}" r="{3 if i % 2 else 2}" fill="#F5ECD7"/>'
    trees = ""
    tree_cols = ("#2F5A3F", "#3D7350") if v < 2 else ("#1E3A2A", "#264A35")
    for (x, r, c) in ((w*0.1, h*0.22, 0), (w*0.28, h*0.17, 1), (w*0.78, h*0.24, 0), (w*0.93, h*0.17, 1)):
        trees += f'<rect x="{x-7}" y="{ground-r*0.6}" width="14" height="{r*0.9}" fill="#3A2A20"/><circle cx="{x}" cy="{ground-r}" r="{r}" fill="{tree_cols[c]}"/>'
    flip = f' transform="translate({w},0) scale(-1,1)"' if v == 1 else ""
    lamp = ""
    if v == 2:
        lamp = (f'<line x1="{w*0.36}" y1="{ground+30}" x2="{w*0.36}" y2="{h*0.42}" stroke="#151A17" stroke-width="8"/>'
                f'<circle cx="{w*0.36}" cy="{h*0.41}" r="12" fill="#FFE7B8"/><circle cx="{w*0.36}" cy="{h*0.41}" r="{h*0.1}" fill="#FFE7B8" opacity=".18"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{skies[v][0]}"/><stop offset="1" stop-color="{skies[v][1]}"/></linearGradient>
<linearGradient id="grass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{"#2F5A3F" if v < 2 else "#1B3324"}"/><stop offset="1" stop-color="#13241A"/></linearGradient></defs>
<rect width="{w}" height="{h}" fill="url(#sky)"/>
{stars}
<circle cx="{sun[0]}" cy="{sun[1]}" r="{sun[2]}" fill="{sun[3]}" opacity="{sun[4]}"/>
<g{flip}>
<path d="M0,{ground} Q{w*0.3},{ground-40} {w*0.55},{ground-10} T{w},{ground-20} V{h} H0 Z" fill="url(#grass)"/>
{trees}
<path d="M{w*0.42},{h} Q{w*0.5},{h*0.8} {w*0.56},{ground} L{w*0.6},{ground} Q{w*0.58},{h*0.8} {w*0.66},{h} Z" fill="#C9A577" opacity="{.85 if v < 2 else .5}"/>
<g fill="#3A2A20"><rect x="{w*0.68}" y="{h*0.74}" width="{w*0.14}" height="10"/><rect x="{w*0.68}" y="{h*0.69}" width="{w*0.14}" height="8"/>
<rect x="{w*0.69}" y="{h*0.74}" width="8" height="34"/><rect x="{w*0.8}" y="{h*0.74}" width="8" height="34"/></g>
{lamp}
</g>
</svg>'''


def train_svg(v, w, h):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A3549"/><stop offset="1" stop-color="#8A6A4A"/></linearGradient></defs>
<rect width="{w}" height="{h}" fill="url(#sky)"/>
<rect x="0" y="{h*0.2}" width="{w}" height="14" fill="#1B2C23"/>
<g fill="#1B2C23">{''.join(f'<rect x="{x}" y="{h*0.2}" width="10" height="{h*0.5}"/>' for x in range(40, int(w), 180))}</g>
<rect x="{w*0.3}" y="{h*0.3}" width="{w*0.4}" height="{h*0.45}" rx="40" fill="#C9CFC8"/>
<rect x="{w*0.34}" y="{h*0.36}" width="{w*0.32}" height="{h*0.16}" rx="12" fill="#2A3549"/>
<rect x="{w*0.3}" y="{h*0.56}" width="{w*0.4}" height="18" fill="{PAL['bronze']}"/>
<circle cx="{w*0.37}" cy="{h*0.66}" r="16" fill="#FFE7B8"/><circle cx="{w*0.63}" cy="{h*0.66}" r="16" fill="#FFE7B8"/>
<rect x="0" y="{h*0.75}" width="{w}" height="{h*0.25}" fill="#3A3530"/>
<rect x="0" y="{h*0.75}" width="{w}" height="10" fill="{PAL['bronze']}"/>
</svg>'''


def render_scene(kind, variant, out_png, w=920, h=560):
    from home_scenes import HOME_KINDS, home_svg
    if kind in HOME_KINDS:
        svg = home_svg(kind, variant, w, h)
    elif kind == "park":
        svg = park_svg(variant, w, h)
    elif kind == "train":
        svg = train_svg(variant, w, h)
    else:
        svg = storefront_svg(kind if kind in SIGN else "default", variant, w, h)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w * 2, output_height=h * 2)
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((w, h), Image.LANCZOS)
    im.save(out_png)
    return out_png


if __name__ == "__main__":
    import sys
    render_scene(sys.argv[1], int(sys.argv[2]), sys.argv[3])
