"""Validate puzzles/puzzles.json before publishing.

Run:  python tools/validate_puzzles.py [path/to/puzzles.json]

Checks (JSON Schema can't express the graph ones):
  - schema shape (via `jsonschema` against puzzles/schema.json if installed, else minimal checks)
  - puzzle ids unique; dot ids unique within a puzzle
  - every edge references existing dots; no self-loops; no duplicate edges (a-b == b-a)
  - each dot's degree == number of edges touching it   <- the key invariant
  - no isolated dots (degree >= 1)
  - minimum spacing between dots (tap-target size on a phone), see MIN_DOT_SPACING
  - every dot at least MIN_EDGE_MARGIN from the board edge (x in 0-1, y in 0-BOARD_H)
  - no dot lies on (or grazes) a solution line it isn't an endpoint of, see MIN_LINE_CLEARANCE
Also prints the date the last puzzle is played, and warns when that's close.

OPEN: solution uniqueness — optionally count alternative graphs that satisfy the same
degree sequence on these positions (e.g. restricted to "plausible" short edges), to flag
puzzles where the numbers alone are too ambiguous. Not implemented.

Exit code 1 if any errors.
"""

import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUZZLES = ROOT / "puzzles" / "puzzles.json"
SCHEMA = ROOT / "puzzles" / "schema.json"

# Keep in sync with LAUNCH_DATE_UTC in js/daily.js.
LAUNCH_DATE = date(2026, 10, 1)
RUNWAY_WARN_DAYS = 14

# Portrait 3:4 board: one unit = board width, so x in [0, 1] and y in [0, BOARD_H].
# Keep in sync with BOARD_H in js/render.js.
BOARD_H = 4 / 3

# Taps go to the nearest dot (js/render.js dotAtPoint), so each dot owns everything closer to
# it than to any other dot. 0.11 ~= 38px centre to centre on a 360px phone (board ~344px wide):
# a tap up to ~19px off still picks the right dot.
MIN_DOT_SPACING = 0.11

# Dot centre to board edge. DOT_R in js/render.js is 0.028; the rest is room for the
# selection stroke and win glow, which the SVG would otherwise clip.
MIN_EDGE_MARGIN = 0.05

# A dot closer than this to a solution line it isn't part of looks like it's on that line.
# ~ DOT_R (0.028) + half the line width + a visible gap.
MIN_LINE_CLEARANCE = 0.05


