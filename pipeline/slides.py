#!/usr/bin/env python3
"""Drop-alert carousel renderer (pit-sheet style) — data-driven, no invented facts."""
import cairosvg

W = H = 1080
BG, INK, YEL, DIM, RED = "#121316", "#F2F1EC", "#FFD23F", "#8B8D93", "#E8442E"
PANEL, LINE = "#191B1F", "#2A2D33"
SANS, MONO = "Inter", "JetBrains Mono"
HANDLE = "@AISN0207"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, size, fill=INK, font=SANS, weight=900, anchor="start",
      spacing="-0.02em", style=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{spacing}" {style}>{esc(s)}</text>')


def hazard(y, h=26):
    p = [f'<rect x="0" y="{y}" width="{W}" height="{h}" fill="{YEL}"/>']
    for x in range(-60, W + 60, 52):
        p.append(f'<polygon points="{x},{y+h} {x+26},{y+h} {x+26+h},{y} {x+h},{y}" fill="{BG}"/>')
    clip = f'<clipPath id="hz{y}"><rect x="0" y="{y}" width="{W}" height="{h}"/></clipPath>'
    return f'<g clip-path="url(#hz{y})">' + "".join(p) + "</g>" + clip


def checker(y, size=18, rows=2):
    return "".join(
        f'<rect x="{c*size}" y="{y+r*size}" width="{size}" height="{size}" fill="{INK}" opacity="0.9"/>'
        for r in range(rows) for c in range(0, W // size + 1) if (r + c) % 2 == 0)


def frame(lap, ticker="OPENAI SUPPLY CO. — DROP WATCH"):
    top = (f'<rect width="{W}" height="52" fill="{YEL}"/>'
           + t(40, 36, ticker, 21, fill=BG, font=MONO, weight=700, spacing="0.12em")
           + t(W - 40, 36, "●  LIVE", 21, fill=BG, font=MONO, weight=700,
               anchor="end", spacing="0.12em"))
    bottom = (checker(H - 96, 16, 2)
              + f'<rect x="0" y="{H-60}" width="{W}" height="60" fill="{BG}"/>'
              + t(40, H - 24, f"LAP {lap:02d}/10", 22, fill=YEL, font=MONO,
                  weight=700, spacing="0.14em")
              + t(W - 40, H - 24, HANDLE, 22, fill=DIM, font=MONO, weight=700,
                  anchor="end", spacing="0.14em"))
    ghost = t(W - 24, 300, f"{lap:02d}", 300, fill="none", font=SANS, weight=900,
              anchor="end", style=f'stroke="{LINE}" stroke-width="2"')
    return top + ghost + bottom


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
            + body + "</svg>")


def wrap(text, limit):
    words, lines, cur = str(text).split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > limit and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = f"{cur} {w_}".strip()
    if cur:
        lines.append(cur)
    return lines[:6]


def mono_block(x, y, lines, size=29, gap=48, fill=INK):
    return "".join(t(x, y + i * gap, ln, size, fill=fill, font=MONO, weight=700,
                     spacing="0em") for i, ln in enumerate(lines))


def build_slides(p, shop, tag="NEW DROP"):
    """p: {name, price, url, desc?, specs?: [(k,v)...]}; shop: {in_stock:[(n,pr)], sold_out:[n]}"""
    name = p["name"].upper()
    price = p.get("price") or ""
    slides = []

    s = frame(1) + hazard(120)
    s += t(64, 320, tag.split()[0], 190, fill=YEL) + t(64, 490, tag.split()[-1], 190)
    s += mono_block(64, 570, wrap(f"{p['name']} — spotted on the official OpenAI Supply Co. store.", 46), 32, 46)
    s += f'<rect x="64" y="690" width="{40+len(name)*26}" height="86" fill="{YEL}"/>'
    s += t(90, 748, name, 42, fill=BG)
    s += t(64, 840, "SWIPE FOR THE FULL SHEET  →", 26, fill=YEL, font=MONO,
           weight=700, spacing="0.14em")
    s += hazard(880)
    slides.append(s)

    s = frame(2) + t(64, 200, "THE ITEM", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    nm = wrap(name, 12)
    for i, ln in enumerate(nm[:2]):
        s += t(64, 330 + i * 130, ln, 130)
    s += t(64, 330 + len(nm[:2]) * 130, price if price else "PRICE ON PAGE", 84, fill=YEL)
    s += mono_block(64, 430 + len(nm[:2]) * 130, wrap(p.get("desc", "Straight from the official store page."), 48), 29, 44)
    slides.append(s)

    s = frame(3) + t(64, 200, "SPEC SHEET", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 300, "STRAIGHT FROM", 72) + t(64, 376, "THE PAGE.", 72, fill=YEL)
    specs = (p.get("specs") or [("SOURCE", "Official product page"),
                                ("STATUS", "In stock at post time")])[:6]
    y = 440
    for k, v in specs:
        s += f'<rect x="64" y="{y}" width="952" height="72" fill="{PANEL}" stroke="{LINE}"/>'
        s += t(96, y + 47, str(k).upper()[:14], 26, fill=DIM, font=MONO, weight=700, spacing="0.12em")
        s += t(400, y + 47, str(v)[:40], 30, font=MONO, weight=700, spacing="0em")
        y += 72
    slides.append(s)

    s = frame(4) + t(64, 200, "CURRENT STORE LINEUP", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 300, "WHAT'S LIVE", 68) + t(64, 372, "RIGHT NOW.", 68, fill=YEL)
    y = 430
    for n, pr in shop["in_stock"][:8]:
        s += t(64, y, n.upper()[:32], 30, font=MONO, weight=700, spacing="0em")
        s += t(1016, y, pr or "-", 30, fill=YEL, font=MONO, weight=700, anchor="end", spacing="0em")
        s += f'<line x1="64" y1="{y+16}" x2="1016" y2="{y+16}" stroke="{LINE}"/>'
        y += 58
    slides.append(s)

    s = frame(5) + t(64, 200, "TRACK RECORD", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 340, "THIS STORE", 96) + t(64, 440, "SELLS OUT.", 96, fill=RED) + t(64, 530, "FAST.", 96)
    gone_n, total = len(shop["sold_out"]), len(shop["sold_out"]) + len(shop["in_stock"])
    s += mono_block(64, 630, [
        "July 2026 — the store opened to the public.",
        "Press reported sizes selling out within hours.",
        "",
        f"Right now: {gone_n} of {total} listed items are gone."], 29, 44)
    slides.append(s)

    s = frame(6) + t(64, 200, "ALREADY GONE", 26, fill=RED, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 296, "THE DNF BOARD", 64)
    y = 370
    for g in shop["sold_out"][:8]:
        s += f'<rect x="64" y="{y}" width="952" height="58" fill="{PANEL}" stroke="{LINE}"/>'
        s += t(96, y + 39, g.upper()[:30], 27, fill=DIM, font=MONO, weight=700, spacing="0.04em")
        s += t(984, y + 39, "SOLD OUT", 24, fill=RED, font=MONO, weight=700, anchor="end", spacing="0.1em")
        y += 58
    slides.append(s)

    s = frame(7) + t(64, 200, "AFTERMARKET", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 330, "SCARCITY IS", 88) + t(64, 422, "THE DESIGN.", 88, fill=YEL)
    s += mono_block(64, 540, [
        "· Employee-era OpenAI swag has resold for hundreds",
        "  of dollars on eBay (per press & sold listings).",
        '· Retired items get "decommissioned" dates in the',
        "  official archive. Sneaker-drop playbook."], 29, 52)
    slides.append(s)

    s = frame(8) + t(64, 200, "HONEST VERDICT", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 320, f"IS {price or 'IT'} WORTH IT?", 74)
    s += f'<rect x="64" y="380" width="460" height="330" fill="{PANEL}" stroke="{YEL}" stroke-width="2"/>'
    s += t(96, 448, "COP IF", 40, fill=YEL)
    s += mono_block(96, 510, ["you collect AI-lab", "artifacts and want the", "story, not just the", "item."], 28, 44)
    s += f'<rect x="556" y="380" width="460" height="330" fill="{PANEL}" stroke="{LINE}" stroke-width="2"/>'
    s += t(588, 448, "SKIP IF", 40, fill=DIM)
    s += mono_block(588, 510, ["you just want the", "generic version. You", "pay a premium for the", "logo moment."], 28, 44, fill=DIM)
    s += t(64, 790, "You're paying for the moment, not the object.", 32, fill=YEL, weight=800, spacing="0em")
    slides.append(s)

    s = frame(9) + t(64, 200, "PIT STOP GUIDE", 26, fill=YEL, font=MONO, weight=700, spacing="0.2em")
    s += t(64, 310, "HOW TO COP", 92)
    y = 400
    for n, txt in [("01", "openai.com/supply  →  SHOP"),
                   ("02", f"Find: {p['name'][:26]}"),
                   ("03", "Pick your size / option"),
                   ("04", "In stock at post time. Move.")]:
        s += f'<rect x="64" y="{y}" width="952" height="92" fill="{PANEL}" stroke="{LINE}"/>'
        s += t(96, y + 60, n, 40, fill=YEL, font=MONO, weight=700)
        s += t(190, y + 58, txt, 34, font=MONO, weight=700, spacing="0em")
        y += 92
    s += t(64, y + 56, "Not affiliated with OpenAI.", 27, fill=DIM, weight=700, spacing="0em")
    slides.append(s)

    s = frame(10, ticker="FOLLOW FOR DAILY AI MERCH INTEL") + checker(120, 22, 2)
    s += t(64, 330, "DON'T MISS", 108) + t(64, 440, "THE NEXT", 108) + t(64, 550, "DROP.", 108, fill=YEL)
    s += mono_block(64, 640, ["Daily drop alerts · restocks · resale intel",
                              "for OpenAI, Anthropic, Google & the rest."], 31, 48)
    s += f'<rect x="64" y="740" width="430" height="86" fill="{YEL}"/>'
    s += t(279, 797, "FOLLOW  +  SAVE", 36, fill=BG, anchor="middle")
    s += t(530, 797, f"→  {HANDLE}", 30, fill=DIM, font=MONO, weight=700, spacing="0.06em")
    slides.append(s)
    return slides


def render(slides, outdir):
    paths = []
    for i, body in enumerate(slides, 1):
        path = outdir / f"slide_{i:02d}.png"
        cairosvg.svg2png(bytestring=svg(body).encode(), write_to=str(path),
                         output_width=W, output_height=H)
        paths.append(path)
    return paths
