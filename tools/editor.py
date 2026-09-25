"""Constelly puzzle editor — runs only on your own computer.

    python tools/editor.py                 # opens http://127.0.0.1:8001/tools/editor.html
    python tools/editor.py --port 8002 --no-browser

Serves the repo on 127.0.0.1 (other machines can't reach it) plus a small JSON API that the
editor page (tools/editor.html) uses to read and write tools/author_puzzles.py — still the
source of truth. Saving a puzzle rewrites its P(...) block (or adds a new one and puts it in
ORDER), regenerates puzzles/puzzles.json, then runs validate_puzzles.py and puzzle_quality.py
and shows their output. The published site has no API, so the editor page does nothing there.

Standard library only. Stop it with Ctrl+C.
"""
import argparse
import ast
import json
import re
import runpy
import subprocess
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = ROOT / "tools" / "author_puzzles.py"
LAUNCH = date(2026, 10, 1)  # keep in sync with LAUNCH_DATE_UTC in js/daily.js
CATEGORIES = ["animal", "plant", "object"]
CLUE_MAX = 80
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
SAVE_LOCK = threading.Lock()


def today_index():
    return (datetime.now(timezone.utc).date() - LAUNCH).days


# ---- reading author_puzzles.py ----------------------------------------------------------------

def load_module(source=None):
    """Run author_puzzles.py (not as __main__, so it doesn't write anything) → its globals."""
    if source is None:
        return runpy.run_path(str(AUTHOR), run_name="author_puzzles")
    ns = {"__name__": "author_puzzles", "__file__": str(AUTHOR)}
    exec(compile(source, str(AUTHOR), "exec"), ns)
    return ns


def list_puzzles():
    mod = load_module()
    by_id = {p["id"]: p for p in mod["PUZZLES"]}
    redrawn = set(mod.get("REDRAWN", []))
    out = []
    for index, pid in enumerate(mod["ORDER"]):
        fitted = mod["fit"](by_id[pid])
        out.append({
            "index": index, "id": pid, "title": fitted["title"], "category": fitted["category"],
            "clue": fitted.get("clue", ""), "redrawn": pid in redrawn,
            "colors": fitted.get("colors", {}),
            "dots": [{"id": d["id"], "x": d["x"], "y": d["y"]} for d in fitted["dots"]],
            "edges": fitted["edges"],
        })
    return {"launch": LAUNCH.isoformat(), "todayIndex": today_index(), "categories": CATEGORIES,
            "palette": mod.get("PALETTE", {}), "puzzles": out}


# ---- writing author_puzzles.py ----------------------------------------------------------------

def num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def edges_to_paths(names, edges):
    """Cover the edges with as few walks as is easy (start at odd-degree dots first)."""
    adj = {n: [] for n in names}
    for i, (a, b) in enumerate(edges):
        adj[a].append((b, i))
        adj[b].append((a, i))
    used, paths = set(), []

    def walk(cur):
        path = [cur]
        while True:
            nxt = next(((v, i) for v, i in adj[cur] if i not in used), None)
            if nxt is None:
                return path
            used.add(nxt[1])
            cur = nxt[0]
            path.append(cur)

    starts = [n for n in names if len(adj[n]) % 2] + list(names)
    for n in starts:
        while any(i not in used for _, i in adj[n]):
            paths.append(" ".join(walk(n)))
    return paths


def wrap(items, sep, width, indent):
    """Join items with sep into lines no longer than width (continuation lines get indent)."""
    lines, cur = [], ""
    for it in items:
        piece = it if not cur else sep + it
        if cur and len(indent) + len(cur) + len(piece) > width:
            lines.append(cur + sep.rstrip())
            cur = it
        else:
            cur += piece
    lines.append(cur)
    return lines


def format_colors(names, colors, palette):
    """{"a|b": "green"} -> 'colors={"green": ["a b c"], ...}' in palette order, or ''."""
    by_color = {}
    for k, c in colors.items():
        by_color.setdefault(c, []).append(k.split("|"))
    parts = []
    for c in [c for c in palette if c in by_color]:
        paths = edges_to_paths([n for n in names if any(n in e for e in by_color[c])], by_color[c])
        parts.append(f"{json.dumps(c)}: [" + ", ".join(json.dumps(x) for x in paths) + "]")
    if not parts:
        return ""
    lines = wrap(parts, ", ", 94, "  ")
    return "colors={" + "\n    ".join(lines) + "}"


