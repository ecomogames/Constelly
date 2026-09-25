// Player-facing strings for the HUD hint count, results, share, how-to-play and stats.
// PLACEHOLDER COPY — edit freely; no logic lives here. Functions take already-formatted values.

const hintWord = (n) => (n === 1 ? "hint" : "hints");

export const STRINGS = {
  close: "Close", // the × on every dialog
  loadFailed: "Couldn't load today's puzzle — check your connection and reload the page.",
  outOfPuzzles:
    "That's all the constellations for now — new ones are coming soon. Check back tomorrow!",

  hud: {
    hint: (used) => (used ? `Hint (${used})` : "Hint"),
    clue: (text) => `“${text}”`, // today's clue, shown between the timer and the Hint button
  },

  results: {
    heading: (number) => `Constelly #${number}`,
    solvedTitle: (title) => `✨ ${title} ✨`,
    time: "Time",
    hints: "Hints",
    share: "Share",
    nextPuzzle: "Next puzzle in",
    nextPuzzleReady: "A new puzzle is ready — reload the page.",
    openButton: "See results",
    replay: "Play again",
    // Shown after solving a replay: the first solve stays the official result (stats, share).
    replayNote: (time, hints) => `Replay: ${time} · ${hints} ${hintWord(hints)}. Your first solve is the one above.`,
    lateNote: "Solved from Past puzzles — it doesn't count toward your streak.",
  },

  share: {
    // No title or category here, ever: the share text must not spoil the picture.
    text: ({ number, time, hints }) =>
      `Constelly #${number} ✨\n⏱ ${time} · 💡 ${hints} ${hintWord(hints)}\nplayconstelly.com`,
    copied: "Copied!",
    failed: "Couldn't copy — try again",
  },

  help: {
    button: "How to play",
    heading: "How to play",
    // One paragraph per entry.
    body: [
      "Connect the stars to reveal a hidden picture.",
      "Each number is how many lines a star still needs. It turns yellow when its lines are right, red when one is wrong.",
      "Tap two stars (or drag) to draw a line. Keep tapping to carry on from the last star; tap it again to stop. The eraser removes lines, undo takes back a move.",
      "The quote at the top is a clue. Still stuck? A hint reveals one correct line. You're scored on time and hints.",
      "A new puzzle every day at 00:00 UTC. Missed one? It's in the menu under Past puzzles.",
    ],
    close: "Play",
    privacy: "Privacy",
    about: "About & FAQ",
    // Alt text for the tutorial animation in the how-to-play dialog.
    demoAlt:
      "Animation: a line is drawn to the wrong star, both stars turn red, the eraser removes it, " +
      "and the right lines complete the picture.",
  },

  stats: {
    button: "Statistics",
    heading: "Statistics",
    solved: "Solved",
    streak: "Current streak",
    maxStreak: "Best streak",
    avgTime: "Average time",
    avgHints: "Average hints",
    bestTime: "Best time",
    none: "–",
    viewToday: "View today's result",
    viewPuzzle: (number) => `View #${number} result`, // same button on a past puzzle
  },

  menu: {
    button: "Menu",
    today: "Today's puzzle",
    past: "Past puzzles",
    help: "How to play",
    stats: "Statistics",
    about: "About & FAQ",
    privacy: "Privacy",
  },

  past: {
    heading: "Past puzzles",
    note: "Play any earlier day. Your streak and stats only count puzzles solved on their own day.",
    none: "No past puzzles yet — come back tomorrow!",
    today: "Today",
    unsolved: "Not played yet",
    started: "In progress",
    late: "played later",
    hints: (n) => `${n} ${hintWord(n)}`,
    // e.g. "Thu 24 Sep"; the date is the UTC day the puzzle was published
    date: (d) => d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }),
  },

  archive: {
    label: (number, date) => `Past puzzle #${number} · ${date}`,
    backToToday: "Back to today",
    replaying: (number) => `Replaying #${number} — your first solve is the one that counts`,
  },
};
