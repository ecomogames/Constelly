import { test } from "node:test";
import assert from "node:assert/strict";
import {
  emptyStats, applyResult, refreshStreak, normalizeStats, summarize, createStore,
} from "../js/storage.js";
import { getDayIndex } from "../js/daily.js";

// Minimal in-memory stand-in for localStorage.
function memory() {
  const m = new Map();
  return {
    m,
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
  };
}
const broken = {
  getItem() { throw new Error("SecurityError"); },
  setItem() { throw new Error("QuotaExceededError"); },
};

// ---- pure streak logic ----

test("streak continues on consecutive days and tracks max/best/average", () => {
  let s = emptyStats();
  s = applyResult(s, 0, 100_000);
  s = applyResult(s, 1, 50_000);
  s = applyResult(s, 2, 90_000);
  assert.equal(s.streak, 3);
  assert.equal(s.maxStreak, 3);
  assert.equal(s.totalSolved, 3);
  assert.equal(s.bestTimeMs, 50_000);
  assert.equal(summarize(s).avgTimeMs, 80_000);
});

test("solving the same day twice counts once", () => {
  const s = applyResult(applyResult(emptyStats(), 4, 1000), 4, 1);
  assert.equal(s.totalSolved, 1);
  assert.equal(s.streak, 1);
  assert.equal(s.bestTimeMs, 1000);
});

test("a gap restarts the streak at 1 and keeps the max", () => {
  let s = emptyStats();
  for (const d of [0, 1, 2]) s = applyResult(s, d, 1000);
  s = applyResult(s, 4, 1000);     // day 3 missed
  assert.equal(s.streak, 1);
  assert.equal(s.maxStreak, 3);
});

test("a missed day resets the streak to 0 on the next load", () => {
  const s = applyResult(applyResult(emptyStats(), 0, 1000), 1, 1000);
  assert.equal(refreshStreak(s, 1).streak, 2, "same day");
  assert.equal(refreshStreak(s, 2).streak, 2, "next day, today's puzzle not solved yet");
  const reset = refreshStreak(s, 3);
  assert.equal(reset.streak, 0, "day 2 was missed");
  assert.equal(reset.maxStreak, 2);
  assert.equal(refreshStreak(emptyStats(), 5).streak, 0);
});

test("the streak boundary is 00:00 UTC", () => {
  // Solved puzzle day 0 (1 Oct). Loading at 23:59 UTC on 2 Oct keeps it; 00:00 UTC on 3 Oct resets.
  const s = applyResult(emptyStats(), 0, 1000);
  assert.equal(refreshStreak(s, getDayIndex(new Date("2026-10-02T23:59:59Z"))).streak, 1);
  assert.equal(refreshStreak(s, getDayIndex(new Date("2026-10-03T00:00:00Z"))).streak, 0);
  // 01:00 on 3 Oct in Denmark (UTC+2) is still 2 Oct in UTC: streak alive.
  assert.equal(refreshStreak(s, getDayIndex(new Date("2026-10-03T01:00:00+02:00"))).streak, 1);
});

test("solving a puzzle after midnight counts for the puzzle's own day", () => {
  // Day 1's puzzle finished at 00:05 UTC on day 2 → still extends a day-0 streak.
  let s = applyResult(emptyStats(), 0, 1000);
  s = applyResult(s, 1, 1000);
  assert.equal(refreshStreak(s, 2).streak, 2);
});

test("normalizeStats repairs junk", () => {
  assert.deepEqual(normalizeStats("nope"), emptyStats());
  const s = normalizeStats({ streak: 3, maxStreak: 1, totalSolved: -2, bestTimeMs: "x", lastSolvedDay: 1.5 });
  assert.equal(s.maxStreak, 3);
  assert.equal(s.totalSolved, 0);
  assert.equal(s.bestTimeMs, null);
  assert.equal(s.lastSolvedDay, null);
});

// ---- store ----