def format_block(pid, title, category, pts, paths, clue="", colors_src=""):
    items = [f"{n} {num(x)} {num(y)}" for n, (x, y) in pts]
    chunks = wrap(items, "; ", 94, "  ")
    pts_src = "\n  ".join(json.dumps(c) for c in chunks)  # wrap() ends each chunk but the last with ";"
    path_lines = wrap([json.dumps(p) for p in paths], ", ", 94, "   ")
    paths_src = "[" + "\n   ".join(path_lines) + "]"
    clue_src = f",\n  clue={json.dumps(clue, ensure_ascii=False)}" if clue else ""
    colors_src = f",\n  {colors_src}" if colors_src else ""
    return (f"P({json.dumps(pid)}, {json.dumps(title, ensure_ascii=False)}, {json.dumps(category)},\n"
            f"  {pts_src},\n  {paths_src}{clue_src}{colors_src})")


def format_list(name, ids):
    lines = wrap([json.dumps(i) for i in ids], ", ", 96, "    ")
    return f"{name} = [\n" + "".join(f"    {l}\n" for l in lines) + "]"


def top_level(tree):
    blocks, spans = {}, {}
    for node in tree.body:
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", None) == "P" and node.value.args
                and isinstance(node.value.args[0], ast.Constant)):
            blocks[node.value.args[0].value] = (node.lineno, node.end_lineno)
        elif (isinstance(node, ast.Assign) and len(node.targets) == 1
              and getattr(node.targets[0], "id", None) in ("ORDER", "REDRAWN")):
            spans[node.targets[0].id] = (node.lineno, node.end_lineno)
    return blocks, spans


class BadRequest(Exception):
    pass


def check_request(body, existing_ids, order, today, palette=()):
    pid = body.get("id", "")
    title = str(body.get("title", "")).strip()
    clue = " ".join(str(body.get("clue") or "").split())
    if len(clue) > CLUE_MAX:
        raise BadRequest(f"clue is longer than {CLUE_MAX} characters")
    category = body.get("category")
    dots, edges = body.get("dots") or [], body.get("edges") or []
    is_new = bool(body.get("isNew"))
    if not isinstance(pid, str) or not ID_RE.match(pid):
        raise BadRequest("id must be lowercase letters, digits and dashes")
    if is_new and pid in existing_ids:
        raise BadRequest(f"there is already a puzzle with id '{pid}'")
    if not is_new and pid not in existing_ids:
        raise BadRequest(f"no puzzle with id '{pid}'")
    if not title:
        raise BadRequest("title is empty")
    if category not in CATEGORIES:
        raise BadRequest(f"category must be one of {', '.join(CATEGORIES)}")
    if len(dots) < 2 or not edges:
        raise BadRequest("a puzzle needs at least two dots and one line")
    names, pts = set(), []
    for d in dots:
        n, x, y = d.get("id"), d.get("x"), d.get("y")
        if not isinstance(n, str) or not NAME_RE.match(n) or n in names:
            raise BadRequest(f"bad or duplicate dot name {n!r}")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (x, y)):
            raise BadRequest(f"dot {n} has no position")
        names.add(n)
        pts.append((n, round(x * 100, 1), round(y * 100, 1)))  # grid units: board width = 100
    seen, touched = set(), set()
    for e in edges:
        if not (isinstance(e, list) and len(e) == 2 and e[0] in names and e[1] in names and e[0] != e[1]):
            raise BadRequest(f"bad line {e!r}")
        k = frozenset(e)
        if k in seen:
            raise BadRequest(f"duplicate line {e[0]}-{e[1]}")
        seen.add(k)
        touched.update(e)
    colors = {}
    raw_colors = body.get("colors") or {}
    if not isinstance(raw_colors, dict):
        raise BadRequest("colors must be an object")
    for k, c in raw_colors.items():
        a, _, b = str(k).partition("|")
        if frozenset((a, b)) not in seen:
            raise BadRequest(f"colour on {k}, which isn't a line")
        if c not in palette:
            raise BadRequest(f"unknown colour {c!r}")
        if c != "yellow":
            colors["|".join(sorted((a, b)))] = c
    if names - touched:
        raise BadRequest(f"dots with no lines: {', '.join(sorted(names - touched))}")
    xs, ys = [p[1] for p in pts], [p[2] for p in pts]
    if max(xs) == min(xs) or max(ys) == min(ys):
        raise BadRequest("dots must not all lie on one horizontal or vertical line")

    index = order.index(pid) if not is_new else None
    if not is_new and index <= today and not body.get("confirmPlayed"):
        raise BadRequest("this puzzle has already been played - confirm to change it")
    position = None
    if is_new:
        position = body.get("position", len(order))
        if not isinstance(position, int) or not (max(today + 1, 0) <= position <= len(order)):
            raise BadRequest(f"position must be between {max(today + 1, 0)} and {len(order)} "
                             "(puzzles that have been played can't move)")
    return (pid, title, category, [(n, (x, y)) for n, x, y in pts], [list(e) for e in edges], position,
            clue, bool(body.get("redrawn")), colors)


