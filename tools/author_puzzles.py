"""Source of truth for the puzzles in puzzles/puzzles.json.

Each puzzle is drawn on a free grid (any units, y pointing down) as named points plus
paths ("a b c a" = edges a-b, b-c, c-a). Degrees are derived from the edges, and each drawing
is scaled uniformly and centred onto the 3:4 board inside an 0.08 margin.

    python tools/author_puzzles.py          # rewrites puzzles/puzzles.json
    python tools/validate_puzzles.py        # always run afterwards
    python tools/puzzle_quality.py          # flags dull puzzles (long degree-2 chains)
    python tools/preview_puzzles.py         # optional: contact sheet PNG (needs matplotlib)

Publish order is ORDER at the bottom (index 0 = launch day). Don't reorder puzzles that have
already been played: the day index picks puzzles by position.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOARD_H = 4 / 3
BOX = (0.08, 0.92, 0.08, BOARD_H - 0.08)  # x0, x1, y0, y1 usable area
PUZZLES = []


def P(pid, title, cat, pts, paths):
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
    PUZZLES.append(dict(id=pid, title=title, category=cat, pts=pts, edges=edges))


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


P("fish", "Fish", "animal",
  "nose 0 50; u1 30 28; u2 62 30; t 80 50; l2 62 70; l1 30 72; tt 100 30; tb 100 70;"
  "fin 48 10;ey1 22 42; ey2 22 56",
  ["nose u1 u2 t l2 l1 nose", "t tt", "tt tb", "tb t", "u1 fin", "fin u2", "u1 l1", "ey1 ey2"])

P("umbrella", "Umbrella", "object",
  "t 50 20.5; l 8 57.4; r 92 57.4; q1 35.7 57.4; q2 64.3 57.4; v1 22.3 64.1; v2 50 64.1;"
  "v3 77.7 64.1; h1 50 102.8; h2 41.6 112.9; h3 30.7 106.1",
  ["q1 t l v1 q1 v2 q2 t r v3 q2", "v2 h1 h2 h3"])

P("pine", "Pine tree", "plant",
  "top 50 19.2; r1 70.1 44.8; r1i 57.3 44.8; r2 81 70.3; r2i 62.8 70.3; r3 92 97.7;"
  "tr 57.3 97.7; trb 57.3 114.1; tlb 42.7 114.1; tl 42.7 97.7; l3 8 97.7; l2i 37.2 70.3;"
  "l2 19 70.3; l1i 42.7 44.8; l1 29.9 44.8",
  ["r1i r1 top l1 l1i l2 l2i l3 tl tlb trb tr r3 r2i r2 r1i l1i", "r2i l2i", "tr tl"])

P("bird", "Bird", "animal",
  "p 8 54.9; f 20.6 49; h 33.2 38.1; k 54.2 53.2; t1 92 53.2; t2 85.3 70; r 62.6 74.2;"
  "bm 37.4 78.4; c 20.6 63.3; w 68.5 61.6; g1 39.9 95.2; g2 60.1 95.2; br1 12.2 95.2;"
  "br2 87.8 95.2",
  ["f p c bm r t2 t1 k h f c", "g1 bm w k", "g2 r", "br1 g1 g2 br2"])

P("kite", "Kite", "object",
  "top 50 8; l 22.4 38.2; r 77.6 38.2; c 50 38.2; b 50 90; t1 41.4 102.9; t2 56.9 113.3;"
  "t3 44.8 125.3; bw1 69 106.4; bw2 69 120.2; bw3 29.3 96; bw4 29.3 109.8",
  ["top l b r top c b t1 t2 t3", "l c r", "t1 bw3 bw4 t1", "t2 bw1 bw2 t2"])

P("whale", "Whale", "animal",
  "n 8 73.8; h 26.5 57; k 54.2 55.3; s 76.9 71.3; bl 56.7 90.6; bf 26.5 90.6; f1 80.2 47.8;"
  "f2 92 56.2; j 29 42.7; s1 18.1 30.1; s2 39.9 30.1; m 31.5 78; fl 41.6 103.2",
  ["n h k s bl bf n m", "j h", "bf fl", "s1 j s2", "s f1 f2 s"])

P("cactus", "Cactus", "plant",
  "bl 38.6 125.3; j1 38.6 91.3; a 14 91.3; at 14 61; ai 27.3 61; ab 27.3 78; j2 38.6 78;"
  "tl 38.6 28.8; top 50 21.2; tr 61.4 28.8; k2 61.4 68.6; bb 72.7 68.6; bt 72.7 45.8;"
  "bi 86 45.8; bo 86 81.8; k1 61.4 81.8; br 61.4 125.3; s2 25.4 44; s3 50 8; s4 86 28.8;"
  "s6 74.6 100.7",
  ["at a j1 bl br k1 bo bi bt bb k2 tr top tl j2 ab ai at s2", "top s3", "bt s4", "k1 s6"])

P("butterfly", "Butterfly", "animal",
  "hd 50 39.8; a1 37.4 26.3; a2 62.6 26.3; b1 50 53.2; bm 50 72.5; b2 50 95.2; p1 18.1 30.5;"
  "p2 8 64.1; p3 18.1 86.8; p4 34.9 107; q1 81.9 30.5; q2 92 64.1; q3 81.9 86.8;"
  "q4 65.1 107",
  ["hd a1", "b2 bm b1 hd a2", "bm p2 p1 b1 q1 q2 bm p3 p4 b2 q4 q3 bm"])

P("daisy", "Daisy", "plant",
  "v0 50 63.3; o0a 33.6 87.6; o0b 18.3 76.5; v1 36.4 53.4; o1a 8.1 45.3; o1b 14 27.3;"
  "v2 41.6 37.4; o2a 40.5 8; o2b 59.5 8; v3 58.4 37.4; o3a 86 27.3; o3b 91.9 45.3;"
  "v4 63.6 53.4; o4a 81.7 76.5; o4b 66.4 87.6; sm 50 101.5; sb 50 125.3; lf 72.9 105.3;"
  "ct 50 48.9",
  ["ct v0 o0a o0b v1 o1a o1b v2 o2a o2b v3 o3a o3b v4 o4a o4b v0 sm sb lf sm", "v1 ct v2",
   "v3 ct v4"])

P("turtle", "Turtle", "animal",
  "s1 33.4 35.7; s2 66.6 35.7; s3 83.2 66.7; s4 66.6 97.6; s5 33.4 97.6; s6 16.8 66.7;"
  "c 50 66.7; hd 50 13.6; l1 8 22.5; l2 92 22.5; l3 92 113.1; l4 8 113.1; t 50 119.7",
  ["s1 s2 s3 s4 s5 s6 s1 hd s2 l2", "s4 l3", "s5 l4", "s2 c s1 l1", "s3 c s4 t s5 c s6"])

P("icecream", "Ice cream", "object",
  "s0 76 36; s1 63 58; s2 37 58; s3 24 36; s4 37 14; s5 63 14;c1 41 74; c2 59 74; c3 45 90;"
  "c4 55 90; tip 50 108",
  ["s0 s1 s2 s3 s4 s5 s0", "s2 c1 c3 tip", "tip c4 c2 s1", "c1 c2", "c3 c4"])

P("fox", "Fox", "animal",
  "lt 14.7 24.7; a 37.4 45.7; b 62.6 45.7; rt 85.3 24.7; cr 92 65; sn 50 108.7; cl 8 65;"
  "m1 36.6 76.7; m2 63.4 76.7; il 24.8 49.9; ir 75.2 49.9",
  ["lt a b rt cr sn cl lt il a", "b ir rt", "cr m2 sn m1 cl"])

P("hourglass", "Hourglass", "object",
  "tl 8 16.4; g1 24.4 16.4; g2 75.6 16.4; tr 92 16.4; bl 8 116.9; g4 24.4 116.9;"
  "g3 75.6 116.9; br 92 116.9; n1 43.6 66.7; n2 56.4 66.7; sp 50 96.8",
  ["g1 tl bl g4 g3 br tr g2 g1 n1 g4 sp g3 n2 g2"])

P("rocket", "Rocket", "object",
  "n 50 8; nl 31.5 32.7; nr 68.5 32.7; lf1 31.5 71.8; bl 31.5 92.4; fb 50 92.4;"
  "br 68.5 92.4; rf1 68.5 71.8; lft 10.9 110.9; rft 89.1 110.9; wt 50 40.9; wr 60.3 51.2;"
  "wb 50 61.5; wl 39.7 51.2; ft 50 125.3; fx1 37.6 115; fx2 62.4 115",
  ["fb bl lf1 nl n nr rf1 br fb ft", "nl nr", "lf1 lft bl", "br rft rf1", "fx1 fb fx2",
   "wt wr wb wl wt"])

P("penguin", "Penguin", "animal",
  "ht 50 17; hr 67.2 28.5; sr 74.8 55.2; br 71 95.3; bb 50 106.8; bl 29 95.3; sl 25.2 55.2;"
  "hl 32.8 28.5; fl 8 83.8; fr 92 83.8; b1 43.3 38; b2 56.7 38; b3 50 51.4; il 34.7 72.4;"
  "ir 65.3 72.4; f1 37.6 116.3; f2 62.4 116.3",
  ["sr hr ht hl sl bl bb br sr fr br", "bl fl sl", "f1 bb il b3 b2 b1 b3 ir bb f2"])

P("camera", "Camera", "object",
  "tl 8 44.8; tr 92 44.8; bl 8 105; br 92 105; hl 31.7 44.8; hm 40.9 28.3; hr 61 28.3;"
  "hb 70.1 44.8; c 50 75.8; e 50 55.7; w 29.9 75.8; s 50 95.9; q 70.1 75.8; fl 19 57.5;"
  "fr 81 57.5; shu 82.9 32",
  ["tl hl hm hr hb tr br bl tl fl", "e c w e q c s w", "hr shu", "tr fr", "s q"])

P("robot", "Robot", "object",
  "ht 28.2 30.5; hr 71.8 30.5; hb 71.8 57.4; hl 28.2 57.4; ant 50 12.1; an 50 30.5;"
  "el 39.9 42.3; er 60.1 42.3; m 50 50.7; bt 19.8 67.5; brt 80.2 67.5; brb 80.2 106.1;"
  "bb 19.8 106.1; b1 50 79.3; b2 50 92.7; al 8 87.7; ar 92 87.7; lg1 34.9 121.3;"
  "lg2 65.1 121.3",
  ["hl ht an hr hb hl bt brt brb bb bt al", "an ant", "hb brt ar", "brb lg2", "bb lg1", "b1 b2",
   "el er m el"])

P("castle", "Castle", "object",
  "bl 4 130; a 4 40; rt 15 16; rr 26 40; c1 26 54; c2 40 54; c3 40 38; c4 60 38;"
  "c5 60 54;c6 74 54; c7 74 40; rt2 85 16; rr2 96 40; k 96 130; g1 38 130; g2 50 102;"
  "g3 62 130;w1 40 74; w2 56 74; w3 56 90; w4 40 90",
  ["bl a rt rr c1 c2 c3 c4 c5 c6 c7 rt2 rr2 k g3 g2 g1 bl", "w1 w2 w3 w4 w1"])

P("train", "Train", "object",
  "ft 8.2 49.8; fb 8.2 105.4; cb 91.8 105.4; ct 91.8 31.9; cf 58 31.9; cfb 58 49.8;"
  "w1 30.1 105.4; w2 69.9 105.4; wl1 18.2 115.4; wlb 30.1 125.3; wl2 42 115.4; wr1 58 115.4;"
  "wrb 69.9 125.3; wr2 81.8 115.4; ch1 24.1 49.8; ch2 24.1 25.9; sm1 12.2 12; sm2 40.1 8;"
  "win1 67.9 43.8; win2 83.8 43.8",
  ["ch1 ft fb w1 w2 cb ct cf cfb ch1 ch2 sm1", "cf win1 win2 ct", "ch2 sm2", "w2 wr1 wrb wr2 w2",
   "w1 wl1 wlb wl2 w1"])

P("balloon", "Hot-air balloon", "object",
  "o0 50 8; o1 76.3 18.9; o2 87.2 45.2; o3 76.3 71.6; o4 50 82.5; o5 23.7 71.6;"
  "o6 12.8 45.2; o7 23.7 18.9; bl 35.1 108.6; br 64.9 108.6; bb1 37 125.3; bb2 63 125.3",
  ["o4 o3 o2 o1 o0 o7 o6 o5 o4 o0", "o3 br o4 bl o5", "bl br bb2 bb1 bl"])

P("clock", "Clock", "object",
  "o0 50 4; o1 82 18; o2 96 50; o3 82 82; o4 50 96; o5 18 82; o6 4 50; o7 18 18;i0 50 22;"
  "i3 78 50; i6 50 78; i9 22 50; c 50 50; hh 68 38; hm 36 70",
  ["o0 o1 o2 o3 o4 o5 o6 o7 o0", "o0 i0", "o2 i3", "o4 i6", "o6 i9", "hh c hm"])

P("tent", "Tent", "object",
  "pk 50 26.1; bl 17.8 93.3; br 82.2 93.3; d1 38.8 93.3; d2 50 45.7; d3 61.2 93.3;"
  "g1 50 104.5; gl 8 84.9; gr 92 84.9; pl 17.8 107.3; pr 82.2 107.3; f1 37.4 68.1;"
  "f2 62.6 68.1",
  ["pk bl d1 d3 br pk d2 d1 g1 d3 d2", "pl bl gl", "pr br gr", "f1 f2"])

P("candle", "Candle", "object",
  "tl 30.4 48.9; tr 69.6 48.9; d1 30.4 64.9; d2 19.8 77.3; d3 30.4 89.8; bl 30.4 112.9;"
  "br 69.6 112.9; w 50 41.8; fl 39.3 27.6; ft 50 8; fr 60.7 27.6; p1 12.7 112.9;"
  "p2 87.3 112.9; pb1 21.6 125.3; pb2 78.4 125.3",
  ["tl tr br bl d3 d2 d1 tl w fl ft fr w tr", "br p2 pb2 pb1 p1 bl"])

P("ferriswheel", "Ferris wheel", "object",
  "r0 50 28.6; c0 50 16.1; r1 70.9 37.2; c1 79.7 28.4; r2 79.6 58.1; c2 92 58.1; r3 70.9 79;"
  "c3 79.7 87.8; r4 50 87.7; c4 50 100.1; r5 29.1 79; c5 20.3 87.8; r6 20.4 58.1; c6 8 58.1;"
  "r7 29.1 37.2; c7 20.3 28.4; hub 50 58.1; bl 26.7 117.2; br 73.3 117.2",
  ["r1 r0 r7 r6 r5 r4 r3 r2 r1 c1", "r3 c3", "r5 c5", "r7 c7", "c0 r0 hub r2 c2",
   "c6 r6 hub r4 c4", "hub bl br hub"])

P("headphones", "Headphones", "object",
  "a2 23.4 32.4; a3 38.9 13.5; a4 59.4 13.5; a5 74.9 32.4; ll 8 63.2; lr 30.3 63.2;"
  "lb1 8 94.1; lb2 30.3 94.1; rl 68 63.2; rr 90.3 63.2; rb1 68 94.1; rb2 90.3 94.1;"
  "cw1 92 111.2; cw2 69.7 119.8",
  ["lb1 lb2 lr a2 a3 a4 a5 rl rr rb2 rb1 rl rb2 cw1 cw2", "lr ll lb1 lr"])

P("laptop", "Laptop", "object",
  "sl 19.8 27.2; sr 80.2 27.2; sbr 80.2 77.6; sbl 19.8 77.6; il 29.8 37.3; ir 70.2 37.3;"
  "ibr 70.2 67.5; ibl 29.8 67.5; bl 8 91; br 92 91; bbl 14.7 106.1; bbr 85.3 106.1;"
  "tp1 39.9 97.7; tp2 60.1 97.7",
  ["sbr sr sl sbl sbr br bl sbl", "bbl bl", "bbr bbl tp1 tp2 bbr br", "il ir ibr ibl il"])

P("sunglasses", "Sunglasses", "object",
  "l1 11.4 59.1; l2 41.6 59.1; l3 38.2 91; l4 16.4 91; r1 58.4 59.1; r2 88.6 59.1;"
  "r3 83.6 91; r4 61.8 91; n 50 69.2; t1 8 42.3; t2 92 42.3",
  ["l2 l1 l4 l3 l2 n r1 r2 r3 r4 r1", "l3 l1 t1", "r4 r2 t2"])

P("hammer", "Hammer", "object",
  "hl 20.7 8; hr 90.2 8; hb 90.2 40.6; hbl 20.7 40.6; cl 9.8 24.3; nk 57.6 40.6;"
  "t1 48.9 55.8; t2 66.3 55.8; g1 47.8 94.9; g2 67.4 94.9; b1 46.7 125.3; b2 68.5 125.3",
  ["g1 t1 nk hb hr hl cl hbl nk t2 g2 b2 b1 g1 g2"])

P("gift", "Gift box", "object",
  "tl 8 42.8; tr 92 42.8; bl 8 117.3; br 92 117.3; lt 8 60; rt 92 60; bt1 36.6 42.8;"
  "bt2 63.4 42.8; bb1 36.6 117.3; bb2 63.4 117.3; k 50 29.4; bw1 25.2 21.8; bw2 42.4 16.1;"
  "bw3 74.8 21.8; bw4 57.6 16.1",
  ["rt tr bt2 bt1 tl lt bl bb1 bb2 br rt lt", "bb2 bt2 k bt1 bb1", "k bw1 bw2 k bw3 bw4 k"])

P("telescope", "Telescope", "object",
  "t1 8 26.6; t2 29 9.4; t3 88.2 49.5; t4 67.2 66.7; m1 58.6 29.4; m2 37.6 46.6; e1 92 64.8;"
  "e2 78.6 76.2; lgb 46.2 97.2; lg1 25.2 123.9; lg2 65.3 123.9",
  ["m1 t2 t1 m2 t4 e2 e1 t3 m1 m2 lgb lg1 lg2 lgb"])

P("compass", "Compass", "object",
  "o0 50 2; o1 84 16; o2 98 50; o3 84 84; o4 50 98; o5 16 84; o6 2 50; o7 16 16;n 50 20;"
  "e 80 50; s 50 80; w 20 50; c 50 50",
  ["o0 o1 o2 o3 o4 o5 o6 o7 o0", "o0 n", "o2 e", "o4 s", "o6 w", "n e s w n", "n c", "c s"])

P("drum", "Drum", "object",
  "tl 14 28; tr 86 28; ml 10 58; mr 90 58; bl 22 88; br 78 88; z1 32 28; z2 68 28;"
  "z3 38 88;z4 62 88; s1 12 14; s2 50 -4; s3 30 -6; s4 66 12",
  ["tl z1 z2 tr mr br z4 z3 bl ml tl", "ml mr", "z1 mr", "z2 ml", "ml z4", "mr z3", "s1 s2",
   "s3 s4"])

P("crab", "Crab", "animal",
  "b0 24.8 70.9; b1 37.4 58.3; b2 62.6 58.3; b3 75.2 70.9; b4 62.6 83.5; b5 37.4 83.5;"
  "e1 43.3 42.3; e2 56.7 42.3; la 12.2 54.1; lc1 8 33.9; lc2 24.8 37.3; ra 87.8 54.1;"
  "rc1 92 33.9; rc2 75.2 37.3; l1 23.1 99.4; l2 9.7 87.7; r1 76.9 99.4; r2 90.3 87.7",
  ["b1 b0 b5 b4 b3 b2 b1 e1", "la b0 l2", "ra b3 r2", "b2 e2", "b4 r1", "b5 l1", "lc1 la lc2",
   "rc1 ra rc2"])

P("bell", "Bell", "object",
  "h1 42.7 18.3; h2 57.3 18.3; s1 37.2 31.1; s2 62.8 31.1; w1 29.9 54.8; w2 70.1 54.8;"
  "f1 20.8 87.7; f2 79.2 87.7; r1 8 100.4; r2 92 100.4; m 50 100.4; cl 50 115.1",
  ["s1 w1 f1 r1 m r2 f2 w2 s2 s1 h1 h2 s2", "m cl"])

P("orion", "Orion", "real-constellation",
  "me 45.7 31.5; be 25.1 48.7; bl 68 52.1; zt 35.4 84.7; zl 47.4 80.4; zm 59.4 76.1;"
  "sa 30.3 119; ri 73.1 113.8; c1 18.3 31.5; c2 8 14.4; s1 86.9 38.4; s2 92 53.8;"
  "s3 88.6 69.2",
  ["bl me be zt zl zm bl s1", "be c1 c2", "zt sa", "zm ri", "s2 bl s3"])

P("car", "Car", "object",
  "fl 8 75.9; fh 9.7 59.1; hw 31.5 55.7; rt1 41.6 37.3; pm 55 37.3; rt2 68.5 37.3;"
  "rw 80.2 55.7; rtop 92 59.1; rb 92 75.9; pb 55 55.7; wt1 26.5 75.9; wl1 18.1 86;"
  "wb1 26.5 96.1; wr1 34.9 86; wt2 73.5 75.9; wl2 65.1 86; wb2 73.5 96.1; wr2 81.9 86",
  ["hw fh fl wt1 wt2 rb rtop rw rt2 pm rt1 hw pb rw", "pm pb", "wt2 wl2 wb2 wr2 wt2",
   "wt1 wl1 wb1 wr1 wt1"])

P("teapot", "Teapot", "object",
  "bl 30.4 96.4; br 66.7 96.4; r1 76.1 78.3; r2 68.8 60.1; ld2 57.2 60.1; ld1 39.9 60.1;"
  "l2 28.3 60.1; l1 21 78.3; k 48.6 48.6; kt 48.6 37; sp1 80.4 52.9; sp2 92 55.8;"
  "h1 15.2 57.3; h2 8 71.7",
  ["r1 br bl l1 l2 ld1 ld2 r2 r1 sp2 sp1 r2", "k ld1", "ld2 k kt", "l2 h1 h2 l1"])

P("dog", "Dog", "animal",
  "t1 36.3 31.1; t2 63.7 31.1; le1 15.3 34.7; le2 8 73.1; le3 22.6 80.4; hl 31.7 51.1;"
  "re1 84.7 34.7; re2 92 73.1; re3 77.4 80.4; hr 68.3 51.1; cl 33.6 87.7; cr 66.4 87.7;"
  "ch 50 102.3; n1 42.7 71.2; n2 57.3 71.2; n3 50 82.2",
  ["t1 t2 re1 re2 re3 hr cr ch cl hl le3 le2 le1 t1 hl", "n3 n2 n1 n3 ch", "t2 hr"])

P("frog", "Frog", "animal",
  "e1 29.9 25.6; e2 44.5 18.3; e3 57.3 25.6; e4 70.1 18.3; hl 13.5 51.1; hr 86.5 51.1;"
  "ch 50 71.2; b1 19 85.8; b2 81 85.8; fl1 8 104.1; fl2 24.4 115.1; fr1 92 104.1;"
  "fr2 75.6 115.1; m1 35.4 56.6; m2 64.6 56.6",
  ["hl e1 e2 e3 e4 hr ch hl b1 fl1 fl2 ch fr2 fr1 b2 hr", "e2 m1 m2 e3"])

P("giraffe", "Giraffe", "animal",
  "h1 80.2 19.6; h2 92 28; n1 71.8 34.7; n2 61.8 59.9; b1 48.3 71.7; b2 18.1 68.3; r 8 83.5;"
  "bl1 13 112; bl2 26.5 112; bd 55 96.9; fl1 48.3 113.7; fl2 61.8 113.7; nk 81.9 41.5;"
  "sp1 29.8 78.4; sp2 41.6 86.8",
  ["n1 h2 h1 nk n1 n2 b1 b2 r bl1", "b1 bd fl1", "b2 sp1 sp2 bd fl2", "r bl2"])

P("horse", "Horse", "animal",
  "e 81.7 19.5; h1 92 35; h2 76.6 48.7; n1 64.6 36.7; n2 57.7 59; b1 42.3 64.1; r1 14.9 59;"
  "t1 8 40.1; t2 8 84.7; bl1 13.1 113.8; bl2 28.6 110.4; fl1 52.6 113.8; fl2 66.3 108.7;"
  "bd 47.4 91.5; m1 69.7 24.7",
  ["r1 b1 n2 n1 h2 h1 e m1 n1", "n2 bd b1", "t1 r1 t2", "fl1 bd fl2", "bl1 r1 bl2"])

P("hedgehog", "Hedgehog", "animal",
  "s0 18 62; s1 22 45; s2 35 33; s3 52 28; s4 69 33; s5 82 45; s6 86 62; p0 0 62;"
  "p1 6 36;p2 26 16; p3 52 10; p4 78 16; p5 98 36; p6 104 62; sn 112 78; fb 74 94;"
  "bb 30 96;ey 72 72; ey2 88 78",
  ["s0 s1 s2 s3 s4 s5 s6", "s0 p0", "s1 p1", "s2 p2", "s3 p3", "s4 p4", "s5 p5", "s6 p6",
   "s6 sn", "sn fb", "fb bb", "bb s0", "ey ey2"])

P("bee", "Bee", "animal",
  "hd1 96 44; hd2 84 28; hd3 66 36; hd4 68 58; hd5 86 62; s1 52 28; s2 50 62;"
  "s3 32 26;s4 30 64; t1 8 32; t2 0 48; t3 10 64; an1 94 8; an2 72 6; w1 58 -2; w2 80 -12;"
  "w3 20 6;w4 42 -4",
  ["hd1 hd2 hd3 hd4 hd5 hd1", "hd3 s1", "s1 s3", "s3 t1", "t1 t2", "t2 t3", "t3 s4", "s4 s2",
   "s2 hd4", "s1 s2", "s3 s4", "hd2 an1", "hd3 an2", "w1 w2", "w3 w4"])

P("ladybug", "Ladybug", "animal",
  "o0 50 36.2; o1 79.7 48.5; o2 92 78.2; o3 79.7 107.9; o4 50 120.2; o5 20.3 107.9;"
  "o6 8 78.2; o7 20.3 48.5; hd 50 23.6; a1 33.2 13.1; a2 66.8 13.1; sp1 26.9 61.4;"
  "sp2 73.1 61.4; sp3 29 97.1; sp4 71 97.1",
  ["o4 o3 o2 o1 o0 o7 o6 o5 o4 o0 hd a1", "hd a2", "sp1 o6 sp3", "sp2 o2 sp4"])

P("spider", "Spider", "animal",
  "b1 50 45.7; b2 67.2 62.8; b3 50 91.5; b4 32.8 62.8; hd 50 24.7; l1 8 28.5; l2 11.8 55.2;"
  "l3 9.9 85.8; l4 21.4 108.7; r1 92 28.5; r2 88.2 55.2; r3 90.1 85.8; r4 78.6 108.7;"
  "k1 25.2 47.6; k2 27.1 78.1; k3 74.8 47.6; k4 72.9 78.1",
  ["b1 b2 b3 b4 b1 hd", "k1 b4", "k2 b3 k4 r3", "k3 b2", "l1 k1 l2", "l3 k2 l4", "r1 k3 r2",
   "k4 r4"])

P("octopus", "Octopus", "animal",
  "h1 51 16.9; h2 76.4 28.6; h3 84.2 55.9; h4 70.5 75.5; h5 31.4 75.5; h6 17.8 55.9;"
  "h7 25.6 28.6; e1 39.3 46.2; e2 62.7 46.2; a1 8 89.1; a2 19.7 110.6; a3 37.3 95;"
  "a4 49 116.5; a5 62.7 95; a6 76.4 114.5; a7 92 91.1",
  ["h3 h2 h1 h7 h6 h5 h4 h3 e2 e1 h6", "a2 a1 h5 a3 a4", "a6 a5 h4 a7"])

P("starfish", "Starfish", "animal",
  "t0 50 26.7; v0 61 55.8; t1 92 57.2; v1 67.8 76.7; t2 76 106.6; v2 50 89.6; t3 24 106.6;"
  "v3 32.2 76.7; t4 8 57.2; v4 39 55.8",
  ["v0 t0 v4 t4 v3 t3 v2 t2 v1 t1 v0 v1 v2 v3 v4 v0"])

P("bat", "Bat", "animal",
  "hd 50 51.8; e1 41.2 39.5; e2 58.7 39.5; b1 41.2 67.5; b2 58.7 67.5; bb 50 93.8;"
  "wl1 29 60.5; wl2 8 53.5; wl3 11.5 85; wl4 30.7 93.8; wr1 71 60.5; wr2 92 53.5;"
  "wr3 88.5 85; wr4 69.3 93.8",
  ["b1 hd e1", "b2 hd e2", "wl1 b1 bb b2 wr1 wr2 wr3 wr4 bb wl4 wl3 wl2 wl1 wl4", "wr1 wr4"])

P("deer", "Deer", "animal",
  "hd 86 40; sn 100 52; a1 76 20; a2 60 6; a3 86 2; b1 96 22; b2 104 6; bd1 60 56;"
  "bk 30 50;r 8 58; t 0 40; bd 50 82; fl1 46 114; fl2 66 112; bl1 10 114; bl2 28 112",
  ["sn hd a1", "a1 a2", "a1 a3", "hd b1", "b1 b2", "hd bd1", "bd1 bk", "bk r", "r t", "bd1 bd",
   "bd fl1", "bd fl2", "r bl1", "r bl2", "bk bd"])

P("ant", "Ant", "animal",
  "hd1 88.3 63.9; hd2 77.4 51.1; hd3 62.8 63.9; hd4 75.6 78.5; th1 50 54.8; th2 46.3 78.5;"
  "ab1 26.3 49.3; ab2 8 65.8; ab3 24.4 84; an1 92 36.5; an2 75.6 29.2; l1 51.8 29.2;"
  "l2 31.7 27.4; l3 53.7 104.1; l4 35.4 105.9",
  ["hd2 hd1 hd4 hd3 hd2 an1", "ab1 th1 hd3 an2", "ab3 ab2 ab1 l2", "hd4 th2 th1 l1",
   "l3 th2 ab3 l4"])

P("lizard", "Lizard", "animal",
  "sn 92 62.5; h1 81.9 50.7; h2 66.8 57.4; b1 51.7 54.1; b2 33.2 57.4; t1 18.1 45.7;"
  "t2 8 64.1; t3 19.8 80.9; b3 36.6 77.6; b4 55 75.9; h3 80.2 72.5; fl1 63.4 35.6;"
  "fl2 46.6 33.9; bl1 26.5 97.7; bl2 41.6 99.4; fr1 70.2 97.7; fr2 56.7 96.1",
  ["h2 h1 sn h3 b4 b3 t3 t2 t1 b2 b1 h2 fl1", "b1 fl2", "b2 bl1", "b3 bl2", "fr2 b4 fr1"])

P("camel", "Camel", "animal",
  "hd1 88.6 30.5; hd2 92 42.3; n1 78.6 44; n2 71.8 65.8; b1 56.7 69.2; hp1 46.6 45.7;"
  "hp2 36.6 69.2; hp3 26.5 47.3; r 13 67.5; t 8 89.3; bd 41.6 89.3; fl1 60.1 114.5;"
  "fl2 71.8 112.9; bl1 19.8 114.5; bl2 31.5 112.9; ea 80.2 18.8",
  ["bd b1 n2 n1 hd2 hd1 ea n1", "hp2 hp1 b1", "n2 bd fl1", "t r hp3 hp2 bd fl2", "bl1 r bl2"])

P("sunflower", "Sunflower", "plant",
  "c0 65.8 54.7; p0 92 45.6; c1 50 63.9; p1 71 82; c2 34.2 54.7; p2 29 82; c3 34.2 36.5;"
  "p3 8 45.6; c4 50 27.3; p4 29 9.2; c5 65.8 36.5; p5 71 9.2; s1 50 91.2; s2 50 115;"
  "lf1 24.4 105.9; lf2 29.9 124.1",
  ["c1 c0 c5 c4 c3 c2 c1 p1 c0 p0 c5 p5 c4 p4 c3 p3 c2 p2 c1 s1 s2 lf1 lf2 s2"])

P("pineapple", "Pineapple", "plant",
  "tl 24 46; tr 76 46; rr 90 74; br 74 112; bl 26 112; ll 10 74; c1 30 26; c2 40 2;"
  "c3 52 26;c4 66 0; c5 76 26",
  ["tl tr rr br bl ll tl", "tl br", "tr bl", "tl c1 c2 c3 c4 c5 tr", "c3 tl", "c3 tr"])

P("strawberry", "Strawberry", "plant",
  "t1 30.8 48.4; t2 50 42.6; t3 69.2 48.4; r1 86.5 69.6; b 50 125.3; l1 13.5 69.6;"
  "sd1 34.6 75.3; sd2 50 67.6; sd3 65.4 75.3; sd4 40.4 96.5; sd5 59.6 96.5; lf1 25 29.2;"
  "lf2 50 23.4; lf3 75 29.2; st 50 8",
  ["t1 t2 t3 r1 b l1 t1 sd1 sd2 t2 lf1", "sd3 sd2", "t3 sd3 sd5 sd4 sd1", "lf3 t2 lf2 st"])

P("pumpkin", "Pumpkin", "plant",
  "t 50 41.8; tl 30.9 45.7; tr 69.1 45.7; l 8 81.9; r 92 81.9; b 50 122; bl 29 118.2;"
  "br 71 118.2; ml 36.6 81.9; mr 63.4 81.9; st1 50 26.6; st2 65.3 11.3; lf 30.9 17",
  ["t tl l bl b br r tr t ml tl", "st1 t mr tr", "bl ml b mr br", "st2 st1 lf"])

P("lemon", "Lemon", "plant",
  "o0 50 24.7; i0 50 42.9; o1 79.7 37; i1 66.8 49.9; o2 92 66.7; i2 73.7 66.7; o3 79.7 96.4;"
  "i3 66.8 83.5; o4 50 108.7; i4 50 90.4; o5 20.3 96.4; i5 33.2 83.5; o6 8 66.7;"
  "i6 26.3 66.7; o7 20.3 37; i7 33.2 49.9; c 50 66.7",
  ["o0 o1 o2 o3 o4 o5 o6 o7 o0 i0 i1 i2 i3 i4 i5 i6 i7 i0 c i2 o2", "o4 i4 c i6 o6"])

P("wheat", "Wheat", "plant",
  "t 50 8; a1 50 31.9; a2 50 55.8; a3 50 79.7; s 50 125.3; gl1 23.9 21; gl2 23.9 44.9;"
  "gl3 23.9 68.8; gr1 76.1 21; gr2 76.1 44.9; gr3 76.1 68.8; lf1 19.6 99.3; lf2 80.4 108",
  ["t a1 a2 a3 s", "gl2 a2 gr2", "gl3 a3 gr3", "lf1 a3 lf2", "t gl1 a1 gr1 t"])

P("acorn", "Acorn", "plant",
  "cl 10 30; ctl 26 8; ctr 74 8; cr 90 30; m1 32 30; m2 50 30; m3 68 30; st 50 -10;n1 16 52;"
  "n2 26 78; nb 50 96; n3 74 78; n4 84 52",
  ["cl ctl ctr cr", "cl m1 m2 m3 cr", "m2 st", "ctl m2", "ctr m2", "cl n1 n2 nb n3 n4 cr"])

P("cupcake", "Cupcake", "object",
  "wl 20 60; p1 40 60; p2 60 60; wr 80 60; bl 32 112; q1 44 112; q2 56 112;"
  "br 68 112;f1 12 52; f2 26 36; f3 42 48; f4 58 34; f5 74 46; f6 88 52;ch1 44 14;"
  "ch2 60 14; ch3 52 2",
  ["wl p1 p2 wr br q2 q1 bl wl", "p1 q1", "p2 q2", "wl f1 f2 f3 f4 f5 f6 wr", "ch1 ch2 ch3 ch1"])

P("donut", "Donut", "object",
  "o0 50 0; o1 84 14; o2 98 48; o3 84 82; o4 50 96; o5 16 82; o6 2 48; o7 16 14;i0 50 26;"
  "i2 72 48; i4 50 70; i6 28 48;s1 22 26; s2 34 20; s3 66 20; s4 78 26; s5 24 70; s6 36 76;"
  "s7 64 76; s8 76 70",
  ["o0 o1 o2 o3 o4 o5 o6 o7 o0", "i0 i2 i4 i6 i0", "s1 s2", "s3 s4", "s5 s6", "s7 s8"])

P("burger", "Burger", "object",
  "bt 50 16.7; btl 12 38.7; btr 88 38.7; ml 8 60.7; mr 92 60.7; l1 20 74.7; l2 38 84.7;"
  "l3 62 74.7; l4 80 84.7; pl 10 92.7; pr 90 92.7; bbl 12 116.7; bbr 88 116.7; sb 50 112.7;"
  "s1 36 32.7; s2 64 32.7",
  ["pl ml btl bt btr mr ml l1 l2 l3 l4 mr pr pl bbl sb bbr pr", "s1 bt s2"])

P("coffee", "Coffee cup", "object",
  "tl 16 36; m1 22 66; bl 32 108; br 70 108; m2 80 66; tr 86 36;h1 96 50; h2 108 70;"
  "h3 92 86;ll 10 18; lt 50 18; lr 92 18; st1 34 2; st2 62 0",
  ["tl m1 bl br m2 tr tl", "m1 m2", "tr h1", "h1 h2", "h2 h3", "h3 m2", "ll lt lr", "ll tl",
   "lr tr", "lt st1", "lt st2"])

P("pizza", "Pizza slice", "object",
  "tp 50 14.7; cl 8 118.7; cr 92 118.7; kl 18 93.7; kr 82 93.7; p1 40 58.7; p2 58 58.7;"
  "p3 34 78.7; p4 66 78.7; p5 50 100.7; p6 50 76.7",
  ["p6 p1 p2 p6 p3 p5 p6 p4 p5", "kl tp kr cr cl kl kr"])

P("bamboo", "Bamboo", "plant",
  "a1 31.2 13; a2 31.2 39.9; a3 31.2 66.7; a4 31.2 93.5; a5 31.2 120.3; b1 67 23.8;"
  "b2 67 50.6; b3 67 77.4; b4 67 104.2; l1 9.8 27.3; l2 8 48.8; l3 90.2 38.1; l4 92 61.3;"
  "l5 50.9 72",
  ["a3 a2 a1", "b3 b2 b1", "a5 a4 a3 l5 b3 b4", "l1 a2 l2", "l3 b2 l4"])

P("lotus", "Lotus", "plant",
  "c 50 35.7; l1 26 47.7; l2 8 71.7; l3 34 69.7; r1 74 47.7; r2 92 71.7; r3 66 69.7;"
  "b 50 73.7; w1 14 97.7; w2 38 89.7; w3 62 89.7; w4 86 97.7; p1 50 57.7",
  ["b l3 l2 l1 c r1 r2 r3 b p1 c", "w2 w1 l2", "w3 w2 b w3 w4 r2", "l3 p1 r3"])

P("corn", "Corn", "plant",
  "t 50 16.1; cl 29 50.4; cr 71 50.4; b 50 115.3; ml 34.7 82.9; mr 65.3 82.9; m1 50 39;"
  "m2 50 65.7; m3 50 92.4; hl 8 73.3; hr 92 73.3; hb1 23.3 117.3; hb2 76.7 117.3",
  ["t cl ml b mr cr t m1 m2 m3 b", "cl m1 cr hr hb2 mr m2 ml hb1 hl cl"])

P("mushroom2", "Toadstool", "plant",
  "c0 8 63.1; c1 18.7 38.1; c2 42 23.8; c3 65.2 29.1; c4 84.9 48.8; c5 92 66.7;"
  "u1 68.8 66.7; u2 47.3 68.5; u3 25.9 66.7; sl 36.6 109.6; sr 58 109.6; g1 36.6 86.3;"
  "g2 58 86.3; d1 36.6 41.6; d2 59.8 47",
  ["c2 c1 c0 u3 u2 u1 c5 c4 c3 c2 d1 d2 c3", "u1 g2 u2 g1 g2 sr sl g1 u3"])

P("grapes", "Grapes", "plant",
  "g1 50 38.4; g2 28.3 58; g3 71.7 58; g4 8.7 79.7; g5 50 79.7; g6 91.3 79.7; g7 28.3 103.6;"
  "g8 71.7 103.6; g9 50 125.3; st 50 10.2; lf1 17.4 8; lf2 21.8 29.7",
  ["g1 g2 g3 g1 st lf1 lf2 st", "g4 g2 g5 g3 g6 g5 g4 g7 g5 g8 g6", "g7 g8 g9 g7"])

P("bus", "Bus", "object",
  "ft 6 20; fb 6 86; rb 96 86; rt 96 20; w1 30 86; w2 74 86;wl1 18 98; wlb 30 110;"
  "wl2 42 98; wr1 62 98; wrb 74 110; wr2 86 98;v1 20 40; v2 44 40; v3 44 58; v4 20 58;"
  "d1 84 40; d2 84 72",
  ["ft rt rb w2 w1 fb ft", "w1 wl1 wlb wl2 w1", "w2 wr1 wrb wr2 w2", "v1 v2 v3 v4 v1", "d1 d2",
   "rt d1", "rb d2"])

P("bridge", "Bridge", "object",
  "l1 8 70; l2 26.5 70; a1 36.6 56.6; a2 50 51.5; a3 63.4 56.6; r2 73.5 70; r1 92 70;"
  "d1 8 103.6; d2 26.5 103.6; d3 73.5 103.6; d4 92 103.6; t1 36.6 36.4; t2 63.4 36.4;"
  "c1 50 29.7; m1 26.5 51.5; m2 73.5 51.5",
  ["a2 a1 l2 l1", "d2 l2 m1 t1 c1 t2 m2 r2 a3 a2 c1", "d3 r2 r1", "d1 d2 d3 d4"])

P("church", "Church", "object",
  "sl 14.6 52.5; sr 42.9 52.5; sb 14.6 125.3; sbr 42.9 125.3; sp 28.8 22.2; cr1 28.8 8;"
  "nl 42.9 74.8; nr 85.4 74.8; nbr 85.4 125.3; w1 28.8 76.8; w2 28.8 99; d1 55.1 125.3;"
  "d2 55.1 101.1; d3 71.2 101.1; d4 71.2 125.3",
  ["sl sp sr nl nr nbr d4 d3 d2 d1 sbr sb sl sr", "sp cr1", "w1 w2"])

P("igloo", "Igloo", "object",
  "l 8 96.8; l1 13.5 67.6; l2 31.7 43.8; t 50 36.5; r2 68.3 43.8; r1 86.5 67.6; r 92 96.8;"
  "d1 35.4 96.8; d2 35.4 76.7; d3 50 69.4; d4 64.6 76.7; d5 64.6 96.8; b1 24.4 62.1;"
  "b2 75.6 62.1",
  ["l1 l d1 d2 d3 d4 d5 r r1 r2 t l2 l1 b1 d2", "b2 r1", "d4 b2 b1"])

P("mailbox", "Mailbox", "object",
  "bl 18 76; br 82 76; t 50 20; tl 18 42; tr 82 42; p1 44 76; p2 44 118;g1 22 118;"
  "g2 66 118; d1 60 48; d2 60 70; f1 96 44; f2 96 24; f3 84 24",
  ["bl tl t tr br p1 bl", "tl tr", "d1 d2", "tr d1", "br d2", "tr f1", "f1 f2", "f2 f3", "p1 p2",
   "p2 g1", "p2 g2"])

P("trafficlight", "Traffic light", "object",
  "tl 22 6; tr 78 6; bl 22 100; br 78 100; p 50 100; pb 50 134; f1 26 134;"
  "f2 74 134;r1 38 20; r2 62 20; r3 62 34; r4 38 34; y1 38 48; y2 62 48; g1 38 76; g2 62 76",
  ["tl tr br p bl tl", "r1 r2 r3 r4 r1", "y1 y2", "g1 g2", "p pb", "pb f1", "pb f2", "tl r4",
   "tr r3"])

P("bench", "Park bench", "object",
  "bl1 14.9 29; bl2 14.9 66.7; br1 85.1 29; br2 85.1 66.7; sl 8 80.4; sr 92 80.4;"
  "lg1 23.4 104.4; lg2 76.6 104.4; m1 14.9 47.8; m2 85.1 47.8; c1 32 66.7; c2 66.3 66.7",
  ["m1 m2 br1 bl1 m1 bl2 sl sr br2 m2", "bl2 lg1 c1 c2 lg2 br2"])

P("trophy", "Trophy", "object",
  "cl 25.2 18.9; cr 74.8 18.9; bl 36.6 66.7; br 63.4 66.7; hl 8 32.3; hl2 19.5 49.5;"
  "hr 92 32.3; hr2 80.5 49.5; st 50 66.7; st2 50 89.6; pl 27.1 89.6; pr 72.9 89.6;"
  "pbl 21.4 114.4; pbr 78.6 114.4; m1 40.5 39.9; m2 59.5 39.9",
  ["cl cr br st bl cl hl hl2 bl", "st2 st", "cr hr hr2 br", "m1 m2", "st2 pl pbl pbr pr st2"])

P("television", "Television", "object",
  "tl 8 36.1; tr 84.4 36.1; bl 8 99.1; br 84.4 99.1; il 17.5 45.7; ir 74.8 45.7;"
  "ibr 74.8 89.6; ibl 17.5 89.6; kt 92 49.5; kb 92 76.2; a1 32.8 20.8; a2 59.5 18.9;"
  "ap 46.2 36.1; lg1 21.4 114.4; lg2 71 114.4",
  ["tr ap tl bl br tr kt kb br lg2", "bl lg1", "a1 ap a2", "il ir ibr ibl il"])

P("violin", "Violin", "object",
  "L1 27.9 56.7; L2 12.4 72.2; L3 25.6 87.7; L4 10.2 105.4; L5 32.3 120.9; B 50 125.3;"
  "R5 67.7 120.9; R4 89.8 105.4; R3 74.4 87.7; R2 87.6 72.2; R1 72.1 56.7; n1 41.1 52.3;"
  "n2 58.9 52.3; h1 38.9 16.9; h2 61.1 16.9; sc 50 8; f1 38.9 89.9; f2 61.1 89.9;"
  "br1 38.9 105.4; br2 61.1 105.4",
  ["n1 L1 L2 L3 L4 L5 B R5 R4 R3 R2 R1 n2 n1 h1 sc h2 n2", "f1 f2 R3", "L3 f1 br1 br2 f2"])

P("microphone", "Microphone", "object",
  "h1 33.5 8; h2 66.5 8; h3 70.6 45.1; h4 29.4 45.1; m1 39.7 26.5; m2 60.3 26.5;"
  "n1 39.7 57.4; n2 60.3 57.4; b1 33.5 82.1; b2 66.5 82.1; s 50 82.1; st 50 115;"
  "f1 29.4 125.3; f2 70.6 125.3",
  ["h1 h2 h3 h4 h1 m1 m2 h2", "n1 h4", "n2 h3", "s b1 n1 n2 b2 s st f1", "st f2"])

P("sled", "Sled", "object",
  "bl 19.8 65; br 80.2 65; s1 33.2 65; s2 66.8 65; r1 13 86.8; r2 87 86.8; rl 8 73.4;"
  "rr 92 73.4; p1 19.8 46.5; p2 80.2 46.5; m1 33.2 46.5; m2 66.8 46.5; d1 50 65; d2 50 46.5",
  ["d1 s1 bl p1 m1 d2 m2 p2 br s2 d1 d2", "r1 s1 m1", "r2 s2 m2", "rl r1 r2 rr"])

P("seagull", "Seagull", "animal",
  "l1 8 59.1; l2 21.4 40.6; l3 36.6 54.1; m 50 38.9; r3 63.4 54.1; r2 78.6 40.6; r1 92 59.1;"
  "hd 50 62.5; bk 61.8 67.5; bd 50 80.9; tl 41.6 94.4; tr 58.4 94.4",
  ["l3 l2 l1", "r3 m l3 hd r3 r2 r1", "bd hd bk", "bd tl tr bd"])

P("beetle", "Beetle", "animal",
  "hd 50 31.7; a1 36 24.7; a2 64 24.7; t1 36 45.7; t2 64 45.7; b1 25.5 63.2; b2 74.5 63.2;"
  "b3 29 94.7; b4 71 94.7; bb 50 108.7; m 50 45.7; m2 50 94.7; l1 9.7 54.4; l2 90.3 54.4;"
  "l3 8 78.9; l4 92 78.9",
  ["t1 hd a1", "t2 hd a2", "b1 t1 m t2 b2 b4 bb b3 b1 l1", "m2 m", "b2 l2", "l3 b3 m2 b4 l4"])

P("panda", "Panda", "animal",
  "hl 15.3 59.4; ht 50 26.5; hr 84.7 59.4; hb 50 106.8; el1 8 33.8; el2 26.3 28.3;"
  "er1 92 33.8; er2 73.7 28.3; ey1 31.7 59.4; ey2 68.3 59.4; n 50 75.8; m1 43.6 86.8;"
  "m2 56.4 86.8; c1 35.4 72.1; c2 64.6 72.1",
  ["hl ht hr hb hl el1 el2 ht er2 er1 hr", "ey1 c1 n c2 ey2", "hb m1 n m2 hb"])

P("tiger", "Tiger", "animal",
  "hl 13.5 55.7; ht 50 22.8; hr 86.5 55.7; hb 50 110.5; el 19 30.1; er 81 30.1;"
  "ey1 33.6 55.7; ey2 66.4 55.7; n 50 72.1; m1 42.7 88.6; m2 57.3 88.6; s1 8 75.8;"
  "s2 92 75.8; w1 24.4 83.1; w2 75.6 83.1",
  ["hl ht hr hb hl el ht er hr", "m1 n ey1", "m2 n ey2", "s1 w1 m1 hb m2 w2 s2"])

P("bear", "Bear", "animal",
  "hl 13.7 59; ht 50 26.6; hr 86.3 59; hb 50 110.6; el1 8 30.4; el2 27.1 22.8; er1 92 30.4;"
  "er2 72.9 22.8; ey1 32.8 60.9; ey2 67.2 60.9; sn1 34.7 80; sn2 65.3 80; n 50 76.2;"
  "m 50 97.2",
  ["hl ht hr hb hl el1 el2 ht er2 er1 hr", "sn1 ey1", "sn2 ey2", "n sn1 m sn2 n m"])

P("monkey", "Monkey", "animal",
  "hl 23.7 55.3; ht 50 29; hr 76.2 55.3; hb 50 104.3; el 8 50; el2 11.5 72.8; er 92 50;"
  "er2 88.5 72.8; f1 41.2 76.3; f2 58.7 76.3; fb 50 92; ey1 39.5 60.5; ey2 60.5 60.5",
  ["f1 f2 fb f1 ey1 ey2 f2", "hl ht hr hb hl el el2 hl", "hr er er2 hr"])

P("koala", "Koala", "animal",
  "hl 25.5 54.4; ht 50 31.7; hr 74.5 54.4; hb 50 101.7; el1 8 36.9; el2 11.5 64.9;"
  "er1 92 36.9; er2 88.5 64.9; n1 43 75.4; n2 57 75.4; n3 50 89.4; ey1 37.8 63.2;"
  "ey2 62.3 63.2",
  ["hb hr ht hl hb n3 n1 n2 n3", "n1 ey1", "n2 ey2", "hl el1 el2 hl", "hr er1 er2 hr"])

P("bigdipper", "Big Dipper", "real-constellation",
  "d1 13.5 87.7; d2 33.6 98.6; d3 55.5 95; d4 73.7 84; d5 81 62.1; d6 59.1 54.8;"
  "d7 37.2 65.8; x1 8 58.4; x2 28.1 42; x3 92 40.2; x4 68.3 34.7",
  ["d1 d2 d3 d4 d5 d6 d7 d1 x1 x2", "d5 x3 x4 d6"])

P("cassiopeia", "Cassiopeia", "real-constellation",
  "a 8 51.5; b 29.4 83.6; c 50.9 47.9; d 72.3 81.9; e 92 46.1; f1 20.5 28.2; f2 59.8 26.5;"
  "f3 83.1 103.3; f4 40.2 106.9; g1 11.6 99.7",
  ["f3 d c b a f1 c f2 e d f4 b g1"])

P("cygnus", "Cygnus", "real-constellation",
  "t 50 18.3; m1 50 47.5; m2 50 73.1; b 50 115.1; wl1 24.4 43.8; wl2 8 34.7; wr1 75.6 43.8;"
  "wr2 92 32.9; wl3 20.8 63.9; wr3 79.2 63.9; f1 31.7 98.6; f2 68.3 98.6",
  ["b m2 m1 t", "wl1 m1 wr1 wr2", "wl2 wl1 wl3 m2 wr3 wr1", "f1 b f2"])

P("leo", "Leo", "real-constellation",
  "r 19.2 103.1; d 43.5 99.3; g 60.3 78.8; z 50.9 54.5; m 32.3 50.8; e 19.2 30.3; h 8 56.4;"
  "t 92 69.5; b 80.8 95.6; n 71.5 56.4; x 60.3 37.7",
  ["z g d r", "t g b t n x z m e h"])

P("scorpius", "Scorpius", "real-constellation",
  "a 72.6 30.1; b 92 19.3; c 55.4 36.5; d 64 58.1; e 59.7 83.9; f 44.6 105.4; g 23.1 114.1;"
  "h 8 99; i 14.5 77.4; j 33.8 73.1; k 46.8 53.7; l 81.2 47.3",
  ["a b", "d a c d e f g h i j", "a k d l a"])

P("orion2", "Taurus", "real-constellation",
  "al 58.4 66.7; e1 36 51.7; e2 13.6 38.7; e3 28.5 77.9; e4 8 90.9; h1 73.3 42.4;"
  "h2 90.1 27.5; h3 78.9 85.3; h4 92 105.9; b1 47.2 59.2; b2 41.6 72.3; c 24.8 61.1",
  ["e1 e2", "b1 e1 c e3 e4", "al b1 b2 e3", "h2 h1 al h3 h4"])

P("gemini", "Gemini", "real-constellation",
  "ca 21.6 19; po 73.8 16.7; a2 28.4 50.8; b2 69.3 48.5; a3 23.9 82.6; b3 64.8 80.3;"
  "a4 8 112.1; a5 39.8 116.6; b4 57.9 112.1; b5 92 109.8; m 46.6 64.4",
  ["a2 ca", "b2 po", "a4 a3 a2 m b2 b3 b4", "a5 a3 m b3 b5"])

P("perseus", "Perseus", "real-constellation",
  "a 56.3 54.1; b 71 31; c 92 18.4; d 41.6 77.2; e 24.8 104.5; f 8 115; g 64.7 81.4;"
  "h 83.6 100.3; i 37.4 33.1; j 14.3 47.8; k 75.2 112.9",
  ["d a b c", "e d g a i j", "f e k h g"])

P("snowman", "Snowman", "object",
  "h0 70 36; h1 60 53; h2 40 53; h3 30 36; h4 40 19; h5 60 19; b0 80 92; b1 65 118;"
  "b2 35 118;b3 20 92; b4 35 66; b5 65 66; t1 34 6; t2 34 -14; t3 66 -14; t4 66 6; al 4 48;"
  "ar 96 48;bt1 50 80; bt2 50 102",
  ["h0 h1 h2 h3 h4 h5 h0", "b0 b1 b2 b3 b4 b5 b0", "h1 b5", "h2 b4", "h4 t1", "t1 t2 t3 t4",
   "t4 h5", "t1 t4", "b4 al", "b5 ar", "bt1 bt2"])

P("snowflake", "Snowflake", "object",
  "t0 92 66.7; m0 71 66.7; b0 80.3 84.2; t1 71 103; m1 60.5 84.9; b1 50 101.7; t2 29 103;"
  "m2 39.5 84.9; b2 19.7 84.2; t3 8 66.7; m3 29 66.7; b3 19.7 49.2; t4 29 30.3;"
  "m4 39.5 48.5; b4 50 31.7; t5 71 30.3; m5 60.5 48.5; b5 80.3 49.2; c 50 66.7",
  ["t0 m0 c m1 t1", "t2 m2 c m3 t3", "t4 m4 c m5 t5", "m0 b0 m1 b1 m2 b2 m3 b3 m4 b4 m5 b5 m0"])

P("dice", "Dice", "object",
  "tl 8 51.5; tr 64 51.5; br 64 107.5; bl 8 107.5; ut 36 25.8; ur 92 25.8; rr 92 81.8;"
  "p1 22 65.5; p2 50 65.5; p3 36 79.5; p4 22 93.5; p5 50 93.5; q1 78 49.2; q2 78 72.5",
  ["tl tr br bl tl ut ur tr", "br rr ur", "p1 p3 p5", "p2 p3 p4", "q1 q2"])

P("ship", "Sailboat", "object",
  "hl 8 94.7; hr 92 94.7; hbl 23.7 112.2; hbr 76.2 112.2; d1 32.5 94.7; d2 67.5 94.7;"
  "m1 50 94.7; m2 50 21.2; s1 57 36.9; s2 83.3 80.7; s3 57 80.7; j1 43 40.4; j2 16.7 80.7;"
  "j3 43 80.7",
  ["m1 d2 hr hbr hbl hl d1 m1 m2 s1 s2 s3 m1 j3 j2 j1 m2"])

P("skateboard", "Skateboard", "object",
  "l1 8 54.9; l2 23.1 38.1; r1 92 54.9; r2 76.9 38.1; dl 34.9 38.1; dr 65.1 38.1;"
  "d1 33.2 56.6; d2 66.8 56.6; t1 33.2 76.7; t2 66.8 76.7; w1 18.1 95.2; w2 43.3 95.2;"
  "w3 56.7 95.2; w4 81.9 95.2",
  ["dl l2 l1 d1 d2 r1 r2 dr dl d1 t1 w1", "dr d2 t2 w3", "w2 t1 t2 w4"])

P("lantern", "Lantern", "object",
  "tl 22.4 40.2; tr 77.6 40.2; bl 22.4 116.1; br 77.6 116.1; ct 50 19.5; h1 33.9 8;"
  "h2 66.1 8; gl 31.6 54; gr 68.4 54; gbl 31.6 102.3; gbr 68.4 102.3; bt1 13.2 125.3;"
  "bt2 86.8 125.3; f 50 77",
  ["tl tr br bl tl ct tr", "gl gr gbr gbl gl f gr", "br bt2 bt1 bl", "h1 ct h2", "gbr f gbl"])

P("well", "Wishing well", "object",
  "rl 10 65.6; rr 87.9 65.6; bl 20.3 114.8; br 77.7 114.8; m1 8 90.2; m2 90 90.2;"
  "pl 26.4 65.6; pr 71.5 65.6; pt 49 18.5; e1 22.3 34.9; e2 75.6 34.9; rp 49 45.2;"
  "rb 49 65.6; h1 92 41.1",
  ["rl pl rb pr rr br bl rl m1 bl", "m2 rr", "e2 e1 rp e2 h1", "pl pt pr", "rb rp", "br m2 m1"])

P("barn", "Barn", "object",
  "l1 8 52.1; l2 19 28.3; r2 81 28.3; r1 92 52.1; bl 8 105; br 92 105; d1 39 105;"
  "d2 39 68.5; d3 61 68.5; d4 61 105; w1 19 63; w2 19 83.1; w3 81 63; w4 81 83.1;"
  "hl 39 44.8; hr 61 44.8",
  ["l1 l2 r2 r1 br d4 d3 d2 d1 bl l1 w1 w2", "hl l2", "hr hl d2", "r2 hr d3", "r1 w3 w4"])

P("birdhouse", "Bird house", "object",
  "l 8.8 51.2; t 50 8; r 91.2 51.2; bl 25.3 104.7; br 74.7 104.7; e1 25.3 51.2;"
  "e2 74.7 51.2; h1 39.7 61.5; h2 60.3 61.5; h3 60.3 82.1; h4 39.7 82.1; p 50 92.4;"
  "pb 50 113; g1 29.4 125.3; g2 70.6 125.3",
  ["e1 l t r e2 e1 bl br e2", "h3 h2 h1 h4 h3 p pb g1", "h4 p", "pb g2"])

P("chessrook", "Chess rook", "object",
  "t1 16 10; t2 30 10; t3 30 24; t4 44 24; t5 44 10; t6 58 10; t7 58 24; t8 72 24;"
  "t9 72 10;t10 86 10; n1 78 40; n2 22 40; m1 26 62; m2 74 62; b1 22 86; b2 78 86;"
  "f1 10 106;f2 90 106",
  ["t1 t2 t3 t4 t5 t6 t7 t8 t9 t10 n1 m2 b2 f2 f1 b1 m1 n2 t1", "m1 m2", "n1 n2", "b1 b2"])

P("key2", "Key", "object",
  "b1 20 8; b2 4 34; b3 20 60; b4 48 60; b5 62 34; b6 48 8; h1 32 26; h2 32 44;t1 82 34;"
  "t2 82 58; t3 102 34; t4 102 56; e 118 34",
  ["b1 b2 b3 b4 b5 b6 b1", "h1 h2", "b1 h1", "b3 h2", "b5 t1", "t1 t2", "t1 t3", "t3 t4", "t3 e"])

P("anchor2", "Anchor", "object",
  "r1 50.9 23.8; r2 66.3 37.5; r3 50.9 51.2; r4 35.4 37.5; s1 50.9 65; s2 50.9 109.5;"
  "al 23.4 65; ar 78.3 65; fl1 20 92.4; fl2 9.7 71.8; fr1 81.7 92.4; fr2 92 71.8;"
  "c1 21.7 27.2; c2 8 35.8",
  ["r3 r2 r1 r4 r3 s1 s2 fl1 fl2 al s1 ar fr2 fr1 s2", "r4 c1 c2"])

P("pencil", "Pencil", "object",
  "t 8 66.7; c1 28.2 51.5; c2 28.2 81.8; f1 43.3 51.5; f2 43.3 81.8; e1 76.9 51.5;"
  "e2 76.9 81.8; er1 92 51.5; er2 92 81.8; m1 58.4 51.5; m2 58.4 81.8",
  ["c1 t c2 f2 m2 e2 er2 er1 e1 m1 f1 c1 c2", "f1 f2", "m1 m2", "e1 e2"])

P("flag", "Flag", "object",
  "p1 18 124; h1 18 96; b4 18 58; b1 18 22; fin 18 4; t1 52 16; t2 86 22; r 86 58;"
  "m 52 64;g1 0 124; g2 44 124",
  ["p1 h1 b4 b1 fin", "b1 t1 t2 r m b4", "t1 m", "p1 g1", "p1 g2"])

ORDER = [
    "fish", "drum", "acorn", "compass", "starfish", "cassiopeia", "fox", "hourglass",
    "pineapple", "pencil", "seagull", "bigdipper", "koala", "pizza", "grapes", "sunglasses",
    "monkey", "gemini", "turtle", "telescope", "corn", "umbrella", "whale", "leo", "bat",
    "balloon", "lotus", "bell", "bear", "perseus", "bird", "bench", "pumpkin", "flag",
    "butterfly", "cygnus", "hammer", "wheat", "icecream", "ant", "orion2", "deer",
    "kite", "bamboo", "frog", "scorpius", "giraffe", "mushroom2", 
    "horse", "orion", "ladybug", "key2", "pine", "panda", "tiger", "tent", 
    "anchor2", "bee", "beetle", "chessrook", "strawberry", "dice", "camel", "headphones",
    "sunflower", "dog", "octopus", "igloo", "lemon", "hedgehog", "lizard",
    "lantern", "daisy", "laptop", "penguin", "spider", "mailbox", "cactus", "microphone", "crab",
    "ship", "skateboard", "sled", "teapot", "trafficlight", "well", "birdhouse", "candle",
    "church", "coffee", "gift", "television", "barn", "bridge", "burger", "camera",
    "donut", "trophy", "bus", "clock", "cupcake", "rocket", "car", "ferriswheel",
    "robot", "snowflake", "snowman", "train", "violin", "castle"
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
    return dict(id=p["id"], title=p["title"], category=p["category"], dots=dots, edges=p["edges"])


def dumps(puzzles):
    """Compact but diff-friendly: one dot per line, edges on one line."""
    j = lambda v: json.dumps(v, ensure_ascii=False)
    blocks = []
    for p in puzzles:
        dots = ",\n".join("      " + j(d) for d in p["dots"])
        blocks.append(
            f'  {{\n    "id": {j(p["id"])},\n    "title": {j(p["title"])},\n'
            f'    "category": {j(p["category"])},\n    "dots": [\n{dots}\n    ],\n'
            f'    "edges": {j(p["edges"])}\n  }}')
    return "[\n" + ",\n".join(blocks) + "\n]\n"


if __name__ == "__main__":
    by_id = {p["id"]: p for p in PUZZLES}
    assert sorted(ORDER) == sorted(by_id), set(by_id) ^ set(ORDER)
    out = [fit(by_id[i]) for i in ORDER]
    if len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        sys.exit("usage: python tools/author_puzzles.py [OUTPUT.json]  (default: puzzles/puzzles.json)")
    path = sys.argv[1] if len(sys.argv) > 1 else ROOT / "puzzles" / "puzzles.json"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(out))
    for p in out:
        print(f"{p['id']:14s} {p['category']:18s} dots={len(p['dots']):2d} edges={len(p['edges'])}")
