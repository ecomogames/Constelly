"""Constelly puzzle kit: list, check, preview, and batch-apply drawings and line colours.

    python tools/puzzle_kit.py order [FROM-TO]          # status table: date, dots, redrawn, colours, clue
    python tools/puzzle_kit.py check [IDS|N-M]          # rule + quality check of live puzzles
    python tools/puzzle_kit.py preview IDS|N-M [--big]  # PNG contact sheet ("Claude outputs/previews/")
    python tools/puzzle_kit.py draft FILE [IDS] [--big] # check + preview a draft file (see below)
    python tools/puzzle_kit.py apply FILE [--redrawn] [--at N] [--force]
                                                        # write a draft into author_puzzles.py

IDS are puzzle ids ("fox bear") and/or puzzle numbers / ranges ("11-20", "#12").
--big renders each puzzle large, with dot names + degrees, next to the player's view (dots only):
use it to pick edges for colouring. PNGs go to "Claude outputs/previews/", which is gitignored —
never commit previews anywhere else: they show the answers and the whole repo is public.
Rendering needs cairosvg (pip install cairosvg); without it the kit writes .svg instead.

Draft file (plain Python, evaluated with P, COLOR and math available):

    P("fox", "Fox", "animal",
      "a 0 0; b 20 5; c 40 0; d 20 30",      # named points "name x y", free grid, y points DOWN
      ["a b c", "b d"],                      # paths: "a b c" = lines a-b and b-c
      clue="Quick, brown, and jumps over lazy dogs",
      colors={"orange": ["a b c"], "white": ["b d"]})   # optional; unlisted lines are yellow

    COLOR("drum", white=["h0 h1 h2"], red=["b0 b1"])     # recolour an EXISTING puzzle, shape untouched;
                                                         # replaces all its colours (unlisted = yellow)

apply: a P() for an existing id replaces that puzzle's drawing/title/clue/colours; a new id is
inserted into ORDER (at puzzle number --at N, default: the end). --redrawn adds the P() ids to
REDRAWN. Puzzles already played (number <= today's) are refused unless --force. Afterwards it
regenerates puzzles/puzzles.json and runs the validator. Coordinates are stored like the editor
stores them (fitted board x100), so re-saving is stable.
"""
import importlib.util
import io
import json
import math
import re
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "Claude outputs" / "previews"

_spec = importlib.util.spec_from_file_location("editor", TOOLS / "editor.py")
ed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ed)

BOARD_H = 4 / 3
BOX = (0.08, 0.92, 0.08, BOARD_H - 0.08)
MIN_DOT_SPACING = 0.11     # keep in sync with tools/validate_puzzles.py
MIN_LINE_CLEARANCE = 0.05
MAX_CHAIN, MIN_JUNCTION = 5, 25   # tools/puzzle_quality.py
DOTS_AIM = (18, 26)
CLUE_MAX, CLUE_AIM = 80, 40  # schema max / house style


def key(a, b):
    return f"{a}|{b}" if a < b else f"{b}|{a}"


def path_pairs(paths):
    for p in paths:
        ids = p.split()
        yield from zip(ids, ids[1:])


# ---- loading ---------------------------------------------------------------------------------

def live():
    """The live puzzles: [(number, puzzle-dict with fitted pts, colours, flags)] in ORDER."""
    mod = ed.load_module()
    by_id = {p["id"]: p for p in mod["PUZZLES"]}
    redrawn = set(mod.get("REDRAWN", []))
    out = []
    for i, pid in enumerate(mod["ORDER"]):
        f = mod["fit"](by_id[pid])
        out.append(dict(number=i + 1, id=pid, title=f["title"], category=f["category"],
                        clue=f.get("clue", ""), colors=f.get("colors", {}),
                        pts={d["id"]: (d["x"], d["y"]) for d in f["dots"]}, edges=f["edges"],
                        redrawn=pid in redrawn, fitted=True))
    return out


