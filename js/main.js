// Entry point: wires the modules together on page load.
//
// Flow:
//   1. load puzzles (puzzles/puzzles.json)
//   2. pick today's puzzle (daily.js); ?p=N overrides it on localhost only
//   3. create game state (game.js), restore saved progress for that puzzle id (storage.js),
//      render it (render.js)
//   4. hook up input + controls (eraser, undo, start over, hint) and the timer
//   5. on win: glow + title, record the result, then the results dialog (with Share).
//      A puzzle that was already solved opens straight into the win state.
//   Header: sidebar menu (today, past puzzles, how to play, stats, privacy) and stats.
//   How-to-play auto-opens on the first visit. ?n=N plays an earlier day ("Past puzzles"):
//   recorded in history but not in stats/streak. "Play again" clears a solved puzzle's progress
//   and reloads; the first result stays the official one (results dialog, share, stats).

import {
  createGame, addEdge, removeEdge, undo, canUndo, startOver, isSolved, edgeKey, splitKey, remaining,
  useHint, elapsedMs, pauseTimer, resumeTimer, snapshot, restoreProgress,
} from "./game.js";
import { getDayIndex, pickPuzzle, puzzleDate, msUntilNextPuzzle } from "./daily.js";
import { createStore, summarize, archiveRows } from "./storage.js";
import { share } from "./share.js";
import { renderBoard } from "./render.js";
import { attachInput } from "./input.js";
import { formatTime, formatCountdown } from "./format.js";
import { STRINGS } from "./strings.js";

const LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]"];
const RESULTS_DELAY_MS = 1000; // let the win glow play before the dialog covers it

const $ = (id) => document.getElementById(id);

// Dev-only: on localhost, ?p=N picks puzzles[N] so any puzzle can be tested. → N | null
function devOverride(count) {
  if (!LOCAL_HOSTS.includes(location.hostname)) return null;
  const raw = new URLSearchParams(location.search).get("p");
  if (raw === null) return null;
  const n = Number.parseInt(raw, 10);
  return Number.isInteger(n) && n >= 0 && n < count ? n : null;
}

// Static labels: data-text="results.time" → textContent, data-label → aria-label + title.
function applyStaticStrings() {
  const lookup = (path) => path.split(".").reduce((o, k) => o?.[k], STRINGS);
  for (const node of document.querySelectorAll("[data-text]")) {
    node.textContent = lookup(node.dataset.text);
  }
  for (const node of document.querySelectorAll("[data-label]")) {
    node.setAttribute("aria-label", lookup(node.dataset.label));
    node.title = lookup(node.dataset.label);
  }
}

// Dialogs close on a tap outside their box (Esc and the × already close them natively).
function lightDismiss(dialog) {
  dialog.addEventListener("click", (e) => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) dialog.close();
  });
}

