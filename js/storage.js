// localStorage persistence — no accounts, no server.
//
// Keys:
//   constelly:progress:<puzzleId>  → game.js snapshot():
//                                    { edges, hinted, hints, started, elapsedMs, solved }
//   constelly:history              → { <puzzleId>: { day, timeMs, hints, solvedAt, late? } }
//                                    first solve only; late = solved from "Past puzzles"
//   constelly:stats                → { streak, maxStreak, lastSolvedDay, totalSolved,
//                                      totalTimeMs, bestTimeMs, totalHints }
//                                    (totalHints was added later: backfilled from history)
//   constelly:seen-help            → 1 once the how-to-play dialog has been shown
//
// Past puzzles (archive) and replays: a past puzzle solved late goes into history (so the list
// shows it solved) but never touches stats or the streak. A replay ("Play again") clears the
// saved progress only; the first result in history stays the official one.
//
// Progress is keyed by puzzle id; streaks use the puzzle's day index (the "day" in history), so
// finishing a puzzle just after midnight still counts for the day it belongs to.
//
// Dev mode (?p=N on localhost, and pre-launch play of #1): progress goes under constelly:dev:
// and history/stats are never written, so testing and early visitors can't pollute real stats.
//
// Every read/write is wrapped in try/catch — storage can be blocked (private mode, disabled
// cookies, quota) and the game must still work without it: reads return null, writes return false.

const PREFIX = "constelly:";
const DEV_PREFIX = "constelly:dev:";

// ---- pure streak / stats logic ----

export function emptyStats() {
  return {
    streak: 0, maxStreak: 0, lastSolvedDay: null, totalSolved: 0, totalTimeMs: 0, bestTimeMs: null,
    totalHints: 0,
  };
}

// Coerce whatever came out of storage into a valid stats object.
export function normalizeStats(raw) {
  const s = emptyStats();
  if (!raw || typeof raw !== "object") return s;
  const count = (v) => (Number.isInteger(v) && v >= 0 ? v : 0);
  const ms = (v) => (Number.isFinite(v) && v >= 0 ? v : null);
  s.streak = count(raw.streak);
  s.maxStreak = Math.max(count(raw.maxStreak), s.streak);
  s.lastSolvedDay = Number.isInteger(raw.lastSolvedDay) ? raw.lastSolvedDay : null;
  s.totalSolved = count(raw.totalSolved);
  s.totalTimeMs = ms(raw.totalTimeMs) ?? 0;
  s.bestTimeMs = ms(raw.bestTimeMs);
  // null = not stored yet (stats saved before this field existed): loadStats backfills it.
  s.totalHints = Number.isInteger(raw.totalHints) && raw.totalHints >= 0 ? raw.totalHints : null;
  return s;
}

// Hints over the puzzles that count toward stats (solved on their own day) — for the backfill.
export function hintsFromHistory(history) {
  let n = 0;
  for (const h of Object.values(history ?? {})) {
    if (h && typeof h === "object" && !h.late && Number.isInteger(h.hints) && h.hints > 0) n += h.hints;
  }
  return n;
}

// A solved puzzle for `day`. Consecutive puzzle days extend the streak; hints don't break it
// (they only feed the average). Solving the same day twice is a no-op. → new stats object
export function applyResult(stats, day, timeMs, hints = 0) {
  const s = { ...stats };
  if (s.lastSolvedDay !== null && day <= s.lastSolvedDay) {
    if (day === s.lastSolvedDay) return s;
    // An older day solved late (shouldn't happen without an archive): count it, keep the streak.
  } else {
    s.streak = s.lastSolvedDay === day - 1 ? s.streak + 1 : 1;
    s.maxStreak = Math.max(s.maxStreak, s.streak);
    s.lastSolvedDay = day;
  }
  s.totalSolved += 1;
  s.totalTimeMs += timeMs;
  s.bestTimeMs = s.bestTimeMs === null ? timeMs : Math.min(s.bestTimeMs, timeMs);
  s.totalHints = (s.totalHints ?? 0) + (Number.isInteger(hints) && hints > 0 ? hints : 0);
  return s;
}

// On load: a streak survives only if yesterday's (or today's) puzzle was solved.
export function refreshStreak(stats, today) {
  if (stats.lastSolvedDay !== null && stats.lastSolvedDay >= today - 1) return stats;
  return stats.streak === 0 ? stats : { ...stats, streak: 0 };
}

