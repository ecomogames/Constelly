// SVG rendering — draws lines and dots into #board from game state.
//
// - Portrait 3:4 board. Puzzle coords: x in 0–1, y in 0–BOARD_H (one unit = board width).
//   viewBox is 1000 × 1333, so position = coord * 1000.
// - Draw lines first, dots on top. Each dot: a circle + how many lines it still needs
//   (hidden at 0 — then only the yellow/red colour shows).
// - Hit testing is geometric (nearest dot / nearest line), not per-element hit circles, so dots
//   can sit closer than a fingertip without ambiguous taps. See dotAtPoint / lineAtPoint.
// - Dot classes: dot--ok (yellow), dot--bad (red), neutral otherwise. Hinted lines: line--hinted.
// - Win state: the whole constellation lights up — dots yellow, each line in its colour
//   (puzzle.colors: { "a|b": "green" }, default yellow), glowing via the #win-glow filter.
//
// renderBoard builds the static parts once; the returned view's update() redraws lines and
// dot states after every change.

import { dotStatus, isSolved, remaining, splitKey } from "./game.js";

const NS = "http://www.w3.org/2000/svg";
const SCALE = 1000;
export const BOARD_H = 4 / 3;
// Sized for a ~360px phone (board ≈ 344px wide, so 1 unit ≈ 0.34px): dot ≈ 19px wide.
// tools/validate_puzzles.py keeps dots ≥ 0.11 apart (≈ 38px) and ≥ 0.05 from the board edge —
// keep those in sync with these numbers.
const DOT_R = 28;
const DOT_HIT_MAX = 90;  // a tap further than this from every dot hits nothing (≈ 31px)
const LINE_HIT_R = 30;   // eraser: a tap within this of a line hits it (≈ 10px either side)

function el(name, attrs = {}, parent) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function distToSegment(p, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const len2 = dx * dx + dy * dy;
  const t = len2 ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / len2)) : 0;
  return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
}

function restartAnimation(node, cls) {
  node.classList.remove(cls);
  void node.getBoundingClientRect(); // restart the animation if it's already running
  node.classList.add(cls);
  node.addEventListener("animationend", () => node.classList.remove(cls), { once: true });
}

export function renderBoard(svg, game) {
  svg.replaceChildren();
  svg.classList.remove("board--solved");
  svg.setAttribute("viewBox", `0 0 ${SCALE} ${Math.round(SCALE * BOARD_H)}`);

  const pos = new Map(game.puzzle.dots.map((d) => [d.id, { x: d.x * SCALE, y: d.y * SCALE }]));
  const colors = game.puzzle.colors ?? {};
  // A soft glow in each line's own colour (a CSS drop-shadow would be one colour for all).
  const defs = el("defs", {}, svg);
  const glow = el("filter", { id: "win-glow", x: "-20%", y: "-20%", width: "140%", height: "140%" }, defs);
  el("feGaussianBlur", { in: "SourceGraphic", stdDeviation: 7, result: "blur" }, glow);
  const merge = el("feMerge", {}, glow);
  el("feMergeNode", { in: "blur" }, merge);
  el("feMergeNode", { in: "SourceGraphic" }, merge);
  const linesLayer = el("g", { class: "lines" }, svg);
  const rubber = el("line", { class: "rubber", visibility: "hidden" }, svg);
  const dotsLayer = el("g", { class: "dots" }, svg);

  const dotEls = new Map();
  const labels = new Map();
  for (const d of game.puzzle.dots) {
    const { x, y } = pos.get(d.id);
    const g = el("g", { class: "dot", "data-dot": d.id }, dotsLayer);
    el("circle", { class: "dot-circle", cx: x, cy: y, r: DOT_R }, g);
    labels.set(d.id, el("text", { class: "dot-label", x, y }, g));
    dotEls.set(d.id, g);
  }

  let lineEls = new Map();
  let drawnKeys = [];

  function update(game) {
    linesLayer.replaceChildren();
    lineEls = new Map();
    drawnKeys = [...game.drawn];
    for (const key of drawnKeys) {
      const [a, b] = splitKey(key);
      const p = pos.get(a), q = pos.get(b);
      let cls = game.hinted.has(key) ? "line line--hinted" : "line";
      if (colors[key]) cls += ` line--c-${colors[key]}`; // only styled once solved (style.css)
      lineEls.set(key, el("line", { class: cls, x1: p.x, y1: p.y, x2: q.x, y2: q.y }, linesLayer));
    }
    for (const [id, g] of dotEls) {
      const status = dotStatus(game, id);
      g.classList.toggle("dot--ok", status === "ok");
      g.classList.toggle("dot--bad", status === "bad");
      const left = remaining(game, id);
      labels.get(id).textContent = left > 0 ? left : "";
    }
    svg.classList.toggle("board--solved", isSolved(game));
  }

  // Nearest dot to an SVG point. strict: only the dot's visible circle counts. → id | null
  function dotAtPoint(p, { strict = false } = {}) {
    let best = null, bestDist = strict ? DOT_R : DOT_HIT_MAX;
    for (const [id, q] of pos) {
      const dist = Math.hypot(p.x - q.x, p.y - q.y);
      if (dist <= bestDist) { best = id; bestDist = dist; }
    }
    return best;
  }

  // Nearest drawn line to an SVG point, within LINE_HIT_R. → key | null
  function lineAtPoint(p) {
    let best = null, bestDist = LINE_HIT_R;
    for (const key of drawnKeys) {
      const [a, b] = splitKey(key);
      const dist = distToSegment(p, pos.get(a), pos.get(b));
      if (dist <= bestDist) { best = key; bestDist = dist; }
    }
    return best;
  }

  function setSelected(id) {
    for (const [dotId, g] of dotEls) g.classList.toggle("dot--selected", dotId === id);
  }

  function setRubberBand(fromId, point) {
    if (!fromId || !point) {
      rubber.setAttribute("visibility", "hidden");
      return;
    }
    const p = pos.get(fromId);
    rubber.setAttribute("x1", p.x);
    rubber.setAttribute("y1", p.y);
    rubber.setAttribute("x2", point.x);
    rubber.setAttribute("y2", point.y);
    rubber.setAttribute("visibility", "visible");
  }

  function shake(id) {
    const g = dotEls.get(id);
    if (g) restartAnimation(g, "dot--shake");
  }

  function shakeLine(key) {
    const line = lineEls.get(key);
    if (line) restartAnimation(line, "line--shake");
  }

  // A hinted line appearing: brief pulse so the eye finds it.
  function flashLine(key) {
    const line = lineEls.get(key);
    if (line) restartAnimation(line, "line--flash");
  }

  update(game);
  return { update, setSelected, setRubberBand, shake, shakeLine, flashLine, dotAtPoint, lineAtPoint };
}
