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
  clue="Quick, brown, and jumps over lazy dogs")

P("ferriswheel", "Ferris wheel", "object",
  "hub 50 46.5; r0 50 8; r1 22.8 19.3; r2 11.5 46.5; r3 22.8 73.8; r4 50 85.1; r5 77.2 73.8;"
  "r6 88.5 46.5; r7 77.2 19.3; c0a 43.4 22; c0b 56.6 22; c3a 16.2 87.8; c3b 29.3 87.8;"
  "c4a 43.4 99.1; c4b 56.6 99.1; c5a 70.7 87.8; c5b 83.8 87.8; ftL 29 125.3; ftR 71 125.3;"
  "gL 11.5 125.3; gR 88.5 125.3",
  ["r0 r1 r2 r3 r4 r5 r6 r7 r0 hub r1", "r0 c0a c0b r0", "r2 hub r3 c3a c3b r3",
   "r4 hub r5 c5a c5b r5", "r4 c4a c4b r4", "r6 hub r7", "ftL hub ftR ftL gL", "ftR gR"],
  clue="Round and round we go")

P("gift", "Gift box", "object",
  "LtL 8 49.4; LbL 8 64.6; BtL 19.8 64.6; BbL 19.8 110.8; RtL 43.7 49.4; RmL 43.7 64.6;"
  "RbL 43.7 110.8; Kc 50 39.4; LuL 26.5 22.6; LoL 18.1 37.7; LiL 31.5 42.7; LtR 92 49.4;"
  "LbR 92 64.6; BtR 80.2 64.6; BbR 80.2 110.8; RtR 56.3 49.4; RmR 56.3 64.6; RbR 56.3 110.8;"
  "LuR 73.5 22.6; LoR 81.9 37.7; LiR 68.5 42.7",
  ["BtL RmL RmR BtR LbR LtR RtR RtL LtL LbL BtL BbL RbL RbR BbR BtR",
   "RbL RmL RtL Kc RtR RmR RbR", "Kc LuL LoL LiL Kc LuR LoR LiR Kc"],
  clue="It's the thought that counts")

P("kite", "Kite", "object",
  "k0 50 8; kl 25.7 24.2; kr 74.3 24.2; kc 50 24.2; kb 50 54.9; t0 54 70.3; t0a 43.5 64.6;"
  "t0b 43.5 76; t0c 64.6 64.6; t0e 64.6 76; t1 46 89.7; t1a 35.4 84.1; t1b 35.4 95.4;"
  "t1c 56.5 84.1; t1e 56.5 95.4; t2 54 109.1; t2a 43.5 103.5; t2b 43.5 114.8; t2c 64.6 103.5;"
  "t2e 64.6 114.8; te 50 125.3",
  ["k0 kl kb kr k0 kc kl", "kr kc kb t0 t1 t2 te", "t0 t0a t0b t0 t0c t0e t0",
   "t1 t1a t1b t1 t1c t1e t1", "t2 t2a t2b t2 t2c t2e t2"],
  clue="Go fly one!")

P("giraffe", "Giraffe", "animal",
  "sn 8 32.9; ht 20 20.9; hb 32 23.9; jw 21.5 40.4; os1 18.5 8.9; os2 32 11.9; nb1 41 43.4;"
  "nf1 29 55.4; wi 53 64.4; bk 68 68.9; rp 83 73.4; ch 38 77.9; bf 42.5 91.4; bf2 54.5 91.4;"
  "bl2 69.5 91.4; bl 81.5 88.4; sp 60.5 79.4; f1 38 124.4; f2 53 124.4; r1 71 124.4;"
  "r2 84.5 124.4; tl 92 94.4",
  ["ht sn jw nf1 ch bf bf2 bl2 bl rp bk wi nb1 hb ht os1", "hb os2", "nb1 nf1", "bk sp wi ch",
   "rp tl", "bf f1", "bl r2", "f2 bf2 sp bl2 r1"],
  clue="Head and neck above the rest")

P("lantern", "Lantern", "object",
  "h1 42.2 21.7; h2 50 8; h3 57.8 21.7; c1 40.2 35.4; c2 59.8 35.4; a1 14.8 54.9; a2 32.4 54.9;"
  "a3 67.6 54.9; a4 85.2 54.9; b1 14.8 109.7; b2 32.4 109.7; b3 67.6 109.7; b4 85.2 109.7;"
  "d1 20.7 125.3; d2 36.3 125.3; d3 63.7 125.3; d4 79.3 125.3; fl 50 68.6; fa 42.2 88.2;"
  "fb 50 98; fc 57.8 88.2",
  ["a1 a2 a3 a4 c2 h3 h2 h1 c1 c2 a3 b3 b2 a2 c1 a1 b1 b2 d2 d1 b1", "a4 b4 b3 d3 d2",
   "b4 d4 d3", "fl fa fb fc fl"],
  clue="Light the way, old-school style")

P("bamboo", "Bamboo", "plant",
  "a0l 29 23.9; a0r 41 23.9; a1l 29 46.4; a1r 41 46.4; a2l 29 68.9; a2r 41 68.9; a3l 29 91.4;"
  "a3r 41 91.4; a4l 29 113.9; a4r 41 113.9; b0l 54.5 43.4; b0r 66.5 43.4; b1l 54.5 66.7;"
  "b1r 66.5 66.7; b2l 54.5 89.9; b2r 66.5 89.9; b3l 54.5 113.9; b3r 66.5 113.9; l1s 54.5 26.9;"
  "l1t 77 19.4; l2s 83 61.4; l2t 92 44.9; l3s 15.5 62.9; l3t 8 83.9",
  ["a1l a0l a0r a1r a2r a3r a4r a4l a3l a2l a1l a1r l1s l1t a1r", "a2l a2r", "a2l l3s l3t a2l",
   "a3l a3r", "b1l b0l b0r b1r b2r b3r b3l b2l b1l b1r l2t l2s b1r", "b2l b2r"],
  clue="A panda's favourite snack bar")

P("bench", "Park bench", "object",
  "p1 21.4 25.5; p2 50 25.5; p3 78.6 25.5; q1 21.4 38.9; q2 50 38.9; q3 78.6 38.9; r1 21.4 52.4;"
  "r2 50 52.4; r3 78.6 52.4; a1 9.7 55.7; a3 90.3 55.7; s0 8 67.5; s1 21.4 67.5; s2 50 67.5;"
  "s3 78.6 67.5; s4 92 67.5; f0 8 79.3; f1 21.4 79.3; f3 78.6 79.3; f4 92 79.3; g1 14.7 107.8;"
  "g3 85.3 107.8",
  ["p2 p1 q1 q2 q3 p3 p2 q2 r2 r1 q1", "q3 r3 r2 s2 s1 r1 a1 s0 s1 f1 f0 s0",
   "s2 s3 r3 a3 s4 s3 f3 f1 g1", "s4 f4 f3 g3"],
  clue="Feed the pigeons, rest your feet")

P("whale", "Whale", "animal",
  "sn 8 77; h1 12.4 60.8; h2 25.7 49; h3 47.8 49; k1 61.1 57.8; q1 71.4 53.4; fl 68.4 37.2;"
  "fn 81.7 45.3; fr 92 56.4; q2 78.7 65.2; u1 69.9 81.4; u2 59.6 96.1; u3 43.4 103.5;"
  "u4 27.2 100.6; u5 12.4 90.2; m1 24.2 85.8; p1 41.9 90.2; p2 56.6 84.4; ey 37.5 57.8;"
  "ey2 37.5 69.6; sp1 25.7 35.7; sp2 15.4 29.8; sp3 36 29.8",
  ["sn h1 h2 h3 k1 q1 fl fn fr q2 u1 u2 u3 u4 u5 sn m1 p1 p2 u1", "h2 sp1 sp2", "q1 q2",
   "u2 p2", "u3 p1", "u4 m1", "ey ey2", "sp1 sp3"],
  clue="Thar she blows!")

P("hammer", "Hammer", "object",
  "fa 8 10.2; fb 8 42.2; fc 21 10.2; fd 21 42.2; t1 32.4 10.9; t2 46.2 11.7; e 58.4 13.2;"
  "h 81.3 20.8; i 92 42.2; j 79.8 35.4; k 66 30.8; hl 32.4 42.2; hr 46.2 42.2; g1l 32.4 77.4;"
  "g1r 46.2 77.4; g2l 32.4 89.6; g2r 46.2 89.6; g3l 32.4 101.8; g3r 46.2 101.8; el 32.4 114;"
  "er 46.2 114; eb 39.3 123.2",
  ["fc fa fb fd fc t1 t2 e h i j k hr hl fd", "t1 hl g1l g2l g3l el eb er g3r g2r g1r hr t2",
   "g1l g1r", "g2l g2r", "g3l g3r"],
  clue="When all you see is nails...")

P("ship", "Sailboat", "object",
  "mt 50 11.7; fg 66.2 17.4; m0 50 23.1; ma 50 39.2; mb 50 57; m1 50 71.5; dk 50 84.4;"
  "mc 88.8 71.5; jk 14.5 71.5; bw 8 84.4; sn 92 84.4; kb 22.5 100.6; ks 79.1 100.6;"
  "la 62.9 39.2; lb 77.1 57; js 30.5 57; w0 11.2 121.6; w1 25.8 111.9; w2 40.3 121.6;"
  "w3 54.8 111.9; w4 69.4 121.6; w5 83.9 111.9",
  ["dk m1 mb ma m0 mt fg m0 la lb mc m1 jk js ma la", "dk bw kb ks sn dk", "lb mb js",
   "w0 w1 w2 w3 w4 w5"],
  clue="Catch the wind, skip the engine")

P("butterfly", "Butterfly", "animal",
  "hd 50 45.7; aL 41.6 23.8; b1 50 57.4; b2 50 74.2; b3 50 102.8; u1L 33.2 33.9; u2L 13 30.5;"
  "u3L 8 52.4; u4L 23.1 72.5; d1L 16.4 92.7; d2L 29.8 109.5; s1L 19.8 44; s2L 33.2 47.3;"
  "s3L 24.8 59.1; aR 58.4 23.8; u1R 66.8 33.9; u2R 87 30.5; u3R 92 52.4; u4R 76.9 72.5;"
  "d1R 83.6 92.7; d2R 70.2 109.5; s1R 80.2 44; s2R 66.8 47.3; s3R 75.2 59.1",
  ["hd aL", "hd aR", "hd b1 b2 b3 d2L d1L u4L u3L u2L u1L b1 u1R u2R u3R u4R b2 u4L",
   "b3 d2R d1R u4R", "s1L s2L s3L s1L", "s1R s2R s3R s1R"],
  clue="I used to be a caterpillar")

P("umbrella", "Umbrella", "object",
  "tip 50 11.2; t 50 23; oL 23.1 28; bL 11.4 41.5; rL0 8 61.6; sL0 18.5 52.4; rL1 29 61.6;"
  "sL1 39.5 52.4; r2 50 61.6; kL 30.7 41.5; km 50 41.5; sh 50 110.3; h1 45 122.1; h2 33.2 122.1;"
  "oR 76.9 28; bR 88.6 41.5; rR0 92 61.6; sR0 81.5 52.4; rR1 71 61.6; sR1 60.5 52.4;"
  "kR 69.3 41.5; h3 26.5 111.2",
  ["tip t oL bL rL0 sL0 rL1 sL1 r2 sR1 rR1 sR0 rR0 bR oR t kL rL1", "bL kL km t kR rR1",
   "bR kR km r2 sh h1 h2 h3"],
  clue="Singin' in the rain, but dry")

