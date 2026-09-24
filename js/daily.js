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

export const LAUNCH_DATE_UTC = "2026-10-01";

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

// Milliseconds until the next 00:00 UTC (when the next puzzle unlocks).
export function msUntilNextPuzzle(now = new Date()) {
  const next = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1);
  return next - now.getTime();
}