def run_tool(name, *args):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / name), *args], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, (r.stdout + r.stderr).strip()


def save(body):
    with SAVE_LOCK:
        raw = AUTHOR.read_bytes().decode("utf-8")
        crlf = "\r\n" in raw
        src = raw.replace("\r\n", "\n")
        mod = load_module(src)
        order = list(mod["ORDER"])
        palette = list(mod.get("PALETTE", {}))
        pid, title, category, pts, edges, position, clue, is_redrawn, colors = check_request(
            body, {p["id"] for p in mod["PUZZLES"]}, order, today_index(), palette)
        redrawn = [i for i in mod.get("REDRAWN", []) if i != pid]
        if is_redrawn:
            redrawn.append(pid)

        names = [n for n, _ in pts]
        block = format_block(pid, title, category, pts, edges_to_paths(names, edges), clue,
                             format_colors(names, colors, palette))
        lines = src.split("\n")
        blocks, spans = top_level(ast.parse(src))
        # Replace from the bottom up so earlier line numbers stay valid.
        edits = []
        if "REDRAWN" in spans:
            edits.append((spans["REDRAWN"], format_list("REDRAWN", redrawn).split("\n")))
        if position is None:  # update in place
            edits.append((blocks[pid], block.split("\n")))
        else:  # new: block goes just above ORDER, id goes into ORDER at `position`
            order.insert(position, pid)
            edits.append((spans["ORDER"], block.split("\n") + [""] + format_list("ORDER", order).split("\n")))
        for (start, end), new in sorted(edits, key=lambda e: -e[0][0]):
            lines[start - 1:end] = new
        new_src = "\n".join(lines)

        # Make sure the file still runs (P() asserts, ORDER matches) before touching the disk.
        check = load_module(new_src)
        assert sorted(check["ORDER"]) == sorted(p["id"] for p in check["PUZZLES"])
        AUTHOR.write_bytes((new_src.replace("\n", "\r\n") if crlf else new_src).encode("utf-8"))

    gen_code, gen_out = run_tool("author_puzzles.py")
    val_code, val_out = run_tool("validate_puzzles.py")
    _, qual_out = run_tool("puzzle_quality.py")
    qual_line = next((l for l in qual_out.splitlines() if re.match(rf"\s*\d+ {re.escape(pid)}\s", l)), "")
    return {"ok": gen_code == 0 and val_code == 0, "id": pid,
            "generate": "OK" if gen_code == 0 else gen_out, "validate": val_out,
            "quality": qual_line.strip(), "qualitySummary": qual_out.splitlines()[-2:] if qual_out else []}


# ---- HTTP -------------------------------------------------------------------------------------

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if self.path.startswith("/api/") or (args and str(args[1])[:1] in "45"):
            super().log_message(fmt, *args)

    def local_only(self):
        # Refuse requests from web pages on other sites (and DNS-rebinding tricks).
        host = (self.headers.get("Host") or "").split(":")[0]
        origin = self.headers.get("Origin")
        ok = host in ("127.0.0.1", "localhost") and (
            origin is None or re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", origin))
        if not ok:
            self.reply(403, {"error": "local requests only"})
        return ok

    def reply(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/puzzles":
            if self.local_only():
                try:
                    self.reply(200, list_puzzles())
                except Exception as e:  # e.g. a syntax error in author_puzzles.py
                    self.reply(500, {"error": f"{type(e).__name__}: {e}"})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/save" or not self.local_only():
            if self.path != "/api/save":
                self.reply(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self.reply(200, save(body))
        except BadRequest as e:
            self.reply(400, {"error": str(e)})
        except Exception as e:
            self.reply(500, {"error": f"{type(e).__name__}: {e}"})


def main():
    ap = argparse.ArgumentParser(description="Constelly puzzle editor (local only)")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(ROOT)))
    url = f"http://127.0.0.1:{args.port}/tools/editor.html"
    print(f"Constelly editor: {url}   (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
