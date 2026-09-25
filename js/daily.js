// Daily puzzle selection — no backend.
//
// Rule (confirmed in CLAUDE.md): puzzle resets at 00:00 UTC for everyone.
// dayIndex = whole UTC days elapsed since LAUNCH_DATE; today's puzzle = puzzles[dayIndex].
//   - Pre-launch (dayIndex < 0): show puzzle 0 (#1).
//   - Past the end of the list: puzzle is null → the page shows a "back tomorrow" message.
//     (No looping: progress is keyed by puzzle id, so a repeat would already count as solved.)
//
// The launch date is the epoch — changing it after launch shifts every player's puzzle.
// Keep in sync with LAUNCH_DATE in tools/validate_puzzles.py.

export const LAUNCH_DATE_UTC = "2026-09-23";

const DAY_MS = 86_400_000;
const EPOCH_MS = Date.parse(`${LAUNCH_DATE_UTC}T00:00:00Z`);

export function getDayIndex(now = new Date()) {
  // Both values are UTC midnights, so the division is exact (no DST in UTC).
  const todayUtc = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.floor((todayUtc - EPOCH_MS) / DAY_MS); // negative before launch
}

// → { index, number, puzzle, preLaunch }   puzzle is null when we've run out of content
export function getTodaysPuzzle(puzzles, now = new Date()) {
  const day = getDayIndex(now);
  const index = Math.max(0, day);
  return { index, number: index + 1, puzzle: puzzles[index] ?? null, preLaunch: day < 0 };
}

// The puzzle to show for this page load. `requested` is the ?n=N number (1-based) from a
// "Past puzzles" link: an earlier day is playable (archive: true); today's number, anything in
// the future, junk, or pre-launch falls back to today's puzzle.
// → { index, number, puzzle, preLaunch, archive }
export function pickPuzzle(puzzles, requested, now = new Date()) {
  const today = getTodaysPuzzle(puzzles, now);
  const n = Number(requested);
  const valid = requested != null && Number.isInteger(n) && n >= 1 && n < today.number && n <= puzzles.length;
  if (today.preLaunch || !valid) return { ...today, archive: false };
  return { index: n - 1, number: n, puzzle: puzzles[n - 1], preLaunch: false, archive: true };
}

// The UTC date a puzzle index is (or was) played on.
export function puzzleDate(index) {
  return new Date(EPOCH_MS + index * DAY_MS);
}

// Milliseconds until the next 00:00 UTC (when the next puzzle unlocks).
export function msUntilNextPuzzle(now = new Date()) {
  const next = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1);
  return next - now.getTime();
}
