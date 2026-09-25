"""Constelly icons + social preview image.

Writes into img/:
  favicon.svg            browser tab icon (vector; modern browsers)
  favicon-32.png         fallback tab icon
  apple-touch-icon.png   180×180, iOS home screen
  icon-192.png, icon-512.png   Android home screen (site.webmanifest)
  og-image.png           1200×630 link preview (WhatsApp, iMessage, Slack, X, Facebook…)

Needs: pip install cairosvg pillow   (same as make_tutorial_gif.py)

The preview shows an original paper plane — never a real puzzle (check ORDER before changing it), so it can't spoil one.
Colours match css/style.css.
"""
import io
import random
from pathlib import Path

import cairosvg
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "img"
BG, FG, DOT, LINE, OK, MUTED = "#0b1026", "#e8ecff", "#c9d1ff", "#7f8bd6", "#ffd84a", "#5c6490"
FONT = "'Segoe UI', system-ui, -apple-system, Roboto, 'DejaVu Sans', sans-serif"

# ---- icon: five stars joined into a "C", on the night-sky square ----------------------------
ICON_DOTS = [(47, 17), (25, 15), (14, 32), (25, 49), (47, 47)]
ICON_LINES = [(0, 1), (1, 2), (2, 3), (3, 4)]


def icon_svg(rounded=True, pad=0.0):
    """pad shrinks the drawing toward the centre (for maskable / home-screen icons)."""
    s = 1 - 2 * pad
    pt = lambda p: (32 + (p[0] - 32) * s, 32 + (p[1] - 32) * s)
    rx = 14 if rounded else 0
    lines = "".join(
        f'<line x1="{pt(ICON_DOTS[a])[0]:.2f}" y1="{pt(ICON_DOTS[a])[1]:.2f}" '
        f'x2="{pt(ICON_DOTS[b])[0]:.2f}" y2="{pt(ICON_DOTS[b])[1]:.2f}"/>' for a, b in ICON_LINES)
    dots = "".join(f'<circle cx="{pt(p)[0]:.2f}" cy="{pt(p)[1]:.2f}" r="{5.6 * s:.2f}"/>'
                   for p in ICON_DOTS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            f'<rect width="64" height="64" rx="{rx}" fill="{BG}"/>'
            f'<g stroke="{OK}" stroke-width="{3.6 * s:.2f}" stroke-linecap="round">{lines}</g>'
            f'<g fill="{OK}">{dots}</g></svg>')


def png(svg, size, path):
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    Image.open(io.BytesIO(data)).convert("RGB" if "apple" in path.name or "icon-" in path.name
                                         else "RGBA").save(path, optimize=True)


# ---- social preview -------------------------------------------------------------------------
W, H = 1200, 630
PLANE = {  # an original drawing (not in the puzzle set), in px
    "n": (1075, 120), "a": (735, 285), "c": (900, 330), "b": (955, 520), "k": (835, 430),
}
PLANE_EDGES = [("n", "a"), ("a", "c"), ("n", "c"), ("n", "b"), ("c", "b"), ("c", "k"), ("k", "b")]
DRAWN = PLANE_EDGES[:5]  # the wings are done; the keel is still to draw


def og_svg():
    rnd = random.Random(7)
    stars = "".join(
        f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, H):.0f}" '
        f'r="{rnd.choice([1, 1, 1.4, 1.8])}" opacity="{rnd.uniform(0.25, 0.7):.2f}"/>'
        for _ in range(140))
    trail = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" opacity="{o}"/>' for x, y, r, o in
                    [(690, 330, 4, 0.7), (640, 385, 3, 0.5), (600, 450, 2.5, 0.35), (575, 520, 2, 0.2)])
    deg = {k: 0 for k in PLANE}
    have = {k: 0 for k in PLANE}
    for a, b in PLANE_EDGES:
        deg[a] += 1
        deg[b] += 1
    for a, b in DRAWN:
        have[a] += 1
        have[b] += 1
    lines = "".join(f'<line x1="{PLANE[a][0]}" y1="{PLANE[a][1]}" x2="{PLANE[b][0]}" y2="{PLANE[b][1]}"/>'
                    for a, b in DRAWN)
    dots = []
    for k, (x, y) in PLANE.items():
        left = deg[k] - have[k]
        if left == 0:  # complete + correct: bright yellow with a glow, number gone
            dots.append(f'<circle cx="{x}" cy="{y}" r="36" fill="url(#glow)"/>'
                        f'<circle cx="{x}" cy="{y}" r="17" fill="{OK}"/>')
        else:
            dots.append(f'<circle cx="{x}" cy="{y}" r="19" fill="{DOT}"/>'
                        f'<text x="{x}" y="{y + 8.5}" text-anchor="middle" font-size="24" '
                        f'font-weight="700" fill="{BG}">{left}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="glow">
      <stop offset="0.35" stop-color="{OK}" stop-opacity="0.45"/><stop offset="1" stop-color="{OK}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="sky" cx="72%" cy="45%" r="80%">
      <stop offset="0" stop-color="#18204a"/><stop offset="1" stop-color="{BG}"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <g fill="{FG}">{stars}</g>
  <g stroke="{LINE}" stroke-width="7" stroke-linecap="round">{lines}</g>
  <line x1="{PLANE['c'][0]}" y1="{PLANE['c'][1]}" x2="{PLANE['k'][0]}" y2="{PLANE['k'][1]}"
        stroke="{DOT}" stroke-width="4" stroke-dasharray="2 12" stroke-linecap="round" opacity="0.6"/>
  <g fill="{OK}">{trail}</g>
  <g font-family="{FONT}">{"".join(dots)}</g>
  <g font-family="{FONT}">
    <text x="90" y="265" font-size="96" font-weight="600" letter-spacing="5" fill="{FG}">Constelly</text>
    <text x="94" y="345" font-size="38" fill="{FG}" opacity="0.85">Connect the stars.</text>
    <text x="94" y="397" font-size="38" fill="{FG}" opacity="0.85">A new picture every day.</text>
    <text x="94" y="505" font-size="32" font-weight="600" letter-spacing="1" fill="{OK}">playconstelly.com</text>
  </g>
</svg>'''


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "favicon.svg").write_text(icon_svg() + "\n", encoding="utf-8")
    png(icon_svg(), 32, OUT / "favicon-32.png")
    png(icon_svg(rounded=False, pad=0.08), 180, OUT / "apple-touch-icon.png")  # iOS rounds it
    png(icon_svg(rounded=False, pad=0.14), 192, OUT / "icon-192.png")  # maskable-safe margin
    png(icon_svg(rounded=False, pad=0.14), 512, OUT / "icon-512.png")
    og = cairosvg.svg2png(bytestring=og_svg().encode(), output_width=W, output_height=H)
    Image.open(io.BytesIO(og)).convert("RGB").save(OUT / "og-image.png", optimize=True)
    for f in ["favicon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png",
              "icon-512.png", "og-image.png"]:
        print(f"img/{f}  {(OUT / f).stat().st_size / 1024:.1f} KB")