// What the stats dialog shows.
export function summarize(stats) {
  return {
    solved: stats.totalSolved,
    streak: stats.streak,
    maxStreak: stats.maxStreak,
    avgTimeMs: stats.totalSolved ? stats.totalTimeMs / stats.totalSolved : null,
    avgHints: stats.totalSolved && stats.totalHints !== null ? stats.totalHints / stats.totalSolved : null,
    bestTimeMs: stats.bestTimeMs,
  };
}

// Rows for the "Past puzzles" list, newest first: every puzzle day from today (or the last
// puzzle, if we've run out) back to #1. Titles only for solved puzzles, so an unplayed day stays
// unspoiled. progressOf(id) → saved progress or null, to spot puzzles started but not finished.
// → [{ day, number, id, today, status, late, title, timeMs, hints }]
//   status: "solved" | "started" | "new";  late: solved from the list, not on its own day
export function archiveRows(history, puzzles, today, progressOf = () => null) {
  const rows = [];
  for (let day = Math.min(today, puzzles.length - 1); day >= 0; day--) {
    const p = puzzles[day];
    const h = history?.[p.id];
    const solved = !!h && typeof h === "object";
    const progress = solved ? null : progressOf(p.id);
    const started = Array.isArray(progress?.edges) && progress.edges.length > 0;
    rows.push({
      day,
      number: day + 1,
      id: p.id,
      today: day === today,
      status: solved ? "solved" : started ? "started" : "new",
      late: solved && h.late === true,
      title: solved ? p.title : null,
      timeMs: solved && Number.isFinite(h.timeMs) ? h.timeMs : null,
      hints: solved && Number.isInteger(h.hints) ? h.hints : null,
    });
  }
  return rows;
}

// ---- storage access ----

// backend: anything with getItem/setItem (defaults to window.localStorage, looked up lazily
// because even touching `localStorage` can throw when storage is blocked).
export function createStore({ dev = false, backend } = {}) {
  const ls = () => backend ?? globalThis.localStorage;

  function read(key) {
    try {
      const raw = ls().getItem(key);
      return raw === null ? null : JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function remove(key) {
    try {
      ls().removeItem(key);
      return true;
    } catch {
      return false;
    }
  }

  function write(key, value) {
    try {
      ls().setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  }

  const progressKey = (id) => `${dev ? DEV_PREFIX : PREFIX}progress:${id}`;

  function loadHistory() {
    const h = read(`${PREFIX}history`);
    return h && typeof h === "object" && !Array.isArray(h) ? h : {};
  }

  return {
    dev,
    loadProgress: (id) => read(progressKey(id)),
    saveProgress: (id, data) => write(progressKey(id), data),
    clearProgress: (id) => remove(progressKey(id)), // "Play again"

    // Current stats with the streak reset if a day was missed (persisted, outside dev mode).
    loadStats(today) {
      const stored = normalizeStats(read(`${PREFIX}stats`));
      const backfill = stored.totalHints === null;
      const filled = backfill ? { ...stored, totalHints: hintsFromHistory(loadHistory()) } : stored;
      const stats = refreshStreak(filled, today);
      if (!dev && (backfill || stats !== filled)) write(`${PREFIX}stats`, stats);
      return stats;
    },

    // Record a solve once per puzzle id (a replay changes nothing). late = solved from the
    // Past puzzles list: kept in history, left out of stats and the streak.
    // → updated stats (unchanged in dev mode / if already recorded / if late)
    recordResult({ id, day, timeMs, hints, late = false }, now = new Date()) {
      let stats = normalizeStats(read(`${PREFIX}stats`));
      if (dev) return stats;
      if (stats.totalHints === null) stats = { ...stats, totalHints: hintsFromHistory(loadHistory()) };
      const history = loadHistory();
      if (history[id]) return stats;
      history[id] = { day, timeMs, hints, solvedAt: now.toISOString(), ...(late ? { late: true } : {}) };
      write(`${PREFIX}history`, history);
      if (late) return stats;
      const next = applyResult(stats, day, timeMs, hints);
      write(`${PREFIX}stats`, next);
      return next;
    },

    // The first (official) result for a puzzle, or null.
    loadResult: (id) => loadHistory()[id] ?? null,

    loadHistory,

    hasSeenHelp: () => read(`${PREFIX}seen-help`) === 1,
    markHelpSeen: () => write(`${PREFIX}seen-help`, 1),
  };
}