def check_schema(puzzles) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        print("note: `jsonschema` not installed - using minimal shape checks "
              "(pip install jsonschema for the full schema)")
        return check_shape_minimal(puzzles)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    # Draft 7 exists in jsonschema 3.x and 4.x (Draft202012Validator is 4.0+ only).
    validator = jsonschema.Draft7Validator(schema)
    return [f"schema: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in validator.iter_errors(puzzles)]


def check_shape_minimal(puzzles) -> list[str]:
    """Just enough structure for the graph checks to run safely."""
    if not isinstance(puzzles, list):
        return ["schema: top level must be a list of puzzles"]
    errors = []
    for i, p in enumerate(puzzles):
        where = f"[#{i}]"
        if not isinstance(p, dict):
            errors.append(f"{where} puzzle must be an object")
            continue
        for key in ("id", "title", "category", "dots", "edges"):
            if key not in p:
                errors.append(f"{where} missing '{key}'")
        for d in p.get("dots", []):
            if not isinstance(d, dict) or not {"id", "x", "y", "degree"} <= d.keys():
                errors.append(f"{where} dot needs id, x, y, degree: {d!r}")
                continue
            for axis, hi in (("x", 1), ("y", BOARD_H)):
                v = d[axis]
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= hi:
                    errors.append(f"{where} dot {d['id']}: {axis}={v!r} must be a number "
                                  f"in [0, {hi:.4g}]")
            deg = d["degree"]
            if isinstance(deg, bool) or not isinstance(deg, int) or deg < 1:
                errors.append(f"{where} dot {d['id']}: degree={deg!r} must be an integer >= 1")
        for e in p.get("edges", []):
            if not (isinstance(e, list) and len(e) == 2 and all(isinstance(x, str) for x in e)):
                errors.append(f"{where} edge must be a pair of dot ids: {e!r}")
    return errors


def check_puzzle(i: int, p: dict) -> list[str]:
    where = f"[#{i} {p['id']}]"
    errors = []

    dots = {}
    for d in p["dots"]:
        if d["id"] in dots:
            errors.append(f"{where} duplicate dot id '{d['id']}'")
            continue
        dots[d["id"]] = d

    touching = {dot_id: 0 for dot_id in dots}
    seen = set()
    for a, b in p["edges"]:
        if a == b:
            errors.append(f"{where} self-loop on '{a}'")
            continue
        missing = [x for x in (a, b) if x not in dots]
        if missing:
            errors.append(f"{where} edge {a}-{b} references missing dot(s): {', '.join(missing)}")
            continue
        key = frozenset((a, b))
        if key in seen:
            errors.append(f"{where} duplicate edge {a}-{b}")
            continue
        seen.add(key)
        touching[a] += 1
        touching[b] += 1

    for dot_id, n in touching.items():
        if n == 0:
            errors.append(f"{where} dot '{dot_id}' is isolated (no edges)")
        elif n != dots[dot_id]["degree"]:
            errors.append(f"{where} dot '{dot_id}' has degree {dots[dot_id]['degree']} "
                          f"but {n} edge(s) touch it")

    ds = list(dots.values())
    for j, d in enumerate(ds):
        for e in ds[j + 1:]:
            dist = math.hypot(d["x"] - e["x"], d["y"] - e["y"])
            if dist < MIN_DOT_SPACING:
                errors.append(f"{where} dots '{d['id']}' and '{e['id']}' are {dist:.3f} apart "
                              f"(min {MIN_DOT_SPACING})")

    m = MIN_EDGE_MARGIN
    for d in ds:
        if not (m <= d["x"] <= 1 - m and m <= d["y"] <= BOARD_H - m):
            errors.append(f"{where} dot '{d['id']}' at ({d['x']}, {d['y']}) is closer than {m} "
                          f"to the board edge (x {m}-{1 - m:.3f}, y {m}-{BOARD_H - m:.3f})")

    for a, b in sorted(tuple(sorted(k)) for k in seen):
        for d in ds:
            if d["id"] in (a, b):
                continue
            dist = dist_to_segment(d, dots[a], dots[b])
            if dist < MIN_LINE_CLEARANCE:
                errors.append(f"{where} dot '{d['id']}' is {dist:.3f} from line {a}-{b} "
                              f"it isn't part of (min {MIN_LINE_CLEARANCE})")
    return errors


def dist_to_segment(p: dict, a: dict, b: dict) -> float:
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    len2 = dx * dx + dy * dy
    t = 0.0 if len2 == 0 else max(0.0, min(1.0, ((p["x"] - a["x"]) * dx + (p["y"] - a["y"]) * dy) / len2))
    return math.hypot(p["x"] - (a["x"] + t * dx), p["y"] - (a["y"] + t * dy))


def report_runway(count: int) -> None:
    if count == 0:
        return
    last = LAUNCH_DATE + timedelta(days=count - 1)
    days_left = (last - datetime.now(timezone.utc).date()).days
    print(f"Last puzzle plays on {last} (UTC), {days_left} day(s) from today.")
    if days_left < RUNWAY_WARN_DAYS:
        print(f"warning: fewer than {RUNWAY_WARN_DAYS} days of puzzles left - "
              "after that players see the 'back tomorrow' message.")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else PUZZLES
    puzzles = json.loads(path.read_text(encoding="utf-8"))

    errors = check_schema(puzzles)
    if errors:  # graph checks assume the shape is right
        print("\n".join(errors))
        print(f"FAILED: {len(errors)} problem(s)")
        return 1

    ids = [p["id"] for p in puzzles]
    for dup in sorted({x for x in ids if ids.count(x) > 1}):
        errors.append(f"duplicate puzzle id '{dup}'")
    for i, p in enumerate(puzzles):
        errors.extend(check_puzzle(i, p))

    if errors:
        print("\n".join(errors))
        print(f"FAILED: {len(errors)} problem(s)")
        return 1
    print(f"OK: {len(puzzles)} puzzle(s)")
    report_runway(len(puzzles))
    return 0


if __name__ == "__main__":
    sys.exit(main())
