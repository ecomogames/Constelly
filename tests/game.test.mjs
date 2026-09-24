import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createGame, addEdge, removeEdge, undo, canUndo, startOver, isSolved, remaining, useHint,
  elapsedMs, pauseTimer, resumeTimer, snapshot, restoreProgress,
} from "../js/game.js";

const dot = (id, degree) => ({ id, x: 0.5, y: 0.5, degree });

// Square a-b-c-d-a: every dot needs 2.
const square = () => createGame({
  id: "square", dots: ["a", "b", "c", "d"].map((id) => dot(id, 2)),
  edges: [["a", "b"], ["b", "c"], ["c", "d"], ["d", "a"]],
});
// Two separate lines a-b and c-d: every dot needs 1.
const pairs = () => createGame({
  id: "pairs", dots: ["a", "b", "c", "d"].map((id) => dot(id, 1)),
  edges: [["a", "b"], ["c", "d"]],
});
// Path a-b-c.
const path = () => createGame({
  id: "path", dots: [dot("a", 1), dot("b", 2), dot("c", 1)], edges: [["a", "b"], ["b", "c"]],
});
const first = () => 0;
const last = () => 0.999;

// ---- hints ----

test("hint branch 1: picks a missing solution line whose endpoints both have room", () => {
  const g = square();
  addEdge(g, "a", "c", 0);            // wrong; a and c keep 1 slot each
  const r = useHint(g, last, 0);
  assert.ok(g.solution.has(r.key));
  assert.deepEqual(r.removed, []);
  assert.ok(g.drawn.has("a|c"), "the wrong line stays: nothing needed removing");
  assert.ok(g.drawn.has(r.key) && g.hinted.has(r.key));
  assert.equal(g.hintsUsed, 1);
});

test("hint branch 1 is preferred over lines with a full endpoint", () => {
  for (const rng of [first, last]) {
    const g = square();
    addEdge(g, "a", "c", 0);
    addEdge(g, "a", "b", 0);          // a full; missing b|c, c|d, d|a — only b|c and c|d have room
    const r = useHint(g, rng, 0);
    assert.ok(["b|c", "c|d"].includes(r.key), r.key);
    assert.deepEqual(r.removed, []);
  }
});

test("hint branch 2: both endpoints full with wrong lines — each loses one", () => {
  const g = pairs();
  addEdge(g, "a", "c", 0);
  addEdge(g, "b", "d", 0);            // every dot full, every line wrong
  const r = useHint(g, first, 0);
  assert.equal(r.key, "a|b");
  assert.deepEqual(r.removed.sort(), ["a|c", "b|d"]);
  assert.deepEqual([...g.drawn], ["a|b"]);
  assert.equal(remaining(g, "c"), 1);
  assert.equal(remaining(g, "d"), 1);
});

test("hint branch 2: only the full endpoint loses a line", () => {
  const g = path();
  addEdge(g, "a", "c", 0);            // a and c full (wrong line); b empty
  const r = useHint(g, first, 0);     // missing a|b and b|c both have a full endpoint
  assert.equal(r.key, "a|b");
  assert.deepEqual(r.removed, ["a|c"]);
  assert.deepEqual([...g.drawn].sort(), ["a|b"]);
});

test("hint returns null once solved", () => {
  const g = pairs();
  addEdge(g, "a", "b", 0);
  addEdge(g, "c", "d", 0);
  assert.equal(useHint(g, first, 0), null);
  assert.equal(g.hintsUsed, 0);
});

test("hint prunes only the undo entries for lines it touched", () => {
  const g = square();
  addEdge(g, "a", "c", 0);            // will stay (room is left)
  addEdge(g, "a", "b", 0);            // a full
  removeEdge(g, "a", "b", 0);
  addEdge(g, "b", "c", 0);
  // Force the hint onto a|b: history has add a|b + remove a|b, both must go.
  const r = useHint(g, () => 0, 0);
  assert.equal(r.key, "a|b");
  assert.deepEqual(g.history.map((e) => e.key), ["a|c", "b|c"]);
  undo(g, 0);                          // removes b|c
  undo(g, 0);                          // removes a|c
  assert.deepEqual([...g.drawn], ["a|b"]);
  assert.equal(canUndo(g), false);
});