P("lotus", "Lotus", "plant",
  "T 50 21.7; a1L 40.2 41.2; a2L 36.5 62.2; cbL 42.5 87.7; v 50 68.2; mtL 23 33.7;"
  "moL 18.5 57.7; obL 29 84.7; otL 8 65.2; olL 15.5 81.7; w1L 14 99.7; w2L 32 99.7;"
  "w3L 39.5 111.7; a1R 59.7 41.2; a2R 63.5 62.2; cbR 57.5 87.7; mtR 77 33.7; moR 81.5 57.7;"
  "obR 71 84.7; otR 92 65.2; olR 84.5 81.7; w1R 86 99.7; w2R 68 99.7; w3R 60.5 111.7",
  ["T a1L a2L cbL obL moL mtL a2L", "T a1R a2R cbR obR moR mtR a2R", "T v cbL cbR v",
   "moL otL olL obL", "w1L w2L", "w3L w3R", "moR otR olR obR", "w1R w2R"],
  clue="Blooms beautifully out of the mud")

P("anchor2", "Anchor", "object",
  "rt 50 17; rb 50 41.2; r1L 39.5 23.1; r2L 39.5 35.2; stL 29 53.3; sct 50 53.3; sbL 29 65.5;"
  "scb 50 65.5; cr 50 116.3; a2L 27.4 108.3; mL 19.3 95.3; tL 17.7 71.1; bL 8 97; cL 30.6 93.7;"
  "r1R 60.5 23.1; r2R 60.5 35.2; stR 71 53.3; sbR 71 65.5; a2R 72.6 108.3; mR 80.7 95.3;"
  "tR 82.3 71.1; bR 92 97; cR 69.4 93.7",
  ["rb r2L r1L rt r1R r2R rb sct stL sbL scb sbR stR sct scb cr a2L mL cL tL bL mL",
   "cr a2R mR cR tR bR mR"],
  clue="I keep you grounded at sea")

P("birdhouse", "Birdhouse", "object",
  "A 50 12.4; IA 50 25.4; ML 29 29; EL 8 45.7; NL 32.6 39.7; IEL 16.7 52.9; WL 16.7 102.1;"
  "PL 43.5 102.1; QL 43.5 121; pL 39.9 90.6; MR 71 29; ER 92 45.7; NR 67.4 39.7; IER 83.3 52.9;"
  "WR 83.3 102.1; PR 56.5 102.1; QR 56.5 121; pR 60.1 90.6; h0 50 58; h1 60.4 65.5;"
  "h2 56.4 77.6; h3 43.6 77.6; h4 39.6 65.5",
  ["ML EL IEL NL IA NR IER ER MR A ML NL", "IEL WL PL PR WR IER", "PL QL QR PR", "pL pR",
   "MR NR", "h0 h1 h2 h3 h4 h0"],
  clue="Tweet home, sweet home")

P("dog", "Dog", "animal",
  "top 50 27.6; tL 31.5 32.6; sL 26.5 54.5; jL 33.2 76.3; chin 50 86.4; eo1L 14.7 36;"
  "eo2L 8 57.8; etL 13 84.7; eyL 38.2 42.7; ey2L 38.2 54.5; nlL 41.6 66.2; nb 50 74.6;"
  "tgL 42.4 95.6; tt 50 105.7; tR 68.5 32.6; sR 73.5 54.5; jR 66.8 76.3; eo1R 85.3 36;"
  "eo2R 92 57.8; etR 87 84.7; eyR 61.8 42.7; ey2R 61.8 54.5; nlR 58.4 66.2; tgR 57.6 95.6",
  ["tL top tR sR jR chin jL sL tL eo1L eo2L etL sL", "chin nb nlR nlL nb",
   "chin tgL tt tgR chin", "eyL ey2L", "tR eo1R eo2R etR sR", "eyR ey2R"],
  clue="Who's a good boy?")

P("coffee", "Coffee cup", "object",
  "tl 18.1 58.3; rb1 33.2 51.5; rb2 60.1 51.5; tr 75.2 58.3; rf2 60.1 65; rf1 33.2 65;"
  "c1 31.5 108.7; c2 61.8 108.7; sl 8 108.7; sr 92 108.7; u1 19.8 118.7; u2 80.2 118.7;"
  "o1 87 66.7; o2 92 81.8; o3 85.3 95.2; hh1 72.1 70; hh2 65.8 93.5; s0a 36.6 38.1;"
  "s0b 31.5 26.3; s0c 36.6 14.6; s1a 56.7 38.1; s1b 51.7 26.3; s1c 56.7 14.6",
  ["tl rb1 rb2 tr rf2 rf1 tl c1 sl u1 u2 sr c2 hh2 hh1 tr", "c1 c2", "hh1 o1 o2 o3 hh2",
   "s0a s0b s0c", "s1a s1b s1c"],
  clue="Espresso yourself!")

P("igloo", "Igloo", "object",
  "o0L 8 92.7; o1L 9.1 80.9; o2L 14.9 64.1; o3L 23.1 52.7; o4L 36.6 43.4; top 50 40.6;"
  "bB1L 26.5 64.1; bB2L 38.2 64.1; bBc 50 64.1; aA1L 26.5 80.9; shL 38.2 80.9; dbL 33.2 92.7;"
  "dtop 50 75.9; o0R 92 92.7; o1R 90.9 80.9; o2R 85.1 64.1; o3R 76.9 52.7; o4R 63.4 43.4;"
  "bB1R 73.5 64.1; bB2R 61.8 64.1; aA1R 73.5 80.9; shR 61.8 80.9; dbR 66.8 92.7",
  ["o1L o0L dbL shL aA1L o1L o2L o3L o4L top o4R o3R o2R o1R o0R dbR shR aA1R o1R",
   "o2L bB1L bB2L bBc bB2R bB1R o2R", "top bBc", "bB1L aA1L", "bB2L shL dtop shR bB2R",
   "bB1R aA1R"],
  clue="Cool pad, snow kidding")

P("wheat", "Wheat", "plant",
  "b1 50 93.1; b2 50 71.1; b3 50 49.1; s0 50 125.3; k0Lt 30.9 78.4; k0La 43.1 80.4;"
  "k0Lb 35.9 89.6; k0Lw 22.1 63.7; k0Rt 69.1 78.4; k0Ra 64.1 89.6; k0Rb 56.9 80.4;"
  "k0Rw 77.9 63.7; k1Lt 30.9 56.4; k1La 43.1 58.4; k1Lb 35.9 67.6; k1Lw 22.1 41.7;"
  "k1Rt 69.1 56.4; k1Ra 64.1 67.6; k1Rb 56.9 58.4; k1Rw 77.9 41.7; ktt 50 24.1; kta 56.6 36.6;"
  "ktb 43.4 36.6; ktw 50 8",
  ["b3 b2 b1 s0", "b3 kta ktt ktb b3", "k0Lt k0La b1 k0Lb k0Lt k0Lw",
   "k0Rt k0Ra b1 k0Rb k0Rt k0Rw", "k1Lt k1La b2 k1Lb k1Lt k1Lw", "k1Rt k1Ra b2 k1Rb k1Rt k1Rw",
   "ktt ktw"],
  clue="Our daily bread starts in a field")

P("koala", "Koala", "animal",
  "j1L 22.9 58; e1L 8.9 49.8; e2L 8 33.5; e3L 21.1 23.9; e4L 36.4 29.5; j2L 40.1 45.3;"
  "c1L 21 91.9; cb 50 109.4; nuL 43 67.4; nlL 41.4 83; nb 50 97; eyL 31.3 65.8; ey2L 31.3 77.5;"
  "j1R 77.1 58; e1R 91.1 49.8; e2R 92 33.5; e3R 78.9 23.9; e4R 63.6 29.5; j2R 59.9 45.3;"
  "c1R 79 91.9; nuR 57 67.4; nlR 58.6 83; eyR 68.7 65.8; ey2R 68.7 77.5",
  ["j1L c1L cb c1R j1R e1R e2R e3R e4R j2R j2L e4L e3L e2L e1L j1L j2L",
   "nlL nuL nuR nlR nb nlL nlR", "eyL ey2L", "j1R j2R", "eyR ey2R"],
  clue="Eucalyptus is my whole personality")

P("camera", "Camera", "object",
  "k1 8 41.5; k2 92 41.5; k3 92 105.3; k4 8 105.3; hb1 33.2 41.5; hb2 66.8 41.5; ht1 39.9 28;"
  "ht2 60.1 28; sL 8 73.4; sR 92 73.4; L0 75.2 73.4; L1 67.8 91.2; L2 50 98.6; L3 32.2 91.2;"
  "L4 24.8 73.4; L5 32.2 55.6; L6 50 48.2; L7 67.8 55.6; i0 36.6 73.4; i1 43.3 61.7;"
  "i2 56.7 61.7; i3 63.4 73.4; i4 56.7 85.1; i5 43.3 85.1",
  ["hb1 k1 sL k4 k3 sR k2 hb2 ht2 ht1 hb1 hb2", "sL L4 L3 L2 L1 L0 sR", "L0 L7 L6 L5 L4",
   "i0 i1 i2 i3 i4 i5 i0 i2"],
  clue="Say cheese!")

P("chessrook", "Chess rook", "object",
  "t1L 15.3 8.2; t2L 29 8.2; t3L 29 21.9; t4L 42.7 21.9; t5L 42.7 8.2; cL 15.3 35.6; gL 29 35.6;"
  "nL 25.3 48.4; wL 23.5 88.6; rL 14.4 97.7; sL 14.4 110.5; fL 8 125.1; t1R 84.7 8.2;"
  "t2R 71 8.2; t3R 71 21.9; t4R 57.3 21.9; t5R 57.3 8.2; cR 84.7 35.6; gR 71 35.6; nR 74.7 48.4;"
  "wR 76.5 88.6; rR 85.6 97.7; sR 85.6 110.5; fR 92 125.1",
  ["t3L t2L t1L cL gL gR cR t1R t2R t3R t4R t5R t5L t4L t3L gL",
   "cL nL wL rL sL fL fR sR rR wR nR cR", "nL nR", "wL wR", "sL sR", "t3R gR"],
  clue="I start every game stuck in a corner")

