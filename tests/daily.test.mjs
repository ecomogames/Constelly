import { test } from "node:test";
import assert from "node:assert/strict";
import { getDayIndex, getTodaysPuzzle, msUntilNextPuzzle, pickPuzzle, puzzleDate, LAUNCH_DATE_UTC } from "../js/daily.js";
import { formatTime, formatCountdown } from "../js/format.js";

// Dates relative to the launch day, so the tests survive a change of LAUNCH_DATE_UTC.
const DAY = 86_400_000;
const L = Date.parse(`${LAUNCH_DATE_UTC}T00:00:00Z`);
const at = (days, ms = 0) => new Date(L + days * DAY + ms);

test("day index flips at 00:00 UTC, not local midnight", () => {
  assert.equal(getDayIndex(at(0)), 0);
  assert.equal(getDayIndex(at(1, -1)), 0);
  assert.equal(getDayIndex(at(1)), 1);
  // 01:30 in Denmark (UTC+2) on day 1 is still day 0 in UTC.
  assert.equal(getDayIndex(at(1, -30 * 60_000)), 0);
  assert.equal(getDayIndex(at(0, -1000)), -1);
});

test("today's puzzle: pre-launch shows #1, past the end is null", () => {
  const ps = [{ id: "x" }, { id: "y" }];
  assert.deepEqual(getTodaysPuzzle(ps, at(-8, 12 * 3_600_000)),
    { index: 0, number: 1, puzzle: ps[0], preLaunch: true });
  assert.deepEqual(getTodaysPuzzle(ps, at(1, 12 * 3_600_000)),
    { index: 1, number: 2, puzzle: ps[1], preLaunch: false });
  assert.equal(getTodaysPuzzle(ps, at(2)).puzzle, null);
});

test("pickPuzzle: earlier days are playable, today/future/junk fall back to today", () => {
  const ps = [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }];
  const now = at(2, 3_600_000); // today = #3
  assert.deepEqual(pickPuzzle(ps, "1", now), { index: 0, number: 1, puzzle: ps[0], preLaunch: false, archive: true });
  assert.equal(pickPuzzle(ps, "2", now).archive, true);
  for (const junk of [null, "3", "4", "0", "-1", "2.5", "abc", ""]) {
    const pick = pickPuzzle(ps, junk, now);
    assert.equal(pick.number, 3, `?n=${junk}`);
    assert.equal(pick.archive, false, `?n=${junk}`);
  }
  // before launch there are no past puzzles
  assert.equal(pickPuzzle(ps, "1", at(-2)).archive, false);
  // after the list runs out, earlier puzzles are still playable
  assert.equal(pickPuzzle(ps, "4", at(10)).archive, true);
  assert.equal(pickPuzzle(ps, "5", at(10)).puzzle, null);
});

test("puzzleDate: index -> the UTC day it's played", () => {
  assert.equal(puzzleDate(0).toISOString().slice(0, 10), LAUNCH_DATE_UTC);
  assert.equal(puzzleDate(2).getTime(), L + 2 * DAY);
});

test("countdown to the next puzzle targets 00:00 UTC", () => {
  assert.equal(msUntilNextPuzzle(new Date("2026-10-01T23:59:59Z")), 1000);
  assert.equal(msUntilNextPuzzle(new Date("2026-10-01T00:00:00Z")), 86_400_000);
  assert.equal(msUntilNextPuzzle(new Date("2026-12-31T12:00:00Z")), 12 * 3_600_000);
});
test("time formatting", () => {
  assert.equal(formatTime(0), "0:00");
  assert.equal(formatTime(161_999), "2:41");
  assert.equal(formatTime(3_599_999), "59:59");
  assert.equal(formatTime(3_600_000), "1:00:00");
  assert.equal(formatTime(3_725_000), "1:02:05");
  assert.equal(formatCountdown(1000), "00:00:01");
  assert.equal(formatCountdown(86_400_000), "24:00:00");
  assert.equal(formatCountdown(3_723_400), "01:02:04");
});
