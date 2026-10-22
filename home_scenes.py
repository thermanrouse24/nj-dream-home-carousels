#!/usr/bin/env python3
"""Cartoon scenes for HOME-BUYING topics (used on cartoon-style covers).

Each scene is a flat, outlined house on a lawn plus one object that matches the topic.
Pick the scene that matches what the post is about. Never use a storefront (coffee, brunch,
pizza...) on a home-buying topic; those are only for local "top 3" posts.

kind -> use it for:
  home        general buying, timelines, "what happens next", working with an agent
  savings     down payment, 20% myth, closing costs, assistance programs, budgeting
  keys        closing day, offer accepted, first home, final walk-through
  documents   preapproval, contracts, attorney review, checklists, paperwork
  calendar    timelines, deadlines, "how long does it take", attorney review days
  inspection  home inspection, appraisal, radon, oil tank, what to check
  taxes       property taxes, transfer fee / mansion tax, ANCHOR, homestead
"""

HOME_KINDS = ("home", "savings", "keys", "documents", "calendar", "inspection", "taxes")
INK = "#1E2420"


def _house(cx, base, s, v):
    body = ["#F2C46B", "#9CC5A1", "#E9A37E"][v % 3]
    roof = ["#C8483C", "#2F5A3F", "#5A4636"][v % 3]
    bw, bh = s, s * 0.62
    x0, y0 = cx - bw / 2, base - bh
    sw = max(3, s * 0.016)
    return (f'<g stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round">'
            f'<rect x="{cx + s*0.18}" y="{y0 - s*0.36}" width="{s*0.1}" height="{s*0.3}" fill="{roof}"/>'
            f'<path d="M{x0 - s*0.08},{y0 + 2} L{cx},{y0 - s*0.42} L{x0 + bw + s*0.08},{y0 + 2} Z" fill="{roof}"/>'
            f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bh}" fill="{body}"/>'
            f'<rect x="{cx - s*0.09}" y="{base - s*0.34}" width="{s*0.18}" height="{s*0.34}" fill="#6B4F3A"/>'
            f'<circle cx="{cx + s*0.05}" cy="{base - s*0.17}" r="{s*0.015}" fill="{INK}"/>'
            f'<rect x="{x0 + s*0.1}" y="{y0 + s*0.12}" width="{s*0.2}" height="{s*0.17}" fill="#BFE0F0"/>'
            f'<rect x="{x0 + bw - s*0.3}" y="{y0 + s*0.12}" width="{s*0.2}" height="{s*0.17}" fill="#BFE0F0"/>'
            f'<path d="M{x0 + s*0.2},{y0 + s*0.12} v{s*0.17} M{x0 + bw - s*0.2},{y0 + s*0.12} v{s*0.17}"/>'
            f'</g>')