P("cupcake", "Cupcake", "object",
  "wL0 18 85.7; wL1 34 85.7; w2 50 85.7; vL0 25.6 125.3; vL1 37.8 125.3; v2 50 125.3;"
  "aL1 8.9 75; aL2 16.5 62.9; bL 25.6 50.7; c1 50 70.5; c2 50 56.8; wR0 82 85.7; wR1 66 85.7;"
  "vR0 74.4 125.3; vR1 62.2 125.3; aR1 91.1 75; aR2 83.5 62.9; bR 74.4 50.7; ch0 50 37.7;"
  "ch1 40.6 30.9; ch2 44.2 19.8; ch3 55.8 19.8; ch4 59.4 30.9; st 62.2 8",
  ["wL0 wL1 w2 wR1 wR0 vR0 vR1 v2 vL1 vL0 wL0 aL1 aL2 bL ch0 bR aR2 aR1 wR0", "wL1 vL1",
   "w2 v2", "aL2 c1 aR2", "bL c2 bR", "wR1 vR1", "ch3 ch2 ch1 ch0 ch4 ch3 st"],
  clue="Muffin compares to me")

P("turtle", "Turtle", "animal",
  "o1L 40.3 36; o1R 59.7 36; o2L 23.8 49.1; o2R 76.2 49.1; o3L 16.7 72.8; o3R 83.3 72.8;"
  "o4L 23.8 96.5; o4R 76.2 96.5; o5L 40.3 109.6; o5R 59.7 109.6; xtL 41.2 55.3; xtR 58.7 55.3;"
  "xmL 30.7 72.8; xmR 69.3 72.8; xbL 41.2 90.3; xbR 58.7 90.3; hdL 36.9 20.3; hdR 63.1 20.3;"
  "hd 50 8; ffL 8 27.3; ffR 92 27.3; bfL 8 118.3; bfR 92 118.3; tail 50 125.3",
  ["o1L o1R o2R o3R o4R o5R o5L o4L o3L o2L o1L xtL xtR xmR xbR xbL xmL xtL",
   "o1L hdL hd hdR o1R xtR", "o1L ffL o2L", "o1R ffR o2R", "o3L xmL", "o3R xmR",
   "o4L bfL o5L xbL", "o4R bfR o5R xbR", "o5L tail o5R"],
  clue="Slow and steady wins the race")

P("headphones", "Headphones", "object",
  "o0 15.4 60.9; i0 26.9 60.9; o1 25.5 36.4; i1 33.7 44.6; o2 50 26.3; i2 50 37.8; o3 74.5 36.4;"
  "i3 66.3 44.6; o4 84.6 60.9; i4 73.1 60.9; c1L 12.1 72.4; c6L 8 89.7; c5L 12.1 107;"
  "c4L 31.9 107; c3L 36 89.7; c2L 31.9 72.4; kL 24.5 89.7; c1R 87.9 72.4; c6R 92 89.7;"
  "c5R 87.9 107; c4R 68.1 107; c3R 64 89.7; c2R 68.1 72.4; kR 75.5 89.7",
  ["o0 o1 o2 o3 o4 i4 i3 i2 i1 i0 o0 c1L c6L c5L c4L c3L c2L i0", "o1 i1", "o2 i2", "o3 i3",
   "o4 c1R c6R c5R c4R c3R c2R i4", "c1L c2L kL c4L", "c1R c2R kR c4R"],
  clue="Noise? Cancelled.")

P("acorn", "Acorn", "plant",
  "st 54.8 8; ct 50 22.5; c1L 30.7 27.3; c2L 16.2 38.5; rimL 9.8 51.4; b1L 22.7 59.4;"
  "b2L 36.3 62.6; b3 50 64.3; h1L 29.1 43.4; h2L 42.8 41.8; n1L 24.3 77.1; n2L 29.9 93.2;"
  "n3L 39.6 106; tip 50 114.1; nib 50 125.3; c1R 69.3 27.3; c2R 83.8 38.5; rimR 90.2 51.4;"
  "b1R 77.3 59.4; b2R 63.7 62.6; h1R 70.9 43.4; h2R 57.2 41.8; n1R 75.7 77.1; n2R 70.1 93.2;"
  "n3R 60.4 106",
  ["st ct c1L c2L rimL b1L b2L b3 b2R b1R rimR c2R c1R ct",
   "tip n3L n2L n1L b1L h1L b2L h2L b3 h2R b2R h1R b1R n1R n2R n3R tip nib"],
  clue="Every mighty oak started here")

P("hourglass", "Hourglass", "object",
  "ptL 8 14.2; ptR 92 14.2; pbL 18.5 24.7; pbR 81.5 24.7; gL 32 24.7; gR 68 24.7; s1L 23.7 39.7;"
  "s1R 76.2 39.7; s2L 30.5 54.7; s2R 69.5 54.7; wL 44 66.7; wR 56 66.7; s3L 30.5 78.7;"
  "s3R 69.5 78.7; s4L 23.7 93.7; s4R 76.2 93.7; qtL 18.5 108.7; qtR 81.5 108.7; gbL 32 108.7;"
  "gbR 68 108.7; qbL 8 119.2; qbR 92 119.2; dip 50 56.2; peak 50 84.7",
  ["pbL ptL ptR pbR gR gL pbL qtL gbL s4L s3L wL s2L s1L gL",
   "pbR qtR gbR s4R s3R wR s2R s1R gR", "s2L dip s2R", "s4L peak s4R", "qtL qbL qbR qtR",
   "gbL gbR"],
  clue="Time is running out... grain by grain")

P("camel", "Camel", "animal",
  "n1 8 41.9; h1 14 31.4; h2 26 28.4; e 30.5 17.9; h3 32 38.9; j 17 50.9; nb 42.5 53.9;"
  "p1 51.5 32.9; d 60.5 46.4; p2 71 32.9; r 83 49.4; t 92 59.9; rt 80.7 65.9; b2 74 77.9;"
  "b1 47 77.9; c 38 70.4; nf 27.5 61.4; fk1 41 95.9; ff1 39.5 115.4; fk2 53 95.9; ff2 56 115.4;"
  "rk1 69.5 95.9; rf1 71 115.4; rk2 81.5 95.9; rf2 84.5 115.4",
  ["h2 h1 n1 j nf c b1 b2 rt r p2 d p1 nb h3 h2 e", "h3 j", "nb c", "r t",
   "ff1 fk1 b1 fk2 ff2", "rf1 rk1 b2 rk2 rf2"],
  clue="Two lumps, please - no sugar needed")

P("rocket", "Rocket", "object",
  "tip 50 8; c1L 41 20; cbL 33.5 36.6; fbL 33.5 78.7; btL 33.5 93.7; ftL 16.9 98.3;"
  "fwL 16.9 84.7; nzL 42.5 101.3; flL 39.5 113.3; fl 50 125.3; wL 38.7 56.1; wuL 44 46.4;"
  "wdL 44 65.9; c1R 59 20; cbR 66.5 36.6; fbR 66.5 78.7; btR 66.5 93.7; ftR 83.1 98.3;"
  "fwR 83.1 84.7; nzR 57.5 101.3; flR 60.5 113.3; wR 61.3 56.1; wuR 56 46.4; wdR 56 65.9",
  ["cbL c1L tip c1R cbR fbR btR nzR nzL btL fbL cbL cbR", "fbL fwL ftL btL btR ftR fwR fbR",
   "nzL flL fl flR nzR", "wL wuL wuR wR wdR wdL wL wR"],
  clue="3... 2... 1... liftoff!")

P("sunglasses", "Sunglasses", "object",
  "aL 8 64.1; bL 25.8 61.6; cL 43.6 64.1; gL 9.3 75.6; dL 43.6 75.6; mL 10.5 92.1;"
  "fL 23.3 102.3; eL 37.3 97.2; gl1L 18.8 82.6; gl2L 27.1 90.8; hL 11.8 41.2; jL 18.2 31;"
  "aR 92 64.1; bR 74.2 61.6; cR 56.4 64.1; gR 90.7 75.6; dR 56.4 75.6; mR 89.5 92.1;"
  "fR 76.7 102.3; eR 62.7 97.2; gl1R 81.2 82.6; gl2R 72.9 90.8; hR 88.2 41.2; jR 81.8 31",
  ["aL hL jL", "aL bL cL cR bR aR hR jR", "aL gL dL cL", "gL mL fL eL dL", "gl1L gl2L",
   "aR gR dR cR", "gR mR fR eR dR", "gl1R gl2R"],
  clue="Too cool for UV rays")

P("telescope", "Telescope", "object",
  "e1 8 67.8; e2 13 78.5; k1 18.1 63.1; k2 23.1 73.8; a0 26.9 55.4; b0 34.6 72.1; a1 47.9 44.5;"
  "b1 56.5 62.9; a2 67.7 34.1; b2 77.1 54.4; a3 81.5 26.3; b3 92 48.9; hub 56.5 75.4;"
  "fl 34.2 113.7; fm 59.1 116.3; fr 82.8 113.7; sl 44.2 96.4; sm 58 97.9; sr 71 96.4;"
  "sc 28.1 28.2; st 28.1 17; sb 28.1 39.4; sw 16.9 28.2; se 39.3 28.2",
  ["k1 k2 e2 e1 k1 a0 a1 a2 a3 b3 b2 b1 b0 k2", "a0 b0", "a1 b1 hub sl fl", "a2 b2",
   "fm sm hub sr fr", "sl sm sr", "st sc sb", "sw sc se"],
  clue="Seeing stars on purpose")

P("ant", "Ant", "animal",
  "hl 38.4 36.4; ael 33.1 18.7; atl 18 8; tl 40.2 61.3; kfl 23.3 47.1; ffl 10 32.9;"
  "fml 9.1 68.4; kbl 21.6 79.1; fbl 8.2 104; al1l 32.2 88.9; al2l 27.8 109.3; hr 61.6 36.4;"
  "aer 66.9 18.7; atr 82 8; tr 59.8 61.3; kfr 76.7 47.1; ffr 90 32.9; fmr 90.9 68.4;"
  "kbr 78.4 79.1; fbr 91.8 104; al1r 67.8 88.9; al2r 72.2 109.3; ht 50 24; n1 50 48.9;"
  "n2 50 75.6; ab 50 125.3",
  ["hl ht hr n1 hl ael atl", "tl n1 tr n2 tl kfl ffl", "tl fml", "tl kbl fbl",
   "al1l n2 al1r al2r ab al2l al1l al1r", "hr aer atr", "tr kfr ffr", "tr fmr", "tr kbr fbr"],
  clue="I can lift fifty times my own weight")

P("corn", "Corn on the cob", "plant",
  "T 50 10.1; o2L 30.8 26.5; v1L 41.8 28.3; o3L 28.1 43.8; v2L 41.8 43.8; o4L 28.1 59.4;"
  "v3L 41.8 59.4; o5L 29.9 74.9; v4L 41.8 74.9; tL 8 48.4; loL 9.8 79.4; lbL 26.3 101.4;"
  "Bm 50 110.5; St 50 123.3; o2R 69.2 26.5; v1R 58.2 28.3; o3R 71.9 43.8; v2R 58.2 43.8;"
  "o4R 71.9 59.4; v3R 58.2 59.4; o5R 70.1 74.9; v4R 58.2 74.9; tR 92 48.4; loR 90.2 79.4;"
  "lbR 73.7 101.4",
  ["o2L T o2R o3R o4R o5R v4R v3R v2R v1R T v1L v2L v3L v4L o5L o4L o3L o2L v1L v1R o2R",
   "o3L v2L v2R o3R", "o4L v3L v3R o4R", "v4L v4R",
   "Bm lbL loL tL o5L Bm lbR loR tR o5R Bm St"],
  clue="All ears, and a-maize-ing at it")

