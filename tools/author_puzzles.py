"""Source of truth for the puzzles in puzzles/puzzles.json.

Each puzzle is drawn on a free grid (any units, y pointing down) as named points plus
paths ("a b c a" = edges a-b, b-c, c-a). Degrees are derived from the edges, and each drawing
is scaled uniformly and centred onto the 3:4 board inside an 0.08 margin.

    python tools/author_puzzles.py          # rewrites puzzles/puzzles.json
    python tools/validate_puzzles.py        # always run afterwards
    python tools/puzzle_quality.py          # flags dull puzzles (long degree-2 chains)
    python tools/preview_puzzles.py         # optional: contact sheet PNG (needs matplotlib)

Each puzzle may have a clue= : a short line shown to the player while solving. It must hint at
the picture without naming it (e.g. hot-air balloon: "I can see my house from here...").

Lines can have colours for the solved picture: colors={"green": ["a b c"], "red": ["d e"]} uses
the same path syntax (each step must be a line of the drawing). Unlisted lines are yellow.
The colours only show once the puzzle is solved, so they never give away which lines are right.
Names: PALETTE below (hex values are the ones css/style.css uses).

Publish order is ORDER at the bottom (index 0 = launch day). Don't reorder puzzles that have
already been played: the day index picks puzzles by position. REDRAWN lists the puzzles whose
drawing has been redone to the new standard (18-26 dots, richer detail, a clue); the rest are
old drawings still waiting for a redraw and sit at the end of ORDER.

Easiest way to edit: python tools/editor.py (visual editor, rewrites this file).
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOARD_H = 4 / 3
BOX = (0.08, 0.92, 0.08, BOARD_H - 0.08)  # x0, x1, y0, y1 usable area
PUZZLES = []

# Line colours (keep in sync with --c-* in css/style.css and the enum in puzzles/schema.json).
PALETTE = {
    "yellow": "#ffd84a", "orange": "#ff9a3c", "red": "#ff4d5e", "pink": "#ff6ec7",
    "purple": "#b78cff", "blue": "#4aa8ff", "cyan": "#38e1f0", "green": "#4be37a",
    "white": "#f2f4ff", "brown": "#c8874f",
}


def edge_key(a, b):  # same as edgeKey() in js/game.js
    return f"{a}|{b}" if a < b else f"{b}|{a}"


def P(pid, title, cat, pts, paths, clue="", colors=None):
    if isinstance(pts, str):
        d = {}
        for item in pts.split(";"):
            item = item.strip()
            if not item:
                continue
            n, x, y = item.split()
            d[n] = (float(x), float(y))
        pts = d
    edges, seen = [], set()
    for path in paths:
        ids = path.split()
        for a, b in zip(ids, ids[1:]):
            k = frozenset((a, b))
            assert a in pts and b in pts, (pid, a, b)
            assert k not in seen, (pid, "dup edge", a, b)
            seen.add(k)
            edges.append([a, b])
    line_colors = {}
    for color, cpaths in (colors or {}).items():
        assert color in PALETTE, (pid, "unknown colour", color)
        for path in cpaths:
            ids = path.split()
            for a, b in zip(ids, ids[1:]):
                k = edge_key(a, b)
                assert frozenset((a, b)) in seen, (pid, "colour on a line that isn't drawn", a, b)
                assert k not in line_colors, (pid, "line coloured twice", a, b)
                if color != "yellow":
                    line_colors[k] = color
    PUZZLES.append(dict(id=pid, title=title, category=cat, pts=pts, edges=edges, clue=clue,
                        colors=line_colors))


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


P("starfish", "Starfish", "animal",
  "t0 52.1 25.8; v0 64.4 48.9; t1 92 59.3; v1 73.9 78.1; t2 72.5 107.6; v2 49.1 96.1;"
  "t3 20.6 103.9; v3 24.2 78.1; t4 8 53.4; v4 33.7 48.9; e1 42.7 57.3; e2 42.7 69.2;"
  "e3 55.4 57.3; e4 55.4 69.2; m1 38 80.3; m2 49.1 84.2; m3 60.1 80.3",
  ["e1 e2", "e3 e4", "m1 m2 m3", "t0 v0 t1 v1 t2 v2 t3 v3 t4 v4 t0", "v0 v1 v2 v3 v4 v0"],
  clue="No, this is Patrick!",
  colors={"red": ["m1 m2 m3", "v0 v1 v2 v3 v4 v0"], "pink": ["t0 v0 t1 v1 t2 v2 t3 v3 t4 v4 t0"],
    "white": ["e1 e2", "e3 e4"]})

P("barn", "Barn", "object",
  "pk 50 22.7; rbL 19 43.9; evL 9.3 65; bsL 9.3 125.3; dtL 28.8 81.3; dbL 28.8 125.3;"
  "dtm 50 81.3; dbm 50 125.3; wtL 40.2 40.6; wbL 40.2 56.9; wv 50 8; rbR 81 43.9; evR 90.7 65;"
  "bsR 90.7 125.3; dtR 71.2 81.3; dbR 71.2 125.3; wtR 59.8 40.6; wbR 59.8 56.9",
  ["pk rbL evL bsL dbL dbm dbR bsR evR rbR pk wv", "evL evR",
   "dtL dtm dtR dbR dtm dbm dtL dbL dtm", "dbm dtR", "wtL wtR wbR wbL wtL wbR", "wbL wtR"],
  clue="Old MacDonald's headquarters",
  colors={"red": ["dbL bsL evL rbL pk rbR evR bsR dbR"],
    "white": ["evL evR", "dtL dtm dtR dbR dbm dbL dtL dbm dtm dbR", "dbL dtm", "dbm dtR", "wtL wtR wbR wbL wtL wbR", "wbL wtR"]})

P("drum", "Drum", "object",
  "h0 92 66.2; h1 79.7 75.9; h2 50 79.9; h3 20.3 75.9; h4 8 66.2; h5 20.3 56.5; h6 50 52.5;"
  "h7 79.7 56.5; b0 92 106.4; b1 79.7 116.1; b2 50 120.1; b3 20.3 116.1; b4 8 106.4;"
  "s1a 20.8 13.3; s1b 79.2 44.3; s2a 79.2 13.3; s2b 20.8 44.3; sx 50 28.8",
  ["b0 h0 h1 h2 h3 h4 h5 h6 h7 h0 b1 b0 h1 b2 b1 h2 b3 b2 h3 b4 b3 h4 b4", "s1a sx s1b",
   "s2a sx s2b"],
  clue="Ba-dum-tss!",
  colors={"red": ["h0 b0 b1 b2 b3 b4 h4"], "white": ["h0 h1 h2 h3 h4 h5 h6 h7 h0"],
    "brown": ["s1a sx s1b", "s2a sx s2b"]})

P("pine", "Pine tree", "plant",
  "ap 50 8.7; o1L 26.5 40.6; o1R 73.5 40.6; i1L 38.2 40.6; i1R 61.8 40.6; c1 50 40.6;"
  "o2L 16.4 72.5; o2R 83.6 72.5; i2L 31.5 72.5; i2R 68.5 72.5; c2 50 72.5; o3L 8 106.1;"
  "o3R 92 106.1; tkL 38.2 106.1; tkR 61.8 106.1; c3 50 106.1; tbL 38.2 124.6; tbR 61.8 124.6",
  ["ap o1L i1L c1 i1R o1R ap c1 c2 c3 tkL o3L i2L o2L i1L", "i1R o2R i2R c2 i2L",
   "i2R o3R tkR c3", "tkL tbL tbR tkR"],
  clue="Evergreen and never needs a haircut",
  colors={"green": ["i1L o1L ap o1R i1R c1 i1L o2L i2L c2 i2R o2R i1R", "i2L o3L tkL c3 tkR o3R i2R"],
    "brown": ["ap c1 c2 c3", "tkL tbL tbR tkR"]})

P("teapot", "Teapot", "object",
  "kn 51.5 32.9; dl 42.5 42.7; dr 60.5 42.7; rl 36.5 52.4; rr 66.5 52.4; sl 27.5 62.9;"
  "sr 75.5 62.9; wl 24.5 77.9; wr 78.5 77.9; bl 29 91.4; br 74 91.4; fl 36.5 100.4;"
  "fr 66.5 100.4; st 8 46.4; sd 14 68.9; h1 87.5 61.4; h2 92 74.9; h3 86 86.9",
  ["dl rl rr dr kn dl dr", "rl sl wl bl fl fr br wr sr rr", "sl st sd wl wr", "sr h1 h2 h3 br"],
  clue="Short and stout",
  colors={"pink": ["wl wr"],
    "blue": ["rl sl wl bl fl fr br wr sr rr", "sl st sd wl", "sr h1 h2 h3 br"],
    "white": ["dl rl rr dr dl kn dr"]})

P("sled", "Sled", "object",
  "p0 12.3 74.3; p3 70.3 74.3; q3 70.3 87.3; q0 12.3 87.3; q1 26.8 87.3; q2 54.3 87.3;"
  "r0 8 98.9; r1 26.8 104.7; r2 54.3 104.7; r3 74.6 104.7; c1 86.2 98.9; c2 92 87.3;"
  "c3 86.2 75.7; x0 50 28.6; x1 60.6 34.8; x2 60.6 47.1; x3 50 53.3; x4 39.4 47.1; x5 39.4 34.8;"
  "xc 50 41",
  ["p3 p0 q0 q1 q2 q3 p3 c3 c2 c1 r3 r2 q2", "q1 r1 r0", "r1 r2", "x0 xc x1", "x2 xc x3",
   "x4 xc x5"],
  clue="Rosebud...",
  colors={"red": ["p3 c3 c2 c1 r3 r2 q2", "q1 r1 r0", "r1 r2"],
    "cyan": ["x0 xc x1", "x2 xc x3", "x4 xc x5"], "brown": ["p0 p3 q3 q2 q1 q0 p0"]})

P("fish", "Fish", "animal",
  "n 8 68.3; a1 16.4 53.2; a2 31.5 45.7; a3 48.3 44.8; a4 61.8 51.5; pt 73.5 61.6; b1 16.4 83.5;"
  "b2 31.5 90.2; b3 48.3 91.9; b4 61.8 85.1; pb 73.5 75.1; tu 92 44.8; tn 83.6 68.3; tl 92 91.9;"
  "df 55 29.7; pf 51.7 103.6; g 38.2 67.5; e1 24 61.6; e2 24 73.4; s1 54.2 68.3",
  ["a3 a2 a1 n b1 b2 b3 b4 pb tl tn tu pt a4 a3 s1 b3 pf b2 g a2 df a4", "pt pb", "e1 e2"],
  clue="Just keep swimming...",
  colors={"orange": ["a2 a1 n b1 b2 b3 b4 pb tl tn tu pt a4 a3 a2 df a4", "pt pb", "b2 pf b3"],
    "white": ["a2 g b2", "a3 s1 b3", "e1 e2"]})

P("balloon", "Hot-air balloon", "object",
  "t 50 8; l1 27.7 15.4; l2 14.6 34.1; l3 14.6 54.6; l4 27.7 75; nl 40.7 89.9; r1 72.3 15.4;"
  "r2 85.4 34.1; r3 85.4 54.6; r4 72.3 75; nr 59.3 89.9; gl1 34.2 33.1; gl2 35.1 54.6;"
  "gr1 65.8 33.1; gr2 64.9 54.6; btl 35.1 106.7; bt 50 106.7; btr 64.9 106.7; bbl 37.9 125.3;"
  "bb 50 125.3; bbr 62.1 125.3",
  ["l2 l1 t r1 r2 r3 r4 nr nl l4 l3 l2 gl1 t gr1 gr2 nr btr bt btl nl gl2 gl1 gr1 r2",
   "l3 gl2 gr2 r3", "btl bbl bb bbr btr", "bt bb"],
  clue="I can see my house from here...",
  colors={"red": ["nl l4 l3 l2 l1 t r1 r2 r3 r4 nr"], "blue": ["l2 gl1 gr1 r2", "l3 gl2 gr2 r3"],
    "white": ["nl btl", "nr btr"], "brown": ["bt btl bbl bb bbr btr bt bb"]})

P("bridge", "Bridge", "object",
  "D0 8 80.1; X1 21.4 80.1; X2 78.6 80.1; D6 92 80.1; T1 21.4 29.7; T2 78.6 29.7; H0 32.9 80.1;"
  "C0 32.9 55.1; H1 44.3 80.1; C1 44.3 66.8; H2 55.7 80.1; C2 55.7 66.8; H3 67.1 80.1;"
  "C3 67.1 55.1; w0 8 96.9; w1 21.4 103.6; w2 35.7 96.9; w3 50 103.6; w4 64.3 96.9;"
  "w5 78.6 103.6; w6 92 96.9",
  ["T1 X1 D0 T1 C0 C1 C2 C3 T2 X2 H3 H2 H1 H0 X1 w1 w0", "T2 D6 X2 w5 w4 w3 w2 w1", "H0 C0",
   "H1 C1", "H2 C2", "H3 C3", "w5 w6"],
  clue="Built for getting over things",
  colors={"red": ["X1 T1 D0 X1 w1", "X2 T2 D6 X2 w5", "T1 C0 C1 C2 C3 T2"],
    "blue": ["w0 w1 w2 w3 w4 w5 w6"],
    "white": ["X1 H0 H1 H2 H3 X2", "H0 C0", "H1 C1", "H2 C2", "H3 C3"]})

P("pineapple", "Pineapple", "plant",
  "tl 38.4 59.2; m 50 59.2; tr 61.6 59.2; ru 73.1 75.8; rl 73.1 108.8; br 61.6 125.3;"
  "bl 38.4 125.3; ll 26.9 108.8; lu 26.9 75.8; n 50 75.8; w 38.4 92.3; e 61.6 92.3; s 50 108.8;"
  "t1 20.3 37.7; v1 36.8 46; t2 31.8 17.9; v2 44.2 34.4; t3 50 8; v3 55.8 34.4; t4 68.2 17.9;"
  "v4 63.2 46; t5 79.7 37.7",
  ["ru tr m tl lu ll bl br rl ru e n tl t1 v1 t2 v2 t3 v3 t4 v4 t5 tr n w lu", "rl e s w ll",
   "br s bl", "v2 m v3"],
  clue="I belong on pizza. Fight me.",
  colors={"orange": ["tl lu ll bl br rl ru tr"],
    "green": ["v2 t2 v1 t1 tl m v2 t3 v3 t4 v4 t5 tr m v3"]})

P("fox", "Fox", "animal",
  "etl 20.5 8; eol 11.1 51.5; eml 24.4 44.5; eil 37.6 37.5; ckl 8 79.5; jl 28.2 96.6;"
  "mkl 32.9 74; eyal 29 58.5; eybl 40.7 63.9; nl 43 113.7; etr 79.5 8; eor 88.9 51.5;"
  "emr 75.6 44.5; eir 62.4 37.5; ckr 92 79.5; jr 71.8 96.6; mkr 67.1 74; eyar 71 58.5;"
  "eybr 59.3 63.9; nr 57 113.7; nb 50 125.3",
  ["etl eil eml eol etl eml", "eol ckl jl nl nr jr ckr eor etr eir eil",
   "ckl mkl nl nb nr mkr ckr", "eyal eybl", "etr emr eor", "emr eir", "eyar eybr"],
  clue="Quick, brown, and jumps over lazy dogs",
  colors={"orange": ["eol ckl jl nl nr jr ckr eor etr eir eil", "ckl mkl nl nb nr mkr ckr"],
    "white": ["eyal eybl", "eyar eybr"],
    "brown": ["etl eil eml eol etl eml", "etr emr eor", "emr eir"]})

P("ferriswheel", "Ferris wheel", "object",
  "hub 50 46.5; r0 50 8; r1 22.8 19.3; r2 11.5 46.5; r3 22.8 73.8; r4 50 85.1; r5 77.2 73.8;"
  "r6 88.5 46.5; r7 77.2 19.3; c0a 43.4 22; c0b 56.6 22; c3a 16.2 87.8; c3b 29.3 87.8;"
  "c4a 43.4 99.1; c4b 56.6 99.1; c5a 70.7 87.8; c5b 83.8 87.8; ftL 29 125.3; ftR 71 125.3;"
  "gL 11.5 125.3; gR 88.5 125.3",
  ["r0 r1 r2 r3 r4 r5 r6 r7 r0 hub r1", "r0 c0a c0b r0", "r2 hub r3 c3a c3b r3",
   "r4 hub r5 c5a c5b r5", "r4 c4a c4b r4", "r6 hub r7", "ftL hub ftR ftL gL", "ftR gR"],
  clue="Round and round we go",
  colors={"red": ["r0 r1 r2 r3 r4 r5 r6 r7 r0"],
    "white": ["r0 c0a c0b r0", "r3 c3a c3b r3", "r4 c4a c4b r4", "r5 c5a c5b r5"],
    "brown": ["ftL hub ftR ftL gL", "ftR gR"]})

P("gift", "Gift box", "object",
  "LtL 8 49.4; LbL 8 64.6; BtL 19.8 64.6; BbL 19.8 110.8; RtL 43.7 49.4; RmL 43.7 64.6;"
  "RbL 43.7 110.8; Kc 50 39.4; LuL 26.5 22.6; LoL 18.1 37.7; LiL 31.5 42.7; LtR 92 49.4;"
  "LbR 92 64.6; BtR 80.2 64.6; BbR 80.2 110.8; RtR 56.3 49.4; RmR 56.3 64.6; RbR 56.3 110.8;"
  "LuR 73.5 22.6; LoR 81.9 37.7; LiR 68.5 42.7",
  ["BtL RmL RmR BtR LbR LtR RtR RtL LtL LbL BtL BbL RbL RbR BbR BtR",
   "RbL RmL RtL Kc RtR RmR RbR", "Kc LuL LoL LiL Kc LuR LoR LiR Kc"],
  clue="It's the thought that counts",
  colors={"red": ["RbL RmL RtL Kc RtR RmR RbR", "Kc LuL LoL LiL Kc LuR LoR LiR Kc"],
    "blue": ["BtL RmL RmR BtR LbR LtR RtR RtL LtL LbL BtL BbL RbL RbR BbR BtR"]})

P("kite", "Kite", "object",
  "k0 50 8; kl 25.7 24.2; kr 74.3 24.2; kc 50 24.2; kb 50 54.9; t0 54 70.3; t0a 43.5 64.6;"
  "t0b 43.5 76; t0c 64.6 64.6; t0e 64.6 76; t1 46 89.7; t1a 35.4 84.1; t1b 35.4 95.4;"
  "t1c 56.5 84.1; t1e 56.5 95.4; t2 54 109.1; t2a 43.5 103.5; t2b 43.5 114.8; t2c 64.6 103.5;"
  "t2e 64.6 114.8; te 50 125.3",
  ["k0 kl kb kr k0 kc kl", "kr kc kb t0 t1 t2 te", "t0 t0a t0b t0 t0c t0e t0",
   "t1 t1a t1b t1 t1c t1e t1", "t2 t2a t2b t2 t2c t2e t2"],
  clue="Go fly one!",
  colors={"red": ["k0 kl kb kr k0 kc kl", "kr kc kb"], "pink": ["t1 t1a t1b t1 t1c t1e t1"],
    "green": ["t0 t0a t0b t0 t0c t0e t0", "t2 t2a t2b t2 t2c t2e t2"],
    "white": ["kb t0 t1 t2 te"]})

P("giraffe", "Giraffe", "animal",
  "sn 8 32.9; ht 20 20.9; hb 32 23.9; jw 21.5 40.4; os1 18.5 8.9; os2 32 11.9; nb1 41 43.4;"
  "nf1 29 55.4; wi 53 64.4; bk 68 68.9; rp 83 73.4; ch 38 77.9; bf 42.5 91.4; bf2 54.5 91.4;"
  "bl2 69.5 91.4; bl 81.5 88.4; sp 60.5 79.4; f1 38 124.4; f2 53 124.4; r1 71 124.4;"
  "r2 84.5 124.4; tl 92 94.4",
  ["ht sn jw nf1 ch bf bf2 bl2 bl rp bk wi nb1 hb ht os1", "hb os2", "nb1 nf1", "bk sp wi ch",
   "rp tl", "bf f1", "bl r2", "f2 bf2 sp bl2 r1"],
  clue="Head and neck above the rest",
  colors={"orange": ["ht sn jw nf1 ch bf bf2 bl2 bl rp bk wi nb1 hb ht os1"],
    "brown": ["hb os2", "nb1 nf1", "bk sp wi ch", "rp tl", "f2 bf2 sp bl2 r1"]})

P("lantern", "Lantern", "object",
  "h1 42.2 21.7; h2 50 8; h3 57.8 21.7; c1 40.2 35.4; c2 59.8 35.4; a1 14.8 54.9; a2 32.4 54.9;"
  "a3 67.6 54.9; a4 85.2 54.9; b1 14.8 109.7; b2 32.4 109.7; b3 67.6 109.7; b4 85.2 109.7;"
  "d1 20.7 125.3; d2 36.3 125.3; d3 63.7 125.3; d4 79.3 125.3; fl 50 68.6; fa 42.2 88.2;"
  "fb 50 98; fc 57.8 88.2",
  ["a1 a2 a3 a4 c2 h3 h2 h1 c1 c2 a3 b3 b2 a2 c1 a1 b1 b2 d2 d1 b1", "a4 b4 b3 d3 d2",
   "b4 d4 d3", "fl fa fb fc fl"],
  clue="Light the way, old-school style",
  colors={"orange": ["fl fa fb fc fl"],
    "red": ["a1 a2 a3 a4 c2 h3 h2 h1 c1 c2 a3 b3 b2 a2 c1 a1 b1 b2", "a4 b4 b3"]})

P("bamboo", "Bamboo", "plant",
  "a0l 29 23.9; a0r 41 23.9; a1l 29 46.4; a1r 41 46.4; a2l 29 68.9; a2r 41 68.9; a3l 29 91.4;"
  "a3r 41 91.4; a4l 29 113.9; a4r 41 113.9; b0l 54.5 43.4; b0r 66.5 43.4; b1l 54.5 66.7;"
  "b1r 66.5 66.7; b2l 54.5 89.9; b2r 66.5 89.9; b3l 54.5 113.9; b3r 66.5 113.9; l1s 54.5 26.9;"
  "l1t 77 19.4; l2s 83 61.4; l2t 92 44.9; l3s 15.5 62.9; l3t 8 83.9",
  ["a1l a0l a0r a1r a2r a3r a4r a4l a3l a2l a1l a1r l1s l1t a1r", "a2l a2r", "a2l l3s l3t a2l",
   "a3l a3r", "b1l b0l b0r b1r b2r b3r b3l b2l b1l b1r l2t l2s b1r", "b2l b2r"],
  clue="A panda's favourite snack bar",
  colors={"green": ["a1l a0l a0r a1r a2r a3r a4r a4l a3l a2l a1l a1r l1s l1t a1r", "b1l b0l b0r b1r b2r b3r b3l b2l b1l b1r l2t l2s b1r", "a2l l3s l3t a2l"],
    "brown": ["a2l a2r", "a3l a3r", "b2l b2r"]})

P("bench", "Park bench", "object",
  "p1 21.4 25.5; p2 50 25.5; p3 78.6 25.5; q1 21.4 38.9; q2 50 38.9; q3 78.6 38.9; r1 21.4 52.4;"
  "r2 50 52.4; r3 78.6 52.4; a1 9.7 55.7; a3 90.3 55.7; s0 8 67.5; s1 21.4 67.5; s2 50 67.5;"
  "s3 78.6 67.5; s4 92 67.5; f0 8 79.3; f1 21.4 79.3; f3 78.6 79.3; f4 92 79.3; g1 14.7 107.8;"
  "g3 85.3 107.8",
  ["p2 p1 q1 q2 q3 p3 p2 q2 r2 r1 q1", "q3 r3 r2 s2 s1 r1 a1 s0 s1 f1 f0 s0",
   "s2 s3 r3 a3 s4 s3 f3 f1 g1", "s4 f4 f3 g3"],
  clue="Feed the pigeons, rest your feet",
  colors={"green": ["q3 r3 r2 s2 s1 r1 a1 s0 s1 f1 f0 s0", "s2 s3 r3 a3 s4 s3 f3 f1 g1", "s4 f4 f3 g3"],
    "brown": ["p2 p1 q1 q2 q3 p3 p2 q2 r2 r1 q1"]})

P("whale", "Whale", "animal",
  "sn 8 77; h1 12.4 60.8; h2 25.7 49; h3 47.8 49; k1 61.1 57.8; q1 71.4 53.4; fl 68.4 37.2;"
  "fn 81.7 45.3; fr 92 56.4; q2 78.7 65.2; u1 69.9 81.4; u2 59.6 96.1; u3 43.4 103.5;"
  "u4 27.2 100.6; u5 12.4 90.2; m1 24.2 85.8; p1 41.9 90.2; p2 56.6 84.4; ey 37.5 57.8;"
  "ey2 37.5 69.6; sp1 25.7 35.7; sp2 15.4 29.8; sp3 36 29.8",
  ["sn h1 h2 h3 k1 q1 fl fn fr q2 u1 u2 u3 u4 u5 sn m1 p1 p2 u1", "h2 sp1 sp2", "q1 q2",
   "u2 p2", "u3 p1", "u4 m1", "ey ey2", "sp1 sp3"],
  clue="Thar she blows!",
  colors={"blue": ["sn h1 h2 h3 k1 q1 fl fn fr q2 u1 u2 u3 u4 u5 sn m1 p1 p2 u1", "q1 q2"],
    "cyan": ["u2 p2", "u3 p1", "u4 m1"], "white": ["h2 sp1 sp2", "ey ey2", "sp1 sp3"]})

P("hammer", "Hammer", "object",
  "fa 8 10.2; fb 8 42.2; fc 21 10.2; fd 21 42.2; t1 32.4 10.9; t2 46.2 11.7; e 58.4 13.2;"
  "h 81.3 20.8; i 92 42.2; j 79.8 35.4; k 66 30.8; hl 32.4 42.2; hr 46.2 42.2; g1l 32.4 77.4;"
  "g1r 46.2 77.4; g2l 32.4 89.6; g2r 46.2 89.6; g3l 32.4 101.8; g3r 46.2 101.8; el 32.4 114;"
  "er 46.2 114; eb 39.3 123.2",
  ["fc fa fb fd fc t1 t2 e h i j k hr hl fd", "t1 hl g1l g2l g3l el eb er g3r g2r g1r hr t2",
   "g1l g1r", "g2l g2r", "g3l g3r"],
  clue="When all you see is nails...",
  colors={"red": ["g1l g1r", "g2l g2r", "g3l g3r"],
    "white": ["fc fa fb fd fc t1 t2 e h i j k hr hl fd"],
    "brown": ["t1 hl g1l g2l g3l el eb er g3r g2r g1r hr t2"]})

P("ship", "Sailboat", "object",
  "mt 50 11.7; fg 66.2 17.4; m0 50 23.1; ma 50 39.2; mb 50 57; m1 50 71.5; dk 50 84.4;"
  "mc 88.8 71.5; jk 14.5 71.5; bw 8 84.4; sn 92 84.4; kb 22.5 100.6; ks 79.1 100.6;"
  "la 62.9 39.2; lb 77.1 57; js 30.5 57; w0 11.2 121.6; w1 25.8 111.9; w2 40.3 121.6;"
  "w3 54.8 111.9; w4 69.4 121.6; w5 83.9 111.9",
  ["dk m1 mb ma m0 mt fg m0 la lb mc m1 jk js ma la", "dk bw kb ks sn dk", "lb mb js",
   "w0 w1 w2 w3 w4 w5"],
  clue="Catch the wind, skip the engine",
  colors={"blue": ["w0 w1 w2 w3 w4 w5"], "white": ["mt fg m0 la lb mc m1 jk js ma la", "lb mb js"],
    "brown": ["mt m0 ma mb m1 dk bw kb ks sn dk"]})

P("butterfly", "Butterfly", "animal",
  "hd 50 45.7; aL 41.6 23.8; b1 50 57.4; b2 50 74.2; b3 50 102.8; u1L 33.2 33.9; u2L 13 30.5;"
  "u3L 8 52.4; u4L 23.1 72.5; d1L 16.4 92.7; d2L 29.8 109.5; s1L 19.8 44; s2L 33.2 47.3;"
  "s3L 24.8 59.1; aR 58.4 23.8; u1R 66.8 33.9; u2R 87 30.5; u3R 92 52.4; u4R 76.9 72.5;"
  "d1R 83.6 92.7; d2R 70.2 109.5; s1R 80.2 44; s2R 66.8 47.3; s3R 75.2 59.1",
  ["hd aL", "hd aR", "hd b1 b2 b3 d2L d1L u4L u3L u2L u1L b1 u1R u2R u3R u4R b2 u4L",
   "b3 d2R d1R u4R", "s1L s2L s3L s1L", "s1R s2R s3R s1R"],
  clue="I used to be a caterpillar",
  colors={"pink": ["s1L s2L s3L s1L", "s1R s2R s3R s1R"],
    "purple": ["u4L u3L u2L u1L b1 u1R u2R u3R u4R b2 u4L d1L d2L b3 d2R d1R u4R"],
    "brown": ["hd aL", "hd aR", "hd b1 b2 b3"]})

P("umbrella", "Umbrella", "object",
  "tip 50 11.2; t 50 23; oL 23.1 28; bL 11.4 41.5; rL0 8 61.6; sL0 18.5 52.4; rL1 29 61.6;"
  "sL1 39.5 52.4; r2 50 61.6; kL 30.7 41.5; km 50 41.5; sh 50 110.3; h1 45 122.1; h2 33.2 122.1;"
  "oR 76.9 28; bR 88.6 41.5; rR0 92 61.6; sR0 81.5 52.4; rR1 71 61.6; sR1 60.5 52.4;"
  "kR 69.3 41.5; h3 26.5 111.2",
  ["tip t oL bL rL0 sL0 rL1 sL1 r2 sR1 rR1 sR0 rR0 bR oR t kL rL1", "bL kL km t kR rR1",
   "bR kR km r2 sh h1 h2 h3"],
  clue="Singin' in the rain, but dry",
  colors={"red": ["t oL bL rL0 sL0 rL1 sL1 r2 sR1 rR1 sR0 rR0 bR oR t"],
    "blue": ["t kL rL1", "t km kL bL", "t kR rR1", "r2 km kR bR"],
    "brown": ["tip t", "r2 sh h1 h2 h3"]})

P("lotus", "Lotus", "plant",
  "T 50 21.7; a1L 40.2 41.2; a2L 36.5 62.2; cbL 42.5 87.7; v 50 68.2; mtL 23 33.7;"
  "moL 18.5 57.7; obL 29 84.7; otL 8 65.2; olL 15.5 81.7; w1L 14 99.7; w2L 32 99.7;"
  "w3L 39.5 111.7; a1R 59.7 41.2; a2R 63.5 62.2; cbR 57.5 87.7; mtR 77 33.7; moR 81.5 57.7;"
  "obR 71 84.7; otR 92 65.2; olR 84.5 81.7; w1R 86 99.7; w2R 68 99.7; w3R 60.5 111.7",
  ["T a1L a2L cbL obL moL mtL a2L", "T a1R a2R cbR obR moR mtR a2R", "T v cbL cbR v",
   "moL otL olL obL", "w1L w2L", "w3L w3R", "moR otR olR obR", "w1R w2R"],
  clue="Blooms beautifully out of the mud",
  colors={"pink": ["a2L a1L T a1R a2R cbR obR moR mtR a2R", "a2L cbL obL moL mtL a2L"],
    "green": ["T v cbL cbR v"],
    "brown": ["moL otL olL obL", "w1L w2L", "w3L w3R", "moR otR olR obR", "w1R w2R"]})

P("anchor2", "Anchor", "object",
  "rt 50 17; rb 50 41.2; r1L 39.5 23.1; r2L 39.5 35.2; stL 29 53.3; sct 50 53.3; sbL 29 65.5;"
  "scb 50 65.5; cr 50 116.3; a2L 27.4 108.3; mL 19.3 95.3; tL 17.7 71.1; bL 8 97; cL 30.6 93.7;"
  "r1R 60.5 23.1; r2R 60.5 35.2; stR 71 53.3; sbR 71 65.5; a2R 72.6 108.3; mR 80.7 95.3;"
  "tR 82.3 71.1; bR 92 97; cR 69.4 93.7",
  ["rb r2L r1L rt r1R r2R rb sct stL sbL scb sbR stR sct scb cr a2L mL cL tL bL mL",
   "cr a2R mR cR tR bR mR"],
  clue="I keep you grounded at sea",
  colors={"blue": ["rb sct stL sbL scb sbR stR sct scb"], "white": ["rt r1L r2L rb r2R r1R rt"],
    "brown": ["scb cr a2L mL cL tL bL mL", "cr a2R mR cR tR bR mR"]})

P("birdhouse", "Birdhouse", "object",
  "A 50 12.4; IA 50 25.4; ML 29 29; EL 8 45.7; NL 32.6 39.7; IEL 16.7 52.9; WL 16.7 102.1;"
  "PL 43.5 102.1; QL 43.5 121; pL 39.9 90.6; MR 71 29; ER 92 45.7; NR 67.4 39.7; IER 83.3 52.9;"
  "WR 83.3 102.1; PR 56.5 102.1; QR 56.5 121; pR 60.1 90.6; h0 50 58; h1 60.4 65.5;"
  "h2 56.4 77.6; h3 43.6 77.6; h4 39.6 65.5",
  ["ML EL IEL NL IA NR IER ER MR A ML NL", "IEL WL PL PR WR IER", "PL QL QR PR", "pL pR",
   "MR NR", "h0 h1 h2 h3 h4 h0"],
  clue="Tweet home, sweet home",
  colors={"orange": ["IEL WL PL PR WR IER", "PL QL QR PR"],
    "brown": ["ML A MR ER IER NR IA NL IEL EL ML NL", "pL pR", "MR NR"]})

P("dog", "Dog", "animal",
  "top 50 27.6; tL 31.5 32.6; sL 26.5 54.5; jL 33.2 76.3; chin 50 86.4; eo1L 14.7 36;"
  "eo2L 8 57.8; etL 13 84.7; eyL 38.2 42.7; ey2L 38.2 54.5; nlL 41.6 66.2; nb 50 74.6;"
  "tgL 42.4 95.6; tt 50 105.7; tR 68.5 32.6; sR 73.5 54.5; jR 66.8 76.3; eo1R 85.3 36;"
  "eo2R 92 57.8; etR 87 84.7; eyR 61.8 42.7; ey2R 61.8 54.5; nlR 58.4 66.2; tgR 57.6 95.6",
  ["tL top tR sR jR chin jL sL tL eo1L eo2L etL sL", "chin nb nlR nlL nb",
   "chin tgL tt tgR chin", "eyL ey2L", "tR eo1R eo2R etR sR", "eyR ey2R"],
  clue="Who's a good boy?",
  colors={"pink": ["chin tgL tt tgR chin"], "blue": ["eyL ey2L", "eyR ey2R"],
    "white": ["chin nb nlR nlL nb"],
    "brown": ["tL top tR sR jR chin jL sL tL eo1L eo2L etL sL", "tR eo1R eo2R etR sR"]})

P("coffee", "Coffee cup", "object",
  "tl 18.1 58.3; rb1 33.2 51.5; rb2 60.1 51.5; tr 75.2 58.3; rf2 60.1 65; rf1 33.2 65;"
  "c1 31.5 108.7; c2 61.8 108.7; sl 8 108.7; sr 92 108.7; u1 19.8 118.7; u2 80.2 118.7;"
  "o1 87 66.7; o2 92 81.8; o3 85.3 95.2; hh1 72.1 70; hh2 65.8 93.5; s0a 36.6 38.1;"
  "s0b 31.5 26.3; s0c 36.6 14.6; s1a 56.7 38.1; s1b 51.7 26.3; s1c 56.7 14.6",
  ["tl rb1 rb2 tr rf2 rf1 tl c1 sl u1 u2 sr c2 hh2 hh1 tr", "c1 c2", "hh1 o1 o2 o3 hh2",
   "s0a s0b s0c", "s1a s1b s1c"],
  clue="Espresso yourself!",
  colors={"white": ["tr rb2 rb1 tl rf1 rf2 tr hh1 o1 o2 o3 hh2 hh1", "c2 hh2", "s0a s0b s0c", "s1a s1b s1c"],
    "brown": ["tl c1 sl u1 u2 sr c2 c1"]})

P("igloo", "Igloo", "object",
  "o0L 8 92.7; o1L 9.1 80.9; o2L 14.9 64.1; o3L 23.1 52.7; o4L 36.6 43.4; top 50 40.6;"
  "bB1L 26.5 64.1; bB2L 38.2 64.1; bBc 50 64.1; aA1L 26.5 80.9; shL 38.2 80.9; dbL 33.2 92.7;"
  "dtop 50 75.9; o0R 92 92.7; o1R 90.9 80.9; o2R 85.1 64.1; o3R 76.9 52.7; o4R 63.4 43.4;"
  "bB1R 73.5 64.1; bB2R 61.8 64.1; aA1R 73.5 80.9; shR 61.8 80.9; dbR 66.8 92.7",
  ["o1L o0L dbL shL aA1L o1L o2L o3L o4L top o4R o3R o2R o1R o0R dbR shR aA1R o1R",
   "o2L bB1L bB2L bBc bB2R bB1R o2R", "top bBc", "bB1L aA1L", "bB2L shL dtop shR bB2R",
   "bB1R aA1R"],
  clue="Cool pad, snow kidding",
  colors={"blue": ["o2L bB1L bB2L bBc bB2R bB1R o2R", "top bBc", "bB1L aA1L", "bB2L shL dtop shR bB2R", "bB1R aA1R"],
    "cyan": ["o0L o1L aA1L shL dbL o0L", "o0R o1R aA1R shR dbR o0R"],
    "white": ["o1L o2L o3L o4L top o4R o3R o2R o1R"]})

P("wheat", "Wheat", "plant",
  "b1 50 93.1; b2 50 71.1; b3 50 49.1; s0 50 125.3; k0Lt 30.9 78.4; k0La 43.1 80.4;"
  "k0Lb 35.9 89.6; k0Lw 22.1 63.7; k0Rt 69.1 78.4; k0Ra 64.1 89.6; k0Rb 56.9 80.4;"
  "k0Rw 77.9 63.7; k1Lt 30.9 56.4; k1La 43.1 58.4; k1Lb 35.9 67.6; k1Lw 22.1 41.7;"
  "k1Rt 69.1 56.4; k1Ra 64.1 67.6; k1Rb 56.9 58.4; k1Rw 77.9 41.7; ktt 50 24.1; kta 56.6 36.6;"
  "ktb 43.4 36.6; ktw 50 8",
  ["b3 b2 b1 s0", "b3 kta ktt ktb b3", "k0Lt k0La b1 k0Lb k0Lt k0Lw",
   "k0Rt k0Ra b1 k0Rb k0Rt k0Rw", "k1Lt k1La b2 k1Lb k1Lt k1Lw", "k1Rt k1Ra b2 k1Rb k1Rt k1Rw",
   "ktt ktw"],
  clue="Our daily bread starts in a field",
  colors={"orange": ["b1 k0La k0Lt k0Lb b1 k0Ra k0Rt k0Rb b1", "b2 k1La k1Lt k1Lb b2 k1Ra k1Rt k1Rb b2", "b3 kta ktt ktb b3"],
    "green": ["b3 b2 b1 s0"]})

P("koala", "Koala", "animal",
  "j1L 22.9 58; e1L 8.9 49.8; e2L 8 33.5; e3L 21.1 23.9; e4L 36.4 29.5; j2L 40.1 45.3;"
  "c1L 21 91.9; cb 50 109.4; nuL 43 67.4; nlL 41.4 83; nb 50 97; eyL 31.3 65.8; ey2L 31.3 77.5;"
  "j1R 77.1 58; e1R 91.1 49.8; e2R 92 33.5; e3R 78.9 23.9; e4R 63.6 29.5; j2R 59.9 45.3;"
  "c1R 79 91.9; nuR 57 67.4; nlR 58.6 83; eyR 68.7 65.8; ey2R 68.7 77.5",
  ["j1L c1L cb c1R j1R e1R e2R e3R e4R j2R j2L e4L e3L e2L e1L j1L j2L",
   "nlL nuL nuR nlR nb nlL nlR", "eyL ey2L", "j1R j2R", "eyR ey2R"],
  clue="Eucalyptus is my whole personality",
  colors={"pink": ["nlL nuL nuR nlR nlL nb nlR"], "white": ["eyL ey2L", "eyR ey2R"],
    "brown": ["j1L j2L e4L e3L e2L e1L j1L c1L cb c1R j1R j2R e4R e3R e2R e1R j1R", "j2L j2R"]})

P("camera", "Camera", "object",
  "k1 8 41.5; k2 92 41.5; k3 92 105.3; k4 8 105.3; hb1 33.2 41.5; hb2 66.8 41.5; ht1 39.9 28;"
  "ht2 60.1 28; sL 8 73.4; sR 92 73.4; L0 75.2 73.4; L1 67.8 91.2; L2 50 98.6; L3 32.2 91.2;"
  "L4 24.8 73.4; L5 32.2 55.6; L6 50 48.2; L7 67.8 55.6; i0 36.6 73.4; i1 43.3 61.7;"
  "i2 56.7 61.7; i3 63.4 73.4; i4 56.7 85.1; i5 43.3 85.1",
  ["hb1 k1 sL k4 k3 sR k2 hb2 ht2 ht1 hb1 hb2", "sL L4 L3 L2 L1 L0 sR", "L0 L7 L6 L5 L4",
   "i0 i1 i2 i3 i4 i5 i0 i2"],
  clue="Say cheese!",
  colors={"blue": ["sL L4 L5 L6 L7 L0 L1 L2 L3 L4", "sR L0"], "cyan": ["i0 i1 i2 i3 i4 i5 i0 i2"],
    "white": ["hb1 ht1 ht2 hb2"], "brown": ["k1 hb1 hb2 k2 sR k3 k4 sL k1"]})

P("chessrook", "Chess rook", "object",
  "t1L 15.3 8.2; t2L 29 8.2; t3L 29 21.9; t4L 42.7 21.9; t5L 42.7 8.2; cL 15.3 35.6; gL 29 35.6;"
  "nL 25.3 48.4; wL 23.5 88.6; rL 14.4 97.7; sL 14.4 110.5; fL 8 125.1; t1R 84.7 8.2;"
  "t2R 71 8.2; t3R 71 21.9; t4R 57.3 21.9; t5R 57.3 8.2; cR 84.7 35.6; gR 71 35.6; nR 74.7 48.4;"
  "wR 76.5 88.6; rR 85.6 97.7; sR 85.6 110.5; fR 92 125.1",
  ["t3L t2L t1L cL gL gR cR t1R t2R t3R t4R t5R t5L t4L t3L gL",
   "cL nL wL rL sL fL fR sR rR wR nR cR", "nL nR", "wL wR", "sL sR", "t3R gR"],
  clue="I start every game stuck in a corner",
  colors={"white": ["t3L t2L t1L cL gL t3L t4L t5L t5R t4R t3R t2R t1R cR gR t3R", "gL gR"],
    "brown": ["cL nL nR cR", "nL wL wR nR", "wL rL sL sR rR wR", "sL fL fR sR"]})

P("cupcake", "Cupcake", "object",
  "wL0 18 85.7; wL1 34 85.7; w2 50 85.7; vL0 25.6 125.3; vL1 37.8 125.3; v2 50 125.3;"
  "aL1 8.9 75; aL2 16.5 62.9; bL 25.6 50.7; c1 50 70.5; c2 50 56.8; wR0 82 85.7; wR1 66 85.7;"
  "vR0 74.4 125.3; vR1 62.2 125.3; aR1 91.1 75; aR2 83.5 62.9; bR 74.4 50.7; ch0 50 37.7;"
  "ch1 40.6 30.9; ch2 44.2 19.8; ch3 55.8 19.8; ch4 59.4 30.9; st 62.2 8",
  ["wL0 wL1 w2 wR1 wR0 vR0 vR1 v2 vL1 vL0 wL0 aL1 aL2 bL ch0 bR aR2 aR1 wR0", "wL1 vL1",
   "w2 v2", "aL2 c1 aR2", "bL c2 bR", "wR1 vR1", "ch3 ch2 ch1 ch0 ch4 ch3 st"],
  clue="Muffin compares to me",
  colors={"red": ["ch3 st"],
    "pink": ["aL1 aL2 bL ch0 ch1 ch2 ch3 ch4 ch0 bR c2 bL", "aL2 c1 aR2 bR", "aR1 aR2"],
    "brown": ["wL0 aL1", "wL0 wL1 w2 wR1 wR0 aR1", "wL0 vL0 vL1 wL1", "w2 v2 vL1", "v2 vR1 wR1", "wR0 vR0 vR1"]})

P("turtle", "Turtle", "animal",
  "o1L 40.3 36; o1R 59.7 36; o2L 23.8 49.1; o2R 76.2 49.1; o3L 16.7 72.8; o3R 83.3 72.8;"
  "o4L 23.8 96.5; o4R 76.2 96.5; o5L 40.3 109.6; o5R 59.7 109.6; xtL 41.2 55.3; xtR 58.7 55.3;"
  "xmL 30.7 72.8; xmR 69.3 72.8; xbL 41.2 90.3; xbR 58.7 90.3; hdL 36.9 20.3; hdR 63.1 20.3;"
  "hd 50 8; ffL 8 27.3; ffR 92 27.3; bfL 8 118.3; bfR 92 118.3; tail 50 125.3",
  ["o1L o1R o2R o3R o4R o5R o5L o4L o3L o2L o1L xtL xtR xmR xbR xbL xmL xtL",
   "o1L hdL hd hdR o1R xtR", "o1L ffL o2L", "o1R ffR o2R", "o3L xmL", "o3R xmR",
   "o4L bfL o5L xbL", "o4R bfR o5R xbR", "o5L tail o5R"],
  clue="Slow and steady wins the race",
  colors={"green": ["o1L o2L o3L o4L o5L o5R o4R o3R o2R o1R o1L xtL xtR xmR xbR xbL xmL xtL", "o1R xtR", "o3L xmL", "o3R xmR", "o5L xbL", "o5R xbR"],
    "brown": ["o2L ffL o1L hdL hd hdR o1R ffR o2R", "o4L bfL o5L tail o5R bfR o4R"]})

P("headphones", "Headphones", "object",
  "o0 15.4 60.9; i0 26.9 60.9; o1 25.5 36.4; i1 33.7 44.6; o2 50 26.3; i2 50 37.8; o3 74.5 36.4;"
  "i3 66.3 44.6; o4 84.6 60.9; i4 73.1 60.9; c1L 12.1 72.4; c6L 8 89.7; c5L 12.1 107;"
  "c4L 31.9 107; c3L 36 89.7; c2L 31.9 72.4; kL 24.5 89.7; c1R 87.9 72.4; c6R 92 89.7;"
  "c5R 87.9 107; c4R 68.1 107; c3R 64 89.7; c2R 68.1 72.4; kR 75.5 89.7",
  ["o0 o1 o2 o3 o4 i4 i3 i2 i1 i0 o0 c1L c6L c5L c4L c3L c2L i0", "o1 i1", "o2 i2", "o3 i3",
   "o4 c1R c6R c5R c4R c3R c2R i4", "c1L c2L kL c4L", "c1R c2R kR c4R"],
  clue="Noise? Cancelled.",
  colors={"purple": ["c1L c2L c3L c4L c5L c6L c1L", "c1R c2R c3R c4R c5R c6R c1R"],
    "white": ["c4L kL c2L", "c4R kR c2R"],
    "brown": ["o1 o2 o3 o4 c1R", "o1 o0 c1L", "o1 i1 i2 i3 i4 c2R", "i1 i0 c2L", "o2 i2", "o3 i3"]})

P("acorn", "Acorn", "plant",
  "st 54.8 8; ct 50 22.5; c1L 30.7 27.3; c2L 16.2 38.5; rimL 9.8 51.4; b1L 22.7 59.4;"
  "b2L 36.3 62.6; b3 50 64.3; h1L 29.1 43.4; h2L 42.8 41.8; n1L 24.3 77.1; n2L 29.9 93.2;"
  "n3L 39.6 106; tip 50 114.1; nib 50 125.3; c1R 69.3 27.3; c2R 83.8 38.5; rimR 90.2 51.4;"
  "b1R 77.3 59.4; b2R 63.7 62.6; h1R 70.9 43.4; h2R 57.2 41.8; n1R 75.7 77.1; n2R 70.1 93.2;"
  "n3R 60.4 106",
  ["st ct c1L c2L rimL b1L b2L b3 b2R b1R rimR c2R c1R ct",
   "tip n3L n2L n1L b1L h1L b2L h2L b3 h2R b2R h1R b1R n1R n2R n3R tip nib"],
  clue="Every mighty oak started here",
  colors={"orange": ["b1L n1L n2L n3L tip n3R n2R n1R b1R"], "green": ["st ct"],
    "brown": ["b1L rimL c2L c1L ct c1R c2R rimR b1R b2R b3 b2L b1L h1L b2L h2L b3 h2R b2R h1R b1R"]})

P("hourglass", "Hourglass", "object",
  "ptL 8 14.2; ptR 92 14.2; pbL 18.5 24.7; pbR 81.5 24.7; gL 32 24.7; gR 68 24.7; s1L 23.7 39.7;"
  "s1R 76.2 39.7; s2L 30.5 54.7; s2R 69.5 54.7; wL 44 66.7; wR 56 66.7; s3L 30.5 78.7;"
  "s3R 69.5 78.7; s4L 23.7 93.7; s4R 76.2 93.7; qtL 18.5 108.7; qtR 81.5 108.7; gbL 32 108.7;"
  "gbR 68 108.7; qbL 8 119.2; qbR 92 119.2; dip 50 56.2; peak 50 84.7",
  ["pbL ptL ptR pbR gR gL pbL qtL gbL s4L s3L wL s2L s1L gL",
   "pbR qtR gbR s4R s3R wR s2R s1R gR", "s2L dip s2R", "s4L peak s4R", "qtL qbL qbR qtR",
   "gbL gbR"],
  clue="Time is running out... grain by grain",
  colors={"cyan": ["gL s1L s2L dip s2R s1R gR", "s2L wL s3L s4L peak s4R s3R wR s2R", "s4L gbL", "s4R gbR"],
    "brown": ["pbL ptL ptR pbR gR gL pbL qtL gbL gbR qtR pbR", "qtL qbL qbR qtR"]})

P("camel", "Camel", "animal",
  "n1 8 41.9; h1 14 31.4; h2 26 28.4; e 30.5 17.9; h3 32 38.9; j 17 50.9; nb 42.5 53.9;"
  "p1 51.5 32.9; d 60.5 46.4; p2 71 32.9; r 83 49.4; t 92 59.9; rt 80.7 65.9; b2 74 77.9;"
  "b1 47 77.9; c 38 70.4; nf 27.5 61.4; fk1 41 95.9; ff1 39.5 115.4; fk2 53 95.9; ff2 56 115.4;"
  "rk1 69.5 95.9; rf1 71 115.4; rk2 81.5 95.9; rf2 84.5 115.4",
  ["h2 h1 n1 j nf c b1 b2 rt r p2 d p1 nb h3 h2 e", "h3 j", "nb c", "r t",
   "ff1 fk1 b1 fk2 ff2", "rf1 rk1 b2 rk2 rf2"],
  clue="Two lumps, please - no sugar needed",
  colors={"orange": ["nb p1 d p2 r rt b2", "r t"], "white": ["h2 e"],
    "brown": ["b2 b1 c nb h3 h2 h1 n1 j nf c", "b2 rk1 rf1", "b2 rk2 rf2", "ff1 fk1 b1 fk2 ff2"]})

P("rocket", "Rocket", "object",
  "tip 50 8; c1L 41 20; cbL 33.5 36.6; fbL 33.5 78.7; btL 33.5 93.7; ftL 16.9 98.3;"
  "fwL 16.9 84.7; nzL 42.5 101.3; flL 39.5 113.3; fl 50 125.3; wL 38.7 56.1; wuL 44 46.4;"
  "wdL 44 65.9; c1R 59 20; cbR 66.5 36.6; fbR 66.5 78.7; btR 66.5 93.7; ftR 83.1 98.3;"
  "fwR 83.1 84.7; nzR 57.5 101.3; flR 60.5 113.3; wR 61.3 56.1; wuR 56 46.4; wdR 56 65.9",
  ["cbL c1L tip c1R cbR fbR btR nzR nzL btL fbL cbL cbR", "fbL fwL ftL btL btR ftR fwR fbR",
   "nzL flL fl flR nzR", "wL wuL wuR wR wdR wdL wL wR"],
  clue="3... 2... 1... liftoff!",
  colors={"orange": ["fbL fwL ftL btL", "fbR fwR ftR btR"], "red": ["tip c1L cbL cbR c1R tip"],
    "blue": ["wL wdL wdR wR wuR wuL wL"], "white": ["cbL fbL btL", "cbR fbR btR"]})

P("sunglasses", "Sunglasses", "object",
  "aL 8 64.1; bL 25.8 61.6; cL 43.6 64.1; gL 9.3 75.6; dL 43.6 75.6; mL 10.5 92.1;"
  "fL 23.3 102.3; eL 37.3 97.2; gl1L 18.8 82.6; gl2L 27.1 90.8; hL 11.8 41.2; jL 18.2 31;"
  "aR 92 64.1; bR 74.2 61.6; cR 56.4 64.1; gR 90.7 75.6; dR 56.4 75.6; mR 89.5 92.1;"
  "fR 76.7 102.3; eR 62.7 97.2; gl1R 81.2 82.6; gl2R 72.9 90.8; hR 88.2 41.2; jR 81.8 31",
  ["aL hL jL", "aL bL cL cR bR aR hR jR", "aL gL dL cL", "gL mL fL eL dL", "gl1L gl2L",
   "aR gR dR cR", "gR mR fR eR dR", "gl1R gl2R"],
  clue="Too cool for UV rays",
  colors={"cyan": ["aL gL dL cL", "gL mL fL eL dL", "aR gR dR cR", "gR mR fR eR dR"],
    "white": ["gl1L gl2L", "gl1R gl2R"], "brown": ["jL hL aL bL cL cR bR aR hR jR"]})

P("telescope", "Telescope", "object",
  "e1 8 67.8; e2 13 78.5; k1 18.1 63.1; k2 23.1 73.8; a0 26.9 55.4; b0 34.6 72.1; a1 47.9 44.5;"
  "b1 56.5 62.9; a2 67.7 34.1; b2 77.1 54.4; a3 81.5 26.3; b3 92 48.9; hub 56.5 75.4;"
  "fl 34.2 113.7; fm 59.1 116.3; fr 82.8 113.7; sl 44.2 96.4; sm 58 97.9; sr 71 96.4;"
  "sc 28.1 28.2; st 28.1 17; sb 28.1 39.4; sw 16.9 28.2; se 39.3 28.2",
  ["k1 k2 e2 e1 k1 a0 a1 a2 a3 b3 b2 b1 b0 k2", "a0 b0", "a1 b1 hub sl fl", "a2 b2",
   "fm sm hub sr fr", "sl sm sr", "st sc sb", "sw sc se"],
  clue="Seeing stars on purpose",
  colors={"blue": ["a1 a0 b0 b1 b2 b3 a3 a2 a1 b1", "a2 b2"], "white": ["st sc sb", "sw sc se"],
    "brown": ["k1 k2 e2 e1 k1 a0", "k2 b0", "b1 hub sl fl", "fm sm hub sr fr", "sl sm sr"]})

P("ant", "Ant", "animal",
  "hl 38.4 36.4; ael 33.1 18.7; atl 18 8; tl 40.2 61.3; kfl 23.3 47.1; ffl 10 32.9;"
  "fml 9.1 68.4; kbl 21.6 79.1; fbl 8.2 104; al1l 32.2 88.9; al2l 27.8 109.3; hr 61.6 36.4;"
  "aer 66.9 18.7; atr 82 8; tr 59.8 61.3; kfr 76.7 47.1; ffr 90 32.9; fmr 90.9 68.4;"
  "kbr 78.4 79.1; fbr 91.8 104; al1r 67.8 88.9; al2r 72.2 109.3; ht 50 24; n1 50 48.9;"
  "n2 50 75.6; ab 50 125.3",
  ["hl ht hr n1 hl ael atl", "tl n1 tr n2 tl kfl ffl", "tl fml", "tl kbl fbl",
   "al1l n2 al1r al2r ab al2l al1l al1r", "hr aer atr", "tr kfr ffr", "tr fmr", "tr kbr fbr"],
  clue="I can lift fifty times my own weight",
  colors={"red": ["al1l n2 tr n1 hr ht hl n1 tl n2 al1r al2r ab al2l al1l al1r"],
    "white": ["hl ael atl", "hr aer atr"],
    "brown": ["tl kfl ffl", "tl fml", "tl kbl fbl", "tr kfr ffr", "tr fmr", "tr kbr fbr"]})

P("corn", "Corn on the cob", "plant",
  "T 50 10.1; o2L 30.8 26.5; v1L 41.8 28.3; o3L 28.1 43.8; v2L 41.8 43.8; o4L 28.1 59.4;"
  "v3L 41.8 59.4; o5L 29.9 74.9; v4L 41.8 74.9; tL 8 48.4; loL 9.8 79.4; lbL 26.3 101.4;"
  "Bm 50 110.5; St 50 123.3; o2R 69.2 26.5; v1R 58.2 28.3; o3R 71.9 43.8; v2R 58.2 43.8;"
  "o4R 71.9 59.4; v3R 58.2 59.4; o5R 70.1 74.9; v4R 58.2 74.9; tR 92 48.4; loR 90.2 79.4;"
  "lbR 73.7 101.4",
  ["o2L T o2R o3R o4R o5R v4R v3R v2R v1R T v1L v2L v3L v4L o5L o4L o3L o2L v1L v1R o2R",
   "o3L v2L v2R o3R", "o4L v3L v3R o4R", "v4L v4R",
   "Bm lbL loL tL o5L Bm lbR loR tR o5R Bm St"],
  clue="All ears, and a-maize-ing at it",
  colors={"orange": ["v1L v1R", "o3L v2L v2R o3R", "o4L v3L v3R o4R", "v4L v4R"],
    "green": ["o5L tL loL lbL Bm o5L", "Bm lbR loR tR o5R Bm"], "white": ["Bm St"]})

P("train", "Steam train", "object",
  "c1 8 32.9; c2 32 32.9; c3 32 53.9; c4 8 80.9; s1 53 53.9; s2 48.5 35.9; s3 69.5 35.9;"
  "s4 65 53.9; f1 80 53.9; f2 80 80.9; cc 92 100.4; cb 80 100.4; w0 20.4 80.9; w1 31.6 80.9;"
  "w2 37.2 90.7; w3 31.6 100.4; w4 20.4 100.4; w5 14.7 90.7; v0 54.9 80.9; v1 66.1 80.9;"
  "v2 71.8 90.7; v3 66.1 100.4; v4 54.9 100.4; v5 49.2 90.7",
  ["s1 c3 c2 c1 c4 w0 w1 v0 v1 f2 f1 s4 s1 s2 s3 s4", "f2 cc cb v2 v1", "w0 w5 w4 w3 w2 w1",
   "w2 v5 v4 v3 v2", "v0 v5"],
  clue="Choo-choo-choose me!",
  colors={"red": ["c1 c2 c3 s1 s4 f1 f2 v1 v0 w1 w0 c4 c1"], "blue": ["s1 s2 s3 s4"],
    "brown": ["f2 cc cb v2 v3 v4 v5 w2 w3 w4 w5 w0", "w1 w2", "v0 v5", "v1 v2"]})

P("pencil", "Pencil", "object",
  "ea 33.5 8; eb 16.8 17.6; f0a 44.8 13.5; f0b 15.9 30.2; f1a 50.4 23.1; f1b 21.4 39.8;"
  "f2a 55.9 32.7; f2p 46.3 38.3; f2q 36.6 43.9; f2b 27 49.4; sa 78.9 72.6; sp 69.3 78.1;"
  "sq 59.6 83.7; sb 50 89.2; k1 79.7 85; k2 70 90.5; k3 60.4 96.1; la 82.6 101.2; lb 73 106.8;"
  "tip 84.1 114.9; w0 70.8 122.4; w1 58.9 113.5; w2 47 123.8; w3 35.2 114.9; w4 23.3 125.3",
  ["f0a ea eb f0b f1b f2b sb k3 lb tip la k1 sa f2a f1a f0a f0b", "f1a f1b", "f2a f2p f2q f2b",
   "f2p sp k1", "f2q sq k2 sp", "sq k3", "la lb", "tip w0 w1 w2 w3 w4"],
  clue="Sharp wit, but I always get the point",
  colors={"orange": ["f2a f2p f2q f2b", "f2p sp k1", "f2q sq k2 sp", "sq k3"],
    "pink": ["ea f0a f0b eb ea"], "white": ["f0a f1a f1b f0b", "tip w0 w1 w2 w3 w4"],
    "brown": ["f1a f2a sa k1 la tip lb k3 sb f2b f1b", "la lb"]})

P("bear", "Bear", "animal",
  "hal 35.6 35.9; hbl 16.1 53.5; hcl 13.9 84.6; hdl 33.8 106.3; e1l 27.1 27; e2l 15 28.1;"
  "e3l 8 38.1; iel 21.1 39.3; eyal 34.8 55.5; eybl 36.4 66.7; mtl 40.4 77.9; ml 33.2 90.7;"
  "har 64.4 35.9; hbr 83.9 53.5; hcr 86.1 84.6; hdr 66.2 106.3; e1r 72.9 27; e2r 85 28.1;"
  "e3r 92 38.1; ier 78.9 39.3; eyar 65.2 55.5; eybr 63.6 66.7; mtr 59.6 77.9; mr 66.8 90.7;"
  "nb 50 87.5; m0 50 99.5",
  ["eyal eybl", "mtl ml m0 mr mtr mtl nb mtr", "eyar eybr", "nb m0",
   "hal hbl hcl hdl hdr hcr hbr har hal e1l e2l e3l hbl iel hal",
   "har e1r e2r e3r hbr ier har"],
  clue="Someone's been sleeping in my bed!",
  colors={"orange": ["mtl ml m0 mr mtr mtl nb mtr", "nb m0"], "cyan": ["eyal eybl", "eyar eybr"],
    "white": ["hal iel hbl", "har ier hbr"],
    "brown": ["hal har hbr hcr hdr hdl hcl hbl hal e1l e2l e3l hbl", "har e1r e2r e3r hbr"]})

P("pizza", "Pizza slice", "object",
  "o0 9.8 19.3; o1 29.1 11.2; o2 50 8; o3 70.9 11.2; o4 90.2 19.3; tip 50 125.3; i0 15.3 33.7;"
  "i4 84.7 33.7; i1 31.5 27.3; i2 50 24.9; i3 68.5 27.3; p0 40.4 43.4; p1 49.5 50; p2 46.1 60.8;"
  "p3 34.7 60.8; p4 31.2 50; qa 77 54; qb 67.4 79.3; q1 65.5 53; q2 57.3 61; q3 58.1 72.5;"
  "ra 35.2 86.4; rb 43.2 107.3; r1 47.2 87.4; r2 51.4 98.7",
  ["o1 o0 i0 ra rb tip qb qa i4 o4 o3 o2 o1 i1 i0", "o3 i3 i2 i1", "i4 i3", "qa q1 q2 q3 qb",
   "ra r1 r2 rb", "p0 p1 p2 p3 p4 p0"],
  clue="That's amore!",
  colors={"orange": ["i0 i1 i2 i3 i4"], "red": ["o1 o0 i0 ra rb tip qb qa i4 o4", "p0 p1 p2 p3 p4 p0"],
    "white": ["qa q1 q2 q3 qb", "ra r1 r2 rb"], "brown": ["o3 o4", "o3 o2 o1 i1", "o3 i3"]})

P("trafficlight", "Traffic light", "object",
  "TL 30.7 8; TR 69.3 8; L1 30.7 38.4; R1 69.3 38.4; L2 30.7 68.7; R2 69.3 68.7; BL 30.7 99.1;"
  "BR 69.3 99.1; Q 50 110.1; G 50 125.3; x0 50 14.6; x1 59.2 21.3; x2 55.7 32; x3 44.3 32;"
  "x4 40.8 21.3; y0 50 44.9; y1 59.2 51.6; y2 55.7 62.4; y3 44.3 62.4; y4 40.8 51.6; z0 50 75.3;"
  "z1 59.2 82; z2 55.7 92.8; z3 44.3 92.8; z4 40.8 82",
  ["L1 L2 BL BR R2 R1 TR TL L1 R1", "L2 R2", "BL Q BR", "Q G", "x0 x1 x2 x3 x4 x0",
   "y0 y1 y2 y3 y4 y0", "z0 z1 z2 z3 z4 z0"],
  clue="Stop, wait for it... go!",
  colors={"red": ["x0 x1 x2 x3 x4 x0"], "green": ["z0 z1 z2 z3 z4 z0"],
    "brown": ["L1 TL TR R1 R2 BR BL L2 L1 R1", "L2 R2", "BL Q BR", "Q G"]})

P("pumpkin", "Pumpkin", "plant",
  "SBL 43 58.7; U1L 28 56.7; U2L 14 66.7; LL 8 82.7; D2L 14 100.7; D1L 28 112.7; B 50 116.7;"
  "R1L 22 84.7; R2L 38 85.7; SBR 57 58.7; U1R 72 56.7; U2R 86 66.7; LR 92 82.7; D2R 86 100.7;"
  "D1R 72 112.7; R1R 78 84.7; R2R 62 85.7; STL 45 40.7; STR 57 38.7; LS1 66 26.7; Lt 87 22.7;"
  "LS2 76 38.7; C1 34 34.7; C2 28 23.7; C3 39 16.7",
  ["U1L SBL SBR U1R U2R LR D2R D1R B D1L D2L LL U2L U1L R1L D1L", "U1R R1R D1R",
   "STL SBL R2L B R2R SBR STR STL C1 C2 C3", "STR LS1 Lt LS2 STR Lt"],
  clue="Your ride, Cinderella... until midnight",
  colors={"orange": ["U1L SBL SBR U1R U2R LR D2R D1R B D1L D2L LL U2L U1L R1L D1L", "U1R R1R D1R", "SBL STL STR SBR R2R B R2L SBL"],
    "green": ["STR LS1 Lt LS2 STR Lt"], "brown": ["STL C1 C2 C3"]})

P("well", "Wishing well", "object",
  "pk 50 10.8; eL 8 37.7; pL 21.4 37.7; xL 21.4 52.8; xc 50 52.8; rL 9.7 86.4; r2L 21.4 84.3;"
  "fL 29.8 94.8; fc 50 97.3; wL 9.7 118.3; w2L 29.8 120.8; wc 50 122.5; bt1L 38.2 64.6;"
  "bb1L 41.6 78; eR 92 37.7; pR 78.6 37.7; xR 78.6 52.8; rR 90.3 86.4; r2R 78.6 84.3;"
  "fR 70.2 94.8; wR 90.3 118.3; w2R 70.2 120.8; bt1R 61.8 64.6; bb1R 58.4 78; bt 50 64.6",
  ["pL eL pk eR pR xR r2R rR fR fc fL rL r2L xL pL pR", "xL xc xR",
   "xc bt bt1L bb1L bb1R bt1R bt", "rL wL w2L wc w2R wR rR", "r2L r2R", "fL w2L", "fc wc",
   "fR w2R"],
  clue="Toss a coin and hope",
  colors={"orange": ["pL eL pk eR pR"], "blue": ["xc bt bt1L bb1L bb1R bt1R bt"],
    "brown": ["pL xL xc xR pR", "xL r2L r2R xR", "rL r2L", "rL fL fc fR rR r2R", "rL wL w2L wc w2R wR rR", "fL w2L", "fc wc", "fR w2R"]})

P("beetle", "Beetle", "animal",
  "hL 42.2 27.8; aL 28.2 13.8; pL 36 37.1; pbL 26.7 55.8; pc 50 55.8; e1L 22 83.8;"
  "e2L 32.9 108.7; bot 50 119.6; k1L 22 34; f1L 15.8 21.6; k2L 14.2 62; f2L 8 76; k3L 12.7 94.7;"
  "f3L 14.2 111.8; hR 57.8 27.8; aR 71.8 13.8; pR 64 37.1; pbR 73.3 55.8; e1R 78 83.8;"
  "e2R 67.1 108.7; k1R 78 34; f1R 84.2 21.6; k2R 85.8 62; f2R 92 76; k3R 87.3 94.7;"
  "f3R 85.8 111.8",
  ["hL aL", "hL pL pbL pc pbR pR hR aR", "hL hR", "pL k1L f1L", "pc bot e2L e1L pbL k2L f2L",
   "e1L k3L f3L", "bot e2R e1R pbR k2R f2R", "pR k1R f1R", "e1R k3R f3R"],
  clue="Crawling in armour since the dinosaurs",
  colors={"orange": ["hL aL", "hR aR"],
    "green": ["pbL pL hL hR pR pbR pc pbL e1L e2L bot pc", "bot e2R e1R pbR"],
    "brown": ["pL k1L f1L", "pbL k2L f2L", "e1L k3L f3L", "pR k1R f1R", "pbR k2R f2R", "e1R k3R f3R"]})

P("bell", "Bell", "object",
  "sL 36 32.4; aL 25.1 40.1; bL 21.2 54.1; cL 19.7 69.7; eL 17.3 82.9; fL 8 94.6; gL 8 107;"
  "mL 29 107; sR 64 32.4; aR 74.9 40.1; bR 78.8 54.1; cR 80.3 69.7; eR 82.7 82.9; fR 92 94.6;"
  "gR 92 107; mR 71 107; t 50 27.7; b0 50 107; q1 39.7 20.2; q2 43.6 8; q3 56.4 8; q4 60.3 20.2;"
  "k1 59.6 114; k2 55.9 125.3; k3 44.1 125.3; k4 40.4 114",
  ["aL bL cL eL fL gL mL b0 mR gR fR eR cR bR aR sR t sL aL aR", "eL eR", "fL fR",
   "t q1 q2 q3 q4 t", "b0 k1 k2 k3 k4 b0"],
  clue="Saved by me at the end of class",
  colors={"orange": ["eL eR", "fL fR"], "red": ["b0 k1 k2 k3 k4 b0"], "brown": ["t q1 q2 q3 q4 t"]})

P("burger", "Burger", "object",
  "t0L 14.9 59.4; t1L 17.9 42.6; t2L 31.7 30.4; t3 50 25.8; pk1L 32.4 59.4; pk2 50 59.4;"
  "v1L 23.7 72.4; v2L 41.2 72.4; pt0L 11.8 72.4; peL 8 83.1; pb0L 11.8 93.8; bbL 16.4 107.5;"
  "sa1L 30.1 48; sa2L 40.1 41.1; t0R 85.1 59.4; t1R 82.1 42.6; t2R 68.3 30.4; pk1R 67.6 59.4;"
  "v1R 76.3 72.4; v2R 58.8 72.4; pt0R 88.2 72.4; peR 92 83.1; pb0R 88.2 93.8; bbR 83.6 107.5;"
  "sa1R 69.9 48; sa2R 59.9 41.1",
  ["t0L t1L t2L t3 t2R t1R t0R pk1R pk2 pk1L t0L v1L pk1L v2L pk2 v2R pk1R v1R t0R",
   "pb0L peL pt0L v1L v2L v2R v1R pt0R peR pb0R bbR bbL pb0L pb0R", "sa1L sa2L", "sa1R sa2R"],
  clue="Hold the pickles, please",
  colors={"orange": ["t0L t1L t2L t3 t2R t1R t0R", "pb0L bbL bbR pb0R pb0L"],
    "green": ["t0L pk1L pk2 pk1R t0R v1R pk1R v2R pk2 v2L pk1L v1L t0L"],
    "white": ["sa1L sa2L", "sa1R sa2R"],
    "brown": ["pb0L peL pt0L v1L v2L v2R v1R pt0R peR pb0R"]})

P("crab", "Crab", "animal",
  "b1L 38.3 58.5; b1R 61.7 58.5; b2L 23.2 70.2; b2R 76.8 70.2; b4L 33.7 84.2; b4R 66.3 84.2;"
  "eL 39.5 46.8; eR 60.5 46.8; wL 18.5 56.2; wR 81.5 56.2; oL 8 44.5; oR 92 44.5; uL 15 29.3;"
  "uR 85 29.3; nL 20.8 42.2; nR 79.2 42.2; lL 32.5 34; lR 67.5 34; k1L 8 76; k1R 92 76;"
  "f1L 8 88.8; f1R 92 88.8; k2L 23.2 92.3; k2R 76.8 92.3; f2L 26.7 104; f2R 73.3 104",
  ["b1L b1R b2R b4R b4L b2L b1L eL", "b1R eR", "b4L k2L f2L", "b4R k2R f2R", "wL b2L k1L f1L",
   "wL oL uL nL lL wL", "wR b2R k1R f1R", "wR oR uR nR lR wR"],
  clue="Pinch me, I must be dreaming",
  colors={"orange": ["b1L b1R b2R b4R b4L b2L b1L"],
    "red": ["b2L wL oL uL nL lL wL", "b2R wR oR uR nR lR wR"], "white": ["b1L eL", "b1R eR"],
    "brown": ["b2L k1L f1L", "b2R k1R f1R", "b4L k2L f2L", "b4R k2R f2R"]})

P("bus", "Bus", "object",
  "a 8 33; b 92 33; c 92 90.1; dd 8 90.1; t0 14.7 44.8; u0 14.7 63.3; t1 31.5 44.8;"
  "u1 31.5 63.3; t2 48.3 44.8; u2 48.3 63.3; t3 65.1 44.8; u3 65.1 63.3; t4 81.9 44.8;"
  "u4 81.9 63.3; w0 19.8 90.1; w1 25.6 80; w2 37.4 80; w3 43.3 90.1; w4 37.4 100.3;"
  "w5 25.6 100.3; v0 56.7 90.1; v1 62.6 80; v2 74.4 80; v3 80.2 90.1; v4 74.4 100.3;"
  "v5 62.6 100.3",
  ["t1 t0 u0 u1 u2 u3 u4 t4 t3 t2 t1 u1", "t2 u2", "t3 u3",
   "w0 dd a b c v3 v2 v1 v0 w3 w2 w1 w0 w5 w4 w3", "v0 v5 v4 v3"],
  clue="Please move down to the back!",
  colors={"orange": ["w0 dd a b c v3"],
    "blue": ["t1 t0 u0 u1 u2 u3 u4 t4 t3 t2 t1 u1", "t2 u2", "t3 u3"],
    "brown": ["w3 v0 v1 v2 v3 v4 v5 v0", "w3 w2 w1 w0 w5 w4 w3"]})

P("cactus", "Cactus", "plant",
  "ct 50 13.4; ctL 38.7 23.1; ctR 61.3 23.1; jL1 38.7 58.6; jL2 38.7 76.4; jR1 61.3 45.7;"
  "jR2 61.3 61.8; bL 38.7 87.7; b0 50 87.7; bR 61.3 87.7; aEL 25.8 58.6; aIL 25.8 44.1;"
  "aTL 16.9 32.7; aOL 8 45.7; aBL 12.8 76.4; aER 74.2 45.7; aIR 74.2 31.1; aTR 83.1 19.8;"
  "aOR 92 32.7; aBR 87.2 61.8; pTL 20.9 87.7; pTR 79.1 87.7; pML 20.9 99; pMR 79.1 99;"
  "pBL 29.8 120; pBR 70.2 120",
  ["ct ctL jL1 jL2 bL pTL pML pMR pTR bR jR2 jR1 ctR ct b0 bL", "jL1 aEL aIL aTL aOL aBL jL2",
   "jR1 aER aIR aTR aOR aBR jR2", "b0 bR", "pML pBL pBR pMR"],
  clue="Don't hug me, I'm a little prickly",
  colors={"orange": ["pML pBL pBR pMR"],
    "green": ["ct ctL jL1 jL2 bL b0 ct ctR jR1 jR2 bR b0", "jL1 aEL aIL aTL aOL aBL jL2", "jR1 aER aIR aTR aOR aBR jR2"],
    "brown": ["bL pTL pML pMR pTR bR"]})

P("church", "Church", "object",
  "ct 50 8; cl 38.7 19.3; cr 61.3 19.3; cc 50 19.3; st 50 32.1; sbl 30.7 53; sbr 69.3 53;"
  "tjl 30.7 85.2; tjr 69.3 85.2; el 9.8 96.4; er 90.2 96.4; gl 9.8 125.3; gr 90.2 125.3;"
  "tgl 30.7 125.3; tgr 69.3 125.3; dl 42 125.3; dr 58 125.3; dml 42 107.7; dmr 58 107.7;"
  "dt 50 96.4; w0 50 60.2; w1 39.6 66.3; w2 39.6 78.3; w3 50 84.3; w4 60.4 78.3; w5 60.4 66.3",
  ["ct cc st sbl sbr st", "cl cc cr", "sbl tjl tgl gl el tjl", "sbr tjr tgr dr dl tgl",
   "tjr er gr tgr", "dl dml dt dmr dr", "w0 w1 w2 w3 w4 w5 w0 w3", "w1 w4", "w2 w5"],
  clue="Sunday best, bells on",
  colors={"orange": ["cc st sbl sbr st"], "blue": ["w0 w1 w2 w3 w4 w5 w0 w3", "w1 w4", "w2 w5"],
    "brown": ["ct cc cl", "cr cc", "dl dml dt dmr dr"]})

P("ladybug", "Ladybug", "animal",
  "b0 50 37.6; b1 75.8 46; b2 91.7 67.9; b3 91.7 95; b4 75.8 116.9; b5 50 125.3; b6 24.2 116.9;"
  "b7 8.3 95; b8 8.3 67.9; b9 24.2 46; hL 30 31.8; hA 41.4 21.4; hB 58.6 21.4; hR 70 31.8;"
  "nL 29 8; nR 71 8; m1 50 50.9; m2 50 68.1; x1 40.5 59.5; x2 59.5 59.5; p00L 30 82.9;"
  "p01L 39 97.9; p02L 20.9 97.9; p00R 70 82.9; p01R 79.1 97.9; p02R 61 97.9",
  ["b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b0 m1 m2 b5", "b1 hR hB hA hL b9", "hA nL", "hB nR",
   "m1 x1 m2 x2 m1", "p00L p01L p02L p00L", "p00R p01R p02R p00R"],
  clue="Seven spots and a lucky streak",
  colors={"red": ["b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b0"], "white": ["m1 x1 m2 x2 m1"],
    "brown": ["b0 m1 m2 b5", "b1 hR hB hA hL b9", "hA nL", "hB nR", "p00L p01L p02L p00L", "p00R p01R p02R p00R"]})

P("clock", "Alarm clock", "object",
  "h0 50 32.6; h1 68.1 37.4; h2 81.4 50.7; h3 86.2 68.8; h4 81.4 86.9; h5 68.1 100.2; h6 50 105;"
  "h7 31.9 100.2; h8 18.6 86.9; h9 13.8 68.8; h10 18.6 50.7; h11 31.9 37.4; t0 50 45.3;"
  "t3 73.5 68.8; t6 50 92.3; t9 26.5 68.8; bR1 82.8 26.8; bR2 92 36; bL1 17.2 26.8; bL2 8 36;"
  "hm 50 17.6; fl 20.2 115.7; fr 79.8 115.7; ctr 50 68.8; hh 37.1 61.3; mh 68.5 58.1",
  ["h1 h0 h11 h10 h9 h8 h7 h6 h5 h4 h3 h2 h1 bR1 bR2 h2", "h3 t3", "h5 fr", "h6 t6", "h7 fl",
   "h9 t9", "h10 bL2 bL1 h11", "t0 h0 hm", "hh ctr mh"],
  clue="Five more minutes, please!",
  colors={"orange": ["h0 hm", "h1 bR1 bR2 h2", "h10 bL2 bL1 h11"], "blue": ["hh ctr mh"],
    "white": ["h0 t0", "h3 t3", "h6 t6", "h9 t9"],
    "brown": ["h5 h6 h7 h8 h9 h10 h11 h0 h1 h2 h3 h4 h5 fr", "h7 fl"]})

P("compass", "Compass", "object",
  "c0 50 40.4; c1 71 46.1; c2 86.3 61.4; c3 92 82.4; c4 86.3 103.4; c5 71 118.8; c6 50 124.4;"
  "c7 29 118.8; c8 13.7 103.4; c9 8 82.4; c10 13.7 61.4; c11 29 46.1; o 50 82.4; tn 50 54.1;"
  "te 78.3 82.4; ts 50 110.7; tw 21.7 82.4; v0 59.1 73.3; v1 59.1 91.5; v2 40.9 91.5;"
  "v3 40.9 73.3; k 50 28.3; q1 39.5 21; q2 43.5 8.9; q3 56.5 8.9; q4 60.5 21",
  ["c3 c2 c1 c0 c11 c10 c9 c8 c7 c6 c5 c4 c3 te v0 tn v3 tw v2 ts v1 te o tn c0 k q1 q2 q3 q4 k",
   "c6 ts o tw c9"],
  clue="Always pointing north, never lost",
  colors={"red": ["c0 k q1 q2 q3 q4 k"],
    "blue": ["c0 tn v0 te c3", "c6 ts v2 tw v3 tn o te v1 ts o tw c9"]})

P("dice", "Dice", "object",
  "C 50 66.7; TL 8 42.4; T 50 18.2; TR 92 42.4; BL 8 90.9; B 50 115.2; BR 92 90.9; p0 50 30.8;"
  "p1 60.1 48.2; p2 39.9 48.2; pc 50 42.4; q0 16.5 57.1; q1 26.3 62.8; q2 16.5 68.5;"
  "r0 41.5 100.5; r1 31.7 94.8; r2 41.5 89.1; s0 84.8 54.9; s1 84.8 66.3; s2 75 60.6;"
  "t0 74.3 73.1; t1 74.3 84.5; t2 64.5 78.8; u0 57.2 102.7; u1 57.2 91.3; u2 67.1 97",
  ["C TL T TR C B BL TL", "TR BR B", "p0 p1 p2 p0 pc p1", "p2 pc", "q0 q1 q2 q0",
   "r0 r1 r2 r0", "s0 s1 s2 s0", "t0 t1 t2 t0", "u0 u1 u2 u0"],
  clue="Feeling lucky? Roll with it",
  colors={"red": ["p0 p1 p2 p0 pc p1", "p2 pc", "q0 q1 q2 q0", "r0 r1 r2 r0", "s0 s1 s2 s0", "t0 t1 t2 t0", "u0 u1 u2 u0"],
    "white": ["C TL T TR C B BL TL", "TR BR B"]})

P("octopus", "Octopus", "animal",
  "top 50 20; uL 31.3 26.2; sL 22 43.3; bL 26.7 62; mL 39.1 69.8; mid 50 71.3; eL1 40.7 40.2;"
  "eL2 40.7 52.7; aL1 17.3 80.7; aL2 8 97.8; aL3 20.4 100.9; bL1 32.9 90; bL2 37.6 110.2;"
  "c1 50 93.1; c2 50 113.3; uR 68.7 26.2; sR 78 43.3; bR 73.3 62; mR 60.9 69.8; eR1 59.3 40.2;"
  "eR2 59.3 52.7; aR1 82.7 80.7; aR2 92 97.8; aR3 79.6 100.9; bR1 67.1 90; bR2 62.4 110.2",
  ["bL mL mid mR bR sR uR top uL sL bL aL1 aL2 aL3 aL1", "mL bL1 bL2", "mid c1 c2", "eL1 eL2",
   "bR aR1 aR2 aR3 aR1", "mR bR1 bR2", "eR1 eR2"],
  clue="Eight arms and still can't hug enough",
  colors={"pink": ["top uR sR bR mR mid mL bL sL uL top"],
    "purple": ["bL aL1 aL2 aL3 aL1", "mL bL1 bL2", "mid c1 c2", "bR aR1 aR2 aR3 aR1", "mR bR1 bR2"],
    "white": ["eL1 eL2", "eR1 eR2"]})

P("mushroom2", "Toadstool", "plant",
  "c0 8 65.2; c1 13.6 43.4; c2 29 27.5; c3 50 21.7; c4 71 27.5; c5 86.4 43.4; c6 92 65.2;"
  "u1 30.5 66.7; u3 69.5 66.7; sL 41.7 80.2; sR 58.3 80.2; mL 41 92.2; mR 59 92.2; fL 35 111.7;"
  "fR 65 111.7; p0 50 33.7; p1 59.3 40.4; p2 55.7 51.3; p3 44.3 51.3; p4 40.7 40.4;"
  "a0 26.7 42.7; a1 33.3 53.9; a2 20.2 53.9; b0 73.2 42.7; b1 79.8 53.9; b2 66.7 53.9",
  ["c0 c1 c2 c3 c4 c5 c6 u3 u1 c0 sL sR c6", "u1 sL mL fL fR mR sR u3", "mL mR",
   "p0 p1 p2 p3 p4 p0", "a0 a1 a2 a0", "b0 b1 b2 b0"],
  clue="Fairy furniture, do not eat",
  colors={"red": ["c0 c1 c2 c3 c4 c5 c6 u3 u1 c0 sL sR c6"],
    "white": ["p0 p1 p2 p3 p4 p0", "a0 a1 a2 a0", "b0 b1 b2 b0"],
    "brown": ["u1 sL mL fL fR mR sR u3", "mL mR"]})

P("flag", "Flag", "object",
  "g00 19.3 17; g01 38.7 11.3; g02 56.5 17; g03 74.2 22.6; g04 92 17; g12 56.5 31.5;"
  "g13 74.2 37.2; g14 92 31.5; g20 19.3 46.1; g21 38.7 40.4; g22 56.5 46.1; g23 74.2 51.7;"
  "g24 92 46.1; g30 19.3 60.6; g31 38.7 55; g32 56.5 60.6; g33 74.2 66.3; g34 92 60.6;"
  "g40 19.3 75.1; g41 38.7 69.5; g42 56.5 75.1; g43 74.2 80.8; g44 92 75.1; bot 19.3 122;"
  "bl 8 122; br 30.6 122",
  ["g02 g01 g00 g20 g30 g40 bot bl", "g02 g03 g04 g14 g13 g12 g02", "g12 g22 g21 g20",
   "g14 g24 g23 g22", "g24 g34 g33 g32 g31 g30", "g34 g44 g43 g42 g41 g40", "bot br"],
  clue="Run me up the pole and salute",
  colors={"red": ["g02 g01 g00 g20 g30 g40", "g02 g03 g04 g14 g13 g12 g02", "g24 g34 g33 g32 g31 g30"],
    "white": ["g12 g22 g21 g20", "g14 g24 g23 g22", "g34 g44 g43 g42 g41 g40"],
    "brown": ["g40 bot bl", "bot br"]})

P("laptop", "Laptop", "object",
  "s0 15.3 8; s1 84.7 8; s2 84.7 59.2; s3 15.3 59.2; i0 26.9 18.7; i1 73.1 18.7; i2 73.1 48.5;"
  "i3 26.9 48.5; b0 8.7 125.3; b1 91.3 125.3; k0 23.6 67.5; k1 36.8 67.5; k2 50 67.5;"
  "k3 63.2 67.5; k4 76.4 67.5; m0 21.9 80.7; m4 78.1 80.7; n0 20.3 93.9; n1 36.8 93.9;"
  "n2 50 93.9; n3 63.2 93.9; n4 79.7 93.9; p0 43.4 105.5; p1 56.6 105.5; p2 56.6 117.1;"
  "p3 43.4 117.1",
  ["s2 s1 s0 s3 s2 b1 b0 s3", "k1 k0 m0 n0 n1 n2 n3 n4 m4 k4 k3 k2 k1 n1", "k2 n2", "k3 n3",
   "m0 m4", "i0 i1 i2 i3 i0", "p0 p1 p2 p3 p0"],
  clue="Ctrl+Alt+Del my way to your lap",
  colors={"blue": ["i0 i1 i2 i3 i0"],
    "cyan": ["k1 k0 m0 n0 n1 n2 n3 n4 m4 k4 k3 k2 k1 n1", "k2 n2", "k3 n3", "m0 m4"],
    "white": ["s2 s1 s0 s3 s2 b1 b0 s3", "p0 p1 p2 p3 p0"]})

P("penguin", "Penguin", "animal",
  "top 50 16.1; o1L 36 22.3; o2L 26.7 36.3; o3L 22 56.6; o4L 23.6 83; o5L 34.4 103.2;"
  "bot 50 107.9; fL 8 87.7; vn 50 41; i1L 40.7 33.2; i2L 32.9 59.7; bk1 43.8 51.9;"
  "bk2 56.2 51.9; bk3 50 62.8; tL 28.2 117.2; t2L 43.8 117.2; o1R 64 22.3; o2R 73.3 36.3;"
  "o3R 78 56.6; o4R 76.4 83; o5R 65.6 103.2; fR 92 87.7; i1R 59.3 33.2; i2R 67.1 59.7;"
  "tR 71.8 117.2; t2R 56.2 117.2",
  ["o3L o2L o1L top o1R o2R o3R o4R o5R bot o5L o4L o3L fL o4L", "o3R fR o4R",
   "o2L i1L vn i1R o2R i2R o5R tR t2R bot t2L tL o5L i2L o2L", "bk1 bk2 bk3 bk1"],
  clue="Always dressed for a black-tie event",
  colors={"orange": ["o5L tL t2L bot t2R tR o5R"],
    "blue": ["o3L o2L o1L top o1R o2R o3R o4R o5R bot o5L o4L o3L fL o4L", "o3R fR o4R"],
    "white": ["o5L i2L o2L i1L vn i1R o2R i2R o5R", "bk1 bk2 bk3 bk1"]})

P("robot", "Robot", "object",
  "an 50 13.8; ab 50 25.4; htL 26.8 25.4; hbL 26.8 64.5; btL 15.2 64.5; bbL 15.2 103.6;"
  "lgL 35.5 103.6; ftL 35.5 119.5; hdL 8 93.5; e1L 32.6 35.5; e2L 44.2 35.5; e3L 44.2 47.1;"
  "e4L 32.6 47.1; mL 38.4 57.3; htR 73.2 25.4; hbR 73.2 64.5; btR 84.8 64.5; bbR 84.8 103.6;"
  "lgR 64.5 103.6; ftR 64.5 119.5; hdR 92 93.5; e1R 67.4 35.5; e2R 55.8 35.5; e3R 55.8 47.1;"
  "e4R 67.4 47.1; mR 61.6 57.3",
  ["an ab htL hbL hbR htR ab", "hbL btL bbL lgL lgR bbR btR hbR", "btL hdL", "lgL ftL",
   "mL mR", "btR hdR", "lgR ftR", "e1L e2L e3L e4L e1L", "e1R e2R e3R e4R e1R"],
  clue="Beep boop, I come in peace",
  colors={"orange": ["btL hdL", "lgL ftL", "btR hdR", "lgR ftR"],
    "red": ["e1L e2L e3L e4L e1L", "e1R e2R e3R e4R e1R"],
    "cyan": ["an ab htL hbL hbR htR ab", "hbL btL bbL lgL lgR bbR btR hbR"], "green": ["mL mR"]})

P("snowman", "Snowman", "object",
  "bmL 29 32.2; bmR 71 32.2; crL 41.7 32.2; crR 58.3 32.2; ctL 41.7 9.7; ctR 58.3 9.7;"
  "sL 24.5 50.2; sR 75.5 50.2; nkL 38.7 66.7; nkR 61.3 66.7; nm 50 66.7; b1L 23 81.7;"
  "b1R 77 81.7; b2L 15.5 102.7; b2R 84.5 102.7; b3L 35 123.7; b3R 65 123.7; hdL 9.5 71.2;"
  "hdR 90.5 71.2; fgL 8 56.2; fgR 92 56.2; nb1 47 42.7; nb2 47 54.7; ntip 81.5 62.2;"
  "bt1 50 84.7; bt2 50 102.7",
  ["crL bmL sL nkL nm nkR sR bmR crR crL ctL ctR crR", "nkL b1L b2L b3L b3R b2R b1R nkR",
   "nm bt1 bt2", "b1L hdL fgL", "b1R hdR fgR", "nb1 nb2 ntip nb1"],
  clue="Chilling out until spring",
  colors={"orange": ["nm bt1 bt2"], "red": ["nkL nm nkR"],
    "white": ["crL bmL sL nkL b1L b2L b3L b3R b2R b1R nkR sR bmR crR crL ctL ctR crR"],
    "brown": ["b1L hdL fgL", "b1R hdR fgR", "nb1 nb2 ntip nb1"]})

P("daisy", "Daisy", "plant",
  "c0 50 59.4; t0l 41.3 80.3; t0r 30.6 75.9; c1 39.2 54.9; t1l 18.3 63.6; t1r 13.8 52.9;"
  "c2 34.8 44.2; t2l 13.8 35.5; t2r 18.3 24.7; c3 39.2 33.4; t3l 30.6 12.4; t3r 41.3 8;"
  "c4 50 29; t4l 58.7 8; t4r 69.4 12.4; c5 60.8 33.4; t5l 81.7 24.7; t5r 86.2 35.5;"
  "c6 65.2 44.2; t6l 86.2 52.9; t6r 81.7 63.6; c7 60.8 54.9; t7l 69.4 75.9; t7r 58.7 80.3;"
  "Lb 50 100; S 50 125.3; Lt 77.1 93.2; Ls 68.6 111.8",
  ["c0 t0l t0r c1 t1l t1r c2 t2l t2r c3 t3l t3r c4 t4l t4r c5 t5l t5r c6 t6l t6r c7 t7l t7r c0 c1 c2 c3 c4 c5 c6 c7 c0 Lb S",
   "Lb Lt Ls Lb"],
  clue="He loves me, he loves me not...",
  colors={"green": ["Lb Lt Ls Lb"],
    "white": ["c0 t0l t0r c1 t1l t1r c2 t2l t2r c3 t3l t3r c4 t4l t4r c5 t5l t5r c6 t6l t6r c7 t7l t7r c0"],
    "brown": ["c0 Lb S"]})

P("trophy", "Trophy", "object",
  "rL 20 15.7; rR 80 15.7; bdL 21.5 27.7; bdR 78.5 27.7; c1L 26 44.2; c1R 74 44.2; c2L 35 56.2;"
  "c2R 65 56.2; nL 44 65.2; nR 56 65.2; h1L 8 18.7; h1R 92 18.7; h2L 8 35.2; h2R 92 35.2;"
  "h3L 12.5 48.7; h3R 87.5 48.7; sL 44 77.2; sR 56 77.2; btL 30.5 90.7; btR 69.5 90.7;"
  "bbL 30.5 117.7; bbR 69.5 117.7; pqL 41 98.2; pqR 59 98.2; pbL 41 110.2; pbR 59 110.2",
  ["rL rR bdR c1R c2R nR sR btR bbR bbL btL sL nL c2L c1L bdL rL h1L h2L h3L c2L",
   "rR h1R h2R h3R c2R", "bdL bdR", "nL nR", "sL sR", "btL btR", "pqL pqR pbR pbL pqL"],
  clue="Winner winner, chicken dinner",
  colors={"orange": ["rL rR bdR c1R c2R nR", "rL bdL c1L c2L nL", "rL h1L h2L h3L c2L", "rR h1R h2R h3R c2R", "bdL bdR"],
    "white": ["pqL pqR pbR pbL pqL"], "brown": ["btL bbL bbR btR btL"]})

P("spider", "Spider", "animal",
  "c0 50 55.8; c1 60.3 63.3; c2 56.4 75.5; c3 43.6 75.5; c4 39.7 63.3; thr 50 15.3; aL 36 91.6;"
  "aBL 42.2 113.3; k1L 32.9 41.8; f1L 17.3 32.4; k2L 23.6 55.8; f2L 8 71.3; k3L 20.4 76;"
  "f3L 8 94.7; k4L 23.6 96.2; f4L 20.4 118; aR 64 91.6; aBR 57.8 113.3; k1R 67.1 41.8;"
  "f1R 82.7 32.4; k2R 76.4 55.8; f2R 92 71.3; k3R 79.6 76; f3R 92 94.7; k4R 76.4 96.2;"
  "f4R 79.6 118",
  ["c0 thr", "c0 c1 c2 c3 c4 c0", "c2 aR aBR aBL aL c3 k3L f3L", "c2 k3R f3R", "c2 k4R f4R",
   "c3 k4L f4L", "aL aR", "f1L k1L c4 k2L f2L", "f1R k1R c1 k2R f2R"],
  clue="Along came one and sat down beside her",
  colors={"purple": ["c2 aR aBR aBL aL c3", "aL aR"], "white": ["c0 thr"],
    "brown": ["f1L k1L c4 c3 c2 c1 c0 c4 k2L f2L", "f3L k3L c3 k4L f4L", "f1R k1R c1 k2R f2R", "f3R k3R c2 k4R f4R"]})

P("violin", "Violin", "object",
  "SC 50 8; P1L 43 17.9; PBL 44 31.9; NBL 44 51.8; UBL 20.2 65.7; C2L 25.1 81.6; C1L 25.1 97.5;"
  "LWL 13.2 109.4; LBL 26.1 122.4; B 50 125.3; FEL 44 79.6; BRL 44 96.5; FaL 35.1 86.6;"
  "FbL 33.1 105.4; PBR 56 31.9; NBR 56 51.8; UBR 79.8 65.7; C2R 74.9 81.6; C1R 74.9 97.5;"
  "LWR 86.8 109.4; LBR 73.9 122.4; FER 56 79.6; BRR 56 96.5; FaR 64.9 86.6; FbR 66.9 105.4;"
  "S2 59.9 16",
  ["FEL NBL UBL C2L C1L LWL LBL B LBR LWR C1R C2R UBR NBR NBL PBL P1L SC S2 PBR NBR FER BRR B BRL FEL FER",
   "BRL BRR", "FaL FbL", "FaR FbR"],
  clue="Chin up, bow ready!",
  colors={"purple": ["FaL FbL", "FaR FbR"], "white": ["BRL BRR"],
    "brown": ["FEL NBL UBL C2L C1L LWL LBL B LBR LWR C1R C2R UBR NBR NBL PBL P1L SC S2 PBR NBR FER BRR B BRL FEL FER"]})

P("bat", "Bat", "animal",
  "earTipL 42.8 23.2; earValley 50 31.9; earTipR 57.2 23.2; eyeL 42.8 40.6; eyeR 57.2 40.6;"
  "jawL 29.7 40.6; jawR 70.3 40.6; shL 19.6 46.4; shR 80.4 46.4; wristL 15.2 58; wristR 84.8 58;"
  "tip1L 8 69.6; tip1R 92 69.6; valleyL 25.4 75.4; valleyR 74.6 75.4; tip2L 21 89.8;"
  "tip2R 79 89.8; bodyBottom 50 97.1; footL 44.2 110.1; footR 55.8 110.1",
  ["valleyL tip2L bodyBottom tip2R valleyR tip1R wristR shR jawR earTipR earValley earTipL jawL shL wristL tip1L valleyL wristL tip2L",
   "valleyR wristR tip2R", "footL bodyBottom footR", "earValley eyeL eyeR earValley"],
  clue="Hangs out upside down all day",
  colors={"purple": ["wristL tip1L valleyL tip2L bodyBottom tip2R valleyR tip1R wristR valleyR", "wristL valleyL", "wristL tip2L", "wristR tip2R"],
    "white": ["earValley eyeL eyeR earValley"],
    "brown": ["wristL shL jawL earTipL earValley earTipR jawR shR wristR", "footL bodyBottom footR"]})

P("key2", "Key", "object",
  "bo_top 22.8 43.8; bo_tr 37.6 54.9; bo_br 37.6 75.9; bo_bot 22.8 87; bo_bl 8 75.9;"
  "bo_tl 8 54.9; in_t 22.8 56.2; in_r 30.2 65.4; in_b 22.8 74.7; in_l 15.4 65.4;"
  "st_mid 53.7 54.9; st2 67.3 54.9; tip 85.8 54.9; sb_mid 53.7 75.9; c1 64.8 75.9; c2 64.8 89.5;"
  "c3 75.9 89.5; c4 75.9 75.9; tipB 92 75.9",
  ["bo_top bo_tr bo_br bo_bot bo_bl bo_tl bo_top in_t in_r in_b in_l in_t",
   "bo_tr st_mid st2 tip tipB c4 c3 c2 c1 sb_mid bo_br", "bo_bot in_b", "st2 c4"],
  clue="I open more doors than I close",
  colors={"orange": ["bo_top bo_tr bo_br bo_bot bo_bl bo_tl bo_top"],
    "cyan": ["bo_tr st_mid st2 tip tipB c4 c3 c2 c1 sb_mid bo_br", "st2 c4"],
    "white": ["bo_top in_t in_r in_b in_l in_t", "bo_bot in_b"]})

P("bee", "Bee", "animal",
  "hd_t 18.1 65.2; hd_b 18.1 84; ant1 8 53.6; ant2 31.2 46.4; bt1 29.7 58; bt2 42.8 55.1;"
  "bt3 55.8 55.1; bt4 68.8 58; tail 80.4 72.5; bb4 68.8 89.8; bb3 55.8 94.2; bb2 42.8 94.2;"
  "bb1 29.7 89.8; st_tip 92 72.5; leg1 29.7 107.2; leg2 42.8 107.2; leg3 55.8 107.2;"
  "w1a 39.9 31.9; w1b 60.1 26.1; w1c 67.4 40.6; w1d 50 44.9",
  ["ant1 hd_t bt1 bt2 bt3 bt4 tail bb4 bb3 bb2 bb1 hd_b hd_t ant2", "bt2 bb2 leg2",
   "tail st_tip", "bb1 leg1", "leg3 bb3 bt3 w1d w1c w1b w1a w1d"],
  clue="Buzz off, I'm busy!",
  colors={"orange": ["ant1 hd_t bt1 bt2 bt3 bt4 tail bb4 bb3 bb2 bb1 hd_b hd_t ant2"],
    "white": ["bt3 w1d w1c w1b w1a w1d"], "brown": ["bt2 bb2 leg2", "bt3 bb3 leg3"]})

P("tent", "Tent", "object",
  "apex 50 34.3; ridgeL 38.6 58.4; ridgeR 61.4 58.4; guyTopL 29.6 77.6; guyTopR 70.4 77.6;"
  "baseL 21.6 94.5; baseR 78.4 94.5; stakeL 8 94.5; stakeR 92 94.5; doorBaseL 38.6 94.5;"
  "doorBaseR 61.4 94.5; groundMid 50 94.5; tuftTip 50 107; zip1 43.2 70.4; zip2 56.8 70.4;"
  "flagA 61.4 26.4; flagB 61.4 43.4; flagA2 38.6 26.4; flagB2 38.6 43.4",
  ["ridgeL apex ridgeR guyTopR baseR doorBaseR groundMid doorBaseL baseL guyTopL ridgeL ridgeR",
   "guyTopL stakeL baseL", "guyTopR stakeR baseR", "doorBaseL zip1 apex zip2 doorBaseR",
   "groundMid tuftTip", "zip1 zip2", "apex flagA flagB apex flagA2 flagB2 apex"],
  clue="Home away from home, zipped shut",
  colors={"orange": ["ridgeL apex ridgeR guyTopR baseR doorBaseR groundMid doorBaseL baseL guyTopL ridgeL ridgeR"],
    "red": ["apex flagA flagB apex flagA2 flagB2 apex"],
    "white": ["guyTopL stakeL baseL", "guyTopR stakeR baseR", "groundMid tuftTip"],
    "brown": ["doorBaseL zip1 apex zip2 doorBaseR", "zip1 zip2"]})

P("strawberry", "Strawberry", "plant",
  "tL 18.7 54.2; tR 81.3 54.2; mL 8 70.2; mR 92 70.2; bL 30.3 98.8; bR 69.7 98.8; tip 50 123.9;"
  "bB 33.9 36.3; midC 50 30.9; bD 66.1 36.3; lt1 12.5 39.9; lt2 41.1 23.8; lt3 58.9 23.8;"
  "lt4 87.5 39.9; stem 50 16.6; stemCurl 64.3 9.5; seedA 23.2 73.8; seedB 39.3 82.8;"
  "seedC 60.7 82.8; seedD 76.8 73.8",
  ["tL mL bL tip bR mR tR tL lt1 bB lt2 midC lt3 bD lt4 tR", "mL seedA seedB seedC seedD mR",
   "midC stem stemCurl"],
  clue="Sweet, red, and covered in freckles",
  colors={"red": ["tL mL bL tip bR mR tR tL"],
    "green": ["tL lt1 bB lt2 midC lt3 bD lt4 tR", "midC stem stemCurl"],
    "white": ["mL seedA seedB seedC seedD mR"]})

P("hedgehog", "Hedgehog", "animal",
  "snoutTop 28.3 57.4; foreheadTop 37.2 46.8; p1 41.6 36.2; v1 47.8 50.3; p2 54 35.3;"
  "v2 58.4 54.7; p3 67.2 34.4; v3 69.9 56.5; p4 77.9 40.6; v4 81.4 57.4; p5 89.3 46.8;"
  "tailTip 92 62.7; hip 78.7 75.1; belly3 67.2 83.9; belly2 53.1 86.6; belly1 39.8 83.9;"
  "chin 26.6 79.5; snoutTip 18.6 70.6; eye 39.8 58.3; whisker 8 75.1; leg1 39.8 96.3;"
  "leg2 53.1 98.9; leg3 67.2 96.3; leg4 83.2 87.4",
  ["snoutTop foreheadTop p1 v1 p2 v2 p3 v3 p4 v4 p5 tailTip hip belly3 belly2 belly1 chin snoutTip snoutTop eye",
   "v1 belly1 leg1", "v2 belly2 leg2", "v3 belly3 leg3", "v4 hip leg4", "snoutTip whisker"],
  clue="Please don't pet the pointy stranger",
  colors={"orange": ["foreheadTop snoutTop snoutTip chin belly1 belly2 belly3 hip tailTip"],
    "white": ["snoutTop eye", "snoutTip whisker"],
    "brown": ["foreheadTop p1 v1 p2 v2 p3 v3 p4 v4 p5 tailTip", "v1 belly1 leg1", "v2 belly2 leg2", "v3 belly3 leg3", "v4 hip leg4"]})

P("microphone", "Microphone", "object",
  "hTL 43.7 8; hTR 72.2 8; hBR 72.2 31; hBL 43.7 31; midL 43.7 19.5; midR 72.2 19.5;"
  "neckL 47 44.2; neckR 68.9 44.2; bandL 47 56.2; bandR 68.9 56.2; handleBL 45.9 77.1;"
  "handleBR 70 77.1; standTop 58 77.1; poleBottom 58 89.1; legL 44.8 100.1; legC 58 101.8;"
  "legR 71.1 100.1; btnL 17.4 57.9; btnR 30.5 57.9; cable2 79.9 110; cable3 71.7 118.2;"
  "cable4 82.6 125.3",
  ["hTL midL hBL hBR midR hTR hTL hBR neckR bandR handleBR standTop handleBL bandL neckL hBL hTR",
   "midL midR", "bandL bandR", "standTop poleBottom legL",
   "legR poleBottom legC cable2 cable3 cable4", "btnL btnR"],
  clue="Is this thing on?",
  colors={"red": ["btnL btnR"],
    "blue": ["hBR neckR bandR handleBR standTop handleBL bandL neckL hBL", "bandL bandR"],
    "white": ["hTL midL hBL hBR midR hTR hTL hBR", "hTR hBL", "midL midR"],
    "brown": ["standTop poleBottom legL", "legR poleBottom legC cable2 cable3 cable4"]})

P("frog", "Frog", "animal",
  "snout 89.2 55.1; hTop 76.7 36.2; eyeTop 64.1 20.5; pupil 64.1 8; eyeBack 51.6 33.1;"
  "backTop 39 26.8; rearSlope 26.5 39.4; hip 17.1 55.1; belly 54.7 70.7; chin 79.8 61.3;"
  "fKnee 67.3 83.3; fFoot 54.7 95.8; fToe1 35.9 111.5; fToe2 69.1 111.5; thigh 10.8 70.7;"
  "knee 23.3 89.6; ankle 39 99; foot 57.8 114.7; toeA 45.3 122.8; toeB 71.6 125.3",
  ["eyeTop hTop snout chin belly hip rearSlope backTop eyeBack eyeTop pupil",
   "hip thigh knee ankle foot toeA", "belly fKnee fFoot fToe1", "fFoot fToe2", "foot toeB"],
  clue="Ribbiting good time",
  colors={"green": ["hip belly chin snout hTop eyeTop eyeBack backTop rearSlope hip thigh knee ankle foot", "belly fKnee fFoot"],
    "white": ["eyeTop pupil"]})

P("candle", "Candle", "object",
  "flameTip 50 8; flameL 40.4 25.7; flameR 59.6 25.7; flameBase 50 35.3; dripL_top 40.4 51.7;"
  "dripR_top 59.6 51.7; dripL_bulge 21.3 63.9; dripL_tip 30.9 73.5; dripR_bulge 78.7 63.9;"
  "dripR_tip 69.1 73.5; botL 40.4 83; botR 59.6 83; plateL 22.7 95.3; plateR 77.3 95.3;"
  "footTop 50 95.3; footBase 50 114.4; footL 36.4 125.3; footR 63.6 125.3",
  ["botL dripL_top flameBase flameR flameTip flameL flameBase dripR_top dripR_bulge dripR_tip dripR_top botR botL plateL footTop plateR botR",
   "footTop footBase footL", "footBase footR", "dripL_top dripL_bulge dripL_tip dripL_top"],
  clue="Make a wish before I burn out",
  colors={"orange": ["flameTip flameR flameBase flameL flameTip"],
    "white": ["flameBase dripL_top botL botR dripR_top flameBase", "dripL_top dripL_bulge dripL_tip dripL_top", "dripR_top dripR_bulge dripR_tip dripR_top"],
    "brown": ["botL plateL footTop plateR botR", "footTop footBase footL", "footBase footR"]})

P("deer", "Deer", "animal",
  "rumpTop 20.5 64.5; midBack 40.4 57.1; shoulderTop 59.6 60; neckBack 68.4 51.2;"
  "headTop 77.3 43.8; snout 90.5 48.2; chin 81.7 55.6; throat 74.3 65.9; chestFront 62.5 75.5;"
  "bellyMid 40.4 80.7; rumpBottom 22.7 79.2; earTip 66.9 33.5; antlerBase 83.2 32;"
  "tineL 71.4 20.2; tineR 92 21.7; tailTip 8 74.8; maneTip1 47.8 46.8; nostrilTip 92 60;"
  "flKnee 71.4 89.5; flHoof 71.4 107.2; frKnee 56.6 93.9; frHoof 56.6 111.6; blKnee 16.8 93.9;"
  "blHoof 16.8 111.6; brKnee 31.6 95.4; brHoof 31.6 113.1",
  ["rumpTop midBack shoulderTop neckBack headTop snout chin throat chestFront bellyMid rumpBottom rumpTop tailTip",
   "shoulderTop maneTip1", "chin nostrilTip", "earTip headTop antlerBase tineL",
   "antlerBase tineR", "flHoof flKnee chestFront frKnee frHoof",
   "blHoof blKnee rumpBottom brKnee brHoof"],
  clue="Feeling a bit antler-social",
  colors={"orange": ["rumpTop midBack shoulderTop neckBack headTop snout chin throat chestFront bellyMid rumpBottom rumpTop"],
    "white": ["rumpTop tailTip", "shoulderTop maneTip1", "chin nostrilTip"],
    "brown": ["earTip headTop antlerBase tineL", "antlerBase tineR", "flHoof flKnee chestFront frKnee frHoof", "blHoof blKnee rumpBottom brKnee brHoof"]})

P("television", "Television", "object",
  "outerTL 15 37.9; antBase 50 37.9; outerTR 85 37.9; outerBR 85 100.1; outerBL 15 100.1;"
  "screenTL 28.2 51.1; screenTR 46.9 51.1; screenBR 46.9 86.9; screenBL 28.2 86.9;"
  "antTipL 32.9 20; antTipR 65.6 24.7; knobTop 67.1 48; knobRight 76.4 57.3;"
  "knobBottom 67.1 66.7; knobLeft 57.8 57.3; lightTip 67.1 79.1; footL 8 113.3; footR 92 113.3",
  ["outerBR outerTR antBase outerTL outerBL outerBR footR", "outerBL footL",
   "screenTL screenTR screenBR screenBL screenTL screenBR", "screenTR screenBL",
   "antTipL antBase antTipR", "knobBottom knobRight knobTop knobLeft knobBottom lightTip"],
  clue="Way before your phone stole the show",
  colors={"red": ["knobBottom knobRight knobTop knobLeft knobBottom lightTip"],
    "cyan": ["screenTL screenTR screenBR screenBL screenTL screenBR", "screenTR screenBL"],
    "white": ["antTipL antBase antTipR"],
    "brown": ["outerBR outerTR antBase outerTL outerBL outerBR footR", "outerBL footL"]})

P("lemon", "Lemon", "plant",
  "topTip 60.1 24.2; tl1 47.8 30.3; tl2 39.9 44.9; tl3 38.8 60.5; tl4 45.5 75;"
  "bottomTip 60.1 86.2; tr4 74.6 75; tr3 81.3 60.5; tr2 80.2 44.9; tr1 72.3 30.3;"
  "stemTip 60.1 10.2; leafBase 71.2 13.6; leafTip1 82.4 8; leafTip2 81.3 23.6;"
  "markTip 60.1 98.5; sliceCenter 32.1 110.8; rim1 32.1 96.3; rim2 46.6 110.8; rim3 32.1 125.3;"
  "rim4 17.6 110.8",
  ["bottomTip tl4 tl3 tl2 tl1 topTip tr1 tr2 tr3 tr4 bottomTip markTip",
   "stemTip topTip leafBase leafTip1", "leafBase leafTip2",
   "rim1 sliceCenter rim2 rim1 rim4 sliceCenter rim3 rim2", "rim3 rim4"],
  clue="When life gives you me, make a drink",
  colors={"green": ["stemTip topTip leafBase leafTip1", "leafBase leafTip2"],
    "white": ["rim1 sliceCenter rim2 rim1 rim4 sliceCenter rim3 rim2", "rim3 rim4"],
    "brown": ["bottomTip markTip"]})

P("horse", "Horse", "animal",
  "rumpTop 28.4 60.5; midBack 45.1 54.3; shoulderTop 61.1 56.2; neckBack 69.8 48.8;"
  "headTop 79.6 40.7; snout 92 45.7; chin 83.4 53.1; throat 74.7 61.7; chestFront 64.8 70.4;"
  "bellyMid 45.1 74.7; rumpBottom 30.2 72.8; earL 71 30.8; earR 85.8 30.8; maneTip1 52.5 45.7;"
  "maneTip2 62.4 39.5; tailMid 16.6 71.6; tailTip1 8 63; tailTip2 9.2 81.5; flKnee 72.2 82.7;"
  "flHoof 72.2 97.5; frKnee 59.9 86.4; frHoof 59.9 101.3; blKnee 25.3 86.4; blHoof 25.3 101.3;"
  "brKnee 37.6 87.7; brHoof 37.6 102.5",
  ["rumpTop midBack shoulderTop neckBack headTop snout chin throat chestFront bellyMid rumpBottom rumpTop tailMid tailTip1",
   "shoulderTop maneTip1", "neckBack maneTip2", "earL headTop earR", "tailMid tailTip2",
   "flHoof flKnee chestFront frKnee frHoof", "blHoof blKnee rumpBottom brKnee brHoof"],
  clue="Straight from its mouth, they say",
  colors={"white": ["rumpTop tailMid tailTip1", "shoulderTop maneTip1", "neckBack maneTip2", "tailMid tailTip2"],
    "brown": ["earL headTop neckBack shoulderTop midBack rumpTop rumpBottom bellyMid chestFront throat chin snout headTop earR", "flHoof flKnee chestFront frKnee frHoof", "blHoof blKnee rumpBottom brKnee brHoof"]})

P("car", "Car", "object",
  "rearBumper 14.1 67.3; trunkTop 20.2 42.9; roofBack 37.2 25.9; doorTop 50.6 25.9;"
  "roofFront 64 25.9; hoodTop 79.8 42.9; frontBumper 85.9 67.3; rockerFront 75 72.1;"
  "rockerMid 49.4 72.1; rockerRear 25 72.1; mirrorTip 85.9 30.8; hubF 79.8 95.3;"
  "rimFtop 79.8 83.1; rimFright 92 95.3; rimFbottom 79.8 107.4; rimFleft 67.7 95.3;"
  "hubR 20.2 95.3; rimRtop 20.2 83.1; rimRright 32.3 95.3; rimRbottom 20.2 107.4;"
  "rimRleft 8 95.3",
  ["doorTop roofBack trunkTop rearBumper rockerRear rockerMid rockerFront frontBumper hoodTop roofFront doorTop rockerMid",
   "hoodTop mirrorTip", "rimFtop hubF rimFright rimFtop rimFleft hubF rimFbottom rimFright",
   "rimFbottom rimFleft", "rimRtop hubR rimRright rimRtop rimRleft hubR rimRbottom rimRright",
   "rimRbottom rimRleft"],
  clue="Beep beep, coming through",
  colors={"red": ["doorTop roofBack trunkTop rearBumper rockerRear rockerMid rockerFront frontBumper hoodTop roofFront doorTop rockerMid", "hoodTop mirrorTip"],
    "white": ["rimFtop hubF rimFright rimFtop rimFleft hubF rimFbottom rimFright", "rimFbottom rimFleft", "rimRtop hubR rimRright rimRtop rimRleft hubR rimRbottom rimRright", "rimRbottom rimRleft"]})

P("seagull", "Seagull", "animal",
  "wTipL 18.3 58.4; primary1L 8 62.5; wBendL 34.1 43.9; covertL 28.7 31.5; wRootL 38.2 68.3;"
  "bodyC 47.3 78.3; wRootR 56.4 68.3; wBendR 60.6 43.9; covertR 65.9 31.5; wTipR 76.3 58.4;"
  "primary1R 88.7 54.3; neck 68 77; headTop 79.6 70; eye 88.7 79.1; beakTip 92 66.7;"
  "tailTip 47.3 93.6; tailForkA 37 101.8; tailForkB 57.7 101.8",
  ["primary1L wTipL wBendL wRootL bodyC wRootR wBendR wTipR primary1R", "wBendL covertL",
   "wBendR covertR", "headTop neck bodyC tailTip tailForkA", "headTop beakTip", "headTop eye",
   "tailTip tailForkB"],
  clue="Soaring over the boardwalk chips",
  colors={"orange": ["headTop beakTip"], "blue": ["primary1L wTipL wBendL", "wBendR wTipR primary1R"],
    "cyan": ["wBendL covertL", "wBendR covertR"],
    "white": ["wBendL wRootL bodyC wRootR wBendR", "headTop neck bodyC tailTip tailForkA", "tailTip tailForkB"]})

P("snowflake", "Snowflake", "object",
  "hub 50 66.7; mid0 69.4 66.7; tip0 92 66.7; t0a 81.4 74.8; t0b 81.4 58.5; mid1 59.7 83.5;"
  "tip1 71 103; t1a 58.7 98; t1b 72.8 89.8; mid2 40.3 83.5; tip2 29 103; t2a 27.2 89.8;"
  "t2b 41.3 98; mid3 30.6 66.7; tip3 8 66.7; t3a 18.6 58.5; t3b 18.6 74.8; mid4 40.3 49.9;"
  "tip4 29 30.3; t4a 41.3 35.4; t4b 27.2 43.5; mid5 59.7 49.9; tip5 71 30.3; t5a 72.8 43.5;"
  "t5b 58.7 35.4",
  ["tip0 mid0 hub mid1 tip1", "t0a mid0 t0b", "t1a mid1 t1b", "tip2 mid2 hub mid3 tip3",
   "t2a mid2 t2b", "t3a mid3 t3b", "tip4 mid4 hub mid5 tip5", "t4a mid4 t4b", "t5a mid5 t5b"],
  clue="No two of us are ever alike",
  colors={"blue": ["t0a mid0 t0b", "t1a mid1 t1b", "t2a mid2 t2b", "t3a mid3 t3b", "t4a mid4 t4b", "t5a mid5 t5b"],
    "cyan": ["mid0 tip0", "mid1 tip1", "mid2 tip2", "mid3 tip3", "mid4 tip4", "mid5 tip5"],
    "white": ["mid0 hub mid1", "mid2 hub mid3", "mid4 hub mid5"]})

P("bird", "Bird", "animal",
  "b0 76.7 61.8; b1 70.6 79.3; b2 55.9 86.5; b3 41.2 79.3; b4 35.1 61.8; b5 41.2 44.4;"
  "b6 55.9 37.1; b7 70.6 44.4; beakTip 92 64.6; eyeDot 84.9 50.1; tailTip1 23.3 41.2;"
  "tailTip2 36.5 26.8; wingBase 24.9 83.7; feather1 14 96.6; feather2 8 83.7; feather3 14 70.7;"
  "footL 46.5 106.5; footR 65.2 106.5; branchL 27 106.5; branchR 84.7 106.5",
  ["b3 b2 b1 b0 b7 b6 b5 b4 b3 wingBase feather1", "beakTip b0 eyeDot", "tailTip1 b5 tailTip2",
   "feather2 wingBase feather3", "footL branchL", "footL footR branchR", "footL b2 footR"],
  clue="Tweet me on the branch, not online",
  colors={"orange": ["beakTip b0 eyeDot"],
    "blue": ["b3 wingBase feather1", "feather2 wingBase feather3"],
    "brown": ["tailTip1 b5 b6 b7 b0 b1 b2 b3 b4 b5 tailTip2", "footL branchL", "footL footR branchR", "footL b2 footR"]})

P("donut", "Donut", "object",
  "o0 92 66.7; i0 70.5 66.7; o1 79.7 96.4; i1 64.5 81.2; o2 50 108.7; i2 50 87.2; o3 20.3 96.4;"
  "i3 35.5 81.2; o4 8 66.7; i4 29.5 66.7; o5 20.3 37; i5 35.5 52.1; o6 50 24.7; i6 50 46.1;"
  "o7 79.7 37; i7 64.5 52.1; s0a 81 73.5; s0b 76.7 83.8; s1a 43.2 97.7; s1b 32.9 93.4;"
  "s2a 19 59.9; s2b 23.3 49.5; s3a 56.8 35.6; s3b 67.1 39.9",
  ["o0 i0 i1 o1 o0 o7 i7 i6 o6 o5 i5 i4 o4 o3 i3 i2 o2 o1", "i0 i7", "i1 i2", "o2 o3", "i3 i4",
   "o4 o5", "i5 i6", "o6 o7", "s0a s0b", "s1a s1b", "s2a s2b", "s3a s3b"],
  clue="Squeeze the middle, it's still there",
  colors={"orange": ["s0a s0b", "s2a s2b"], "pink": ["i0 i1 i2 i3 i4 i5 i6 i7 i0"],
    "blue": ["s1a s1b", "s3a s3b"], "brown": ["o0 o1 o2 o3 o4 o5 o6 o7 o0"]})

P("grapes", "Grapes", "plant",
  "g0 50 52.8; g1l 37.9 70.9; g1r 62.1 70.9; g2l 25.8 89; g2m 50 89; g2r 74.2 89;"
  "g3a 13.7 107.2; g3b 37.9 107.2; g3c 62.1 107.2; g3d 86.3 107.2; g4a 25.8 125.3; g4b 50 125.3;"
  "g4c 74.2 125.3; stem1 50 28.6; leafTop 31.9 8; leafTip 13.7 16.5; leafBot 28.2 29.8;"
  "leafTop2 68.1 8; leafTip2 86.3 16.5; leafBot2 71.8 29.8",
  ["g0 g1l g2l g3a g4a g3b g2l", "g0 g1r g2m g1l",
   "g0 stem1 leafTop leafTip leafBot stem1 leafTop2 leafTip2 leafBot2 stem1",
   "g1r g2r g3c g2m g3b g4b g3c g4c g3d g2r", "g4a g4b g4c"],
  clue="Squash me and wait a few years",
  colors={"purple": ["g1l g0 g1r g2m g1l g2l g3a g4a g3b g2l", "g1r g2r g3c g2m g3b g4b g3c g4c g3d g2r", "g4a g4b g4c"],
    "green": ["g0 stem1 leafTop leafTip leafBot stem1 leafTop2 leafTip2 leafBot2 stem1"]})

P("lizard", "Lizard", "animal",
  "snoutTip 92 63.7; headTop 83 45.7; napeTop 71 39.7; spineMid 56 42.7; hipTop 41 49.9;"
  "tailBase 30.8 60.7; belly3 41 73.9; belly2 59 77.5; belly1 75.2 70.3; jaw 86 75.1;"
  "tail1 20 51.7; tail2 11 63.7; tailTip 8 78.7; eye 78.8 30.7; spike1 53 25.9; spike2 35 33.7;"
  "flKnee 83 87.7; flFoot 74 99.7; flToe1 60.8 107.5; flToe2 84.8 107.5; blKnee 23 75.7;"
  "blFoot 32 89.5; blToe1 23 96.7; blToe2 42.8 97.9",
  ["headTop snoutTip jaw belly1 belly2 belly3 tailBase hipTop spineMid napeTop headTop eye",
   "spineMid spike1", "hipTop spike2", "belly1 flKnee flFoot flToe1",
   "tailTip tail2 tail1 tailBase blKnee blFoot blToe1", "flFoot flToe2", "blFoot blToe2"],
  clue="Sun-worshipper on a rock",
  colors={"green": ["belly1 jaw snoutTip headTop napeTop spineMid hipTop tailBase belly3 belly2 belly1 flKnee flFoot flToe1", "tailTip tail2 tail1 tailBase blKnee blFoot blToe1", "flFoot flToe2", "blFoot blToe2"],
    "white": ["headTop eye"], "brown": ["spineMid spike1", "hipTop spike2"]})

P("castle", "Castle", "object",
  "c1 19.8 53.4; m1a 19.8 41.6; m1b 34.5 41.6; c2 34.5 53.4; c3 52.2 53.4; m2a 52.2 41.6;"
  "m2b 66.9 41.6; c4 66.9 53.4; c5 80.2 53.4; baseL 19.8 106.5; baseR 80.2 106.5;"
  "doorL 41.9 106.5; doorApex 53.7 82.9; doorR 65.5 106.5; spike1 19.8 28.4; spike3 47.8 28.4;"
  "flagPoleTop 65.5 26.9; flagTip 77.3 29.8; torchL 8 96.1; torchR 92 96.1",
  ["m1a c1 baseL doorL doorR baseR c5 c4 m2b m2a c3 c2 m1b m1a spike1", "m2a spike3",
   "m2b flagPoleTop flagTip", "baseL torchL", "baseR torchR", "doorL doorApex doorR"],
  clue="Moat not included",
  colors={"orange": ["baseL torchL", "baseR torchR"], "red": ["flagPoleTop flagTip"],
    "brown": ["m1a c1 baseL doorL doorR baseR c5 c4 m2b m2a c3 c2 m1b m1a spike1", "m2a spike3", "m2b flagPoleTop", "doorL doorApex doorR"]})

P("monkey", "Monkey", "animal",
  "muzzleTip 83.1 66.2; muzzleTop 70.3 59.3; browTop 63.3 47.4; headTop 55.4 36.5;"
  "earTop 52.5 50.4; earBack 40.6 44.4; napeStart 43.6 62.2; backTop 33.7 54.3;"
  "rumpTop 24.8 64.2; rumpBack 23.8 76.1; hipFront 36.7 78; belly 50.5 80; chestFront 64.3 74.1;"
  "chin 76.2 76.1; eye 67.3 30.6; nostril 92 56.3; earInner 43.6 31.6; elbow 67.3 87.9;"
  "hand 61.4 98.8; knee 33.7 91.9; foot 26.8 102.7; tail1 12.9 70.1; tailTip 8 81",
  ["muzzleTip muzzleTop browTop headTop earTop earBack napeStart backTop rumpTop rumpBack hipFront belly chestFront chin muzzleTip nostril",
   "headTop eye", "earTop earInner", "rumpBack tail1 tailTip", "hipFront knee foot",
   "chestFront elbow hand"],
  clue="Branch manager, self-appointed",
  colors={"orange": ["rumpBack tail1 tailTip"], "white": ["headTop eye"],
    "brown": ["muzzleTip muzzleTop browTop headTop earTop earBack napeStart backTop rumpTop rumpBack hipFront belly chestFront chin muzzleTip nostril", "earTop earInner", "hipFront knee foot", "chestFront elbow hand"]})

P("mailbox", "Mailbox", "object",
  "bL 26.7 83; aL 26.7 55; aTL 35.1 34.5; aT 59.3 25.1; aTR 83.6 34.5; aR 92 55; bR 92 83;"
  "postAttach 59.3 83; flagBase 26.7 69; dL 40.7 59.7; dR 78 59.7; dR2 78 75.5; dL2 40.7 75.5;"
  "handleA 64.9 66.2; handleB 50 69; postBottom 59.3 125; baseL 40.7 125; baseR 78 125;"
  "flagLow 8 59.7; flagTop 8 27; flagTip 31.3 12.1; slotA 59.3 8.3",
  ["aL flagBase bL postAttach bR aR aTR aT aTL aL dL dR aR", "aT slotA",
   "postAttach postBottom baseL", "flagBase flagLow flagTop flagTip flagLow", "dL dL2 dR2 dR",
   "handleA handleB", "postBottom baseR"],
  clue="You've got mail",
  colors={"red": ["flagBase flagLow flagTop flagTip flagLow"],
    "blue": ["aL flagBase bL postAttach bR aR aTR aT aTL aL dL dR aR", "dL dL2 dR2 dR"],
    "white": ["aT slotA", "handleA handleB"],
    "brown": ["postAttach postBottom baseL", "postBottom baseR"]})

P("panda", "Panda", "animal",
  "h0 50 37.5; h1 78 48; h2 92 72.5; h3 78 97; h4 50 107.5; h5 22 97; h6 8 72.5; h7 22 48;"
  "earLa 8 28.2; earLb 24.3 25.8; earLc 31.3 37.5; earRa 68.7 37.5; earRb 75.7 25.8;"
  "earRc 92 28.2; pL1 32.5 57.3; pL2 44.2 69; pL3 32.5 80.7; pL4 20.8 69; pLc 32.5 69;"
  "pR1 67.5 57.3; pR2 79.2 69; pR3 67.5 80.7; pR4 55.8 69; pRc 67.5 69; noseA 43 95.8;"
  "noseB 57 95.8",
  ["pL1 pL2 pL3 pL4 pL1 pLc pL2", "pL3 pLc pL4", "pR1 pR2 pR3 pR4 pR1 pRc pR2", "pR3 pRc pR4",
   "noseA noseB", "h0 h1 h2 h3 h4 h5 h6 h7 h0", "h1 earRa earRb earRc h1",
   "h7 earLa earLb earLc h7"],
  clue="Black, white, and bamboo all over",
  colors={"pink": ["noseA noseB"], "white": ["h0 h1 h2 h3 h4 h5 h6 h7 h0"],
    "brown": ["pL1 pL2 pL3 pL4 pL1 pLc pL2", "pL3 pLc pL4", "pR1 pR2 pR3 pR4 pR1 pRc pR2", "pR3 pRc pR4", "h1 earRa earRb earRc h1", "h7 earLa earLb earLc h7"]})

P("icecream", "Ice Cream Cone", "object",
  "A 50 125.3; R1L 42.2 110.7; R1R 57.8 110.7; R2L 34.4 96; R2M 50 96; R2R 65.6 96;"
  "R3A 26.5 84.3; R3B 42.2 84.3; R3C 57.8 84.3; R3D 73.5 84.3; P1 30.4 58.8; V1 40.2 70.6;"
  "P2 50 53; V2 59.8 70.6; P3 69.6 58.8; sp1 26.5 37.3; sp2 36.3 47.1; sp3 50 35.4;"
  "sp4 63.7 47.1; sp5 73.5 37.3; swirlTip 50 19.7; chL 40.2 8; chR 59.8 8",
  ["R1L A R1R R2M R1L R2L R3A P1 V1 P2 V2 P3 R3D R2R R1R", "R2L R3B R2M R3C R2R",
   "P1 sp1 sp2 sp3 sp4 sp5 P3", "sp3 swirlTip chL chR swirlTip"],
  clue="Brain freeze in a crunchy cup",
  colors={"red": ["sp3 swirlTip chL chR swirlTip"], "pink": ["R3A P1 V1 P2 V2 P3 R3D"],
    "white": ["P1 sp1 sp2 sp3 sp4 sp5 P3"],
    "brown": ["R1L R2M R1R A R1L R2L R3A", "R1R R2R R3D", "R2L R3B R2M R3C R2R"]})

P("sunflower", "Sunflower", "plant",
  "c0 50 27.9; c1 61.7 32.4; c2 66.2 44.1; c3 61.7 55.8; c4 50 60.3; c5 38.3 55.8; c6 33.8 44.1;"
  "c7 38.3 32.4; t0 50 8; t1 69.9 17; t2 81.6 44.1; t3 69.9 71.2; t5 30.1 71.2; t6 18.4 44.1;"
  "t7 30.1 17; stemMid 50 84.7; stemBot 50 111.8; leafTop 68.1 89.2; leafTip 81.6 96.5;"
  "leafBot 69.9 105.5; leafTop2 36.5 105.5; leafTip2 18.4 118.1; leafBot2 31.9 125.3",
  ["t0 c0 c1 c2 c3 c4 c5 c6 c7 c0 c4 stemMid stemBot leafTop2 leafTip2 leafBot2 stemBot",
   "t1 c1 c5 t5", "t2 c2 c6 t6", "t3 c3 c7 t7", "stemMid leafTop leafTip leafBot stemMid"],
  clue="I always turn to face the sun",
  colors={"green": ["c4 stemMid stemBot leafTop2 leafTip2 leafBot2 stemBot", "stemMid leafTop leafTip leafBot stemMid"],
    "brown": ["c0 c1 c2 c3 c4 c5 c6 c7 c0 c4", "c1 c5", "c2 c6", "c3 c7"]})

P("tiger", "Tiger", "animal",
  "noseTip 92 77.9; muzzleTop 81.7 68.5; browTop 78 57.3; earTip1 74.3 46.1; earTip2 62.1 42.4;"
  "napeStart 61.2 57.3; shoulderTop 50.9 46.1; midBack 40.7 40.5; hipTop 30.4 50.8;"
  "rumpBack 23.9 62.9; loin 37.9 76; belly 54.7 78.8; chestFront 72.4 76.9; chin 82.7 85.3;"
  "eye 70.5 65.7; stripeTip1 43.5 54.5; stripeTip2 24.8 38.7; tailBase 15.5 53.6; tail1 8 42.4;"
  "tailTip 26.7 26.5; flKnee 78 96.5; flPaw 68.7 106.8; blKnee 35.1 90; blPaw 32.3 101.2",
  ["browTop muzzleTop noseTip chin chestFront belly loin rumpBack hipTop midBack shoulderTop napeStart earTip2 earTip1 browTop eye",
   "shoulderTop stripeTip1", "hipTop stripeTip2", "rumpBack tailBase tail1 tailTip",
   "loin blKnee blPaw", "chestFront flKnee flPaw"],
  clue="Prowls in orange pajamas",
  colors={"orange": ["rumpBack loin belly chestFront chin noseTip muzzleTop browTop earTip1 earTip2 napeStart shoulderTop midBack hipTop rumpBack tailBase tail1 tailTip", "loin blKnee blPaw", "chestFront flKnee flPaw"],
    "white": ["browTop eye"], "brown": ["shoulderTop stripeTip1", "hipTop stripeTip2"]})

P("skateboard", "Skateboard", "object",
  "tT 8 41.5; tB1 20.6 52.4; tB2 37.4 55.7; tB3 62.6 55.7; tB4 79.4 52.4; nT 92 41.5;"
  "tT2 8 56.6; bB1 20.6 67.5; bB2 37.4 70.9; bB3 62.6 70.9; bB4 79.4 67.5; nT2 92 56.6;"
  "wheelTop1 20.6 80.9; w1r 32.4 92.7; w1b 20.6 104.5; w1l 8.8 92.7; wheelTop2 79.4 80.9;"
  "w2r 91.2 92.7; w2b 79.4 104.5; w2l 67.6 92.7; accentA 8 28.9; accentB 92 28.9",
  ["tT tB1 tB2 tB3 tB4 nT nT2 bB4 bB3 bB2 bB1 tT2 tT accentA", "nT accentB",
   "bB1 wheelTop1 w1r w1b w1l wheelTop1", "bB4 wheelTop2 w2r w2b w2l wheelTop2"],
  clue="Four wheels and a whole lot of attitude",
  colors={"red": ["tT accentA", "nT accentB"],
    "white": ["bB1 wheelTop1 w1r w1b w1l wheelTop1", "bB4 wheelTop2 w2r w2b w2l wheelTop2"],
    "brown": ["tT tB1 tB2 tB3 tB4 nT nT2 bB4 bB3 bB2 bB1 tT2 tT"]})

# Publish order (index 0 = launch day). Redrawn puzzles first, old drawings after.
ORDER = [
    "starfish", "barn", "drum", "pine", "teapot", "sled", "fish", "balloon", "bridge",
    "pineapple", "fox", "ferriswheel", "gift", "kite", "giraffe", "lantern", "bamboo", "bench",
    "whale", "hammer", "ship", "butterfly", "umbrella", "lotus", "anchor2", "birdhouse", "dog",
    "coffee", "igloo", "wheat", "koala", "camera", "chessrook", "cupcake", "turtle",
    "headphones", "acorn", "hourglass", "camel", "rocket", "sunglasses", "telescope", "ant",
    "corn", "train", "pencil", "bear", "pizza", "trafficlight", "pumpkin", "well", "beetle",
    "bell", "burger", "crab", "bus", "cactus", "church", "ladybug", "clock", "compass", "dice",
    "octopus", "mushroom2", "flag", "laptop", "penguin", "robot", "snowman", "daisy", "trophy",
    "spider", "violin", "bat", "key2", "bee", "tent", "strawberry", "hedgehog", "microphone",
    "frog", "candle", "deer", "television", "lemon", "horse", "car", "seagull", "snowflake",
    "bird", "donut", "grapes", "lizard", "castle", "monkey", "mailbox", "panda", "icecream",
    "sunflower", "tiger", "skateboard"
]

# Puzzles redrawn to the new standard; everything else in ORDER is an old drawing.
REDRAWN = [
    "fox", "ferriswheel", "gift", "kite", "giraffe", "lantern", "bamboo", "bench", "whale",
    "hammer", "ship", "butterfly", "umbrella", "lotus", "anchor2", "birdhouse", "dog", "coffee",
    "igloo", "wheat", "koala", "camera", "chessrook", "cupcake", "turtle", "headphones", "acorn",
    "hourglass", "camel", "rocket", "sunglasses", "telescope", "ant", "corn", "train", "pencil",
    "bear", "pizza", "trafficlight", "pumpkin", "well", "beetle", "bell", "burger", "crab",
    "bus", "cactus", "church", "ladybug", "clock", "compass", "dice", "octopus", "mushroom2",
    "flag", "laptop", "penguin", "robot", "snowman", "daisy", "trophy", "spider", "violin",
    "starfish", "barn", "drum", "pine", "teapot", "sled", "fish", "balloon", "bridge",
    "pineapple", "bat", "key2", "bee", "tent", "strawberry", "hedgehog", "microphone", "frog",
    "candle", "deer", "television", "lemon", "horse", "car", "seagull", "snowflake", "bird",
    "donut", "grapes", "lizard", "castle", "monkey", "mailbox", "panda", "icecream", "sunflower",
    "tiger", "skateboard"
]


def fit(p):
    xs = [v[0] for v in p["pts"].values()]
    ys = [v[1] for v in p["pts"].values()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    x0, x1, y0, y1 = BOX
    s = min((x1 - x0) / w, (y1 - y0) / h)
    ox = 0.5 - s * (min(xs) + max(xs)) / 2
    oy = BOARD_H / 2 - s * (min(ys) + max(ys)) / 2
    deg = {k: 0 for k in p["pts"]}
    for a, b in p["edges"]:
        deg[a] += 1
        deg[b] += 1
    dots = [dict(id=k, x=round(ox + s * x, 3), y=round(oy + s * y, 3), degree=deg[k])
            for k, (x, y) in p["pts"].items()]
    out = dict(id=p["id"], title=p["title"], category=p["category"])
    if p.get("clue"):
        out["clue"] = p["clue"]
    out.update(dots=dots, edges=p["edges"])
    if p.get("colors"):  # in edge order, so the JSON diff stays stable
        order = [edge_key(a, b) for a, b in p["edges"]]
        out["colors"] = {k: p["colors"][k] for k in order if k in p["colors"]}
    return out


def dumps(puzzles):
    """Compact but diff-friendly: one dot per line, edges on one line."""
    j = lambda v: json.dumps(v, ensure_ascii=False)
    blocks = []
    for p in puzzles:
        dots = ",\n".join("      " + j(d) for d in p["dots"])
        blocks.append(
            f'  {{\n    "id": {j(p["id"])},\n    "title": {j(p["title"])},\n'
            f'    "category": {j(p["category"])},\n'
            + (f'    "clue": {j(p["clue"])},\n' if p.get("clue") else "")
            + f'    "dots": [\n{dots}\n    ],\n'
            f'    "edges": {j(p["edges"])}'
            + (f',\n    "colors": {j(p["colors"])}' if p.get("colors") else "")
            + "\n  }")
    return "[\n" + ",\n".join(blocks) + "\n]\n"


if __name__ == "__main__":
    by_id = {p["id"]: p for p in PUZZLES}
    assert sorted(ORDER) == sorted(by_id), set(by_id) ^ set(ORDER)
    assert set(REDRAWN) <= set(ORDER), set(REDRAWN) - set(ORDER)
    out = [fit(by_id[i]) for i in ORDER]
    if len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        sys.exit("usage: python tools/author_puzzles.py [OUTPUT.json]  (default: puzzles/puzzles.json)")
    path = sys.argv[1] if len(sys.argv) > 1 else ROOT / "puzzles" / "puzzles.json"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(out))
    for p in out:
        print(f"{p['id']:14s} {p['category']:18s} dots={len(p['dots']):2d} edges={len(p['edges'])}")
