"""Constelly how-to-play tutorial GIF: draw right, draw wrong (red), erase, draw right, solve.

Writes img/tutorial.gif (looping) and img/tutorial-still.png (shown instead when the player
prefers reduced motion). Needs: pip install cairosvg pillow

Frames are SVG (same colours/shapes as css/style.css + js/render.js), rasterised with cairosvg,
assembled into a looping GIF with PIL.
"""
import io
from pathlib import Path
import cairosvg
from PIL import Image

W = H = 400
OUT_PX = 400
FPS = 25
OUT_DIR = Path(__file__).resolve().parent.parent / "img"

BG, FG, DOT, LINE, OK, BAD, MUTED = "#0b1026", "#e8ecff", "#c9d1ff", "#7f8bd6", "#ffd84a", "#ff5a5a", "#5c6490"
R = 22  # dot radius

P = {"c": (200, 195), "a": (72, 250), "b": (296, 105), "d": (332, 250), "e": (160, 50)}
DEG = {"c": 2, "a": 1, "b": 1, "d": 1, "e": 1}
SOLUTION = {frozenset("ca"), frozenset("cd"), frozenset("be")}
ERASER = (200, 345)
ERASER_ICON = ("M16.2 3.8a2 2 0 0 1 2.8 0l2.2 2.2a2 2 0 0 1 0 2.8L12 18h7v2H8.5l-4.7-4.7a2 2 0 0 1 0-2.8z"
               "M6.3 13.9 10 17.6l.4.4H12l2-2-4.6-4.6z")


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def mid(a, b):
    return lerp(P[a], P[b], 0.5)


# ---- timeline: list of (duration_s, fn(t) -> state) ------------------------------------------
# state: lines (set of frozensets), selected (dot id|None), rubber ((x,y)|None),
#        finger ((x,y)|None), pressed (bool), eraser (bool), fade (0..1 overlay), blink (line, opacity)
def S(**kw):
    base = dict(lines=set(), selected=None, rubber=None, finger=None, pressed=False,
                eraser=False, blink=None, fade=0.0, win=0.0)
    base.update(kw)
    return base


L1, L2, L3, L4 = frozenset("ca"), frozenset("cb"), frozenset("cd"), frozenset("be")
REST = (215, 300)  # where the finger hovers between actions
steps = []
add = lambda d, f: steps.append((d, f))

add(0.25, lambda t: S(fade=1 - t))                                   # fade in from last loop
add(0.6, lambda t: S())
add(0.5, lambda t: S(finger=lerp(REST, P["c"], ease(t))))             # move to centre
add(0.15, lambda t: S(finger=P["c"], pressed=True, selected="c"))
add(0.7, lambda t: S(finger=lerp(P["c"], P["a"], ease(t)), pressed=True, selected="c",
                     rubber=lerp(P["c"], P["a"], ease(t))))           # drag to A
add(0.7, lambda t: S(lines={L1}, finger=P["a"]))                      # A lights yellow
add(0.45, lambda t: S(lines={L1}, finger=lerp(P["a"], P["c"], ease(t))))
add(0.15, lambda t: S(lines={L1}, finger=P["c"], pressed=True, selected="c"))
add(0.7, lambda t: S(lines={L1}, finger=lerp(P["c"], P["b"], ease(t)), pressed=True, selected="c",
                     rubber=lerp(P["c"], P["b"], ease(t))))           # drag to B (wrong)
add(1.1, lambda t: S(lines={L1, L2}, finger=P["b"]))                  # C and B go red
add(0.6, lambda t: S(lines={L1, L2}, finger=lerp(P["b"], ERASER, ease(t))))
add(0.15, lambda t: S(lines={L1, L2}, finger=ERASER, pressed=True, eraser=True))
add(0.3, lambda t: S(lines={L1, L2}, finger=ERASER, eraser=True))
add(0.6, lambda t: S(lines={L1, L2}, finger=lerp(ERASER, mid("c", "b"), ease(t)), eraser=True))
add(0.35, lambda t: S(lines={L1, L2}, finger=mid("c", "b"), pressed=True, eraser=True,
                      blink=(L2, 0.2 if 0.25 < t < 0.75 else 1.0)))    # tap line: blink…
add(0.6, lambda t: S(lines={L1}, finger=mid("c", "b"), eraser=True))  # …gone, C and B neutral
add(0.5, lambda t: S(lines={L1}, finger=lerp(mid("c", "b"), P["c"], ease(t)), eraser=True))
add(0.2, lambda t: S(lines={L1}, finger=P["c"], pressed=True, selected="c"))  # tap dot: eraser off
add(0.7, lambda t: S(lines={L1}, finger=lerp(P["c"], P["d"], ease(t)), pressed=True, selected="c",
                     rubber=lerp(P["c"], P["d"], ease(t))))           # drag to D (right)
add(0.6, lambda t: S(lines={L1, L3}, finger=lerp(P["d"], P["b"], ease(t))))
add(0.15, lambda t: S(lines={L1, L3}, finger=P["b"], pressed=True, selected="b"))
add(0.7, lambda t: S(lines={L1, L3}, finger=lerp(P["b"], P["e"], ease(t)), pressed=True, selected="b",
                     rubber=lerp(P["b"], P["e"], ease(t))))           # drag B to E: solved