P("train", "Steam train", "object",
  "c1 8 32.9; c2 32 32.9; c3 32 53.9; c4 8 80.9; s1 53 53.9; s2 48.5 35.9; s3 69.5 35.9;"
  "s4 65 53.9; f1 80 53.9; f2 80 80.9; cc 92 100.4; cb 80 100.4; w0 20.4 80.9; w1 31.6 80.9;"
  "w2 37.2 90.7; w3 31.6 100.4; w4 20.4 100.4; w5 14.7 90.7; v0 54.9 80.9; v1 66.1 80.9;"
  "v2 71.8 90.7; v3 66.1 100.4; v4 54.9 100.4; v5 49.2 90.7",
  ["s1 c3 c2 c1 c4 w0 w1 v0 v1 f2 f1 s4 s1 s2 s3 s4", "f2 cc cb v2 v1", "w0 w5 w4 w3 w2 w1",
   "w2 v5 v4 v3 v2", "v0 v5"],
  clue="Choo-choo-choose me!")

P("pencil", "Pencil", "object",
  "ea 33.5 8; eb 16.8 17.6; f0a 44.8 13.5; f0b 15.9 30.2; f1a 50.4 23.1; f1b 21.4 39.8;"
  "f2a 55.9 32.7; f2p 46.3 38.3; f2q 36.6 43.9; f2b 27 49.4; sa 78.9 72.6; sp 69.3 78.1;"
  "sq 59.6 83.7; sb 50 89.2; k1 79.7 85; k2 70 90.5; k3 60.4 96.1; la 82.6 101.2; lb 73 106.8;"
  "tip 84.1 114.9; w0 70.8 122.4; w1 58.9 113.5; w2 47 123.8; w3 35.2 114.9; w4 23.3 125.3",
  ["f0a ea eb f0b f1b f2b sb k3 lb tip la k1 sa f2a f1a f0a f0b", "f1a f1b", "f2a f2p f2q f2b",
   "f2p sp k1", "f2q sq k2 sp", "sq k3", "la lb", "tip w0 w1 w2 w3 w4"],
  clue="Sharp wit, but I always get the point")

P("bear", "Bear", "animal",
  "hal 35.6 35.9; hbl 16.1 53.5; hcl 13.9 84.6; hdl 33.8 106.3; e1l 27.1 27; e2l 15 28.1;"
  "e3l 8 38.1; iel 21.1 39.3; eyal 34.8 55.5; eybl 36.4 66.7; mtl 40.4 77.9; ml 33.2 90.7;"
  "har 64.4 35.9; hbr 83.9 53.5; hcr 86.1 84.6; hdr 66.2 106.3; e1r 72.9 27; e2r 85 28.1;"
  "e3r 92 38.1; ier 78.9 39.3; eyar 65.2 55.5; eybr 63.6 66.7; mtr 59.6 77.9; mr 66.8 90.7;"
  "nb 50 87.5; m0 50 99.5",
  ["eyal eybl", "mtl ml m0 mr mtr mtl nb mtr", "eyar eybr", "nb m0",
   "hal hbl hcl hdl hdr hcr hbr har hal e1l e2l e3l hbl iel hal",
   "har e1r e2r e3r hbr ier har"],
  clue="Someone's been sleeping in my bed!")

P("pizza", "Pizza slice", "object",
  "o0 9.8 19.3; o1 29.1 11.2; o2 50 8; o3 70.9 11.2; o4 90.2 19.3; tip 50 125.3; i0 15.3 33.7;"
  "i4 84.7 33.7; i1 31.5 27.3; i2 50 24.9; i3 68.5 27.3; p0 40.4 43.4; p1 49.5 50; p2 46.1 60.8;"
  "p3 34.7 60.8; p4 31.2 50; qa 77 54; qb 67.4 79.3; q1 65.5 53; q2 57.3 61; q3 58.1 72.5;"
  "ra 35.2 86.4; rb 43.2 107.3; r1 47.2 87.4; r2 51.4 98.7",
  ["o1 o0 i0 ra rb tip qb qa i4 o4 o3 o2 o1 i1 i0", "o3 i3 i2 i1", "i4 i3", "qa q1 q2 q3 qb",
   "ra r1 r2 rb", "p0 p1 p2 p3 p4 p0"],
  clue="That's amore!")

P("trafficlight", "Traffic light", "object",
  "TL 30.7 8; TR 69.3 8; L1 30.7 38.4; R1 69.3 38.4; L2 30.7 68.7; R2 69.3 68.7; BL 30.7 99.1;"
  "BR 69.3 99.1; Q 50 110.1; G 50 125.3; x0 50 14.6; x1 59.2 21.3; x2 55.7 32; x3 44.3 32;"
  "x4 40.8 21.3; y0 50 44.9; y1 59.2 51.6; y2 55.7 62.4; y3 44.3 62.4; y4 40.8 51.6; z0 50 75.3;"
  "z1 59.2 82; z2 55.7 92.8; z3 44.3 92.8; z4 40.8 82",
  ["L1 L2 BL BR R2 R1 TR TL L1 R1", "L2 R2", "BL Q BR", "Q G", "x0 x1 x2 x3 x4 x0",
   "y0 y1 y2 y3 y4 y0", "z0 z1 z2 z3 z4 z0"],
  clue="Stop, wait for it... go!")

P("pumpkin", "Pumpkin", "plant",
  "SBL 43 58.7; U1L 28 56.7; U2L 14 66.7; LL 8 82.7; D2L 14 100.7; D1L 28 112.7; B 50 116.7;"
  "R1L 22 84.7; R2L 38 85.7; SBR 57 58.7; U1R 72 56.7; U2R 86 66.7; LR 92 82.7; D2R 86 100.7;"
  "D1R 72 112.7; R1R 78 84.7; R2R 62 85.7; STL 45 40.7; STR 57 38.7; LS1 66 26.7; Lt 87 22.7;"
  "LS2 76 38.7; C1 34 34.7; C2 28 23.7; C3 39 16.7",
  ["U1L SBL SBR U1R U2R LR D2R D1R B D1L D2L LL U2L U1L R1L D1L", "U1R R1R D1R",
   "STL SBL R2L B R2R SBR STR STL C1 C2 C3", "STR LS1 Lt LS2 STR Lt"],
  clue="Your ride, Cinderella... until midnight")

P("well", "Wishing well", "object",
  "pk 50 10.8; eL 8 37.7; pL 21.4 37.7; xL 21.4 52.8; xc 50 52.8; rL 9.7 86.4; r2L 21.4 84.3;"
  "fL 29.8 94.8; fc 50 97.3; wL 9.7 118.3; w2L 29.8 120.8; wc 50 122.5; bt1L 38.2 64.6;"
  "bb1L 41.6 78; eR 92 37.7; pR 78.6 37.7; xR 78.6 52.8; rR 90.3 86.4; r2R 78.6 84.3;"
  "fR 70.2 94.8; wR 90.3 118.3; w2R 70.2 120.8; bt1R 61.8 64.6; bb1R 58.4 78; bt 50 64.6",
  ["pL eL pk eR pR xR r2R rR fR fc fL rL r2L xL pL pR", "xL xc xR",
   "xc bt bt1L bb1L bb1R bt1R bt", "rL wL w2L wc w2R wR rR", "r2L r2R", "fL w2L", "fc wc",
   "fR w2R"],
  clue="Toss a coin and hope")

P("beetle", "Beetle", "animal",
  "hL 42.2 27.8; aL 28.2 13.8; pL 36 37.1; pbL 26.7 55.8; pc 50 55.8; e1L 22 83.8;"
  "e2L 32.9 108.7; bot 50 119.6; k1L 22 34; f1L 15.8 21.6; k2L 14.2 62; f2L 8 76; k3L 12.7 94.7;"
  "f3L 14.2 111.8; hR 57.8 27.8; aR 71.8 13.8; pR 64 37.1; pbR 73.3 55.8; e1R 78 83.8;"
  "e2R 67.1 108.7; k1R 78 34; f1R 84.2 21.6; k2R 85.8 62; f2R 92 76; k3R 87.3 94.7;"
  "f3R 85.8 111.8",
  ["hL aL", "hL pL pbL pc pbR pR hR aR", "hL hR", "pL k1L f1L", "pc bot e2L e1L pbL k2L f2L",
   "e1L k3L f3L", "bot e2R e1R pbR k2R f2R", "pR k1R f1R", "e1R k3R f3R"],
  clue="Crawling in armour since the dinosaurs")

P("bell", "Bell", "object",
  "sL 36 32.4; aL 25.1 40.1; bL 21.2 54.1; cL 19.7 69.7; eL 17.3 82.9; fL 8 94.6; gL 8 107;"
  "mL 29 107; sR 64 32.4; aR 74.9 40.1; bR 78.8 54.1; cR 80.3 69.7; eR 82.7 82.9; fR 92 94.6;"
  "gR 92 107; mR 71 107; t 50 27.7; b0 50 107; q1 39.7 20.2; q2 43.6 8; q3 56.4 8; q4 60.3 20.2;"
  "k1 59.6 114; k2 55.9 125.3; k3 44.1 125.3; k4 40.4 114",
  ["aL bL cL eL fL gL mL b0 mR gR fR eR cR bR aR sR t sL aL aR", "eL eR", "fL fR",
   "t q1 q2 q3 q4 t", "b0 k1 k2 k3 k4 b0"],
  clue="Saved by me at the end of class")

P("burger", "Burger", "object",
  "t0L 14.9 59.4; t1L 17.9 42.6; t2L 31.7 30.4; t3 50 25.8; pk1L 32.4 59.4; pk2 50 59.4;"
  "v1L 23.7 72.4; v2L 41.2 72.4; pt0L 11.8 72.4; peL 8 83.1; pb0L 11.8 93.8; bbL 16.4 107.5;"
  "sa1L 30.1 48; sa2L 40.1 41.1; t0R 85.1 59.4; t1R 82.1 42.6; t2R 68.3 30.4; pk1R 67.6 59.4;"
  "v1R 76.3 72.4; v2R 58.8 72.4; pt0R 88.2 72.4; peR 92 83.1; pb0R 88.2 93.8; bbR 83.6 107.5;"
  "sa1R 69.9 48; sa2R 59.9 41.1",
  ["t0L t1L t2L t3 t2R t1R t0R pk1R pk2 pk1L t0L v1L pk1L v2L pk2 v2R pk1R v1R t0R",
   "pb0L peL pt0L v1L v2L v2R v1R pt0R peR pb0R bbR bbL pb0L pb0R", "sa1L sa2L", "sa1R sa2R"],
  clue="Hold the pickles, please")