def load_draft(path):
    items, recolors = [], []

    def P(pid, title, cat, pts, paths, clue="", colors=None):
        d = {}
        for item in pts.split(";"):
            item = item.strip()
            if item:
                n, x, y = item.split()
                if n in d:
                    raise ValueError(f"{pid}: point {n} defined twice")
                d[n] = (float(x), float(y))
        edges, seen = [], set()
        for a, b in path_pairs(paths):
            if a not in d or b not in d:
                raise ValueError(f"{pid}: path uses unknown point {a if a not in d else b}")
            if a == b or frozenset((a, b)) in seen:
                raise ValueError(f"{pid}: self-loop or duplicate line {a}-{b}")
            seen.add(frozenset((a, b)))
            edges.append([a, b])
        items.append(dict(id=pid, title=title, category=cat, clue=clue, pts=d, edges=edges,
                          colors=colors_to_keys(pid, colors or {}, seen), fitted=False))

    def COLOR(pid, **colors):
        recolors.append((pid, colors))

    ns = {"P": P, "COLOR": COLOR, "math": math, "__file__": str(path)}
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), ns)
    return items, recolors


def colors_to_keys(pid, colors, edge_set):
    palette = ed.load_module().get("PALETTE", {})
    out = {}
    for color, paths in colors.items():
        if color not in palette:
            raise ValueError(f"{pid}: unknown colour {color!r} (palette: {', '.join(palette)})")
        for a, b in path_pairs(paths):
            if frozenset((a, b)) not in edge_set:
                raise ValueError(f"{pid}: colour on {a}-{b}, which isn't a line")
            k = key(a, b)
            if k in out:
                raise ValueError(f"{pid}: line {a}-{b} coloured twice")
            if color != "yellow":
                out[k] = color
    return out


# ---- checks ----------------------------------------------------------------------------------

