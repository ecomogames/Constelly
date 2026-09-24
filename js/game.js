// Pure game logic — no DOM. Keep it testable.
//
// State: the puzzle, the set of drawn edges, locked hinted edges, the undo history, the hint
// count and the timer. Edges are undirected: normalise a key like "a|b" with ids sorted.
//
// Rules (from CLAUDE.md, decisions confirmed):
//   - Each dot's number = its required degree; the UI shows remaining() = how many it still needs.
//   - HARD CAP: adding a line that would push either endpoint past its degree is rejected
//     (return a result the UI can use to shake the dot). Duplicate lines are rejected too.
//   - Removing a line is allowed unless it's a hinted line (hinted lines are locked).
//   - Dot status: "neutral" while drawn degree < required;
//                 once equal → "ok" if every touching line is in the solution, else "bad".
//   - Solved when drawn edge set === solution edge set (every dot "ok").
//   - Undo: every player add/remove is recorded; undo() applies the inverse of the last one.
//     startOver() removes all non-hinted lines and clears the history (it's confirmed, not undoable).
//   - Hint: see useHint. Hinted lines are locked, survive startOver and are never in history.
//   - Timer: active time only (paused while the tab is hidden, not counted while the page is
//     closed). Stored as data — elapsedMs banked so far + runningSince for the current stretch —
//     and started by the first successfully drawn line or the first hint. It stops on solve.
//     Functions that change the board take `now` (ms) so tests can drive the clock.