P("crab", "Crab", "animal",
  "b1L 38.3 58.5; b1R 61.7 58.5; b2L 23.2 70.2; b2R 76.8 70.2; b4L 33.7 84.2; b4R 66.3 84.2;"
  "eL 39.5 46.8; eR 60.5 46.8; wL 18.5 56.2; wR 81.5 56.2; oL 8 44.5; oR 92 44.5; uL 15 29.3;"
  "uR 85 29.3; nL 20.8 42.2; nR 79.2 42.2; lL 32.5 34; lR 67.5 34; k1L 8 76; k1R 92 76;"
  "f1L 8 88.8; f1R 92 88.8; k2L 23.2 92.3; k2R 76.8 92.3; f2L 26.7 104; f2R 73.3 104",
  ["b1L b1R b2R b4R b4L b2L b1L eL", "b1R eR", "b4L k2L f2L", "b4R k2R f2R", "wL b2L k1L f1L",
   "wL oL uL nL lL wL", "wR b2R k1R f1R", "wR oR uR nR lR wR"],
  clue="Pinch me, I must be dreaming")

P("bus", "Bus", "object",
  "a 8 33; b 92 33; c 92 90.1; dd 8 90.1; t0 14.7 44.8; u0 14.7 63.3; t1 31.5 44.8;"
  "u1 31.5 63.3; t2 48.3 44.8; u2 48.3 63.3; t3 65.1 44.8; u3 65.1 63.3; t4 81.9 44.8;"
  "u4 81.9 63.3; w0 19.8 90.1; w1 25.6 80; w2 37.4 80; w3 43.3 90.1; w4 37.4 100.3;"
  "w5 25.6 100.3; v0 56.7 90.1; v1 62.6 80; v2 74.4 80; v3 80.2 90.1; v4 74.4 100.3;"
  "v5 62.6 100.3",
  ["t1 t0 u0 u1 u2 u3 u4 t4 t3 t2 t1 u1", "t2 u2", "t3 u3",
   "w0 dd a b c v3 v2 v1 v0 w3 w2 w1 w0 w5 w4 w3", "v0 v5 v4 v3"],
  clue="Please move down to the back!")

P("cactus", "Cactus", "plant",
  "ct 50 13.4; ctL 38.7 23.1; ctR 61.3 23.1; jL1 38.7 58.6; jL2 38.7 76.4; jR1 61.3 45.7;"
  "jR2 61.3 61.8; bL 38.7 87.7; b0 50 87.7; bR 61.3 87.7; aEL 25.8 58.6; aIL 25.8 44.1;"
  "aTL 16.9 32.7; aOL 8 45.7; aBL 12.8 76.4; aER 74.2 45.7; aIR 74.2 31.1; aTR 83.1 19.8;"
  "aOR 92 32.7; aBR 87.2 61.8; pTL 20.9 87.7; pTR 79.1 87.7; pML 20.9 99; pMR 79.1 99;"
  "pBL 29.8 120; pBR 70.2 120",
  ["ct ctL jL1 jL2 bL pTL pML pMR pTR bR jR2 jR1 ctR ct b0 bL", "jL1 aEL aIL aTL aOL aBL jL2",
   "jR1 aER aIR aTR aOR aBR jR2", "b0 bR", "pML pBL pBR pMR"],
  clue="Don't hug me, I'm a little prickly")

P("church", "Church", "object",
  "ct 50 8; cl 38.7 19.3; cr 61.3 19.3; cc 50 19.3; st 50 32.1; sbl 30.7 53; sbr 69.3 53;"
  "tjl 30.7 85.2; tjr 69.3 85.2; el 9.8 96.4; er 90.2 96.4; gl 9.8 125.3; gr 90.2 125.3;"
  "tgl 30.7 125.3; tgr 69.3 125.3; dl 42 125.3; dr 58 125.3; dml 42 107.7; dmr 58 107.7;"
  "dt 50 96.4; w0 50 60.2; w1 39.6 66.3; w2 39.6 78.3; w3 50 84.3; w4 60.4 78.3; w5 60.4 66.3",
  ["ct cc st sbl sbr st", "cl cc cr", "sbl tjl tgl gl el tjl", "sbr tjr tgr dr dl tgl",
   "tjr er gr tgr", "dl dml dt dmr dr", "w0 w1 w2 w3 w4 w5 w0 w3", "w1 w4", "w2 w5"],
  clue="Sunday best, bells on")

P("ladybug", "Ladybug", "animal",
  "b0 50 37.6; b1 75.8 46; b2 91.7 67.9; b3 91.7 95; b4 75.8 116.9; b5 50 125.3; b6 24.2 116.9;"
  "b7 8.3 95; b8 8.3 67.9; b9 24.2 46; hL 30 31.8; hA 41.4 21.4; hB 58.6 21.4; hR 70 31.8;"
  "nL 29 8; nR 71 8; m1 50 50.9; m2 50 68.1; x1 40.5 59.5; x2 59.5 59.5; p00L 30 82.9;"
  "p01L 39 97.9; p02L 20.9 97.9; p00R 70 82.9; p01R 79.1 97.9; p02R 61 97.9",
  ["b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b0 m1 m2 b5", "b1 hR hB hA hL b9", "hA nL", "hB nR",
   "m1 x1 m2 x2 m1", "p00L p01L p02L p00L", "p00R p01R p02R p00R"],
  clue="Seven spots and a lucky streak")

P("clock", "Alarm clock", "object",
  "h0 50 32.6; h1 68.1 37.4; h2 81.4 50.7; h3 86.2 68.8; h4 81.4 86.9; h5 68.1 100.2; h6 50 105;"
  "h7 31.9 100.2; h8 18.6 86.9; h9 13.8 68.8; h10 18.6 50.7; h11 31.9 37.4; t0 50 45.3;"
  "t3 73.5 68.8; t6 50 92.3; t9 26.5 68.8; bR1 82.8 26.8; bR2 92 36; bL1 17.2 26.8; bL2 8 36;"
  "hm 50 17.6; fl 20.2 115.7; fr 79.8 115.7; ctr 50 68.8; hh 37.1 61.3; mh 68.5 58.1",
  ["h1 h0 h11 h10 h9 h8 h7 h6 h5 h4 h3 h2 h1 bR1 bR2 h2", "h3 t3", "h5 fr", "h6 t6", "h7 fl",
   "h9 t9", "h10 bL2 bL1 h11", "t0 h0 hm", "hh ctr mh"],
  clue="Five more minutes, please!")

P("compass", "Compass", "object",
  "c0 50 40.4; c1 71 46.1; c2 86.3 61.4; c3 92 82.4; c4 86.3 103.4; c5 71 118.8; c6 50 124.4;"
  "c7 29 118.8; c8 13.7 103.4; c9 8 82.4; c10 13.7 61.4; c11 29 46.1; o 50 82.4; tn 50 54.1;"
  "te 78.3 82.4; ts 50 110.7; tw 21.7 82.4; v0 59.1 73.3; v1 59.1 91.5; v2 40.9 91.5;"
  "v3 40.9 73.3; k 50 28.3; q1 39.5 21; q2 43.5 8.9; q3 56.5 8.9; q4 60.5 21",
  ["c3 c2 c1 c0 c11 c10 c9 c8 c7 c6 c5 c4 c3 te v0 tn v3 tw v2 ts v1 te o tn c0 k q1 q2 q3 q4 k",
   "c6 ts o tw c9"],
  clue="Always pointing north, never lost")

P("dice", "Dice", "object",
  "C 50 66.7; TL 8 42.4; T 50 18.2; TR 92 42.4; BL 8 90.9; B 50 115.2; BR 92 90.9; p0 50 30.8;"
  "p1 60.1 48.2; p2 39.9 48.2; pc 50 42.4; q0 16.5 57.1; q1 26.3 62.8; q2 16.5 68.5;"
  "r0 41.5 100.5; r1 31.7 94.8; r2 41.5 89.1; s0 84.8 54.9; s1 84.8 66.3; s2 75 60.6;"
  "t0 74.3 73.1; t1 74.3 84.5; t2 64.5 78.8; u0 57.2 102.7; u1 57.2 91.3; u2 67.1 97",
  ["C TL T TR C B BL TL", "TR BR B", "p0 p1 p2 p0 pc p1", "p2 pc", "q0 q1 q2 q0",
   "r0 r1 r2 r0", "s0 s1 s2 s0", "t0 t1 t2 t0", "u0 u1 u2 u0"],
  clue="Feeling lucky? Roll with it")

P("octopus", "Octopus", "animal",
  "top 50 20; uL 31.3 26.2; sL 22 43.3; bL 26.7 62; mL 39.1 69.8; mid 50 71.3; eL1 40.7 40.2;"
  "eL2 40.7 52.7; aL1 17.3 80.7; aL2 8 97.8; aL3 20.4 100.9; bL1 32.9 90; bL2 37.6 110.2;"
  "c1 50 93.1; c2 50 113.3; uR 68.7 26.2; sR 78 43.3; bR 73.3 62; mR 60.9 69.8; eR1 59.3 40.2;"
  "eR2 59.3 52.7; aR1 82.7 80.7; aR2 92 97.8; aR3 79.6 100.9; bR1 67.1 90; bR2 62.4 110.2",
  ["bL mL mid mR bR sR uR top uL sL bL aL1 aL2 aL3 aL1", "mL bL1 bL2", "mid c1 c2", "eL1 eL2",
   "bR aR1 aR2 aR3 aR1", "mR bR1 bR2", "eR1 eR2"],
  clue="Eight arms and still can't hug enough")

P("mushroom2", "Toadstool", "plant",
  "c0 8 65.2; c1 13.6 43.4; c2 29 27.5; c3 50 21.7; c4 71 27.5; c5 86.4 43.4; c6 92 65.2;"
  "u1 30.5 66.7; u3 69.5 66.7; sL 41.7 80.2; sR 58.3 80.2; mL 41 92.2; mR 59 92.2; fL 35 111.7;"
  "fR 65 111.7; p0 50 33.7; p1 59.3 40.4; p2 55.7 51.3; p3 44.3 51.3; p4 40.7 40.4;"
  "a0 26.7 42.7; a1 33.3 53.9; a2 20.2 53.9; b0 73.2 42.7; b1 79.8 53.9; b2 66.7 53.9",
  ["c0 c1 c2 c3 c4 c5 c6 u3 u1 c0 sL sR c6", "u1 sL mL fL fR mR sR u3", "mL mR",
   "p0 p1 p2 p3 p4 p0", "a0 a1 a2 a0", "b0 b1 b2 b0"],
  clue="Fairy furniture, do not eat")

P("flag", "Flag", "object",
  "g00 19.3 17; g01 38.7 11.3; g02 56.5 17; g03 74.2 22.6; g04 92 17; g12 56.5 31.5;"
  "g13 74.2 37.2; g14 92 31.5; g20 19.3 46.1; g21 38.7 40.4; g22 56.5 46.1; g23 74.2 51.7;"
  "g24 92 46.1; g30 19.3 60.6; g31 38.7 55; g32 56.5 60.6; g33 74.2 66.3; g34 92 60.6;"
  "g40 19.3 75.1; g41 38.7 69.5; g42 56.5 75.1; g43 74.2 80.8; g44 92 75.1; bot 19.3 122;"
  "bl 8 122; br 30.6 122",
  ["g02 g01 g00 g20 g30 g40 bot bl", "g02 g03 g04 g14 g13 g12 g02", "g12 g22 g21 g20",
   "g14 g24 g23 g22", "g24 g34 g33 g32 g31 g30", "g34 g44 g43 g42 g41 g40", "bot br"],
  clue="Run me up the pole and salute")