def fit(pts):
    xs, ys = [v[0] for v in pts.values()], [v[1] for v in pts.values()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    x0, x1, y0, y1 = BOX
    s = min((x1 - x0) / w if w else 1e9, (y1 - y0) / h if h else 1e9)
    ox, oy = 0.5 - s * (min(xs) + max(xs)) / 2, BOARD_H / 2 - s * (min(ys) + max(ys)) / 2
    return {k: (round(ox + s * x, 3), round(oy + s * y, 3)) for k, (x, y) in pts.items()}


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0 if l2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def analyse(p):
    F = p["pts"] if p.get("fitted") else fit(p["pts"])
    deg = {k: 0 for k in F}
    adj = {k: [] for k in F}
    for a, b in p["edges"]:
        deg[a] += 1; deg[b] += 1
        adj[a].append(b); adj[b].append(a)
    errors, warns, bad = [], [], set()
    if p["category"] not in ("animal", "plant", "object"):
        errors.append("category must be animal, plant or object")
    for k, v in deg.items():
        if not v:
            errors.append(f"dot {k} has no lines"); bad.add(k)
    names, min_sp = list(F), 9
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = math.dist(F[a], F[b]); min_sp = min(min_sp, d)
            if d < MIN_DOT_SPACING:
                errors.append(f"{a}-{b} too close: {d:.3f} < {MIN_DOT_SPACING}"); bad.update((a, b))
    for a, b in p["edges"]:
        for k in names:
            if k not in (a, b) and seg_dist(F[k], F[a], F[b]) < MIN_LINE_CLEARANCE:
                errors.append(f"{k} is {seg_dist(F[k], F[a], F[b]):.3f} from line {a}-{b}"); bad.add(k)
    best, seen = 0, set()
    for start in deg:
        if deg[start] != 2 or start in seen:
            continue
        run, here = 1, {start}; seen.add(start)
        for first in adj[start]:
            prev, cur = start, first
            while deg.get(cur) == 2 and cur not in here:
                seen.add(cur); here.add(cur); run += 1
                nxt = [x for x in adj[cur] if x != prev]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
        best = max(best, run)
    n = len(deg)
    junc = round(100 * sum(v >= 3 for v in deg.values()) / n) if n else 0
    if best > MAX_CHAIN:
        errors.append(f"run of {best} degree-2 dots (max {MAX_CHAIN})")
    if junc < MIN_JUNCTION:
        errors.append(f"only {junc}% of dots have 3+ lines (min {MIN_JUNCTION}%)")
    if not DOTS_AIM[0] <= n <= DOTS_AIM[1]:
        warns.append(f"{n} dots (aim {DOTS_AIM[0]}-{DOTS_AIM[1]})")
    clue = (p.get("clue") or "").strip()
    if not clue:
        errors.append("no clue")
    elif len(clue) > CLUE_MAX:
        errors.append(f"clue is {len(clue)} chars (max {CLUE_MAX})")
    if clue:
        if len(clue) > CLUE_AIM:
            warns.append(f"clue is {len(clue)} chars (aim <= {CLUE_AIM})")
        words = {w for w in re.findall(r"[a-z]+", f"{p['title']} {p['id']}".lower()) if len(w) > 2}
        hit = sorted(w for w in words if re.search(rf"\b{w}", clue.lower()))
        if hit:
            errors.append(f"clue gives it away: {', '.join(hit)}")
    if not p.get("colors"):
        warns.append("no line colours (all yellow)")
    return dict(F=F, deg=deg, errors=errors, warns=warns, bad=bad, n=n, junc=junc, chain=best, min_sp=min_sp)


def report(ps):
    failed = 0
    for p in ps:
        a = analyse(p)
        failed += bool(a["errors"])
        num = f"#{p['number']:<3} " if p.get("number") else ""
        print(f"{'FAIL' if a['errors'] else 'ok  '} {num}{p['id']:13} {a['n']:2} dots  junc {a['junc']:3}%  "
              f"chain {a['chain']}  min {a['min_sp']:.3f}  colours {len(p.get('colors') or {}):2}  clue: {p.get('clue','')}")
        for e in a["errors"]:
            print("       ERROR", e)
        for w in a["warns"]:
            print("       warn ", w)
    print(f"\n{len(ps) - failed}/{len(ps)} pass")
    return failed


# ---- rendering -------------------------------------------------------------------------------

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tile(p, a, x0, y0, W, player=False, palette=None):
    s, H = W, W * BOARD_H
    F, deg, r = a["F"], a["deg"], 0.028 * W
    big = W >= 500
    out = [f'<rect x="{x0}" y="{y0}" width="{W}" height="{H:.1f}" fill="#0b1026"/>']
    if not player:
        for u, v in p["edges"]:
            col = palette.get((p.get("colors") or {}).get(key(u, v), "yellow"), "#ffd84a")
            (ax, ay), (bx, by) = F[u], F[v]
            out.append(f'<line x1="{x0 + ax * s:.1f}" y1="{y0 + ay * s:.1f}" x2="{x0 + bx * s:.1f}" '
                       f'y2="{y0 + by * s:.1f}" stroke="{col}" stroke-width="{0.012 * s:.1f}" stroke-linecap="round"/>')
    for k, (x, y) in F.items():
        fill = "#ff5a5a" if k in a["bad"] else ("#c9d1ff" if player else "#ffd84a")
        out.append(f'<circle cx="{x0 + x * s:.1f}" cy="{y0 + y * s:.1f}" r="{r:.1f}" fill="{fill}"/>')
        if player or big:
            out.append(f'<text x="{x0 + x * s:.1f}" y="{y0 + y * s + r * 0.38:.1f}" font-size="{r * 1.1:.1f}" '
                       f'font-weight="700" text-anchor="middle" fill="#0b1026" font-family="DejaVu Sans, sans-serif">{deg[k]}</text>')
        if big and not player:
            out.append(f'<text x="{x0 + x * s + r * 1.1:.1f}" y="{y0 + y * s - r * 0.9:.1f}" font-size="{r * 0.75:.1f}" '
                       f'fill="#8a93c4" font-family="DejaVu Sans Mono, monospace">{esc(k)}</text>')
    cy = y0 + H + 18
    num = f"#{p['number']} " if p.get("number") else ""
    out.append(f'<text x="{x0}" y="{cy}" font-size="14" font-weight="700" fill="{"#ff5a5a" if a["errors"] else "#6fdc8c"}" '
               f'font-family="DejaVu Sans, sans-serif">{esc(num + p["id"] + " · " + p["title"])}</text>')
    out.append(f'<text x="{x0}" y="{cy + 17}" font-size="12" fill="#c9d1ff" font-family="DejaVu Sans, sans-serif">'
               f'{a["n"]} dots · junc {a["junc"]}% · chain {a["chain"]}</text>')
    out.append(f'<text x="{x0}" y="{cy + 34}" font-size="12" font-style="italic" fill="#e8ecff" '
               f'font-family="DejaVu Sans, sans-serif">“{esc((p.get("clue") or "")[:70])}”</text>')
    return "".join(out)


def render(ps, name, big=False):
    palette = ed.load_module().get("PALETTE", {})
    W, gap, cap = (560, 28, 60) if big else (260, 20, 60)
    tiles = [(p, analyse(p), pl) for p in ps for pl in ((False, True) if big else (False,))]
    cols = 2 if big else min(5, max(1, len(tiles)))
    H = W * BOARD_H
    rows = math.ceil(len(tiles) / cols)
    TW, TH = cols * (W + gap) + gap, rows * (H + cap + gap) + gap
    body = [f'<rect width="{TW}" height="{TH:.0f}" fill="#1a1f33"/>']
    for i, (p, a, pl) in enumerate(tiles):
        body.append(tile(p, a, gap + (i % cols) * (W + gap), gap + (i // cols) * (H + cap + gap), W, pl, palette))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{TW}" height="{TH:.0f}">{"".join(body)}</svg>'
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg
        path = OUT / f"{name}.png"
        path.write_bytes(cairosvg.svg2png(bytestring=svg.encode()))
    except Exception as e:  # no cairosvg / no libcairo
        path = OUT / f"{name}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"(cairosvg unavailable: {type(e).__name__}; wrote SVG instead)")
    print(f"preview: {path}")


# ---- selection -------------------------------------------------------------------------------

def select(ps, args):
    if not args:
        return ps
    by_num = {p["number"]: p for p in ps}
    chosen = []
    for a in args:
        a = a.lstrip("#")
        m = re.fullmatch(r"(\d+)-(\d+)", a)
        if m:
            chosen += [by_num[n] for n in range(int(m[1]), int(m[2]) + 1) if n in by_num]
        elif a.isdigit():
            chosen.append(by_num[int(a)])
        else:
            chosen += [p for p in ps if p["id"] == a] or sys.exit(f"no puzzle {a!r}")
    return chosen


# ---- apply -----------------------------------------------------------------------------------

def apply(path, redrawn=False, at=None, force=False):
    items, recolors = load_draft(path)
    for p in items:
        a = analyse(p)
        if a["errors"]:
            sys.exit(f"{p['id']} fails: {'; '.join(a['errors'][:4])} — fix it in the draft first")
    raw = ed.AUTHOR.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    src = raw.replace("\r\n", "\n")
    mod = ed.load_module(src)
    order = list(mod["ORDER"])
    palette = list(mod.get("PALETTE", {}))
    by_id = {p["id"]: p for p in mod["PUZZLES"]}
    today = ed.today_index()
    played = lambda pid: pid in order and order.index(pid) <= today
    blocks, spans = ed.top_level(__import__("ast").parse(src))
    edits, new_ids = [], []

    def block_for(pid, title, cat, fitted_pts, edges, clue, colors):
        pts = [(n, (round(x * 100, 1), round(y * 100, 1))) for n, (x, y) in fitted_pts.items()]
        names = [n for n, _ in pts]
        return ed.format_block(pid, title, cat, pts, ed.edges_to_paths(names, edges), clue,
                               ed.format_colors(names, colors, palette)).split("\n")

    for p in items:
        if played(p["id"]) and not force:
            sys.exit(f"{p['id']} has already been played (#{order.index(p['id']) + 1}) — use --force only if you mean it")
        new = block_for(p["id"], p["title"], p["category"], fit(p["pts"]), p["edges"], p["clue"], p["colors"])
        if p["id"] in blocks:
            edits.append((blocks[p["id"]], new))
        else:
            new_ids.append((p["id"], new))
    for pid, colors in recolors:
        if pid not in by_id:
            sys.exit(f"COLOR: no puzzle {pid!r}")
        old = by_id[pid]
        f = mod["fit"](old)
        cols = colors_to_keys(pid, colors, {frozenset(e) for e in old["edges"]})
        edits.append((blocks[pid], block_for(pid, old["title"], old["category"],
                                             {d["id"]: (d["x"], d["y"]) for d in f["dots"]},
                                             old["edges"], old.get("clue", ""), cols)))
    if new_ids:
        pos = len(order) if at is None else at - 1
        if pos <= today and not force:
            sys.exit(f"--at {at} is on or before today's puzzle (#{today + 1})")
        for i, (pid, _) in enumerate(new_ids):
            order.insert(pos + i, pid)
        s, e = spans["ORDER"]
        extra = []
        for _, b in new_ids:
            extra += b + [""]
        edits.append(((s, e), extra + ed.format_list("ORDER", order).split("\n")))
    if redrawn and "REDRAWN" in spans:
        red = list(mod.get("REDRAWN", []))
        red += [p["id"] for p in items if p["id"] not in red]
        edits.append((spans["REDRAWN"], ed.format_list("REDRAWN", red).split("\n")))
    lines = src.split("\n")
    for (s, e), new in sorted(edits, key=lambda x: -x[0][0]):
        lines[s - 1:e] = new
    new_src = "\n".join(lines)
    ed.load_module(new_src)  # must still run (P() asserts, ORDER consistent)
    ed.AUTHOR.write_bytes((new_src.replace("\n", "\r\n") if crlf else new_src).encode("utf-8"))
    print(f"applied: {len(items)} drawing(s) ({len(new_ids)} new), {len(recolors)} recolour(s)")
    for tool in ("author_puzzles.py", "validate_puzzles.py"):
        r = subprocess.run([sys.executable, str(TOOLS / tool)], cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()
        print(f"{tool}: {'OK' if r.returncode == 0 else 'FAILED'}  {tail[-1] if tail else ''}")
        if r.returncode:
            print("\n".join(tail[-15:]))
            sys.exit(1)


# ---- main ------------------------------------------------------------------------------------

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    big = "--big" in args
    args = [a for a in args if a != "--big"]
    if cmd == "order":
        ps = select(live(), args)
        today = ed.today_index()
        print(f"{'#':>4} {'date':10} {'id':13} {'title':18} {'cat':7} dots redrawn colours clue")
        for p in ps:
            d = (ed.LAUNCH + timedelta(days=p["number"] - 1)).isoformat()
            mark = "<- today" if p["number"] - 1 == today else ("played" if p["number"] - 1 < today else "")
            print(f"{p['number']:>4} {d} {p['id']:13} {p['title'][:18]:18} {p['category']:7} {len(p['pts']):4} "
                  f"{'yes' if p['redrawn'] else 'OLD':7} {len(p['colors']):7} {'yes' if p['clue'] else '-':4} {mark}")
        return 0
    if cmd == "check":
        return 1 if report(select(live(), args)) else 0
    if cmd == "preview":
        ps = select(live(), args)
        render(ps, ("big-" if big else "") + ("-".join(a.lstrip("#") for a in args)[:60] or "all"), big)
        return 0
    if cmd == "draft":
        items, recolors = load_draft(args[0])
        only = args[1:]
        ps = [p for p in items if not only or p["id"] in only]
        lv = {p["id"]: p for p in live()}
        for pid, colors in recolors:
            if (not only or pid in only) and pid in lv:
                p = dict(lv[pid]); p["colors"] = colors_to_keys(pid, colors, {frozenset(e) for e in p["edges"]})
                ps.append(p)
        failed = report(ps)
        render(ps, ("big-" if big else "") + Path(args[0]).stem + ("-" + "-".join(only) if only else ""), big)
        return 1 if failed else 0
    if cmd == "apply":
        at = next((int(args[i + 1]) for i, a in enumerate(args) if a == "--at"), None)
        apply(args[0], redrawn="--redrawn" in args, at=at, force="--force" in args)
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as e:  # bad draft: unknown point/colour, duplicate line, ...
        sys.exit(f"error: {e}")