test("store: progress round-trip and result recorded once", () => {
  const backend = memory();
  const store = createStore({ backend });
  assert.equal(store.loadProgress("fish"), null);
  store.saveProgress("fish", { edges: ["a|b"], hints: 1 });
  assert.deepEqual(store.loadProgress("fish"), { edges: ["a|b"], hints: 1 });
  assert.ok(backend.m.has("constelly:progress:fish"));

  store.recordResult({ id: "fish", day: 0, timeMs: 5000, hints: 1 });
  const again = store.recordResult({ id: "fish", day: 0, timeMs: 1, hints: 0 });
  assert.equal(again.totalSolved, 1);
  assert.equal(again.bestTimeMs, 5000);
  assert.equal(JSON.parse(backend.m.get("constelly:history")).fish.hints, 1);
});

test("store: loadStats persists a streak reset", () => {
  const backend = memory();
  const store = createStore({ backend });
  store.recordResult({ id: "a", day: 0, timeMs: 1000, hints: 0 });
  store.recordResult({ id: "b", day: 1, timeMs: 1000, hints: 0 });
  assert.equal(store.loadStats(2).streak, 2);
  assert.equal(store.loadStats(5).streak, 0);
  assert.equal(JSON.parse(backend.m.get("constelly:stats")).streak, 0);
});

test("store: dev mode uses its own progress prefix and never writes history/stats", () => {
  const backend = memory();
  const dev = createStore({ dev: true, backend });
  dev.saveProgress("fish", { edges: [] });
  dev.recordResult({ id: "fish", day: 0, timeMs: 1000, hints: 0 });
  dev.loadStats(10);
  assert.deepEqual([...backend.m.keys()], ["constelly:dev:progress:fish"]);
  assert.equal(createStore({ backend }).loadProgress("fish"), null);
});

test("store: blocked storage never throws", () => {
  const store = createStore({ backend: broken });
  assert.equal(store.loadProgress("x"), null);
  assert.equal(store.saveProgress("x", {}), false);
  assert.deepEqual(store.loadStats(3), emptyStats());
  assert.equal(store.recordResult({ id: "x", day: 3, timeMs: 1, hints: 0 }).totalSolved, 1);
  assert.equal(store.hasSeenHelp(), false);
  assert.equal(store.markHelpSeen(), false);
});

test("store: corrupt JSON reads as nothing", () => {
  const backend = memory();
  backend.setItem("constelly:progress:x", "{not json");
  backend.setItem("constelly:history", "[1,2]");
  const store = createStore({ backend });
  assert.equal(store.loadProgress("x"), null);
  assert.equal(store.recordResult({ id: "x", day: 0, timeMs: 1, hints: 0 }).totalSolved, 1);
});

// ---- history list ----
import { historyRows } from "../js/storage.js";

test("historyRows: newest first, titles only for solved days, today flagged", () => {
  const puzzles = [{ id: "a", title: "Fish" }, { id: "b", title: "Tulip" }, { id: "c", title: "House" }];
  const history = { a: { day: 0, timeMs: 61_000, hints: 1 } };
  const rows = historyRows(history, puzzles, 2);
  assert.deepEqual(rows.map((r) => [r.number, r.status, r.title]), [
    [3, "today", null], [2, "missed", null], [1, "solved", "Fish"],
  ]);
  assert.equal(rows[2].timeMs, 61_000);
  assert.equal(rows[2].hints, 1);
});

test("historyRows: empty before launch, capped past the end and by limit", () => {
  const puzzles = [{ id: "a", title: "A" }, { id: "b", title: "B" }];
  assert.deepEqual(historyRows({}, puzzles, -3), []);
  assert.deepEqual(historyRows({}, puzzles, 10).map((r) => r.day), [1, 0]);
  assert.equal(historyRows({}, puzzles, 1, 1).length, 1);
  assert.equal(historyRows(null, puzzles, 0)[0].status, "today");
});
