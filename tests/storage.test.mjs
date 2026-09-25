import { test } from "node:test";
import assert from "node:assert/strict";
import {
  emptyStats, applyResult, refreshStreak, normalizeStats, summarize, createStore,
} from "../js/storage.js";
import { getDayIndex, LAUNCH_DATE_UTC } from "../js/daily.js";

const L = Date.parse(`${LAUNCH_DATE_UTC}T00:00:00Z`);
const at = (days, ms = 0) => new Date(L + days * 86_400_000 + ms);

// Minimal in-memory stand-in for localStorage.
function memory() {
  const m = new Map();
  return {
    m,
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}
const broken = {
  getItem() { throw new Error("SecurityError"); },
  setItem() { throw new Error("QuotaExceededError"); },
  removeItem() { throw new Error("SecurityError"); },
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
  // Solved puzzle day 0. Loading at 23:59 UTC on day 1 keeps it; 00:00 UTC on day 2 resets.
  const s = applyResult(emptyStats(), 0, 1000);
  assert.equal(refreshStreak(s, getDayIndex(at(2, -1000))).streak, 1);
  assert.equal(refreshStreak(s, getDayIndex(at(2))).streak, 0);
  // 01:00 on day 2 in Denmark (UTC+2) is still day 1 in UTC: streak alive.
  assert.equal(refreshStreak(s, getDayIndex(at(2, -3_600_000))).streak, 1);
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

// ---- past puzzles + replays ----
import { archiveRows } from "../js/storage.js";

test("store: a late (Past puzzles) solve goes into history but not stats", () => {
  const backend = memory();
  const store = createStore({ backend });
  store.recordResult({ id: "a", day: 2, timeMs: 3000, hints: 0 });
  const stats = store.recordResult({ id: "b", day: 0, timeMs: 1000, hints: 2, late: true });
  assert.equal(stats.totalSolved, 1);
  assert.equal(stats.bestTimeMs, 3000);
  assert.equal(stats.streak, 1);
  const b = store.loadResult("b");
  assert.deepEqual([b.day, b.timeMs, b.hints, b.late], [0, 1000, 2, true]);
  assert.equal(store.loadResult("a").late, undefined);
  assert.equal(store.loadResult("zzz"), null);
});

test("store: Play again clears progress but keeps the first result", () => {
  const backend = memory();
  const store = createStore({ backend });
  store.saveProgress("a", { edges: ["x|y"], solved: true });
  store.recordResult({ id: "a", day: 0, timeMs: 9000, hints: 1 });
  assert.equal(store.clearProgress("a"), true);
  assert.equal(store.loadProgress("a"), null);
  const after = store.recordResult({ id: "a", day: 0, timeMs: 10, hints: 0 }); // replay solved faster
  assert.equal(after.bestTimeMs, 9000);
  assert.equal(store.loadResult("a").timeMs, 9000);
  assert.equal(createStore({ backend: broken }).clearProgress("a"), false);
});

test("archiveRows: newest first, titles only once solved, started and late flagged", () => {
  const puzzles = [{ id: "a", title: "Fish" }, { id: "b", title: "Tulip" }, { id: "c", title: "House" }, { id: "d", title: "Kite" }];
  const history = { a: { day: 0, timeMs: 61_000, hints: 1, late: true }, c: { day: 2, timeMs: 5000, hints: 0 } };
  const progress = { b: { edges: ["p|q"] }, d: { edges: [] } };
  const rows = archiveRows(history, puzzles, 3, (id) => progress[id] ?? null);
  assert.deepEqual(rows.map((r) => [r.number, r.status, r.title, r.today, r.late]), [
    [4, "new", null, true, false], [3, "solved", "House", false, false],
    [2, "started", null, false, false], [1, "solved", "Fish", false, true],
  ]);
  assert.equal(rows[3].timeMs, 61_000);
  assert.equal(rows[3].hints, 1);
});

test("archiveRows: empty before launch, capped past the end", () => {
  const puzzles = [{ id: "a", title: "A" }, { id: "b", title: "B" }];
  assert.deepEqual(archiveRows({}, puzzles, -3), []);
  assert.deepEqual(archiveRows({}, puzzles, 10).map((r) => [r.day, r.today]), [[1, false], [0, false]]);
  assert.equal(archiveRows(null, puzzles, 0)[0].status, "new");
});

// ---- average hints ----
import { hintsFromHistory } from "../js/storage.js";
import { formatAverage } from "../js/format.js";

test("average hints: counted per on-day solve, one decimal at most", () => {
  let s = emptyStats();
  s = applyResult(s, 0, 1000, 2);
  s = applyResult(s, 1, 1000, 0);
  s = applyResult(s, 2, 1000, 0);
  assert.equal(s.totalHints, 2);
  assert.equal(formatAverage(summarize(s).avgHints), "0.7");
  assert.equal(formatAverage(1), "1");
  assert.equal(formatAverage(2.25), "2.3");
  assert.equal(summarize(emptyStats()).avgHints, null);
  // the same day twice is still a no-op
  assert.equal(applyResult(s, 2, 1, 5).totalHints, 2);
});

test("store: totalHints is backfilled from history for stats saved before it existed", () => {
  const backend = memory();
  backend.setItem("constelly:stats", JSON.stringify({ streak: 2, maxStreak: 2, lastSolvedDay: 1, totalSolved: 2, totalTimeMs: 4000, bestTimeMs: 1000 }));
  backend.setItem("constelly:history", JSON.stringify({
    a: { day: 0, timeMs: 3000, hints: 3 }, b: { day: 1, timeMs: 1000, hints: 0 }, c: { day: 0, timeMs: 1, hints: 9, late: true },
  }));
  const store = createStore({ backend });
  assert.equal(store.loadStats(2).totalHints, 3);
  assert.equal(JSON.parse(backend.m.get("constelly:stats")).totalHints, 3);
  assert.equal(store.recordResult({ id: "d", day: 2, timeMs: 1000, hints: 1 }).totalHints, 4);
  assert.equal(hintsFromHistory(null), 0);
});

test("store: late solves don't add hints to the average", () => {
  const store = createStore({ backend: memory() });
  store.recordResult({ id: "a", day: 3, timeMs: 1000, hints: 1 });
  assert.equal(store.recordResult({ id: "b", day: 0, timeMs: 1000, hints: 4, late: true }).totalHints, 1);
});