export function edgeKey(a, b) {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

export function splitKey(key) {
  return key.split("|");
}

export function createGame(puzzle) {
  const dots = new Map(puzzle.dots.map((d) => [d.id, d]));
  const solution = new Set();
  for (const [a, b] of puzzle.edges) {
    if (!dots.has(a) || !dots.has(b)) {
      throw new Error(`Puzzle ${puzzle.id}: edge ${a}-${b} references a missing dot`);
    }
    solution.add(edgeKey(a, b));
  }

  const game = {
    puzzle, dots, solution,
    drawn: new Set(), hinted: new Set(), history: [],
    hintsUsed: 0,
    timer: { started: false, finished: false, paused: false, elapsedMs: 0, runningSince: null },
  };

  // Cheap runtime guard; tools/validate_puzzles.py is the real pre-publish check.
  for (const d of puzzle.dots) {
    const n = countTouching(solution, d.id);
    if (n !== d.degree) {
      console.warn(`Puzzle ${puzzle.id}: dot ${d.id} has degree ${d.degree} but ${n} solution edges`);
    }
  }
  return game;
}

function countTouching(keys, id) {
  let n = 0;
  for (const key of keys) {
    const [a, b] = splitKey(key);
    if (a === id || b === id) n++;
  }
  return n;
}

export function drawnDegree(game, id) {
  return countTouching(game.drawn, id);
}

// How many more lines this dot needs (the number shown on it). 0 → number hidden.
export function remaining(game, id) {
  return game.dots.get(id).degree - drawnDegree(game, id);
}

// → { ok: true } | { ok: false, reason: "self" | "duplicate" | "cap", capped: [ids] }
function tryAdd(game, a, b) {
  if (a === b) return { ok: false, reason: "self", capped: [] };
  const key = edgeKey(a, b);
  if (game.drawn.has(key)) return { ok: false, reason: "duplicate", capped: [] };
  const capped = [a, b].filter((id) => remaining(game, id) <= 0);
  if (capped.length) return { ok: false, reason: "cap", capped };
  game.drawn.add(key);
  return { ok: true };
}

// → { ok: true } | { ok: false, reason: "missing" | "locked" }
function tryRemove(game, key) {
  if (!game.drawn.has(key)) return { ok: false, reason: "missing" };
  if (game.hinted.has(key)) return { ok: false, reason: "locked" };
  game.drawn.delete(key);
  return { ok: true };
}

// ---- timer ----

export function elapsedMs(game, now = Date.now()) {
  const t = game.timer;
  return t.elapsedMs + (t.runningSince === null ? 0 : Math.max(0, now - t.runningSince));
}

function startTimer(game, now) {
  const t = game.timer;
  if (t.started) return;
  t.started = true;
  if (!t.paused) t.runningSince = now;
}

// Bank the running stretch (tab hidden). Safe to call repeatedly.
export function pauseTimer(game, now = Date.now()) {
  const t = game.timer;
  t.elapsedMs = elapsedMs(game, now);
  t.runningSince = null;
  t.paused = true;
}

export function resumeTimer(game, now = Date.now()) {
  const t = game.timer;
  t.paused = false;
  if (t.started && !t.finished && t.runningSince === null) t.runningSince = now;
}

// After any board change: stop the clock once solved.
function settle(game, now) {
  if (game.timer.finished || !isSolved(game)) return;
  game.timer.elapsedMs = elapsedMs(game, now);
  game.timer.runningSince = null;
  game.timer.finished = true;
}

// ---- player actions — recorded for undo ----

export function addEdge(game, a, b, now = Date.now()) {
  const result = tryAdd(game, a, b);
  if (result.ok) {
    game.history.push({ type: "add", key: edgeKey(a, b) });
    startTimer(game, now);
    settle(game, now);
  }
  return result;
}

export function removeEdge(game, a, b, now = Date.now()) {
  const key = edgeKey(a, b);
  const result = tryRemove(game, key);
  if (result.ok) {
    game.history.push({ type: "remove", key });
    settle(game, now);
  }
  return result;
}

export function canUndo(game) {
  return game.history.length > 0;
}

// Reverts the last action. → { ok: true, key } | { ok: false, key, capped? } | null (nothing to undo)
// If the inverse is no longer possible (e.g. a hint filled a dot since), the entry is dropped.
export function undo(game, now = Date.now()) {
  const entry = game.history.pop();
  if (!entry) return null;
  const result = entry.type === "add"
    ? { key: entry.key, ...tryRemove(game, entry.key) }
    : { key: entry.key, ...tryAdd(game, ...splitKey(entry.key)) };
  if (result.ok) settle(game, now);
  return result;
}

export function startOver(game) {
  for (const key of [...game.drawn]) if (!game.hinted.has(key)) game.drawn.delete(key);
  game.history.length = 0;
}

// Reveal one correct, currently missing line. → { key, removed: [keys] } | null (already solved)
//   1. Prefer a random missing solution line whose endpoints both still have room.
//   2. If there is none, take any missing solution line and, at each endpoint that is full,
//      remove one wrong (non-solution) line first. A full endpoint that is missing one of its
//      solution lines always has a wrong line, and it's never a hinted one (those are correct).
// The hint isn't an undoable action. Rather than clearing the undo history, it drops just the
// entries for the lines it touched, so undo can never remove the hinted line or bring back a line
// the hint removed. Other entries still apply (a re-add that now hits the cap fails safely).
export function useHint(game, rng = Math.random, now = Date.now()) {
  const missing = [...game.solution].filter((key) => !game.drawn.has(key));
  if (!missing.length) return null;
  const roomy = missing.filter((key) => splitKey(key).every((id) => remaining(game, id) > 0));
  const pool = roomy.length ? roomy : missing;
  const key = pool[Math.floor(rng() * pool.length)];

  const removed = [];
  for (const id of splitKey(key)) {
    if (remaining(game, id) > 0) continue;
    const wrong = [...game.drawn].filter((k) => !game.solution.has(k) && splitKey(k).includes(id));
    const victim = wrong[Math.floor(rng() * wrong.length)];
    game.drawn.delete(victim);
    removed.push(victim);
  }

  game.drawn.add(key);
  game.hinted.add(key);
  game.hintsUsed++;
  const touched = new Set([key, ...removed]);
  const kept = game.history.filter((entry) => !touched.has(entry.key));
  game.history.splice(0, game.history.length, ...kept);
  startTimer(game, now);
  settle(game, now);
  return { key, removed };
}

export function dotStatus(game, id) {
  if (remaining(game, id) > 0) return "neutral";
  for (const key of game.drawn) {
    const [a, b] = splitKey(key);
    if ((a === id || b === id) && !game.solution.has(key)) return "bad";
  }
  return "ok";
}

export function isSolved(game) {
  if (game.drawn.size !== game.solution.size) return false;
  for (const key of game.drawn) if (!game.solution.has(key)) return false;
  return true;
}

// ---- save / restore (storage.js owns where this goes) ----

export function snapshot(game, now = Date.now()) {
  return {
    edges: [...game.drawn],
    hinted: [...game.hinted],
    hints: game.hintsUsed,
    started: game.timer.started,
    elapsedMs: Math.round(elapsedMs(game, now)),
    solved: game.timer.finished,
  };
}

// Apply saved progress to a fresh game, dropping anything that doesn't fit the puzzle (unknown
// dots, duplicates, over-cap lines, "hinted" lines that aren't in the solution). The undo history
// isn't saved, so it starts empty. The timer comes back paused; call resumeTimer when visible.
export function restoreProgress(game, saved, now = Date.now()) {
  if (!saved || typeof saved !== "object") return game;
  const list = (v) => (Array.isArray(v) ? v : []);
  const ids = (key) => {
    if (typeof key !== "string") return null;
    const pair = splitKey(key);
    return pair.length === 2 && pair.every((id) => game.dots.has(id)) ? pair : null;
  };

  for (const key of list(saved.hinted)) {
    const pair = ids(key);
    if (pair && game.solution.has(edgeKey(...pair)) && tryAdd(game, ...pair).ok) {
      game.hinted.add(edgeKey(...pair));
    }
  }
  for (const key of list(saved.edges)) {
    const pair = ids(key);
    if (pair) tryAdd(game, ...pair);
  }

  const hints = Number.isInteger(saved.hints) && saved.hints > 0 ? saved.hints : 0;
  game.hintsUsed = Math.max(hints, game.hinted.size);
  const t = game.timer;
  const ms = Number(saved.elapsedMs);
  t.elapsedMs = Number.isFinite(ms) && ms > 0 ? ms : 0;
  t.started = saved.started === true || t.elapsedMs > 0 || game.drawn.size > 0;
  t.paused = true;
  t.runningSince = null;
  settle(game, now);
  return game;
}