def _prop(kind, cx, base, s):
    sw = max(3, s * 0.03)
    g = f'<g stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round">'
    if kind == "savings":  # piggy bank + coin stack
        r = s * 0.36
        pcx = cx - s * 0.15
        cy = base - r * 1.25
        coins = "".join(f'<ellipse cx="{cx + s*0.62}" cy="{base - s*0.07 - k*s*0.1}" rx="{s*0.17}" ry="{s*0.06}" fill="#F2C46B"/>'
                        for k in range(5))
        return (g + f'<rect x="{pcx - r*0.65}" y="{cy + r*0.6}" width="{r*0.28}" height="{r*0.62}" fill="#F4A6A0"/>'
                f'<rect x="{pcx + r*0.38}" y="{cy + r*0.6}" width="{r*0.28}" height="{r*0.62}" fill="#F4A6A0"/>'
                f'<path d="M{pcx - r*0.35},{cy - r*0.8} l{r*0.12},-{r*0.4} l{r*0.28},{r*0.3} Z" fill="#F4A6A0"/>'
                f'<ellipse cx="{pcx}" cy="{cy}" rx="{r*1.15}" ry="{r*0.9}" fill="#F4A6A0"/>'
                f'<ellipse cx="{pcx - r*1.12}" cy="{cy + r*0.05}" rx="{r*0.22}" ry="{r*0.28}" fill="#F4A6A0"/>'
                f'<path d="M{pcx - r*0.15},{cy - r*0.62} h{r*0.5}"/>'
                f'<circle cx="{pcx - r*0.6}" cy="{cy - r*0.2}" r="{s*0.018}" fill="{INK}"/>'
                + coins + '</g>')
    if kind == "keys":
        r = s * 0.2
        cy = base - s * 0.5
        kx = cx - s * 0.35
        return (g + f'<rect x="{kx + r*0.8}" y="{cy - s*0.05}" width="{s*0.7}" height="{s*0.1}" fill="#F2C46B"/>'
                f'<rect x="{kx + r*0.8 + s*0.45}" y="{cy + s*0.05}" width="{s*0.08}" height="{s*0.14}" fill="#F2C46B"/>'
                f'<rect x="{kx + r*0.8 + s*0.58}" y="{cy + s*0.05}" width="{s*0.08}" height="{s*0.1}" fill="#F2C46B"/>'
                f'<circle cx="{kx}" cy="{cy}" r="{r}" fill="#F2C46B"/>'
                f'<circle cx="{kx}" cy="{cy}" r="{r*0.4}" fill="#F3E6CC"/></g>')
    if kind in ("documents", "taxes"):
        w_, h_ = s * 0.62, s * 0.82
        x0, y0 = cx - w_ / 2, base - h_
        lines = "".join(f'<path d="M{x0 + w_*0.32},{y0 + h_*(0.3 + k*0.16)} h{w_*0.52}"/>' for k in range(4))
        if kind == "documents":
            marks = "".join(f'<path d="M{x0 + w_*0.1},{y0 + h_*(0.3 + k*0.16)} l{w_*0.05},{w_*0.05} l{w_*0.08},-{w_*0.1}" stroke="#2F7A4A"/>'
                            for k in range(4))
        else:
            marks = (f'<text x="{x0 + w_*0.5}" y="{y0 + h_*0.2}" font-family="Arial" font-weight="700" '
                     f'font-size="{s*0.11}" text-anchor="middle" fill="{INK}" stroke="none">TAX</text>'
                     + "".join(f'<circle cx="{x0 + w_*0.17}" cy="{y0 + h_*(0.3 + k*0.16)}" r="{s*0.02}" fill="{INK}"/>' for k in range(4)))
        return (g + f'<rect x="{x0}" y="{y0}" width="{w_}" height="{h_}" rx="{s*0.03}" fill="#FFFFFF"/>'
                f'<rect x="{x0 + w_*0.3}" y="{y0 - s*0.05}" width="{w_*0.4}" height="{s*0.1}" rx="{s*0.02}" fill="#9AA39C"/>'
                + lines + marks + '</g>')
    if kind == "calendar":
        w_, h_ = s * 0.8, s * 0.72
        x0, y0 = cx - w_ / 2, base - h_
        cells = ""
        for r in range(3):
            for c in range(4):
                fill = "#C8483C" if (r, c) == (1, 2) else "#F3E6CC"
                cells += (f'<rect x="{x0 + w_*(0.08 + c*0.22)}" y="{y0 + h_*(0.36 + r*0.2)}" '
                          f'width="{w_*0.16}" height="{h_*0.13}" fill="{fill}"/>')
        return (g + f'<rect x="{x0}" y="{y0}" width="{w_}" height="{h_}" rx="{s*0.03}" fill="#FFFFFF"/>'
                f'<rect x="{x0}" y="{y0}" width="{w_}" height="{h_*0.24}" fill="#C8483C"/>'
                f'<path d="M{x0 + w_*0.25},{y0 - s*0.06} v{s*0.12} M{x0 + w_*0.75},{y0 - s*0.06} v{s*0.12}"/>'
                + cells + '</g>')
    if kind == "inspection":
        r = s * 0.26
        mx, cy = cx - s * 0.1, base - s * 0.62
        return (g + f'<path d="M{mx + r*0.7},{cy + r*0.7} L{mx + r*1.6},{cy + r*1.6}" stroke-width="{sw*2.6}"/>'
                f'<circle cx="{mx}" cy="{cy}" r="{r}" fill="#BFE0F0"/></g>')
    return ""


def home_svg(kind, v, w, h):
    ground = h * 0.84
    hs = h * 0.78
    hx = w * 0.36 if kind != "home" else w * 0.5
    clouds = (f'<g fill="#FFFFFF" stroke="{INK}" stroke-width="3">'
              f'<ellipse cx="{w*0.12}" cy="{h*0.2}" rx="{h*0.12}" ry="{h*0.05}"/>'
              f'<ellipse cx="{w*0.88}" cy="{h*0.14}" rx="{h*0.1}" ry="{h*0.045}"/></g>')
    bushes = "".join(f'<circle cx="{x}" cy="{ground - h*0.03}" r="{h*0.06}" fill="#5E9B6A" stroke="{INK}" stroke-width="3"/>'
                     for x in (hx - hs * 0.6, hx + hs * 0.6))
    prop = _prop(kind, w * 0.78, ground, h * 0.62) if kind != "home" else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="#F3E6CC"/>{clouds}'
            f'<rect x="-5" y="{ground}" width="{w + 10}" height="{h - ground + 5}" fill="#9CC5A1" stroke="{INK}" stroke-width="3"/>'
            f'{_house(hx, ground, hs, v)}{bushes}{prop}</svg>')