P("laptop", "Laptop", "object",
  "s0 15.3 8; s1 84.7 8; s2 84.7 59.2; s3 15.3 59.2; i0 26.9 18.7; i1 73.1 18.7; i2 73.1 48.5;"
  "i3 26.9 48.5; b0 8.7 125.3; b1 91.3 125.3; k0 23.6 67.5; k1 36.8 67.5; k2 50 67.5;"
  "k3 63.2 67.5; k4 76.4 67.5; m0 21.9 80.7; m4 78.1 80.7; n0 20.3 93.9; n1 36.8 93.9;"
  "n2 50 93.9; n3 63.2 93.9; n4 79.7 93.9; p0 43.4 105.5; p1 56.6 105.5; p2 56.6 117.1;"
  "p3 43.4 117.1",
  ["s2 s1 s0 s3 s2 b1 b0 s3", "k1 k0 m0 n0 n1 n2 n3 n4 m4 k4 k3 k2 k1 n1", "k2 n2", "k3 n3",
   "m0 m4", "i0 i1 i2 i3 i0", "p0 p1 p2 p3 p0"],
  clue="Ctrl+Alt+Del my way to your lap")

P("penguin", "Penguin", "animal",
  "top 50 16.1; o1L 36 22.3; o2L 26.7 36.3; o3L 22 56.6; o4L 23.6 83; o5L 34.4 103.2;"
  "bot 50 107.9; fL 8 87.7; vn 50 41; i1L 40.7 33.2; i2L 32.9 59.7; bk1 43.8 51.9;"
  "bk2 56.2 51.9; bk3 50 62.8; tL 28.2 117.2; t2L 43.8 117.2; o1R 64 22.3; o2R 73.3 36.3;"
  "o3R 78 56.6; o4R 76.4 83; o5R 65.6 103.2; fR 92 87.7; i1R 59.3 33.2; i2R 67.1 59.7;"
  "tR 71.8 117.2; t2R 56.2 117.2",
  ["o3L o2L o1L top o1R o2R o3R o4R o5R bot o5L o4L o3L fL o4L", "o3R fR o4R",
   "o2L i1L vn i1R o2R i2R o5R tR t2R bot t2L tL o5L i2L o2L", "bk1 bk2 bk3 bk1"],
  clue="Always dressed for a black-tie event")

P("robot", "Robot", "object",
  "an 50 13.8; ab 50 25.4; htL 26.8 25.4; hbL 26.8 64.5; btL 15.2 64.5; bbL 15.2 103.6;"
  "lgL 35.5 103.6; ftL 35.5 119.5; hdL 8 93.5; e1L 32.6 35.5; e2L 44.2 35.5; e3L 44.2 47.1;"
  "e4L 32.6 47.1; mL 38.4 57.3; htR 73.2 25.4; hbR 73.2 64.5; btR 84.8 64.5; bbR 84.8 103.6;"
  "lgR 64.5 103.6; ftR 64.5 119.5; hdR 92 93.5; e1R 67.4 35.5; e2R 55.8 35.5; e3R 55.8 47.1;"
  "e4R 67.4 47.1; mR 61.6 57.3",
  ["an ab htL hbL hbR htR ab", "hbL btL bbL lgL lgR bbR btR hbR", "btL hdL", "lgL ftL",
   "mL mR", "btR hdR", "lgR ftR", "e1L e2L e3L e4L e1L", "e1R e2R e3R e4R e1R"],
  clue="Beep boop, I come in peace")

P("snowman", "Snowman", "object",
  "bmL 29 32.2; bmR 71 32.2; crL 41.7 32.2; crR 58.3 32.2; ctL 41.7 9.7; ctR 58.3 9.7;"
  "sL 24.5 50.2; sR 75.5 50.2; nkL 38.7 66.7; nkR 61.3 66.7; nm 50 66.7; b1L 23 81.7;"
  "b1R 77 81.7; b2L 15.5 102.7; b2R 84.5 102.7; b3L 35 123.7; b3R 65 123.7; hdL 9.5 71.2;"
  "hdR 90.5 71.2; fgL 8 56.2; fgR 92 56.2; nb1 47 42.7; nb2 47 54.7; ntip 81.5 62.2;"
  "bt1 50 84.7; bt2 50 102.7",
  ["crL bmL sL nkL nm nkR sR bmR crR crL ctL ctR crR", "nkL b1L b2L b3L b3R b2R b1R nkR",
   "nm bt1 bt2", "b1L hdL fgL", "b1R hdR fgR", "nb1 nb2 ntip nb1"],
  clue="Chilling out until spring")

P("daisy", "Daisy", "plant",
  "c0 50 59.4; t0l 41.3 80.3; t0r 30.6 75.9; c1 39.2 54.9; t1l 18.3 63.6; t1r 13.8 52.9;"
  "c2 34.8 44.2; t2l 13.8 35.5; t2r 18.3 24.7; c3 39.2 33.4; t3l 30.6 12.4; t3r 41.3 8;"
  "c4 50 29; t4l 58.7 8; t4r 69.4 12.4; c5 60.8 33.4; t5l 81.7 24.7; t5r 86.2 35.5;"
  "c6 65.2 44.2; t6l 86.2 52.9; t6r 81.7 63.6; c7 60.8 54.9; t7l 69.4 75.9; t7r 58.7 80.3;"
  "Lb 50 100; S 50 125.3; Lt 77.1 93.2; Ls 68.6 111.8",
  ["c0 t0l t0r c1 t1l t1r c2 t2l t2r c3 t3l t3r c4 t4l t4r c5 t5l t5r c6 t6l t6r c7 t7l t7r c0 c1 c2 c3 c4 c5 c6 c7 c0 Lb S",
   "Lb Lt Ls Lb"],
  clue="He loves me, he loves me not...")

P("trophy", "Trophy", "object",
  "rL 20 15.7; rR 80 15.7; bdL 21.5 27.7; bdR 78.5 27.7; c1L 26 44.2; c1R 74 44.2; c2L 35 56.2;"
  "c2R 65 56.2; nL 44 65.2; nR 56 65.2; h1L 8 18.7; h1R 92 18.7; h2L 8 35.2; h2R 92 35.2;"
  "h3L 12.5 48.7; h3R 87.5 48.7; sL 44 77.2; sR 56 77.2; btL 30.5 90.7; btR 69.5 90.7;"
  "bbL 30.5 117.7; bbR 69.5 117.7; pqL 41 98.2; pqR 59 98.2; pbL 41 110.2; pbR 59 110.2",
  ["rL rR bdR c1R c2R nR sR btR bbR bbL btL sL nL c2L c1L bdL rL h1L h2L h3L c2L",
   "rR h1R h2R h3R c2R", "bdL bdR", "nL nR", "sL sR", "btL btR", "pqL pqR pbR pbL pqL"],
  clue="Winner winner, chicken dinner")

P("spider", "Spider", "animal",
  "c0 50 55.8; c1 60.3 63.3; c2 56.4 75.5; c3 43.6 75.5; c4 39.7 63.3; thr 50 15.3; aL 36 91.6;"
  "aBL 42.2 113.3; k1L 32.9 41.8; f1L 17.3 32.4; k2L 23.6 55.8; f2L 8 71.3; k3L 20.4 76;"
  "f3L 8 94.7; k4L 23.6 96.2; f4L 20.4 118; aR 64 91.6; aBR 57.8 113.3; k1R 67.1 41.8;"
  "f1R 82.7 32.4; k2R 76.4 55.8; f2R 92 71.3; k3R 79.6 76; f3R 92 94.7; k4R 76.4 96.2;"
  "f4R 79.6 118",
  ["c0 thr", "c0 c1 c2 c3 c4 c0", "c2 aR aBR aBL aL c3 k3L f3L", "c2 k3R f3R", "c2 k4R f4R",
   "c3 k4L f4L", "aL aR", "f1L k1L c4 k2L f2L", "f1R k1R c1 k2R f2R"],
  clue="Along came one and sat down beside her")

P("violin", "Violin", "object",
  "SC 50 8; P1L 43 17.9; PBL 44 31.9; NBL 44 51.8; UBL 20.2 65.7; C2L 25.1 81.6; C1L 25.1 97.5;"
  "LWL 13.2 109.4; LBL 26.1 122.4; B 50 125.3; FEL 44 79.6; BRL 44 96.5; FaL 35.1 86.6;"
  "FbL 33.1 105.4; PBR 56 31.9; NBR 56 51.8; UBR 79.8 65.7; C2R 74.9 81.6; C1R 74.9 97.5;"
  "LWR 86.8 109.4; LBR 73.9 122.4; FER 56 79.6; BRR 56 96.5; FaR 64.9 86.6; FbR 66.9 105.4;"
  "S2 59.9 16",
  ["FEL NBL UBL C2L C1L LWL LBL B LBR LWR C1R C2R UBR NBR NBL PBL P1L SC S2 PBR NBR FER BRR B BRL FEL FER",
   "BRL BRR", "FaL FbL", "FaR FbR"],
  clue="Chin up, bow ready!")

P("bat", "Bat", "animal",
  "earL 43.5 42.4; headT 50 52.1; shL 41.1 60.2; wristL 27.4 44.1; tipL 8 65.1; v1L 19.3 68.3;"
  "f2L 25.8 84.4; v2L 32.2 73.1; hipL 41.9 81.2; bot 50 90.9; earR 56.5 42.4; shR 58.9 60.2;"
  "wristR 72.6 44.1; tipR 92 65.1; v1R 80.7 68.3; f2R 74.2 84.4; v2R 67.8 73.1; hipR 58.1 81.2",
  ["shL earL headT earR shR wristR tipR v1R f2R v2R hipR shR",
   "shL wristL tipL v1L f2L v2L hipL shL", "f2L wristL hipL bot hipR wristR f2R"],
  clue="Hangs out upside down all day")

P("key2", "Key", "object",
  "b1 20 8; b2 4 34; b3 20 60; b4 48 60; b5 62 34; b6 48 8; h1 32 26; h2 32 44;t1 82 34;"
  "t2 82 58; t3 102 34; t4 102 56; e 118 34",
  ["b1 b2 b3 b4 b5 b6 b1", "h1 h2", "b1 h1", "b3 h2", "b5 t1", "t1 t2", "t1 t3", "t3 t4", "t3 e"])

P("bee", "Bee", "animal",
  "t1 44.3 67; t2 56.4 64.9; t3 68.5 67.7; br 80.6 79.8; u3 68.5 91.9; u2 56.4 94.8;"
  "u1 44.3 92.6; st 92 82; wa1 35.1 48.5; wa2 46.4 38.5; wb1 62.1 38.5; wb2 74.9 47.1;"
  "h1 26.2 90; h2 14.3 86.1; h3 14.3 73.6; h4 26.2 69.7; bf 33.6 79.8; an1 8 59.9;"
  "an2 23.7 54.2",
  ["t2 t1 bf h1 h2 h3 h4 bf u1 u2 u3 br t3 t2 u2", "t2 wa2 wa1 t1 u1", "t2 wb1 wb2 t3 u3",
   "br st", "h3 an1", "h4 an2"],
  clue="Buzz off, I'm busy!")

