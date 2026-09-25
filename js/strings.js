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
      "Each number is how many lines that star still needs. A star turns yellow when its lines are right and red when one is wrong.",
      "Tap two stars (or drag between them) to draw a line. Use the eraser to remove lines, or undo your last move.",
      "Stuck? A hint reveals one correct line. You're scored on time and hints used.",
      "A new puzzle every day at 00:00 UTC.",
    ],
    close: "Play",
    privacy: "Privacy",
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
    bestTime: "Best time",
    none: "–",
    viewToday: "View today's result",
    history: "History",
    historyToday: "Today — not solved yet",
    historyMissed: "Missed",
    historyHints: (n) => `${n} ${hintWord(n)}`,
  },
};