add(0.5, lambda t: S(lines={L1, L3, L4}, finger=lerp(P["e"], REST, ease(t)), win=ease(t / 0.6)))
add(1.8, lambda t: S(lines={L1, L3, L4}, win=1.0))
add(0.3, lambda t: S(lines={L1, L3, L4}, win=1.0, fade=t))                        # fade out, loop


def dot_status(d, lines):
    mine = [l for l in lines if d in l]
    if len(mine) < DEG[d]:
        return "neutral", DEG[d] - len(mine)
    return ("ok" if all(l in SOLUTION for l in mine) else "bad"), 0


def svg(s):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{OUT_PX}" height="{OUT_PX}" '
           f'viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    # faint background stars
    for x, y, r in [(30, 30, 1.2), (120, 40, 0.9), (370, 140, 1.1), (40, 320, 1.0), (360, 330, 0.8),
                    (150, 110, 0.7), (250, 290, 0.8), (330, 20, 0.9), (110, 290, 0.7)]:
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{FG}" opacity="0.35"/>')
    win = s["win"]
    if win:
        out.append('<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
                   '<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/>'
                   '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    out.append(f'<g filter="url(#glow)" opacity="{0.4 + 0.6 * win}">' if win else '<g>')
    for l in s["lines"]:
        a, b = sorted(l)
        op = s["blink"][1] if s["blink"] and s["blink"][0] == l else 1
        out.append(f'<line x1="{P[a][0]}" y1="{P[a][1]}" x2="{P[b][0]}" y2="{P[b][1]}" stroke="{LINE}" '
                   f'stroke-width="5" stroke-linecap="round" opacity="{op}"/>'.replace(f'stroke="{LINE}"', f'stroke="{OK if win else LINE}"'))
    if s["rubber"]:
        c = P[s["selected"]]
        x, y = s["rubber"]
        out.append(f'<line x1="{c[0]}" y1="{c[1]}" x2="{x}" y2="{y}" stroke="{FG}" stroke-width="3.5" '
                   f'stroke-dasharray="8 8" stroke-linecap="round" opacity="0.7"/>')
    for d, (x, y) in P.items():
        st, left = dot_status(d, s["lines"])
        fill = {"neutral": DOT, "ok": OK, "bad": BAD}[st]
        stroke = FG if s["selected"] == d else "none"
        glow = f'<circle cx="{x}" cy="{y}" r="{R + 7}" fill="{fill}" opacity="0.18"/>' if st != "neutral" else ""
        out.append(f'{glow}<circle cx="{x}" cy="{y}" r="{R}" fill="{fill}" stroke="{stroke}" stroke-width="5"/>')
        if left:
            out.append(f'<text x="{x}" y="{y + 10}" text-anchor="middle" font-family="DejaVu Sans" '
                       f'font-weight="bold" font-size="28" fill="{BG}">{left}</text>')
    out.append("</g>")
    # eraser button (pill, like .controls button; filled when aria-pressed)
    ex, ey = ERASER
    on = s["eraser"]
    out.append(f'<rect x="{ex - 30}" y="{ey - 23}" width="60" height="46" rx="23" '
               f'fill="{FG if on else "none"}" stroke="{FG if on else MUTED}" stroke-width="1.5"/>')
    out.append(f'<g transform="translate({ex - 13},{ey - 13}) scale(1.08)"><path d="{ERASER_ICON}" '
               f'fill="{BG if on else FG}"/></g>')
    # finger / touch indicator
    if s["finger"]:
        x, y = s["finger"]
        r = 15 if s["pressed"] else 19
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{FG}" opacity="{0.45 if s["pressed"] else 0.28}" '
                   f'stroke="{FG}" stroke-width="2" stroke-opacity="0.8"/>')
    if s["fade"]:
        out.append(f'<rect width="{W}" height="{H}" fill="{BG}" opacity="{s["fade"]}"/>')
    out.append("</svg>")
    return "".join(out)


frames = []
STILL_FRAME = 140  # ~5.6 s in: both dots red, finger heading for the eraser
for dur, f in steps:
    n = max(1, round(dur * FPS))
    for i in range(n):
        png = cairosvg.svg2png(bytestring=svg(f(i / max(1, n - 1))).encode())
        frames.append(Image.open(io.BytesIO(png)).convert("RGB"))

# shared palette from a few representative frames, then merge identical consecutive frames
ref = Image.new("RGB", (OUT_PX, OUT_PX * 4))
for k, idx in enumerate([len(frames) // 5, len(frames) // 3, len(frames) // 2, -30]):
    ref.paste(frames[idx], (0, OUT_PX * k))
pal = ref.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
merged, durs = [], []
for im in q:
    if merged and im.tobytes() == merged[-1].tobytes():
        durs[-1] += 1000 // FPS
    else:
        merged.append(im); durs.append(1000 // FPS)
OUT_DIR.mkdir(exist_ok=True)
merged[0].save(OUT_DIR / "tutorial.gif", save_all=True,
               append_images=merged[1:], duration=durs, loop=0, optimize=True, disposal=1)
# still for prefers-reduced-motion: the "wrong line -> red" moment, eraser about to be used
frames[STILL_FRAME].save(OUT_DIR / "tutorial-still.png", optimize=True)
print(len(frames), "frames ->", len(merged), "unique; total", sum(durs) / 1000, "s")
