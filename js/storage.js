// localStorage persistence — no accounts, no server.
//
// Keys:
//   constelly:progress:<puzzleId>  → game.js snapshot():
//                                    { edges, hinted, hints, started, elapsedMs, solved }
//   constelly:history              → { <puzzleId>: { day, timeMs, hints, solvedAt } }
//   constelly:stats                → { streak, maxStreak, lastSolvedDay, totalSolved,
//                                      totalTimeMs, bestTimeMs }
//   constelly:seen-help            → 1 once the how-to-play dialog has been shown
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
  return { streak: 0, maxStreak: 0, lastSolvedDay: null, totalSolved: 0, totalTimeMs: 0, bestTimeMs: null };
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
  return s;
}

// A solved puzzle for `day`. Consecutive puzzle days extend the streak; hints don't matter.
// Solving the same day twice is a no-op. → new stats object
export function applyResult(stats, day, timeMs) {
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
    bestTimeMs: stats.bestTimeMs,
  };
}

// Rows for the history list in the stats dialog, newest first: one per puzzle day from today
// (or the last puzzle, if we've run out) back to launch, at most `limit`. Titles only for
// solved puzzles — a missed day stays unspoiled. → [{ day, number, status, title, timeMs, hints }]
//   status: "solved" | "today" (today's puzzle, not solved yet) | "missed"
export function historyRows(history, puzzles, today, limit = 30) {
  const rows = [];
  for (let day = Math.min(today, puzzles.length - 1); day >= 0 && rows.length < limit; day--) {
    const p = puzzles[day];
    const h = history?.[p.id];
    const solved = h && typeof h === "object";
    rows.push({
      day,
      number: day + 1,
      status: solved ? "solved" : day === today ? "today" : "missed",
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

    // Current stats with the streak reset if a day was missed (persisted, outside dev mode).
    loadStats(today) {
      const stored = normalizeStats(read(`${PREFIX}stats`));
      const stats = refreshStreak(stored, today);
      if (!dev && stats !== stored) write(`${PREFIX}stats`, stats);
      return stats;
    },

    // Record a solve once per puzzle id. → updated stats (unchanged in dev mode / if already recorded)
    recordResult({ id, day, timeMs, hints }, now = new Date()) {
      const stats = normalizeStats(read(`${PREFIX}stats`));
      if (dev) return stats;
      const history = loadHistory();
      if (history[id]) return stats;
      history[id] = { day, timeMs, hints, solvedAt: now.toISOString() };
      const next = applyResult(stats, day, timeMs);
      write(`${PREFIX}history`, history);
      write(`${PREFIX}stats`, next);
      return next;
    },

    loadHistory,

    hasSeenHelp: () => read(`${PREFIX}seen-help`) === 1,
    markHelpSeen: () => write(`${PREFIX}seen-help`, 1),
  };
}
