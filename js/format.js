// Small pure formatters shared by the HUD, results, stats and share text.

const pad = (n) => String(n).padStart(2, "0");

// Elapsed time: m:ss, or h:mm:ss from an hour up. Whole seconds, rounded down.
export function formatTime(ms) {
  const total = Math.max(0, Math.floor((Number(ms) || 0) / 1000));
  const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
  return h ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

// Countdown to the next puzzle: always hh:mm:ss.
export function formatCountdown(ms) {
  const total = Math.max(0, Math.ceil((Number(ms) || 0) / 1000));
  return `${pad(Math.floor(total / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`;
}

// An average for the stats dialog: at most one decimal, no trailing ".0" (1, 0.3, 2.5).
export function formatAverage(x) {
  return String(Math.round(x * 10) / 10);
}