async function init() {
  applyStaticStrings();
  document.querySelectorAll("dialog.dialog").forEach(lightDismiss);

  let puzzles;
  try {
    const res = await fetch("puzzles/puzzles.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    puzzles = await res.json();
  } catch {
    // Offline, or a flaky connection mid-load: say so instead of showing an empty board.
    $("board").style.display = "none";
    $("controls").hidden = true;
    $("hint-btn").hidden = true;
    $("timer").hidden = true;
    $("reveal").textContent = STRINGS.loadFailed;
    $("reveal").hidden = false;
    return;
  }
  const override = devOverride(puzzles.length);
  const pick = override !== null
    ? { index: override, number: override + 1, puzzle: puzzles[override], preLaunch: false, archive: false }
    : pickPuzzle(puzzles, new URLSearchParams(location.search).get("n"));

  $("puzzle-num").textContent = `#${pick.number}`;
  document.title = `Constelly #${pick.number} — daily constellation puzzle`;
  if (pick.archive) {
    $("archive-label").textContent = STRINGS.archive.label(pick.number, STRINGS.past.date(puzzleDate(pick.index)));
    $("archive-bar").hidden = false;
  }

  const svg = $("board");
  const reveal = $("reveal");
  const controls = $("controls");
  const hintBtn = $("hint-btn");
  const eraserBtn = $("eraser-btn");
  const undoBtn = $("undo-btn");
  const resetBtn = $("reset-btn");
  const resultsBtn = $("results-btn");
  const timerEl = $("timer");
  const confirmReset = $("confirm-reset");
  const resultsDialog = $("results");
  const helpDialog = $("help");
  const statsDialog = $("stats");

  // Dev override and pre-launch play keep their progress apart and never touch history/stats.
  const store = createStore({ dev: override !== null || pick.preLaunch });
  const today = getDayIndex();
  store.loadStats(today); // resets a broken streak as soon as the game loads

  // ---- how to play: opens by itself on the very first visit ----
  for (const text of STRINGS.help.body) {
    const p = document.createElement("p");
    p.textContent = text;
    $("help-body").appendChild(p);
  }
  $("help-demo-img").alt = STRINGS.help.demoAlt;
  const menuDialog = $("menu");
  const pastDialog = $("past");
  const closeAll = () => document.querySelectorAll("dialog[open]").forEach((d) => d.close());

  // ---- sidebar menu ----
  $("menu-btn").addEventListener("click", () => { closeAll(); menuDialog.showModal(); });
  $("menu-today").addEventListener("click", (e) => {
    // Already on today's puzzle: just close the menu instead of reloading.
    if (!pick.archive && override === null) { e.preventDefault(); menuDialog.close(); }
  });
  $("menu-past").addEventListener("click", () => openPast());
  $("menu-help").addEventListener("click", () => { closeAll(); helpDialog.showModal(); });
  $("menu-stats").addEventListener("click", () => { closeAll(); $("stats-btn").click(); });
  $("stats-past").addEventListener("click", () => openPast());
  if (!store.hasSeenHelp()) {
    helpDialog.showModal();
    store.markHelpSeen();
  }

  // ---- past puzzles ----
  function openPast() {
    const rows = archiveRows(store.loadHistory(), puzzles, getDayIndex(), store.loadProgress);
    const list = $("past-list");
    list.replaceChildren();
    if (!rows.length) {
      const li = document.createElement("li");
      li.className = "past-row";
      li.textContent = STRINGS.past.none;
      list.appendChild(li);
    }
    for (const r of rows) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.className = `past-row past-row--${r.status}` + (pick.puzzle && r.day === pick.index ? " past-row--current" : "");
      a.href = r.today ? "./" : `?n=${r.number}`;
      const num = document.createElement("span");
      num.className = "past-num";
      num.textContent = `#${r.number}`;
      const title = document.createElement("span");
      title.className = "past-title";
      title.textContent = r.status === "solved" ? r.title
        : r.status === "started" ? STRINGS.past.started : STRINGS.past.unsolved;
      const date = document.createElement("span");
      date.className = "past-date";
      date.textContent = r.today ? STRINGS.past.today : STRINGS.past.date(puzzleDate(r.day));
      a.append(num, title, date);
      if (r.status === "solved") {
        const meta = document.createElement("span");
        meta.className = "past-meta";
        meta.textContent = [r.timeMs === null ? null : formatTime(r.timeMs),
          r.hints === null ? null : STRINGS.past.hints(r.hints), r.late ? STRINGS.past.late : null]
          .filter(Boolean).join(" · ");
        a.append(meta);
      }
      li.append(a);
      list.appendChild(li);
    }
    closeAll();
    pastDialog.showModal();
    list.querySelector(".past-row--current")?.scrollIntoView({ block: "nearest" });
  }

  // ---- stats ----
  let isSolvedNow = () => false; // replaced once a puzzle is loaded
  const statTime = (ms) => (ms === null ? STRINGS.stats.none : formatTime(ms));
  $("stats-btn").addEventListener("click", () => {
    const s = summarize(store.loadStats(today));
    $("stat-solved").textContent = String(s.solved);
    $("stat-streak").textContent = String(s.streak);
    $("stat-max-streak").textContent = String(s.maxStreak);
    $("stat-avg").textContent = statTime(s.avgTimeMs);
    $("stat-best").textContent = statTime(s.bestTimeMs);
    $("stats-today").hidden = !isSolvedNow();
    closeAll();
    statsDialog.showModal();
  });

  if (!pick.puzzle) {
    svg.style.display = "none";
    controls.hidden = true;
    hintBtn.hidden = true;
    timerEl.hidden = true;
    reveal.textContent = STRINGS.outOfPuzzles;
    reveal.hidden = false;
    return;
  }

  const puzzle = pick.puzzle;
  if (puzzle.clue) {
    $("clue").textContent = STRINGS.hud.clue(puzzle.clue);
    $("clue").hidden = false;
  }
  // The first solve is the official result (results dialog, share, stats); replays don't change it.
  const official = () => (store.dev ? null : store.loadResult(puzzle.id));
  const game = restoreProgress(createGame(puzzle), store.loadProgress(puzzle.id));
  const view = renderBoard(svg, game);
  if (official() && !isSolved(game)) {  // a "Play again" in progress
    $("archive-label").textContent = STRINGS.archive.replaying(pick.number);
    $("archive-today").hidden = !pick.archive;
    $("archive-bar").hidden = false;
  }
  let solved = false;

  let leaving = false; // set by "Play again", so pagehide doesn't save the old board back
  const save = () => { if (!leaving) store.saveProgress(puzzle.id, snapshot(game)); };
  function recordResult() {
    store.recordResult({ id: puzzle.id, day: pick.index, timeMs: elapsedMs(game), hints: game.hintsUsed,
      late: pick.archive });
  }
  function playAgain() {
    leaving = true;
    store.clearProgress(puzzle.id);
    location.reload();
  }

  // ---- results ----
  let countdownTimer = null;

  function currentResult() {
    return { number: pick.number, title: puzzle.title, timeMs: elapsedMs(game), hints: game.hintsUsed };
  }

  function updateCountdown() {
    // Past 00:00 UTC since the page loaded: today's puzzle has changed under us.
    $("results-next").textContent = getDayIndex() !== today
      ? STRINGS.results.nextPuzzleReady
      : `${STRINGS.results.nextPuzzle} ${formatCountdown(msUntilNextPuzzle())}`;
  }

  // What the results dialog shows and Share sends: the official (first) solve if there is one.
  function shownResult() {
    const now = currentResult();
    const first = official();
    return first ? { ...now, timeMs: first.timeMs, hints: first.hints, late: !!first.late, now } : { ...now, now };
  }

  function openResults() {
    const r = shownResult();
    $("results-heading").textContent = STRINGS.results.heading(r.number);
    $("results-title").textContent = STRINGS.results.solvedTitle(r.title);
    $("results-time").textContent = formatTime(r.timeMs);
    $("results-hints").textContent = String(r.hints);
    const isReplay = r.now.timeMs !== r.timeMs || r.now.hints !== r.hints;
    const notes = [isReplay ? STRINGS.results.replayNote(formatTime(r.now.timeMs), r.now.hints) : null,
      r.late ? STRINGS.results.lateNote : null].filter(Boolean);
    $("results-replay").textContent = notes.join(" ");
    $("results-replay").hidden = notes.length === 0;
    $("share-status").textContent = "";
    updateCountdown();
    clearInterval(countdownTimer);
    countdownTimer = setInterval(updateCountdown, 1000);
    for (const d of [helpDialog, statsDialog, menuDialog, pastDialog]) if (d.open) d.close();
    if (!resultsDialog.open) resultsDialog.showModal();
  }
  resultsDialog.addEventListener("close", () => clearInterval(countdownTimer));
  resultsBtn.addEventListener("click", openResults);
  $("replay-btn").addEventListener("click", playAgain);
  $("results-replay-btn").addEventListener("click", playAgain);
  $("stats-today").addEventListener("click", openResults);
  isSolvedNow = () => solved;

  let statusTimer = null;
  $("share-btn").addEventListener("click", async () => {
    const outcome = await share(shownResult());
    const message = { copied: STRINGS.share.copied, failed: STRINGS.share.failed }[outcome] ?? "";
    $("share-status").textContent = message;
    clearTimeout(statusTimer);
    if (message) statusTimer = setTimeout(() => ($("share-status").textContent = ""), 2500);
  });

  // ---- timer display: derived from game.timer on each tick, never counted up ----
  function showTime() {
    timerEl.textContent = formatTime(elapsedMs(game));
  }
  const tick = setInterval(showTime, 250);

  function showSolved() {
    input.detach();
    clearInterval(tick);
    showTime();
    reveal.textContent = puzzle.title;
    reveal.hidden = false;
    resultsBtn.hidden = false;
    $("replay-btn").hidden = false;
    document.querySelector(".stage").classList.add("stage--solved");
  }

  function refresh() {
    view.update(game);
    solved = isSolved(game);
    undoBtn.disabled = solved || !canUndo(game);
    resetBtn.disabled = solved || game.drawn.size === game.hinted.size;
    eraserBtn.disabled = solved;
    hintBtn.disabled = solved;
    hintBtn.textContent = STRINGS.hud.hint(game.hintsUsed);
    showTime();
  }

  // After a player action or hint: refresh, and if that solved it, celebrate once.
  function afterChange() {
    const wasSolved = solved;
    refresh();
    save();
    if (solved && !wasSolved) {
      recordResult();
      showSolved();
      setTimeout(openResults, RESULTS_DELAY_MS);
    }
  }

  const input = attachInput(svg, view, {
    onSelect: (id) => view.setSelected(id),
    onRubberBand: (fromId, point) => view.setRubberBand(fromId, point),
    onEraserChange: (on) => eraserBtn.setAttribute("aria-pressed", String(on)),
    onConnect(a, b) {
      const result = addEdge(game, a, b);
      if (!result.ok && result.reason === "cap") result.capped.forEach((id) => view.shake(id));
      afterChange();
      // Tap-tap chains on from b while b can still take a line.
      return !solved && remaining(game, b) > 0;
    },
    onEraseLine(a, b) {
      const result = removeEdge(game, a, b);
      if (!result.ok && result.reason === "locked") view.shakeLine(edgeKey(a, b));
      afterChange();
    },
  });

  eraserBtn.addEventListener("click", () => input.setEraser(!input.isErasing()));

  undoBtn.addEventListener("click", () => {
    const result = undo(game);
    // Only fails once hints exist (a hint may have filled a dot since the erase being undone).
    if (result && !result.ok) (result.capped ?? splitKey(result.key)).forEach((id) => view.shake(id));
    afterChange();
  });

  hintBtn.addEventListener("click", () => {
    const result = useHint(game);
    if (!result) return;
    afterChange();
    view.flashLine(result.key);
    // Dots that had a wrong line taken away to make room.
    new Set(result.removed.flatMap(splitKey)).forEach((id) => {
      if (splitKey(result.key).includes(id)) view.shake(id);
    });
  });

  resetBtn.addEventListener("click", () => confirmReset.showModal());
  // Act on the submit itself (synchronous, and Esc never submits) rather than on "close" +
  // returnValue, which keeps its old value when the dialog is dismissed with Esc.
  confirmReset.querySelector("form").addEventListener("submit", (e) => {
    if (e.submitter?.value !== "reset") return;
    input.setEraser(false);
    startOver(game);
    afterChange();
  });

  // Active time only: pause while the tab is hidden, and save then — on mobile, "hidden" is often
  // the last event a page gets before it's killed.
  function onVisibility() {
    if (document.hidden) {
      pauseTimer(game);
      save();
    } else {
      // A tab left open past 00:00 UTC: load the new puzzle — unless the player is part-way
      // through the old one (its progress is saved; solving it still counts for its own day).
      if (override === null && !pick.archive && getDayIndex() !== today && (solved || game.drawn.size === 0)) {
        location.reload();
        return;
      }
      resumeTimer(game);
    }
    showTime();
  }
  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", save);
  onVisibility();

  refresh();
  if (solved) {
    // Revisiting a solved puzzle: straight to the win state; results reopen via the button.
    recordResult(); // no-op if already recorded (covers a solve whose result never got saved)
    showSolved();
  }
}

init();
