import { test } from "node:test";
import assert from "node:assert/strict";
import { buildShareText } from "../js/share.js";
import puzzles from "../puzzles/puzzles.json" with { type: "json" };

test("share text has number, time and hints", () => {
  const text = buildShareText({ number: 12, timeMs: 161_000, hints: 1 });
  assert.match(text, /#12\b/);
  assert.match(text, /2:41/);
  assert.match(text, /1 hint\b/);
  assert.match(text, /constelly\.com/);
  assert.match(buildShareText({ number: 1, timeMs: 0, hints: 2 }), /2 hints/);
});

test("share text never contains the title or category", () => {
  for (const [i, p] of puzzles.entries()) {
    const text = buildShareText({ ...p, number: i + 1, timeMs: 65_000, hints: 3 }).toLowerCase();
    assert.ok(!text.includes(p.title.toLowerCase()), `${p.id}: title leaked`);
    assert.ok(!text.includes(p.category.toLowerCase()), `${p.id}: category leaked`);
  }
});