P("tent", "Tent", "object",
  "pk 50 26.1; bl 17.8 93.3; br 82.2 93.3; d1 38.8 93.3; d2 50 45.7; d3 61.2 93.3;"
  "g1 50 104.5; gl 8 84.9; gr 92 84.9; pl 17.8 107.3; pr 82.2 107.3; f1 37.4 68.1;"
  "f2 62.6 68.1",
  ["pk bl d1 d3 br pk d2 d1 g1 d3 d2", "pl bl gl", "pr br gr", "f1 f2"])

P("strawberry", "Strawberry", "plant",
  "t1 30.8 48.4; t2 50 42.6; t3 69.2 48.4; r1 86.5 69.6; b 50 125.3; l1 13.5 69.6;"
  "sd1 34.6 75.3; sd2 50 67.6; sd3 65.4 75.3; sd4 40.4 96.5; sd5 59.6 96.5; lf1 25 29.2;"
  "lf2 50 23.4; lf3 75 29.2; st 50 8",
  ["t1 t2 t3 r1 b l1 t1 sd1 sd2 t2 lf1", "sd3 sd2", "t3 sd3 sd5 sd4 sd1", "lf3 t2 lf2 st"])

P("hedgehog", "Hedgehog", "animal",
  "s0 18 62; s1 22 45; s2 35 33; s3 52 28; s4 69 33; s5 82 45; s6 86 62; p0 0 62;"
  "p1 6 36;p2 26 16; p3 52 10; p4 78 16; p5 98 36; p6 104 62; sn 112 78; fb 74 94;"
  "bb 30 96;ey 72 72; ey2 88 78",
  ["s0 s1 s2 s3 s4 s5 s6", "s0 p0", "s1 p1", "s2 p2", "s3 p3", "s4 p4", "s5 p5", "s6 p6",
   "s6 sn", "sn fb", "fb bb", "bb s0", "ey ey2"])

P("microphone", "Microphone", "object",
  "h1 33.5 8; h2 66.5 8; h3 70.6 45.1; h4 29.4 45.1; m1 39.7 26.5; m2 60.3 26.5;"
  "n1 39.7 57.4; n2 60.3 57.4; b1 33.5 82.1; b2 66.5 82.1; s 50 82.1; st 50 115;"
  "f1 29.4 125.3; f2 70.6 125.3",
  ["h1 h2 h3 h4 h1 m1 m2 h2", "n1 h4", "n2 h3", "s b1 n1 n2 b2 s st f1", "st f2"])

P("frog", "Frog", "animal",
  "e0 39.9 16; e1 54.9 24.7; e2 54.9 42; e3 39.9 50.7; e4 24.8 42; e5 24.8 24.7; pa 39.9 27.6;"
  "pb 39.9 39.1; sn 8 56.5; mc 42.8 63.8; cn 13.8 69.6; ch 26.8 81.1; fw 25.4 104.3;"
  "f1 12.3 110.1; f2 28.3 115.9; bl 42.8 95.6; bk 73.2 50.7; rp 92 72.5; th 71.7 71;"
  "kn 58.7 89.8; he 89.1 104.3; t1 54.3 107.2; t2 58.7 117.4",
  ["e2 e1 e0 e5 e4 e3 e2 bk rp he kn bl ch cn sn e4", "pa pb", "sn mc", "ch fw f1", "fw f2",
   "bk th kn", "t1 he t2"],
  clue="Ribbit if you love lily pads")

P("candle", "Candle", "object",
  "tl 30.4 48.9; tr 69.6 48.9; d1 30.4 64.9; d2 19.8 77.3; d3 30.4 89.8; bl 30.4 112.9;"
  "br 69.6 112.9; w 50 41.8; fl 39.3 27.6; ft 50 8; fr 60.7 27.6; p1 12.7 112.9;"
  "p2 87.3 112.9; pb1 21.6 125.3; pb2 78.4 125.3",
  ["tl tr br bl d3 d2 d1 tl w fl ft fr w tr", "br p2 pb2 pb1 p1 bl"])

P("deer", "Deer", "animal",
  "n 8 63.9; c 16.4 72.3; th 27.6 69.5; p 27.6 52.7; f 16.4 54.1; ear 38.8 47.1; a1 23.4 38.7;"
  "a2 29 26.1; a3 40.2 14.9; t1 12.2 31.7; t2 19.2 17.7; t3 30.4 9.3; w 40.2 69.5; rt 82.2 68.1;"
  "tl 92 58.3; ch 29 82.1; fl1 36 93.3; fl2 47.2 93.3; bl1 66.8 93.3; bl2 78 89.1;"
  "hf1 31.8 124.1; hf2 48.6 124.1; hb1 65.4 124.1; hb2 80.8 124.1",
  ["th c n f p w rt bl2 bl1 fl2 fl1 ch th p ear", "p a1 a2 a3 t3", "a1 t1", "a2 t2", "rt tl",
   "fl1 hf1", "fl2 hf2", "bl1 hb1", "bl2 hb2"],
  clue="Feeling a bit antler-social")

P("television", "Television", "object",
  "tl 8 36.1; tr 84.4 36.1; bl 8 99.1; br 84.4 99.1; il 17.5 45.7; ir 74.8 45.7;"
  "ibr 74.8 89.6; ibl 17.5 89.6; kt 92 49.5; kb 92 76.2; a1 32.8 20.8; a2 59.5 18.9;"
  "ap 46.2 36.1; lg1 21.4 114.4; lg2 71 114.4",
  ["tr ap tl bl br tr kt kb br lg2", "bl lg1", "a1 ap a2", "il ir ibr ibl il"])

P("lemon", "Lemon", "plant",
  "tipR 72.2 49.1; u1 53.7 49.4; u2 33.9 55.8; u3 19.9 69.2; u4 12.2 85.8; u6 10.6 101.2;"
  "u5 13.4 112; tipL 12.6 125.3; w5 25.3 121.4; w6 36.6 121.4; w4 51.1 116.2; w3 65.3 104.7;"
  "w2 75 87.9; w1 76.3 67.1; g1 24.5 99; g2 25.1 83.8; g3 32.7 70.6; lf1 89.4 35.2; lft 83.2 8;"
  "lf2 64.2 28.5; lfm 78.2 26.6",
  ["tipR u1 u2 u3 u4 u6 u5 tipL w5 w6 w4 w3 w2 w1 tipR lf1 lft lf2 tipR lfm lft", "u5 w5",
   "g1 g2 g3", "lf1 lfm lf2"],
  clue="When life gives you me, make a drink")

P("horse", "Horse", "animal",
  "E 49.3 15.8; Ef 41.9 32; Eb 55.2 30.6; Fh 30.1 39.4; N1 15.4 73.3; N2 8 88; M1 13.9 99.8;"
  "C 27.2 102.8; J1 41.9 98.4; J2 55.2 88; T 59.6 71.8; Nf 64 117.5; Pb 64 37.9; Nb1 72.8 61.5;"
  "Nb2 78.7 88; Nbb 81.7 117.5; m1 78.7 37.9; m2 87.6 64.5; m3 92 92.5; k1 44.8 77.7;"
  "k2 47.8 65.9; e1 33.1 52.7; e2 44.8 54.1; mo 30.1 91",
  ["Ef E Eb Pb Nb1 Nb2 Nbb Nf T J2 J1 C M1 N2 N1 Fh Ef Eb", "M1 mo", "J2 k1 k2",
   "Pb m1 Nb1 m2 Nb2 m3 Nbb", "e1 e2"],
  clue="Straight from its mouth, they say")

P("car", "Car", "object",
  "fl 8 75.9; fh 9.7 59.1; hw 31.5 55.7; rt1 41.6 37.3; pm 55 37.3; rt2 68.5 37.3;"
  "rw 80.2 55.7; rtop 92 59.1; rb 92 75.9; pb 55 55.7; wt1 26.5 75.9; wl1 18.1 86;"
  "wb1 26.5 96.1; wr1 34.9 86; wt2 73.5 75.9; wl2 65.1 86; wb2 73.5 96.1; wr2 81.9 86",
  ["hw fh fl wt1 wt2 rb rtop rw rt2 pm rt1 hw pb rw", "pm pb", "wt2 wl2 wb2 wr2 wt2",
   "wt1 wl1 wb1 wr1 wt1"])

P("seagull", "Seagull", "animal",
  "bt 8 38.4; bu 22.5 31.9; bl 22.5 44.1; ht 33.8 20.6; hb 46.8 25.5; np 50 38.4; bk 67.8 48.1;"
  "wt 92 69.1; ws 40.3 52.9; w1 54.8 67.5; tt 87.2 82; ut 74.2 78.8; bb 59.7 83.6; be 43.5 82;"
  "ch 30.6 70.7; nf 25.8 56.2; pl 40.3 101.4; pr 62.9 101.4; ql 40.3 124; qr 62.9 124;"
  "m1 54.8 17.4; m2 62.9 9.3; m3 72.6 15.8; m4 82.3 9.3; m5 90.4 17.4",
  ["bu bt bl bu ht hb np bk wt w1 ws np", "bl nf ch be bb ut tt wt", "w1 ut", "bb pr pl be",
   "pl ql qr pr", "m1 m2 m3 m4 m5"],
  clue="Mine? Mine? Mine?")

P("snowflake", "Snowflake", "object",
  "t0 92 66.7; m0 71 66.7; b0 80.3 84.2; t1 71 103; m1 60.5 84.9; b1 50 101.7; t2 29 103;"
  "m2 39.5 84.9; b2 19.7 84.2; t3 8 66.7; m3 29 66.7; b3 19.7 49.2; t4 29 30.3;"
  "m4 39.5 48.5; b4 50 31.7; t5 71 30.3; m5 60.5 48.5; b5 80.3 49.2; c 50 66.7",
  ["t0 m0 c m1 t1", "t2 m2 c m3 t3", "t4 m4 c m5 t5", "m0 b0 m1 b1 m2 b2 m3 b3 m4 b4 m5 b5 m0"])

P("bird", "Bird", "animal",
  "bt 92 35; bu 74.6 27; bl 76.2 41.3; h1 69.8 14.4; h2 54 11.2; h3 39.7 20.7; k1 34.9 41.3;"
  "k2 28.6 63.5; tb1 27 82.5; t1 8 101.5; t2 19.1 112.6; tb2 39.7 92; be1 49.2 99.9;"
  "be2 66.6 93.6; ch 80.9 74.6; c1 84.1 55.6; e1 50.8 25.5; e2 62.7 25.5; e3 56.7 35.8;"
  "wa 44.5 49.2; wb 63.5 55.6; wc 58.7 76.2; br1 8 122.1; fl 47.6 122.1; fr 65.1 122.1;"
  "br2 90.4 122.1",
  ["bu bt bl bu h1 h2 h3 k1 k2 tb1 t1 t2 tb2 tb1 wc wb wa tb1", "bl c1 ch be2 be1 tb2",
   "be1 fl br1", "be2 fr fl", "fr br2", "e1 e2 e3 e1"],
  clue="Tweet me on the branch, not online")