test("hinted lines can't be erased or undone and survive startOver", () => {
  const g = square();
  const { key } = useHint(g, first, 0);
  const [a, b] = key.split("|");
  assert.deepEqual(removeEdge(g, a, b, 0), { ok: false, reason: "locked" });
  assert.equal(canUndo(g), false);
  addEdge(g, "a", "c", 0);
  startOver(g);
  assert.deepEqual([...g.drawn], [key]);
  assert.deepEqual([...g.hinted], [key]);
  assert.equal(g.hintsUsed, 1, "start over keeps the hint count");
});

// ---- timer ----

test("timer: rejected lines don't start it; the first drawn line does", () => {
  const g = path();
  addEdge(g, "a", "a", 100);           // self: rejected
  assert.equal(g.timer.started, false);
  assert.equal(elapsedMs(g, 5000), 0);
  addEdge(g, "a", "c", 1000);
  assert.equal(g.timer.started, true);
  assert.equal(elapsedMs(g, 4000), 3000);
  addEdge(g, "a", "b", 9000);          // cap: rejected, doesn't restart the clock
  assert.equal(elapsedMs(g, 9000), 8000);
});

test("timer: a hint before any line starts it (no 0:00 hint-only runs)", () => {
  const g = square();
  useHint(g, first, 2000);
  assert.equal(g.timer.started, true);
  assert.equal(elapsedMs(g, 7000), 5000);
});

test("timer: pauses while hidden and stops on solve", () => {
  const g = pairs();
  addEdge(g, "a", "b", 0);
  pauseTimer(g, 10_000);
  assert.equal(elapsedMs(g, 60_000), 10_000, "hidden time doesn't count");
  resumeTimer(g, 60_000);
  addEdge(g, "c", "d", 65_000);        // solves it
  assert.equal(g.timer.finished, true);
  assert.equal(elapsedMs(g, 999_999), 15_000);
  resumeTimer(g, 999_999);
  assert.equal(elapsedMs(g, 2_000_000), 15_000, "resume after solve does nothing");
});

test("timer: starting while hidden waits for resume", () => {
  const g = path();
  pauseTimer(g, 0);
  addEdge(g, "a", "b", 1000);
  assert.equal(elapsedMs(g, 5000), 0);
  resumeTimer(g, 5000);
  assert.equal(elapsedMs(g, 6000), 1000);
});

// ---- save / restore ----

test("snapshot → restore round-trips lines, hints and time; history starts empty", () => {
  const g = square();
  addEdge(g, "a", "c", 0);
  useHint(g, first, 0);
  const saved = JSON.parse(JSON.stringify(snapshot(g, 42_000)));
  const h = restoreProgress(square(), saved, 50_000);
  assert.deepEqual([...h.drawn].sort(), [...g.drawn].sort());
  assert.deepEqual([...h.hinted], [...g.hinted]);
  assert.equal(h.hintsUsed, 1);
  assert.equal(h.history.length, 0);
  assert.equal(elapsedMs(h, 99_000), 42_000, "comes back paused");
  resumeTimer(h, 100_000);
  assert.equal(elapsedMs(h, 101_000), 43_000);
});

test("restore drops invalid data", () => {
  const h = restoreProgress(pairs(), {
    edges: ["a|c", "a|b", "x|y", "a|a|b", 7, "c|d"],   // a|b over cap (a full from a|c)
    hinted: ["b|d", "zz|a"],                           // not in the solution / unknown dot
    hints: -3, elapsedMs: "nope", started: "yes",
  });
  // a|c fills a and c, so a|b and c|d are over the cap; the rest are malformed.
  assert.deepEqual([...h.drawn], ["a|c"]);
  assert.equal(h.hinted.size, 0);
  assert.equal(h.hintsUsed, 0);
  assert.equal(h.timer.elapsedMs, 0);
  assert.equal(h.timer.started, true, "lines on the board imply a started timer");
  assert.equal(restoreProgress(pairs(), null).drawn.size, 0);
});

test("restoring a solved board marks the timer finished", () => {
  const h = restoreProgress(pairs(), { edges: ["a|b", "c|d"], hints: 0, elapsedMs: 61_000 });
  assert.equal(isSolved(h), true);
  assert.equal(h.timer.finished, true);
  resumeTimer(h, 0);
  assert.equal(elapsedMs(h, 10_000_000), 61_000);
});
