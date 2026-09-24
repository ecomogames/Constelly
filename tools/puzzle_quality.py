"""How interesting is each puzzle? python tools/puzzle_quality.py [puzzles.json]

A dot-to-dot is dull when the solution is one long chain of degree-2 dots: the numbers tell you
nothing and you just follow the outline (e.g. the first Apple). It's interesting when lines branch,
so the player has to work out which neighbour a line goes to (e.g. Car, Crab, Teapot).

    chain  longest run of consecutive degree-2 dots   (want <= 5)
    junc%  share of dots with degree >= 3             (want >= 25)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_CHAIN = 5
MIN_JUNCTION_SHARE = 25


def metrics(p):
    deg = {d["id"]: d["degree"] for d in p["dots"]}
    adj = {d["id"]: [] for d in p["dots"]}
    for a, b in p["edges"]:
        adj[a].append(b)
        adj[b].append(a)
    best, seen = 0, set()
    for start in deg:
        if deg[start] != 2 or start in seen:
            continue
        run, seen_here = 1, {start}
        seen.add(start)
        for first in adj[start]:
            prev, cur = start, first
            while deg.get(cur) == 2 and cur not in seen_here:
                seen.add(cur)
                seen_here.add(cur)
                run += 1
                nxt = [x for x in adj[cur] if x != prev]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
        best = max(best, run)
    junctions = sum(1 for v in deg.values() if v >= 3)
    return best, junctions, round(100 * junctions / len(deg))


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else ROOT / "puzzles" / "puzzles.json"
    puzzles = json.load(open(path, encoding="utf-8"))
    dull = []
    print(f"{'#':>3} {'id':14} {'dots':>4} {'chain':>5} {'junc%':>5}")
    for i, p in enumerate(puzzles, 1):
        chain, _, share = metrics(p)
        bad = chain > MAX_CHAIN or share < MIN_JUNCTION_SHARE
        if bad:
            dull.append(p["id"])
        print(f"{i:>3} {p['id']:14} {len(p['dots']):>4} {chain:>5} {share:>5}{'  <- dull' if bad else ''}")
    print(f"\n{len(puzzles) - len(dull)}/{len(puzzles)} pass (chain <= {MAX_CHAIN}, junc% >= {MIN_JUNCTION_SHARE})")
    if dull:
        print("dull:", " ".join(dull))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