P("donut", "Donut", "object",
  "o0 50 0; o1 84 14; o2 98 48; o3 84 82; o4 50 96; o5 16 82; o6 2 48; o7 16 14;i0 50 26;"
  "i2 72 48; i4 50 70; i6 28 48;s1 22 26; s2 34 20; s3 66 20; s4 78 26; s5 24 70; s6 36 76;"
  "s7 64 76; s8 76 70",
  ["o0 o1 o2 o3 o4 o5 o6 o7 o0", "i0 i2 i4 i6 i0", "s1 s2", "s3 s4", "s5 s6", "s7 s8"])

P("grapes", "Grapes", "plant",
  "g0 36.1 97.9; g1 50.3 88.1; g2 66.4 99.4; g3 63.8 114.1; g4 50.2 120.4; g5 37.3 112.9;"
  "g6 24.2 92.3; g7 21 79.4; g8 33.4 67.5; g9 49.1 74.5; g10 63.9 67.4; g11 76.7 75.3;"
  "g12 77.6 89.9; g13 35.1 51.1; g14 48.6 44.2; g15 61.7 50.5; g16 8 65.8; g17 16.4 49;"
  "g18 78.5 47.3; g19 87.3 62; s1 52.7 28.4; la 64.6 12.9; lt 92 18.4; lb 79.2 33",
  ["g0 g1 g2 g3 g4 g5 g0 g6 g7 g8 g9 g1", "g2 g12 g11 g10 g9", "g7 g16 g17 g13 g8",
   "g10 g15 g14 g13", "g11 g19 g18 g15", "g14 s1 la lt lb s1 lt"],
  clue="Squash me and wait a few years")

P("lizard", "Lizard", "animal",
  "sn 47.6 12.8; hL 36.5 25.5; hR 58.7 23.9; shL 39.7 42.9; shR 57.1 42.9; bR 58.7 60.3;"
  "hpL 46 76.2; hpR 63.5 73; elL 22.3 47.6; ftL 19.1 31.8; taL 8 25.5; tbL 23.8 17.5;"
  "elR 74.6 39.7; ftR 80.9 23.9; taR 77.7 12.8; tbR 92 22.3; fbL 30.2 92; tcL 17.5 93.6;"
  "tdL 28.6 104.7; fbR 79.3 84.1; tcR 92 84.1; tdR 79.3 96.8; t1 60.3 90.4; t2 57.1 106.3;"
  "t3 44.5 117.4; t4 28.6 120.6",
  ["hL sn hR shR bR hpR t1 hpL shL hL hR", "hpL fbL tcL", "hpR fbR tcR",
   "ftL elL shL shR elR ftR taR", "ftL taL", "ftL tbL", "ftR tbR", "fbL tdL", "fbR tdR",
   "t1 t2 t3 t4"],
  clue="Sun's out, tongue's out")

P("castle", "Castle", "object",
  "bl 4 130; a 4 40; rt 15 16; rr 26 40; c1 26 54; c2 40 54; c3 40 38; c4 60 38;"
  "c5 60 54;c6 74 54; c7 74 40; rt2 85 16; rr2 96 40; k 96 130; g1 38 130; g2 50 102;"
  "g3 62 130;w1 40 74; w2 56 74; w3 56 90; w4 40 90",
  ["bl a rt rr c1 c2 c3 c4 c5 c6 c7 rt2 rr2 k g3 g2 g1 bl", "w1 w2 w3 w4 w1"])

P("monkey", "Monkey", "animal",
  "h1l 37.5 26.9; hel 22 44.6; hbl 21.3 69.6; eal 13.2 37.2; ebl 8 54.1; ecl 10.2 68.1;"
  "ltl 37.5 41.6; eyal 30.1 60.8; eybl 41.2 63; nl 43.4 75.5; sl 27.9 88.8; cl 37.5 106.5;"
  "h1r 62.5 26.9; her 78 44.6; hbr 78.7 69.6; ear 86.8 37.2; ebr 92 54.1; ecr 89.8 68.1;"
  "ltr 62.5 41.6; eyar 69.9 60.8; eybr 58.8 63; nr 56.6 75.5; sr 72.1 88.8; cr 62.5 106.5;"
  "md 50 56.4; s0 50 94.7",
  ["hel h1l h1r her hbr sr cr cl sl hbl hel eal ebl ecl hbl", "hel ebl",
   "hel ltl md ltr her ear ebr ecr hbr", "eyal eybl", "her ebr", "eyar eybr",
   "nl sl s0 sr nr nl"],
  clue="Going bananas since forever")

P("mailbox", "Mailbox", "object",
  "F1 8.2 84.4; F2 38.4 84.4; F3 38.4 61.3; F4 34 50.7; F5 23.3 46.2; F6 12.7 50.7; F7 8.2 61.3;"
  "B2 91.8 73.8; B3 91.8 50.7; B4 87.3 40; B5 76.7 35.6; h1 17.1 72; h2 29.6 72; pb 61.6 61.3;"
  "pm 61.6 22.2; pt 61.6 8; fa 81.1 8; fb 81.1 22.2; q1 54.4 80.9; q2 68.7 78; q3 54.4 125.3;"
  "q4 68.7 125.3",
  ["F2 F1 F7 F6 F5 F4 F3 F2 q1 q2 B2 B3 B4 B5 F5", "F3 F7", "h1 h2", "pb pm pt fa fb pm",
   "q1 q3 q4 q2"],
  clue="You've got mail")

P("panda", "Panda", "animal",
  "n3 50 96.6; m 50 108.7; bl 27.4 118.4; br 72.6 118.4; l 9.6 82.8; r 90.4 82.8; h1 16.1 47.3;"
  "g1 83.9 47.3; h2 35.5 32.7; g2 64.5 32.7; e1 8 27.9; f1 92 27.9; e2 24.2 15; f2 75.8 15;"
  "n1 43.5 86.1; n2 56.5 86.1; pa 40.3 52.1; qa 59.7 52.1; pb 20.9 65.1; qb 79.1 65.1;"
  "pc 24.2 92.5; qc 75.8 92.5; ya 30.6 79.6; za 69.4 79.6; yb 35.5 68.3; zb 64.5 68.3",
  ["n3 n2 qc qb qa n2 n1 pc pb pa n1 n3 m", "h1 l bl br r g1 g2 h2 h1 e1 e2 h2", "g1 f1 f2 g2",
   "ya yb", "za zb"],
  clue="Black, white, and bamboo all over")

P("icecream", "Ice cream cone", "object",
  "s1L 18.5 78.1; s2L 28.5 86.7; s3L 39.3 78.1; d1L 12.8 65.2; d2L 18.5 50.9; d3L 32.8 40.9;"
  "k1L 35.7 99.6; k2L 42.8 112.5; s1R 81.5 78.1; s2R 71.5 86.7; s3R 60.7 78.1; d1R 87.2 65.2;"
  "d2R 81.5 50.9; d3R 67.2 40.9; k1R 64.3 99.6; k2R 57.2 112.5; s0 50 88.1; top 50 38;"
  "tip 50 125.3; st 61.4 8; h1 40.5 31.1; h2 44.1 19.9; h3 55.9 19.9; h4 59.5 31.1",
  ["s2L s1L d1L d2L d3L top d3R d2R d1R s1R s2R s3R s0 s3L s2L k1L k2L tip k2R k1R s2R",
   "k2L k1R s0 k1L k2R", "st h3 h2 h1 top h4 h3"],
  clue="Brain freeze in a crunchy cup")

P("sunflower", "Sunflower", "plant",
  "t0 50 92.2; d0 41.9 71.8; t1 22.6 82.3; d1 29.5 61.4; t2 8 57; d2 26.7 45.5; t3 13.1 28.3;"
  "d3 34.8 31.4; t4 35.4 9.5; d4 50 25.9; t5 64.6 9.5; d5 65.2 31.4; t6 86.9 28.3; d6 73.3 45.5;"
  "t7 92 57; d7 70.5 61.4; t8 77.4 82.3; d8 58.1 71.8; s1 50 106.4; s2 50 122.2; la 64.2 93.8;"
  "lt 86.3 95.4; lb 72.1 109.6; lc 35.8 111.2; lu 13.7 108; ld 29.5 123.8",
  ["t0 d0 t1 d1 t2 d2 t3 d3 t4 d4 t5 d5 t6 d6 t7 d7 t8 d8 t0 s1 s2 lc lu ld s2 lu",
   "d0 d1 d2 d3 d4 d5 d6 d7 d8 d0 d6 d4 d2 d8", "d1 d5", "d3 d7", "s1 la lt lb s1 lt"],
  clue="I always turn to face the sun")

P("tiger", "Tiger", "animal",
  "T 50 30.3; EiL 36.9 31.2; EaL 31.3 19.1; EbL 18.3 20.9; EoL 12.7 35.9; S1L 8 56.4;"
  "S2L 10.8 78.8; CkL 23.9 101.2; B 50 114.3; st1L 24.8 54.5; st2L 26.7 75.1; F 50 47.1;"
  "FsL 38.8 46.1; YaL 35.1 62.9; YbL 44.4 69.5; NL 41.6 84.4; N 50 93.7; EiR 63.1 31.2;"
  "EaR 68.7 19.1; EbR 81.7 20.9; EoR 87.3 35.9; S1R 92 56.4; S2R 89.2 78.8; CkR 76.1 101.2;"
  "st1R 75.2 54.5; st2R 73.3 75.1; FsR 61.2 46.1; YaR 64.9 62.9; YbR 55.6 69.5; NR 58.4 84.4",
  ["T EiL EaL EbL EoL S1L S2L CkL B CkR S2R S1R EoR EbR EaR EiR T F", "EoL EiL FsL",
   "S1L st1L", "S2L st2L", "B N NR NL N", "YaL YbL", "EoR EiR FsR", "S1R st1R", "S2R st2R",
   "YaR YbR"],
  clue="They're grrreat!")

P("skateboard", "Skateboard", "object",
  "Nt 50 8; NaL 38 13; WtL 35 26.1; WbL 35 40.1; WoTL 18.9 26.1; WoBL 18.9 40.1; XtL 35 93.2;"
  "XbL 35 107.3; XoTL 18.9 93.2; XoBL 18.9 107.3; TaL 38 120.3; Tt 50 125.3; NaR 62 13;"
  "WtR 65 26.1; WbR 65 40.1; WoTR 81.1 26.1; WoBR 81.1 40.1; XtR 65 93.2; XbR 65 107.3;"
  "XoTR 81.1 93.2; XoBR 81.1 107.3; TaR 62 120.3; z1 55 50.1; z2 43 70.2; z3 57 66.2;"
  "z4 45 86.2",
  ["z1 z2 z3 z4", "Nt NaL WtL WbL XtL XbL TaL Tt TaR XbR XtR WbR WtR NaR Nt",
   "WtL WoTL WoBL WbL WbR WoBR WoTR WtR WtL", "XtL XoTL XoBL XbL XbR XoBR XoTR XtR XtL"],
  clue="Ollie, ollie, oxen free!")

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
    "pineapple"
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
