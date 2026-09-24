import { test } from "node:test";
import assert from "node:assert/strict";
import { getDayIndex, getTodaysPuzzle, msUntilNextPuzzle } from "../js/daily.js";
import { formatTime, formatCountdown } from "../js/format.js";

test("day index flips at 00:00 UTC, not local midnight", () => {
  assert.equal(getDayIndex(new Date("2026-10-01T00:00:00Z")), 0);
  assert.equal(getDayIndex(new Date("2026-10-01T23:59:59.999Z")), 0);
  assert.equal(getDayIndex(new Date("2026-10-02T00:00:00Z")), 1);
  // 01:30 in Denmark (UTC+2) on 2 Oct is still 1 Oct in UTC.
  assert.equal(getDayIndex(new Date("2026-10-02T01:30:00+02:00")), 0);
  assert.equal(getDayIndex(new Date("2026-10-02T02:00:00+02:00")), 1);
  assert.equal(getDayIndex(new Date("2026-09-30T23:59:59Z")), -1);
});

test("today's puzzle: pre-launch shows #1, past the end is null", () => {
  const ps = [{ id: "x" }, { id: "y" }];
  assert.deepEqual(getTodaysPuzzle(ps, new Date("2026-09-22T12:00:00Z")),
    { index: 0, number: 1, puzzle: ps[0], preLaunch: true });
  assert.deepEqual(getTodaysPuzzle(ps, new Date("2026-10-02T12:00:00Z")),
    { index: 1, number: 2, puzzle: ps[1], preLaunch: false });
  assert.equal(getTodaysPuzzle(ps, new Date("2026-10-03T00:00:00Z")).puzzle, null);
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
